#!/usr/bin/env python3
"""NYC Criminal Justice Graph Explorer.

Person-centric exploration of NYC DOC jail data. Click on a person to see
their full history, then explore connections to other people who share
charges, admission dates, precincts, or overlapping jail stays.

Launch: uv run streamlit run dashboard.py
"""

from __future__ import annotations

import html as html_lib
import tempfile
from pathlib import Path

import networkx as nx
import plotly.express as px
import plotly.graph_objects as go
import polars as pl
import streamlit as st
from pyvis.network import Network

DERIVED_DIR = Path("data/derived")

st.set_page_config(page_title="NYC CJ Graph Explorer", layout="wide")

CHARGE_LABELS = {
    "120.00": "Assault 3rd", "120.05": "Assault 2nd", "120.10": "Assault 1st",
    "125.25": "Murder 2nd", "130.52": "Criminal Sex Act 2nd",
    "140.15": "Crim Trespass 2nd", "140.20": "Burglary 3rd", "140.25": "Burglary 2nd",
    "155.25": "Petit Larceny", "155.30": "Grand Larceny 4th", "155.35": "Grand Larceny 3rd",
    "160.05": "Robbery 3rd", "160.10": "Robbery 2nd", "160.15": "Robbery 1st",
    "215.50": "Criminal Contempt 2nd", "215.51": "Criminal Contempt 1st",
    "220.03": "Drug Poss 7th", "220.16": "Drug Poss 3rd", "220.39": "Drug Sale 3rd",
    "265.03": "Weapon Poss 2nd", "240.20": "Reckless Endang 1st",
}

TIER_COLORS = {
    "single": "#6b7280", "low_repeat": "#3b82f6",
    "moderate_repeat": "#f59e0b", "high_repeat": "#ef4444",
}


def charge_label(code: str | None) -> str:
    if not code:
        return "Unknown"
    label = CHARGE_LABELS.get(code)
    return f"{code} ({label})" if label else code


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

@st.cache_data
def load_persons() -> pl.DataFrame:
    return pl.read_parquet(DERIVED_DIR / "doc_recidivism_persons.parquet")


@st.cache_data
def load_episodes() -> pl.DataFrame:
    return pl.read_parquet(DERIVED_DIR / "doc_recidivism_episodes.parquet")


@st.cache_data
def load_cohort() -> pl.DataFrame:
    return pl.read_parquet(DERIVED_DIR / "doc_cohort_recidivism.parquet")


@st.cache_data
def load_bridge() -> pl.DataFrame:
    return pl.read_parquet(DERIVED_DIR / "arrest_doc_bridge.parquet")


@st.cache_data
def build_coadmission_index() -> pl.DataFrame:
    """Pre-compute co-admission groups: people admitted same day + same charge."""
    e = load_episodes()
    groups = (
        e.filter(pl.col("top_charge").is_not_null())
        .group_by(["admit_date", "top_charge"])
        .agg(
            pl.col("INMATEID").n_unique().alias("n_people"),
            pl.col("INMATEID").alias("people"),
        )
        .filter(pl.col("n_people").is_between(2, 30))  # skip huge generic clusters
    )
    return groups


def find_connections(person_id: str, episodes: pl.DataFrame, coadmit: pl.DataFrame) -> dict:
    """Find all people connected to a given person through shared episodes."""
    person_eps = episodes.filter(pl.col("INMATEID") == person_id)
    if person_eps.height == 0:
        return {"co_admitted": [], "person_episodes": person_eps}

    # Find co-admission matches: same date + charge
    connections = []
    for row in person_eps.iter_rows(named=True):
        if row["top_charge"] is None:
            continue
        matches = coadmit.filter(
            (pl.col("admit_date") == row["admit_date"])
            & (pl.col("top_charge") == row["top_charge"])
        )
        for m in matches.iter_rows(named=True):
            for pid in m["people"]:
                if pid != person_id:
                    connections.append({
                        "connected_id": pid,
                        "link_type": "co_admission",
                        "date": row["admit_date"],
                        "charge": row["top_charge"],
                    })

    return {
        "co_admitted": connections,
        "person_episodes": person_eps,
    }


