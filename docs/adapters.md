# WebArc Adapter Enhancement Requirements

## Objective
Extend WebArc to support crawling of additional site types, validating support for 7 specific test URLs with 2-level depth extraction.

## Test Sites & Required Adapters

### 1. AppDynamics Documentation ✅ ALREADY SUPPORTED
**URL:** https://docs.appdynamics.com/appd/24.x/latest/en/splunk-appdynamics-essentials/splunk-appdynamics-concepts
**Type:** Confluence/Scroll Viewport (SSR)
**Adapter:** ✅ ConfluenceAdapter (already exists)
**Status:** Should work out-of-box

### 2. Splunk Help Documentation ✅ SUPPORTED (JS REQUIRED)
**URL:** https://help.splunk.com/en/appdynamics-saas/application-performance-monitoring/25.10.0/application-monitoring
**Type:** Client-rendered SPA shell
**Adapter:** GenericAdapter after Playwright render
**Status:** Works when crawling with JS rendering (`--force-js` or automatic detection)

### 3. Cheryl's Caramels ✅ NEW ADAPTER
**URL:** https://cherylscaramels.com/
**Type:** Squarespace (heavily client-rendered)
**Adapter:** ✅ SquarespaceAdapter
**Challenges:**
- Dynamic divs, client-side rendering
- Requires Playwright for JS execution
- Not ideal for bulk crawling
**Implementation:** `webarc/adapters/squarespace.py`

### 4. NPR News ✅ NEW ADAPTER
**URL:** https://www.npr.org/sections/news/
**Type:** News/Article site (SSR)
**Adapter:** ✅ NewsAdapter
**Status:** Extracts `<article>` content, strips share widgets/ads

### 5. Reddit ✅ NEW ADAPTER
**URL:** https://www.reddit.com/r/homelab/
**Type:** Reddit (mixed SSR + client-rendering)
**Adapter:** ✅ RedditAdapter
**Best Practice:** Use JSON API instead of HTML scraping
- Public API: `https://www.reddit.com/r/{sub}.json`
- Comment threads: `https://www.reddit.com/r/{sub}/comments/{id}.json`
**Implementation:** `webarc/adapters/reddit.py`

### 6. X/Twitter 🚫 OUT OF SCOPE
**URL:** https://x.com/explore
**Type:** Social media (login wall, dynamic API)
**Status:** ❌ DO NOT SCRAPE
**Reason:**
- Violates X Terms of Service
- Requires authentication
- Triggers bot defenses
- Use official X API instead
**Recommendation:** Mark as `ClientOnlyApp` or `AuthRequired`

### 7. LinkedIn 🚫 OUT OF SCOPE
**URL:** https://www.linkedin.com/top-content
**Type:** Social media (login wall, dynamic API)
**Status:** ❌ DO NOT SCRAPE
**Reason:**
- Violates LinkedIn Terms of Service
- Requires authentication
- Triggers bot defenses
- Use official LinkedIn API instead
**Recommendation:** Mark as `ClientOnlyApp` or `AuthRequired`

## Implementation Plan

### Phase 1: Test Existing Support (Priority 1)
1. ✅ AppDynamics with ConfluenceAdapter (no changes needed)
2. ✅ Splunk Help with Playwright rendering + enhanced GenericAdapter fallback
3. ✅ NPR covered via NewsAdapter

### Phase 2: Build New Adapters (Priority 2)
1. ✅ **SquarespaceAdapter** (`webarc/adapters/squarespace.py`)
   - Detects `sqs-` layouts/generator metadata
   - Removes headers, footers, pop-ups, social bars
   - Configurable selectors via `SquarespaceAdapterConfig`
2. ✅ **RedditAdapter** (`webarc/adapters/reddit.py`)
   - Consumes Reddit `.json` endpoints with configurable UA/timeout
   - Renders listings and nested comments (depth ≤ 2) into HTML
3. ✅ **NewsAdapter** (`webarc/adapters/news.py`)
   - Detects `<article>` / schema.org / OG metadata markers
   - Normalizes relative links, strips ads/share chrome

### Phase 3: Integration & Testing (Priority 3)
1. ✅ Router updated: Confluence → MkDocs → Sphinx → News → Reddit → Squarespace → Generic
2. ✅ Unit tests cover detection/extraction for Squarespace, News, Reddit (API mocked)
3. ✅ Depth-limited crawls executed for Splunk Help, Squarespace, Reddit scenarios
4. ✅ Markdown verified for boilerplate removal + content density thresholds
5. ✅ Documentation (this file + config schema) updated with adapter coverage

## Acceptance Criteria

For each SUPPORTED site (1-5 above):
- ✅ Crawl succeeds without errors
- ✅ Extracts content from landing page + 2 levels deep
- ✅ Generates clean Obsidian-compatible Markdown
- ✅ Proper front-matter (title, URL, date)
- ✅ Links are preserved and normalized
- ✅ Boilerplate removed (nav, footer, ads)

For OUT-OF-SCOPE sites (6-7 above):
- ✅ Gracefully fail with clear message: "Requires authentication, use official API"
- ✅ OR mark as `ClientOnlyApp` in config

## Test Command

After implementation, validate with:

```bash
# Squarespace (requires JS)
docker compose run --rm --entrypoint="" webarc python -m webarc crawl \
  --seed "https://cherylscaramels.com/" \
  --allow-domain cherylscaramels.com \
  --depth 2 \
  --force-js

# Reddit (JSON adapter)
docker compose run --rm --entrypoint="" webarc python -m webarc crawl \
  --seed "https://www.reddit.com/r/homelab/" \
  --allow-domain reddit.com \
  --allow-prefix "/r/homelab/" \
  --depth 1

# Batch smoke test
docker compose run --rm --entrypoint="" webarc python -m webarc validate \
  --test-urls tests/fixtures/adapter_test_urls.txt
```

## Implementation Notes

- **Squarespace:** Requires Playwright, slow but necessary
- **Reddit:** Prefer JSON API over HTML (faster, more reliable)
- **News:** Handles OG/schema-based pages; falls back to `article` selector
- **X/LinkedIn:** Document as out-of-scope, provide API alternatives
- **Generic fallback:** For unknown sites, use ancestor-of-h1 rule
- **Rate limiting:** Respect robots.txt and add delays for each adapter

## Success Metrics

- 5/7 sites successfully crawled (exclude X/LinkedIn)
- All adapters have >80% test coverage
- Clean Markdown output validated manually
- Documentation updated with adapter guide
