from fastmcp.tools import tool
import datetime
from docs_handlers.pdf_handler import PDFHandler

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
    pdf_handler = PDFHandler('/Users/calogeroforte/UPF_Handout.pdf')
    text = pdf_handler.get_section_text_by_heading(section_title_i)
    return text





