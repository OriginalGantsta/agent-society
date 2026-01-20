"""PostgreSQL-based configuration source.

Loads configuration from PostgreSQL database tables via tool_catalog view:
    - agents
    - agent_versions
    - agent_version_tools
    - agent_version_middlewares
    - tool_catalog (view: mcp_servers UNION agents)
    - middleware_types
    
Requires psycopg2 or psycopg (add to requirements.txt):
    psycopg2-binary>=2.9.0
"""
import json
import sys
from typing import Any, Dict, Optional
from uuid import UUID


class PostgresSource:
    """Load configuration from PostgreSQL database.
    
    This source reads agent configuration from a PostgreSQL database,
    including LLM settings, tools, middlewares, and MCP server configurations.
    
    Database Schema:
        agents - Agent metadata (name, description)
        agent_versions - Agent version configuration (model, temperature, prompt)
        agent_version_tools - Tools associated with agent version
        agent_version_middlewares - Middleware configurations
        tool_catalog - Unified view of mcp_servers and agents
        middleware_types - Middleware type registry
    
    Args:
        connection_string: PostgreSQL connection string
        agent_name: Name of the agent to load configuration for
        
    Example:
        >>> conn_str = "postgresql://user:pass@localhost:5432/agent_control_plane"
        >>> source = PostgresSource(conn_str, agent_name="research-agent")
        >>> config_data = source.load(no_mcp=False)
    """
    
    def __init__(self, connection_string: str, agent_name: str):
        """Initialize repository with database connection.
        
        Args:
            connection_string: PostgreSQL connection string (DSN)
            agent_name: Name of the agent to load
        """
        self.connection_string = connection_string
        self.agent_name = agent_name
        self._conn = None
    
    def _connect(self):
        """Lazy connection initialization."""
        if self._conn is None:
            try:
                import psycopg2
                from psycopg2.extras import RealDictCursor
                self._conn = psycopg2.connect(
                    self.connection_string,
                    cursor_factory=RealDictCursor
                )
            except ImportError:
                raise ImportError(
                    "psycopg2 is required for PostgresSource. "
                    "Install with: pip install psycopg2-binary"
                )
        return self._conn
    
    def _close(self):
        """Close database connection."""
        if self._conn is not None:
            self._conn.close()
            self._conn = None
    
    def load(self, no_mcp: bool = False) -> Dict[str, Any]:
        """Load complete agent configuration from PostgreSQL.
        
        Orchestrates the config assembly pipeline:
        1. Fetch agent and active version data
        2. Build base config (name, LLM, prompt)
        3. Build middlewares config
        4. Build tools config with override support
        
        Args:
            no_mcp: If True, sets tools to empty list; otherwise loads 
                    tools from agent_version_tools with override support
        
        Returns:
            Complete agent configuration dictionary with tools always present
            (empty list if no tools configured or no_mcp=True)
            
        Raises:
            FileNotFoundError: If agent or active version not found
        """
        try:
            conn = self._connect()
            cur = conn.cursor()
            
            agent_data = self._fetch_agent_data(cur)
            
            # Build sub-objects
            name = agent_data["name"]
            description = agent_data.get("description", "")
            llm = self._build_llm(agent_data)
            prompt = self._build_prompt(agent_data)
            middlewares = self._build_middlewares(agent_data) or []
            tools = [] if no_mcp else (self._build_tools(agent_data) or [])
            
            # Assemble final config
            config = {
                "name": name,
                "description": description,
                "llm": llm,
                "middlewares": middlewares,
                "tools": tools
            }
            
            if prompt:
                config["prompt"] = prompt
            
            return config
            
        finally:
            self._close()
    
    def _fetch_agent_data(self, cur) -> Dict[str, Any]:
        """Fetch agent, version, middlewares, and tools in a single query.
        
        Uses CTEs with JSON aggregation to minimize database round trips.
        Leverages tool_catalog view for unified tool access (MCP + agents).
        Applies filters for active version and enabled items at query level.
        
        Args:
            cur: Database cursor
        
        Returns:
            Dictionary with agent metadata, middlewares array, and tools array
            
        Raises:
            FileNotFoundError: If agent not found or has no active version
        """
        # TODO: Use schema versioning to handle different config formats
        cur.execute("""
            WITH agent_data AS (
                SELECT 
                    a.id as agent_id,
                    a.name,
                    a.description,
                    av.id as version_id,
                    av.version,
                    av.model_name,
                    av.model_temperature,
                    av.prompt,
                    av.schema_version
                FROM agents a
                JOIN agent_versions av ON a.id = av.agent_id
                WHERE a.name = %s AND av.is_active = TRUE
                LIMIT 1
            ),
            middlewares_agg AS (
                SELECT 
                    ad.version_id,
                    COALESCE(
                        json_agg(
                            json_build_object(
                                'type', avm.middleware_type,
                                'config', avm.config,
                                'enabled', avm.enabled,
                                'execution_order', avm.execution_order
                            )
                            ORDER BY avm.execution_order
                        ) FILTER (WHERE avm.middleware_type IS NOT NULL),
                        '[]'::json
                    ) as middlewares
                FROM agent_data ad
                LEFT JOIN agent_version_middlewares avm 
                    ON ad.version_id = avm.agent_version_id 
                    AND avm.enabled = TRUE
                GROUP BY ad.version_id
            ),
            tools_agg AS (
                SELECT 
                    ad.version_id,
                    COALESCE(
                        json_agg(
                            json_build_object(
                                'tool_kind', tc.tool_kind,
                                'tool_id', avt.tool_id,
                                'tool_name', tc.tool_name,
                                'enabled', avt.enabled,
                                'priority', avt.priority,
                                'transport', COALESCE(
                                    avt.override->>'transport',
                                    tc.transport
                                ),
                                'command', COALESCE(
                                    avt.override->>'command',
                                    tc.command
                                ),
                                'args', COALESCE(
                                    avt.override->'args',
                                    tc.args
                                ),
                                'env', COALESCE(
                                    avt.override->'env',
                                    tc.env
                                )
                            )
                            ORDER BY avt.priority
                        ) FILTER (WHERE avt.tool_id IS NOT NULL AND avt.enabled = TRUE AND tc.enabled = TRUE),
                        '[]'::json
                    ) as tools
                FROM agent_data ad
                LEFT JOIN agent_version_tools avt ON ad.version_id = avt.agent_version_id
                LEFT JOIN tool_catalog tc ON avt.tool_id = tc.tool_id
                GROUP BY ad.version_id
            )
            SELECT 
                ad.*,
                ma.middlewares,
                ta.tools
            FROM agent_data ad
            LEFT JOIN middlewares_agg ma ON ad.version_id = ma.version_id
            LEFT JOIN tools_agg ta ON ad.version_id = ta.version_id
        """, (self.agent_name,))
        
        result = cur.fetchone()
        if not result:
            raise FileNotFoundError(
                f"Agent '{self.agent_name}' not found or has no active version"
            )
        
        return result
    
    def _build_llm(self, agent_data: Dict[str, Any]) -> Dict[str, Any]:
        """Build LLM configuration.
        
        Args:
            agent_data: Raw agent data from database
            
        Returns:
            LLM configuration dictionary with model_name and temperature
        """
        return {
            "model_name": agent_data["model_name"],
            "temperature": float(agent_data["model_temperature"])
        }
    
    def _build_prompt(self, agent_data: Dict[str, Any]) -> Optional[str]:
        """Build prompt configuration.
        
        Args:
            agent_data: Raw agent data from database
            
        Returns:
            Prompt string if present, None otherwise
        """
        return agent_data.get("prompt")
    
    def _build_middlewares(self, agent_data: Dict[str, Any]) -> Optional[list]:
        """Transform middleware data into config format.
        
        Business Rule: Only enabled middlewares, ordered by execution_order.
        The query pre-filters and pre-orders, this just transforms the shape.
        
        Args:
            agent_data: Raw agent data containing middlewares array
            
        Returns:
            List of middleware configs, or None if no middlewares
        """
        middlewares = agent_data.get("middlewares", [])
        if not middlewares:
            return None
        
        return [
            {
                "type": m["type"],
                "enabled": m["enabled"],
                **({"config": m["config"]} if m["config"] else {})
            }
            for m in middlewares
        ]
    
    def _build_tools(self, agent_data: Dict[str, Any]) -> Optional[list]:
        """Transform tool data into MCP servers config format.
        
        TODO: HTTP-BASED AGENT TOOL RESOLUTION (Dec 2025)
        ================================================================
        IMPLEMENTED: Agent tools now default to HTTP transport instead of stdio
        
        For tool_kind='agent':
        1. Queries agent_instances table to find running instance:
           - Looks up by agent name
           - Filters by heartbeat freshness (last 20 minutes)
           - Orders by most recent heartbeat
        2. If healthy instance found:
           - Uses HTTP transport with endpoint URL from database
           - Example: {"transport": "http", "url": "http://demo-agent:8000"}
           - No command/args needed (HTTP doesn't spawn processes)
        3. If no instance found:
           - Falls back to stdio transport
           - Spawns new process with: python -m agent.mcp.server --source-type postgres ...
        
        BENEFIT: Agents can communicate via HTTP instead of spawning new processes
        - supervisor-agent can call demo-agent's running instance
        - More efficient than stdio (no process startup overhead)
        - Leverages existing heartbeat-based health tracking
        
        SEE ALSO: _get_agent_instance_endpoint() method below
        ================================================================
        
        Business Rules:
        - Only enabled tools from enabled servers (pre-filtered by query)
        - Respects agent_version_tools.override for command/args/transport/env
        - Groups multiple tools by server name into single MCP config
        - For 'agent' tool_kind: queries agent_instances table to find running instance
          and uses HTTP transport with endpoint URL (defaults to http if no instance found)
        - Special handling: "python" command is resolved to sys.executable for venv compatibility
        
        Args:
            agent_data: Raw agent data containing tools array from tool_catalog
            
        Returns:
            List with single MCP tool config, or None if no tools
        """
        tools_data = agent_data.get("tools", [])
        if not tools_data:
            return None
        
        servers = {}
        for tool in tools_data:
            tool_name = tool["tool_name"]
            tool_kind = tool["tool_kind"]
        
            if tool_kind == "agent":
                # Query agent_instances to find a running instance
                endpoint_url = self._get_agent_instance_endpoint(tool_name)
                
                if endpoint_url:
                    # Use HTTP transport with endpoint from agent_instances
                    server_config = {
                        "transport": tool["transport"] or "http",
                        "url": endpoint_url
                    }
                    
                    # HTTP transport doesn't need command/args
                    if tool["env"]:
                        server_config["env"] = tool["env"]
                else:
                    # Fallback to stdio if no running instance found
                    command = tool["command"] or sys.executable
                    if command == "python":
                        command = sys.executable
                    
                    server_config = {
                        "transport": "stdio",
                        "command": command
                    }
                    
                    if tool["args"]:
                        server_config["args"] = tool["args"]
                    else:
                        server_config["args"] = [
                            "-m", "agent.mcp.server",
                            "--source-type", "postgres",
                            "--postgres-dsn", self.connection_string,
                            "--agent-name", tool_name
                        ]
                    
                    if tool["env"]:
                        server_config["env"] = tool["env"]
            else:
                # Resolve "python" keyword for MCP servers
                command = tool["command"]
                if command == "python":
                    command = sys.executable
                
                server_config = {
                    "transport": tool["transport"],
                    "command": command
                }
                if tool["args"]:
                    server_config["args"] = tool["args"]
                if tool["env"]:
                    server_config["env"] = tool["env"]
            
            servers[tool_name] = server_config
        
        if not servers:
            return None
        
        return [
            {
                "type": "mcp",
                "enabled": True,
                "servers": servers
            }
        ]
    
    def _get_agent_instance_endpoint(self, agent_name: str) -> Optional[str]:
        """Get endpoint URL for a running agent instance.
        
        Queries agent_instances table to find the most recent healthy instance
        based on heartbeat freshness (within last 20 minutes).
        
        Args:
            agent_name: Name of the agent to find
            
        Returns:
            Endpoint URL if healthy instance found, None otherwise
        """
        try:
            conn = self._connect()
            cur = conn.cursor()
            
            cur.execute("""
                SELECT ai.endpoint_url
                FROM agent_instances ai
                JOIN agents a ON ai.agent_id = a.id
                WHERE a.name = %s
                  AND ai.last_heartbeat > NOW() - INTERVAL '20 minutes'
                ORDER BY ai.last_heartbeat DESC
                LIMIT 1
            """, (agent_name,))
            
            result = cur.fetchone()
            if result:
                return result['endpoint_url']
            return None
        except Exception as e:
            import sys
            print(f"Warning: Failed to query agent instance for {agent_name}: {e}", file=sys.stderr)
            return None
    

