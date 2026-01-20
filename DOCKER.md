# Docker Deployment Guide

## Overview

This Docker setup packages the MCP-based AI agent system into containers. Each container runs the same runtime image but is configured for a different agent via environment variables.

## Architecture

- **One reusable runtime image**: All agents use the same Docker image
- **Agent identity via env vars**: `AGENT_NAME` and `POSTGRES_DSN` specify which agent to run
- **No CLI arguments**: All configuration comes from environment variables
- **Control plane**: Agent definitions stored in PostgreSQL database

## Quick Start

### 1. Build the Runtime Image

```bash
docker build -t agent-runtime:latest .
```

### 2. Run with Docker Compose

```bash
# Set your OpenAI API key
export OPENAI_API_KEY=sk-...

# Start all services (postgres + agents)
docker-compose up -d

# View logs
docker-compose logs -f demo-agent
docker-compose logs -f supervisor-agent

# Stop all services
docker-compose down
```

### 3. Run a Single Agent Container

```bash
docker run -d \
  --name my-agent \
  --network agent-network \
  -e SOURCE_TYPE=postgres \
  -e POSTGRES_DSN=postgresql://agent_admin:agent_admin_pw_dev_only@agent-postgres:5432/agent_control_plane \
  -e AGENT_NAME=demo-agent \
  -e OPENAI_API_KEY=sk-... \
  agent-runtime:latest
```

## Environment Variables

### Required for Postgres Mode

- `SOURCE_TYPE=postgres` - Configuration source type
- `POSTGRES_DSN` - PostgreSQL connection string
- `AGENT_NAME` - Name of agent to load from database
- `OPENAI_API_KEY` - OpenAI API key (or appropriate LLM credentials)

### Optional

- `LANGCHAIN_TRACING_V2=false` - Disable LangChain tracing (default: false)

## Container Details

**Entrypoint**: `python -m agent.mcp.server`

**Port**: 8000 (MCP server, primarily for debugging)

**Working Directory**: `/app`

## Adding New Agents

To run a new agent:

1. **Define the agent in PostgreSQL** (control plane tables)
2. **Start a new container** with `AGENT_NAME` set to the new agent's name

```bash
docker run -d \
  --name research-agent \
  --network agent-network \
  -e SOURCE_TYPE=postgres \
  -e POSTGRES_DSN=postgresql://agent_admin:agent_admin_pw_dev_only@agent-postgres:5432/agent_control_plane \
  -e AGENT_NAME=research-agent \
  -e OPENAI_API_KEY=sk-... \
  agent-runtime:latest
```

Or add to `docker-compose.yaml`:

```yaml
  research-agent:
    build:
      context: .
      dockerfile: Dockerfile
    environment:
      - SOURCE_TYPE=postgres
      - POSTGRES_DSN=postgresql://agent_admin:agent_admin_pw_dev_only@agent-postgres:5432/agent_control_plane
      - AGENT_NAME=research-agent
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    depends_on:
      - agent-postgres
    networks:
      - agent-network
    restart: unless-stopped
```

## Troubleshooting

### Check agent logs
```bash
docker logs demo-agent
```

### Verify agent loaded correctly
```bash
docker exec demo-agent python -c "import os; print(f'Agent: {os.getenv(\"AGENT_NAME\")}')"
```

### Test database connectivity
```bash
docker exec agent-postgres psql -U agent_admin -d agent_control_plane -c "SELECT name FROM agents;"
```

### Rebuild after code changes
```bash
docker-compose build
docker-compose up -d
```
