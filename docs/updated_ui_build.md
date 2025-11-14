Here’s a single, self-contained **README.md** you can hand to Cursor’s agent to build the **front end** for your local crawler (the Markdown extractor). It assumes your backend already roughly follows the MVP we outlined (Scrapy + adapters + Obsidian-MD output). The spec gives the AI everything it needs: product scope, UX flows, wireframe descriptions, API contracts, types, state machines, build/run steps, test plan, and quality bars.

---

# WebArc MD — Frontend (MVP)

A local-first web UI to plan, run, and review web → Markdown extraction jobs. Designed for **corporate laptops in Docker**, used by up to 500 SEs. The frontend is a **Next.js** app (TypeScript, Tailwind, shadcn/ui) hitting a local backend over HTTP on `localhost`.

> Scope: **Read-only UI + job orchestration**. No raw scraping logic in the UI.
> Output targets **Obsidian-ready Markdown** plus manifest and link graph.

---

## 0) Goals & Non-Goals

### Goals

* Friendly UI to:

  * Plan a crawl (estimate scope, show risks).
  * Launch a run with sane defaults and guardrails.
  * Stream/refresh status & logs in near-real time.
  * Browse output (folders, pages), preview Markdown, download archives.
  * Review quality gates, warnings, and failure reasons.
* Keep users polite by default (robots, throttling, domain/version/language locks).
* No auth or external services required.

### Non-Goals (MVP)

* No account system or multi-tenant backends.
* No social/e-commerce scraping helpers (block by default).
* No PDF/PPT extraction in this UI (text-HTML only).
* No embedding/indexing/RAG—**extraction only**.

---

## 1) Architecture

**Next.js 14 (App Router) + React 18**

* UI components: **shadcn/ui**
* Styling: **TailwindCSS**
* Charts: *none for MVP* (simple counts/cards)
* Markdown preview: `react-markdown` + `rehype-raw` *off* (security), `rehype-slug`
* HTTP client: `fetch` with abort controllers
* Live updates: **polling every 2s** to start; optional **SSE** toggle if backend supports it
* Build target: **Docker** (node:20-alpine) → static served by Next server in the same container as backend or separate

**Assumptions**

* Backend listens at `http://localhost:7777` (configurable).
* Backend exposes the routes defined in **Section 4**.
* Files written to a host-mounted `/out` directory; backend exposes browse endpoints.

---

## 2) UX Overview (pages & flows)

### A. Dashboard `/`

* **Cards**: “New Plan”, “Quick Run”, “Recent Runs (10)”
* **Recent Runs table**: id, status, seeds count, pages_ok/degraded/failed, start/end time, actions (View | Download | Delete*)

  * Delete is **optional**; if not supported, hide
* **Global Warnings**: Robots policy on/off, risky domains blocked, network backoff active

### B. New Plan `/plan`

Form:

* **Seeds**: textarea (one URL per line) or upload seeds.txt
* **Profiles** (radio): *Default*, *Conservative*, *Wide*
* Advanced (accordion):

  * Allow domains (csv)
  * Path prefixes
  * Depth (1–6)
  * Target language (default: `en`)
  * Version lock (on)
  * Respect robots (on)
  * Max pages per host / total
  * Deny domains (prepopulated with ecommerce/social)
  * JS fallback (auto)
    Buttons:
* **Run Plan** → calls `POST /api/plan`
  Plan Results:
* Estimated pages by domain/prefix
* Found sitemap? yes/no
* Detected languages/versions (top 3)
* Risk report (see Section 6)
* CTA: **Start Run with this Plan** (prefills Run form)

### C. New Run `/run`

* Same form as Plan but adds:

  * **Run name** (optional)
  * **Output directory** (default: `/out/<slug-of-first-seed>_<timestamp>`)
  * **Budgets**: runtime, pages, bytes
* Submit → `POST /api/runs`
* Redirect to `/runs/:id`

### D. Run Detail `/runs/:id`

