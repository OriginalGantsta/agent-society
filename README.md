# AI Agent Template

A production-ready, enterprise-grade template for building AI agents using **LangGraph**, **OpenAI**, and the **Model Context Protocol (MCP)**. This template provides a clean, modular architecture with built-in configuration management, comprehensive testing, and async factory patterns.

## Features

- **Modular Architecture**: Clean separation of concerns with `core`, `services`, and `interface` layers
- **Async Factory Pattern**: Proper async initialization using factory methods
- **MCP Integration**: Dynamic tool loading via Model Context Protocol
- **Configuration-Driven**: JSON-based configuration for agents and tools
- **Type-Safe**: Full type hints and dataclass-based configuration
- **Comprehensive Testing**: 16 tests covering all modules with pytest
- **LangSmith Support**: Built-in observability and tracing
- **Conversation Memory**: Thread-based conversation persistence using LangGraph checkpointers
- **Streaming Responses**: Real-time token streaming for better UX

## Architecture

```
agent/
├── agent.py                # Agent runtime and factory
├── bootstrap.py            # Shared agent creation logic
├── observability.py        # LangSmith configuration
├── cli/                    # CLI entrypoint
│   ├── cli.py              # Terminal chat interface
│   └── ui.py               # CLI formatting
├── mcp/                    # MCP server entrypoint
│   └── server.py           # MCP protocol server
├── config/                 # Configuration layer
│   ├── agent_config.py     # Configuration models
│   └── sources/            # Config sources (filesystem, postgres)
├── infrastructure/         # Infrastructure layer
│   ├── llm/                # LLM providers and resolver
│   ├── tools/              # Tool providers and resolver
│   ├── middleware/         # Middleware providers and resolver
│   └── checkpointer/       # Checkpointer providers and resolver
├── app/                    # Application runtimes (future)
└── requirements.txt        # Python dependencies

tests/                      # Test suite
├── cli/
│   ├── test_cli.py
│   └── test_ui.py
├── config/
│   ├── test_config.py
│   └── test_postgres_source.py
├── infrastructure/
│   ├── checkpointer/
│   ├── llm/
│   ├── middleware/
│   └── tools/
├── services/
│   └── test_agent.py
└── conftest.py
```

## Installation

### Prerequisites

- Python 3.12+
- OpenAI API key
- (Optional) LangSmith API key for tracing

### Setup

1. **Clone the repository**:

```bash
git clone <your-repo>
cd src
```

2. **Create a virtual environment**:

```bash
python -m venv agent/venv
```

3. **Activate the virtual environment**:

Windows:

```bash
agent\venv\Scripts\activate
```

Unix/MacOS:

```bash
source agent/venv/bin/activate
```

4. **Install dependencies**:

```bash
pip install -r agent/requirements.txt
```

5. **Configure environment variables**:

Create a `.env` file in the `src` directory:

```env
OPENAI_API_KEY=your_openai_api_key_here
LANGCHAIN_API_KEY=your_langsmith_api_key_here  # Optional
LANGCHAIN_TRACING_V2=true                       # Optional
```

## Configuration

### Agent Configuration

Edit `agent/config/agent.json`:

```json
{
  "name": "my-agent",
  "model": {
    "name": "gpt-4",
    "temperature": 0.7
  },
  "prompt": "You are a helpful AI assistant..."
}
```

### MCP Server Configuration

Edit `agent/config/mcp_servers.json` to add tools:

```json
{
  "sequential-thinking": {
    "command": "npx",
    "args": ["-y", "@modelcontextprotocol/server-sequential-thinking"],
    "transport": "stdio"
  },
  "memory": {
    "command": "npx",
    "args": ["-y", "@modelcontextprotocol/server-memory"],
    "transport": "stdio"
  }
}
```

## Usage

### Interactive Mode

```bash
python -m agent.main
```

### Single Query

```bash
python -m agent.main "What is the weather today?"
```

### With Thread Continuity

```bash
python -m agent.main --thread-id my-session-123
```

