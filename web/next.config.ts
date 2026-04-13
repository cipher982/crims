import type { NextConfig } from "next";

const basePath = process.env.NEXT_PUBLIC_BASE_PATH || "";

const nextConfig: NextConfig = {
  basePath,
  output: "standalone",
  serverExternalPackages: [
    "@duckdb/node-api",
    "@duckdb/node-bindings",
    "@duckdb/node-bindings-darwin-arm64",
    "@duckdb/node-bindings-darwin-x64",
    "@duckdb/node-bindings-linux-x64",
    "@duckdb/node-bindings-linux-arm64",
  ],
  outputFileTracingIncludes: {
    "/*": [
      "./node_modules/@duckdb/node-bindings/**/*",
      "./node_modules/@duckdb/node-bindings-darwin-arm64/**/*",
      "./node_modules/@duckdb/node-bindings-darwin-x64/**/*",
      "./node_modules/@duckdb/node-bindings-linux-x64/**/*",
      "./node_modules/@duckdb/node-bindings-linux-arm64/**/*",
    ],
  },
  turbopack: {
    root: __dirname,
  },
};

export default nextConfig;
