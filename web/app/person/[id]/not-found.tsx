import Link from "next/link";

export default function PersonNotFound() {
  return (
    <div className="flex flex-col items-center justify-center py-20">
      <h1 className="text-2xl font-bold text-gray-900">Person Not Found</h1>
      <p className="mt-2 text-gray-600">
        That INMATEID doesn&apos;t exist in the dataset.
      </p>
      <Link
        href="/search"
        className="mt-4 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
      >
        Search People
      </Link>
    </div>
  );
}
