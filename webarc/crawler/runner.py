"""Main crawler runner that orchestrates the full pipeline."""

import logging
import hashlib
from pathlib import Path
from typing import Dict, Any, Optional, Iterable, List, Set
from datetime import datetime
from urllib.parse import urlparse
import xml.etree.ElementTree as ET

from scrapy.crawler import CrawlerProcess

from webarc.config.loader import load_config
from webarc.config.schema import WebArcConfig
from webarc.crawler.spider import WebArcSpider
from webarc.crawler.settings import get_scrapy_settings
from webarc.crawler.state import StateManager
from webarc.extractors.quality import ContentQuality
from webarc.adapters.router import AdapterRouter
from webarc.html2md.converter import ObsidianMarkdownConverter
from webarc.output.writer import OutputWriter
from webarc.output.manifest import ManifestWriter

try:
    import requests
except ImportError:  # pragma: no cover - requests is in requirements
    requests = None

logger = logging.getLogger(__name__)


class ExtractionPipeline:
    """
    Shared extraction pipeline used by crawler and direct fetch workflows.
    """

    def __init__(
        self,
        config: WebArcConfig,
        output_dir: Path,
        output_writer: OutputWriter,
        manifest_writer: ManifestWriter,
        adapter_router: AdapterRouter,
        markdown_converter: ObsidianMarkdownConverter,
    ):
        self.config = config
        self.output_dir = output_dir
        self.output_writer = output_writer
        self.manifest_writer = manifest_writer
        self.adapter_router = adapter_router
        self.markdown_converter = markdown_converter

    def process(self, url: str, html: str, status: int = 200) -> Dict[str, Any]:
        """
        Run extraction pipeline for a single page.

        Returns dict with keys:
            success: bool
            reason: Optional[str]
            file_path: Optional[Path]
            quality: Optional[ContentQuality]
            metadata: Optional[Dict[str, Any]]
        """
        result: Dict[str, Any] = {
            'success': False,
            'reason': None,
            'file_path': None,
            'quality': None,
            'metadata': None,
        }

        quality = ContentQuality(html, url)
        is_acceptable, reason = quality.is_acceptable(
            min_content_density=self.config.extraction.min_content_density,
            min_content_length=self.config.extraction.min_content_length,
            min_word_count=self.config.extraction.min_word_count,
            max_nav_link_ratio=self.config.extraction.max_nav_link_ratio,
            min_paragraph_count=self.config.extraction.min_paragraph_count,
            require_heading=self.config.extraction.require_heading,
        )

        if not is_acceptable:
            result['reason'] = reason
            return result

        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, 'lxml')
        adapter = self.adapter_router.get_adapter(url, html)
        extracted = adapter.extract_content(soup, url)

        markdown = self.markdown_converter.convert(extracted['body_html'], url)
        content_hash = hashlib.sha256(markdown.encode('utf-8')).hexdigest()

        metadata = {
            'title': extracted['title'],
            'source_url': url,
            'canonical_url': url,
            'version': extracted.get('version'),
            'lang': extracted.get('lang', 'en'),
            'framework': extracted.get('framework'),
            'adapter': adapter.__class__.__name__,
            'fetched_at': datetime.utcnow().isoformat() + 'Z',
            'render_type': 'static',
            'content_hash': f"sha256:{content_hash}",
            'quality': {
                'status': 'ok',
                'content_density': quality.content_density,
                'word_count': quality.word_count,
                'paragraph_count': quality.paragraph_count,
                'heading_count': quality.heading_count,
            },
        }

        content_dict = {
            'markdown': markdown,
            'metadata': metadata,
            'content_hash': content_hash,
        }

        file_path = self.output_writer.write_page(url, content_dict)

        manifest_entry = {
            'url': url,
            'canonical_url': url,
            'file_path': str(file_path.relative_to(self.output_dir)),
            'title': extracted['title'],
            'content_hash': f"sha256:{content_hash}",
            'fetched_at': metadata['fetched_at'],
            'http_status': status,
            'render_type': 'static',
            'word_count': quality.word_count,
            'framework': extracted.get('framework'),
            'adapter': adapter.__class__.__name__,
            'quality_status': 'ok',
            'content_density': quality.content_density,
        }
        self.manifest_writer.write_manifest_entry(manifest_entry)

        result.update(
            success=True,
            file_path=file_path,
            quality=quality,
            metadata=metadata,
        )
        return result


