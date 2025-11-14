Here’s a single, self-contained **Frontend Design + Build Spec (README.md)** you can hand to Cursor’s agent to build the MVP UI for your crawler. It assumes your crawler runs locally in Docker and exposes a simple HTTP API (defined below). The UI is opinionated: fast to build, easy for 500 SEs, and safe by default.

---

# WebArc MD — Frontend (MVP)

Local UI for crawling websites → **Obsidian-ready Markdown** with strong guardrails

## 0) Purpose & Non-Goals

**Purpose:** Give Sales Engineers a simple, local UI to:

* Configure a crawl (seed URLs, depth, allow/deny rules)
* Run **plan → sample → full crawl**
* Monitor progress and backoff/rate-limit behavior
* Review results (OK/Degraded/Failed), reasons, and reports
* Browse/download generated Markdown files and manifests

**Non-Goals (MVP):**

* No auth/SSO, no multi-user server. Local only.
* No vectorization/RAG indexing (out of scope).
* No scraping credentials or bypass of paywalls/CAPTCHAs.
* No social/e-commerce scraping helpers (blocklisted by default).

---

## 1) Target Runtime & Stack

* **Containerized app (docker-compose)**

  * `frontend`: Next.js 15 (App Router) + React 18 + TypeScript + Tailwind + shadcn/ui
  * `backend`: your existing crawler API (FastAPI/Flask) + Playwright deps (already built)
* **Local only** (bind to `127.0.0.1`, default port 5173 FE / 8000 BE)
* **Filesystem**: mount a host directory to backend `/out` and expose file listing via API

---

## 2) High-Level UX Flow

1. **Home / Dashboard**

   * Quick status: last run, page counts, failures, output folder
   * Buttons: **Plan**, **Sample**, **Full Run**, **Open Output Folder**

2. **New Crawl Wizard**

   * **Step 1 — Scope**: seeds (URL/list), depth, allow domains/prefixes, stay-in-domain toggle
   * **Step 2 — Safety**: respect robots, deny domains (preloaded), language lock, version lock, budgets (max pages/runtime), concurrency & delay (with warnings)
   * **Step 3 — Filters**: deny params (`utm_*`, `q`, `sort`, etc.), deny paths (`/search`, `/login`, …)
   * **Step 4 — Render & Adapters**: auto-detect adapters, JS fallback (max wait), wait selectors
   * **Step 5 — Review & Confirm**: risk summary (robots, sitemap found, estimated pages)

3. **Run View (live)**

   * Progress: processed/queued, per-host QPS, backoff events, 429/503 counters
   * Stream of events (deduped): warnings (version/language cross), blocks (external domain, deny rules), UUID/entropy stop triggers
   * Abort / Pause / Resume controls

4. **Results**

   * Tabs: **Pages**, **Failures**, **Degraded**, **Report**
   * Table with filters/search (status, host, adapter, size, reason)
   * Detail drawer: front-matter preview, reason text, quick link to open the MD file
   * Download: ZIP of `pages/`, `manifest.jsonl`, `graph.jsonl`, `report.md`

5. **Settings**

   * Default profile: **Conservative / Default / Wide**
   * Deny domains list (preloaded with Amazon/LinkedIn/X/Facebook/Reddit)
   * Pi-hole/StevenBlack hosts support (optional local file)—“load once”
   * User agent string, contact email (Org defaults but editable)
   * Output directory picker (host path -> mounted volume)

---

## 3) MVP Scope (Must/Should/Could)

**Must**

* Create/edit/save a crawl config (single JSON file)
* Plan → Sample (`N` pages) → Full crawl controls
* Live progress with backoff/rate-limit events
* Show final counts: OK/Degraded/Failed + top failure reasons
* Browse/download outputs; open file in system (where supported)
* Safety banners: robots on/off, risky domains blocked, version & language locks enabled
* Honest failures with reason text from backend

**Should**

* Profiles (Conservative/Default/Wide)
* Deny-domains preloaded; user can add/remove (local only)
* Load StevenBlack hosts file (optional): merge into deny-domains (UI toggle, off by default)
* Persist last 10 runs (local storage + backend `/runs` dir)

**Could (V2)**

* Per-site adapter preview (show detected framework)
* Side-by-side HTML → MD diff for a sample page
* Domain reputation check (corporate DNS or Umbrella verdict proxy if available)