def find_overlapping_stays(person_id: str, episodes: pl.DataFrame) -> pl.DataFrame:
    """Find people whose jail stays overlapped with this person."""
    person_eps = episodes.filter(
        (pl.col("INMATEID") == person_id)
        & pl.col("discharge_date").is_not_null()
    )
    if person_eps.height == 0:
        return pl.DataFrame()

    results = []
    for row in person_eps.iter_rows(named=True):
        admit = row["admit_date"]
        discharge = row["discharge_date"]
        # Find others who were in jail during this period
        overlaps = episodes.filter(
            (pl.col("INMATEID") != person_id)
            & (pl.col("admit_date") <= discharge)
            & (
                (pl.col("discharge_date") >= admit)
                | pl.col("discharge_date").is_null()
            )
            & (pl.col("top_charge").is_not_null())
        ).select("INMATEID", "admit_date", "discharge_date", "top_charge").head(100)
        results.append(overlaps)

    if not results:
        return pl.DataFrame()
    return pl.concat(results).unique(subset=["INMATEID", "admit_date"])


def build_person_graph(
    person_id: str,
    person_eps: pl.DataFrame,
    connections: list[dict],
    persons_df: pl.DataFrame,
    max_nodes: int = 40,
) -> str:
    """Build an interactive pyvis network graph centered on a person."""
    net = Network(height="600px", width="100%", bgcolor="#1a1a2e", font_color="white")
    net.barnes_hut(gravity=-3000, central_gravity=0.3, spring_length=150)

    # Center node
    person_info = persons_df.filter(pl.col("INMATEID") == person_id)
    if person_info.height > 0:
        p = person_info.row(0, named=True)
        tier = p.get("recidivism_tier", "single")
        label = f"{person_id}\n{p['total_admissions']} stays"
        title = (
            f"INMATEID: {person_id}\n"
            f"Admissions: {p['total_admissions']}\n"
            f"Race: {p.get('race', '?')} | Sex: {p.get('sex', '?')}\n"
            f"First: {p.get('first_admission', '?')}\n"
            f"Last: {p.get('last_admission', '?')}\n"
            f"Tier: {tier}"
        )
    else:
        tier = "single"
        label = person_id
        title = person_id

    net.add_node(
        person_id,
        label=label,
        title=title,
        color=TIER_COLORS.get(tier, "#6b7280"),
        size=35,
        shape="dot",
        borderWidth=3,
        borderWidthSelected=5,
    )

    # Deduplicate connections, count shared events per connected person
    conn_counts: dict[str, list[dict]] = {}
    for c in connections:
        cid = c["connected_id"]
        conn_counts.setdefault(cid, []).append(c)

    # Sort by number of shared events, take top N
    sorted_conns = sorted(conn_counts.items(), key=lambda x: len(x[1]), reverse=True)

    for cid, events in sorted_conns[:max_nodes]:
        # Look up connected person info
        cp = persons_df.filter(pl.col("INMATEID") == cid)
        if cp.height > 0:
            cp_row = cp.row(0, named=True)
            cp_tier = cp_row.get("recidivism_tier", "single")
            cp_label = f"{cid}\n{cp_row['total_admissions']} stays"
            cp_title = (
                f"INMATEID: {cid}\n"
                f"Admissions: {cp_row['total_admissions']}\n"
                f"Race: {cp_row.get('race', '?')} | Sex: {cp_row.get('sex', '?')}\n"
                f"Tier: {cp_tier}\n"
                f"---\n"
                f"Shared events with {person_id}: {len(events)}"
            )
            for ev in events[:5]:
                cp_title += f"\n  {ev['date']} | {charge_label(ev['charge'])}"
        else:
            cp_tier = "single"
            cp_label = cid
            cp_title = cid

        net.add_node(
            cid,
            label=cp_label,
            title=cp_title,
            color=TIER_COLORS.get(cp_tier, "#6b7280"),
            size=15 + min(len(events) * 5, 20),
            shape="dot",
        )

        # Edge
        edge_title = f"{len(events)} shared admission(s)"
        for ev in events[:3]:
            edge_title += f"\n{ev['date']} | {charge_label(ev['charge'])}"

        net.add_edge(
            person_id, cid,
            title=edge_title,
            value=len(events),
            color="#4a5568",
        )

    # Generate HTML
    with tempfile.NamedTemporaryFile(suffix=".html", delete=False, mode="w") as f:
        net.save_graph(f.name)
        return Path(f.name).read_text()


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

st.sidebar.title("NYC CJ Explorer")
page = st.sidebar.radio(
    "View",
    ["Person Explorer", "People Search", "Co-Admission Network", "Stats Overview"],
)


