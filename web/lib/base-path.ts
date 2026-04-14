const rawBasePath = process.env.NEXT_PUBLIC_BASE_PATH ?? "";

export const BASE_PATH =
  rawBasePath && rawBasePath !== "/"
    ? rawBasePath.replace(/\/+$/, "")
    : "";

export function withBasePath(pathname: string): string {
  if (!pathname.startsWith("/")) {
    throw new Error(`Path must start with '/': ${pathname}`);
  }
  return BASE_PATH ? `${BASE_PATH}${pathname}` : pathname;
}
