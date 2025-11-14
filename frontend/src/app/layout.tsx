import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import Link from "next/link";
import "./globals.css";
import { ThemeProvider } from "@/components/theme-provider";
import { cn } from "@/lib/utils";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "WebArc Console",
  description: "Local-first UI for planning and monitoring WebArc crawls.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const navLinks = [
    { href: "/", label: "Dashboard" },
    { href: "/plan", label: "Plan" },
    { href: "/run", label: "Run" },
    { href: "/runs", label: "Runs" },
    { href: "/settings", label: "Settings" },
  ];

  return (
    <html lang="en" suppressHydrationWarning>
      <body
        className={cn(
          geistSans.variable,
          geistMono.variable,
          "min-h-screen bg-slate-50 text-slate-900 antialiased dark:bg-slate-950 dark:text-slate-100",
        )}
      >
        <ThemeProvider attribute="class" defaultTheme="system" enableSystem>
          <div className="flex min-h-screen flex-col">
            <header className="sticky top-0 z-40 border-b border-slate-200 bg-white/80 backdrop-blur dark:border-slate-800 dark:bg-slate-950/80">
              <div className="mx-auto flex w-full max-w-6xl items-center justify-between px-6 py-4">
                <Link href="/" className="flex items-center gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-slate-900 text-white dark:bg-slate-100 dark:text-slate-900">
                    <span className="text-lg font-semibold">WA</span>
                  </div>
                  <div className="hidden flex-col text-sm leading-tight sm:flex">
                    <span className="font-semibold">WebArc Console</span>
                    <span className="text-muted-foreground">
                      Local crawl orchestrator
                    </span>
                  </div>
                </Link>
                <nav className="flex items-center gap-6 text-sm font-medium text-muted-foreground">
                  {navLinks.map((link) => (
                    <Link
                      key={link.href}
                      href={link.href}
                      className="transition hover:text-slate-900 dark:hover:text-slate-100"
                    >
                      {link.label}
                    </Link>
                  ))}
                </nav>
              </div>
            </header>
            <main className="mx-auto w-full max-w-6xl flex-1 px-6 py-10">
              {children}
            </main>
            <footer className="border-t border-slate-200 bg-white py-6 text-center text-xs text-muted-foreground dark:border-slate-800 dark:bg-slate-950">
              WebArc MD — Frontend MVP · Built for local-first knowledge capture
            </footer>
          </div>
        </ThemeProvider>
      </body>
    </html>
  );
}