# ---------------------------------------------------------------------------
# Person Explorer — the hero page
# ---------------------------------------------------------------------------

if page == "Person Explorer":
    st.title("Person Explorer")

    persons = load_persons()
    episodes = load_episodes()
    coadmit = build_coadmission_index()

    # Person selection
    col_input, col_random = st.columns([3, 1])
    with col_input:
        person_id = st.text_input(
            "Enter INMATEID",
            placeholder="e.g. 20064261",
            help="Enter a person ID to explore their history and connections",
        )
    with col_random:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Random High-Repeat"):
            high_repeat = persons.filter(pl.col("recidivism_tier") == "high_repeat")
            person_id = high_repeat.sample(1).get_column("INMATEID").item()
            st.session_state["explore_id"] = person_id
            st.rerun()

    # Check session state for navigation
    if "explore_id" in st.session_state and not person_id:
        person_id = st.session_state["explore_id"]
    if person_id:
        st.session_state["explore_id"] = person_id

    if not person_id:
        st.info("Enter an INMATEID above, or click 'Random High-Repeat' to explore a person with 11+ jail stays.")
        # Show some interesting starting points
        st.subheader("Starting Points")
        top = persons.sort("total_admissions", descending=True).head(20)
        cols = ["INMATEID", "total_admissions", "recidivism_tier", "race", "sex", "first_admission", "last_admission", "first_known_charge"]
        st.dataframe(top.select(cols).to_pandas(), use_container_width=True, height=400)
        st.stop()

    person_id = person_id.strip()

    # --- Person profile ---
    person_info = persons.filter(pl.col("INMATEID") == person_id)
    if person_info.height == 0:
        st.error(f"INMATEID '{person_id}' not found")
        st.stop()

    p = person_info.row(0, named=True)

    st.markdown("---")

    # Profile header
    tier = p["recidivism_tier"]
    tier_color = TIER_COLORS.get(tier, "#6b7280")
    st.markdown(
        f"### <span style='color:{tier_color}'>{tier.replace('_', ' ').title()}</span> &mdash; {p['total_admissions']} Admissions",
        unsafe_allow_html=True,
    )

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("INMATEID", person_id)
    c2.metric("Race", p.get("race", "?"))
    c3.metric("Sex", p.get("sex", "?"))
    c4.metric("Birth Year", str(p.get("approx_birth_year", "?")))
    avg_stay = p.get("avg_stay_days")
    c5.metric("Avg Stay", f"{avg_stay:.0f}d" if avg_stay else "?")
    avg_gap = p.get("avg_gap_days")
    c6.metric("Avg Gap", f"{avg_gap:.0f}d" if avg_gap else "?")

    # --- Episode timeline ---
    st.subheader("Episode Timeline")
    person_eps = episodes.filter(pl.col("INMATEID") == person_id).sort("admit_date")

    # Visual timeline — horizontal bars showing each jail stay
    timeline_data = person_eps.with_columns(
        pl.col("top_charge").map_elements(charge_label, return_dtype=pl.Utf8).alias("charge_label"),
        pl.lit("stay").alias("row"),
    ).to_pandas()

    if not timeline_data.empty and "discharge_date" in timeline_data.columns:
        import pandas as pd
        timeline_data["discharge_date"] = pd.to_datetime(timeline_data["discharge_date"]).fillna(pd.to_datetime(timeline_data["admit_date"]))
        timeline_data["admit_date"] = pd.to_datetime(timeline_data["admit_date"])
        timeline_data["ep_label"] = timeline_data.apply(
            lambda r: f"Ep {r['episode_num']}: {r['charge_label']}", axis=1
        )
        fig = px.timeline(
            timeline_data,
            x_start="admit_date",
            x_end="discharge_date",
            y="row",
            color="charge_label",
            title="Jail Stays (hover for details)",
            hover_data=["episode_num", "stay_days", "gap_days", "status_code", "charge_label"],
        )
        fig.update_layout(height=250, showlegend=True, yaxis_visible=False)
        st.plotly_chart(fig, use_container_width=True)

    # Episode table
    ep_cols = ["episode_num", "admit_date", "discharge_date", "stay_days", "gap_days", "top_charge", "status_code", "age_at_discharge"]
    available_cols = [c for c in ep_cols if c in person_eps.columns]
    st.dataframe(person_eps.select(available_cols).to_pandas(), use_container_width=True)

    # --- Charge progression ---
    charges = person_eps.filter(pl.col("top_charge").is_not_null()).select("episode_num", "top_charge", "admit_date")
    if charges.height > 1:
        unique_charges = charges.get_column("top_charge").unique().to_list()
        if len(unique_charges) > 1:
            st.subheader("Charge Progression")
            st.caption(f"{len(unique_charges)} distinct charges across {charges.height} episodes")
            for row in charges.iter_rows(named=True):
                st.markdown(f"**Ep {row['episode_num']}** ({row['admit_date']}) — {charge_label(row['top_charge'])}")

    # --- Connection graph ---
    st.subheader("Connection Graph")
    st.caption("People admitted on the same day with the same charge (potential co-defendants or related cases)")

    conn_data = find_connections(person_id, episodes, coadmit)
    connections = conn_data["co_admitted"]

    if not connections:
        st.info("No co-admission connections found for this person (charge may be null or no same-day matches).")
    else:
        unique_connected = len(set(c["connected_id"] for c in connections))
        st.caption(f"{unique_connected} connected people via {len(connections)} shared admission events")

        graph_html = build_person_graph(person_id, person_eps, connections, persons)
        st.components.v1.html(graph_html, height=650, scrolling=False)

        # Connected people table
        st.subheader("Connected People")
        conn_rows = []
        conn_counts: dict[str, int] = {}
        for c in connections:
            conn_counts[c["connected_id"]] = conn_counts.get(c["connected_id"], 0) + 1

        for cid, count in sorted(conn_counts.items(), key=lambda x: x[1], reverse=True)[:30]:
            cp = persons.filter(pl.col("INMATEID") == cid)
            if cp.height > 0:
                r = cp.row(0, named=True)
                conn_rows.append({
                    "INMATEID": cid,
                    "shared_events": count,
                    "total_admissions": r["total_admissions"],
                    "tier": r["recidivism_tier"],
                    "race": r.get("race"),
                    "sex": r.get("sex"),
                    "first_charge": r.get("first_known_charge"),
                })

        if conn_rows:
            conn_df = pl.DataFrame(conn_rows)
            st.dataframe(conn_df.to_pandas(), use_container_width=True)

            # Navigation: click to explore a connected person
            st.markdown("**Explore a connected person:**")
            nav_cols = st.columns(min(len(conn_rows), 6))
            for i, row in enumerate(conn_rows[:6]):
                with nav_cols[i]:
                    if st.button(f"{row['INMATEID']}", key=f"nav_{row['INMATEID']}"):
                        st.session_state["explore_id"] = row["INMATEID"]
                        st.rerun()

    # --- Bridge data (geography) ---
    bridge = load_bridge()
    person_bridge = bridge.filter(pl.col("INMATEID") == person_id)
    if person_bridge.height > 0:
        st.subheader("Arrest Geography (from Arrest-DOC Bridge)")
        st.caption("Heuristic matches — candidate links, not ground truth")

        map_data = person_bridge.filter(
            pl.col("lat").is_not_null() & (pl.col("lat") != 0)
        ).select(
            pl.col("lat").alias("latitude"),
            pl.col("lon").alias("longitude"),
        ).to_pandas()

        if not map_data.empty:
            st.map(map_data)

        bridge_cols = ["arrest_date", "arrest_boro", "arrest_precinct", "penal_code", "arrest_race", "arrest_sex", "law_category"]
        st.dataframe(person_bridge.select(bridge_cols).to_pandas(), use_container_width=True)