class WebArcCrawler:
    """
    Main crawler orchestrator that runs the full pipeline.
    """
    
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
        download_only: bool = False,
    ):
        """
        Initialize WebArc crawler.
        
        Args:
            seed_url: Starting URL
            config: WebArc configuration
            output_dir: Output directory
            max_depth: Maximum crawl depth
            allowed_domain: Domain restriction
            allowed_prefix: Path prefix restriction
            visited_urls: Set of already-visited URLs (for resume)
        """
        self.seed_url = seed_url
        self.config = config or load_config()
        self.output_dir = Path(output_dir)
        self.max_depth = max_depth
        self.allowed_domain = allowed_domain or self.config.allow_domain
        self.allowed_prefix = allowed_prefix or self.config.allow_prefix
        self.visited_urls = visited_urls or set()
        self.version_lock = version_lock
        # DISABLED: Sitemap expansion was adding URLs from multiple versions
        # Rely only on link following with strict filter instead
        self.extra_seed_urls = []
        self.download_only = download_only
        
        # Queue directory for download-only mode
        if self.download_only:
            self.queue_dir = self.output_dir / '_queue'
            self.queue_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize components
        self.output_writer = OutputWriter(self.output_dir, self.config)
        self.manifest_writer = ManifestWriter(self.output_dir)
        self.adapter_router = AdapterRouter(self.config)
        self.markdown_converter = ObsidianMarkdownConverter(self.config)
        self.pipeline = ExtractionPipeline(
            config=self.config,
            output_dir=self.output_dir,
            output_writer=self.output_writer,
            manifest_writer=self.manifest_writer,
            adapter_router=self.adapter_router,
            markdown_converter=self.markdown_converter,
        )
        self.state_manager = StateManager(self.output_dir)
        
        # Statistics
        self.stats = {
            'pages_crawled': 0,
            'pages_extracted': 0,
            'pages_skipped': 0,
            'errors': 0,
        }
        
        # Track spider instance for state checkpointing
        self.spider_instance = None
    
    def run(self) -> Dict[str, Any]:
        """
        Run the crawler.
        
        Returns:
            Dictionary with crawl statistics
        """
        logger.info(f"Starting crawl: {self.seed_url}")
        
        # Get Scrapy settings
        scrapy_settings = get_scrapy_settings(self.config)
        scrapy_settings['ALLOWED_DOMAIN'] = self.allowed_domain
        scrapy_settings['ALLOWED_PREFIX'] = self.allowed_prefix
        
        # Create crawler process
        process = CrawlerProcess(scrapy_settings)
        
        # Add spider with callback
        process.crawl(
            WebArcSpider,
            seed_url=self.seed_url,
            config=self.config,
            allowed_domain=self.allowed_domain,
            allowed_prefix=self.allowed_prefix,
            max_depth=self.max_depth,
            visited_urls=self.visited_urls,
            version_lock=self.version_lock,
            extra_seed_urls=self.extra_seed_urls,
        )
        
        # Start crawling (blocking)
        process.start()
        
        return self.stats
    
    def process_response(self, response, spider: WebArcSpider):
        """
        Process a crawled response through the full pipeline.
        
        Args:
            response: Scrapy Response object
            spider: Spider instance
        """
        self.stats['pages_crawled'] += 1
        
        url = response.url
        
        # STRICT FILTER: Only process URLs that start with the exact seed URL prefix
        seed_prefix = '/'.join(self.seed_url.split('/')[:7])  # Get up to /en
        if not url.startswith(seed_prefix):
            logger.debug(f"Skipping {url} in process_response: does not start with {seed_prefix}")
            self.stats['pages_skipped'] += 1
            return
        
        # Skip binary files (images, archives, etc.)
        content_type = response.headers.get('Content-Type', b'').decode('utf-8', errors='ignore').lower()
        if content_type and not any(ct in content_type for ct in ['text/html', 'text/plain', 'application/xhtml']):
            logger.debug(f"Skipping binary file {url}: Content-Type {content_type}")
            self.stats['pages_skipped'] += 1
            return
        
        # Check if response is text (raises AttributeError for binary)
        try:
            html = response.text
        except AttributeError:
            logger.debug(f"Skipping binary file {url}: Response content isn't text")
            self.stats['pages_skipped'] += 1
            return
        
        # Download-only mode: just save HTML to queue, don't process
        if self.download_only:
            import hashlib
            import json
            from urllib.parse import urlparse
            
            # Create queue entry
            url_hash = hashlib.sha256(url.encode()).hexdigest()[:16]
            queue_file = self.queue_dir / f"{url_hash}.html"
            meta_file = self.queue_dir / f"{url_hash}.json"
            
            # Save HTML
            queue_file.write_text(html, encoding='utf-8')
            
            # Save metadata
            meta = {
                'url': url,
                'status': response.status,
                'content_type': content_type,
                'fetched_at': datetime.utcnow().isoformat() + 'Z',
            }
            meta_file.write_text(json.dumps(meta), encoding='utf-8')
            
            logger.debug(f"Queued {url} for processing")
            self.stats['pages_extracted'] += 1  # Count as "extracted" in download-only mode
            return
        
        # Normal mode: process through pipeline
        try:
            pipeline_result = self.pipeline.process(url, html, response.status)
        except Exception as e:  # pragma: no cover - defensive coverage
            logger.error(f"Error processing {response.url}: {e}")
            self.stats['errors'] += 1
            error_entry = {
                'url': response.url,
                'error_type': 'PROCESSING_ERROR',
                'error_message': str(e),
                'attempted_at': datetime.utcnow().isoformat() + 'Z',
            }
            self.manifest_writer.write_error_entry(error_entry)
            return

        if not pipeline_result['success']:
            logger.debug(f"Skipping {url}: {pipeline_result['reason']}")
            self.stats['pages_skipped'] += 1
            return
        
        self.stats['pages_extracted'] += 1
        
        crawler_state = {
            'seed_url': self.seed_url,
            'config_hash': '',  # TODO: hash config
            'pages_crawled': self.stats['pages_crawled'],
            'pages_extracted': self.stats['pages_extracted'],
            'pages_skipped': self.stats['pages_skipped'],
            'pages_failed': self.stats['errors'],
            'queue': list(spider.visited_urls),  # Approximate queue as visited URLs
            'visited': list(spider.visited_urls),
            'status': 'running',
            'max_depth': self.max_depth,
            'allowed_domain': self.allowed_domain,
            'allowed_prefix': self.allowed_prefix,
        }
        self.state_manager.maybe_checkpoint(crawler_state)
            
    def _load_version_seed_urls(self) -> List[str]:
        """
        Load additional seed URLs for the locked version using sitemaps.
        """
        if requests is None:
            logger.info("Requests unavailable; skipping sitemap expansion.")
            return []

        version_segment = self.version_lock.strip('/')
        if not version_segment:
            return []

        parsed_seed = urlparse(self.seed_url)
        base_domain = parsed_seed.netloc
        sitemap_index_url = f"https://{base_domain}/sitemap.xml"
        headers = {'User-Agent': self.config.crawler.user_agent}

        try:
            index_resp = requests.get(sitemap_index_url, headers=headers, timeout=30)
            index_resp.raise_for_status()
        except Exception as exc:
            logger.warning(f"Failed to load sitemap index: {exc}")
            return []

        sitemap_urls = _extract_sitemap_urls(index_resp.text)
        version_urls: Set[str] = set()
        prefix = f"https://{base_domain}/en/appdynamics-saas/"

        for sitemap_url in sitemap_urls:
            if 'appdynamics-saas' not in sitemap_url:
                continue
            try:
                sm_resp = requests.get(sitemap_url, headers=headers, timeout=30)
                sm_resp.raise_for_status()
            except Exception:
                continue
            for url in _extract_sitemap_urls(sm_resp.text):
                # STRICT FILTER: Only include URLs that start with the exact seed URL prefix
                seed_prefix = '/'.join(self.seed_url.split('/')[:7])  # Get up to /en
                if not url.startswith(seed_prefix):
                    continue
                version_urls.add(url)

        version_urls.discard(self.seed_url)
        logger.info(f"Sitemap expansion added {len(version_urls)} URLs for version {self.version_lock}")
        return sorted(version_urls)


