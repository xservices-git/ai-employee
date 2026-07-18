FROM python:3.12-slim

WORKDIR /app

# Install system deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN pip install --no-cache-dir uv

# Copy dependency files
COPY pyproject.toml uv.lock* ./

# Install deps
RUN uv sync --frozen --no-dev 2>/dev/null || uv sync --no-dev

# Copy code
COPY core/ ./core/
COPY api/ ./api/
COPY mcp-servers/ ./mcp-servers/
COPY domain_configs/ ./domain_configs/
COPY eval/ ./eval/

# Create data dir
RUN mkdir -p /data /workspace

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

EXPOSE 8000

CMD ["uv", "run", "python", "-m", "api.main"]
