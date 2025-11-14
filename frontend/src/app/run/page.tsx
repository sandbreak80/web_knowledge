export default function RunPage() {
  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-semibold tracking-tight">Launch Run</h1>
        <p className="mt-2 max-w-2xl text-sm text-muted-foreground">
          Configure crawl parameters, output location, and guardrails before
          dispatching a run. This page will share the <code>RunForm</code>
          component with the plan view, toggled into run mode with additional
          budgets and output settings.
        </p>
      </div>
      <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-950">
        <p className="text-sm text-muted-foreground">
          Replace this placeholder with the interactive run form. For now the
          page highlights layout structure and copy.
        </p>
      </div>
      <div className="rounded-xl border border-dashed border-slate-300 p-6 text-sm text-muted-foreground dark:border-slate-700">
        <p>
          TODO: Surface validation errors, guardrail confirmations (robots,
          denylist), and a summary preview of the effective configuration before
          submission.
        </p>
      </div>
    </div>
  );
}
