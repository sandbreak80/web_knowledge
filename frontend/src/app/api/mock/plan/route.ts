import { NextResponse } from "next/server";

export async function POST() {
  return NextResponse.json({
    estimate: {
      total_pages: 124,
      by_domain: [{ domain: "docs.example.com", pages: 124 }],
    },
    sitemap_found: true,
    languages: [{ lang: "en", count: 124 }],
    versions: [{ version: "25.10.0", count: 124 }],
    risks: [
      {
        code: "ROBOTS_OK",
        level: "info",
        message: "robots.txt allows crawl",
      },
      {
        code: "VERSION_LOCK",
        level: "info",
        message: "version lock enabled",
      },
    ],
    plan_id: "plan_mock_001",
    effective_config: {
      seeds: ["https://docs.example.com/app"],
      version: { lock: true },
      crawl: { depth: 3, respect_robots: true },
    },
  });
}
