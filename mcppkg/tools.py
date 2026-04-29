from fastmcp.tools import tool
import datetime

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

