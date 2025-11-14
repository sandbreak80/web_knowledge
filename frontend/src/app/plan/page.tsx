import Link from "next/link";
import { Suspense } from "react";

export default function PlanPage() {
  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-semibold tracking-tight">New Plan</h1>
        <p className="mt-2 max-w-2xl text-sm text-muted-foreground">
          Submit one or more seed URLs to estimate scope, generate guardrails,
          and review risks before launching a crawl. The final UI will render a
          full form powered by `RunForm` with a plan-only submit button.
        </p>
      </div>
      <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_380px]">
        <section className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-950">
          <h2 className="text-lg font-semibold">Plan Configuration</h2>
          <p className="mt-2 text-sm text-muted-foreground">
            Replace this placeholder with the shared <code>RunForm</code>
            component (plan mode). Include seed textarea/upload, profiles, and
            advanced options.
          </p>
        </section>
        <aside className="space-y-6">
          <section className="rounded-xl border border-dashed border-slate-300 p-4 text-sm text-muted-foreground dark:border-slate-700">
            <p>
              Plan summary cards (estimated pages, sitemap discovery, languages,
              versions, risks) will render here once the API is connected.
            </p>
          </section>
          <section className="rounded-xl border border-dashed border-slate-300 p-4 text-sm text-muted-foreground dark:border-slate-700">
            <p>
              After plan success, surface a CTA to
              <Link href="/run" className="font-medium text-slate-900 dark:text-slate-100">
                &nbsp;Start Run with this configuration
              </Link>
              .
            </p>
          </section>
        </aside>
      </div>
      <Suspense fallback={null}>
        <section className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-950">
          <h3 className="text-base font-semibold">Plan History (Coming Soon)</h3>
          <p className="mt-2 text-sm text-muted-foreground">
            Wire this section to display recently generated plans and allow
            users to rehydrate configurations.
          </p>
        </section>
      </Suspense>
    </div>
  );
}
