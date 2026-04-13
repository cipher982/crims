#!/usr/bin/env python3
"""Legacy Streamlit NYC Criminal Justice Explorer.

Person-centric exploration of NYC DOC jail data. Click on a person to see
their full history, episode sequence, charge progression, and any matched
arrest geography from the heuristic arrest-to-DOC bridge.

This remains useful as a quick local fallback, but the canonical explorer is
the Next.js app in `web/`.

Launch: uv run streamlit run dashboard.py
"""

from __future__ import annotations

from pathlib import Path

import plotly.express as px
import polars as pl
import streamlit as st

DERIVED_DIR = Path("data/derived")

st.set_page_config(page_title="NYC CJ Explorer", layout="wide")

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




# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

st.sidebar.title("NYC CJ Explorer")
page = st.sidebar.radio(
    "View",
    ["Person Explorer", "People Search", "Stats Overview"],
)


# ---------------------------------------------------------------------------
# Person Explorer — the hero page
# ---------------------------------------------------------------------------

if page == "Person Explorer":
    st.title("Person Explorer")

    persons = load_persons()
    episodes = load_episodes()

    # Person selection
    col_input, col_random = st.columns([3, 1])
    with col_input:
        person_id = st.text_input(
            "Enter INMATEID",
            placeholder="e.g. 20064261",
            help="Enter a person ID to explore their history",
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
        st.info("Select a row below to explore, or click 'Random High-Repeat'.")
        top = persons.sort("total_admissions", descending=True).head(50)
        display = top.select(
            "INMATEID", "total_admissions", "recidivism_tier", "race", "sex",
            pl.col("first_admission").cast(pl.Utf8).str.slice(0, 10).alias("first_admission"),
            pl.col("last_admission").cast(pl.Utf8).str.slice(0, 10).alias("last_admission"),
            pl.col("first_known_charge").map_elements(charge_label, return_dtype=pl.Utf8).alias("first_charge"),
        )
        event = st.dataframe(
            display.to_pandas(),
            use_container_width=True,
            height=500,
            on_select="rerun",
            selection_mode="single-row",
        )
        if event.selection.rows:
            selected_id = display.row(event.selection.rows[0], named=True)["INMATEID"]
            st.session_state["explore_id"] = selected_id
            st.rerun()
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
    race = p.get("race", "Unknown")
    sex = p.get("sex", "Unknown")
    birth_year = p.get("approx_birth_year", "?")
    avg_stay = p.get("avg_stay_days")
    avg_gap = p.get("avg_gap_days")
    first_charge = charge_label(p.get("first_known_charge"))
    last_charge = charge_label(p.get("last_known_charge"))

    stay_str = f"{avg_stay:.0f} days avg stay" if avg_stay else ""
    gap_str = f"{avg_gap:.0f} days avg gap" if avg_gap else ""
    stats_parts = [s for s in [stay_str, gap_str] if s]

    st.markdown(
        f"### <span style='color:{tier_color}'>{tier.replace('_', ' ').title()}</span> &mdash; "
        f"{p['total_admissions']} Admissions &mdash; {race} {sex}, b.&nbsp;~{birth_year}",
        unsafe_allow_html=True,
    )
    if stats_parts:
        st.caption(" · ".join(stats_parts))
    st.markdown(
        f"**First charge:** {first_charge} &nbsp;&nbsp; **Last charge:** {last_charge}",
        unsafe_allow_html=True,
    )

    # --- Episodes ---
    st.subheader("Episodes")
    person_eps = episodes.filter(pl.col("INMATEID") == person_id).sort("admit_date")

    # Format dates cleanly and add charge labels for display
    display_eps = person_eps.with_columns(
        pl.col("admit_date").cast(pl.Utf8).str.slice(0, 10).alias("admitted"),
        pl.col("discharge_date").cast(pl.Utf8).str.slice(0, 10).alias("discharged"),
        pl.col("top_charge").map_elements(charge_label, return_dtype=pl.Utf8).alias("charge"),
    )

    ep_display_cols = ["episode_num", "admitted", "discharged", "stay_days", "gap_days", "charge", "status_code", "age_at_discharge"]
    available_cols = [c for c in ep_display_cols if c in display_eps.columns]
    st.dataframe(
        display_eps.select(available_cols).to_pandas(),
        use_container_width=True,
        column_config={
            "episode_num": st.column_config.NumberColumn("#", width="small"),
            "admitted": "Admitted",
            "discharged": "Discharged",
            "stay_days": st.column_config.NumberColumn("Stay (days)", width="small"),
            "gap_days": st.column_config.NumberColumn("Gap (days)", width="small"),
            "charge": "Charge",
            "status_code": "Status",
            "age_at_discharge": st.column_config.NumberColumn("Age", width="small"),
        },
        height=min(400, person_eps.height * 38 + 40),
    )

    # --- Charge progression ---
    charges = person_eps.filter(pl.col("top_charge").is_not_null()).select("episode_num", "top_charge", "admit_date")
    if charges.height > 1:
        unique_charges = charges.get_column("top_charge").unique().to_list()
        if len(unique_charges) > 1:
            st.subheader("Charge Progression")
            st.caption(f"{len(unique_charges)} distinct charges across {charges.height} episodes")
            for row in charges.iter_rows(named=True):
                st.markdown(f"**Ep {row['episode_num']}** ({row['admit_date']}) — {charge_label(row['top_charge'])}")

    # --- Other episodes for same person (navigation) ---
    if person_eps.height > 1:
        st.subheader("Return Pattern")
        gaps = person_eps.filter(pl.col("gap_days").is_not_null()).get_column("gap_days").to_list()
        if gaps:
            st.caption(
                f"{len(gaps)} returns. Gaps: min {min(gaps)} days, median {sorted(gaps)[len(gaps)//2]} days, max {max(gaps)} days"
            )

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
    sort_cols = ["total_admissions", "recidivism_tier", "race", "first_admission", "last_admission", "avg_stay_days", "distinct_charges"]
    sort_col = st.selectbox("Sort by", sort_cols, index=0)
    sort_desc = st.checkbox("Descending", value=True)

    sorted_df = filtered.sort(sort_col, descending=sort_desc).head(500)
    display = sorted_df.select(
        "INMATEID", "total_admissions", "recidivism_tier", "race", "sex",
        pl.col("approx_birth_year").cast(pl.Int32, strict=False).alias("birth_year"),
        pl.col("first_admission").cast(pl.Utf8).str.slice(0, 10).alias("first_admission"),
        pl.col("last_admission").cast(pl.Utf8).str.slice(0, 10).alias("last_admission"),
        pl.col("avg_stay_days").round(0).cast(pl.Int32, strict=False).alias("avg_stay_days"),
        pl.col("first_known_charge").map_elements(charge_label, return_dtype=pl.Utf8).alias("first_charge"),
        "distinct_charges",
    )

    st.caption(f"Click a row to explore that person. Showing top 500 of {filtered.height:,}.")
    event = st.dataframe(
        display.to_pandas(),
        use_container_width=True,
        height=600,
        on_select="rerun",
        selection_mode="single-row",
    )
    if event.selection.rows:
        selected_id = display.row(event.selection.rows[0], named=True)["INMATEID"]
        st.session_state["explore_id"] = selected_id
        st.switch_page("Person Explorer") if hasattr(st, "switch_page") else None
        # Fallback: set state and tell user
        st.success(f"Selected {selected_id} — switch to **Person Explorer** in the sidebar.")
        st.session_state["explore_id"] = selected_id




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
