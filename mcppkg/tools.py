from fastmcp.tools import tool
import datetime
import os
from docs_handlers.pdf_document import PDFDocument

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
    name="get_pdf_content",
    description="Get a section text from a PDF",
    annotations={"readOnlyHint": True}
)
async def get_pdf_text(section_title_i) -> str:
    pdf = PDFDocument('/Users/calogeroforte/UPF_Handout.pdf')
    text = pdf.get_section_text_by_heading(section_title_i)
    return text

@tool(
    name="list_local_files",
    description="List all files in the directory specified by LOCAL_PATHS in .env.",
)
async def list_local_files() -> list[str]:
    """List all files in the directory specified by LOCAL_PATHS in .env.
    
    Returns:
        A list of strings representing the names of the files in the directory.
    """
    local_path = os.getenv("LOCAL_PATHS", "~/")
    local_path = os.path.expanduser(local_path)
    
    if not os.path.isdir(local_path):
        return [f"Error: {local_path} is not a valid directory."]
        
    try:
        files = []
        for file in os.listdir(local_path):
            if os.path.isfile(os.path.join(local_path, file)):
                files.append(file)
        return files
    except Exception as e:
        return [f"Error reading directory {local_path}: {str(e)}"]