# ---------------------------------------------------------------------------
# People Search
# ---------------------------------------------------------------------------

elif page == "People Search":
    st.title("People Search")
    persons = load_persons()

    with st.expander("Filters", expanded=True):
        fc1, fc2, fc3, fc4 = st.columns(4)

        tiers = ["All"] + sorted(persons.get_column("recidivism_tier").unique().drop_nulls().to_list())
        tier_filter = fc1.selectbox("Recidivism Tier", tiers)

        races = ["All"] + sorted(persons.get_column("race").unique().drop_nulls().to_list())
        race_filter = fc2.selectbox("Race", races)

        sexes = ["All"] + sorted(persons.get_column("sex").unique().drop_nulls().to_list())
        sex_filter = fc3.selectbox("Sex", sexes)

        min_admissions = fc4.number_input("Min Admissions", min_value=1, value=1, step=1)

        fc5, fc6 = st.columns(2)
        charge_search = fc5.text_input("Charge Code (contains)", placeholder="e.g. 155 or 265.03")

    filtered = persons.filter(pl.col("total_admissions") >= min_admissions)
    if tier_filter != "All":
        filtered = filtered.filter(pl.col("recidivism_tier") == tier_filter)
    if race_filter != "All":
        filtered = filtered.filter(pl.col("race") == race_filter)
    if sex_filter != "All":
        filtered = filtered.filter(pl.col("sex") == sex_filter)
    if charge_search:
        filtered = filtered.filter(
            pl.col("first_known_charge").is_not_null()
            & pl.col("first_known_charge").str.contains(charge_search)
        )

    st.caption(f"{filtered.height:,} people matching filters")

    c1, c2, c3 = st.columns(3)
    c1.metric("People", f"{filtered.height:,}")
    c2.metric("Avg Admissions", f"{filtered.select(pl.col('total_admissions').mean()).item():.1f}")
    repeat_pct = filtered.filter(pl.col("total_admissions") > 1).height / max(filtered.height, 1)
    c3.metric("Repeat Rate", f"{repeat_pct:.1%}")

    # Sortable table
    display_cols = ["INMATEID", "total_admissions", "recidivism_tier", "race", "sex", "approx_birth_year", "first_admission", "last_admission", "avg_stay_days", "first_known_charge", "distinct_charges"]
    sort_col = st.selectbox("Sort by", display_cols, index=1)
    sort_desc = st.checkbox("Descending", value=True)

    sorted_df = filtered.select(display_cols).sort(sort_col, descending=sort_desc)
    st.dataframe(sorted_df.head(500).to_pandas(), use_container_width=True, height=600)

    if filtered.height > 500:
        st.caption(f"Showing first 500 of {filtered.height:,}")

    # Click to explore
    st.markdown("**Enter an INMATEID from the table to explore on the Person Explorer page.**")


