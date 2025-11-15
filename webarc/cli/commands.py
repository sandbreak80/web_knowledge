"""CLI commands for WebArc."""

import re
import typer
from rich.console import Console
from typing import List, Optional
from pathlib import Path

from webarc.config.loader import load_config
from webarc.crawler.runner import WebArcFetcher

app = typer.Typer(
    name="webarc",
    help="Local web documentation to Obsidian Markdown extractor",
    add_completion=False,
)

console = Console()


def _load_urls(cli_urls: List[str], urls_file: Optional[Path]) -> List[str]:
    """
    Merge CLI URLs with optional file-provided URLs, filtering duplicates/comments.
    """
    urls: List[str] = list(cli_urls)

    if urls_file:
        file_urls = [
            line.strip()
            for line in urls_file.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.strip().startswith("#")
        ]
        urls.extend(file_urls)

    seen = set()
    unique_urls: List[str] = []
    for item in urls:
        if item not in seen:
            seen.add(item)
            unique_urls.append(item)

    if not unique_urls:
        console.print("[bold red]Error:[/bold red] No URLs provided. Use --url or --urls-file.")
        raise typer.Exit(6)

    return unique_urls


@app.command()
def plan(
    seed: str = typer.Option(..., "--seed", help="Seed URL to start crawl"),
    allow_domain: Optional[str] = typer.Option(None, "--allow-domain", help="Restrict to this domain"),
    allow_prefix: Optional[str] = typer.Option(None, "--allow-prefix", help="Only crawl URLs with this prefix"),
    depth: int = typer.Option(3, "--depth", "-d", help="Maximum crawl depth"),
    show_rules: bool = typer.Option(False, "--show-rules", help="Display safety rules that would apply"),
    estimate: bool = typer.Option(False, "--estimate", help="Estimate page count from sitemap"),
    min_content_density: Optional[float] = typer.Option(
        None,
        "--min-content-density",
        help="Override minimum content density required to extract a page (default 0.3)",
    ),
    min_word_count: Optional[int] = typer.Option(
        None,
        "--min-word-count",
        help="Override minimum word count required to extract a page (default 50)",
    ),
):
    """
    Preview crawl plan without actually fetching pages.
    
    Shows:
    - Domain restrictions
    - Safety rules that would apply
    - Estimated page count (if sitemap available)
    - Configuration summary
    """
    console.print("[bold blue]WebArc Crawl Plan[/bold blue]\n")
    
    if depth < 0:
        console.print("[bold red]Error:[/bold red] Depth must be non-negative.")
        raise typer.Exit(1)
    
    # Load config
    config = load_config()

    # Apply extraction overrides
    if min_content_density is not None:
        config.extraction.min_content_density = min_content_density
    if min_word_count is not None:
        config.extraction.min_word_count = min_word_count
    
    # Display plan
    console.print(f"[green]Seed URL:[/green] {seed}")
    console.print(f"[green]Max Depth:[/green] {depth}")
    
    if allow_domain:
        console.print(f"[green]Domain Restriction:[/green] {allow_domain}")
    
    if allow_prefix:
        console.print(f"[green]Path Prefix:[/green] {allow_prefix}")
    
    console.print("\n[bold]Configuration:[/bold]")
    console.print(f"  Safety Mode: {config.safety.mode}")
    console.print(f"  Respect robots.txt: {config.safety.respect_robots_txt}")
    console.print(f"  JavaScript Rendering: {'Enabled' if config.render.static_first else 'Disabled'}")
    console.print(f"  Output Format: {config.output.format}")
    
    if show_rules:
        console.print("\n[bold]Safety Rules:[/bold]")
        console.print(f"  Max URL Length: {config.safety.max_url_length}")
        console.print(f"  Max Query Params: {config.safety.max_query_params}")
        console.print(f"  Entropy Threshold: {config.safety.entropy_threshold}")
        console.print(f"  Pagination Limit: {config.safety.max_pagination_depth}")
        
        if config.safety.blocked_patterns:
            console.print("\n  Blocked Patterns:")
            for pattern in config.safety.blocked_patterns:
                console.print(f"    - {pattern}")
    
    if estimate:
        console.print("\n[bold]Fetching sitemap...[/bold]")
        from webarc.crawler.planner import CrawlPlanner
        
        planner = CrawlPlanner(
            seed_url=seed,
            config=config,
            allowed_domain=allow_domain,
            allowed_prefix=allow_prefix,
            max_depth=depth,
        )
        
        plan = planner.plan()
        
        if plan.get('error'):
            console.print(f"[red]Error:[/red] {plan['error']}")
        elif plan.get('estimated_pages'):
            console.print(f"[green]Estimated pages:[/green] {plan['estimated_pages']}")
            if plan.get('sitemap_urls'):
                console.print(f"[green]Sitemap URLs found:[/green] {len(plan['sitemap_urls'])}")
        else:
            console.print("[yellow]No sitemap found or sitemap is empty[/yellow]")
    
    console.print("\n[dim]Run with 'webarc crawl' to execute this plan[/dim]")


