from fastmcp.tools import tool
from fastmcp.exceptions import ToolError
from fastmcp import Context

import datetime
import os
import logging
from docspkg.pdf_document import PDFDocument
from docspkg.document import DocumentException

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
        try:
            logger.info(f"Extracting section '{section_title_i}' from {pdf.file_name}")
            res.append( pdf.get_section_text_by_heading(section_title_i)[1] )
        except DocumentException as e:
            logger.error(f"Error getting section text by heading: {e} in pdf {pdf.file_name}")
            continue

    if(len(res) > 0):
        logger.info(f"Successfully extracted section '{section_title_i}' from documents")
        return "\n".join(res)
    else:
        logger.error(f"No results found for section '{section_title_i}' in document '{pdf_name_i}'")
        raise ToolError("The research didn't yeld any result")





