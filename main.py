import logging
import os
from dotenv import load_dotenv

# Load environment variables before setting up MCP
load_dotenv()

from mcppkg.server import McpServer
from mcppkg.tools import get_current_time, get_pdf_text
import uvicorn

# Instantiate the MCP Server
server = McpServer(enable_auth_i=False)
# Register the tools
server.register_tools( [get_current_time, get_pdf_text] )
        
# Configure basic logging for the script execution 
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

port = int(os.getenv("MCP_PORT", "8001"))
logger.info(f"Starting basic MCP server on port {port}")
mcp_app = server.build_app()
uvicorn.run(mcp_app, host="127.0.0.1", port=port)