def _extract_sitemap_urls(xml_text: str) -> List[str]:
    urls: List[str] = []
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return urls

    for element in root.iter():
        if element.tag.endswith('loc') and element.text:
            urls.append(element.text.strip())
    return urls


class WebArcFetcher:
    """
    Fetch a list of URLs without crawling.
    """

    def __init__(
        self,
        config: Optional[WebArcConfig] = None,
        output_dir: Path = Path("./out"),
    ):
        self.config = config or load_config()
        self.output_dir = Path(output_dir)
        self.output_writer = OutputWriter(self.output_dir, self.config)
        self.manifest_writer = ManifestWriter(self.output_dir)
        self.adapter_router = AdapterRouter(self.config)
        self.markdown_converter = ObsidianMarkdownConverter(self.config)
        self.pipeline = ExtractionPipeline(
            config=self.config,
            output_dir=self.output_dir,
            output_writer=self.output_writer,
            manifest_writer=self.manifest_writer,
            adapter_router=self.adapter_router,
            markdown_converter=self.markdown_converter,
        )
        self.stats = {
            'pages_fetched': 0,
            'pages_extracted': 0,
            'pages_skipped': 0,
            'errors': 0,
        }

    def fetch(self, urls: Iterable[str]) -> Dict[str, Any]:
        if requests is None:
            raise RuntimeError("The requests library is required for fetch mode.")

        for url in urls:
            if not url:
                continue

            try:
                response = requests.get(
                    url,
                    timeout=self.config.crawler.download_timeout,
                    headers={'User-Agent': self.config.crawler.user_agent},
                )
            except Exception as exc:
                logger.error(f"Failed to fetch {url}: {exc}")
                self.stats['errors'] += 1
                continue

            self.stats['pages_fetched'] += 1

            if response.status_code != 200:
                logger.warning(
                    f"Skipping {url}: HTTP {response.status_code}"
                )
                self.stats['pages_skipped'] += 1
                continue

            result = self.pipeline.process(url, response.text, response.status_code)

            if not result['success']:
                logger.debug(f"Skipping {url}: {result['reason']}")
                self.stats['pages_skipped'] += 1
                continue

            self.stats['pages_extracted'] += 1

        return self.stats
