-- Agent Control Plane Database Schema
-- PostgreSQL 17+ compatible
-- Dumped from actual production database

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

-- ============================================================================
-- TABLES
-- ============================================================================

-- Agents: Core agent metadata
CREATE TABLE agents (
    id UUID PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);

-- Agent Versions: Version-specific configuration
CREATE TABLE agent_versions (
    id UUID PRIMARY KEY,
    agent_id UUID NOT NULL,
    version INTEGER NOT NULL,
    model_name TEXT NOT NULL,
    model_temperature NUMERIC NOT NULL,
    prompt TEXT NOT NULL,
    schema_version INTEGER DEFAULT 1 NOT NULL,
    is_active BOOLEAN DEFAULT FALSE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    CONSTRAINT agent_versions_unique_version UNIQUE (agent_id, version),
    CONSTRAINT agent_versions_agent_id_fkey FOREIGN KEY (agent_id) 
        REFERENCES agents(id) ON DELETE CASCADE
);

-- MCP Servers: External tool servers
CREATE TABLE mcp_servers (
    id UUID PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    description TEXT,
    transport TEXT NOT NULL,
    command TEXT NOT NULL,
    args JSONB NOT NULL,
    env JSONB DEFAULT '{}'::jsonb NOT NULL,
    enabled BOOLEAN DEFAULT TRUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    CONSTRAINT mcp_servers_transport_check CHECK (
        transport = ANY (ARRAY['stdio'::text, 'http'::text, 'sse'::text])
    )
);

-- Agent Version Tools: Tools associated with agent versions
CREATE TABLE agent_version_tools (
    id UUID PRIMARY KEY,
    agent_version_id UUID NOT NULL,
    tool_kind TEXT NOT NULL,
    tool_id UUID NOT NULL,
    enabled BOOLEAN DEFAULT TRUE NOT NULL,
    priority INTEGER,
    override JSONB DEFAULT '{}'::jsonb NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    CONSTRAINT agent_version_tools_unique UNIQUE (agent_version_id, tool_kind, tool_id),
    CONSTRAINT agent_version_tools_kind_check CHECK (
        tool_kind = ANY (ARRAY['mcp_server'::text, 'agent'::text])
    ),
    CONSTRAINT agent_version_tools_agent_version_id_fkey FOREIGN KEY (agent_version_id)
        REFERENCES agent_versions(id) ON DELETE CASCADE
);

-- Middleware Types: Registry of available middleware
CREATE TABLE middleware_types (
    type TEXT PRIMARY KEY,
    description TEXT,
    config_schema JSONB NOT NULL,
    schema_version INTEGER DEFAULT 1 NOT NULL,
    enabled BOOLEAN DEFAULT TRUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);

-- Agent Version Middlewares: Middleware configurations
CREATE TABLE agent_version_middlewares (
    id UUID PRIMARY KEY,
    agent_version_id UUID NOT NULL,
    middleware_type TEXT NOT NULL,
    config JSONB NOT NULL,
    enabled BOOLEAN DEFAULT TRUE NOT NULL,
    execution_order INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    CONSTRAINT agent_middleware_execution_order_unique UNIQUE (agent_version_id, execution_order),
    CONSTRAINT agent_middleware_agent_version_id_fkey FOREIGN KEY (agent_version_id)
        REFERENCES agent_versions(id) ON DELETE CASCADE
);

-- Agent Instances: Runtime tracking of agent deployments
CREATE TABLE agent_instances (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id UUID NOT NULL,
    agent_version_id UUID NOT NULL,
    
    endpoint_url TEXT NOT NULL,
    transport TEXT NOT NULL DEFAULT 'http',
    
    last_heartbeat TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    started_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    stopped_at TIMESTAMP WITH TIME ZONE,
    
    CONSTRAINT agent_instances_agent_id_fkey
        FOREIGN KEY (agent_id) REFERENCES agents(id) ON DELETE CASCADE,
    CONSTRAINT agent_instances_agent_version_id_fkey
        FOREIGN KEY (agent_version_id) REFERENCES agent_versions(id) ON DELETE CASCADE,
    CONSTRAINT agent_instances_transport_check 
        CHECK (transport = ANY (ARRAY['stdio'::text, 'http'::text, 'sse'::text]))
);

-- ============================================================================
-- VIEWS
-- ============================================================================

-- Tool Catalog: Unified view of MCP servers and agents as tools
CREATE VIEW tool_catalog AS
SELECT 
    'mcp_server'::text AS tool_kind,
    s.id AS tool_id,
    s.name AS tool_name,
    s.description AS tool_description,
    s.transport,
    s.command,
    s.args,
    s.env,
    s.enabled
FROM mcp_servers s
UNION ALL
SELECT 
    'agent'::text AS tool_kind,
    a.id AS tool_id,
    a.name AS tool_name,
    a.description AS tool_description,
    NULL::text AS transport,
    NULL::text AS command,
    NULL::jsonb AS args,
    NULL::jsonb AS env,
    (EXISTS (
        SELECT 1 FROM agent_versions av 
        WHERE av.agent_id = a.id AND av.is_active = true
    )) AS enabled
FROM agents a;

-- ============================================================================
-- INDEXES
-- ============================================================================

-- Ensure only one active version per agent
CREATE UNIQUE INDEX agent_one_active_version 
    ON agent_versions USING btree (agent_id) 
    WHERE is_active = true;

-- Optimize instance resolution queries (find healthy instances by heartbeat freshness)
CREATE INDEX idx_agent_instances_resolution 
    ON agent_instances USING btree (agent_id, last_heartbeat);

-- ============================================================================
-- SAMPLE DATA
-- ============================================================================

-- Demo Agent
INSERT INTO agents VALUES (
    'b54fd2cb-0340-4194-8cef-d0f8e8e6796d',
    'demo-agent',
    'Demo agent for testing PostgreSQL configuration source',
    '2025-12-26 22:43:00.738158+00',
    '2025-12-26 22:43:00.738158+00'
);

INSERT INTO agent_versions VALUES (
    '128b3379-03fc-499b-abb6-3fb894f7a3a9',
    'b54fd2cb-0340-4194-8cef-d0f8e8e6796d',
    1,
    'gpt-4o-mini',
    0.7,
    'You are a helpful research assistant. Summarize long conversations concisely.',
    1,
    true,
    '2025-12-26 22:43:00.744773+00'
);

-- Supervisor Agent
INSERT INTO agents VALUES (
    'a2e658fa-99a4-49d3-bcef-58b1294d33a3',
    'supervisor-agent',
    'Supervisor agent that delegates research tasks to specialized agents',
    '2025-12-29 21:40:47.424281+00',
    '2025-12-29 21:40:47.424281+00'
);

INSERT INTO agent_versions VALUES (
    '295a679e-afe1-4d4a-8986-035b72329ae5',
    'a2e658fa-99a4-49d3-bcef-58b1294d33a3',
    1,
    'gpt-4o-mini',
    0.3,
    'You are a supervisor agent that coordinates research tasks. When given a research question, delegate it to your research assistant (demo-agent) who has summarization capabilities. Review the results and provide a clear, synthesized answer to the user.',
    1,
    true,
    '2025-12-29 21:40:54.705399+00'
);
