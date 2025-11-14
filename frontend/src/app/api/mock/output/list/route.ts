import { NextResponse } from "next/server";

export async function GET() {
  return NextResponse.json({
    dirs: [
      { name: "docs", path: "docs" },
      { name: "refs", path: "refs" },
    ],
    files: [
      {
        name: "overview.md",
        path: "docs/overview.md",
        bytes: 12345,
      },
    ],
  });
}
