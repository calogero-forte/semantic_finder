import logging
import os
from dotenv import load_dotenv

# Load environment variables before setting up MCP
load_dotenv()

from mcppkg.server import McpServer
from mcppkg.tools import get_current_time
import uvicorn

server = McpServer()
server.get_mcp().add_tool(get_current_time)
        
# Configure basic logging for the script execution 
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

port = int(os.getenv("MCP_PORT", "8001"))
logger.info(f"Starting basic MCP server on port {port}")
mcp_app = server.build_app()
uvicorn.run(mcp_app, host="127.0.0.1", port=port)
