"""MCP Server entrypoint.

Runs the agent as a Model Context Protocol server, exposing agent
capabilities through the MCP protocol.

TODO: AGENT INSTANCE TRACKING & HTTP-BASED AGENT COMMUNICATION (Dec 2025)
============================================================================
IMPLEMENTED:
- agent_instances table: Runtime tracking of deployed agent instances
  - Columns: id, agent_id, agent_version_id, endpoint_url, transport, 
    last_heartbeat, started_at, stopped_at
  - NO status column - health determined by heartbeat staleness (last 20 min)
  - Index on (agent_id, last_heartbeat) for efficient health queries

- Self-registration on startup:
  - Agents register themselves in agent_instances when they start
  - Endpoint URL constructed from env vars: AGENT_HOSTNAME, MCP_INTERNAL_PORT
  - Uses single atomic CTE query to lookup agent_id/version_id and insert

- Heartbeat mechanism:
  - Background thread sends periodic UPDATE to last_heartbeat
  - Defaults to 900 seconds (15 min), configurable via HEARTBEAT_INTERVAL_SECONDS
  - First heartbeat runs immediately on startup
  - No status transitions - just heartbeat timestamp updates

- Agent-to-agent HTTP communication:
  - Agents can use other agents as tools via MCP protocol
  - Default transport changed from stdio to HTTP
  - postgres.py queries agent_instances table to find running instances
  - Returns HTTP endpoint (e.g., http://demo-agent:8000) instead of spawning process
  - Falls back to stdio if no healthy instance found

DESIGN DECISIONS:
- Removed status column: Heartbeat staleness is authoritative, not declared status
- Infrastructure-driven endpoints: Port/hostname from env vars, not CLI args
- Removed --port argument: Internal port fixed at 8000 (MCP_INTERNAL_PORT)
- Health = heartbeat, not tool usage: Server is healthy when bound, not when called

NEXT STEPS (if resuming):
- Test supervisor-agent calling demo-agent via HTTP in production
- Consider adding metrics/observability for agent communication
- May need to handle stopped_at timestamp on graceful shutdown
- Consider cleanup job for stale instances (heartbeat > X hours old)
============================================================================
"""
import argparse
import asyncio
import os
import threading
from uuid import UUID

from dotenv import load_dotenv
from fastmcp import FastMCP

from agent.bootstrap import create_agent_from_args

_agent = None
_agent_lock = asyncio.Lock()
_args = None
_mcp = None
_instance_id = None


async def get_agent():
    """Get or create the singleton agent instance.
    
    Returns:
        Initialized Agent instance
    """
    global _agent
    if _agent is None:
        async with _agent_lock:
            if _agent is None:
                _agent = await create_agent_from_args(_args)
    return _agent


async def chat(message: str, thread_id: str = "default") -> str:
    """
    Send a message to the conversational AI agent.
    
    Args:
        message: The user's message or question to send to the agent
        thread_id: Unique identifier for the conversation thread. Use the same ID to continue a conversation.
    
    Returns:
        The agent's response to the user's message
    """
    agent = await get_agent()
    reply = await agent.invoke(
        query=message,
        thread_id=thread_id,
    )
    return reply


async def register_agent_instance(args: argparse.Namespace) -> UUID:
    """Register this agent instance in the database.
    
    Args:
        args: Parsed command-line arguments containing postgres connection info
        
    Returns:
        UUID of the created instance record
    """
    try:
        import psycopg2
        from psycopg2.extras import RealDictCursor
        
        conn = psycopg2.connect(args.postgres_dsn, cursor_factory=RealDictCursor)
        cur = conn.cursor()
        
        hostname = os.getenv('AGENT_HOSTNAME', args.agent_name)
        internal_port = int(os.getenv('MCP_INTERNAL_PORT', '8000'))
        endpoint_url = f"http://{hostname}:{internal_port}"
        
        # Insert instance record with initial heartbeat
        cur.execute("""
            WITH agent_data AS (
                SELECT a.id as agent_id, av.id as agent_version_id
                FROM agents a
                JOIN agent_versions av ON a.id = av.agent_id
                WHERE a.name = %s AND av.is_active = TRUE
            )
            INSERT INTO agent_instances 
                (agent_id, agent_version_id, endpoint_url, transport)
            SELECT agent_id, agent_version_id, %s, 'http'
            FROM agent_data
            RETURNING id
        """, (args.agent_name, endpoint_url))
        
        result = cur.fetchone()
        if not result:
            raise ValueError(f"Agent '{args.agent_name}' not found or has no active version")
        
        instance_id = result['id']
        conn.commit()
        
        cur.close()
        conn.close()
        
        return instance_id
        
    except Exception as e:
        import sys
        print(f"Warning: Failed to register agent instance: {e}", file=sys.stderr)
        # Don't fail agent startup if registration fails
        return None


