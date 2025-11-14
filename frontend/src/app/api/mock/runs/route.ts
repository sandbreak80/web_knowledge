import { NextResponse } from "next/server";

const runs = [
  {
    id: "run_mock_001",
    status: "running",
    started_at: new Date().toISOString(),
    ended_at: null,
    seeds_count: 2,
    ok: 34,
    degraded: 4,
    failed: 1,
  },
  {
    id: "run_mock_000",
    status: "succeeded",
    started_at: new Date(Date.now() - 86_400_000).toISOString(),
    ended_at: new Date(Date.now() - 85_900_000).toISOString(),
    seeds_count: 1,
    ok: 128,
    degraded: 6,
    failed: 0,
  },
];

export async function GET() {
  return NextResponse.json({ runs });
}

export async function POST() {
  return NextResponse.json(
    { run_id: "run_mock_002", status: "queued" },
    { status: 202 },
  );
}
