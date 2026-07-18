FROM python:3.12-slim

WORKDIR /app

# Install system deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN pip install --no-cache-dir uv

# Install MCP deps
COPY mcp-servers/ ./mcp-servers/
COPY core/ ./core/
COPY pyproject.toml ./

RUN uv pip install --system mcp chromadb

CMD ["python", "-m", "mcp_servers.data_processing.server"]