* **Header**: status badge (queued/running/paused/succeeded/degraded/failed/aborted), seeds, host(s)
* **Progress**: count of fetched / ok / degraded / failed, elapsed time
* **Live Log**: tail of last N lines (`GET /api/runs/:id/logs?tail=200`)
* **Quality Summary**: density failures, structure loss, cross-version/language blocks
* **Controls**: Pause/Resume, Abort (if supported)
* **Tabs**:

  * **Pages** (table): url, http, render(static/js), status(ok/degraded/failed), reasons, open preview
  * **Warnings**: deduped reasons (UUID explosion, robots blocked, param explosion, etc.) with counts + sample URLs
  * **Config**: effective config snapshot
  * **Artifacts**: download `manifest.jsonl`, `graph.jsonl`, `.zip` of `.md` files

### E. Output Browser `/runs/:id/output`

* Left panel: **folder tree** under output dir (lazy loaded)
* Right panel: **file list** and **preview**
* **Markdown preview**: front-matter rendered as a summary card; body preview; copy and download buttons
* **Search**: client-side filename search; (stretch: simple full-text over `.md` bodies with server help)

---

## 3) Component Inventory

* `RunForm` (shared by Plan & Run)
* `PlanSummary`
* `RunHeader`, `RunProgress`, `RunControls`
* `LiveLog`
* `PagesTable`
* `WarningsPanel`
* `ConfigViewer` (JSON viewer with collapse)
* `ArtifactsPanel`
* `OutputTree`, `OutputFileList`, `MarkdownPreview`
* `DomainRiskBanner` (robots, denylist, throttle notices)
* `ConfirmDialog` (abort/ignore robots confirmations)
* `Toaster` (notifications)

---

## 4) Backend API Contract (Frontend Expectations)

> If your backend differs, add a BFF layer in `/app/api/*` to adapt.

### Planning

* `POST /api/plan`

  * Body:

    ```json
    {
      "seeds": ["https://docs.appdynamics.com/appd/24.x/latest/en/splunk-appdynamics-essentials"],
      "allow": { "domains": ["docs.appdynamics.com"], "prefixes": ["/appd/24.x/"] },
      "depth": 3,
      "language": { "target": "en" },
      "version": { "lock": true },
      "crawl": { "respect_robots": true, "max_pages": 1000, "max_runtime_s": 3600 },
      "throttle": { "per_host_concurrency": 2, "delay_s": [0.7,1.5] },
      "render": { "enable": true, "auto_fallback": true, "max_wait_s": 10 },
      "filters": { "deny_params": ["utm_*","fbclid","gclid","session"], "deny_paths": ["/search","/login"] }
    }
    ```
  * 200 Response:

    ```json
    {
      "estimate": { "total_pages": 124, "by_domain": [{"domain":"docs.appdynamics.com","pages":124}] },
      "sitemap_found": true,
      "languages": [{"lang":"en","count":124}],
      "versions": [{"version":"24.x","count":124}],
      "risks": [
        {"code":"ROBOTS_OK","level":"info","message":"robots.txt allows crawl"},
        {"code":"VERSION_LOCK","level":"info","message":"version lock enabled"}
      ],
      "plan_id":"plan_20251112_103015",
      "effective_config": { ... }   // backend-resolved config
    }
    ```

### Runs

* `POST /api/runs`

  * Body: same as `/api/plan` plus `run_name`, `output_dir` (optional)
  * 202 Response:

    ```json
    { "run_id":"run_20251112_103045", "status":"queued" }
    ```

* `GET /api/runs?limit=10`

  ```json
  { "runs":[
    {"id":"run_...","status":"running","started_at":"...","ended_at":null,
     "seeds_count":1,"ok":34,"degraded":4,"failed":1}
  ]}
  ```

* `GET /api/runs/:id/status`

  ```json
  {
    "id":"run_...",
    "status":"running",
    "progress":{"fetched":120,"ok":98,"degraded":14,"failed":8},
    "elapsed_s": 420,
    "hosts":[{"domain":"docs.appdynamics.com","qps":0.7,"concurrency":2}],
    "throttle":{"backoff":false,"recent_429":0},
    "warnings":[{"code":"UUID_EXPLOSION","count":3}],
    "quality":{"density_fail":4,"structure_loss":2}
  }
  ```

* `GET /api/runs/:id/logs?tail=200` → `{ "lines": ["[10:30:12] ...", "..."] }`

