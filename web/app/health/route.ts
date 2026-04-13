import { NextResponse } from "next/server";
import { getDataDir, pq, query } from "@/lib/db";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

export async function GET() {
  try {
    await query<{ ok: number }>(
      `SELECT 1 as ok FROM '${pq("doc_recidivism_persons.parquet")}' LIMIT 1`
    );

    return NextResponse.json({
      ok: true,
      dataDir: getDataDir(),
    });
  } catch (error) {
    return NextResponse.json(
      {
        ok: false,
        dataDir: getDataDir(),
        error: error instanceof Error ? error.message : "Unknown error",
      },
      { status: 503 }
    );
  }
}
