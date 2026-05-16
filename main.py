from mcppkg.server import McpServer
import os

# Instantiate the MCP Server
server = McpServer( name_i=os.getenv("MCP_NAME", "mcp_server"), enable_auth_i=True )

# Run the server
server()


