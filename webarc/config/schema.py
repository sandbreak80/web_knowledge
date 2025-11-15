"""Configuration schema for WebArc using Pydantic."""

from typing import List, Optional
from pydantic import BaseModel, Field


class CrawlerConfig(BaseModel):
    """Crawler configuration settings."""
    max_depth: int = 3
    concurrent_requests: int = 16  # Increased for faster crawling
    concurrent_requests_per_domain: int = 10  # Increased for faster extraction
    download_delay: float = 0.1  # Reduced delay for faster processing
    download_timeout: int = 30
    max_page_size_mb: int = 10
    retry_times: int = 2
    user_agent: str = "WebArc/1.0 (+https://github.com/yourorg/webarc) Documentation Archiver"
    
    # Auto-throttle settings
    autothrottle_enabled: bool = True
    autothrottle_start_delay: int = 1
    autothrottle_max_delay: int = 10
    autothrottle_target_concurrency: float = 10.0  # Increased for faster extraction
    
    # Memory management
    memusage_enabled: bool = True
    memusage_limit_mb: int = 1024
    memusage_warning_mb: int = 768
    
    # Response limits
    download_maxsize: int = 10485760  # 10MB
    download_warnsize: int = 5242880  # 5MB


class SafetyConfig(BaseModel):
    """Safety guard configuration."""
    mode: str = "advisory"  # "advisory" or "enforce"
    respect_robots_txt: bool = True
    same_domain_only: bool = True
    max_url_length: int = 2000
    max_query_params: int = 10
    max_pagination_depth: int = 50
    entropy_threshold: float = 3.5
    max_redirects: int = 10
    
    blocked_patterns: List[str] = Field(default_factory=lambda: [
        ".*/auth/.*",
        ".*/login/.*",
        ".*/search\\?.*",
        ".*/api/.*",
        ".*\\.(zip|exe|dmg|pkg)$",
    ])
    
    pagination_keywords: List[str] = Field(default_factory=lambda: [
        "page",
        "offset",
        "start",
        "limit",
        "skip",
    ])
    
    use_blocklist: bool = True
    blocklist_path: str = "./lists/stevenblack_hosts.txt"


class RenderConfig(BaseModel):
    """JavaScript rendering configuration."""
    static_first: bool = True
    js_timeout_ms: int = 15000
    js_network_idle_ms: int = 5000
    browser_pool_size: int = 3
    reuse_contexts: bool = True
    disable_images: bool = True
    force_js: bool = False
    
    js_detection_triggers: List[str] = Field(default_factory=lambda: [
        "Loading...",
        "Please wait",
        "data-react-root",
        "data-reactroot",
        "ng-app",
        "vue-app",
        "<div id=\"root\"></div>",
        "<div id=\"app\"></div>",
    ])
    
    browser_args: List[str] = Field(default_factory=lambda: [
        "--no-sandbox",
        "--disable-dev-shm-usage",
        "--disable-gpu",
    ])


class ExtractionConfig(BaseModel):
    """Content extraction configuration."""
    min_content_density: float = 0.3
    min_content_length: int = 100
    min_word_count: int = 50
    max_nav_link_ratio: float = 0.5
    min_paragraph_count: int = 1
    require_heading: bool = True
    
    preserve_html_tags: List[str] = Field(default_factory=lambda: [
        "table",
        "pre",
        "code",
        "img",
        "blockquote",
    ])
    
    check_language: bool = True
    detect_paywalls: bool = True
    detect_captcha: bool = True


class OutputConfig(BaseModel):
    """Output format configuration."""
    format: str = "obsidian"
    obsidian_link_style: str = "wikilink"  # "wikilink" or "markdown"
    relative_links: bool = True
    preserve_anchors: bool = True
    slug_strategy: str = "url-path"  # "url-path" or "title-based"
    max_filename_length: int = 200
    deduplicate: str = "content-hash"  # "content-hash" or "url-canonical"
    
    image_mode: str = "ignore"  # "ignore", "download", or "embed"
    image_max_size_mb: int = 5
    image_embed_max_kb: int = 50
    image_formats: List[str] = Field(default_factory=lambda: [
        "png",
        "jpg",
        "jpeg",
        "gif",
        "svg",
    ])
    
    create_index: bool = True
    preserve_directory_structure: bool = True
    output_encoding: str = "utf-8"
    normalize_unicode: str = "NFC"


