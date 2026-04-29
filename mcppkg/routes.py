"""Custom routes for the MCP server."""
from __future__ import annotations

from starlette.requests import Request
from starlette.responses import JSONResponse


async def health(request: Request) -> JSONResponse:
    """
    Health check route.

    request: (Request) The HTTP request object.

    Return
    -------------------
    (JSONResponse) The JSON response with health status.
    """
    return JSONResponse({"status": "ok", "version": "1.0.0"})