---

## 4) API Contract (backend expected by frontend)

> If your backend already exists, align/extend to these endpoints. Otherwise, build these in FastAPI.

### 4.1 Configuration

* `GET /api/version` → `{ "backend":"webarc-md", "version":"0.4.0" }`
* `GET /api/defaults` → default config JSON
* `GET /api/profiles` → `{ "conservative": {...}, "default": {...}, "wide": {...} }`
* `POST /api/validate-config` (body: config JSON) → `{ "ok":true, "warnings":[...], "errors":[...] }`

### 4.2 Pre-Run

* `POST /api/plan` (body: config)
  Returns:

  ```json
  {
    "ok": true,
    "robots": {"respected": true, "notes": ["robots allows /appd/..."]},
    "sitemap": {"found": true, "urls": 412},
    "estimate": {"pages": 730, "depth": 3},
    "risks": ["version drift: /latest/", "cross-language links detected"],
    "deny_domains": ["amazon.com","linkedin.com",...]
  }
  ```

* `POST /api/sample?limit=10` (body: config) → starts a short run; returns `{"run_id":"..."}`

* `POST /api/run` (body: config) → starts full run; returns `{"run_id":"..."}`

* `GET /api/run/{run_id}/status` → live status:

  ```json
  {
    "state":"running", // idle|planning|sampling|running|paused|aborted|done|error
    "processed": 132,
    "queued": 88,
    "ok": 90, "degraded": 30, "failed": 12,
    "per_host": [{"host":"docs.appdynamics.com","qps":0.6,"concurrency":1}],
    "rate_limit": {"429":2,"503":1,"backoffs":4},
    "warnings": ["Cross-version URL blocked: /25.x/..."],
    "started_at":"...", "eta_sec": 420
  }
  ```

* `POST /api/run/{run_id}/pause|resume|abort` → `{ "ok": true }`

### 4.3 Results & Files

* `GET /api/run/{run_id}/summary` → counts, top reasons, adapter stats
* `GET /api/run/{run_id}/pages` → paged list:

  ```json
  {
    "items":[{"url":"...","status":"ok|degraded|failed","reason":null,"adapter":"confluence-viewport","size": 18342,"path": "pages/foo.md"}],
    "next_cursor":"..."
  }
  ```
* `GET /api/run/{run_id}/page?path=pages/foo.md` → returns Markdown (text)
* `GET /api/run/{run_id}/report` → `report.md` (text)
* `GET /api/run/{run_id}/download.zip` → ZIP (binary)
* `GET /api/runs` → recent runs metadata array
* `GET /api/output/list?path=/` → directory listing (recursive=false) for safe browsing

**Error format (all endpoints):**

```json
{ "ok": false, "error": { "code": "RobotsBlocked|ClientOnlyApp|UUIDExplosion|InvalidConfig|Internal", "message": "..." } }
```

---

## 5) Data Models (JSON Schemas, simplified)

```ts
// Config
type CrawlConfig = {
  run_name: string;
  seeds: string[];                     // URLs
  allow: { domains: string[]; prefixes: string[] };
  language: { target: "en"; allow_hreflang: boolean };
  version: { lock: boolean };
  crawl: { depth: number; max_pages: number; max_runtime_s: number; respect_robots: boolean; user_agent: string };
  throttle: { per_host_concurrency: number; delay_s: [number, number]; };
  render: { enable: boolean; auto_fallback: boolean; max_wait_s: number; wait_selectors: string[] };
  filters: { deny_params: string[]; deny_paths: string[]; external_follow: boolean };
  adapters: { auto_detect: boolean; enabled: string[] }; // e.g., "confluence-viewport","mkdocs"
  html2md: { preserve_tables: boolean; admonitions: boolean; code_fence_lang_guess: boolean };
  obsidian: { mode: "strict" | "loose" };
  budgets: { max_html_bytes: number };
  quality_thresholds: { min_text_chars: number; min_content_density: number; max_structure_loss_pct: number };
  deny_domains: string[];             // includes risky defaults
};
```

```ts
// PageItem
type PageItem = {
  url: string;
  status: "ok" | "degraded" | "failed";
  reason: string | null;
  adapter: string | "unknown";
  size: number;
  path: string;                        // relative path to markdown
  title?: string;
};
```

