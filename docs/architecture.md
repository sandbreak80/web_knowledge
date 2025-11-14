# WebArc Architecture Documentation

## Overview

WebArc is a local-first, Dockerized web crawler that extracts structured Markdown from documentation sites (Confluence, MkDocs, Sphinx) to create Obsidian-compatible knowledge bases. The system is designed for Sales Engineers and knowledge workers who need offline access to vendor documentation without cloud dependencies.

## System Architecture

### High-Level Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                         CLI Layer                                │
│  (plan, crawl, resume, validate, stats commands)                │
└────────────────────────────┬────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Crawl Planner                                 │
│  - Domain validation                                            │
│  - Sitemap discovery                                             │
│  - Dry-run preview                                              │
└────────────────────────────┬────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                  Scrapy Crawler Core                            │
│  - Request scheduling                                            │
│  - Depth control                                                 │
│  - Domain/prefix fencing                                         │
│  - Safety guards (middlewares)                                   │
└────────────────────────────┬────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Render Router                                 │
│  - Static HTML fetch (default)                                   │
│  - JavaScript detection                                          │
│  - Playwright integration (if JS needed)                        │
└────────────────────────────┬────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                 Extraction Pipeline                              │
│  - Boilerplate removal                                           │
│  - Adapter routing (Confluence/MkDocs/Sphinx/Generic)            │
│  - Content quality checks                                        │
│  - Duplicate detection                                           │
└────────────────────────────┬────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│              HTML → Markdown Converter                           │
│  - Obsidian-flavored Markdown                                    │
│  - YAML front-matter generation                                  │
│  - Wikilink transformation                                      │
│  - Admonition mapping                                            │
└────────────────────────────┬────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Output Writer                                 │
│  - Filename sanitization                                         │
│  - Collision handling                                            │
│  - File writing                                                  │
└────────────────────────────┬────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│              Manifest & State Writer                             │
│  - manifest.jsonl (page metadata)                                │
│  - graph.jsonl (link relationships)                             │
│  - errors.jsonl (error tracking)                                 │
│  - resume.jsonl (state checkpointing)                           │
└─────────────────────────────────────────────────────────────────┘
```

## Component Details

### 1. CLI Layer (`webarc/cli/commands.py`)

**Purpose:** User-facing command-line interface using Typer and Rich.

**Commands:**
- `plan`: Preview crawl plan without fetching pages
- `crawl`: Execute full crawl and extraction
- `resume`: Resume interrupted crawl from checkpoint
- `validate`: Verify output integrity
- `stats`: Display crawl statistics

**Responsibilities:**
- Parse command-line arguments
- Load configuration (`webarc.yaml`)
- Initialize crawler components
- Display progress and results

### 2. Crawl Planner (`webarc/crawler/planner.py`)

**Purpose:** Pre-crawl analysis and planning.

**Key Features:**
- Domain validation
- Sitemap discovery (robots.txt, common sitemap locations)
- Sitemap parsing (XML sitemap extraction)
- Page count estimation

**Methods:**
- `plan()`: Generate crawl plan
- `_discover_sitemap()`: Find sitemap URLs
- `_parse_sitemap()`: Extract URLs from sitemap XML

### 3. Scrapy Crawler Core (`webarc/crawler/`)

#### 3.1 Spider (`webarc/crawler/spider.py`)

**Purpose:** Main Scrapy spider that orchestrates crawling.

**Key Features:**
- Depth-limited crawling
- Link extraction and filtering
- Safety guard integration
- Graph relationship tracking

**Lifecycle:**
1. `start_requests()`: Generate initial requests from seed URLs
2. `parse()`: Process responses, extract links, delegate to crawler instance
3. `_extract_links()`: Extract and normalize links from HTML
4. `_check_safety_guards()`: Apply safety rules before following links

#### 3.2 Middlewares (`webarc/crawler/middlewares.py`)

**Purpose:** Request/response processing hooks.

**Middlewares:**
- `DomainFenceMiddleware`: Enforce domain/prefix restrictions
- `WebArcRobotsTxtMiddleware`: Respect robots.txt rules
- `BlocklistMiddleware`: Block malicious/undesired domains

**Flow:**
```
Request → DomainFenceMiddleware → BlocklistMiddleware → RobotsTxtMiddleware → Downloader
```

#### 3.3 Pipelines (`webarc/crawler/pipelines.py`)

**Purpose:** Post-processing of scraped items.

**Pipelines:**
- `WebArcPipeline`: Pass-through pipeline (processing handled in runner)
- `DuplicateFilterPipeline`: Filter duplicate URLs based on canonical URL

#### 3.4 Runner (`webarc/crawler/runner.py`)

**Purpose:** Orchestrates the entire crawling and processing pipeline.

**Key Components:**
- `WebArcCrawler`: Main crawler orchestrator
- `ExtractionPipeline`: Shared extraction logic

**Responsibilities:**
- Initialize Scrapy CrawlerProcess
- Configure spider with callbacks
- Process responses through full pipeline
- Manage state checkpointing
- Track statistics

**Main Flow:**
1. `run()`: Start Scrapy crawler process
2. `process_response()`: Process each crawled page:
   - Extract content via adapter
   - Convert HTML to Markdown
   - Check content quality
   - Write output files
   - Update manifests
   - Checkpoint state

### 4. Safety Guards (`webarc/safety/`)

**Purpose:** Prevent accidental scraping and enforce safety rules.

**Components:**
- `domain_fence.py`: Domain and prefix restrictions
- `entropy.py`: Detect random identifiers (UUIDs, hashes)
- `param_guard.py`: Detect parameter explosion patterns
- `pagination.py`: Limit pagination following
- `robots.py`: RFC 9309 compliant robots.txt parsing
- `blocklist.py`: StevenBlack hosts blocklist checking

**Integration:**
- Applied in spider `_check_safety_guards()`
- Enforced via middlewares
- Configurable via `webarc.yaml`

### 5. Render Router (`webarc/render/router.py`)

**Purpose:** Decide between static HTML fetch and JavaScript rendering.

**Detection Logic:**
- Check `force_js` config flag
- Check domain cache (domains known to need JS)
- Analyze HTML content length
- Detect JS framework indicators (React, Vue, Angular)
- Check for empty content containers
- Detect `<noscript>` warnings

**Integration:**
- Currently detection exists but not fully wired into pipeline
- `render_type` hardcoded to `'static'` in runner
- Playwright integration available but not activated

### 6. Extraction Pipeline (`webarc/extractors/`)

#### 6.1 Boilerplate Removal (`webarc/extractors/boilerplate.py`)

**Purpose:** Remove navigation, headers, footers, ads.

**Methods:**
- `extract_main_content()`: Use readability-lxml and trafilatura

#### 6.2 Content Quality (`webarc/extractors/quality.py`)

**Purpose:** Evaluate content quality before extraction.

**Metrics:**
- Content density (text/total HTML ratio)
- Word count
- Paragraph count
- Heading count

**Checks:**
- Minimum content density threshold
- Minimum word count
- Heading requirement (optional)

### 7. Adapter System (`webarc/adapters/`)

**Purpose:** Site-specific content extraction logic.

**Adapters:**
- `ConfluenceAdapter`: Atlassian Confluence pages
- `MkDocsAdapter`: MkDocs documentation sites
- `SphinxAdapter`: Sphinx documentation sites
- `GenericAdapter`: Fallback for unknown sites

**Adapter Interface:**
- `matches(url, html)`: Detect if adapter applies
- `extract_content(soup, url)`: Extract main content
- `transform_links(html, base_url)`: Transform links (some incomplete)

**Router:**
- `AdapterRouter`: Selects appropriate adapter based on page characteristics

### 8. HTML → Markdown Converter (`webarc/html2md/converter.py`)

**Purpose:** Convert extracted HTML to Obsidian-flavored Markdown.

**Features:**
- YAML front-matter generation
- Wikilink transformation (`[text](url)` → `[[text]]`)
- Admonition mapping (HTML callouts → Obsidian callouts)
- Table preservation
- Code fence preservation
- Image handling (download/embed modes planned)

**Methods:**
- `convert(html, url)`: Main conversion entry point
- `_transform_admonitions()`: Map HTML callouts
- `_transform_links()`: Convert to wikilinks
- `_transform_images()`: Handle images
- `_post_process()`: Final cleanup

### 9. Output Management (`webarc/output/`)

#### 9.1 Writer (`webarc/output/writer.py`)

**Purpose:** Write Markdown files to filesystem.

**Features:**
- Filename sanitization (remove invalid chars, limit length)
- Collision handling (append numbers for duplicates)
- Symlink deduplication (planned)
- YAML front-matter formatting

**Methods:**
- `write_page(markdown, metadata, url)`: Write page to file
- `url_to_filepath(url)`: Convert URL to filesystem path
- `_sanitize_filename(name)`: Clean filename
- `_handle_collision(path)`: Resolve filename collisions
- `_format_with_frontmatter(markdown, metadata)`: Add YAML front-matter

#### 9.2 Manifest Writer (`webarc/output/manifest.py`)

**Purpose:** Write crawl metadata to JSONL files.

**Files:**
- `manifest.jsonl`: Page metadata (one JSON object per line)
- `graph.jsonl`: Link relationships (source → target)
- `errors.jsonl`: Error tracking
- `resume.jsonl`: State checkpointing (written by StateManager)

**Methods:**
- `write_manifest_entry(metadata)`: Write page metadata
- `write_graph_entry(source, target)`: Write link relationship
- `write_error_entry(url, error)`: Write error record

### 10. State Management (`webarc/crawler/state.py`)

**Purpose:** Enable resumable crawls via checkpointing.

**Features:**
- Save crawl state periodically
- Load state for resume
- Track visited URLs, queue, statistics

**Methods:**
- `save_state(crawler_state)`: Write state to `resume.jsonl`
- `load_state()`: Load state from `resume.jsonl`
- `maybe_checkpoint(crawler_state)`: Conditional checkpointing

**State Structure:**
```python
{
    'seed_url': str,
    'config_hash': str,  # TODO: implement
    'pages_crawled': int,
    'pages_extracted': int,
    'pages_skipped': int,
    'pages_failed': int,
    'queue': List[str],
    'visited': List[str],
    'timestamp': str
}
```

### 11. Configuration System (`webarc/config/`)

#### 11.1 Schema (`webarc/config/schema.py`)

**Purpose:** Pydantic models for configuration validation.

**Sections:**
- `CrawlerConfig`: Scrapy settings
- `SafetyConfig`: Safety guard thresholds
- `RenderConfig`: JS rendering settings
- `ExtractionConfig`: Content quality thresholds
- `OutputConfig`: Output directory and formatting
- `LoggingConfig`: Logging levels
- `AdaptersConfig`: Adapter-specific settings

#### 11.2 Loader (`webarc/config/loader.py`)

**Purpose:** Load and validate `webarc.yaml` configuration.

**Methods:**
- `find_config_file()`: Locate config file
- `load_config(config_file)`: Load and validate config

## Data Flow

### Crawl Execution Flow

1. **CLI Invocation**
   ```
   webarc crawl --seed https://docs.example.com
   ```

2. **Configuration Loading**
   - Load `webarc.yaml`
   - Override with CLI flags
   - Validate with Pydantic

3. **Crawler Initialization**
   - Create `WebArcCrawler` instance
   - Initialize adapters, converters, writers
   - Set up state manager

4. **Scrapy Process Start**
   - Create `CrawlerProcess` with Scrapy settings
   - Configure spider with callbacks
   - Start crawling (blocking)

5. **Page Processing (per page)**
   ```
   Request → Middlewares → Downloader → Response
   Response → Spider.parse() → WebArcCrawler.process_response()
   process_response():
     - Extract HTML content
     - Route to adapter
     - Extract main content
     - Check quality
     - Convert to Markdown
     - Write file
     - Update manifests
     - Checkpoint state (periodically)
   ```

6. **Link Discovery**
   - Spider extracts links from HTML
   - Applies safety guards
   - Filters by domain/prefix
   - Adds to crawl queue

7. **Completion**
   - Final state checkpoint
   - Statistics summary
   - Exit with status code

### Resume Flow

1. **Load State**
   ```
   webarc resume
   → Load resume.jsonl
   → Extract visited_urls
   ```

2. **Initialize Crawler**
   - Pass `visited_urls` to spider
   - Spider skips already-visited URLs

3. **Continue Crawling**
   - Same flow as normal crawl
   - State accumulates from checkpoint

## Integration Points

### Scrapy Integration

- **Spider-Crawler Coupling**: Currently uses class attribute (`WebArcSpider.crawler_instance`). Should use Scrapy signals for proper decoupling.

- **Middleware Chain**: DomainFence → Blocklist → RobotsTxt → Downloader

- **Pipeline Chain**: WebArcPipeline → DuplicateFilterPipeline

### State Management Integration

- Checkpointing triggered in `process_response()` via `StateManager.maybe_checkpoint()`
- State includes visited URLs, statistics, queue approximation

### Adapter Integration

- AdapterRouter selects adapter based on `matches()` method
- Adapters extract content, transform links
- Generic adapter always matches (fallback)

## Configuration

### Configuration File (`webarc.yaml`)

Located via `find_config_file()`:
1. `--config` CLI flag
2. `WEBARC_CONFIG` environment variable
3. `./webarc.yaml`
4. `~/.config/webarc.yaml`

### Environment Variables

None required. All configuration via `webarc.yaml`.

### Docker Configuration

- Non-root user (`webarc:webarc`)
- Resource limits (2GB RAM)
- Volume mounts (`./out`, `./artifacts`)
- Entrypoint override for testing

## Error Handling

### Error Categories

1. **Network Errors**: Retried via Scrapy retry middleware
2. **Parsing Errors**: Logged to `errors.jsonl`, page skipped
3. **Quality Failures**: Logged, page skipped
4. **File System Errors**: Logged, crawl continues

### Error Tracking

- Errors written to `errors.jsonl`
- Error count tracked in statistics
- Exit codes: 0 (success), 1 (validation failure), 2 (crawl errors)

## Performance Considerations

### Concurrency

- Scrapy handles request concurrency
- Configurable via `concurrent_requests` and `concurrent_requests_per_domain`
- Default: 8 total, 3 per domain

### Memory Management

- Large pages skipped (`max_page_size_mb`)
- State checkpointing reduces memory footprint
- Browser pool limited (3 max for Playwright)

### Disk Usage

- Output files written incrementally
- Manifest files append-only (JSONL)
- Symlink deduplication planned to reduce disk usage

## Security Considerations

### Safety Guards

- Domain fencing prevents crawling unintended sites
- Blocklist prevents malicious domains
- Robots.txt compliance respects site policies
- Entropy detection prevents infinite loops
- Parameter explosion detection prevents combinatorial explosion

### Docker Security

- Non-root user execution
- Resource limits prevent DoS
- Network isolation via Docker

## Known Limitations

1. **Critical Path Testing**: `WebArcCrawler.run()` has 0% test coverage
2. **Incomplete Features**:
   - URL canonicalization placeholder (uses URL directly)
   - JS rendering detection not wired (hardcoded to 'static')
   - Config hash calculation missing (TODO)
3. **Architecture Debt**:
   - Spider-crawler coupling via class attribute (should use signals)
   - Some adapters have incomplete `transform_links()` implementations

## Future Improvements

1. **Architecture**:
   - Replace class attribute coupling with Scrapy signals
   - Fully integrate render router into pipeline
   - Complete adapter implementations

2. **Testing**:
   - Add integration tests for `crawler.run()`
   - Add middleware integration tests
   - Add spider `parse()` method tests

3. **Documentation**:
   - API reference documentation
   - Operations guide
   - Quickstart guide

4. **Features**:
   - Implement config hash calculation
   - Complete URL canonicalization
   - Wire JS rendering detection
   - Add symlink deduplication
   - Add image download/embed modes