* `POST /api/runs/:id/control`

  * Body: `{ "action":"pause"|"resume"|"abort" }`
  * 200 Response: `{ "status":"paused" }`

* **(Optional SSE)** `GET /api/runs/:id/events`
  Event types: `status`, `log`, `warning`, `page` (include minimal payloads).

### Pages & Output

* `GET /api/runs/:id/pages?status=all|ok|degraded|failed&offset=0&limit=100`

  ```json
  { "total": 123, "items":[
    {"url":"https://...","http":200,"render":"static","status":"ok","reasons":[],"path":"vendor/appdynamics/v=24.x/page.md"}
  ]}
  ```

* `GET /api/output/list?root=/out/run_.../pages&path=vendor/appdynamics/v=24.x`

  ```json
  { "dirs":[{"name":"v=24.x","path":"vendor/appdynamics/v=24.x"}],
    "files":[{"name":"splunk-appdynamics-essentials.md","path":"vendor/appdynamics/v=24.x/splunk-appdynamics-essentials.md","bytes":13452}] }
  ```

* `GET /api/output/page?root=/out/run_.../pages&path=vendor/appdynamics/v=24.x/splunk-appd.md`

  ```json
  { "front_matter": { "title":"...", "source_url":"...", "quality": {...} },
    "body_md": "## Heading\nContent..." }
  ```

* `GET /api/runs/:id/artifacts/manifest` → stream `manifest.jsonl`

* `GET /api/runs/:id/artifacts/graph` → stream `graph.jsonl`

* `GET /api/runs/:id/artifacts/zip` → stream `.zip` of `.md`

---

## 5) Data Models (TypeScript)

```ts
export type RiskLevel = "info" | "warn" | "error";
export type RunStatus = "queued" | "running" | "paused" | "succeeded" | "degraded" | "failed" | "aborted";

export interface PlanRequest { /* same as /api/plan body */ }
export interface PlanResponse {
  estimate: { total_pages: number; by_domain: {domain:string; pages:number}[] };
  sitemap_found: boolean;
  languages: { lang:string; count:number }[];
  versions: { version:string; count:number }[];
  risks: { code:string; level:RiskLevel; message:string }[];
  plan_id: string;
  effective_config: Record<string, unknown>;
}

export interface RunSummary {
  id: string;
  status: RunStatus;
  started_at: string | null;
  ended_at: string | null;
  seeds_count: number;
  ok: number; degraded: number; failed: number;
}

export interface RunStatusResponse {
  id: string; status: RunStatus;
  progress: { fetched:number; ok:number; degraded:number; failed:number };
  elapsed_s: number;
  hosts: { domain:string; qps:number; concurrency:number }[];
  throttle: { backoff:boolean; recent_429:number };
  warnings: { code:string; count:number }[];
  quality: { density_fail:number; structure_loss:number };
}

export type PageStatus = "ok" | "degraded" | "failed";
export interface PageItem {
  url: string; http: number; render: "static" | "js";
  status: PageStatus; reasons: string[]; path: string;
}

export interface OutputListing {
  dirs: { name: string; path: string }[];
  files: { name: string; path: string; bytes: number }[];
}

export interface MdPageResponse {
  front_matter: Record<string, unknown>;
  body_md: string;
}
```

---

## 6) Built-in Safety & “Intelligence” (Frontend Behaviors)

* **Robots & TOS banner**: If `respect_robots = false`, show **red banner** with “Are you sure?” and a link to robots.txt.
* **Denylist awareness**: If any seed domain matches the denylist (e.g., amazon/linkedin/reddit/x/facebook), require user confirmation; default block with explanation.
* **Language lock reminder**: If plan detects >1 language and target ≠ majority, prompt to pin a single language.
* **Version drift reminder**: If seed uses `/latest/`, warn and suggest pin to versioned path; quick action: “Rewrite to pinned version”.
* **Rate-limit hints**: If `/status` reports backoff, display “We slowed the crawl due to 429/503; estimated time increases”.
* **UUID/entropy explosion**: If backend warns `UUID_EXPLOSION`/`PARAM_EXPLOSION`, surface with human-friendly text and one-click “Reduce depth” or “Add deny param”.

---

## 7) UI Wireframe Notes (textual)

