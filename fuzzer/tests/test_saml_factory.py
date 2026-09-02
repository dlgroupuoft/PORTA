"""Tests for SAML factory."""

import base64

from lxml import etree

from src.utils.saml_factory import SAMLFactory, SAML_NS, SAMLP_NS, DS_NS


def _decode_response(b64_xml: str) -> etree._Element:
    xml_bytes = base64.b64decode(b64_xml)
    return etree.fromstring(xml_bytes)


class TestSAMLFactory:
    def test_create_valid_response(self):
        factory = SAMLFactory()
        b64 = factory.create_response(
            issuer="http://idp.example.com",
            destination="http://sp.example.com/acs",
            name_id="alice@example.com",
            attributes={"role": "admin", "group": "developers"},
        )
        assert isinstance(b64, str)
        assert len(b64) > 100

        root = _decode_response(b64)
        assert root.tag == f"{{{SAMLP_NS}}}Response"

        # Check assertion exists
        assertions = root.findall(f".//{{{SAML_NS}}}Assertion")
        assert len(assertions) >= 1

        # Check signature exists
        sigs = root.findall(f".//{{{DS_NS}}}Signature")
        assert len(sigs) >= 1

    def test_create_response_with_name_id(self):
        factory = SAMLFactory()
        b64 = factory.create_response(
            issuer="http://idp.test",
            destination="http://sp.test/acs",
            name_id="bob@test.com",
            attributes={},
        )
        root = _decode_response(b64)
        nids = root.findall(f".//{{{SAML_NS}}}NameID")
        assert any(nid.text == "bob@test.com" for nid in nids)

    def test_xsw_variants_well_formed(self):
        """Each XSW variant (1-8) must produce well-formed XML."""
        factory = SAMLFactory()
        for variant in range(1, 9):
            b64 = factory.create_xsw_response(
                variant=variant,
                legitimate_name_id="legit@example.com",
                malicious_name_id="evil@attacker.com",
                issuer="http://idp.example.com",
                destination="http://sp.example.com/acs",
                attributes={"role": "user"},
            )
            root = _decode_response(b64)
            assert root.tag == f"{{{SAMLP_NS}}}Response", f"XSW{variant} not a Response"

            # Must contain at least one signature
            sigs = root.findall(f".//{{{DS_NS}}}Signature")
            assert len(sigs) >= 1, f"XSW{variant} has no signature"

            # Must contain the malicious NameID somewhere
            nids = root.findall(f".//{{{SAML_NS}}}NameID")
            nid_texts = [n.text for n in nids]
            assert "evil@attacker.com" in nid_texts, \
                f"XSW{variant} missing evil NameID, found {nid_texts}"

    def test_expired_response(self):
        factory = SAMLFactory()
        b64 = factory.create_expired_response(
            issuer="http://idp.test",
            destination="http://sp.test/acs",
            name_id="user@test.com",
            attributes={},
            expired_minutes_ago=60,
        )
        root = _decode_response(b64)
        conditions = root.findall(f".//{{{SAML_NS}}}Conditions")
        assert len(conditions) >= 1
        not_on_or_after = conditions[0].get("NotOnOrAfter")
        assert not_on_or_after is not None

    def test_unsigned_assertion_in_signed_response(self):
        factory = SAMLFactory()
        b64 = factory.create_unsigned_assertion_in_signed_response(
            issuer="http://idp.test",
            destination="http://sp.test/acs",
            malicious_name_id="evil@test.com",
            attributes={"role": "admin"},
        )
        root = _decode_response(b64)

        # Response should have a signature
        resp_sigs = root.findall(f"./{{{DS_NS}}}Signature")
        assert len(resp_sigs) >= 1

        # Assertion itself should NOT have a direct signature child
        assertion = root.find(f".//{{{SAML_NS}}}Assertion")
        assert assertion is not None
        assertion_sigs = assertion.findall(f"./{{{DS_NS}}}Signature")
        assert len(assertion_sigs) == 0, "Assertion should not be individually signed"

    def test_idp_metadata(self):
        factory = SAMLFactory()
        xml = factory.get_idp_metadata(
            entity_id="http://idp.test",
            sso_url="http://idp.test/sso",
        )
        assert "EntityDescriptor" in xml
        assert "X509Certificate" in xml

    def test_generate_self_signed_cert(self):
        key, cert = SAMLFactory.generate_self_signed_cert("Test CA")
        assert key is not None
        assert cert is not None