---

## 6) UI Screens & Components

**Global**

* **TopBar**: run picker, last status, Settings
* **DangerBanner**: shows robots off / risky domains allowed / external follow on
* **Toast/Toaster**: queue of warnings/errors

**Home**

* Cards: *New Crawl*, *Resume Last*, *Open Output*, *Recent Runs*

**New Crawl Wizard** (multi-step form)

* *ScopeForm*: `seeds[]`, `depth`, allow domain/prefix
* *SafetyForm*: robots toggle, deny domains (with defaults), language lock (select), version lock
* *BudgetsForm*: max pages/runtime, concurrency & delay sliders (with text warnings)
* *FiltersForm*: deny params/paths (tag inputs)
* *RenderForm*: auto-fallback, max wait, selectors (chips), adapters on/off
* *Review*: “Plan Summary” with computed risks

**Run View**

* **ProgressBar** with counts
* **PerHostStats** mini-cards
* **EventStream** (virtualized list)
* **Controls**: Pause/Resume/Abort

**Results**

* **PagesTable** (status, adapter, title, size) with filter chips and quick search
* **PageDrawer**: Markdown preview (monospace), front-matter snippet, open-in-file-system
* **ReportView**: render `report.md`

**Settings**

* **Profiles** selector: Conservative / Default / Wide
* **DenyDomainsEditor**: preloaded risky list; add/remove rows
* **Blocklist Import**: upload StevenBlack hosts file → parse → apply to deny-domains (off by default)
* **UserAgentEditor** and contact email
* **OutputPath** (host path mapping note)

---

## 7) Safety & “Built-in Intelligence” in UI

* **Robots**: default ON; turning OFF requires typing `YES` in a modal.
* **External links**: default OFF. If ON, show red banner and require allowlist domains.
* **Language lock**: default `en`; changing shows “language explosion” warning.
* **Version lock**: default ON if seed path contains a version segment.
* **Deny-domains**: prefill `[amazon.*, linkedin.com, facebook.com, instagram.com, twitter.com, x.com, reddit.com]` (editable)
* **Budget caps**: sensible defaults (max_pages 1000, runtime 3600s). Warn if exceeded.
* **Plan step** shows: robots status, sitemap presence, estimated page count, risky patterns (UUID/entropy), version/language drifts.

---

## 8) Accessibility, Perf, and Offline

* WCAG AA basics (labels, keyboard nav, focus states)
* No external CDNs (corporate laptop friendly)
* Cache last config and last 10 run summaries in browser localStorage
* Handle backend down: show reconnect & health check

---

## 9) Build & Run

**docker-compose.yml (concept)**

* `frontend` (Next.js) on `5173`, `BACKEND_URL=http://backend:8000`
* `backend` on `8000`, mounts `./out:/out`
* `network_mode: bridge`, publish `5173:5173`, `8000:8000` (optional)
* Non-root users in both containers

**Commands**

```bash
# Dev
docker compose up --build

# Open UI
http://localhost:5173
```

---

## 10) Acceptance Criteria (MVP)

1. Can create a config via Wizard and save it.
2. **Plan** produces a summary with robots/sitemap/estimate and risks.
3. **Sample (10)** runs and shows live status; results list shows 10 items across statuses.
4. **Full Run** can be started, paused, resumed, aborted.
5. Results tab lists pages with filters; clicking a row previews Markdown.
6. Report is viewable and downloadable; ZIP output works.
7. Safety banners reflect risky toggles; robots OFF requires confirmation.
8. Deny-domains list preloaded and editable; changes persist.
9. Works entirely offline (aside from target crawling), on a corporate laptop.

---

## 11) Test Plan (Playwright E2E)

* **Wizard happy path**: fill minimal config → plan → sample(3) → full run(quick mock) → verify counts and ZIP
* **Safety toggles**: robots OFF requires confirmation; external follow ON shows red banner
* **Deny-domains**: add `example.com`, ensure plan warns when seed is example.com
* **Results filters**: search by adapter/status; open file preview
* **Resume run**: start → pause → resume → done
* **Blocklist import**: upload StevenBlack hosts file; deny-domains grows; plan indicates blocks

*(During FE tests, stub backend responses with MSW or test endpoints.)*

---

## 12) Directory Structure (frontend)

