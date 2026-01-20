# Multi-stage build for MCP agent runtime
FROM python:3.11-slim AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Runtime stage
FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Copy Python packages from builder
COPY --from=builder /root/.local /root/.local

# Copy application source
COPY src/ .

# Ensure Python packages are in PATH
ENV PATH=/root/.local/bin:$PATH

# Default environment variables (can be overridden at runtime)
ENV SOURCE_TYPE=postgres
ENV LANGCHAIN_TRACING_V2=false

# Expose MCP server port (if needed for debugging)
EXPOSE 8000

# Run as MCP server - all config from env vars
ENTRYPOINT ["python", "-m", "agent.mcp.server"]
