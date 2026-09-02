"""Shared cryptographic utilities."""

from __future__ import annotations

import base64
import hashlib
from datetime import datetime, timedelta, timezone

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec, rsa
from cryptography.hazmat.primitives.asymmetric.ec import (
    EllipticCurvePrivateKey,
    EllipticCurvePublicKey,
    SECP256R1,
)
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey, RSAPublicKey
from cryptography.x509.oid import NameOID


def generate_rsa_key_pair(
    key_size: int = 2048,
) -> tuple[RSAPrivateKey, RSAPublicKey]:
    private = rsa.generate_private_key(public_exponent=65537, key_size=key_size)
    return private, private.public_key()


def generate_ec_key_pair(
    curve: ec.EllipticCurve | None = None,
) -> tuple[EllipticCurvePrivateKey, EllipticCurvePublicKey]:
    curve = curve or SECP256R1()
    private = ec.generate_private_key(curve)
    return private, private.public_key()


def key_to_jwks(public_key: RSAPublicKey | EllipticCurvePublicKey, kid: str | None = None) -> dict:
    """Convert a public key to a single-key JWKS dict."""
    if isinstance(public_key, RSAPublicKey):
        numbers = public_key.public_numbers()
        n_bytes = numbers.n.to_bytes((numbers.n.bit_length() + 7) // 8, "big")
        e_bytes = numbers.e.to_bytes((numbers.e.bit_length() + 7) // 8, "big")
        jwk: dict = {
            "kty": "RSA",
            "n": base64url_encode(n_bytes),
            "e": base64url_encode(e_bytes),
            "alg": "RS256",
            "use": "sig",
        }
    elif isinstance(public_key, EllipticCurvePublicKey):
        numbers = public_key.public_numbers()
        size = (public_key.key_size + 7) // 8
        x_bytes = numbers.x.to_bytes(size, "big")
        y_bytes = numbers.y.to_bytes(size, "big")
        jwk = {
            "kty": "EC",
            "crv": "P-256",
            "x": base64url_encode(x_bytes),
            "y": base64url_encode(y_bytes),
            "alg": "ES256",
            "use": "sig",
        }
    else:
        raise TypeError(f"Unsupported key type: {type(public_key)}")

    if kid:
        jwk["kid"] = kid
    else:
        # deterministic kid from thumbprint
        jwk["kid"] = _jwk_thumbprint(jwk)
    return {"keys": [jwk]}


def _jwk_thumbprint(jwk: dict) -> str:
    """Compute a JWK thumbprint (RFC 7638) for use as kid."""
    import json as _json

    if jwk["kty"] == "RSA":
        members = {"e": jwk["e"], "kty": jwk["kty"], "n": jwk["n"]}
    else:
        members = {"crv": jwk["crv"], "kty": jwk["kty"], "x": jwk["x"], "y": jwk["y"]}
    canonical = _json.dumps(members, sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha256(canonical.encode()).digest()
    return base64url_encode(digest)


def jwks_to_key(jwks_dict: dict) -> RSAPublicKey | EllipticCurvePublicKey:
    """Decode the first key from a JWKS dict."""
    keys = jwks_dict.get("keys", [jwks_dict])
    k = keys[0]
    if k["kty"] == "RSA":
        n = int.from_bytes(base64url_decode(k["n"]), "big")
        e = int.from_bytes(base64url_decode(k["e"]), "big")
        return rsa.RSAPublicNumbers(e, n).public_key()
    if k["kty"] == "EC":
        x = int.from_bytes(base64url_decode(k["x"]), "big")
        y = int.from_bytes(base64url_decode(k["y"]), "big")
        return ec.EllipticCurvePublicNumbers(x, y, SECP256R1()).public_key()
    raise ValueError(f"Unsupported key type: {k['kty']}")


def generate_self_signed_cert(
    key: RSAPrivateKey | EllipticCurvePrivateKey,
    cn: str = "VALENCE Test",
    validity_days: int = 365,
) -> x509.Certificate:
    subject = issuer = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, cn)])
    now = datetime.now(timezone.utc)
    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now)
        .not_valid_after(now + timedelta(days=validity_days))
        .sign(key, hashes.SHA256())
    )
    return cert


# ---------------------------------------------------------------------------
# Base64url helpers (RFC 7515)
# ---------------------------------------------------------------------------

def base64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def base64url_decode(s: str) -> bytes:
    s += "=" * (-len(s) % 4)
    return base64.urlsafe_b64decode(s)