def send_heartbeat(instance_id: UUID, postgres_dsn: str) -> None:
    """Send heartbeat update for this agent instance.
    
    Args:
        instance_id: UUID of the instance record
        postgres_dsn: PostgreSQL connection string
    """
    if instance_id is None:
        return
    
    try:
        import psycopg2
        conn = psycopg2.connect(postgres_dsn)
        cur = conn.cursor()
        
        cur.execute("""
            UPDATE agent_instances 
            SET last_heartbeat = NOW()
            WHERE id = %s
        """, (instance_id,))
        conn.commit()
        
        cur.close()
        conn.close()
    except Exception as e:
        import sys
        print(f"Warning: Failed to send heartbeat: {e}", file=sys.stderr)


def heartbeat_worker(instance_id: UUID, postgres_dsn: str, interval_seconds: int) -> None:
    """Background thread that sends periodic heartbeats.
    
    Runs first heartbeat immediately, then repeats at interval.
    
    Args:
        instance_id: UUID of the instance record
        postgres_dsn: PostgreSQL connection string
        interval_seconds: Seconds between heartbeats
    """
    import time
    
    # Send first heartbeat immediately
    send_heartbeat(instance_id, postgres_dsn)
    
    # Then send periodic heartbeats
    while True:
        time.sleep(interval_seconds)
        send_heartbeat(instance_id, postgres_dsn)


def run_mcp_server() -> None:
    """Run the agent as an MCP server."""
    global _args, _mcp
    
    load_dotenv()
    
    # TODO: Need to figure out how to make langchain tracing work
    import os
    os.environ["LANGCHAIN_TRACING_V2"] = "false"
    
    _args = parse_args()
    
    _mcp = FastMCP(name=_args.agent_name)
    
    # Register the chat tool using add_tool with the mcp instance decorator
    _mcp.add_tool(_mcp.tool()(chat))
    
    # Register agent instance on startup if using postgres
    if _args.source_type == "postgres":
        _instance_id = asyncio.run(register_agent_instance(_args))
        # Start heartbeat thread in background
        # HEARTBEAT_INTERVAL_SECONDS: defaults to 900 (15 minutes)
        # First heartbeat runs immediately, then repeats at interval
        heartbeat_interval = int(os.getenv("HEARTBEAT_INTERVAL_SECONDS", "900"))
        heartbeat_thread = threading.Thread(
            target=heartbeat_worker,
            args=(_instance_id, _args.postgres_dsn, heartbeat_interval),
            daemon=True
        )
        heartbeat_thread.start()
    
    try:
        # Run the FastMCP server with HTTP transport
        # Bind to 0.0.0.0 to accept connections from outside the container
        internal_port = int(os.getenv("MCP_INTERNAL_PORT", "8000"))
        _mcp.run(transport="http", host="0.0.0.0", port=internal_port, show_banner=False)
    except KeyboardInterrupt:
        # Write to stderr, not stdout
        import sys
        print("\nShutting down MCP server...", file=sys.stderr)
    except Exception as e:
        import sys
        print(f"Error: {e}", file=sys.stderr)
        exit(1)


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments for MCP server."""
    parser = argparse.ArgumentParser(
        description="Run agent as MCP server",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    
    parser.add_argument(
        "--config",
        dest="config_base_path",
        type=str,
        default="config",
        help="Path to configuration directory (default: config)",
    )
    
    parser.add_argument(
        "--source-type",
        type=str,
        default=os.getenv("SOURCE_TYPE", "postgres"),
        choices=["filesystem", "postgres"],
        help="Configuration source type (default: postgres, or SOURCE_TYPE env var)",
    )
    
    parser.add_argument(
        "--postgres-dsn",
        type=str,
        default=os.getenv("POSTGRES_DSN"),
        help="PostgreSQL connection string (required for postgres source, defaults to POSTGRES_DSN env var)",
    )
    
    parser.add_argument(
        "--agent-name",
        type=str,
        default=os.getenv("AGENT_NAME"),
        help="Agent name to load from database (required for postgres source, defaults to AGENT_NAME env var)",
    )
    
    parser.add_argument(
        "--no-mcp",
        action="store_true",
        help="Run without loading MCP tools",
    )
    
    args = parser.parse_args()
    
    # Validate postgres source requirements
    if args.source_type == "postgres":
        if not args.postgres_dsn:
            parser.error("--postgres-dsn or POSTGRES_DSN env var is required when --source-type=postgres")
        if not args.agent_name:
            parser.error("--agent-name or AGENT_NAME env var is required when --source-type=postgres")
    
    return args


if __name__ == "__main__":
    run_mcp_server()
