#!/usr/bin/env python3
"""Controllable mock Identity Provider for VALENCE fuzzing.

Serves OIDC discovery, JWKS, SAML metadata, and simple OAuth2 endpoints.
The signing key, claims, and SAML certificate can be changed at runtime
via admin HTTP endpoints.
"""

import base64
import hashlib
import json
import secrets
import time
import uuid
from datetime import datetime, timedelta, timezone
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse

# --- Crypto bootstrap (uses stdlib + PyJWT + cryptography) ---
import jwt as pyjwt
import signxml
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509 import (
    CertificateBuilder, Name, NameAttribute, random_serial_number,
)
from cryptography.x509.oid import NameOID

HOST = "0.0.0.0"
PORT = 9090
ISSUER = f"http://mock-idp:{PORT}"


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _generate_rsa():
    key = rsa.generate_private_key(65537, 2048)
    return key


def _key_to_jwk(pub):
    nums = pub.public_numbers()
    n_bytes = nums.n.to_bytes((nums.n.bit_length() + 7) // 8, "big")
    e_bytes = nums.e.to_bytes((nums.e.bit_length() + 7) // 8, "big")
    kid = _b64url(hashlib.sha256(n_bytes[:32]).digest())[:16]
    return {"kty": "RSA", "use": "sig", "alg": "RS256",
            "kid": kid, "n": _b64url(n_bytes), "e": _b64url(e_bytes)}


def _self_signed_cert(key, cn="Mock IdP"):
    now = datetime.now(timezone.utc)
    subject = issuer = Name([NameAttribute(NameOID.COMMON_NAME, cn)])
    cert = (CertificateBuilder()
            .subject_name(subject).issuer_name(issuer)
            .public_key(key.public_key())
            .serial_number(random_serial_number())
            .not_valid_before(now)
            .not_valid_after(now + timedelta(days=365))
            .sign(key, hashes.SHA256()))
    return cert


# --- Global mutable state ---
_signing_key = _generate_rsa()
_saml_key = _generate_rsa()
_saml_cert = _self_signed_cert(_saml_key)
_default_claims = {"sub": "testuser", "email": "test@valence.local",
                   "name": "Test User", "groups": ["developers"],
                   "email_verified": False}
_auth_codes: dict[str, dict] = {}
_omit_nonce = True  # When True, id_tokens omit the nonce claim


class MockIdPHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/health":
            self._json(200, {"status": "ok"})
        elif path == "/.well-known/openid-configuration":
            self._oidc_discovery()
        elif path == "/keys":
            self._jwks()
        elif path == "/saml/metadata":
            self._saml_metadata()
        elif path == "/saml/key":
            self._saml_private_key()
        elif path == "/saml/sso":
            self._saml_sso()
        elif path == "/authorize":
            self._authorize()
        elif path == "/userinfo":
            self._userinfo()
        else:
            self._json(404, {"error": "not found"})

    def do_POST(self):
        path = urlparse(self.path).path
        body = self._read_body()

        if path == "/token":
            self._token(body)
        elif path == "/admin/set-signing-key":
            self._admin_set_signing_key()
        elif path == "/admin/set-claims":
            self._admin_set_claims(body)
        elif path == "/admin/set-saml-cert":
            self._admin_set_saml_cert()
        elif path == "/admin/mint-jwt":
            self._admin_mint_jwt(body)
        elif path == "/admin/set-nonce-mode":
            self._admin_set_nonce_mode(body)
        else:
            self._json(404, {"error": "not found"})

    # --- OIDC ---

    def _oidc_discovery(self):
        self._json(200, {
            "issuer": ISSUER,
            "authorization_endpoint": f"{ISSUER}/authorize",
            "token_endpoint": f"{ISSUER}/token",
            "jwks_uri": f"{ISSUER}/keys",
            "userinfo_endpoint": f"{ISSUER}/userinfo",
            "response_types_supported": ["code"],
            "subject_types_supported": ["public"],
            "id_token_signing_alg_values_supported": ["RS256"],
        })

    def _jwks(self):
        jwk = _key_to_jwk(_signing_key.public_key())
        self._json(200, {"keys": [jwk]})

    def _get_kid(self):
        """Return the kid from the current JWKS."""
        jwk = _key_to_jwk(_signing_key.public_key())
        return jwk.get("kid", "default-kid")

    def _userinfo(self):
        """Minimal userinfo endpoint for OIDC source callback."""
        self._json(200, dict(_default_claims))

    def _authorize(self):
        qs = parse_qs(urlparse(self.path).query)
        redirect_uri = qs.get("redirect_uri", [""])[0]
        state = qs.get("state", [""])[0]
        code = secrets.token_urlsafe(32)
        _auth_codes[code] = {
            "redirect_uri": redirect_uri,
            "client_id": qs.get("client_id", [""])[0],
            "nonce": qs.get("nonce", [""])[0],
        }
        location = f"{redirect_uri}?code={code}&state={state}"
        self.send_response(302)
        self.send_header("Location", location)
        self.end_headers()

    def _token(self, body: dict):
        code = body.get("code", [""])[0] if isinstance(body.get("code"), list) else body.get("code", "")
        code_info = _auth_codes.pop(code, None)
        now = int(time.time())
        claims = dict(_default_claims)
        # Use client_id from the original authorization request (stored with code)
        _cid = body.get("client_id", [""])[0] if isinstance(body.get("client_id"), list) else body.get("client_id", "")
        if not _cid and code_info:
            _cid = code_info.get("client_id", "")
        if not _cid:
            # Try HTTP Basic auth header
            auth_header = self.headers.get("Authorization", "")
            if auth_header.startswith("Basic "):
                import base64 as _b64
                _cid = _b64.b64decode(auth_header[6:]).decode().split(":")[0]
        # Set aud to the client_id from the ORIGINAL auth request
        _aud = code_info.get("client_id", _cid) if code_info else _cid
        claims.update({"iss": ISSUER, "aud": _aud or "test",
                       "iat": now, "exp": now + 3600})
        if not _omit_nonce and code_info and code_info.get("nonce"):
            claims["nonce"] = code_info["nonce"]
        _kid = self._get_kid()
        id_token = pyjwt.encode(claims, _signing_key, algorithm="RS256",
                                headers={"kid": _kid})
        self._json(200, {
            "access_token": secrets.token_urlsafe(32),
            "token_type": "Bearer",
            "expires_in": 3600,
            "id_token": id_token,
        })

    # --- SAML ---

    def _saml_metadata(self):
        cert_pem = _saml_cert.public_bytes(serialization.Encoding.PEM).decode()
        cert_b64 = "".join(cert_pem.strip().split("\n")[1:-1])
        xml = f"""<?xml version="1.0"?>
<EntityDescriptor xmlns="urn:oasis:names:tc:SAML:2.0:metadata" entityID="{ISSUER}">
  <IDPSSODescriptor protocolSupportEnumeration="urn:oasis:names:tc:SAML:2.0:protocol">
    <KeyDescriptor use="signing">
      <ds:KeyInfo xmlns:ds="http://www.w3.org/2000/09/xmldsig#">
        <ds:X509Data><ds:X509Certificate>{cert_b64}</ds:X509Certificate></ds:X509Data>
      </ds:KeyInfo>
    </KeyDescriptor>
    <SingleSignOnService Binding="urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST"
                         Location="{ISSUER}/saml/sso"/>
  </IDPSSODescriptor>
</EntityDescriptor>"""
        self.send_response(200)
        self.send_header("Content-Type", "application/xml")
        self.end_headers()
        self.wfile.write(xml.encode())

    def _saml_sso(self):
        """Handle SAML SSO request (SP-initiated flow).

        Parses the SAMLRequest, builds a signed SAMLResponse using current
        claims and SAML key, then returns an HTML auto-submit form that
        POSTs the SAMLResponse to the SP's ACS URL.
        """
        import zlib
        from xml.etree import ElementTree as ET

        qs = parse_qs(urlparse(self.path).query)
        saml_request_b64 = qs.get("SAMLRequest", [""])[0]
        relay_state = qs.get("RelayState", [""])[0]

        # Decode and parse SAMLRequest
        acs_url = ""
        request_id = ""
        try:
            raw = base64.b64decode(saml_request_b64)
            try:
                xml_bytes = zlib.decompress(raw, -15)
            except zlib.error:
                xml_bytes = raw
            root = ET.fromstring(xml_bytes)
            acs_url = root.get("AssertionConsumerServiceURL", "")
            request_id = root.get("ID", "")
        except Exception:
            pass

        if not acs_url:
            self._json(400, {"error": "cannot parse SAMLRequest or missing ACS URL"})
            return

        # Build SAMLResponse with current claims
        now = datetime.now(timezone.utc)
        not_after = now + timedelta(minutes=5)
        assertion_id = f"_assertion_{uuid.uuid4().hex[:16]}"
        response_id = f"_response_{uuid.uuid4().hex[:16]}"

        claims = dict(_default_claims)
        name_id = claims.get("email", claims.get("sub", "testuser"))
        email = claims.get("email", "test@valence.local")
        name = claims.get("name", "Test User")
        sub = claims.get("sub", "testuser")
        email_verified = str(claims.get("email_verified", "false")).lower()

        # Build the SAML Response XML
        from lxml import etree
        from signxml import XMLSigner

        # SP entity ID derived from the ACS URL pattern
        connector_id = acs_url.rsplit("/", 1)[-1]
        sp_entity_id = f"http://localhost:3001/enterprise-sso/{connector_id}"
        ts = now.strftime("%Y-%m-%dT%H:%M:%SZ")
        ts_after = not_after.strftime("%Y-%m-%dT%H:%M:%SZ")

        ns_ds = "http://www.w3.org/2000/09/xmldsig#"
        response_xml = f"""<samlp:Response xmlns:samlp="urn:oasis:names:tc:SAML:2.0:protocol"
            xmlns:saml="urn:oasis:names:tc:SAML:2.0:assertion"
            ID="{response_id}" Version="2.0" IssueInstant="{ts}"
            Destination="{acs_url}"{f' InResponseTo="{request_id}"' if request_id else ''}>
          <saml:Issuer>{ISSUER}</saml:Issuer>
          <samlp:Status><samlp:StatusCode Value="urn:oasis:names:tc:SAML:2.0:status:Success"/></samlp:Status>
          <saml:Assertion ID="{assertion_id}" IssueInstant="{ts}" Version="2.0">
            <saml:Issuer>{ISSUER}</saml:Issuer>
            <ds:Signature xmlns:ds="{ns_ds}" Id="placeholder"/>
            <saml:Subject>
              <saml:NameID Format="urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress">{name_id}</saml:NameID>
              <saml:SubjectConfirmation Method="urn:oasis:names:tc:SAML:2.0:cm:bearer">
                <saml:SubjectConfirmationData{f' InResponseTo="{request_id}"' if request_id else ''}
                  NotOnOrAfter="{ts_after}" Recipient="{acs_url}"/>
              </saml:SubjectConfirmation>
            </saml:Subject>
            <saml:Conditions NotBefore="{ts}" NotOnOrAfter="{ts_after}">
              <saml:AudienceRestriction>
                <saml:Audience>{sp_entity_id}</saml:Audience>
              </saml:AudienceRestriction>
            </saml:Conditions>
            <saml:AuthnStatement AuthnInstant="{ts}">
              <saml:AuthnContext>
                <saml:AuthnContextClassRef>urn:oasis:names:tc:SAML:2.0:ac:classes:PasswordProtectedTransport</saml:AuthnContextClassRef>
              </saml:AuthnContext>
            </saml:AuthnStatement>
            <saml:AttributeStatement>
              <saml:Attribute Name="email"><saml:AttributeValue>{email}</saml:AttributeValue></saml:Attribute>
              <saml:Attribute Name="name"><saml:AttributeValue>{name}</saml:AttributeValue></saml:Attribute>
              <saml:Attribute Name="sub"><saml:AttributeValue>{sub}</saml:AttributeValue></saml:Attribute>
              <saml:Attribute Name="email_verified"><saml:AttributeValue>{email_verified}</saml:AttributeValue></saml:Attribute>
            </saml:AttributeStatement>
          </saml:Assertion>
        </samlp:Response>"""

        # Sign the assertion with signxml (proper XML-DSIG)
        root = etree.fromstring(response_xml.encode())
        assertion_el = root.find("{urn:oasis:names:tc:SAML:2.0:assertion}Assertion")

        key_pem = _saml_key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption(),
        )
        cert_pem = _saml_cert.public_bytes(serialization.Encoding.PEM)

        signer = XMLSigner(
            method=signxml.methods.enveloped,
            signature_algorithm="rsa-sha256",
            digest_algorithm="sha256",
            c14n_algorithm="http://www.w3.org/2001/10/xml-exc-c14n#",
        )
        signed_assertion = signer.sign(
            assertion_el,
            key=key_pem,
            cert=[cert_pem],
            reference_uri=f"#{assertion_id}",
        )

        root.remove(assertion_el)
        root.append(signed_assertion)

        response_xml = etree.tostring(root, xml_declaration=False).decode()

        saml_response_b64 = base64.b64encode(response_xml.encode()).decode()

        # Return HTML auto-submit form (POST binding)
        html = (
            f'<html><body onload="document.forms[0].submit()">'
            f'<form method="POST" action="{acs_url}">'
            f'<input type="hidden" name="SAMLResponse" value="{saml_response_b64}"/>'
            f'<input type="hidden" name="RelayState" value="{relay_state}"/>'
            f'</form></body></html>'
        )

        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        self.wfile.write(html.encode())

    def _saml_private_key(self):
        """Expose the SAML signing private key (PEM) for XSW fuzzing.

        This allows the fuzzer to build XSW payloads where the legitimate
        assertion is signed with the *trusted* IdP key while the malicious
        assertion is unsigned — testing whether the SP correctly validates
        which assertion carries a valid signature.
        """
        key_pem = _saml_key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption(),
        ).decode()
        cert_pem = _saml_cert.public_bytes(serialization.Encoding.PEM).decode()
        self._json(200, {"key_pem": key_pem, "cert_pem": cert_pem})

    # --- Admin ---

    def _admin_set_signing_key(self):
        global _signing_key
        _signing_key = _generate_rsa()
        self._json(200, {"status": "new RSA key generated",
                         "kid": _key_to_jwk(_signing_key.public_key())["kid"]})

    def _admin_set_claims(self, body: dict):
        global _default_claims
        # body comes from form parse — flatten
        new_claims = {}
        for k, v in body.items():
            val = v[0] if isinstance(v, list) and len(v) == 1 else v
            # Normalize boolean-like values for OIDC compliance
            if k == "email_verified":
                val = str(val).lower() in ("true", "1", "yes")
            new_claims[k] = val
        _default_claims.update(new_claims)
        self._json(200, {"status": "claims updated", "claims": _default_claims})

    def _admin_set_saml_cert(self):
        global _saml_key, _saml_cert
        _saml_key = _generate_rsa()
        _saml_cert = _self_signed_cert(_saml_key)
        self._json(200, {"status": "new SAML cert generated"})

    def _admin_set_nonce_mode(self, body):
        global _omit_nonce
        val = body.get("omit_nonce", body.get("omit", ["true"]))
        if isinstance(val, list):
            val = val[0]
        _omit_nonce = str(val).lower() in ("true", "1", "yes")
        self._json(200, {"omit_nonce": _omit_nonce})

    def _admin_mint_jwt(self, body):
        """Mint a custom JWT with caller-specified claims.

        Accepts JSON body with arbitrary claims.  The JWT is signed with
        the current OIDC signing key.  If ``exp`` or ``iat`` are omitted
        from the request, they are NOT added — this enables testing
        missing-claim scenarios.
        """
        claims = {}
        if isinstance(body, dict):
            for k, v in body.items():
                claims[k] = v[0] if isinstance(v, list) and len(v) == 1 else v
        claims.setdefault("iss", ISSUER)
        claims.setdefault("sub", _default_claims.get("sub", "testuser"))
        jwk = _key_to_jwk(_signing_key.public_key())
        token = pyjwt.encode(claims, _signing_key, algorithm="RS256",
                             headers={"kid": jwk["kid"]})
        self._json(200, {"token": token, "kid": jwk["kid"], "claims": claims})

    # --- Helpers ---

    def _read_body(self) -> dict:
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length) if length else b""
        ct = self.headers.get("Content-Type", "")
        if "json" in ct:
            return json.loads(raw) if raw else {}
        return parse_qs(raw.decode())

    def _json(self, code, data):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def log_message(self, fmt, *args):
        pass  # suppress default logging


if __name__ == "__main__":
    server = HTTPServer((HOST, PORT), MockIdPHandler)
    print(f"Mock IdP listening on {HOST}:{PORT}")
    server.serve_forever()