@app.command()
def crawl(
    seed: str = typer.Option(..., "--seed", help="Seed URL to start crawl"),
    allow_domain: Optional[str] = typer.Option(None, "--allow-domain", help="Restrict to this domain"),
    allow_prefix: Optional[str] = typer.Option(None, "--allow-prefix", help="Only crawl URLs with this prefix"),
    depth: int = typer.Option(3, "--depth", "-d", help="Maximum crawl depth"),
    out: str = typer.Option("./out", "--out", "-o", help="Output directory"),
    force_js: bool = typer.Option(False, "--force-js", help="Force JavaScript rendering for all pages"),
    ignore_robots: bool = typer.Option(False, "--ignore-robots", help="Ignore robots.txt (use carefully)"),
    config_file: Optional[str] = typer.Option(None, "--config", "-c", help="Config file path"),
    min_content_density: Optional[float] = typer.Option(
        None,
        "--min-content-density",
        help="Override minimum content density required to extract a page (default 0.3)",
    ),
    min_word_count: Optional[int] = typer.Option(
        None,
        "--min-word-count",
        help="Override minimum word count required to extract a page (default 50)",
    ),
    user_agent: Optional[str] = typer.Option(
        None,
        "--user-agent",
        help="Override crawler User-Agent header",
    ),
    version_lock: Optional[str] = typer.Option(
        None,
        "--version-lock",
        help="Restrict crawl to URLs containing this version segment (e.g. /25.10.0/)",
    ),
    download_only: bool = typer.Option(
        False,
        "--download-only",
        help="Download HTML only, queue for later processing (faster crawling)",
    ),
):
    """
    Execute crawl and extract content.
    """
    from pathlib import Path
    from webarc.crawler.runner import WebArcCrawler
    
    console.print("[bold blue]WebArc Crawler[/bold blue]\n")
    
    # Load config
    config = load_config(config_file)
    
    # Override config with CLI args
    if force_js:
        config.render.force_js = True
    if ignore_robots:
        config.safety.respect_robots_txt = False
    if min_content_density is not None:
        config.extraction.min_content_density = min_content_density
    if min_word_count is not None:
        config.extraction.min_word_count = min_word_count
    if user_agent:
        config.crawler.user_agent = user_agent

    if version_lock is None:
        match = re.search(r'/(\d+\.\d+\.\d+)/', seed)
        if match:
            version_lock = f"/{match.group(1)}/"
    
    # Initialize crawler
    crawler = WebArcCrawler(
        seed_url=seed,
        config=config,
        output_dir=Path(out),
        max_depth=depth,
        allowed_domain=allow_domain,
        allowed_prefix=allow_prefix,
        version_lock=version_lock,
        download_only=download_only,
    )
    
    # Link crawler instance to spider
    # This is a workaround - in production, use proper Scrapy signals
    import webarc.crawler.spider
    webarc.crawler.spider.WebArcSpider.crawler_instance = crawler
    
    # Run crawl
    try:
        results = crawler.run()
        
        # Display results
        console.print("\n[bold green]✓ Crawl Complete[/bold green]\n")
        console.print(f"[green]Pages crawled:[/green] {results['pages_crawled']}")
        console.print(f"[green]Pages extracted:[/green] {results['pages_extracted']}")
        console.print(f"[green]Pages skipped:[/green] {results['pages_skipped']}")
        console.print(f"[red]Errors:[/red] {results['errors']}")
        console.print(f"\n[green]Output:[/green] {out}")
        
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted by user[/yellow]")
        console.print("Run 'webarc resume' to continue")
        raise typer.Exit(5)
    
    except Exception as e:
        console.print(f"\n[bold red]Error:[/bold red] {e}")
        raise typer.Exit(2)