```
/app
  /api (frontend BFF fetchers)
  /components
  /runs/[runId]/page
  /new (wizard steps)
  /settings
  /results
  /report
/lib (schemas, validators, types)
/styles (Tailwind)
```

---

## 13) Open Questions / Assumptions

* Backend supports chunked event streaming? (If yes, use SSE/WebSocket for live events; else poll `/status` every 2s.)
* Backend can serve files from `/out` safely (read-only)? (Assumed yes.)
* “Open in file system” action is limited to showing the path and copying it to clipboard (browser sandbox).

---

## 14) Future (Post-MVP)

* Adapter insight (detected framework, selector preview)
* Side-by-side HTML→MD diff for samples
* Policies: organization-managed profiles + deny lists
* Optional local Ollama augmentations (title/summary/tags) with clear separation from source truth
* Domain reputation hook (Umbrella verdict proxy or internal allowlist)

---

## 15) Copy & Guidance (UI microcopy)

* **Robots Warning:** “Respect robots is ON (recommended). Turning it OFF may violate site policies. Type YES to continue.”
* **External Follow Warning:** “Following external domains can explode scope and trigger rate limits. Keep OFF unless you explicitly allow a short list.”
* **Language Lock Note:** “Locking to one language prevents 10× page explosions from hreflang variants.”
* **Version Lock Note:** “Pinned to version branch from seed (recommended for reproducible knowledge bases).”

---

## 16) Definition of Done

* Runs via `docker compose up` on a corporate laptop (no external CDNs).
* All acceptance tests pass locally with mocked backend.
* Manual test against a small docs site (e.g., 3–10 pages) shows end-to-end: config → plan → sample → run → browse → zip download.

---

## 17) Implementation To-Do (Engineering Checklist)

### Foundation & Tooling
- [ ] Scaffold `frontend/` Next.js 15 project (TS, Tailwind, shadcn/ui) with lint/format scripts.
- [ ] Extend `docker-compose.yml` with `frontend` service, shared network, mounted `/out`, and `BACKEND_URL` env.
- [ ] Create shared type definitions (`lib/types.ts`) for configs, run status, page items.

### API Client Layer
- [ ] Implement REST fetchers for `/api/version`, `/api/defaults`, `/api/profiles`, `/api/validate-config`.
- [ ] Implement crawl endpoints: `/api/plan`, `/api/sample`, `/api/run`, `/api/run/{id}/status|pause|resume|abort`.
- [ ] Implement results/file endpoints: `/api/run/{id}/summary|pages|page|report|download.zip`, `/api/runs`, `/api/output/list`.
- [ ] Provide mock handlers (MSW or local fixtures) to simulate backend during development/tests.

### UI Screens
- [ ] Home dashboard with quick actions, recent runs, safety banners.
- [ ] Crawl wizard (`/new`) with Scope → Safety → Filters → Render → Review steps, validation, draft persistence.
- [ ] Run view (`/runs/[id]`) showing progress, per-host stats, event log, pause/resume/abort.
- [ ] Results view with filterable table, Markdown preview drawer, download actions.
- [ ] Report tab rendering `report.md` and exposing ZIP/manifest downloads.
- [ ] Settings page with profiles, deny-domain editor, blocklist import, UA/contact, output path.

### Shared Components & State
- [ ] Build SafetyBanner, ConfirmationModal, WizardStepper, MarkdownPreview, EventLog (virtualized).
- [ ] Set up Zustand/Context store for active run monitoring and polling lifecycle.
- [ ] Cache last-used config and recent runs in localStorage with hydration on load.

### Testing & QA
- [ ] Unit tests for client/helpers (config normalization, risk summarizer).
- [ ] Playwright E2E flows: wizard happy path, safety toggles, run resume, results filter, blocklist import.
- [ ] CI job running lint, type-check, and Playwright against mocked backend.

### Documentation & Hand-off
- [ ] Update root README with frontend setup (`docker compose up`, env vars, mock mode).
- [ ] Note API expectations and any backend gaps discovered during implementation.
- [ ] File follow-up tickets for stretch items (SSE, adapter insights, diff view).

---

This spec is designed so an AI coding agent can build the frontend **autonomously** and integrate with your existing backend. If your backend diverges, align it to the API contract above or add a small BFF layer in the frontend to adapt.
