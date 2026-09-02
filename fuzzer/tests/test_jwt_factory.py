"""Tests for JWT factory."""

import json
import time

import jwt as pyjwt
import pytest

from src.utils.jwt_factory import JWTFactory
from src.utils.crypto import generate_rsa_key_pair


class TestJWTFactory:
    def test_create_and_verify(self):
        factory = JWTFactory()
        token = factory.create_token({"sub": "alice", "iss": "test", "aud": "test"})
        assert isinstance(token, str)
        assert token.count(".") == 2

        # Verify with the factory's own public key
        jwks = factory.get_public_key_jwks()
        from src.utils.crypto import jwks_to_key
        pub = jwks_to_key(jwks)
        claims = pyjwt.decode(token, pub, algorithms=["RS256"], audience="test")
        assert claims["sub"] == "alice"

    def test_create_unsigned_token(self):
        factory = JWTFactory()
        token = factory.create_unsigned_token({"sub": "test", "iss": "none"})
        assert token.endswith(".")
        header, claims = factory.decode_without_verification(token)
        assert header["alg"] == "none"
        assert claims["sub"] == "test"

    def test_resign_with_different_key(self):
        factory = JWTFactory()
        new_key, new_pub = generate_rsa_key_pair()

        original = factory.create_token({"sub": "alice", "iss": "test", "aud": "test"})
        resigned = factory.resign_token(original, new_key)

        # Should be valid with new key
        claims = pyjwt.decode(resigned, new_pub, algorithms=["RS256"], audience="test")
        assert claims["sub"] == "alice"

        # Should be invalid with original key
        with pytest.raises(pyjwt.InvalidSignatureError):
            from src.utils.crypto import jwks_to_key
            orig_pub = jwks_to_key(factory.get_public_key_jwks())
            pyjwt.decode(resigned, orig_pub, algorithms=["RS256"], audience="test")

    def test_tamper_claims(self):
        factory = JWTFactory()
        original = factory.create_token({"sub": "alice", "iss": "test", "aud": "test"})
        tampered = factory.tamper_claims(original, {"sub": "admin", "role": "superuser"})

        header, claims = factory.decode_without_verification(tampered)
        assert claims["sub"] == "admin"
        assert claims["role"] == "superuser"
        assert claims["iss"] == "test"

    def test_decode_without_verification(self):
        factory = JWTFactory()
        token = factory.create_token({"sub": "bob", "iss": "test"})
        header, claims = factory.decode_without_verification(token)
        assert header["alg"] == "RS256"
        assert claims["sub"] == "bob"

    def test_jwks_output(self):
        factory = JWTFactory()
        jwks = factory.get_public_key_jwks()
        assert "keys" in jwks
        assert len(jwks["keys"]) == 1
        key = jwks["keys"][0]
        assert key["kty"] == "RSA"
        assert "n" in key
        assert "e" in key
        assert "kid" in key

    def test_generate_key_pair(self):
        priv, pub = JWTFactory.generate_key_pair()
        assert priv is not None
        assert pub is not None

    def test_token_has_standard_time_claims(self):
        factory = JWTFactory()
        token = factory.create_token({"sub": "test"})
        _, claims = factory.decode_without_verification(token)
        assert "iat" in claims
        assert "exp" in claims
        assert claims["exp"] > claims["iat"]