@app.command()
def fetch(
    url: List[str] = typer.Option(
        [],
        "--url",
        help="URL to fetch (repeatable)",
        show_default=False,
    ),
    urls_file: Optional[Path] = typer.Option(
        None,
        "--urls-file",
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        help="Path to file containing URLs (one per line)",
    ),
    out: str = typer.Option("./out", "--out", "-o", help="Output directory"),
    config_file: Optional[str] = typer.Option(None, "--config", "-c", help="Config file path"),
    min_content_density: Optional[float] = typer.Option(
        None,
        "--min-content-density",
        help="Override minimum content density required to extract a page (default 0.3)",
    ),
    min_word_count: Optional[int] = typer.Option(
        None,
        "--min-word-count",
        help="Override minimum word count required to extract a page (default 50)",
    ),
    user_agent: Optional[str] = typer.Option(
        None,
        "--user-agent",
        help="Override User-Agent header for direct fetches",
    ),
):
    """
    Fetch specific URLs without crawling.
    """
    console.print("[bold blue]WebArc Fetch[/bold blue]\n")

    config = load_config(config_file)

    if min_content_density is not None:
        config.extraction.min_content_density = min_content_density
    if min_word_count is not None:
        config.extraction.min_word_count = min_word_count
    if user_agent:
        config.crawler.user_agent = user_agent

    unique_urls = _load_urls(url, urls_file)

    fetcher = WebArcFetcher(config=config, output_dir=Path(out))

    try:
        stats = fetcher.fetch(unique_urls)
    except Exception as exc:
        console.print(f"\n[bold red]Error:[/bold red] {exc}")
        raise typer.Exit(2)

    console.print("\n[bold green]✓ Fetch Complete[/bold green]\n")
    console.print(f"[green]Pages requested:[/green] {len(unique_urls)}")
    console.print(f"[green]Pages fetched:[/green] {stats['pages_fetched']}")
    console.print(f"[green]Pages extracted:[/green] {stats['pages_extracted']}")
    console.print(f"[green]Pages skipped:[/green] {stats['pages_skipped']}")
    console.print(f"[red]Errors:[/red] {stats['errors']}")
    console.print(f"\n[green]Output:[/green] {out}")


@app.command()
def resume(
    state_file: str = typer.Option(..., "--state-file", help="Path to resume.jsonl state file"),
    out: str = typer.Option("./out", "--out", "-o", help="Output directory"),
    config_file: Optional[str] = typer.Option(None, "--config", "-c", help="Config file path"),
):
    """
    Resume an interrupted crawl from saved state.
    """
    from pathlib import Path
    from webarc.crawler.runner import WebArcCrawler
    import orjson
    
    console.print("[bold blue]Resuming Crawl[/bold blue]\n")
    
    # Load state
    state_path = Path(state_file)
    if not state_path.exists():
        console.print(f"[red]Error:[/red] State file not found: {state_file}")
        raise typer.Exit(1)
    
    try:
        with open(state_path, 'rb') as f:
            content = f.read()
            if not content:
                console.print("[red]Error:[/red] State file is empty")
                raise typer.Exit(1)
            state = orjson.loads(content)
    except Exception as e:
        console.print(f"[red]Error loading state:[/red] {e}")
        raise typer.Exit(1)
    
    # Validate state
    if not state.get('seed_url'):
        console.print("[red]Error:[/red] Invalid state file: missing seed_url")
        raise typer.Exit(1)
    
    # Load config
    config = load_config(config_file)
    
    # Display resume info
    console.print(f"[green]Seed URL:[/green] {state['seed_url']}")
    console.print(f"[green]Previously crawled:[/green] {state.get('pages_crawled', 0)} pages")
    console.print(f"[green]Visited URLs:[/green] {len(state.get('visited', []))}")
    
    # Initialize crawler with restored visited URLs
    visited_urls = set(state.get('visited', []))
    
    crawler = WebArcCrawler(
        seed_url=state['seed_url'],
        config=config,
        output_dir=Path(out),
        max_depth=state.get('max_depth', 3),
        allowed_domain=state.get('allowed_domain'),
        allowed_prefix=state.get('allowed_prefix'),
        visited_urls=visited_urls,
    )
    
    # Link crawler instance to spider
    import webarc.crawler.spider
    webarc.crawler.spider.WebArcSpider.crawler_instance = crawler
    
    console.print(f"\n[yellow]Note:[/yellow] Resuming with {len(visited_urls)} already-visited URLs")
    
    # Run crawl
    try:
        results = crawler.run()
        
        console.print("\n[bold green]✓ Resume Complete[/bold green]\n")
        console.print(f"[green]Pages crawled:[/green] {results['pages_crawled']}")
        console.print(f"[green]Pages extracted:[/green] {results['pages_extracted']}")
        console.print(f"[green]Pages skipped:[/green] {results['pages_skipped']}")
        console.print(f"[red]Errors:[/red] {results['errors']}")
        
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted by user[/yellow]")
        raise typer.Exit(5)
    except Exception as e:
        console.print(f"\n[bold red]Error:[/bold red] {e}")
        raise typer.Exit(2)