### Without MCP Tools

```bash
python -m agent.main --no-mcp
```

### Custom Configuration

```bash
python -m agent.main --config path/to/config
```

### Command-Line Options

```
usage: main.py [-h] [--config CONFIG] [--mcp-dir MCP_DIR] [--interactive]
               [--trace] [--thread-id THREAD_ID] [--no-mcp]
               [query]

positional arguments:
  query                 Query to send to the agent

optional arguments:
  --config CONFIG       Path to configuration directory (default: agent/config)
  --mcp-dir MCP_DIR     Directory containing MCP server JSON files
  --interactive, -i     Run in interactive mode
  --trace               Enable LangSmith tracing
  --thread-id THREAD_ID Thread ID for conversation continuity
  --no-mcp              Run without loading MCP servers
```

## Testing

### Run All Tests

```bash
python -m pytest tests/
```

### Run Specific Test File

```bash
python -m pytest tests/test_main.py
```

### Run with Coverage

```bash
pip install pytest-cov
python -m pytest tests/ --cov=agent --cov-report=html
```

### Test Structure

Tests follow the **Given-When-Then** naming convention:

```python
def test_given_valid_config_when_load_called_then_returns_agent_config():
    # Arrange (Given)
    config_data = {...}

    # Act (When)
    config = AgentConfig.from_dict(config_data)

    # Assert (Then)
    assert config.name == "expected-name"
```

## Development

### Project Patterns

1. **Async Factory Pattern**: Use `AgentFactory.create()` instead of direct instantiation
2. **Dependency Injection**: Services receive dependencies through constructors
3. **Configuration as Code**: JSON files loaded into typed dataclasses
4. **Layered Architecture**: `core` → `services` → `interface`

### Adding New Features

1. **New Service**:

   - Add to `agent/services/`
   - Create corresponding test in `tests/services/`
   - Update factory if needed

2. **New Configuration**:

   - Update `AgentConfig` in `core/config.py`
   - Update `agent.json` schema
   - Add validation tests

3. **New MCP Tool**:
   - Add server config to `mcp_servers.json`
   - No code changes needed (tools loaded dynamically)

### Code Quality

- **Type Hints**: All functions have type annotations
- **Docstrings**: Public APIs documented
- **Linting**: Run `mypy` and `pylint` before committing
- **Testing**: Minimum 80% coverage required

## Architecture Decisions

### Why Async Factory Pattern?

The `AgentFactory.create()` pattern ensures proper async initialization:

- LLM clients need async setup
- Graph construction happens before use
- Cleaner error handling

### Why MCP?

Model Context Protocol allows:

- Dynamic tool addition without code changes
- Standardized tool interface
- Easy integration with external services

### Why LangGraph?

LangGraph provides:

- Built-in memory/checkpointing
- ReAct agent pattern
- Streaming support
- Observability

## Troubleshooting

### Import Error: Module Not Found

If you encounter errors like:

```
ImportError: module 'langchain_core.runnables.config' not found
```

This indicates a version mismatch. Fix by reinstalling dependencies:

```bash
.\agent\venv\Scripts\pip.exe install -r agent/requirements.txt --force-reinstall
```

Or on Unix/MacOS:

```bash
pip install -r agent/requirements.txt --force-reinstall
```

### Import Errors

Ensure you're running as a module:

```bash
python -m agent.main  # ✓ Correct
python agent/main.py  # ✗ Wrong
```

### MCP Tools Not Loading

1. Check `mcp_servers.json` syntax
2. Verify `npx` is installed (`npm install -g npx`)
3. Test with `--no-mcp` flag to isolate issue

### OpenAI API Errors

1. Verify API key in `.env`
2. Check rate limits
3. Ensure model name is correct

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

MIT

## Acknowledgments

- Built with [LangGraph](https://github.com/langchain-ai/langgraph)
- Uses [Model Context Protocol](https://modelcontextprotocol.io/)
- Powered by [OpenAI](https://openai.com/)
