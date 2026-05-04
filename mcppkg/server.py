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
from docspkg.document_handler import DocumentHandler
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)

@asynccontextmanager
async def mcp_lifespan(server: FastMCP) -> dict:
    """
    Lifespan manager for the MCP server.

    Return
    -------------------
    (dict) A dictionary containing a DocumentHandler instance
    """
    yield {"doc_handler": DocumentHandler()}

class McpServer:
    """
    This class instantiates an MCP server and provides
    methods to build the ASGI application and to 
    register tools and resources.
    """

    def __init__(self, name_i="mcp_server", enable_auth_i=True):        

        # Authenticator instantiation
        if( enable_auth_i ):
            self.mcp_authenticator = MCPAuthenticator()
            provider = self.mcp_authenticator.provider
        else:
            self.mcp_authenticator = None
            provider = None

        # MCP creation
        self.mcp = FastMCP(
            name=name_i,
            auth=provider,
            lifespan=mcp_lifespan,
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

    def register_tools(self, tool_i: Tool | list[Tool]):

        if( isinstance(tool_i, list) ):
            for tool in tool_i:
                self.mcp.add_tool(tool)
        else:
            self.mcp.add_tool(tool_i)

    def register_resources(self, resource_i: Resource | list[Resource]):

        if( isinstance(resource_i, list) ):
            for res in resource_i:
                self.mcp.add_resource(res)
        else:
            self.mcp.add_resource(resource_i)

    def register_routes(self, route_i: Callable, uri_i: str, http_method_i: str | list[str]):
        if( isinstance( http_method_i, list) ):
            self.mcp.custom_route(uri_i, methods=http_method_i)(route_i)
        else:
            self.mcp.custom_route(uri_i, methods=[http_method_i])(route_i)


    def __call__(self):

        from dotenv import load_dotenv
        from mcppkg.routes import health
        from mcppkg.tools import get_current_time, get_pdf_text, get_pdf_toc
        from mcppkg.resources import get_all_documents, get_documents_by_name, get_documents_by_extension
        import uvicorn

        # Load environment variables before setting up MCP
        load_dotenv()

        # Register health route
        self.register_routes(health, "/health", "GET")
        # Register the tools
        self.register_tools( [get_current_time, get_pdf_text, get_pdf_toc] )
        # Register the resources
        self.register_resources( [get_all_documents, get_documents_by_name, get_documents_by_extension] )

        # Configure basic logging for the script execution 
        logging.basicConfig(level=logging.INFO)
        logger = logging.getLogger(__name__)

        port = int(os.getenv("MCP_PORT", "8001"))
        logger.info(f"Starting basic MCP server on port {port}")
        mcp_app = self.build_app()
        uvicorn.run(mcp_app, host="127.0.0.1", port=port)
        
