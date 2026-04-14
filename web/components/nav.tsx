import Link from "next/link";

export function Nav() {
  return (
    <div className="drose-nav-wrap">
      <nav className="drose-nav">
        <div className="drose-brand-block">
          <p className="drose-brand-kicker">David Rose / Public Research</p>
          <Link href="/" className="drose-brand">
            NYC Criminal Justice Explorer
          </Link>
          <p className="drose-brand-subtitle">
            Public NYC DOC recidivism explorer, person histories, and arrest bridge subset.
          </p>
        </div>

        <div className="drose-nav-links">
          <Link href="/" className="drose-nav-link">
            Overview
          </Link>
          <Link href="/search" className="drose-nav-link">
            Search People
          </Link>
          <Link href="/random-person" className="drose-nav-link">
            Random Person
          </Link>
        </div>
      </nav>
    </div>
  );
}
