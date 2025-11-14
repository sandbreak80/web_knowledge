import { NextResponse } from "next/server";

const progress = {
  fetched: 64,
  ok: 52,
  degraded: 8,
  failed: 4,
};

export async function GET() {
  return NextResponse.json({
    id: "run_mock_001",
    status: "running",
    progress,
    elapsed_s: 420,
    hosts: [{ domain: "docs.example.com", qps: 0.7, concurrency: 2 }],
    throttle: { backoff: false, recent_429: 0 },
    warnings: [{ code: "UUID_EXPLOSION", count: 2 }],
    quality: { density_fail: 4, structure_loss: 1 },
  });
}
