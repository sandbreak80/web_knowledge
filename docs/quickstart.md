# WebArc Quickstart Guide

Get started with WebArc in minutes! This guide walks you through installation, configuration, and your first crawl.

## Table of Contents

- [What is WebArc?](#what-is-webarc)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Quick Start (5 Minutes)](#quick-start-5-minutes)
- [Your First Crawl](#your-first-crawl)
- [Understanding Output](#understanding-output)
- [Common Tasks](#common-tasks)
- [Next Steps](#next-steps)

---

## What is WebArc?

WebArc is a local-first, Dockerized web crawler that extracts structured Markdown from documentation sites (Confluence, MkDocs, Sphinx) to create Obsidian-compatible knowledge bases.

**Key Features:**
- ✅ Crawls documentation sites safely (respects robots.txt, domain restrictions)
- ✅ Extracts clean content (removes navigation, ads, boilerplate)
- ✅ Converts to Obsidian Markdown (with YAML front-matter, wikilinks)
- ✅ Resumable crawls (checkpointing, state management)
- ✅ Works offline (no cloud dependencies)

**Perfect for:**
- Sales Engineers needing offline documentation access
- Knowledge workers building local knowledge bases
- RAG corpus generation from documentation sites

---

## Prerequisites

### Required Software

1. **Docker** (version 20.10+)
   ```bash
   # Check if Docker is installed
   docker --version
   
   # If not installed, visit: https://docs.docker.com/get-docker/
   ```

2. **Docker Compose** (version 2.0+)
   ```bash
   # Check if Docker Compose is installed
   docker compose version
   
   # Usually included with Docker Desktop
   ```

### System Requirements

- **Memory**: 2GB RAM minimum
- **Disk Space**: Varies by crawl size (start with 1GB free)
- **Network**: Access to target documentation sites
- **OS**: Linux, macOS, or Windows (with Docker)

### Verify Installation

```bash
# Verify Docker is running
docker info

# Verify Docker Compose works
docker compose version
```

---

## Installation

### Step 1: Clone or Download Project

If you have the project files, skip to Step 2. Otherwise:

```bash
# If using git
git clone <repository-url>
cd web_knowledge

# Or download and extract the project files
```

### Step 2: Verify Project Structure

Ensure these files/directories exist:

```
web_knowledge/
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── config/
│   └── webarc.yaml
├── lists/
│   └── stevenblack_hosts.txt
└── Makefile
```

### Step 3: Build Docker Image

```bash
# Build the Docker image (takes 5-10 minutes first time)
make docker-build

# Or directly:
docker compose build
```

**What happens:**
- Downloads Python base image
- Installs dependencies (Scrapy, Playwright, etc.)
- Installs Chromium browser
- Sets up non-root user
- Creates directories

**Expected output:**
```
Successfully built <image-id>
Successfully tagged webarc:latest
```

### Step 4: Verify Installation

```bash
# Test that WebArc works
docker compose run --rm webarc --help
```

You should see:
```
Usage: webarc [OPTIONS] COMMAND [ARGS]...

  Local web documentation to Obsidian Markdown extractor

Commands:
  crawl    Execute crawl and extract content
  plan     Preview crawl plan without actually fetching pages
  resume   Resume interrupted crawl from checkpoint
  stats    Display crawl statistics
  validate Verify output integrity
```

**✅ Installation Complete!**

---

## Quick Start (5 Minutes)

### Example: Crawl a Documentation Site

Let's crawl a simple documentation site to see WebArc in action:

```bash
# 1. Preview the crawl plan
docker compose run --rm webarc plan \
  --seed https://docs.example.com \
  --estimate

# 2. Run a shallow crawl (depth 1) to test
docker compose run --rm webarc crawl \
  --seed https://docs.example.com \
  --output ./out \
  --depth 1 \
  --allow-domain docs.example.com

# 3. Check the results
ls -lh out/
cat out/manifest.jsonl | head -1 | jq .
```

### What Just Happened?

1. **Plan**: Previewed what would be crawled (without fetching)
2. **Crawl**: Actually crawled the site and extracted content
3. **Output**: Generated Markdown files in `out/` directory

---

## Your First Crawl

### Step-by-Step: Crawl MkDocs Documentation

Let's crawl a real MkDocs documentation site:

```bash
# Step 1: Preview the crawl
docker compose run --rm webarc plan \
  --seed https://www.mkdocs.org \
  --allow-domain www.mkdocs.org \
  --depth 2 \
  --estimate \
  --show-rules

# Step 2: Run the crawl
docker compose run --rm webarc crawl \
  --seed https://www.mkdocs.org \
  --output ./out \
  --allow-domain www.mkdocs.org \
  --depth 2

# Step 3: View statistics
docker compose run --rm webarc stats --output ./out

# Step 4: Validate output
docker compose run --rm webarc validate --output ./out
```

### Understanding the Command

```bash
docker compose run --rm webarc crawl \
  --seed https://www.mkdocs.org \      # Starting URL
  --output ./out \                      # Where to save files
  --allow-domain www.mkdocs.org \      # Only crawl this domain
  --depth 2                             # Maximum crawl depth
```

**Important Flags:**
- `--seed`: The starting URL (required)
- `--output`: Output directory (default: `./out`)
- `--allow-domain`: Restrict to this domain (recommended!)
- `--depth`: How many levels deep to crawl (default: 3)

### What Gets Crawled?

WebArc will:
1. Start at the seed URL
2. Extract links from each page
3. Follow links that:
   - Are on the same domain (`--allow-domain`)
   - Are within depth limit (`--depth`)
   - Pass safety checks (robots.txt, blocklist, etc.)
4. Extract content and convert to Markdown
5. Write files to output directory

---

## Understanding Output

### Output Structure

After a crawl, your `out/` directory will contain:

```
out/
├── index.md                    # Example: Home page
├── getting-started.md          # Example: Getting started page
├── configuration.md            # Example: Configuration page
├── manifest.jsonl             # Metadata for all pages
├── graph.jsonl                # Link relationships
├── errors.jsonl               # Error records (if any)
└── resume.jsonl               # State checkpoint
```

### Manifest File

`manifest.jsonl` contains metadata for each page:

```json
{
  "url": "https://docs.example.com/page",
  "title": "Page Title",
  "file_path": "page.md",
  "fetched_at": "2025-11-11T18:00:00Z",
  "content_hash": "sha256:abc123...",
  "quality": {
    "status": "ok",
    "content_density": 0.45,
    "word_count": 250
  }
}
```

### Graph File

`graph.jsonl` contains link relationships:

```json
{"source": "https://docs.example.com/page1", "target": "https://docs.example.com/page2"}
```

Useful for:
- Building knowledge graphs
- Validating internal links
- Understanding site structure

### Markdown Files

Each page becomes a Markdown file with:

**YAML Front-Matter:**
```yaml
---
title: Page Title
source_url: https://docs.example.com/page
canonical_url: https://docs.example.com/page
fetched_at: 2025-11-11T18:00:00Z
content_hash: sha256:abc123...
adapter: MkDocsAdapter
quality:
  status: ok
  content_density: 0.45
  word_count: 250
---
```

**Content:**
```markdown
# Page Title

This is the extracted content in Obsidian-flavored Markdown.

## Section

With [[wikilinks]] to other pages.

> And callout blocks.
```

---

## Common Tasks

### Task 1: Preview Before Crawling

Always preview first to understand what will be crawled:

```bash
docker compose run --rm webarc plan \
  --seed https://docs.example.com \
  --allow-domain docs.example.com \
  --depth 3 \
  --estimate \
  --show-rules
```

**Output shows:**
- Domain restrictions
- Safety rules
- Estimated page count (if sitemap available)
- Configuration summary

### Task 2: Crawl with Custom Settings

```bash
# Crawl deeper
docker compose run --rm webarc crawl \
  --seed https://docs.example.com \
  --depth 5 \
  --output ./deep_crawl

# Crawl with quality filters
docker compose run --rm webarc crawl \
  --seed https://docs.example.com \
  --min-content-density 0.4 \
  --min-word-count 100

# Crawl specific version
docker compose run --rm webarc crawl \
  --seed https://docs.example.com \
  --version-lock "25.10.0"
```

### Task 3: Resume Interrupted Crawl

If a crawl is interrupted (Ctrl+C, crash):

```bash
# Resume from checkpoint
docker compose run --rm webarc resume \
  --output ./out
```

**Requirements:**
- `out/resume.jsonl` must exist
- Output directory must match original crawl

### Task 4: Validate Output

After crawling, validate the output:

```bash
# Basic validation (check files exist)
docker compose run --rm webarc validate \
  --output ./out

# Validate with link checking
docker compose run --rm webarc validate \
  --output ./out \
  --check-links
```

**Exit codes:**
- `0`: Validation passed
- `1`: Validation failed (missing files, broken links)

### Task 5: View Statistics

```bash
# Display crawl statistics
docker compose run --rm webarc stats \
  --output ./out
```

**Shows:**
- Total pages crawled
- Pages extracted
- Pages skipped
- Errors encountered
- File counts

### Task 6: Use Configuration File

Create/edit `config/webarc.yaml`:

```yaml
crawler:
  max_depth: 5
  concurrent_requests: 8

safety:
  respect_robots_txt: true
  same_domain_only: true

output:
  format: "obsidian"
  obsidian_link_style: "wikilink"
```

Then run without specifying all flags:

```bash
docker compose run --rm webarc crawl \
  --seed https://docs.example.com \
  --config config/webarc.yaml
```

---

## Common Use Cases

### Use Case 1: Archive Vendor Documentation

**Goal**: Create offline copy of vendor documentation

```bash
# Step 1: Preview
docker compose run --rm webarc plan \
  --seed https://vendor-docs.example.com \
  --allow-domain vendor-docs.example.com \
  --estimate

# Step 2: Crawl
docker compose run --rm webarc crawl \
  --seed https://vendor-docs.example.com \
  --allow-domain vendor-docs.example.com \
  --output ./vendor_docs \
  --depth 4

# Step 3: Validate
docker compose run --rm webarc validate \
  --output ./vendor_docs \
  --check-links
```

### Use Case 2: Extract Specific Documentation Section

**Goal**: Only crawl a specific section (e.g., `/api/`)

```bash
docker compose run --rm webarc crawl \
  --seed https://docs.example.com/api/ \
  --allow-domain docs.example.com \
  --allow-prefix /api/ \
  --output ./api_docs
```

### Use Case 3: Create RAG Corpus

**Goal**: Extract documentation for RAG system

```bash
# Crawl with high quality thresholds
docker compose run --rm webarc crawl \
  --seed https://docs.example.com \
  --allow-domain docs.example.com \
  --min-content-density 0.4 \
  --min-word-count 100 \
  --output ./rag_corpus

# Output is ready for RAG ingestion
# Each .md file has clean content + metadata
```

### Use Case 4: Resume Large Crawl

**Goal**: Resume interrupted large crawl

```bash
# Original crawl (interrupted)
docker compose run --rm webarc crawl \
  --seed https://large-docs.example.com \
  --output ./large_crawl \
  --depth 5

# Later: Resume
docker compose run --rm webarc resume \
  --output ./large_crawl
```

---

## Troubleshooting

### Problem: "Container won't start"

**Solution:**
```bash
# Check Docker is running
docker info

# Check image exists
docker images | grep webarc

# Rebuild if needed
make docker-build
```

### Problem: "Permission denied" errors

**Solution:**
```bash
# Fix directory permissions
chmod 755 out/ logs/ artifacts/

# Or recreate directories
mkdir -p out logs artifacts
```

### Problem: "No such file or directory: config/webarc.yaml"

**Solution:**
```bash
# Check config file exists
ls -la config/webarc.yaml

# Or use default config (no --config flag)
docker compose run --rm webarc crawl \
  --seed https://docs.example.com
```

### Problem: "Network timeout" or "Connection refused"

**Solution:**
```bash
# Test network connectivity
docker compose run --rm webarc ping -c 3 docs.example.com

# Check if site is accessible
curl -I https://docs.example.com

# Increase timeout in config/webarc.yaml
crawler:
  download_timeout: 60  # Increase from 30
```

### Problem: "Out of memory" errors

**Solution:**
```bash
# Reduce concurrency in config/webarc.yaml
crawler:
  concurrent_requests: 4  # Reduce from 8

# Or increase Docker memory limit in docker-compose.yml
mem_limit: 4g  # Increase from 2g
```

### Problem: "Resume not working"

**Solution:**
```bash
# Check resume file exists
ls -la out/resume.jsonl

# Check resume file is valid JSON
cat out/resume.jsonl | jq .

# Ensure output directory matches original crawl
```

---

## Next Steps

### Learn More

- **Architecture**: Read `docs/architecture.md` for system design
- **API Reference**: Read `docs/api_reference.md` for programmatic usage
- **Operations**: Read `docs/operations.md` for deployment and maintenance

### Advanced Topics

1. **Custom Adapters**: Create site-specific adapters (see `docs/api_reference.md`)
2. **Configuration**: Customize `config/webarc.yaml` for your needs
3. **Performance Tuning**: Optimize for large crawls (see `docs/operations.md`)
4. **Integration**: Use WebArc programmatically (see `docs/api_reference.md`)

### Getting Help

1. **Check Logs**: Review `logs/webarc.log` and Docker logs
2. **Check Errors**: Review `out/errors.jsonl` after crawls
3. **Validate Config**: Test configuration with `plan` command
4. **Review Documentation**: Check architecture and API docs

---

## Quick Reference

### Essential Commands

```bash
# Build
make docker-build

# Plan crawl
docker compose run --rm webarc plan --seed URL --estimate

# Crawl
docker compose run --rm webarc crawl --seed URL --output ./out

# Resume
docker compose run --rm webarc resume --output ./out

# Validate
docker compose run --rm webarc validate --output ./out

# Stats
docker compose run --rm webarc stats --output ./out
```

### Common Flags

- `--seed URL`: Starting URL (required)
- `--output DIR`: Output directory (default: `./out`)
- `--allow-domain DOMAIN`: Restrict to domain (recommended)
- `--depth N`: Maximum crawl depth (default: 3)
- `--force-js`: Force JavaScript rendering
- `--ignore-robots`: Ignore robots.txt (use carefully)
- `--min-content-density FLOAT`: Minimum content density (default: 0.3)
- `--min-word-count INT`: Minimum word count (default: 50)
- `--version-lock STRING`: Restrict to URLs containing version

### Output Files

- `manifest.jsonl`: Page metadata
- `graph.jsonl`: Link relationships
- `errors.jsonl`: Error records
- `resume.jsonl`: State checkpoint
- `*.md`: Markdown files (one per page)

---

## Example Workflow

### Complete Example: Crawl and Use Documentation

```bash
# 1. Build (one-time)
make docker-build

# 2. Preview crawl
docker compose run --rm webarc plan \
  --seed https://docs.example.com \
  --allow-domain docs.example.com \
  --depth 3 \
  --estimate

# 3. Run crawl
docker compose run --rm webarc crawl \
  --seed https://docs.example.com \
  --allow-domain docs.example.com \
  --output ./my_docs \
  --depth 3

# 4. Check progress (in another terminal)
watch -n 5 'wc -l my_docs/manifest.jsonl'

# 5. View statistics
docker compose run --rm webarc stats --output ./my_docs

# 6. Validate output
docker compose run --rm webarc validate --output ./my_docs

# 7. Use the Markdown files
# Open in Obsidian, use for RAG, etc.
ls my_docs/*.md
```

---

## Tips for Success

1. **Always preview first**: Use `plan` command before crawling
2. **Use domain restrictions**: Always specify `--allow-domain` to prevent accidents
3. **Start shallow**: Test with `--depth 1` before deep crawls
4. **Respect robots.txt**: Don't use `--ignore-robots` unless necessary
5. **Monitor progress**: Watch `manifest.jsonl` to track progress
6. **Validate output**: Always run `validate` after crawling
7. **Check errors**: Review `errors.jsonl` for failed pages
8. **Resume on interruption**: Use `resume` if crawl is interrupted

---

## What's Next?

You're ready to start crawling! Here are suggested next steps:

1. **Try a small crawl**: Start with `--depth 1` on a familiar site
2. **Explore output**: Open the generated Markdown files
3. **Customize config**: Edit `config/webarc.yaml` for your needs
4. **Read operations guide**: Learn about monitoring and maintenance
5. **Read API reference**: Learn programmatic usage

**Happy Crawling! 🕷️**
