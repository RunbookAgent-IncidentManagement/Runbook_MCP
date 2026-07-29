#!/usr/bin/env python3
"""
MCP Tool Client Module
Thin stdio client managing sessions to local Kubernetes and Jira MCP servers.
Uses official MCP SDK (ClientSession + stdio_client + AsyncExitStack) with direct fallback runner.
"""
import os
import sys
import json
import asyncio
import logging
from typing import Dict, Any, Optional
from contextlib import AsyncExitStack

logger = logging.getLogger(__name__)

# Paths to local MCP servers
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
K8S_SERVER_SCRIPT = os.path.join(BASE_DIR, "mcp-servers", "kubernetes_mcp_server.py")
JIRA_SERVER_SCRIPT = os.path.join(BASE_DIR, "mcp-servers", "jira_mcp_server.py")


class MCPToolClient:
    """Manages MCP tool execution sessions to Kubernetes and Jira servers over stdio."""

    def __init__(self):
        self.k8s_script = K8S_SERVER_SCRIPT
        self.jira_script = JIRA_SERVER_SCRIPT

    async def call_tool(self, server: str, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a tool on the specified MCP server (kubernetes or jira).
        Returns a dictionary response.
        """
        server_key = server.lower()
        script = self.k8s_script if "k8s" in server_key or "kubernetes" in server_key else self.jira_script

        try:
            # 1. Try invoking official stdio MCP client session
            from mcp.client.stdio import stdio_client, StdioServerParameters
            from mcp.client.session import ClientSession

            server_params = StdioServerParameters(
                command=sys.executable,
                args=[script],
                env=dict(os.environ)
            )

            async with stdio_client(server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    result = await session.call_tool(tool_name, arguments)
                    
                    # Extract content from MCP response
                    if hasattr(result, "content") and result.content:
                        text_content = ""
                        for item in result.content:
                            if hasattr(item, "text"):
                                text_content += item.text
                        try:
                            return json.loads(text_content)
                        except Exception:
                            return {"status": "success", "raw_text": text_content}
                    return {"status": "success", "data": str(result)}
        except Exception as exc:
            logger.debug(f"MCP stdio session fallback for server '{server}': {exc}. Using direct in-process/script runner.")
            return await self._direct_script_call(server_key, tool_name, arguments)

    async def _direct_script_call(self, server: str, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Direct execution fallback for MCP tools."""
        if "k8s" in server or "kubernetes" in server:
            sys.path.insert(0, os.path.join(BASE_DIR, "mcp-servers"))
            import kubernetes_mcp_server as k8s_srv
            func = getattr(k8s_srv, tool_name, None)
            if func:
                raw = func(**arguments)
                try:
                    return json.loads(raw) if isinstance(raw, str) else raw
                except Exception:
                    return {"result": raw}
        elif "jira" in server:
            sys.path.insert(0, os.path.join(BASE_DIR, "mcp-servers"))
            import jira_mcp_server as jira_srv
            func = getattr(jira_srv, tool_name, None)
            if func:
                raw = func(**arguments)
                try:
                    return json.loads(raw) if isinstance(raw, str) else raw
                except Exception:
                    return {"result": raw}

        return {"status": "error", "message": f"Tool '{tool_name}' not found on server '{server}'."}


mcp_client = MCPToolClient()
