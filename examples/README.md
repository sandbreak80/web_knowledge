# WebArc Example Outputs

This directory contains example outputs from WebArc crawls to help you understand the output format and structure.

## Example Structure

After crawling a documentation site, WebArc creates the following structure:

```
out/
├── manifest.jsonl          # Index of all crawled pages
├── graph.jsonl            # Link graph between pages
├── errors.jsonl           # Errors encountered during crawl
├── resume.jsonl           # Resume state (if crawl was interrupted)
└── pages/                 # Extracted Markdown files
    ├── index.md
    ├── getting-started.md
    ├── api-reference.md
    └── ...
```

## Example Markdown File

Here's what a typical extracted Markdown file looks like:

```markdown
---
title: "Getting Started with WebArc"
source_url: "https://docs.example.com/getting-started"
canonical_url: "https://docs.example.com/getting-started"
version: "1.0"
lang: "en"
framework: "mkdocs"
adapter: "MkDocsAdapter"
fetched_at: "2025-11-11T18:00:00Z"
render_type: "static"
content_hash: "sha256:abc123..."
quality:
  status: "ok"
  content_density: 0.75
  word_count: 450
  heading_count: 5
---

# Getting Started with WebArc

WebArc is a local-first web crawler that extracts documentation sites into Obsidian-compatible Markdown files.

## Features

- **Local-first**: No cloud dependencies
- **Safe**: Multiple safety guards prevent accidental scraping
- **Configurable**: Extensive configuration options
- **Resumable**: Can resume interrupted crawls

## Installation

See the [[installation]] guide for detailed instructions.

## Quick Start

```bash
docker compose run --rm webarc crawl --seed https://docs.example.com
```

This will crawl the documentation site and extract all pages into Markdown files.
```

## Example manifest.jsonl

Each line is a JSON object representing one crawled page:

```json
{"url": "https://docs.example.com/getting-started", "file_path": "pages/getting-started.md", "title": "Getting Started", "word_count": 450, "adapter": "MkDocsAdapter", "quality_status": "ok"}
{"url": "https://docs.example.com/api-reference", "file_path": "pages/api-reference.md", "title": "API Reference", "word_count": 1200, "adapter": "MkDocsAdapter", "quality_status": "ok"}
```

## Example graph.jsonl

Each line represents a link between pages:

```json
{"source_url": "https://docs.example.com/getting-started", "target_url": "https://docs.example.com/api-reference", "link_type": "internal"}
{"source_url": "https://docs.example.com/getting-started", "target_url": "https://docs.example.com/installation", "link_type": "internal"}
```

## Example errors.jsonl

Each line represents an error encountered during crawling:

```json
{"url": "https://docs.example.com/broken-page", "error": "HTTP 404", "timestamp": "2025-11-11T18:00:00Z"}
{"url": "https://docs.example.com/timeout-page", "error": "Request timeout", "timestamp": "2025-11-11T18:00:00Z"}
```

## Using Examples

To see real examples:

1. Run a test crawl:
   ```bash
   docker compose run --rm webarc crawl --seed https://docs.example.com --depth 1
   ```

2. Check the output:
   ```bash
   ls -la out/pages/
   cat out/manifest.jsonl
   ```

3. View statistics:
   ```bash
   docker compose run --rm webarc stats --output-dir out/
   ```

## Notes

- All example files use Obsidian-compatible Markdown format
- Links are converted to wikilinks (`[[link]]`) by default
- YAML front-matter contains metadata about each page
- Files are organized by URL path structure
