# WebArc API Reference

This document provides a comprehensive reference for all public APIs in WebArc.

## Table of Contents

- [CLI Commands](#cli-commands)
- [Crawler Core](#crawler-core)
- [Configuration](#configuration)
- [Adapters](#adapters)
- [Extractors](#extractors)
- [HTML to Markdown](#html-to-markdown)
- [Output Management](#output-management)
- [Render Router](#render-router)
- [Safety Guards](#safety-guards)
- [State Management](#state-management)
- [Utilities](#utilities)

---

## CLI Commands

### `webarc.cli.commands`

#### `app`

Typer application instance for CLI commands.

```python
from webarc.cli.commands import app
```

#### `plan`

Preview crawl plan without fetching pages.

**Signature:**
```python
def plan(
    seed: str,
    allow_domain: Optional[str] = None,
    allow_prefix: Optional[str] = None,
    depth: int = 3,
    show_rules: bool = False,
    estimate: bool = False,
    min_content_density: Optional[float] = None,
    min_word_count: Optional[int] = None,
) -> None
```

**Parameters:**
- `seed` (str, required): Seed URL to start crawl
- `allow_domain` (str, optional): Restrict to this domain
- `allow_prefix` (str, optional): Only crawl URLs with this prefix
- `depth` (int, default=3): Maximum crawl depth
- `show_rules` (bool, default=False): Display safety rules
- `estimate` (bool, default=False): Estimate page count from sitemap
- `min_content_density` (float, optional): Override minimum content density
- `min_word_count` (int, optional): Override minimum word count

**Returns:** None (prints to console)

**Example:**
```bash
webarc plan --seed https://docs.example.com --estimate --show-rules
```

#### `crawl`

Execute full crawl and extraction.

**Signature:**
```python
def crawl(
    seed: str,
    output: Path = Path("./out"),
    config_file: Optional[str] = None,
    allow_domain: Optional[str] = None,
    allow_prefix: Optional[str] = None,
    depth: int = 3,
    force_js: bool = False,
    ignore_robots: bool = False,
    min_content_density: Optional[float] = None,
    min_word_count: Optional[int] = None,
    user_agent: Optional[str] = None,
    version_lock: Optional[str] = None,
) -> None
```

**Parameters:**
- `seed` (str, required): Starting URL
- `output` (Path, default="./out"): Output directory
- `config_file` (str, optional): Path to config file
- `allow_domain` (str, optional): Domain restriction
- `allow_prefix` (str, optional): Path prefix restriction
- `depth` (int, default=3): Maximum crawl depth
- `force_js` (bool, default=False): Force JavaScript rendering
- `ignore_robots` (bool, default=False): Ignore robots.txt
- `min_content_density` (float, optional): Minimum content density
- `min_word_count` (int, optional): Minimum word count
- `user_agent` (str, optional): Override User-Agent header
- `version_lock` (str, optional): Restrict to URLs containing version segment

**Returns:** None (writes files to output directory)

**Example:**
```bash
webarc crawl --seed https://docs.example.com --output ./my_docs --depth 5
```

#### `resume`

Resume interrupted crawl from checkpoint.

**Signature:**
```python
def resume(
    output: Path = Path("./out"),
    config_file: Optional[str] = None,
) -> None
```

**Parameters:**
- `output` (Path, default="./out"): Output directory containing resume.jsonl
- `config_file` (str, optional): Path to config file

**Returns:** None (continues crawl)

**Example:**
```bash
webarc resume --output ./my_docs
```

#### `validate`

Verify output integrity.

**Signature:**
```python
def validate(
    output: Path = Path("./out"),
    check_links: bool = False,
) -> None
```

**Parameters:**
- `output` (Path, default="./out"): Output directory to validate
- `check_links` (bool, default=False): Verify internal links

**Returns:** None (exits with code 1 if validation fails)

**Example:**
```bash
webarc validate --output ./my_docs --check-links
```

#### `stats`

Display crawl statistics.

**Signature:**
```python
def stats(
    output: Path = Path("./out"),
) -> None
```

**Parameters:**
- `output` (Path, default="./out"): Output directory

**Returns:** None (prints statistics to console)

**Example:**
```bash
webarc stats --output ./my_docs
```

---

## Crawler Core

### `webarc.crawler.runner`

#### `WebArcCrawler`

Main crawler orchestrator that runs the full pipeline.

**Signature:**
```python
class WebArcCrawler:
    def __init__(
        self,
        seed_url: str,
        config: Optional[WebArcConfig] = None,
        output_dir: Path = Path("./out"),
        max_depth: int = 3,
        allowed_domain: Optional[str] = None,
        allowed_prefix: Optional[str] = None,
        visited_urls: Optional[set] = None,
        version_lock: Optional[str] = None,
    )
```

**Parameters:**
- `seed_url` (str, required): Starting URL
- `config` (WebArcConfig, optional): Configuration (defaults to loaded config)
- `output_dir` (Path, default="./out"): Output directory
- `max_depth` (int, default=3): Maximum crawl depth
- `allowed_domain` (str, optional): Domain restriction
- `allowed_prefix` (str, optional): Path prefix restriction
- `visited_urls` (set, optional): Already-visited URLs (for resume)
- `version_lock` (str, optional): Version segment restriction

**Methods:**

##### `run()`

Run the crawler.

**Signature:**
```python
def run(self) -> Dict[str, Any]
```

**Returns:**
- `Dict[str, Any]`: Dictionary with crawl statistics:
  - `pages_crawled` (int): Total pages crawled
  - `pages_extracted` (int): Pages successfully extracted
  - `pages_skipped` (int): Pages skipped (quality/duplicate)
  - `errors` (int): Number of errors

**Example:**
```python
from webarc.crawler.runner import WebArcCrawler

crawler = WebArcCrawler(
    seed_url="https://docs.example.com",
    output_dir="./out",
    max_depth=3
)
stats = crawler.run()
print(f"Crawled {stats['pages_crawled']} pages")
```

##### `process_response()`

Process a crawled response through the full pipeline.

**Signature:**
```python
def process_response(
    self,
    response: scrapy.http.Response,
    spider: WebArcSpider
) -> None
```

**Parameters:**
- `response` (scrapy.http.Response): Scrapy response object
- `spider` (WebArcSpider): Spider instance

**Returns:** None (writes files, updates manifests)

**Note:** This is called automatically by the spider during crawling.

### `webarc.crawler.planner`

#### `CrawlPlanner`

Plan crawl without actually fetching pages.

**Signature:**
```python
class CrawlPlanner:
    def __init__(
        self,
        seed_url: str,
        config: WebArcConfig,
        allowed_domain: Optional[str] = None,
        allowed_prefix: Optional[str] = None,
        max_depth: int = 3
    )
```

**Parameters:**
- `seed_url` (str, required): Starting URL
- `config` (WebArcConfig, required): Configuration
- `allowed_domain` (str, optional): Domain restriction
- `allowed_prefix` (str, optional): Path prefix restriction
- `max_depth` (int, default=3): Maximum crawl depth

**Methods:**

##### `plan()`

Generate crawl plan.

**Signature:**
```python
def plan(self) -> dict
```

**Returns:**
- `dict`: Plan dictionary with:
  - `seed_url` (str): Starting URL
  - `allowed_domain` (str): Domain restriction
  - `allowed_prefix` (str): Path prefix restriction
  - `max_depth` (int): Maximum depth
  - `estimated_pages` (int, optional): Estimated page count from sitemap

**Example:**
```python
from webarc.crawler.planner import CrawlPlanner
from webarc.config.loader import load_config

config = load_config()
planner = CrawlPlanner(
    seed_url="https://docs.example.com",
    config=config
)
plan = planner.plan()
print(f"Estimated pages: {plan.get('estimated_pages', 'unknown')}")
```

##### `_discover_sitemap()`

Discover sitemap URLs.

**Signature:**
```python
def _discover_sitemap(self) -> List[str]
```

**Returns:**
- `List[str]`: List of sitemap URLs found

**Note:** Checks robots.txt and common sitemap locations.

##### `_parse_sitemap()`

Parse sitemap XML and extract URLs.

**Signature:**
```python
def _parse_sitemap(self, sitemap_url: str) -> List[str]
```

**Parameters:**
- `sitemap_url` (str): URL of sitemap XML

**Returns:**
- `List[str]`: List of URLs from sitemap

### `webarc.crawler.spider`

#### `WebArcSpider`

Main Scrapy spider for WebArc crawler.

**Signature:**
```python
class WebArcSpider(scrapy.Spider):
    name = 'webarc'
    
    def __init__(
        self,
        seed_url: str,
        config: WebArcConfig,
        allowed_domain: Optional[str] = None,
        allowed_prefix: Optional[str] = None,
        max_depth: int = 3,
        visited_urls: Optional[Set[str]] = None,
        version_lock: Optional[str] = None,
        extra_seed_urls: Optional[List[str]] = None,
        crawler_instance: Optional[WebArcCrawler] = None,
    )
```

**Note:** This class is primarily used internally by Scrapy. Use `WebArcCrawler` for programmatic access.

---

## Configuration

### `webarc.config.loader`

#### `load_config()`

Load configuration from YAML file or use defaults.

**Signature:**
```python
def load_config(config_path: Optional[str] = None) -> WebArcConfig
```

**Parameters:**
- `config_path` (str, optional): Path to config file. If None, searches standard locations:
  1. `./webarc.yaml`
  2. `./config/webarc.yaml`
  3. `~/.webarc/webarc.yaml`

**Returns:**
- `WebArcConfig`: Configuration object with loaded or default values

**Example:**
```python
from webarc.config.loader import load_config

config = load_config()
print(f"Max depth: {config.crawler.max_depth}")
```

#### `find_config_file()`

Find webarc.yaml config file in standard locations.

**Signature:**
```python
def find_config_file() -> Optional[Path]
```

**Returns:**
- `Optional[Path]`: Path to config file if found, None otherwise

**Example:**
```python
from webarc.config.loader import find_config_file

config_path = find_config_file()
if config_path:
    print(f"Found config at: {config_path}")
```

### `webarc.config.schema`

#### `WebArcConfig`

Main configuration class (Pydantic model).

**Signature:**
```python
class WebArcConfig(BaseModel):
    crawler: CrawlerConfig
    safety: SafetyConfig
    render: RenderConfig
    extraction: ExtractionConfig
    output: OutputConfig
    logging: LoggingConfig
    adapters: AdaptersConfig
    allow_domain: Optional[str] = None
    allow_prefix: Optional[str] = None
```

**Attributes:**
- `crawler` (CrawlerConfig): Scrapy crawler settings
- `safety` (SafetyConfig): Safety guard thresholds
- `render` (RenderConfig): JavaScript rendering settings
- `extraction` (ExtractionConfig): Content quality thresholds
- `output` (OutputConfig): Output directory and formatting
- `logging` (LoggingConfig): Logging levels
- `adapters` (AdaptersConfig): Adapter-specific settings
- `allow_domain` (str, optional): Default domain restriction
- `allow_prefix` (str, optional): Default path prefix restriction

**Example:**
```python
from webarc.config.schema import WebArcConfig

config = WebArcConfig()
config.crawler.max_depth = 5
config.safety.max_url_length = 500
```

---

## Adapters

### `webarc.adapters.base`

#### `SiteAdapter`

Base class for site-specific extraction adapters.

**Signature:**
```python
class SiteAdapter(ABC):
    @abstractmethod
    def matches(self, url: str, html: str) -> bool
    
    @abstractmethod
    def extract_content(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]
    
    @abstractmethod
    def transform_links(self, source_url: str, links: List[str]) -> List[str]
```

**Methods:**

##### `matches()`

Return True if this adapter should handle the page.

**Signature:**
```python
def matches(self, url: str, html: str) -> bool
```

**Parameters:**
- `url` (str): Page URL
- `html` (str): HTML content

**Returns:**
- `bool`: True if adapter matches

##### `extract_content()`

Extract and structure content.

**Signature:**
```python
def extract_content(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]
```

**Parameters:**
- `soup` (BeautifulSoup): Parsed HTML
- `url` (str): Source URL

**Returns:**
- `Dict[str, Any]`: Dictionary with:
  - `title` (str): Page title
  - `body_html` (str): Main content HTML (cleaned)
  - `version` (str, optional): Version identifier
  - `lang` (str): Language code
  - `framework` (str): Framework name
  - `remove_selectors` (List[str]): CSS selectors to remove
  - `metadata` (Dict[str, Any]): Additional front-matter fields

##### `transform_links()`

Transform links to Obsidian format.

**Signature:**
```python
def transform_links(self, source_url: str, links: List[str]) -> List[str]
```

**Parameters:**
- `source_url` (str): Source page URL
- `links` (List[str]): List of link URLs

**Returns:**
- `List[str]`: List of transformed links

### `webarc.adapters.router`

#### `AdapterRouter`

Route pages to appropriate adapter.

**Signature:**
```python
class AdapterRouter:
    def __init__(self, config: WebArcConfig)
```

**Parameters:**
- `config` (WebArcConfig): Configuration

**Methods:**

##### `get_adapter()`

Select best adapter for this page.

**Signature:**
```python
def get_adapter(self, url: str, html: str) -> SiteAdapter
```

**Parameters:**
- `url` (str): Page URL
- `html` (str): HTML content

**Returns:**
- `SiteAdapter`: Adapter instance (ConfluenceAdapter, MkDocsAdapter, SphinxAdapter, or GenericAdapter)

**Example:**
```python
from webarc.adapters.router import AdapterRouter
from webarc.config.loader import load_config

config = load_config()
router = AdapterRouter(config)
adapter = router.get_adapter("https://docs.example.com/page", html_content)
content = adapter.extract_content(soup, "https://docs.example.com/page")
```

---

## Extractors

### `webarc.extractors.boilerplate`

#### `extract_main_content()`

Extract main content from HTML, removing boilerplate.

**Signature:**
```python
def extract_main_content(html: str, url: str) -> str
```

**Parameters:**
- `html` (str): HTML content
- `url` (str): Source URL

**Returns:**
- `str`: Cleaned HTML with main content only

**Example:**
```python
from webarc.extractors.boilerplate import extract_main_content

clean_html = extract_main_content(raw_html, "https://example.com/page")
```

### `webarc.extractors.quality`

#### `ContentQuality`

Evaluate page quality and determine if worth extracting.

**Signature:**
```python
class ContentQuality:
    def __init__(self, html: str, url: str)
```

**Parameters:**
- `html` (str): HTML content
- `url` (str): Page URL

**Attributes:**
- `word_count` (int): Number of words
- `content_density` (float): Content density ratio
- `paragraph_count` (int): Number of paragraphs
- `heading_count` (int): Number of headings
- `link_count` (int): Number of links
- `table_count` (int): Number of tables
- `code_block_count` (int): Number of code blocks

**Methods:**

##### `is_acceptable()`

Check if content meets quality thresholds.

**Signature:**
```python
def is_acceptable(
    self,
    min_content_density: float = 0.3,
    min_word_count: int = 50,
    require_heading: bool = False
) -> Tuple[bool, Optional[str]]
```

**Parameters:**
- `min_content_density` (float, default=0.3): Minimum content density
- `min_word_count` (int, default=50): Minimum word count
- `require_heading` (bool, default=False): Require at least one heading

**Returns:**
- `Tuple[bool, Optional[str]]`: (is_acceptable, reason_if_not)

**Example:**
```python
from webarc.extractors.quality import ContentQuality

quality = ContentQuality(html, url)
is_ok, reason = quality.is_acceptable(
    min_content_density=0.3,
    min_word_count=50
)
if not is_ok:
    print(f"Rejected: {reason}")
```

---

## HTML to Markdown

### `webarc.html2md.converter`

#### `ObsidianMarkdownConverter`

Convert HTML to Obsidian-flavored Markdown.

**Signature:**
```python
class ObsidianMarkdownConverter:
    def __init__(self, config: WebArcConfig)
```

**Parameters:**
- `config` (WebArcConfig): Configuration

**Methods:**

##### `convert()`

Convert HTML to clean Markdown.

**Signature:**
```python
def convert(self, html: str, source_url: str) -> str
```

**Parameters:**
- `html` (str): HTML content
- `source_url` (str): Source URL

**Returns:**
- `str`: Markdown content

**Example:**
```python
from webarc.html2md.converter import ObsidianMarkdownConverter
from webarc.config.loader import load_config

config = load_config()
converter = ObsidianMarkdownConverter(config)
markdown = converter.convert(html_content, "https://example.com/page")
```

---

## Output Management

### `webarc.output.writer`

#### `OutputWriter`

Write extracted content to filesystem with deduplication.

**Signature:**
```python
class OutputWriter:
    def __init__(self, output_dir: Path, config)
```

**Parameters:**
- `output_dir` (Path): Output directory path
- `config`: WebArc configuration

**Methods:**

##### `write_page()`

Write page to filesystem with deduplication.

**Signature:**
```python
def write_page(self, url: str, content: Dict[str, Any]) -> Path
```

**Parameters:**
- `url` (str): Source URL
- `content` (Dict[str, Any]): Dictionary with keys:
  - `markdown` (str): Markdown content
  - `metadata` (Dict[str, Any]): Page metadata
  - `content_hash` (str, optional): Content hash

**Returns:**
- `Path`: Path to written file

**Example:**
```python
from webarc.output.writer import OutputWriter
from pathlib import Path
from webarc.config.loader import load_config

config = load_config()
writer = OutputWriter(Path("./out"), config)
file_path = writer.write_page(
    "https://example.com/page",
    {
        "markdown": "# Page Title\n\nContent...",
        "metadata": {"title": "Page Title", "source_url": "https://example.com/page"}
    }
)
```

##### `url_to_filepath()`

Convert URL to filesystem path.

**Signature:**
```python
def url_to_filepath(self, url: str) -> Path
```

**Parameters:**
- `url` (str): URL

**Returns:**
- `Path`: Filesystem path

### `webarc.output.manifest`

#### `ManifestWriter`

Write crawl metadata to JSONL files.

**Signature:**
```python
class ManifestWriter:
    def __init__(self, output_dir: Path)
```

**Parameters:**
- `output_dir` (Path): Output directory

**Methods:**

##### `write_manifest_entry()`

Write page metadata.

**Signature:**
```python
def write_manifest_entry(self, metadata: Dict[str, Any]) -> None
```

**Parameters:**
- `metadata` (Dict[str, Any]): Page metadata dictionary

**Returns:** None (writes to `manifest.jsonl`)

##### `write_graph_entry()`

Write link relationship.

**Signature:**
```python
def write_graph_entry(self, source: str, target: str) -> None
```

**Parameters:**
- `source` (str): Source URL
- `target` (str): Target URL

**Returns:** None (writes to `graph.jsonl`)

##### `write_error_entry()`

Write error record.

**Signature:**
```python
def write_error_entry(self, url: str, error: str) -> None
```

**Parameters:**
- `url` (str): URL that failed
- `error` (str): Error message

**Returns:** None (writes to `errors.jsonl`)

**Example:**
```python
from webarc.output.manifest import ManifestWriter
from pathlib import Path

writer = ManifestWriter(Path("./out"))
writer.write_manifest_entry({
    "url": "https://example.com/page",
    "title": "Page Title",
    "file_path": "page.md"
})
writer.write_graph_entry(
    "https://example.com/page1",
    "https://example.com/page2"
)
```

---

## Render Router

### `webarc.render.router`

#### `RenderRouter`

Decide whether to use static HTML or JavaScript rendering.

**Signature:**
```python
class RenderRouter:
    def __init__(self, config: WebArcConfig)
```

**Parameters:**
- `config` (WebArcConfig): Configuration

**Methods:**

##### `check_js_needed()`

Detect if JavaScript rendering is required.

**Signature:**
```python
def check_js_needed(self, html: str, url: str) -> bool
```

**Parameters:**
- `html` (str): HTML content to check
- `url` (str): URL of the page

**Returns:**
- `bool`: True if JavaScript rendering is needed

**Example:**
```python
from webarc.render.router import RenderRouter
from webarc.config.loader import load_config

config = load_config()
router = RenderRouter(config)
needs_js = router.check_js_needed(html_content, "https://example.com/page")
```

##### `mark_domain_js_needed()`

Mark domain as requiring JavaScript rendering.

**Signature:**
```python
def mark_domain_js_needed(self, url: str) -> None
```

**Parameters:**
- `url` (str): URL to extract domain from

**Returns:** None (adds domain to cache)

---

## Safety Guards

### `webarc.safety.domain_fence`

#### `validate_domain_restriction()`

Validate URL against domain and prefix restrictions.

**Signature:**
```python
def validate_domain_restriction(
    url: str,
    allowed_domain: Optional[str] = None,
    allowed_prefix: Optional[str] = None
) -> Tuple[bool, Optional[str]]
```

**Parameters:**
- `url` (str): URL to validate
- `allowed_domain` (str, optional): Allowed domain
- `allowed_prefix` (str, optional): Allowed path prefix

**Returns:**
- `Tuple[bool, Optional[str]]`: (is_allowed, reason_if_not)

#### `extract_domain_from_url()`

Extract domain from URL.

**Signature:**
```python
def extract_domain_from_url(url: str) -> str
```

**Parameters:**
- `url` (str): URL

**Returns:**
- `str`: Domain name

### `webarc.safety.entropy`

#### `check_url_for_random_segments()`

Check URL for random identifier segments (UUIDs, hashes).

**Signature:**
```python
def check_url_for_random_segments(
    url: str,
    entropy_threshold: float = 3.5
) -> Tuple[bool, List[str]]
```

**Parameters:**
- `url` (str): URL to check
- `entropy_threshold` (float, default=3.5): Entropy threshold

**Returns:**
- `Tuple[bool, List[str]]`: (has_random_segments, list_of_segments)

#### `calculate_entropy()`

Calculate Shannon entropy of a string.

**Signature:**
```python
def calculate_entropy(s: str) -> float
```

**Parameters:**
- `s` (str): String to analyze

**Returns:**
- `float`: Entropy value

#### `is_random_identifier()`

Check if a segment is a random identifier.

**Signature:**
```python
def is_random_identifier(
    segment: str,
    entropy_threshold: float = 3.5
) -> bool
```

**Parameters:**
- `segment` (str): URL segment to check
- `entropy_threshold` (float, default=3.5): Entropy threshold

**Returns:**
- `bool`: True if segment appears random

### `webarc.safety.robots`

#### `RobotsTxtParser`

RFC 9309 compliant robots.txt parser.

**Signature:**
```python
class RobotsTxtParser:
    def __init__(self, user_agent: str = "*")
```

**Parameters:**
- `user_agent` (str, default="*"): User agent string

**Methods:**

##### `parse()`

Parse robots.txt content.

**Signature:**
```python
def parse(self, robots_txt: str, base_url: str) -> None
```

**Parameters:**
- `robots_txt` (str): robots.txt content
- `base_url` (str): Base URL for resolving relative paths

**Returns:** None (updates internal rules)

##### `can_fetch()`

Check if URL can be fetched.

**Signature:**
```python
def can_fetch(self, url: str) -> bool
```

**Parameters:**
- `url` (str): URL to check

**Returns:**
- `bool`: True if URL can be fetched

**Example:**
```python
from webarc.safety.robots import RobotsTxtParser

parser = RobotsTxtParser(user_agent="WebArc/1.0")
parser.parse(robots_txt_content, "https://example.com")
if parser.can_fetch("https://example.com/page"):
    print("Allowed")
```

### `webarc.safety.blocklist`

#### `load_blocklist()`

Load StevenBlack hosts blocklist.

**Signature:**
```python
def load_blocklist(blocklist_path: str) -> Set[str]
```

**Parameters:**
- `blocklist_path` (str): Path to blocklist file

**Returns:**
- `Set[str]`: Set of blocked domains

#### `check_blocklist()`

Check if domain is in blocklist.

**Signature:**
```python
def check_blocklist(domain: str, blocklist_path: str) -> bool
```

**Parameters:**
- `domain` (str): Domain to check
- `blocklist_path` (str): Path to blocklist file

**Returns:**
- `bool`: True if domain is blocked

#### `reset_blocklist_cache()`

Reset blocklist cache.

**Signature:**
```python
def reset_blocklist_cache() -> None
```

**Returns:** None (clears cache)

### `webarc.safety.param_guard`

#### `ParamExplosionDetector`

Detect parameter explosion patterns in URLs.

**Signature:**
```python
class ParamExplosionDetector:
    def __init__(self, max_params: int = 10)
```

**Parameters:**
- `max_params` (int, default=10): Maximum query parameters

**Methods:**

##### `check_url()`

Check URL for parameter explosion.

**Signature:**
```python
def check_url(self, url: str) -> Tuple[bool, Optional[str]]
```

**Parameters:**
- `url` (str): URL to check

**Returns:**
- `Tuple[bool, Optional[str]]`: (is_explosion, reason_if_yes)

### `webarc.safety.pagination`

#### `PaginationDetector`

Detect and limit pagination following.

**Signature:**
```python
class PaginationDetector:
    def __init__(self, max_depth: int = 3)
```

**Parameters:**
- `max_depth` (int, default=3): Maximum pagination depth

**Methods:**

##### `is_pagination()`

Check if URL is a pagination URL.

**Signature:**
```python
def is_pagination(self, url: str) -> bool
```

**Parameters:**
- `url` (str): URL to check

**Returns:**
- `bool`: True if URL appears to be pagination

##### `should_follow()`

Check if pagination URL should be followed.

**Signature:**
```python
def should_follow(self, url: str) -> bool
```

**Parameters:**
- `url` (str): Pagination URL

**Returns:**
- `bool`: True if should follow

##### `reset()`

Reset pagination tracking.

**Signature:**
```python
def reset(self) -> None
```

**Returns:** None (resets internal state)

---

## State Management

### `webarc.crawler.state`

#### `StateManager`

Periodically save crawler state for resumability.

**Signature:**
```python
class StateManager:
    def __init__(self, output_dir: Path, checkpoint_interval: int = 100)
```

**Parameters:**
- `output_dir` (Path): Output directory
- `checkpoint_interval` (int, default=100): Save state every N URLs

**Methods:**

##### `save_state()`

Save current crawler state.

**Signature:**
```python
def save_state(self, crawler_state: Dict[str, Any]) -> None
```

**Parameters:**
- `crawler_state` (Dict[str, Any]): State dictionary with:
  - `seed_url` (str): Starting URL
  - `config_hash` (str): Config hash (TODO: implement)
  - `pages_crawled` (int): Pages crawled
  - `pages_extracted` (int): Pages extracted
  - `pages_skipped` (int): Pages skipped
  - `pages_failed` (int): Pages failed
  - `queue` (List[str]): Queue of URLs
  - `visited` (List[str]): Visited URLs
  - `status` (str): Status string

**Returns:** None (writes to `resume.jsonl`)

##### `load_state()`

Load previous crawler state.

**Signature:**
```python
def load_state(self) -> Optional[Dict[str, Any]]
```

**Returns:**
- `Optional[Dict[str, Any]]`: State dictionary or None if not found

**Example:**
```python
from webarc.crawler.state import StateManager
from pathlib import Path

manager = StateManager(Path("./out"))
state = manager.load_state()
if state:
    visited_urls = set(state.get('visited', []))
    print(f"Resuming with {len(visited_urls)} visited URLs")
```

##### `maybe_checkpoint()`

Save state if checkpoint interval reached.

**Signature:**
```python
def maybe_checkpoint(self, crawler_state: Dict[str, Any]) -> None
```

**Parameters:**
- `crawler_state` (Dict[str, Any]): Current crawler state

**Returns:** None (conditionally saves state)

---

## Utilities

### `webarc.utils.url`

#### `canonicalize_url()`

Canonicalize URL (normalize, remove fragments, etc.).

**Signature:**
```python
def canonicalize_url(url: str, preserve_anchors: bool = False) -> str
```

**Parameters:**
- `url` (str): URL to canonicalize
- `preserve_anchors` (bool, default=False): Preserve URL fragments

**Returns:**
- `str`: Canonicalized URL

**Example:**
```python
from webarc.utils.url import canonicalize_url

canonical = canonicalize_url("https://example.com/page?foo=bar#section")
# Returns: "https://example.com/page?foo=bar"
```

#### `extract_domain()`

Extract domain from URL.

**Signature:**
```python
def extract_domain(url: str) -> str
```

**Parameters:**
- `url` (str): URL

**Returns:**
- `str`: Domain name

#### `is_same_domain()`

Check if two URLs are on the same domain.

**Signature:**
```python
def is_same_domain(url1: str, url2: str) -> bool
```

**Parameters:**
- `url1` (str): First URL
- `url2` (str): Second URL

**Returns:**
- `bool`: True if same domain

#### `is_internal_link()`

Check if target URL is an internal link from source URL.

**Signature:**
```python
def is_internal_link(source_url: str, target_url: str) -> bool
```

**Parameters:**
- `source_url` (str): Source page URL
- `target_url` (str): Target link URL

**Returns:**
- `bool`: True if internal link

---

## Error Handling

All APIs may raise standard Python exceptions:

- `ValueError`: Invalid parameter values
- `FileNotFoundError`: Missing files (config, blocklist, etc.)
- `KeyError`: Missing dictionary keys
- `AttributeError`: Missing attributes

WebArc-specific errors are logged but generally don't raise exceptions to allow crawl continuation.

---

## Version Information

Current version information can be found in:
- `webarc/__init__.py`: Package version
- `requirements.txt`: Dependency versions
- `Dockerfile`: Container configuration

---

## Examples

### Complete Crawl Example

```python
from webarc.crawler.runner import WebArcCrawler
from pathlib import Path

crawler = WebArcCrawler(
    seed_url="https://docs.example.com",
    output_dir=Path("./output"),
    max_depth=3,
    allowed_domain="docs.example.com"
)

stats = crawler.run()
print(f"Extracted {stats['pages_extracted']} pages")
```

### Custom Adapter Example

```python
from webarc.adapters.base import SiteAdapter
from bs4 import BeautifulSoup
from typing import Dict, Any, List

class MyCustomAdapter(SiteAdapter):
    def matches(self, url: str, html: str) -> bool:
        return "my-site.com" in url
    
    def extract_content(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        title = soup.find('title').text if soup.find('title') else "Untitled"
        body = soup.find('main') or soup.find('article')
        return {
            "title": title,
            "body_html": str(body) if body else "",
            "lang": "en",
            "framework": "custom"
        }
    
    def transform_links(self, source_url: str, links: List[str]) -> List[str]:
        # Custom link transformation
        return links
```

### Programmatic Content Extraction

```python
from webarc.extractors.boilerplate import extract_main_content
from webarc.extractors.quality import ContentQuality
from webarc.html2md.converter import ObsidianMarkdownConverter
from webarc.config.loader import load_config
import requests

# Fetch page
response = requests.get("https://docs.example.com/page")
html = response.text

# Extract main content
clean_html = extract_main_content(html, response.url)

# Check quality
quality = ContentQuality(clean_html, response.url)
is_ok, reason = quality.is_acceptable()

if is_ok:
    # Convert to Markdown
    config = load_config()
    converter = ObsidianMarkdownConverter(config)
    markdown = converter.convert(clean_html, response.url)
    print(markdown)
else:
    print(f"Content rejected: {reason}")
```
