import { DuckDBInstance } from "@duckdb/node-api";
import path from "path";

const DATA_DIR = path.resolve(process.cwd(), "../data/derived");

let instance: DuckDBInstance | null = null;

async function getInstance(): Promise<DuckDBInstance> {
  if (!instance) {
    instance = await DuckDBInstance.create();
  }
  return instance;
}

export async function query<T = Record<string, unknown>>(
  sql: string
): Promise<T[]> {
  const db = await getInstance();
  const conn = await db.connect();
  try {
    const reader = await conn.runAndReadAll(sql);
    return reader.getRowObjectsJS().map((row) => normalizeRecord(row)) as T[];
  } finally {
    conn.closeSync();
  }
}

/** Resolve a parquet file path relative to data/derived/ */
export function pq(filename: string): string {
  return path.join(DATA_DIR, filename).replace(/'/g, "''");
}

function normalizeRecord(row: Record<string, unknown>): Record<string, unknown> {
  return Object.fromEntries(
    Object.entries(row).map(([key, value]) => [key, normalizeValue(value)])
  );
}

function normalizeValue(value: unknown): unknown {
  if (typeof value === "bigint") {
    const numberValue = Number(value);
    return Number.isSafeInteger(numberValue) ? numberValue : value.toString();
  }
  if (value instanceof Date) {
    return value.toISOString().slice(0, 10);
  }
  if (Array.isArray(value)) {
    return value.map((item) => normalizeValue(item));
  }
  if (value && typeof value === "object") {
    return Object.fromEntries(
      Object.entries(value).map(([key, item]) => [key, normalizeValue(item)])
    );
  }
  return value;
}
