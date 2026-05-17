from __future__ import annotations

"""
License Statement & Module Information
======================================

This code is provided as open-source software and has been developed as part of the 
Master in Applied Artificial Intelligence postgraduate course, for the Python Programming topic.

The purpose of this application is to serve as a Model Context Protocol (MCP) server, 
providing a Large Language Model (LLM) the capability to access and retrieve 
information from local documents to answer related queries.

- Program Name: Semantic Finder
- Module Name: routes.py
- Revision: 1.0
- Author: Calogero Forte
- Affiliation: University of Palermo
- Development Date: May 2026
"""

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