# ---------------------------------------------------------------------------
# Co-Admission Network
# ---------------------------------------------------------------------------

elif page == "Co-Admission Network":
    st.title("Co-Admission Network Explorer")
    st.caption("Find clusters of people admitted on the same day with the same charge")

    episodes = load_episodes()
    persons = load_persons()

    fc1, fc2, fc3 = st.columns(3)
    charge_filter = fc1.text_input("Charge Code", placeholder="e.g. 125.25 (Murder 2nd)")
    date_filter = fc2.date_input("Admission Date (optional)", value=None)
    min_cluster = fc3.number_input("Min Cluster Size", min_value=2, max_value=30, value=3)

    # Build clusters based on filters
    base = episodes.filter(pl.col("top_charge").is_not_null())
    if charge_filter:
        base = base.filter(pl.col("top_charge").str.contains(charge_filter))
    if date_filter:
        base = base.filter(pl.col("admit_date") == date_filter)

    clusters = (
        base.group_by(["admit_date", "top_charge"])
        .agg(
            pl.col("INMATEID").n_unique().alias("n_people"),
            pl.col("INMATEID").alias("people"),
        )
        .filter(
            (pl.col("n_people") >= min_cluster) & (pl.col("n_people") <= 30)
        )
        .sort("n_people", descending=True)
    )

    st.caption(f"{clusters.height:,} clusters found")

    if clusters.height > 0:
        # Show top clusters
        cluster_display = clusters.select(
            "admit_date", "top_charge", "n_people"
        ).with_columns(
            pl.col("top_charge").map_elements(charge_label, return_dtype=pl.Utf8).alias("charge_label"),
        ).head(50)

        st.dataframe(cluster_display.to_pandas(), use_container_width=True, height=300)

        # Select a cluster to visualize
        st.subheader("Visualize a Cluster")
        cluster_options = []
        for row in clusters.head(20).iter_rows(named=True):
            label = f"{row['admit_date']} | {charge_label(row['top_charge'])} | {row['n_people']} people"
            cluster_options.append((label, row))

        if cluster_options:
            selected_label = st.selectbox(
                "Select cluster",
                [c[0] for c in cluster_options],
            )
            selected_idx = [c[0] for c in cluster_options].index(selected_label)
            selected = cluster_options[selected_idx][1]

            # Build graph for this cluster
            people_ids = selected["people"]
            net = Network(height="500px", width="100%", bgcolor="#1a1a2e", font_color="white")
            net.barnes_hut(gravity=-2000, spring_length=100)

            for pid in people_ids:
                p_info = persons.filter(pl.col("INMATEID") == pid)
                if p_info.height > 0:
                    r = p_info.row(0, named=True)
                    tier = r.get("recidivism_tier", "single")
                    title = (
                        f"{pid}\n"
                        f"Total: {r['total_admissions']} admissions\n"
                        f"Race: {r.get('race', '?')} | Sex: {r.get('sex', '?')}\n"
                        f"Tier: {tier}"
                    )
                    net.add_node(
                        pid,
                        label=f"{pid}\n{r['total_admissions']} stays",
                        title=title,
                        color=TIER_COLORS.get(tier, "#6b7280"),
                        size=15 + min(r["total_admissions"] * 2, 25),
                    )
                else:
                    net.add_node(pid, label=pid, color="#6b7280", size=15)

            # Connect all members of the cluster
            for i, pid1 in enumerate(people_ids):
                for pid2 in people_ids[i + 1:]:
                    net.add_edge(pid1, pid2, color="#4a5568")

            with tempfile.NamedTemporaryFile(suffix=".html", delete=False, mode="w") as f:
                net.save_graph(f.name)
                graph_html = Path(f.name).read_text()

            st.components.v1.html(graph_html, height=550, scrolling=False)

            # Table of cluster members
            cluster_people = persons.filter(pl.col("INMATEID").is_in(people_ids))
            display_cols = ["INMATEID", "total_admissions", "recidivism_tier", "race", "sex", "approx_birth_year", "first_known_charge"]
            st.dataframe(cluster_people.select(display_cols).to_pandas(), use_container_width=True)

    else:
        st.info("No clusters found matching filters. Try broadening the search.")


