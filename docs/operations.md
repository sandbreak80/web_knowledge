# WebArc Operations Guide

This guide covers deployment, monitoring, maintenance, and troubleshooting for WebArc.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Deployment](#deployment)
- [Configuration](#configuration)
- [Running Crawls](#running-crawls)
- [Monitoring](#monitoring)
- [Maintenance](#maintenance)
- [Troubleshooting](#troubleshooting)
- [Performance Tuning](#performance-tuning)
- [Security](#security)
- [Backup and Recovery](#backup-and-recovery)

---

## Prerequisites

### System Requirements

- **Docker**: Version 20.10+ (required)
- **Docker Compose**: Version 2.0+ (required)
- **Disk Space**: Sufficient space for output directory (varies by crawl size)
- **Memory**: 2GB RAM minimum (Docker resource limit: 2GB)
- **Network**: Access to target documentation sites
- **CPU**: 2 cores recommended

### Required Files

Before deploying, ensure these files exist:

1. **Configuration File**: `config/webarc.yaml` (example provided)
2. **Blocklist**: `lists/stevenblack_hosts.txt` (must be present for blocklist functionality)

### Directory Structure

```
web_knowledge/
├── config/
│   └── webarc.yaml          # Configuration file
├── lists/
│   └── stevenblack_hosts.txt  # Blocklist file
├── out/                      # Output directory (created automatically)
├── logs/                     # Log files (created automatically)
├── artifacts/                # Build/test artifacts (created automatically)
└── docker-compose.yml        # Docker Compose configuration
```

---

## Deployment

### Docker Deployment

WebArc is designed to run exclusively in Docker containers. No host Python installation is required.

#### 1. Build Docker Image

```bash
# Build the image
make docker-build

# Or directly:
docker compose build
```

The build process:
- Installs Python dependencies from `requirements.txt`
- Installs Playwright Chromium browser
- Sets up non-root user (`webarc:webarc`)
- Creates necessary directories

#### 2. Verify Installation

```bash
# Check if image builds successfully
docker compose build

# Verify container starts
docker compose run --rm webarc --help
```

#### 3. Check Prerequisites

```bash
# Verify config file exists
ls -la config/webarc.yaml

# Verify blocklist exists
ls -la lists/stevenblack_hosts.txt

# Check Docker resources
docker info | grep -E "Total Memory|CPUs"
```

### Environment Variables

No environment variables are required. All configuration is done via `webarc.yaml`.

Optional environment variables (set in `docker-compose.yml`):
- `PYTHONUNBUFFERED=1`: Ensure Python output is unbuffered
- `LOG_LEVEL=INFO`: Override logging level

### Volume Mounts

The `docker-compose.yml` mounts these directories:

- `./out:/app/out`: Output directory (read-write)
- `./config:/app/config:ro`: Configuration files (read-only)
- `./lists:/app/lists:ro`: Blocklist files (read-only)
- `./logs:/app/logs`: Log files (read-write)
- `./artifacts:/app/artifacts`: Build/test artifacts (read-write)

Ensure these directories exist or are created automatically.

---

## Configuration

### Configuration File Location

WebArc searches for `webarc.yaml` in this order:

1. `--config` CLI flag path
2. `./webarc.yaml`
3. `./config/webarc.yaml`
4. `~/.webarc/webarc.yaml`

### Configuration Sections

See `config/webarc.yaml` for complete schema. Key sections:

#### Crawler Settings

```yaml
crawler:
  max_depth: 3                    # Maximum crawl depth
  concurrent_requests: 8          # Total concurrent requests
  concurrent_requests_per_domain: 3  # Per-domain limit
  download_delay: 0.5             # Seconds between requests
  download_timeout: 30             # Request timeout
  max_page_size_mb: 10            # Skip large pages
```

#### Safety Settings

```yaml
safety:
  mode: "advisory"                # "advisory" or "enforce"
  respect_robots_txt: true
  same_domain_only: true
  max_url_length: 2000
  max_query_params: 10
  max_pagination_depth: 50
  entropy_threshold: 3.5
```

#### Output Settings

```yaml
output:
  format: "obsidian"
  obsidian_link_style: "wikilink"
  relative_links: true
  max_filename_length: 200
  deduplicate: "content-hash"
```

### Configuration Validation

Configuration is validated using Pydantic models. Invalid configurations will:
- Fall back to defaults
- Log warnings
- Continue with partial configuration

---

## Running Crawls

### Basic Crawl

```bash
# Run a crawl
docker compose run --rm webarc crawl \
  --seed https://docs.example.com \
  --output ./out \
  --depth 3
```

### Advanced Options

```bash
# Crawl with domain restriction
docker compose run --rm webarc crawl \
  --seed https://docs.example.com \
  --allow-domain docs.example.com \
  --depth 5

# Force JavaScript rendering
docker compose run --rm webarc crawl \
  --seed https://docs.example.com \
  --force-js

# Override quality thresholds
docker compose run --rm webarc crawl \
  --seed https://docs.example.com \
  --min-content-density 0.4 \
  --min-word-count 100

# Version-locked crawl (e.g., only /25.10.0/ URLs)
docker compose run --rm webarc crawl \
  --seed https://docs.example.com \
  --version-lock "25.10.0"
```

### Preview Crawl Plan

Before crawling, preview the plan:

```bash
# Preview plan
docker compose run --rm webarc plan \
  --seed https://docs.example.com \
  --estimate \
  --show-rules

# Preview with custom settings
docker compose run --rm webarc plan \
  --seed https://docs.example.com \
  --depth 5 \
  --allow-domain docs.example.com \
  --estimate
```

### Resume Interrupted Crawl

If a crawl is interrupted, resume from checkpoint:

```bash
# Resume from checkpoint
docker compose run --rm webarc resume \
  --output ./out
```

The resume command:
- Loads state from `out/resume.jsonl`
- Skips already-visited URLs
- Continues from checkpoint

**Note**: Checkpoints are saved every 100 pages by default (configurable via `StateManager`).

### Validate Output

After crawling, validate output integrity:

```bash
# Validate output
docker compose run --rm webarc validate \
  --output ./out

# Validate with link checking
docker compose run --rm webarc validate \
  --output ./out \
  --check-links
```

Exit codes:
- `0`: Validation passed
- `1`: Validation failed (missing files, broken links)

### View Statistics

View crawl statistics:

```bash
# Display statistics
docker compose run --rm webarc stats \
  --output ./out
```

Shows:
- Total pages crawled
- Pages extracted
- Pages skipped
- Errors encountered
- File counts

---

## Monitoring

### Log Files

Logs are written to multiple locations:

#### Application Logs

- **Location**: `logs/webarc.log` (if configured)
- **Format**: JSON or text (configurable)
- **Rotation**: Automatic (max 100MB, 5 backups)

#### Docker Logs

```bash
# View container logs
docker compose logs webarc

# Follow logs in real-time
docker compose logs -f webarc

# View last 100 lines
docker compose logs --tail=100 webarc
```

#### Docker Log Configuration

Configured in `docker-compose.yml`:
- Driver: `json-file`
- Max size: 10MB per file
- Max files: 3

### Artifacts

Build and test artifacts are stored in `artifacts/`:

- `coverage.json`: Test coverage data
- `test.log`: Test execution logs
- `lint.log`: Linting results
- `typecheck.log`: Type checking results
- `docker-build.log`: Docker build logs

### Output Files

Crawl output is written to `out/`:

#### Manifest Files

- **`manifest.jsonl`**: Page metadata (one JSON object per line)
  - URL, title, file path, timestamps, quality metrics
- **`graph.jsonl`**: Link relationships (source → target)
  - Used for link validation and graph analysis
- **`errors.jsonl`**: Error records
  - Failed URLs, error messages, timestamps
- **`resume.jsonl`**: State checkpoint (latest only)
  - Visited URLs, queue, statistics

#### Markdown Files

- **Location**: `out/` directory (preserves directory structure)
- **Format**: Obsidian-flavored Markdown with YAML front-matter
- **Naming**: Based on URL path (sanitized)

### Monitoring Crawl Progress

#### Real-Time Monitoring

```bash
# Watch output directory
watch -n 5 'ls -lh out/*.md | wc -l'

# Monitor manifest file
tail -f out/manifest.jsonl | jq .

# Check errors
tail -f out/errors.jsonl | jq .
```

#### Statistics During Crawl

```bash
# Count extracted pages
wc -l out/manifest.jsonl

# Count errors
wc -l out/errors.jsonl

# Count graph edges
wc -l out/graph.jsonl

# Check disk usage
du -sh out/
```

### Health Checks

#### Container Health

```bash
# Check container status
docker compose ps

# Check resource usage
docker stats webarc_crawler

# Check container logs for errors
docker compose logs webarc | grep -i error
```

#### Output Health

```bash
# Validate output integrity
docker compose run --rm webarc validate --output ./out

# Check for missing files
docker compose run --rm webarc validate --output ./out --check-links
```

---

## Maintenance

### Regular Maintenance Tasks

#### 1. Clean Old Output

```bash
# Remove old output (be careful!)
rm -rf out/*.md
rm -f out/manifest.jsonl out/graph.jsonl out/errors.jsonl

# Keep resume.jsonl if resuming
```

#### 2. Rotate Logs

Logs are automatically rotated, but you can manually clean:

```bash
# Clean old log files
find logs/ -name "*.log.*" -mtime +30 -delete
```

#### 3. Update Blocklist

```bash
# Download latest StevenBlack blocklist
curl -o lists/stevenblack_hosts.txt \
  https://raw.githubusercontent.com/StevenBlack/hosts/master/hosts
```

#### 4. Rebuild Docker Image

```bash
# Rebuild with latest code
make docker-build

# Or rebuild without cache
docker compose build --no-cache
```

### Resuming Crawls

#### When to Resume

Resume a crawl if:
- Crawl was interrupted (Ctrl+C, system crash)
- Network timeout occurred
- Manual stop was needed

#### How to Resume

```bash
# Resume from checkpoint
docker compose run --rm webarc resume --output ./out
```

**Requirements:**
- `out/resume.jsonl` must exist
- Output directory must be accessible
- Configuration should match original crawl

#### Resume Behavior

- Loads visited URLs from checkpoint
- Skips already-visited URLs
- Continues from queue
- Accumulates statistics

**Note**: Resume uses approximate queue (visited URLs). Some URLs may be re-crawled if they were in-flight when checkpoint was saved.

### Updating Configuration

#### Update Config File

1. Edit `config/webarc.yaml`
2. Restart crawl (or resume if in progress)

**Note**: Changing config mid-crawl may cause inconsistencies. Best practice: complete or cancel crawl, then restart with new config.

#### Validate Configuration

```bash
# Test config loading
docker compose run --rm webarc plan \
  --seed https://docs.example.com \
  --config config/webarc.yaml
```

### Cleaning Up

#### Clean Output Directory

```bash
# Remove all output
rm -rf out/*

# Remove specific files
rm -f out/manifest.jsonl out/graph.jsonl out/errors.jsonl

# Keep resume.jsonl for resume
```

#### Clean Docker Resources

```bash
# Remove stopped containers
docker compose down

# Remove images
docker rmi webarc:latest

# Clean build cache
docker builder prune
```

#### Clean Test Artifacts

```bash
# Use Makefile target
make clean

# Or manually:
rm -rf artifacts/*.log
rm -rf .pytest_cache/
rm -rf htmlcov/
find . -type d -name __pycache__ -exec rm -r {} +
```

---

## Troubleshooting

### Common Issues

#### 1. Container Won't Start

**Symptoms**: Container exits immediately

**Diagnosis**:
```bash
# Check container logs
docker compose logs webarc

# Check container status
docker compose ps -a
```

**Solutions**:
- Verify Docker is running: `docker info`
- Check disk space: `df -h`
- Verify image built: `docker images | grep webarc`
- Check resource limits: `docker stats`

#### 2. Permission Denied Errors

**Symptoms**: Cannot write to output directory

**Diagnosis**:
```bash
# Check directory permissions
ls -la out/

# Check container user
docker compose exec webarc whoami
```

**Solutions**:
- Ensure directories are writable: `chmod 755 out/ logs/ artifacts/`
- Check volume mount permissions
- Verify non-root user in container (`webarc:webarc`)

#### 3. Network Timeouts

**Symptoms**: Crawl hangs or times out

**Diagnosis**:
```bash
# Check network connectivity
docker compose exec webarc ping -c 3 docs.example.com

# Check DNS resolution
docker compose exec webarc nslookup docs.example.com
```

**Solutions**:
- Increase `download_timeout` in config
- Check firewall/proxy settings
- Verify target site is accessible
- Check Docker network configuration

#### 4. Out of Memory

**Symptoms**: Container killed, "OOM" errors

**Diagnosis**:
```bash
# Check memory usage
docker stats webarc_crawler

# Check memory limits
docker inspect webarc_crawler | grep -i memory
```

**Solutions**:
- Reduce `concurrent_requests` in config
- Reduce `max_page_size_mb` threshold
- Increase Docker memory limit in `docker-compose.yml`
- Enable memory monitoring: `memusage_enabled: true`

#### 5. Missing Blocklist File

**Symptoms**: Warnings about missing blocklist

**Diagnosis**:
```bash
# Check if file exists
ls -la lists/stevenblack_hosts.txt
```

**Solutions**:
- Download blocklist: See "Update Blocklist" section
- Disable blocklist: Set `safety.use_blocklist: false` in config
- Verify volume mount: Check `docker-compose.yml`

#### 6. Invalid Configuration

**Symptoms**: Config errors, fallback to defaults

**Diagnosis**:
```bash
# Test config loading
docker compose run --rm webarc plan \
  --seed https://docs.example.com \
  --config config/webarc.yaml
```

**Solutions**:
- Validate YAML syntax: `yamllint config/webarc.yaml`
- Check Pydantic validation errors in logs
- Review config schema in `docs/api_reference.md`
- Use example config as template

#### 7. Resume Not Working

**Symptoms**: Resume command fails or re-crawls everything

**Diagnosis**:
```bash
# Check resume file exists
ls -la out/resume.jsonl

# Check resume file content
cat out/resume.jsonl | jq .
```

**Solutions**:
- Verify `resume.jsonl` exists and is valid JSON
- Check that output directory matches original crawl
- Ensure config matches original crawl
- Verify visited URLs are in resume file

### Error Codes

Exit codes:
- `0`: Success
- `1`: Validation failure (validate command)
- `2`: Crawl errors encountered
- `130`: Interrupted (Ctrl+C)

### Debugging

#### Enable Debug Logging

```yaml
# In webarc.yaml
logging:
  level: "DEBUG"
```

Or via environment variable:
```bash
docker compose run --rm -e LOG_LEVEL=DEBUG webarc crawl \
  --seed https://docs.example.com
```

#### Verbose Output

```bash
# Run with verbose output
docker compose run --rm webarc crawl \
  --seed https://docs.example.com \
  --output ./out \
  --depth 3 \
  2>&1 | tee crawl.log
```

#### Check Intermediate State

```bash
# Inspect manifest entries
cat out/manifest.jsonl | jq . | head -20

# Check errors
cat out/errors.jsonl | jq .

# Check graph relationships
cat out/graph.jsonl | jq . | head -20
```

---

## Performance Tuning

### Crawler Performance

#### Concurrent Requests

Adjust based on target site capacity:

```yaml
crawler:
  concurrent_requests: 8          # Increase for faster crawling
  concurrent_requests_per_domain: 3  # Per-domain limit
  download_delay: 0.5             # Reduce for faster crawling (be respectful!)
```

**Recommendations**:
- Start conservative (8 total, 3 per domain)
- Monitor target site response times
- Respect robots.txt crawl-delay directives
- Increase gradually if site handles load well

#### Memory Management

```yaml
crawler:
  memusage_enabled: true
  memusage_limit_mb: 1024         # Stop if exceeded
  memusage_warning_mb: 768        # Log warning
  max_page_size_mb: 10            # Skip large pages
```

**Tuning**:
- Reduce `max_page_size_mb` to skip large pages
- Enable memory monitoring to detect leaks
- Adjust Docker memory limit if needed

#### Network Performance

```yaml
crawler:
  download_timeout: 30             # Increase for slow sites
  download_maxsize: 10485760        # 10MB max
  retry_times: 2                    # Retry failed requests
```

**Tuning**:
- Increase timeout for slow sites
- Reduce retry times for faster failure detection
- Adjust based on network conditions

### Output Performance

#### File Writing

- Files are written incrementally (no batch processing)
- Manifest files use JSONL (append-only, efficient)
- Large crawls may have many small files

#### Disk I/O

- Use SSD for output directory if possible
- Monitor disk space: `df -h`
- Clean old output regularly

### Resource Limits

#### Docker Limits

Configured in `docker-compose.yml`:
```yaml
mem_limit: 2g      # Maximum memory
cpus: 2            # CPU cores
pids_limit: 100   # Process limit
```

**Adjustments**:
- Increase `mem_limit` for large crawls
- Increase `cpus` for faster processing
- Monitor with `docker stats`

---

## Security

### Container Security

#### Non-Root User

WebArc runs as non-root user (`webarc:webarc`):
- User ID: 1000
- Group ID: 1000
- No sudo privileges

#### Security Options

Configured in `docker-compose.yml`:
```yaml
security_opt:
  - no-new-privileges:true
```

Prevents privilege escalation.

#### Resource Limits

Prevent DoS attacks:
- Memory limit: 2GB
- CPU limit: 2 cores
- Process limit: 100

### Network Security

#### Domain Restrictions

Always use domain restrictions:
```bash
docker compose run --rm webarc crawl \
  --seed https://docs.example.com \
  --allow-domain docs.example.com
```

Prevents crawling unintended sites.

#### Blocklist

Enable blocklist to prevent malicious domains:
```yaml
safety:
  use_blocklist: true
  blocklist_path: "./lists/stevenblack_hosts.txt"
```

#### Robots.txt Compliance

Respect robots.txt by default:
```yaml
safety:
  respect_robots_txt: true
```

Override only when necessary:
```bash
docker compose run --rm webarc crawl \
  --seed https://docs.example.com \
  --ignore-robots  # Use carefully!
```

### Data Security

#### Output Directory

- Output contains public documentation (typically not sensitive)
- Ensure output directory permissions are appropriate
- Consider encryption for sensitive documentation

#### Log Files

- Logs may contain URLs and error messages
- Rotate logs regularly
- Secure log file permissions

#### State Files

- `resume.jsonl` contains visited URLs
- May reveal crawl patterns
- Secure appropriately

---

## Backup and Recovery

### Backup Strategy

#### Output Directory

```bash
# Backup output directory
tar -czf webarc-output-$(date +%Y%m%d).tar.gz out/

# Backup to remote location
rsync -avz out/ user@backup-server:/backups/webarc/
```

#### Configuration

```bash
# Backup configuration
cp config/webarc.yaml config/webarc.yaml.backup
```

#### State Files

```bash
# Backup resume state
cp out/resume.jsonl out/resume.jsonl.backup
```

### Recovery

#### Restore Output

```bash
# Restore from backup
tar -xzf webarc-output-20231111.tar.gz

# Verify restoration
docker compose run --rm webarc validate --output ./out
```

#### Restore State

```bash
# Restore resume state
cp out/resume.jsonl.backup out/resume.jsonl

# Resume crawl
docker compose run --rm webarc resume --output ./out
```

### Disaster Recovery

#### Complete Rebuild

If container/image is corrupted:

```bash
# Remove old image
docker rmi webarc:latest

# Rebuild
make docker-build

# Verify
docker compose run --rm webarc --help
```

#### Data Recovery

If output directory is corrupted:

1. Check `errors.jsonl` for failed URLs
2. Re-crawl failed URLs manually
3. Validate output integrity
4. Merge with existing output if needed

---

## Best Practices

### Crawl Planning

1. **Always preview first**: Use `plan` command before crawling
2. **Start small**: Test with `--depth 1` before full crawl
3. **Use domain restrictions**: Always specify `--allow-domain`
4. **Respect robots.txt**: Don't use `--ignore-robots` unless necessary

### Resource Management

1. **Monitor disk space**: Large crawls can generate GBs of output
2. **Monitor memory**: Watch for OOM errors
3. **Set appropriate limits**: Adjust Docker limits based on system capacity
4. **Clean regularly**: Remove old output and logs

### Error Handling

1. **Check errors.jsonl**: Review errors after each crawl
2. **Validate output**: Always run `validate` after crawl
3. **Monitor logs**: Watch for warnings and errors
4. **Resume on failure**: Use resume for interrupted crawls

### Maintenance

1. **Update blocklist**: Keep blocklist current
2. **Rebuild images**: Rebuild after code updates
3. **Rotate logs**: Clean old log files regularly
4. **Backup output**: Backup important crawl results

---

## Support and Troubleshooting

### Getting Help

1. **Check logs**: Review `logs/webarc.log` and Docker logs
2. **Check errors**: Review `out/errors.jsonl`
3. **Validate config**: Test configuration loading
4. **Review documentation**: Check `docs/architecture.md` and `docs/api_reference.md`

### Common Commands Reference

```bash
# Build
make docker-build

# Test
make docker-test

# Lint
make docker-lint

# Type check
make docker-typecheck

# Run all checks
make docker-test-all

# Clean
make clean

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

---

## Appendix

### Exit Codes

- `0`: Success
- `1`: Validation failure
- `2`: Crawl errors
- `130`: Interrupted (Ctrl+C)

### File Formats

- **manifest.jsonl**: One JSON object per line
- **graph.jsonl**: One JSON object per line (`{"source": "...", "target": "..."}`)
- **errors.jsonl**: One JSON object per line (`{"url": "...", "error": "..."}`)
- **resume.jsonl**: Single JSON object (latest checkpoint)

### Configuration Precedence

1. CLI flags (highest priority)
2. `webarc.yaml` file
3. Default values (lowest priority)

### Logging Levels

- `DEBUG`: Detailed debugging information
- `INFO`: General informational messages
- `WARNING`: Warning messages (non-fatal)
- `ERROR`: Error messages (may be fatal)
