"""
License Statement & Module Information
======================================

This code is provided as open-source software and has been developed as part of the 
Master in Applied Artificial Intelligence postgraduate course, for the Python Programming topic.

The purpose of this application is to serve as a Model Context Protocol (MCP) server, 
providing a Large Language Model (LLM) the capability to access and retrieve 
information from local documents to answer related queries.

- Program Name: Semantic Finder
- Module Name: resources.py
- Revision: 1.0
- Author: Calogero Forte
- Affiliation: University of Palermo
- Development Date: May 2026
"""

import os
import logging
from fastmcp import Context
from fastmcp.resources import resource
# from docspkg.document_handler import DocumentHandler
# from docspkg.document import Document # To check if it is needed
# from docspkg.pdf_document import PDFDocument

logger = logging.getLogger(__name__)

@resource( uri="local://documents/all" )
def get_all_documents(context_i: Context) -> str:
    """
    This resource exposes all documents the client is allowed to access to.

    context_i: (Context) The FastMCP context

    Return
    -------------------
    (str) A formatted string of all documents
    """
    doc_handler = context_i.request_context.lifespan_context.get("doc_handler")
    if doc_handler is None:
        logger.error("DocumentHandler not found in context.")
        return "Error: DocumentHandler not found in context."
    
    logger.info("Accessing all documents resource.")
    
    # Sync with the current content of the directory
    doc_handler.sync_documents( os.getenv("LOCAL_PATHS") )
    
    result = []
    for doc in doc_handler:
        result.append(f"- {doc.file_name}")
        
    logger.info(f"Found {len(result)} documents in the local database.")
        
    if not result:
        return "No documents found in the local database."
        
    return "All documents:\n" + "\n".join(result)

##################################################

@resource( uri="local://documents/name/{name_i}" )
def get_documents_by_name(name_i: str, context_i: Context) -> str:
    """
    This resource filters documents by a given name string.

    name_i: (str) The name to filter by
    context_i: (Context) The FastMCP context

    Return
    -------------------
    (str) A formatted string of filtered documents
    """
    doc_handler = context_i.request_context.lifespan_context.get("doc_handler")
    if doc_handler is None:
        logger.error("DocumentHandler not found in context.")
        return "Error: DocumentHandler not found in context."
        
    logger.info(f"Filtering documents by name: '{name_i}'")
        
    # Sync with the current content of the directory
    doc_handler.sync_documents( os.getenv("LOCAL_PATHS") )
    
    result = []
    for doc in doc_handler.filter_documents(name_i=name_i):
        result.append(f"- {doc.file_name}")
        
    logger.info(f"Found {len(result)} documents matching name: '{name_i}'")
        
    if not result:
        return f"No documents found matching name: '{name_i}'"
        
    return f"Documents matching name '{name_i}':\n" + "\n".join(result)

##################################################

@resource( uri="local://documents/extension/{extension_i}" )
def get_documents_by_extension(extension_i: str, context_i: Context) -> str:
    """
    This resource filters documents by a given extension.

    extension_i: (str) The extension to filter by
    context_i: (Context) The FastMCP context

    Return
    -------------------
    (str) A formatted string of filtered documents
    """
    doc_handler = context_i.request_context.lifespan_context.get("doc_handler")
    if doc_handler is None:
        logger.error("DocumentHandler not found in context.")
        return "Error: DocumentHandler not found in context."
        
    logger.info(f"Filtering documents by extension: '{extension_i}'")
        
    # Sync with the current content of the directory
    doc_handler.sync_documents( os.getenv("LOCAL_PATHS") )
    
    result = []
    for doc in doc_handler.filter_documents(extension_i=extension_i):
        result.append(f"- {doc.file_name}")
        
    logger.info(f"Found {len(result)} documents with extension: '{extension_i}'")
        
    if not result:
        return f"No documents found with extension: '{extension_i}'"
        
    return f"Documents with extension '{extension_i}':\n" + "\n".join(result)
