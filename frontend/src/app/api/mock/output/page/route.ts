import { NextResponse } from "next/server";

export async function GET() {
  return NextResponse.json({
    front_matter: {
      title: "Mock Page",
      source_url: "https://docs.example.com/mock",
      quality: { status: "ok" },
    },
    body_md: "## Mock Content\n\nThis is a placeholder body for local UI development.",
  });
}
