"""McpServer class encapsulating FastMCP server and authentication."""
from __future__ import annotations

import logging
import os
from typing import Any
from fastmcp import FastMCP
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from .authentication import MCPAuthenticator, _RegistrationCompatMiddleware
from .routes import health

logger = logging.getLogger(__name__)

class McpServer:
    def __init__(self, enable_auth_i=True):        

        # Authenticator instantiation
        if( enable_auth_i ):
            self.mcp_authenticator = MCPAuthenticator()
            provider = self.mcp_authenticator.provider
        else:
            self.mcp_authenticator = None
            provider = None

        # MCP creation
        self.mcp = FastMCP(
            name="fincance_mcp",
            auth=provider,
        )

        # Registration
        if(self.mcp_authenticator != None):
            self.mcp_authenticator.register_routes(self.mcp)


    def build_app(self) -> Any:
        """
        Build and return the ASGI application.

        Return
        -------------------
        (Any) The constructed ASGI application instance.
        """
        self.mcp.custom_route("/health", methods=["GET"])(health)
        
        app = self.mcp.http_app(path="/mcp", stateless_http=False)
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["https://antigravity.google"],
            allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:\d+)?",
            allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
            allow_headers=["Authorization", "Content-Type", "mcp-session-id"],
            expose_headers=["mcp-session-id"],
        )
        if( self.mcp_authenticator != None and self.mcp_authenticator.enabled ):
            app = _RegistrationCompatMiddleware(app)
        return app

    def get_mcp(self) -> FastMCP:
        return self.mcp

    def register_tools(self, tool_i: Tool | [Tool]):

        if( isinstance(tool_i, list) ):
            for tool in tool_i:
                self.mcp.add_tool(tool)
        else:
            self.mcp.add_tool(tool_i)

    def __call__(self):
        pass
        
