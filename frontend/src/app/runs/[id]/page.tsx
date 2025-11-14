import { notFound } from "next/navigation";

interface RunDetailPageProps {
  params: { id: string };
}

export default function RunDetailPage({ params }: RunDetailPageProps) {
  const { id } = params;

  if (!id) {
    notFound();
  }

  return (
    <div className="space-y-8">
      <header className="space-y-2">
        <h1 className="text-3xl font-semibold tracking-tight">Run {id}</h1>
        <p className="text-sm text-muted-foreground">
          Live status, logs, quality signals, and artifacts will render here.
          Replace placeholders with data hooks once the backend endpoints are
          wired up.
        </p>
      </header>
      <section className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_380px]">
        <div className="space-y-6">
          <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-950">
            <h2 className="text-lg font-semibold">Progress Overview</h2>
            <p className="mt-2 text-sm text-muted-foreground">
              TODO: Render progress tiles, host stats, and guardrail banners.
            </p>
          </div>
          <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-950">
            <h2 className="text-lg font-semibold">Live Log</h2>
            <div className="mt-4 h-64 overflow-auto rounded-lg bg-slate-900 p-4 font-mono text-xs text-slate-100">
              <p>10:30:12 [info] Bootstrapping crawl process…</p>
              <p>10:30:13 [info] Enqueued 2 seed URLs</p>
              <p>10:30:20 [warn] robots denied https://example.com/search</p>
            </div>
          </div>
          <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-950">
            <h2 className="text-lg font-semibold">Tabs</h2>
            <p className="mt-2 text-sm text-muted-foreground">
              Tabs for Pages, Warnings, Config, and Artifacts will live here
              using `@/components` panels.
            </p>
          </div>
        </div>
        <aside className="space-y-6">
          <div className="rounded-xl border border-dashed border-slate-300 p-5 text-sm text-muted-foreground dark:border-slate-700">
            TODO: Add run controls (Pause/Resume/Abort) and quality summary.
          </div>
          <div className="rounded-xl border border-dashed border-slate-300 p-5 text-sm text-muted-foreground dark:border-slate-700">
            TODO: Show effective configuration JSON viewer.
          </div>
        </aside>
      </section>
      <section className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-950">
        <h2 className="text-lg font-semibold">Output Preview</h2>
        <p className="mt-2 text-sm text-muted-foreground">
          Provide a quick link to the output browser and highlight the latest
          successful Markdown page.
        </p>
      </section>
    </div>
  );
}
