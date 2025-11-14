import Link from "next/link";
import { ArrowRight, Play, Waves } from "lucide-react";

const quickLinks = [
  {
    href: "/plan",
    title: "New Plan",
    description: "Estimate scope, risks, and guardrails before a run.",
    icon: <Waves className="h-5 w-5" aria-hidden="true" />,
  },
  {
    href: "/run",
    title: "Quick Run",
    description: "Launch with saved defaults and sensible safety limits.",
    icon: <Play className="h-5 w-5" aria-hidden="true" />,
  },
  {
    href: "/runs",
    title: "Run History",
    description: "Review the last 10 runs, status, warnings, and artifacts.",
    icon: <ArrowRight className="h-5 w-5" aria-hidden="true" />,
  },
];

export default function DashboardPage() {
  return (
    <div className="space-y-10">
      <header className="space-y-4">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-full bg-slate-900 text-white dark:bg-slate-100 dark:text-slate-900">
            <span className="text-xl font-semibold">WA</span>
          </div>
          <div>
            <h1 className="text-3xl font-semibold tracking-tight">WebArc Console</h1>
            <p className="text-sm text-muted-foreground">
              Plan, run, and review Markdown extraction jobs with guardrails.
            </p>
          </div>
        </div>
        <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-950">
          <p className="text-sm text-muted-foreground">
            This dashboard surfaces quick actions, recent runs, and global safety
            signals. Build out the supporting components under `components/`
            and wire them into live data.
          </p>
        </div>
      </header>

      <section>
        <h2 className="text-lg font-semibold">Get Started</h2>
        <div className="mt-4 grid gap-4 md:grid-cols-3">
          {quickLinks.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className="group flex flex-col rounded-xl border border-slate-200 bg-white p-5 shadow-sm transition hover:-translate-y-1 hover:shadow-lg dark:border-slate-800 dark:bg-slate-950"
            >
              <div className="flex h-10 w-10 items-center justify-center rounded-full bg-slate-900 text-white dark:bg-slate-100 dark:text-slate-900">
                {link.icon}
              </div>
              <h3 className="mt-4 text-base font-semibold">{link.title}</h3>
              <p className="mt-2 text-sm text-muted-foreground">
                {link.description}
              </p>
              <span className="mt-4 inline-flex items-center gap-2 text-sm font-medium text-slate-900 transition group-hover:gap-3 dark:text-slate-100">
                Open <ArrowRight className="h-4 w-4" aria-hidden="true" />
              </span>
            </Link>
          ))}
        </div>
      </section>

      <section>
        <div className="rounded-xl border border-dashed border-slate-300 p-6 text-sm text-muted-foreground dark:border-slate-700">
          <p>
            Next steps: add <code>RecentRunsTable</code>,
            <code>SafetyBanner</code>, and <code>RunSummaryCards</code> components
            here. Wire them to the backend via hooks in `lib/hooks`.
          </p>
        </div>
      </section>
    </div>
  );
}
