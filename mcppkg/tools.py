from fastmcp.tools import tool
from fastmcp.exceptions import ToolError
from fastmcp import Context

import datetime
import os
import logging
from docs_handlers.pdf_document import PDFDocument

logger = logging.getLogger(__name__)

@tool(
    name="get_current_time",
    description="Get the current date and time.",
)
async def get_current_time() -> str:
    """Get the current date and time.
    
    Returns:
        A string representing the current date and time in ISO 8601 format.
    """
    return datetime.datetime.now().isoformat()

@tool(
    name="get_pdfs_toc",
    description="""Retrieve the table of contents of the PDF given by name.
    In this way the client can understand what topics this PDF covers""",
    annotations={"readOnlyHint": True}
)
async def get_pdf_toc(pdf_name_i: str, ctx: Context) -> str:
    logger.info(f"Retrieving TOC from PDF '{pdf_name_i}'")
    # Get the docs_handler
    doc_handler = ctx.request_context.lifespan_context.get("doc_handler")
    # Add a timer or some flag
    doc_handler.sync_documents(os.getenv("LOCAL_PATHS"))
    toc = None
    for pdf in doc_handler.filter_documents(name_i = pdf_name_i):
        toc = pdf.get_toc()

    if(toc != None):
        logger.info(f"Successfully retrieved TOC from {pdf.file_name}")
        return PDFDocument.formtat_toc(toc)
    else:
        logger.error(f"No results found for TOC in document '{pdf_name_i}'")
        raise ToolError("The research didn't yeld any result")


@tool(
    name="get_pdfs_texts",
    description="""Retrieve the text that match the searched section in each pdf documents.
    In this way a client can answer a question with the information contained in the PDF documents""",
    annotations={"readOnlyHint": True}
)
async def get_pdf_text(pdf_name_i: str, section_title_i: str, ctx: Context) -> dict:

    logger.info(f"Retrieving text from PDF '{pdf_name_i}' for section '{section_title_i}'")

    res = []

    # Get the docs_handler
    doc_handler = ctx.request_context.lifespan_context.get("doc_handler")
    # Add a timer or some flag
    doc_handler.sync_documents(os.getenv("LOCAL_PATHS"))
    
    for pdf in doc_handler.filter_documents(name_i = pdf_name_i, extension_i = "pdf"):
        logger.info(f"Extracting section '{section_title_i}' from {pdf.file_name}")
        res.append( pdf.get_section_text_by_heading(section_title_i)[1] )

    if(len(res) > 0):
        logger.info(f"Successfully extracted section '{section_title_i}' from documents")
        return "\n".join(res)
    else:
        logger.error(f"No results found for section '{section_title_i}' in document '{pdf_name_i}'")
        raise ToolError("The research didn't yeld any result")

# @tool(
#     name="list_local_files",
#     description="List all files in the directory specified by LOCAL_PATHS in .env.",
# )
# async def list_local_files() -> list[str]:
#     """List all files in the directory specified by LOCAL_PATHS in .env.
    
#     Returns:
#         A list of strings representing the names of the files in the directory.
#     """
#     local_path = os.getenv("LOCAL_PATHS", "~/")
#     local_path = os.path.expanduser(local_path)
    
#     if not os.path.isdir(local_path):
#         return [f"Error: {local_path} is not a valid directory."]
        
#     try:
#         files = []
#         for file in os.listdir(local_path):
#             if os.path.isfile(os.path.join(local_path, file)):
#                 files.append(file)
#         return files
#     except Exception as e:
#         return [f"Error reading directory {local_path}: {str(e)}"]





