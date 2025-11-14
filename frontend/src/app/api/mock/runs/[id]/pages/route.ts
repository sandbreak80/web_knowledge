import { NextResponse } from "next/server";

const items = Array.from({ length: 8 }).map((_, index) => ({
  url: `https://docs.example.com/page-${index + 1}`,
  http: 200,
  render: index % 3 === 0 ? "js" : "static",
  status: index % 5 === 0 ? "degraded" : "ok",
  reasons: index % 5 === 0 ? ["structure_loss"] : [],
  path: `docs/example/page-${index + 1}.md`,
}));

export async function GET() {
  return NextResponse.json({ total: 8, items });
}
