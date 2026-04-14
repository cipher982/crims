import Link from "next/link";

export default function PersonNotFound() {
  return (
    <div className="drose-empty-state drose-panel">
      <div>
        <p className="drose-kicker">Lookup Failed</p>
        <h1 className="drose-page-title">Person Not Found</h1>
        <p className="drose-lead">
          That INMATEID doesn&apos;t exist in the dataset.
        </p>
      </div>
      <Link
        href="/search"
        className="drose-button drose-button-primary mt-6"
      >
        Search People
      </Link>
    </div>
  );
}
