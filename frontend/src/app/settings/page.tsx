export default function SettingsPage() {
  return (
    <div className="space-y-8">
      <header className="space-y-2">
        <h1 className="text-3xl font-semibold tracking-tight">Settings</h1>
        <p className="text-sm text-muted-foreground">
          Manage defaults, friendly names for profiles, local storage, and UI
          preferences. This section will evolve as backend capabilities land.
        </p>
      </header>
      <section className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-950">
        <h2 className="text-lg font-semibold">Environment</h2>
        <p className="mt-2 text-sm text-muted-foreground">
          TODO: Render backend URL, poll interval, SSE toggle, and adapter
          enablement states. Persist overrides to local storage.
        </p>
      </section>
      <section className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-950">
        <h2 className="text-lg font-semibold">Saved Profiles</h2>
        <p className="mt-2 text-sm text-muted-foreground">
          TODO: List stored crawl profiles, allow editing, duplication, and
          deletion.
        </p>
      </section>
    </div>
  );
}
