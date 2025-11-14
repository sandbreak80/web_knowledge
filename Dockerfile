# Complete production Dockerfile

FROM python:3.11-slim-bookworm

# Metadata
LABEL maintainer="webarc@example.com"
LABEL description="WebArc - Local web documentation to Obsidian Markdown extractor"
LABEL version="1.0.0"

# Install system dependencies for Playwright
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    ca-certificates \
    fonts-liberation \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libatspi2.0-0 \
    libcairo2 \
    libcups2 \
    libdbus-1-3 \
    libdrm2 \
    libgbm1 \
    libglib2.0-0 \
    libnspr4 \
    libnss3 \
    libpango-1.0-0 \
    libx11-6 \
    libxcb1 \
    libxcomposite1 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    libxkbcommon0 \
    libxrandr2 \
    xdg-utils \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN useradd -m -u 1000 -s /bin/bash webarc

# Set working directory
WORKDIR /app

# Copy requirements first (for caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers (Chromium only)
RUN playwright install chromium
RUN playwright install-deps chromium

# Copy application code
COPY . .

# Ensure lists directory exists (create if missing)
RUN mkdir -p /app/lists

# Create output directory
RUN mkdir -p /app/out && chown webarc:webarc /app/out

# Create logs directory
RUN mkdir -p /app/logs && chown webarc:webarc /app/logs

# Create artifacts directory
RUN mkdir -p /app/artifacts && chown webarc:webarc /app/artifacts

# Set ownership
RUN chown -R webarc:webarc /app

# Switch to non-root user
USER webarc

# Health check (optional)
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)"

# Default command
ENTRYPOINT ["python", "-m", "webarc"]
CMD ["--help"]