@app.command()
def validate(
    output_dir: str = typer.Option(..., "--output-dir", help="Output directory to validate"),
    check_links: bool = typer.Option(False, "--check-links", help="Verify internal links resolve"),
):
    """
    Validate extracted content.
    """
    from pathlib import Path
    import orjson
    
    console.print("[bold blue]Validating Output[/bold blue]\n")
    
    output_path = Path(output_dir)
    if not output_path.exists():
        console.print(f"[red]Error:[/red] Output directory not found: {output_dir}")
        raise typer.Exit(1)
    
    manifest_file = output_path / 'manifest.jsonl'
    if not manifest_file.exists():
        console.print(f"[red]Error:[/red] Manifest file not found: {manifest_file}")
        raise typer.Exit(1)
    
    # Read manifest entries
    entries = []
    try:
        with open(manifest_file, 'rb') as f:
            for line in f:
                if line.strip():
                    entries.append(orjson.loads(line))
    except Exception as e:
        console.print(f"[red]Error reading manifest:[/red] {e}")
        raise typer.Exit(1)
    
    console.print(f"[green]Found {len(entries)} manifest entries[/green]\n")
    
    # Validate files exist
    missing_files = []
    valid_files = 0
    
    for entry in entries:
        file_path = entry.get('file_path')
        if not file_path:
            missing_files.append({'entry': entry, 'reason': 'Missing file_path'})
            continue
        
        full_path = output_path / file_path
        if not full_path.exists():
            missing_files.append({'entry': entry, 'reason': f'File not found: {file_path}'})
        else:
            valid_files += 1
    
    # Display results
    if missing_files:
        console.print(f"[red]✗ {len(missing_files)} files missing:[/red]")
        for item in missing_files[:10]:  # Show first 10
            console.print(f"  - {item['entry'].get('url', 'unknown')}: {item['reason']}")
        if len(missing_files) > 10:
            console.print(f"  ... and {len(missing_files) - 10} more")
    else:
        console.print(f"[green]✓ All {valid_files} files exist[/green]")
    
    # Check links if requested
    if check_links:
        console.print("\n[bold]Checking internal links...[/bold]")
        graph_file = output_path / 'graph.jsonl'
        
        if graph_file.exists():
            graph_entries = []
            try:
                with open(graph_file, 'rb') as f:
                    for line in f:
                        if line.strip():
                            graph_entries.append(orjson.loads(line))
            except Exception as e:
                console.print(f"[yellow]Warning:[/yellow] Could not read graph.jsonl: {e}")
                graph_entries = []
            
            console.print(f"[green]Found {len(graph_entries)} link relationships[/green]")
            
            # Check if target URLs have corresponding files
            broken_links = []
            for graph_entry in graph_entries:
                target_url = graph_entry.get('target_url')
                # Find corresponding manifest entry
                found = False
                for entry in entries:
                    if entry.get('url') == target_url or entry.get('canonical_url') == target_url:
                        found = True
                        break
                
                if not found:
                    broken_links.append(graph_entry)
            
            if broken_links:
                console.print(f"[yellow]⚠ {len(broken_links)} links point to uncrawled pages[/yellow]")
            else:
                console.print("[green]✓ All links resolve[/green]")
        else:
            console.print("[yellow]Warning:[/yellow] graph.jsonl not found")
    
    console.print("\n[bold]Summary:[/bold]")
    console.print(f"  Total entries: {len(entries)}")
    console.print(f"  Valid files: {valid_files}")
    console.print(f"  Missing files: {len(missing_files)}")
    
    if missing_files:
        raise typer.Exit(1)


