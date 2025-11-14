import Link from "next/link";

const placeholderRuns = [
  {
    id: "run_20251112_103045",
    status: "running",
    started_at: "2025-11-12T10:30:45Z",
    seeds_count: 2,
    ok: 34,
    degraded: 4,
    failed: 1,
  },
];

export default function RunsPage() {
  return (
    <div className="space-y-8">
      <header className="space-y-2">
        <h1 className="text-3xl font-semibold tracking-tight">Run History</h1>
        <p className="text-sm text-muted-foreground">
          Browse recent runs, monitor current progress, and quickly jump into
          details. Replace the placeholder data with the `useRuns` hook wired to
          `/api/runs?limit=10`.
        </p>
      </header>
      <div className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm dark:border-slate-800 dark:bg-slate-950">
        <table className="min-w-full divide-y divide-slate-200 text-sm dark:divide-slate-800">
          <thead className="bg-slate-50 dark:bg-slate-900/40">
            <tr>
              <th className="px-4 py-3 text-left font-medium">Run ID</th>
              <th className="px-4 py-3 text-left font-medium">Status</th>
              <th className="px-4 py-3 text-left font-medium">Seeds</th>
              <th className="px-4 py-3 text-left font-medium">OK</th>
              <th className="px-4 py-3 text-left font-medium">Degraded</th>
              <th className="px-4 py-3 text-left font-medium">Failed</th>
              <th className="px-4 py-3 text-left font-medium">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-200 dark:divide-slate-800">
            {placeholderRuns.map((run) => (
              <tr key={run.id} className="bg-white dark:bg-slate-950">
                <td className="px-4 py-3 font-mono text-xs sm:text-sm">
                  {run.id}
                </td>
                <td className="px-4 py-3 capitalize">{run.status}</td>
                <td className="px-4 py-3">{run.seeds_count}</td>
                <td className="px-4 py-3">{run.ok}</td>
                <td className="px-4 py-3">{run.degraded}</td>
                <td className="px-4 py-3">{run.failed}</td>
                <td className="px-4 py-3">
                  <Link
                    href={`/runs/${run.id}`}
                    className="text-sm font-medium text-blue-600 hover:underline dark:text-blue-400"
                  >
                    View
                  </Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="rounded-xl border border-dashed border-slate-300 p-6 text-sm text-muted-foreground dark:border-slate-700">
        <p>
          TODO: Implement virtualized table for large histories, status filters,
          and run deletion once backend supports it.
        </p>
      </div>
    </div>
  );
}
