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
- Module Name: authentication.py
- Revision: 1.0
- Author: Calogero Forte
- Affiliation: University of Palermo
- Development Date: May 2026
"""
"""
Courtesy Statement
==================

The code used in this module is courtesy of 
Ing. Andrea Citrolo - The Software Academy - andrea.citrolo@thesoftwareacademy.it
Reference project:
https://github.com/The-Software-Academy/mcp-example/tree/main
"""

import json
import logging
import os
import secrets
import time
import urllib.parse
from pathlib import Path
from string import Template
from typing import Any
from fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import JSONResponse, RedirectResponse, Response

logger = logging.getLogger(__name__)

if os.getenv("MCP_AUTH_TOKEN"):
    from mcp.server.auth.provider import (
        AccessToken,
        AuthorizationCode,
        AuthorizationParams,
        RefreshToken,
        construct_redirect_uri,
    )
    from mcp.server.auth.settings import ClientRegistrationOptions, RevocationOptions
    from mcp.shared.auth import OAuthClientInformationFull, OAuthToken
    from fastmcp.server.auth.providers.in_memory import InMemoryOAuthProvider

    class ConsentOAuthProvider(InMemoryOAuthProvider):
        """
        InMemoryOAuthProvider that redirects to a browser consent page before issuing codes.
        """

        def __init__(self, base_url: str) -> None:
            super().__init__(
                base_url=base_url,
                client_registration_options=ClientRegistrationOptions(
                    enabled=True, valid_scopes=["mcp:full"], default_scopes=["mcp:full"],
                ),
                revocation_options=RevocationOptions(enabled=True),
                required_scopes=["mcp:full"],
            )
            self._base_url = base_url.rstrip("/")
            self.pending: dict[str, tuple[OAuthClientInformationFull, AuthorizationParams]] = {}

        async def authorize(self, client: OAuthClientInformationFull, params: AuthorizationParams) -> str:
            key = secrets.token_urlsafe(16)
            self.pending[key] = (client, params)
            return f"{self._base_url}/oauth/consent?key={urllib.parse.quote(key)}"

        def approve(self, key: str) -> str | None:
            item = self.pending.pop(key, None)
            if item is None:
                return None
            client, params = item
            scopes = params.scopes or []
            if client.scope:
                allowed = set(client.scope.split())
                scopes = [s for s in scopes if s in allowed]
            code_value = f"code_{secrets.token_hex(16)}"
            self.auth_codes[code_value] = AuthorizationCode(
                code=code_value,
                client_id=client.client_id or "",
                redirect_uri=params.redirect_uri,
                redirect_uri_provided_explicitly=params.redirect_uri_provided_explicitly,
                scopes=scopes,
                expires_at=time.time() + 300,
                code_challenge=params.code_challenge,
            )
            return construct_redirect_uri(str(params.redirect_uri), code=code_value, state=params.state)

        def deny(self, key: str) -> str | None:
            item = self.pending.pop(key, None)
            if item is None:
                return None
            _, params = item
            return construct_redirect_uri(
                str(params.redirect_uri),
                error="access_denied",
                error_description="User denied access",
                state=params.state,
            )

    class PersistentOAuthProvider(ConsentOAuthProvider):
        """
        ConsentOAuthProvider that persists clients and tokens to a JSON file.
        """

        def __init__(self, base_url: str, state_path: Path) -> None:
            super().__init__(base_url=base_url)
            self._state_path = state_path
            self._load()

        def _load(self) -> None:
            if not self._state_path.exists():
                return
            try:
                data = json.loads(self._state_path.read_text())
                now = time.time()
                for cdata in data.get("clients", {}).values():
                    c = OAuthClientInformationFull.model_validate(cdata)
                    if c.client_id:
                        self.clients[c.client_id] = c
                for tdata in data.get("refresh_tokens", {}).values():
                    t = RefreshToken.model_validate(tdata)
                    self.refresh_tokens[t.token] = t
                for tdata in data.get("access_tokens", {}).values():
                    t = AccessToken.model_validate(tdata)
                    if t.expires_at is None or t.expires_at > now:
                        self.access_tokens[t.token] = t
                self._access_to_refresh_map.update(data.get("access_to_refresh", {}))
                self._refresh_to_access_map.update(data.get("refresh_to_access", {}))
                logger.info(
                    "OAuth state loaded from %s: %d client(s), %d access token(s), %d refresh token(s)",
                    self._state_path, len(self.clients), len(self.access_tokens), len(self.refresh_tokens),
                )
            except Exception as exc:
                logger.warning("OAuth state file %s unreadable (%s) — deleting and starting fresh", self._state_path, exc)
                try:
                    self._state_path.unlink()
                except OSError:
                    pass

        def _save(self) -> None:
            try:
                now = time.time()
                self._state_path.parent.mkdir(parents=True, exist_ok=True)
                data = {
                    "version": 1,
                    "clients": {cid: c.model_dump(mode="json") for cid, c in self.clients.items()},
                    "refresh_tokens": {tok: t.model_dump(mode="json") for tok, t in self.refresh_tokens.items()},
                    "access_tokens": {
                        tok: t.model_dump(mode="json")
                        for tok, t in self.access_tokens.items()
                        if t.expires_at is None or t.expires_at > now
                    },
                    "access_to_refresh": dict(self._access_to_refresh_map),
                    "refresh_to_access": dict(self._refresh_to_access_map),
                }
                self._state_path.write_text(json.dumps(data, indent=2))
            except Exception as exc:
                logger.warning("Failed to save OAuth state: %s", exc)

        async def register_client(self, client_info: OAuthClientInformationFull) -> None:
            await super().register_client(client_info)
            self._save()

        async def exchange_authorization_code(self, client: OAuthClientInformationFull, authorization_code: AuthorizationCode) -> OAuthToken:
            token = await super().exchange_authorization_code(client, authorization_code)
            self._save()
            return token

        async def exchange_refresh_token(self, client: OAuthClientInformationFull, refresh_token: RefreshToken, scopes: list[str]) -> OAuthToken:
            token = await super().exchange_refresh_token(client, refresh_token, scopes)
            self._save()
            return token

        async def revoke_token(self, token: AccessToken | RefreshToken) -> None:
            await super().revoke_token(token)
            self._save()


class MCPAuthenticator:
    """
    Handles MCP authentication, including OAuth provider setup and web page rendering for consent.
    """

    def __init__(self) -> None:
        self.enabled = bool(os.getenv("MCP_AUTH_TOKEN"))
        self.provider: Any = None

        self._TEMPLATES = Path(__file__).parent / "templates"
        self._CONSENT_HTML = (self._TEMPLATES / "consent.html").read_text() if (self._TEMPLATES / "consent.html").exists() else "<html><body>Consent Template Missing</body></html>"
        self._CONSENT_EXPIRED_HTML = (self._TEMPLATES / "consent_expired.html").read_text() if (self._TEMPLATES / "consent_expired.html").exists() else "<html><body>Consent Expired Template Missing</body></html>"

        if self.enabled:
            _OAUTH_STATE_PATH = Path(os.getenv("MCP_OAUTH_STATE_PATH") or (Path(__file__).parent.parent / "credentials" / "oauth_state.json"))
            self.provider = PersistentOAuthProvider(
                base_url=f"http://localhost:{int(os.getenv('MCP_PORT', '8001'))}", 
                state_path=_OAUTH_STATE_PATH
            )

    def _render_consent(self, key: str, client_name: str, scopes: list[str], error: str = "") -> str:
        """
        Render the consent HTML with the given parameters.

        key: (str) The consent key.
        client_name: (str) The client name.
        scopes: (list[str]) The requested scopes.
        error: (str) Any error message to display.

        Return
        -------------------
        (str) The rendered HTML string.
        """
        scope_items = "".join(f"<li>{s}</li>" for s in scopes)
        error_html = f'<p class="error">{error}</p>' if error else ""
        return Template(self._CONSENT_HTML).substitute(key=key, client_name=client_name, scope_items=scope_items, error_html=error_html)

    def register_routes(self, mcp: FastMCP) -> None:
        """
        Registers authentication related custom routes on the FastMCP instance.

        mcp: (FastMCP) The FastMCP instance.

        Return
        -------------------
        (None) No return value.
        """
        @mcp.custom_route("/auth-status", methods=["GET"])
        async def auth_status(request: Request) -> JSONResponse:
            """
            Get the authentication status.

            request: (Request) The HTTP request object.

            Return
            -------------------
            (JSONResponse) The JSON response containing the auth status.
            """
            return JSONResponse({
                "mcp_auth_enabled": self.enabled,
            })

        @mcp.custom_route("/oauth/consent", methods=["GET"])
        async def oauth_consent_page(request: Request) -> Response:
            """
            Render the OAuth consent page for MCP client authorisation.

            request: (Request) The HTTP request object.

            Return
            -------------------
            (Response) The HTTP response containing the consent page HTML or an error.
            """
            if self.provider is None:
                return Response("MCP auth is not enabled.", status_code=404)
            key = request.query_params.get("key", "")
            item = self.provider.pending.get(key)
            if item is None:
                return Response(self._CONSENT_EXPIRED_HTML, media_type="text/html", status_code=400)
            client, params = item
            client_name = client.client_name or client.client_id or "Unknown client"
            scopes = params.scopes or ["mcp:full"]
            return Response(self._render_consent(key, client_name, scopes), media_type="text/html")

        @mcp.custom_route("/oauth/consent", methods=["POST"])
        async def oauth_consent_action(request: Request) -> Response:
            """
            Handle Approve or Deny from the consent page.

            request: (Request) The HTTP request object containing form data.

            Return
            -------------------
            (Response) A redirect response to complete the flow or an error response.
            """
            if self.provider is None:
                return Response("MCP auth is not enabled.", status_code=404)
            form = await request.form()
            key = str(form.get("key", ""))
            action = str(form.get("action", "deny"))

            if action == "deny":
                redirect_url = self.provider.deny(key)
                if redirect_url is None:
                    return Response(self._CONSENT_EXPIRED_HTML, media_type="text/html", status_code=400)
                return RedirectResponse(redirect_url, status_code=302)

            # Validate the server password before approving.
            entered = str(form.get("token", ""))
            expected = os.getenv("MCP_AUTH_TOKEN", "")
            if entered != expected:
                item = self.provider.pending.get(key)
                if item is None:
                    return Response(self._CONSENT_EXPIRED_HTML, media_type="text/html", status_code=400)
                client, params = item
                client_name = client.client_name or client.client_id or "Unknown client"
                scopes = params.scopes or ["mcp:full"]
                html = self._render_consent(key, client_name, scopes, error="Incorrect password. Try again.")
                return Response(html, media_type="text/html", status_code=401)

            redirect_url = self.provider.approve(key)
            if redirect_url is None:
                return Response(self._CONSENT_EXPIRED_HTML, media_type="text/html", status_code=400)
            return RedirectResponse(redirect_url, status_code=302)


class _RegistrationCompatMiddleware:
    """
    Normalize POST /register for clients that omit refresh_token from grant_types.
    """

    def __init__(self, app: Any) -> None:
        self._app = app

    async def __call__(self, scope: Any, receive: Any, send: Any) -> None:
        if scope.get("type") == "http" and scope.get("path") == "/register" and scope.get("method") == "POST":
            chunks: list[bytes] = []
            more = True
            while more:
                msg = await receive()
                chunks.append(msg.get("body", b""))
                more = msg.get("more_body", False)
            body = b"".join(chunks)

            try:
                data = json.loads(body)
                logger.debug("POST /register body: %s", json.dumps(data))
                grant_types: list[str] = data.get("grant_types", ["authorization_code", "refresh_token"])
                if isinstance(grant_types, list) and "authorization_code" in grant_types and "refresh_token" not in grant_types:
                    data["grant_types"] = grant_types + ["refresh_token"]
                    body = json.dumps(data).encode()
                    logger.info("RegistrationCompat: added refresh_token to grant_types for client %r",
                                data.get("client_name", "<unknown>"))
            except (json.JSONDecodeError, TypeError):
                pass

            delivered = False

            async def patched_receive() -> Any:
                nonlocal delivered
                if not delivered:
                    delivered = True
                    return {"type": "http.request", "body": body, "more_body": False}
                return {"type": "http.disconnect"}

            await self._app(scope, patched_receive, send)
        else:
            await self._app(scope, receive, send)
