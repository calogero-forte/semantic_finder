import os
import logging
from fastmcp import Context
from docs_handlers.document_handler import DocumentHandler
from docs_handlers.document import Document
from docs_handlers.pdf_document import PDFDocument

logger = logging.getLogger(__name__)

def _sync_documents(doc_handler: DocumentHandler):
    """
    Synchronizes the DocumentHandler with the files currently in the LOCAL_PATHS directory.
    Instantiates specific Document subclasses (like PDFDocument) depending on the extension.
    """
    local_paths = os.getenv("LOCAL_PATHS")
    if not local_paths:
        logger.error("LOCAL_PATHS environment variable is not set.")
        return

    local_paths = os.path.expanduser(local_paths)
    current_files = Document.get_all_documents(local_paths)
    
    doc_handler.clear_documents()
    
    for file_path in current_files:
        ext = file_path.lower().split('.')[-1]
        try:
            if ext == 'pdf':
                doc = PDFDocument(file_path)
                doc_handler.add_document(doc)
            else:
                # Add future document handlers here (e.g., txt, docx) using polymorphism
                logger.debug(f"Document type '{ext}' is not currently supported: {file_path}")
        except Exception as e:
            logger.error(f"Failed to load document {file_path}: {e}")

def get_all_documents(context: Context) -> str:
    """
    Resource that exposes all documents found in the LOCAL_PATHS directory.
    """
    doc_handler = context.request_context.lifespan_context.get("doc_handler")
    if doc_handler is None:
        return "Error: DocumentHandler not found in context."
        
    _sync_documents(doc_handler)
    
    result = []
    for doc in doc_handler:
        result.append(f"- {doc.file_name} (Type: {doc.file_extenstion})")
        
    if not result:
        return "No documents found in the local database."
        
    return "All documents:\n" + "\n".join(result)

def get_documents_by_name(name: str, context: Context) -> str:
    """
    Resource that filters documents by a given name string.
    """
    doc_handler = context.request_context.lifespan_context.get("doc_handler")
    if doc_handler is None:
        return "Error: DocumentHandler not found in context."
        
    _sync_documents(doc_handler)
    
    result = []
    for doc in doc_handler.filter_documents(name_i=name):
        result.append(f"- {doc.file_name} (Type: {doc.file_extenstion})")
        
    if not result:
        return f"No documents found matching name: '{name}'"
        
    return f"Documents matching name '{name}':\n" + "\n".join(result)

def get_documents_by_extension(extension: str, context: Context) -> str:
    """
    Resource that filters documents by a given extension.
    """
    doc_handler = context.request_context.lifespan_context.get("doc_handler")
    if doc_handler is None:
        return "Error: DocumentHandler not found in context."
        
    _sync_documents(doc_handler)
    
    result = []
    for doc in doc_handler.filter_documents(extension_i=extension):
        result.append(f"- {doc.file_name} (Type: {doc.file_extenstion})")
        
    if not result:
        return f"No documents found with extension: '{extension}'"
        
    return f"Documents with extension '{extension}':\n" + "\n".join(result)
