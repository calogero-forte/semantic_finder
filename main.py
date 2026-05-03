import logging
import os
from dotenv import load_dotenv

# Load environment variables before setting up MCP
load_dotenv()

from mcppkg.server import McpServer
from mcppkg.tools import get_current_time, get_pdf_text, list_local_files
from mcppkg.resources import get_all_documents, get_documents_by_name, get_documents_by_extension
import uvicorn

# Instantiate the MCP Server
server = McpServer( name_i=os.getenv("MCP_NAME", "mcp_server"), enable_auth_i=False )
# Register the tools
server.register_tools( [get_current_time, get_pdf_text, list_local_files] )
# Register the resources
server.register_resources({
    "local://documents/all": get_all_documents,
    "local://documents/name/{name}": get_documents_by_name,
    "local://documents/extension/{extension}": get_documents_by_extension
})

# Configure basic logging for the script execution 
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

port = int(os.getenv("MCP_PORT", "8001"))
logger.info(f"Starting basic MCP server on port {port}")
mcp_app = server.build_app()
uvicorn.run(mcp_app, host="127.0.0.1", port=port)