* **Dashboard**: three cards on top row, recent runs table below. Right sidebar “safety status” (robots on/off, denylist).
* **Plan**: form left; results right after submit. Risk list is a stacked list with badges (info/warn/error).
* **Run Detail**: header strip (status, controls), then two columns: left = progress tiles + LiveLog; right = Tabs (Pages, Warnings, Config, Artifacts).
* **Output**: resizable left tree, right file list + Markdown preview; front-matter shown in a data card (title, url, version, quality).

---

## 8) State Machines (key views)

**Run lifecycle**

```
QUEUED -> RUNNING -> (PAUSED -> RUNNING) -> (SUCCEEDED | DEGRADED | FAILED | ABORTED)
```

**Polling**

* Start poll on mount (2s).
* Stop poll when terminal status or on tab hidden (optional).
* SSE: if available, disable poll and subscribe to events; retry with backoff on disconnect.

---

## 9) Error Handling & Empty States

* Network errors → toast + retry button on each panel.
* Empty lists (no runs, no pages) → friendly “Nothing yet” states.
* 4xx from backend → inline hints (e.g., invalid seed URL).
* 5xx → “Backend busy; try again” + link to logs.

---

## 10) Accessibility & i18n

* All interactive elements keyboard accessible; focus rings on.
* `aria-live="polite"` on status numbers.
* Color usage not sole conveyor of meaning (status badges include icons + labels).
* English only for MVP; strings centralized for future i18n.

---

## 11) Security

* Frontend runs on `localhost` only; no external calls.
* Do **not** render raw HTML in Markdown preview (`rehype-raw` off).
* Sanitize file paths from query params before calling output endpoints.
* No credentials stored; per-run config stored transiently (optional localStorage for last form values).

---

## 12) Performance

* Virtualized tables for large page lists (>1k).
* Debounced search in Output Browser.
* Chunked log tail fetch (tail=200 default).

---

## 13) Configuration (env)

* `NEXT_PUBLIC_BACKEND_URL` (default `http://localhost:7777`)
* `NEXT_PUBLIC_POLL_INTERVAL_MS` (default `2000`)
* `NEXT_PUBLIC_SSE_ENABLED` (default `false`)

---

## 14) Project Structure

```
webapp/
  app/
    layout.tsx
    page.tsx                 # Dashboard
    plan/page.tsx
    run/page.tsx             # New Run (shares RunForm)
    runs/[id]/page.tsx       # Run detail
    runs/[id]/output/page.tsx
    api/                     # (optional BFF shims if backend differs)
  components/
    RunForm.tsx
    PlanSummary.tsx
    RunHeader.tsx
    RunProgress.tsx
    RunControls.tsx
    LiveLog.tsx
    PagesTable.tsx
    WarningsPanel.tsx
    ConfigViewer.tsx
    ArtifactsPanel.tsx
    OutputTree.tsx
    OutputFileList.tsx
    MarkdownPreview.tsx
    DomainRiskBanner.tsx
  lib/
    api.ts                   # typed fetch wrappers
    types.ts
    sse.ts                   # optional SSE helper
    utils.ts
  styles/
    globals.css
  test/
    e2e/ (Playwright)
    unit/ (Vitest)
  tailwind.config.ts
  package.json
  README.md (this file)
  Dockerfile
```

---

## 15) Implementation Notes

### API client (`lib/api.ts`)

* Wrap `fetch` with:

  * base URL from env
  * timeout via `AbortController`
  * JSON parsing with narrow types
  * utilities: `getPlan`, `postRun`, `getRunStatus`, `getRunLogs`, `listPages`, `listOutput`, `getMdPage`, `getArtifacts`

### LiveLog

* Poll `/logs?tail=200`; append diff only; auto-scroll when near bottom.

### MarkdownPreview

* Show **front-matter card** (selected common fields): title, source_url, version, quality.status, counts.
* Render body with `react-markdown`; plugins: `remark-gfm`, `rehype-slug`; **no raw HTML**.

### PagesTable

* Server-side pagination (offset/limit)
* Filters: status, render mode
* “Open in preview” button

### OutputTree

* Request children from `/api/output/list` lazily; maintain expanded nodes in state.

---

## 16) Quality Bars (Definition of Done)