@app.command()
def process(
    queue_dir: str = typer.Option(..., "--queue-dir", help="Queue directory with downloaded HTML files"),
    out: str = typer.Option("./out", "--out", "-o", help="Output directory"),
    config_file: Optional[str] = typer.Option(None, "--config", "-c", help="Config file path"),
    min_content_density: Optional[float] = typer.Option(
        None,
        "--min-content-density",
        help="Override minimum content density required to extract a page (default 0.3)",
    ),
    min_word_count: Optional[int] = typer.Option(
        None,
        "--min-word-count",
        help="Override minimum word count required to extract a page (default 50)",
    ),
    threads: int = typer.Option(10, "--threads", "-t", help="Number of processing threads"),
    min_content_length: Optional[int] = typer.Option(
        None,
        "--min-content-length",
        help="Override minimum content length (default 100)",
    ),
    max_nav_link_ratio: Optional[float] = typer.Option(
        None,
        "--max-nav-link-ratio",
        help="Override maximum nav link ratio (default 0.5)",
    ),
    min_paragraph_count: Optional[int] = typer.Option(
        None,
        "--min-paragraph-count",
        help="Override minimum paragraph count (default 1)",
    ),
    require_heading: Optional[bool] = typer.Option(
        None,
        "--require-heading/--no-require-heading",
        help="Require headings (default True)",
    ),
    no_quality_checks: bool = typer.Option(
        False,
        "--no-quality-checks",
        help="Disable all quality checks - extract everything",
    ),
):
    """
    Process queued HTML files from download-only crawl.
    """
    from pathlib import Path
    import json
    import logging
    from concurrent.futures import ThreadPoolExecutor, as_completed
    from webarc.crawler.runner import ExtractionPipeline
    from webarc.output.writer import OutputWriter
    from webarc.output.manifest import ManifestWriter
    from webarc.adapters.router import AdapterRouter
    from webarc.html2md.converter import ObsidianMarkdownConverter
    
    logger = logging.getLogger(__name__)
    
    console.print("[bold blue]Processing Queue[/bold blue]\n")
    
    queue_path = Path(queue_dir).resolve()
    if not queue_path.exists():
        console.print(f"[red]Error:[/red] Queue directory not found: {queue_dir}")
        console.print(f"[yellow]Debug:[/yellow] Resolved path: {queue_path}")
        console.print(f"[yellow]Debug:[/yellow] Current working directory: {Path.cwd()}")
        raise typer.Exit(1)
    
    # Debug: list files in directory
    try:
        all_files = list(queue_path.iterdir())
        html_count = len(list(queue_path.glob("*.html")))
        console.print(f"[yellow]Debug:[/yellow] Directory contains {len(all_files)} files, {html_count} HTML files")
    except Exception as e:
        console.print(f"[yellow]Debug:[/yellow] Error listing directory: {e}")
    
    # Load config
    config = load_config(config_file)
    
    # Override config with CLI args
    if no_quality_checks:
        # Disable all quality checks - extract everything
        config.extraction.min_content_density = 0.0
        config.extraction.min_content_length = 0
        config.extraction.min_word_count = 0
        config.extraction.max_nav_link_ratio = 1.0
        config.extraction.min_paragraph_count = 0
        config.extraction.require_heading = False
        console.print("[yellow]Quality checks disabled - extracting all files[/yellow]\n")
    else:
        # Override individual thresholds if provided
        if min_content_density is not None:
            config.extraction.min_content_density = min_content_density
        if min_word_count is not None:
            config.extraction.min_word_count = min_word_count
        if min_content_length is not None:
            config.extraction.min_content_length = min_content_length
        if max_nav_link_ratio is not None:
            config.extraction.max_nav_link_ratio = max_nav_link_ratio
        if min_paragraph_count is not None:
            config.extraction.min_paragraph_count = min_paragraph_count
        if require_heading is not None:
            config.extraction.require_heading = require_heading
    
    # Initialize components
    output_path = Path(out)
    output_writer = OutputWriter(output_path, config)
    manifest_writer = ManifestWriter(output_path)
    adapter_router = AdapterRouter(config)
    markdown_converter = ObsidianMarkdownConverter(config)
    pipeline = ExtractionPipeline(
        config=config,
        output_dir=output_path,
        output_writer=output_writer,
        manifest_writer=manifest_writer,
        adapter_router=adapter_router,
        markdown_converter=markdown_converter,
    )
    
    # Find all HTML files in queue
    html_files = list(queue_path.glob("*.html"))
    console.print(f"[green]Found {len(html_files)} files to process[/green]\n")
    
    stats = {
        'processed': 0,
        'extracted': 0,
        'skipped': 0,
        'errors': 0,
    }
    
    def process_file(html_file: Path):
        """Process a single HTML file from the queue."""
        meta_file = html_file.with_suffix('.json')
        
        if not meta_file.exists():
            return {'status': 'error', 'reason': 'Missing metadata file'}
        
        try:
            # Load metadata
            meta = json.loads(meta_file.read_text(encoding='utf-8'))
            url = meta['url']
            status = meta.get('status', 200)
            
            # Load HTML
            html = html_file.read_text(encoding='utf-8')
            
            # Process through pipeline
            result = pipeline.process(url, html, status)
            
            # NEVER delete files - keep all files for potential reprocessing
            # Move processed files to _processed subdirectory
            processed_dir = queue_path / '_processed'
            processed_dir.mkdir(exist_ok=True)
            
            if result['success']:
                # Move successfully extracted files to _processed
                html_file.rename(processed_dir / html_file.name)
                meta_file.rename(processed_dir / meta_file.name)
                return {'status': 'extracted', 'url': url}
            else:
                # Move skipped files to _skipped for potential reprocessing
                skipped_dir = queue_path / '_skipped'
                skipped_dir.mkdir(exist_ok=True)
                html_file.rename(skipped_dir / html_file.name)
                meta_file.rename(skipped_dir / meta_file.name)
                return {'status': 'skipped', 'url': url, 'reason': result['reason']}
                
        except Exception as e:
            logger.error(f"Error processing {html_file}: {e}")
            return {'status': 'error', 'url': str(html_file), 'reason': str(e)}
    
    # Process files in parallel
    with ThreadPoolExecutor(max_workers=threads) as executor:
        futures = {executor.submit(process_file, html_file): html_file for html_file in html_files}
        
        with console.status("[bold green]Processing...") as status:
            for future in as_completed(futures):
                stats['processed'] += 1
                result = future.result()
                
                if result['status'] == 'extracted':
                    stats['extracted'] += 1
                elif result['status'] == 'skipped':
                    stats['skipped'] += 1
                else:
                    stats['errors'] += 1
                
                # Update status
                if stats['processed'] % 10 == 0:
                    status.update(f"[bold green]Processed {stats['processed']}/{len(html_files)} (extracted: {stats['extracted']}, skipped: {stats['skipped']}, errors: {stats['errors']})[/bold green]")
    
    # Display results
    console.print("\n[bold]Processing Complete[/bold]")
    console.print(f"  Processed: {stats['processed']}")
    console.print(f"  Extracted: {stats['extracted']}")
    console.print(f"  Skipped: {stats['skipped']} (moved to _skipped/ for reprocessing)")
    console.print(f"  Errors: {stats['errors']}")
    
    processed_dir = queue_path / '_processed'
    skipped_dir = queue_path / '_skipped'
    processed_count = len(list(processed_dir.glob("*.html"))) if processed_dir.exists() else 0
    skipped_count = len(list(skipped_dir.glob("*.html"))) if skipped_dir.exists() else 0
    
    console.print(f"\n[bold]File Status:[/bold]")
    console.print(f"  Processed (extracted): {processed_count} files in {processed_dir}")
    if stats['skipped'] > 0:
        console.print(f"  Skipped: {skipped_count} files in {skipped_dir}")
        console.print(f"\n[yellow]Note:[/yellow] All files are preserved (none deleted)")
        console.print(f"[yellow]You can reprocess skipped files with different quality thresholds:[/yellow]")
        console.print(f"[dim]  docker compose run --rm webarc process --queue-dir {skipped_dir} --out {out} --min-content-density 0.01 --min-word-count 1[/dim]")


