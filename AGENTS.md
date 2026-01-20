# Agent Instructions

## Quick Start

### CLI Mode (Terminal Chat)
```powershell
.\.venv\Scripts\Activate.ps1
cd src
python -m pytest tests/ -v
python -m agent.cli.cli
```

### MCP Server Mode
```powershell
.\.venv\Scripts\Activate.ps1
cd src
python -m agent.mcp.server
```

## Entrypoints

The system now supports multiple entrypoints:

- **CLI**: `agent/cli/cli.py` - Terminal-based interactive chat
- **MCP Server**: `agent/mcp/server.py` - Model Context Protocol server exposing agent as MCP tool
- **Shared Bootstrap**: `agent/bootstrap.py` - Common agent creation logic used by all entrypoints

### MCP Server Implementation

The MCP server exposes the agent's chat capability as a Model Context Protocol tool using FastMCP:

- **Tool**: `chat(message: str, thread_id: str)` - Send a message and get agent response
- **Architecture**: Lazy singleton pattern for agent instance
- **Testing**: Fully tested using TDD methodology

**Run the server:**
```powershell
python -m agent.mcp.server --source-type postgres --postgres-dsn "..." --agent-name demo-agent
```

## Database Access

PostgreSQL running in Docker: `agent-postgres` on port 5432

**Query via psql:**
```powershell
# Simple queries (use -t for tuple-only output to avoid hanging)
docker exec agent-postgres psql -U agent_admin -d agent_control_plane -c "SELECT version();"
docker exec agent-postgres psql -U agent_admin -d agent_control_plane -c "\dt"

# View agents
docker exec agent-postgres psql -U agent_admin -d agent_control_plane -c "SELECT id, name, description FROM agents;"

# View active agent versions
docker exec agent-postgres psql -U agent_admin -d agent_control_plane -c "SELECT a.name, av.version, av.model_name FROM agents a JOIN agent_versions av ON a.id = av.agent_id WHERE av.is_active = TRUE;"

# View tool catalog (MCP servers + agents)
docker exec agent-postgres psql -U agent_admin -d agent_control_plane -c "SELECT tool_kind, tool_name, tool_description FROM tool_catalog WHERE enabled = TRUE;"

# View agent's tools
docker exec agent-postgres psql -U agent_admin -d agent_control_plane -c "SELECT a.name, tc.tool_kind, tc.tool_name FROM agents a JOIN agent_versions av ON a.id = av.agent_id JOIN agent_version_tools avt ON av.id = avt.agent_version_id JOIN tool_catalog tc ON avt.tool_id = tc.tool_id WHERE a.name = 'supervisor-agent' AND av.is_active = TRUE AND avt.enabled = TRUE;"
```

**Connection details:**
- Host: localhost:5432
- User: agent_admin
- Password: agent_admin_pw_dev_only
- Database: agent_control_plane

## Creating Agents with Agent Tools

### Example: Supervisor Agent Using Demo Agent

The database now supports **agents-as-tools** via the `tool_catalog` view, which provides a unified interface for both MCP servers and agents.

**1. Create a new agent:**
```powershell
docker exec agent-postgres psql -U agent_admin -d agent_control_plane -c "INSERT INTO agents (id, name, description, created_at) VALUES (gen_random_uuid(), 'supervisor-agent', 'Supervisor agent that delegates research tasks', NOW()) RETURNING id, name;"
```

**2. Create an active version:**
```powershell
docker exec agent-postgres psql -U agent_admin -d agent_control_plane -c "INSERT INTO agent_versions (id, agent_id, version, model_name, model_temperature, prompt, is_active, schema_version, created_at) VALUES (gen_random_uuid(), '<agent-id>', 1, 'gpt-4o-mini', 0.3, 'Your prompt here...', TRUE, 1, NOW()) RETURNING id, version;"
```

**3. Add an agent as a tool (using `tool_kind='agent'`):**
```powershell
docker exec agent-postgres psql -U agent_admin -d agent_control_plane -c "INSERT INTO agent_version_tools (id, agent_version_id, tool_kind, tool_id, enabled, priority, created_at) VALUES (gen_random_uuid(), '<version-id>', 'agent', '<demo-agent-id>', TRUE, 1, NOW()) RETURNING id, tool_kind, enabled;"
```

**4. Optional: Add custom overrides (transport, command, args, env):**
```powershell
docker exec agent-postgres psql -U agent_admin -d agent_control_plane -c "UPDATE agent_version_tools SET override = '{\"transport\": \"sse\", \"env\": {\"CUSTOM_VAR\": \"value\"}}' WHERE id = '<tool-id>';"
```

### How Agent Tools Work

- **Convention-based defaults**: Agent tools with NULL command/args automatically get:
  - `transport`: "stdio"
  - `command`: "python"  
  - `args`: `["-m", "agent.mcp.server", "--source-type", "postgres", "--postgres-dsn", "<dsn>", "--agent-name", "<name>"]`

- **Override support**: Use `agent_version_tools.override` JSONB column to customize any field
- **Unified view**: `tool_catalog` view provides consistent interface for both MCP servers and agents
- **Single provider**: All tools (MCP and agent) go through the same MCP tool resolver

## Design Rules

### Model Organization

**Principle:** Models belong where they have semantic meaning, not in generic directories.

**Rules:**
- Agent configuration model (`AgentConfig`) → `agent/config/agent_config.py`
- Infrastructure specs (`ToolSpec`, `LLMSpec`, `MiddlewareSpec`, `CheckpointerSpec`) → `agent/infrastructure/<area>/specs.py`
- Protocols (ConfigSource) → interface abstraction layer

### Explicit Structure

Favor explicit imports over `__init__.py` side effects. Provider registration happens via explicit imports in bootstrap modules (e.g., `agent/services/agent.py`), not hidden in package initialization.

Use `__init__.py` only for: public APIs, intentional initialization, or improving clarity.

### Test-Code Alignment

**Problem:** Refactors changing file structure leave tests misaligned, creating brittle suites.

**Rule:** When refactoring code, update tests concurrently:
- Move test files to mirror source structure
- Rename tests to match new components
- Update imports, mocks, and fixtures
- Remove obsolete test files
- Validate all tests pass

**Example:**
```
# Before
agent/services/checkpointer.py → tests/services/test_checkpointer.py

# After  
agent/checkpointer/resolver.py → tests/checkpointer/test_checkpointer_resolver.py
```

A refactor is incomplete if tests don't match the refactored structure.
