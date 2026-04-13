import Link from "next/link";

export function Nav() {
  return (
    <nav className="sticky top-0 z-50 border-b border-gray-200 bg-white/80 backdrop-blur">
      <div className="mx-auto flex max-w-7xl items-center gap-6 px-4 py-3">
        <Link href="/" className="text-lg font-bold text-gray-900">
          NYC CJ Explorer
        </Link>
        <Link
          href="/search"
          className="text-sm font-medium text-gray-600 hover:text-gray-900"
        >
          Search People
        </Link>
        <Link
          href="/random-person"
          className="text-sm font-medium text-gray-600 hover:text-gray-900"
        >
          Random Person
        </Link>
      </div>
    </nav>
  );
}