class LoggingConfig(BaseModel):
    """Logging configuration."""
    level: str = "INFO"  # DEBUG, INFO, WARNING, ERROR
    format: str = "json"  # "json" or "text"
    file: str = "./logs/webarc.log"
    rotate: bool = True
    max_log_size_mb: int = 100
    backup_count: int = 5
    show_progress: bool = True
    progress_update_interval: int = 1


class ConfluenceAdapterConfig(BaseModel):
    """Confluence adapter configuration."""
    enabled: bool = True
    domains: List[str] = Field(default_factory=lambda: ["docs.appdynamics.com"])
    content_selector: str = ".confluence-content"
    remove_selectors: List[str] = Field(default_factory=lambda: [
        ".ia-fixed-sidebar",
        ".page-metadata",
        ".footer",
    ])


class MkDocsAdapterConfig(BaseModel):
    """MkDocs adapter configuration."""
    enabled: bool = True
    content_selector: str = ".md-content"
    remove_selectors: List[str] = Field(default_factory=lambda: [
        ".md-sidebar",
        ".md-header",
    ])


class SphinxAdapterConfig(BaseModel):
    """Sphinx adapter configuration."""
    enabled: bool = True
    content_selector: str = "div.body"
    remove_selectors: List[str] = Field(default_factory=lambda: [
        ".sphinxsidebar",
        ".related",
    ])


class SquarespaceAdapterConfig(BaseModel):
    """Squarespace adapter configuration."""
    enabled: bool = True
    content_selectors: List[str] = Field(default_factory=lambda: [
        'main',
        '[data-content-field="main-content"]',
        '.sqs-layout',
        '.Index-page-content',
    ])
    remove_selectors: List[str] = Field(default_factory=lambda: [
        'header',
        'footer',
        '.sqs-announcement-bar',
        '.sqs-popup-overlay',
    ])


class NewsAdapterConfig(BaseModel):
    """Generic news/article adapter configuration."""
    enabled: bool = True
    content_selectors: List[str] = Field(default_factory=lambda: [
        'article',
        'main',
        '[role="main"]',
        '.article-body',
        '.story-body',
    ])
    remove_selectors: List[str] = Field(default_factory=lambda: [
        'header',
        'footer',
        '.advertisement',
        '.social-share',
        '.share-tools',
        '.story-meta',
        '.byline__meta',
    ])


class RedditAdapterConfig(BaseModel):
    """Reddit adapter configuration."""
    enabled: bool = True
    use_json_api: bool = True
    request_timeout: int = 15
    user_agent: str = "WebArc/1.0 (+https://github.com/yourorg/webarc) RedditAdapter"


class AdaptersConfig(BaseModel):
    """Site-specific adapter configurations."""
    confluence: ConfluenceAdapterConfig = Field(default_factory=ConfluenceAdapterConfig)
    mkdocs: MkDocsAdapterConfig = Field(default_factory=MkDocsAdapterConfig)
    sphinx: SphinxAdapterConfig = Field(default_factory=SphinxAdapterConfig)
    squarespace: SquarespaceAdapterConfig = Field(default_factory=SquarespaceAdapterConfig)
    news: NewsAdapterConfig = Field(default_factory=NewsAdapterConfig)
    reddit: RedditAdapterConfig = Field(default_factory=RedditAdapterConfig)


class WebArcConfig(BaseModel):
    """Complete WebArc configuration."""
    crawler: CrawlerConfig = Field(default_factory=CrawlerConfig)
    safety: SafetyConfig = Field(default_factory=SafetyConfig)
    render: RenderConfig = Field(default_factory=RenderConfig)
    extraction: ExtractionConfig = Field(default_factory=ExtractionConfig)
    output: OutputConfig = Field(default_factory=OutputConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    adapters: AdaptersConfig = Field(default_factory=AdaptersConfig)
    
    # CLI overrides (not in YAML)
    allow_domain: Optional[str] = None
    allow_prefix: Optional[str] = None
    force_adapter: Optional[str] = None