@app.command()
def stats(
    output_dir: str = typer.Option(..., "--output-dir", help="Output directory to analyze"),
):
    """
    Analyze output statistics and relationships.
    """
    from pathlib import Path
    from collections import Counter
    import orjson
    
    console.print("[bold blue]Output Statistics[/bold blue]\n")
    
    output_path = Path(output_dir)
    if not output_path.exists():
        console.print(f"[red]Error:[/red] Output directory not found: {output_dir}")
        raise typer.Exit(1)
    
    manifest_file = output_path / 'manifest.jsonl'
    graph_file = output_path / 'graph.jsonl'
    errors_file = output_path / 'errors.jsonl'
    
    if not manifest_file.exists():
        console.print(f"[red]Error:[/red] Manifest file not found: {manifest_file}")
        raise typer.Exit(1)
    
    # Read manifest
    entries = []
    try:
        with open(manifest_file, 'rb') as f:
            for line in f:
                if line.strip():
                    entries.append(orjson.loads(line))
    except Exception as e:
        console.print(f"[yellow]Warning:[/yellow] Could not read manifest: {e}")
    
    # Read graph
    graph_entries = []
    if graph_file.exists():
        try:
            with open(graph_file, 'rb') as f:
                for line in f:
                    if line.strip():
                        graph_entries.append(orjson.loads(line))
        except Exception as e:
            console.print(f"[yellow]Warning:[/yellow] Could not read graph: {e}")
    
    # Read errors
    error_entries = []
    if errors_file.exists():
        try:
            with open(errors_file, 'rb') as f:
                for line in f:
                    if line.strip():
                        error_entries.append(orjson.loads(line))
        except Exception as e:
            console.print(f"[yellow]Warning:[/yellow] Could not read errors: {e}")
    
    # Calculate statistics
    total_pages = len(entries)
    total_words = sum(entry.get('word_count', 0) for entry in entries)
    avg_words = total_words / total_pages if total_pages > 0 else 0
    
    # Adapter distribution
    adapters = Counter(entry.get('adapter', 'unknown') for entry in entries)
    
    # Framework distribution
    frameworks = Counter(entry.get('framework', 'unknown') for entry in entries)
    
    # Quality status
    quality_statuses = Counter(entry.get('quality_status', 'unknown') for entry in entries)
    
    # Link statistics
    total_links = len(graph_entries)
    internal_links = sum(1 for e in graph_entries if e.get('link_type') == 'internal')
    
    # Display statistics
    console.print("[bold]Crawl Statistics[/bold]")
    console.print(f"  Total pages: {total_pages}")
    console.print(f"  Total words: {total_words:,}")
    console.print(f"  Average words per page: {avg_words:.0f}")
    console.print(f"  Total links: {total_links}")
    console.print(f"  Internal links: {internal_links}")
    console.print(f"  Errors: {len(error_entries)}")
    
    if adapters:
        console.print("\n[bold]Adapters Used[/bold]")
        for adapter, count in adapters.most_common():
            console.print(f"  {adapter}: {count}")
    
    if frameworks and frameworks.most_common(1)[0][0] != 'unknown':
        console.print("\n[bold]Frameworks Detected[/bold]")
        for framework, count in frameworks.most_common(5):
            if framework != 'unknown':
                console.print(f"  {framework}: {count}")
    
    if quality_statuses:
        console.print("\n[bold]Quality Status[/bold]")
        for status, count in quality_statuses.most_common():
            console.print(f"  {status}: {count}")
    
    # Top pages by word count
    if entries:
        top_pages = sorted(entries, key=lambda x: x.get('word_count', 0), reverse=True)[:5]
        console.print("\n[bold]Top Pages by Word Count[/bold]")
        for i, page in enumerate(top_pages, 1):
            title = page.get('title', 'Untitled')[:50]
            word_count = page.get('word_count', 0)
            console.print(f"  {i}. {title} ({word_count:,} words)")
    
    # Error summary
    if error_entries:
        error_types = Counter(e.get('error_type', 'unknown') for e in error_entries)
        console.print("\n[bold]Error Summary[/bold]")
        for error_type, count in error_types.most_common():
            console.print(f"  {error_type}: {count}")


def main():
    """Entry point for CLI."""
    app()


if __name__ == "__main__":
    main()
