# WebArc

A powerful, local-first web knowledge extraction tool that converts web content into structured, Obsidian-friendly Markdown for building personal knowledge bases.

## Overview

WebArc is designed to extract, process, and archive web documentation and content into a local, searchable knowledge base. It's perfect for:

- Archiving documentation sites
- Building personal knowledge bases
- Creating offline documentation
- Extracting structured content for RAG (Retrieval-Augmented Generation) systems

## Features

- **Smart Content Extraction**: Automatically detects and extracts main content using readability algorithms and site-specific adapters
- **Obsidian-Friendly Output**: Generates Markdown with YAML front-matter, wikilinks, and proper formatting
- **Site Adapters**: Specialized extractors for Confluence, MkDocs, Sphinx, Squarespace, Reddit, and more
- **Safety Guards**: Built-in protection against link farms, spam, and low-quality content
- **Version Locking**: Restrict crawls to specific documentation versions
- **Deduplication**: Automatic content deduplication with symlinks
- **Knowledge Graph**: Generates link relationships for graph-based navigation
- **Docker Support**: Fully containerized for easy deployment

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Python 3.11+ (for local development)

### Installation

```bash
# Clone the repository
git clone http://192.168.50.212:3000/bstoner/web_knowledge.git
cd web_knowledge

# Build the Docker image
docker compose build
```

### Basic Usage

```bash
# Crawl a single page
docker compose run --rm webarc crawl \
  --seed "https://example.com/docs" \
  --allow-domain example.com \
  --depth 2 \
  --out ./out/example

# Fetch specific URLs without crawling
docker compose run --rm webarc fetch \
  --url "https://example.com/page1" \
  --url "https://example.com/page2" \
  --out ./out/example

# Plan a crawl (dry-run)
docker compose run --rm webarc plan \
  --seed "https://example.com/docs" \
  --depth 3 \
  --estimate
```

## Project Structure

```
web_knowledge/
├── webarc/              # Main application code
│   ├── adapters/        # Site-specific content extractors
│   ├── crawler/         # Scrapy-based crawler
│   ├── extractors/      # Content quality and boilerplate removal
│   ├── html2md/         # HTML to Markdown conversion
│   ├── output/          # File writing and deduplication
│   └── safety/          # Safety guards and filters
├── tests/               # Unit and integration tests
├── docs/                # Documentation
├── config/              # Configuration files
├── frontend/            # Next.js frontend (in development)
└── out/                 # Output directory (crawled content)
```

## Configuration

See `config/webarc.yaml.example` for configuration options. Key settings include:

- Content quality thresholds
- Crawler behavior (depth, concurrency, delays)
- Adapter configurations
- Safety guard settings

## Documentation

Comprehensive documentation is available in the `docs/` directory:

- `docs/README.md` - Full project documentation
- `docs/architecture.md` - System architecture
- `docs/api_reference.md` - API documentation
- `docs/operations.md` - Operations guide
- `docs/adapters.md` - Adapter documentation

## Development

```bash
# Run tests
docker compose run --rm webarc pytest

# Run with coverage
docker compose run --rm webarc pytest --cov=webarc

# Lint code
docker compose run --rm webarc ruff check webarc/
```

## License

Proprietary - All rights reserved

## Repository

- **Gitea**: http://192.168.50.212:3000/bstoner/web_knowledge.git
- **Branch**: main

## Status

🚧 **Active Development** - The project is under active development. See `docs/README.md` for current status and roadmap.