* **Functional**

  * Can execute Plan and show estimates/risks.
  * Can start a Run and see live progress/logs.
  * Can list pages with statuses and reasons.
  * Can browse output directories and preview `.md`.
  * Can download `manifest.jsonl`, `graph.jsonl`, and `.zip`.

* **Safety**

  * Robots off → banner & confirmation.
  * Seeds in denylist → confirmation.
  * Latest version → warning to pin.

* **UX**

  * Responsive layout; usable at 1280×800.
  * Accessible controls; keyboard nav; focus states present.

* **Reliability**

  * Polling survives transient 5xx; UI resumes.
  * SSE (if enabled) auto-reconnect with backoff.

---

## 17) Tests (Playwright + Vitest)

**E2E (Playwright)**

* Plan → shows estimate and risks
* Run → transitions queued→running; logs appear
* Output browser → open a known `.md`, front-matter visible
* Warnings tab lists UUID explosion when backend fixture set
* Robots-off confirmation flow blocks until confirmed

**Unit (Vitest)**

* `api.ts` functions parse sample payloads
* `MarkdownPreview` renders front-matter summary safely
* `DomainRiskBanner` logic

---

## 18) Build & Run

### Dev

```bash
pnpm i
pnpm dev
# expects backend at http://localhost:7777
```

### Docker (frontend only)

`Dockerfile`:

```dockerfile
FROM node:20-alpine AS deps
WORKDIR /app
COPY package.json pnpm-lock.yaml ./
RUN corepack enable && pnpm i --frozen-lockfile

FROM node:20-alpine AS build
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN pnpm build

FROM node:20-alpine AS run
WORKDIR /app
ENV NODE_ENV=production
COPY --from=build /app/.next ./.next
COPY --from=build /app/public ./public
COPY package.json pnpm-lock.yaml ./
COPY --from=deps /app/node_modules ./node_modules
EXPOSE 3000
CMD ["pnpm","start"]
```

Run:

```bash
docker build -t webarc-frontend .
docker run --rm -p 3000:3000 \
  -e NEXT_PUBLIC_BACKEND_URL=http://host.docker.internal:7777 \
  webarc-frontend
```

*(If backend and frontend share a docker-compose, set service-to-service URL.)*

---

## 19) Roadmap (Post-MVP)

* SSE event stream as default; fall back to polling.
* Simple **full-text search** over `.md` bodies (server-side).
* Output diff view between runs (changed/added/removed pages).
* Per-site adapter docs (show which adapter handled a page).
* Optional Ollama augmentation toggle and job queue.
* User-export of a “run report” Markdown.

---

## 20) Open Questions for Backend (flag before coding)

1. Are `/api/output/*` endpoints guaranteed read-only with path sanitization?
2. What’s the max payload size for `/pages` listing (we’ll paginate by 100)?
3. Will `/status` include per-host backoff info and recent 429 counts (for UX hints)?
4. Do you want frontend to offer **Abort** and **Pause/Resume** controls now or hide until implemented?
5. Can backend provide **effective_config** snapshot for each run (for the Config tab)?

---

## 21) Sample Fixtures (for local UI dev without backend)

Place under `webapp/app/api/mock/*.json` for mock mode.

* `plan.response.json` — sample estimate with risks
* `runs.list.json` — 3 runs (running, degraded, succeeded)
* `runs.status.json` — progress numbers + warnings
* `runs.pages.json` — 100 fake pages with mixed statuses
* `output.list.json` — tree listing
* `output.page.json` — front-matter + body_md sample

Enable mock via env: `NEXT_PUBLIC_BACKEND_URL=/api/mock` and ship minimal Next route handlers that serve these JSONs.

---

## 22) Styling Guidelines

* **Cards** with soft shadows, rounded-2xl
* Clear status colors + icons (✅ ok, ⚠️ degraded, ❌ failed)
* Monospace font for logs
* Use `Dialog` for confirmations; `Toast` for transient notices
* Avoid dense tables; keep 12–16px padding

---

**This spec is sufficient for an AI coding agent to scaffold and build the entire frontend MVP**, with graceful fallbacks if the backend is partially stubbed. If your backend deviates from Section 4, add a tiny BFF under `/app/api/*` to normalize responses to the contracts above.
