"""JWT token factory for fuzzing."""

from __future__ import annotations

import json
import time
from typing import Any

import jwt as pyjwt
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey, RSAPublicKey

from src.utils.crypto import base64url_decode, base64url_encode, generate_rsa_key_pair, key_to_jwks


class JWTFactory:
    """Create, tamper, and re-sign JWTs for identity broker fuzzing."""

    def __init__(self, default_signing_key: RSAPrivateKey | None = None):
        if default_signing_key is None:
            self._private_key, self._public_key = generate_rsa_key_pair()
        else:
            self._private_key = default_signing_key
            self._public_key = default_signing_key.public_key()

    # ------------------------------------------------------------------
    # Token creation
    # ------------------------------------------------------------------

    def create_token(
        self,
        claims: dict[str, Any],
        headers: dict[str, Any] | None = None,
        signing_key: RSAPrivateKey | None = None,
        algorithm: str = "RS256",
    ) -> str:
        key = signing_key or self._private_key
        hdr = dict(headers) if headers else {}
        # Ensure standard time claims
        now = int(time.time())
        claims.setdefault("iat", now)
        claims.setdefault("exp", now + 3600)
        return pyjwt.encode(claims, key, algorithm=algorithm, headers=hdr)

    def create_unsigned_token(self, claims: dict[str, Any]) -> str:
        """Create a JWT with alg=none (for I1 testing)."""
        header = {"alg": "none", "typ": "JWT"}
        h_b64 = base64url_encode(json.dumps(header, separators=(",", ":")).encode())
        now = int(time.time())
        claims.setdefault("iat", now)
        claims.setdefault("exp", now + 3600)
        p_b64 = base64url_encode(json.dumps(claims, separators=(",", ":")).encode())
        return f"{h_b64}.{p_b64}."

    def create_token_raw_claims(
        self,
        claims: dict[str, Any],
        headers: dict[str, Any] | None = None,
        signing_key: RSAPrivateKey | None = None,
    ) -> str:
        """Create a JWT with exact claim types as provided, bypassing
        library type coercion. Use this for type confusion mutations."""
        from cryptography.hazmat.primitives.asymmetric import padding
        from cryptography.hazmat.primitives import hashes

        key = signing_key or self._private_key
        hdr = {"alg": "RS256", "typ": "JWT"}
        if headers:
            hdr.update(headers)
        h_b64 = base64url_encode(json.dumps(hdr, separators=(",", ":")).encode())
        p_b64 = base64url_encode(json.dumps(claims, separators=(",", ":"), default=str).encode())
        signing_input = f"{h_b64}.{p_b64}".encode()
        signature = key.sign(signing_input, padding.PKCS1v15(), hashes.SHA256())
        sig_b64 = base64url_encode(signature)
        return f"{h_b64}.{p_b64}.{sig_b64}"

    # ------------------------------------------------------------------
    # Token manipulation
    # ------------------------------------------------------------------

    def resign_token(
        self,
        token: str,
        new_key: RSAPrivateKey,
        new_algorithm: str | None = None,
    ) -> str:
        header, claims = self.decode_without_verification(token)
        alg = new_algorithm or header.get("alg", "RS256")
        # Remove auto-set fields that PyJWT adds
        header.pop("alg", None)
        header.pop("typ", None)
        return pyjwt.encode(claims, new_key, algorithm=alg, headers=header)

    def tamper_claims(
        self,
        token: str,
        claim_overrides: dict[str, Any],
        signing_key: RSAPrivateKey | None = None,
    ) -> str:
        header, claims = self.decode_without_verification(token)
        claims.update(claim_overrides)
        key = signing_key or self._private_key
        alg = header.get("alg", "RS256")
        header.pop("alg", None)
        header.pop("typ", None)
        return pyjwt.encode(claims, key, algorithm=alg, headers=header)

    # ------------------------------------------------------------------
    # Key export
    # ------------------------------------------------------------------

    def get_public_key_jwks(self) -> dict:
        return key_to_jwks(self._public_key)

    # ------------------------------------------------------------------
    # Decoding
    # ------------------------------------------------------------------

    def decode_without_verification(self, token: str) -> tuple[dict, dict]:
        header = pyjwt.get_unverified_header(token)
        claims = pyjwt.decode(token, options={"verify_signature": False})
        return header, claims

    # ------------------------------------------------------------------
    # Key generation
    # ------------------------------------------------------------------

    @staticmethod
    def generate_key_pair() -> tuple[RSAPrivateKey, RSAPublicKey]:
        return generate_rsa_key_pair()
