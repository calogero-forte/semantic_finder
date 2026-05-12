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
    """
    
    Return
    -------------------
    (str) A string representing the current date and time in ISO 8601 format.
    """
    return datetime.datetime.now().isoformat()

##################################################

@tool(
    name="get_pdfs_toc",
    description="""Retrieve the table of contents of the PDF given by name.
    In this way the client can understand what topics this PDF covers""",
    annotations={"readOnlyHint": True}
)
async def get_pdf_toc(pdf_name_i: str, ctx_i: Context) -> str:
    """
    Retrieve the table of contents of the PDF given by name.

    pdf_name_i: (str) The name of the PDF file
    ctx_i: (Context) The FastMCP context

    Return
    -------------------
    (str) The formatted table of contents
    """
    logger.info(f"Retrieving TOC from PDF '{pdf_name_i}'")
    # Get the docs_handler
    doc_handler = ctx_i.request_context.lifespan_context.get("doc_handler")
    # Add a timer or some flag
    doc_handler.sync_documents(os.getenv("LOCAL_PATHS"))

    try:
        # TODO: adjust this for which is useless for the moment
        for pdf in doc_handler.filter_documents(name_i = pdf_name_i): 
            logger.info(f"Successfully retrieved TOC from {pdf.file_name}")
            return pdf.toc
    except DocumentException as e:
        logger.error(f"Error getting TOC: {e} in pdf {pdf.file_name}")
        raise ToolError("The research didn't yeld any result")

##################################################

@tool(
    name="get_pdfs_texts",
    description="""Retrieve the text that match the searched section in each pdf documents.
    In this way a client can answer a question with the information contained in the PDF documents""",
    annotations={"readOnlyHint": True}
)
async def get_pdf_text(pdf_name_i: str, section_title_i: str, ctx_i: Context) -> str:
    """
    Retrieve the text that match the searched section in each pdf documents.

    pdf_name_i: (str) The name of the PDF file
    section_title_i: (str) The section title to search for
    ctx_i: (Context) The FastMCP context

    Return
    -------------------
    (str) The extracted text content
    """

    logger.info(f"Retrieving text from PDF '{pdf_name_i}' for section '{section_title_i}'")

    res = []

    # Get the docs_handler
    doc_handler = ctx_i.request_context.lifespan_context.get("doc_handler")
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

##################################################

@tool(
    name="get_word_toc",
    description="""Retrieve the table of contents of the word given by name.
    In this way the client can understand what topics this word covers""",
    annotations={"readOnlyHint": True}
)
async def get_word_toc(word_name_i: str, ctx_i: Context) -> str:
    """
    Retrieve the table of contents of the word given by name.

    word_name_i: (str) The name of the word file
    ctx_i: (Context) The FastMCP context

    Return
    -------------------
    (str) The formatted table of contents
    """
    logger.info(f"Retrieving TOC from word '{word_name_i}'")
    # Get the docs_handler
    doc_handler = ctx_i.request_context.lifespan_context.get("doc_handler")
    # Add a timer or some flag
    doc_handler.sync_documents(os.getenv("LOCAL_PATHS"))

    try:
        # TODO: adjust this for which is useless for the moment
        for word in doc_handler.filter_documents(name_i = word_name_i): 
            logger.info(f"Successfully retrieved TOC from {word.file_name}")
            return word.toc
    except DocumentException as e:
        logger.error(f"Error getting TOC: {e} in {word.file_name}")
        raise ToolError("The research didn't yeld any result")

##################################################

tool(
    name="get_word_text",
    description="""Retrieve the text that match the searched section in each word documents.
    In this way a client can answer a question with the information contained in the word documents""",
    annotations={"readOnlyHint": True}
)
async def get_word_text(word_name_i: str, section_title_i: str, ctx_i: Context) -> str:
    """
    Retrieve the text that match the searched section in each word documents.

    word_name_i: (str) The name of the word file
    section_title_i: (str) The section title to search for
    ctx_i: (Context) The FastMCP context

    Return
    -------------------
    (str) The extracted text content
    """

    logger.info(f"Retrieving text from word '{word_name_i}' for section '{section_title_i}'")

    res = []

    # Get the docs_handler
    doc_handler = ctx_i.request_context.lifespan_context.get("doc_handler")
    # Add a timer or some flag
    doc_handler.sync_documents(os.getenv("LOCAL_PATHS"))
    
    for word in doc_handler.filter_documents(name_i = word_name_i, extension_i = "docx"):
        try:
            logger.info(f"Extracting section '{section_title_i}' from {word.file_name}")
            res.append( word.get_section_text_by_heading(section_title_i)[1] )
            break
        except DocumentException as e:
            logger.error(f"Error getting section text by heading: {e} in {word.file_name}")
            continue

    if(len(res) > 0):
        logger.info(f"Successfully extracted section '{section_title_i}' from documents")
        return "\n".join(res)
    else:
        logger.error(f"No results found for section '{section_title_i}' in document '{word_name_i}'")
        raise ToolError("The research didn't yeld any result")