# ---------------------------------------------------------------------------
# Stats Overview
# ---------------------------------------------------------------------------

elif page == "Stats Overview":
    st.title("Stats Overview")

    persons = load_persons()
    episodes = load_episodes()
    cohort = load_cohort()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Unique People", f"{persons.height:,}")
    c2.metric("Jail Episodes", f"{episodes.height:,}")
    c3.metric("Repeat Rate", f"{persons.filter(pl.col('total_admissions') > 1).height / persons.height:.1%}")
    eligible_1yr = cohort.filter(pl.col("returned_1yr").is_not_null())
    c4.metric("1yr Return Rate", f"{eligible_1yr.filter(pl.col('returned_1yr') == True).height / eligible_1yr.height:.1%}")  # noqa: E712

    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        # Admissions by year
        by_year = (
            episodes.with_columns(pl.col("admit_date").dt.year().alias("year"))
            .group_by("year").len().sort("year").to_pandas()
        )
        by_year["year"] = by_year["year"].astype(str)
        fig = px.bar(by_year, x="year", y="len", title="Admissions by Year", labels={"len": "Count", "year": "Year"})
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        # 1yr rate trend
        yearly = (
            cohort.filter(pl.col("returned_1yr").is_not_null())
            .group_by("cohort_year")
            .agg(pl.col("returned_1yr").mean().alias("rate"))
            .sort("cohort_year").to_pandas()
        )
        fig2 = px.line(yearly, x="cohort_year", y="rate", title="1-Year Return Rate", labels={"rate": "Rate", "cohort_year": "Year"})
        fig2.update_yaxes(tickformat=".0%")
        st.plotly_chart(fig2, use_container_width=True)

    col3, col4 = st.columns(2)

    with col3:
        tiers = persons.group_by("recidivism_tier").len().sort("len", descending=True).to_pandas()
        fig3 = px.pie(tiers, names="recidivism_tier", values="len", title="Recidivism Tiers", color="recidivism_tier", color_discrete_map=TIER_COLORS)
        st.plotly_chart(fig3, use_container_width=True)

    with col4:
        # Top charges for repeaters
        repeaters = persons.filter(pl.col("total_admissions") > 1)
        charges = (
            repeaters.filter(pl.col("first_known_charge").is_not_null())
            .group_by("first_known_charge").len()
            .sort("len", descending=True).head(12).to_pandas()
        )
        charges["label"] = charges["first_known_charge"].map(charge_label)
        fig4 = px.bar(charges, x="len", y="label", orientation="h", title="Top Charges (Repeaters)", labels={"len": "People", "label": "Charge"})
        fig4.update_layout(yaxis={"categoryorder": "total ascending"})
        st.plotly_chart(fig4, use_container_width=True)
