"""OAuth2 / OIDC flow helper for fuzzing."""

from __future__ import annotations

import hashlib
import secrets
from urllib.parse import parse_qs, urlencode, urlparse

import requests

from src.utils.crypto import base64url_encode


class OAuthFlowHelper:
    """Helper for manipulating OAuth2 authorization code flows."""

    def __init__(self, session: requests.Session | None = None):
        self.session = session or requests.Session()

    def start_authorization(
        self,
        auth_url: str,
        client_id: str,
        redirect_uri: str,
        scope: str = "openid",
        state: str | None = None,
        nonce: str | None = None,
        code_challenge: str | None = None,
        code_challenge_method: str | None = None,
        extra_params: dict | None = None,
    ) -> tuple[str, dict]:
        """Send authorization request.

        Returns (redirect_location, captured_params).
        """
        params: dict = {
            "response_type": "code",
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "scope": scope,
            "state": state or self.generate_state(),
        }
        if nonce:
            params["nonce"] = nonce
        if code_challenge:
            params["code_challenge"] = code_challenge
            params["code_challenge_method"] = code_challenge_method or "S256"
        if extra_params:
            params.update(extra_params)

        r = self.session.get(
            auth_url,
            params=params,
            allow_redirects=False,
            timeout=10,
        )

        # Follow redirects but stop when we hit the redirect_uri
        max_redirects = 10
        for _ in range(max_redirects):
            if r.status_code not in (301, 302, 303, 307, 308):
                break
            location = r.headers.get("Location", "")
            if location.startswith(redirect_uri):
                return location, self.capture_redirect_url(location)
            r = self.session.get(location, allow_redirects=False, timeout=10)

        # If we ended on the redirect_uri, parse it
        location = r.headers.get("Location", r.url or "")
        return location, self.capture_redirect_url(location)

    def exchange_code(
        self,
        token_url: str,
        code: str,
        redirect_uri: str,
        client_id: str,
        client_secret: str | None = None,
        code_verifier: str | None = None,
        extra_params: dict | None = None,
    ) -> dict:
        """Exchange authorization code for tokens."""
        data: dict = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_uri,
            "client_id": client_id,
        }
        if client_secret:
            data["client_secret"] = client_secret
        if code_verifier:
            data["code_verifier"] = code_verifier
        if extra_params:
            data.update(extra_params)

        r = self.session.post(token_url, data=data, timeout=10)
        return r.json()

    def capture_redirect(self, response: requests.Response) -> dict:
        """Extract query parameters from a redirect response."""
        location = response.headers.get("Location", "")
        return self.capture_redirect_url(location)

    @staticmethod
    def capture_redirect_url(url: str) -> dict:
        """Parse code, state, error from a redirect URL."""
        parsed = urlparse(url)
        params = parse_qs(parsed.query)
        # Flatten single-value lists
        return {k: v[0] if len(v) == 1 else v for k, v in params.items()}

    @staticmethod
    def generate_pkce() -> tuple[str, str]:
        """Generate (code_verifier, code_challenge) for PKCE S256."""
        verifier = secrets.token_urlsafe(64)[:128]
        digest = hashlib.sha256(verifier.encode("ascii")).digest()
        challenge = base64url_encode(digest)
        return verifier, challenge

    @staticmethod
    def generate_state() -> str:
        return secrets.token_urlsafe(32)

    @staticmethod
    def generate_nonce() -> str:
        return secrets.token_urlsafe(32)
