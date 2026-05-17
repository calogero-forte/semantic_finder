"""
License Statement & Module Information
======================================

This code is provided as open-source software and has been developed as part of the 
Master in Applied Artificial Intelligence postgraduate course, for the Python Programming topic.

The purpose of this application is to serve as a Model Context Protocol (MCP) server, 
providing a Large Language Model (LLM) the capability to access and retrieve 
information from local documents to answer related queries.

- Program Name: Semantic Finder
- Module Name: tools.py
- Revision: 1.0
- Author: Calogero Forte
- Affiliation: University of Palermo
- Development Date: May 2026
"""

from fastmcp.tools import tool
from fastmcp.exceptions import ToolError
from fastmcp import Context
import datetime
import os
import logging
from docspkg.pdf_document import PDFDocument
from docspkg.document import DocumentException
from docspkg.toc_document import TocDocument

logger = logging.getLogger(__name__)

@tool(
    name="get_current_time",
    description="Get the current date and time.",
)
async def get_current_time() -> str:
    """
    
    Return
    -------------------
    (str) A string representing the current date and time in ISO 8601 format.
    """
    return datetime.datetime.now().isoformat()

##################################################

@tool(
    name="get_documents_toc",
    description="""Retrieve the table of contents of the documents which names contains the keyword (if the document has one).
    In this way the client can understand what topics these document covers""",
    annotations={"readOnlyHint": True}
)
async def get_documents_toc(search_keyword_i: str, ctx_i: Context) -> str:
    """
    Retrieve the table of contents of the documents which names contains the keyword (if the document has one).

    search_keyword_i: (str) The keyword to search for in the document names
    ctx_i: (Context) The FastMCP context

    Return
    -------------------
    (dict) The formatted table of contents
    """
    logger.info(f"Retrieving TOC from documents containing '{search_keyword_i}'")
    # Get the docs_handler
    doc_handler = ctx_i.request_context.lifespan_context.get("doc_handler")
    # Add a timer or some flag
    doc_handler.sync_documents(os.getenv("LOCAL_PATHS"))

    res = []

    for doc in doc_handler.filter_documents(name_i = search_keyword_i): 
        try:
            if(isinstance(doc, TocDocument)):
                logger.info(f"Retrieved TOC from {doc.file_name}")
                res.append({
                    "document": doc.file_name,
                    "toc": doc.toc
                })
        except DocumentException as e:
            logger.error(f"Error getting TOC: {e} in doc {doc.file_name}")
            continue
    
    if(len(res) == 0):
        logger.error(f"No table of contents found for documents containing '{search_keyword_i}'")
        return f"No table of contents found for documents containing '{search_keyword_i}'"
            
    return res


##################################################

@tool(
    name="get_documents_text",
    description="""Retrieve the text that match the searched section in each document.
    In this way a client can answer questions with the information contained in the documents""",
    annotations={"readOnlyHint": True}
)
async def get_documents_text(documents_name_i: list[str], search_keyword_i: str, ctx_i: Context) -> str:
    """
    Retrieve the text that match the searched keyword in each document.

    documents_name_i: (list[str]) The name of the documents file
    search_keyword_i: (str) The keyword to search for in the documents content
    ctx_i: (Context) The FastMCP context

    Return
    -------------------
    (str) The extracted text content
    """

    logger.info(f"Retrieving text from documents '{documents_name_i}' for keyword '{search_keyword_i}'")

    res = []

    # Get the docs_handler
    doc_handler = ctx_i.request_context.lifespan_context.get("doc_handler")
    # Add a timer or some flag
    doc_handler.sync_documents(os.getenv("LOCAL_PATHS"))
    
    for doc in doc_handler.filter_documents(name_i = documents_name_i, extension_i = ["pdf", "docx"]):
        try:
            logger.info(f"Extracting text related to '{search_keyword_i}' from {doc.file_name}")
            section_res = doc.get_section_text_by_heading(search_keyword_i)
            if isinstance(section_res, tuple):
                res.append( section_res[1] )
            else:
                logger.warning(f"Keyword '{search_keyword_i}' not found in {doc.file_name}")
        except DocumentException as e:
            logger.error(f"Error getting section text by heading: {e} in doc {doc.file_name}")
            continue

    if(len(res) > 0):
        logger.info(f"Successfully extracted text for keyword '{search_keyword_i}' from documents")
        return "\n".join(res)
    else:
        logger.error(f"No results found for keyword '{search_keyword_i}' in documents '{documents_name_i}'")
        return f"No results found for keyword '{search_keyword_i}' in documents '{documents_name_i}'"

##################################################

@tool(
    name="analyze_txt_document",
    description="""Analyze the content of a txt file on the base of a query.
    A query can be a prompt to the Agent ant the client can use the output to answer it""",
    annotations={"readOnlyHint": True}
)
async def analyze_txt_document(txt_name_i: str, query_i: str, ctx_i: Context) -> str:
    """
    Analyze a text document and return a summary of its content.

    txt_name_i: (str) The name of the text document
    query_i: (str) The query to analyze the document on the base of
    ctx_i: (Context) The FastMCP context

    Return
    -------------------
    (str) A summary of the document content
    """

    logger.info(f"Analyzing text document '{txt_name_i}'")

    # Get the docs_handler
    doc_handler = ctx_i.request_context.lifespan_context.get("doc_handler")
    # Add a timer or some flag
    doc_handler.sync_documents(os.getenv("LOCAL_PATHS"))
    
    res = []
    for txt in doc_handler.filter_documents(name_i = txt_name_i, extension_i = "txt"):
        try:
            logger.info(f"Analyzing text document '{txt.file_name}'")

            for i in range(txt.page_num):
                current_page = txt.get_page_text(i)
                if query_i in current_page:
                    res.append(current_page)
                    res.append("\n")
            
        except DocumentException as e:
            logger.error(f"Error analyzing text document: {e} in {txt.file_name}")
            res.append("")
            continue

    return "\n".join(res)