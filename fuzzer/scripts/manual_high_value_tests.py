"""手写的高价值测试序列 — 不需要 LLM。"""
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.stateful.models import Event, EventSequence, OracleCheck
from src.stateful.sequence_executor import SequenceExecutor
from src.utils.jwt_factory import JWTFactory
from src.utils.crypto import generate_rsa_key_pair
from src.adapters.vault_adapter import VaultAdapter
from src.oracles.i4_principal_binding import I4PrincipalBindingOracle
from src.oracles.i5_authorization_binding import I5AuthorizationBindingOracle
from cryptography.hazmat.primitives import serialization

VAULT_URL = os.getenv("VAULT_URL", "http://localhost:8200")
ADMIN_TOKEN = "root"
MOUNT = "manual-test-jwt"

def setup():
    """Create executor with fresh JWT key pair."""
    import requests
    priv, pub = generate_rsa_key_pair()
    pub_pem = pub.public_bytes(serialization.Encoding.PEM,
                                serialization.PublicFormat.SubjectPublicKeyInfo).decode()
    factory = JWTFactory(default_signing_key=priv)
    adapter = VaultAdapter({"base_url": VAULT_URL, "admin_token": ADMIN_TOKEN,
                           "auth_mount_path": MOUNT, "role_name": "test"})
    oracles = {"I4": I4PrincipalBindingOracle(), "I5": I5AuthorizationBindingOracle()}

    headers = {"X-Vault-Token": ADMIN_TOKEN}
    requests.post(f"{VAULT_URL}/v1/sys/auth/{MOUNT}", headers=headers, json={"type": "jwt"})
    requests.post(f"{VAULT_URL}/v1/auth/{MOUNT}/config", headers=headers,
                 json={"jwt_validation_pubkeys": [pub_pem]})

    return SequenceExecutor(vault_adapter=adapter, jwt_factory=factory,
                           oracles=oracles, admin_token=ADMIN_TOKEN)


def run_sequence(executor, seq):
    print(f"\n{'='*60}")
    print(f"  {seq.sequence_id}: {seq.description}")
    print(f"  Invariant: {seq.primary_invariant}")
    print(f"{'='*60}")
    result = executor.execute(seq)
    print(f"  Status: {result.status}")
    findings = []
    for v in result.verdicts:
        marker = {"VIOLATION": "🔴", "UNEXPECTED": "🟡", "BY_DESIGN": "🟢",
                  "REJECTED": "⬜", "ERROR": "⚠️"}.get(v.verdict_type.value, "?")
        src = "[AUTO]" if "[AutoVerify]" in v.description else "[SYNTACTIC]" if "[Syntactic]" in v.description else "[ASSERT]"
        print(f"  {marker} {src} [{v.invariant}] {v.verdict_type.value}")
        print(f"     {v.description[:120]}")
        if v.verdict_type.value in ("VIOLATION", "UNEXPECTED"):
            findings.append(v)
    return result, findings


# ====================================================================
# Test 1: sub="" (空 sub)
# ====================================================================
def test_empty_sub(executor):
    return run_sequence(executor, EventSequence(
        sequence_id="manual_i4_empty_sub",
        description="Login with empty string sub claim",
        invariant_hypothesis="I4: empty sub should be rejected or map to unique entity",
        primary_invariant="I4",
        events=[
            Event(event_type="setup_jwt_role",
                  params={"mount": MOUNT, "role_name": "empty-sub-test",
                          "user_claim": "sub", "bound_audiences": ["vault"],
                          "token_policies": ["default"]},
                  auth_as="admin"),
            Event(event_type="login_jwt",
                  params={"mount": MOUNT, "role": "empty-sub-test",
                          "jwt_claims": {"sub": "", "aud": "vault"}},
                  auth_as="empty_user",
                  captures={"empty_entity": "auth.entity_id"},
                  expected_outcome="any"),
            Event(event_type="login_jwt",
                  params={"mount": MOUNT, "role": "empty-sub-test",
                          "jwt_claims": {"sub": "legitimate-user", "aud": "vault"}},
                  auth_as="legit_user",
                  captures={"legit_entity": "auth.entity_id"}),
        ],
        oracle_checks=[
            OracleCheck(check_id="empty_sub", invariant="I4",
                       assertion="empty_user_login_success == False",
                       violation_description="Empty sub accepted — potential identity confusion",
                       cve_analog="vault-sub-empty-bug"),
        ],
    ))


# ====================================================================
# Test 2: Unicode normalization — café vs café (NFC vs NFD)
# ====================================================================
def test_unicode_normalization(executor):
    import unicodedata
    nfc = unicodedata.normalize("NFC", "café")
    nfd = unicodedata.normalize("NFD", "café")
    return run_sequence(executor, EventSequence(
        sequence_id="manual_i4_unicode",
        description=f"Unicode NFC vs NFD: '{nfc}' vs '{nfd}' (different bytes, same visual)",
        invariant_hypothesis="I4: visually identical but byte-different strings should not collide",
        primary_invariant="I4",
        events=[
            Event(event_type="setup_jwt_role",
                  params={"mount": MOUNT, "role_name": "unicode-test",
                          "user_claim": "sub", "bound_audiences": ["vault"],
                          "token_policies": ["default"]},
                  auth_as="admin"),
            Event(event_type="login_jwt",
                  params={"mount": MOUNT, "role": "unicode-test",
                          "jwt_claims": {"sub": nfc, "aud": "vault"}},
                  auth_as="user_nfc",
                  captures={"nfc_entity": "auth.entity_id"}),
            Event(event_type="login_jwt",
                  params={"mount": MOUNT, "role": "unicode-test",
                          "jwt_claims": {"sub": nfd, "aud": "vault"}},
                  auth_as="user_nfd",
                  captures={"nfd_entity": "auth.entity_id"}),
            Event(event_type="verify_entity",
                  params={"entity_id": "{{nfc_entity}}"},
                  auth_as="admin",
                  captures={"nfc_aliases": "data.aliases", "nfc_name": "data.name"}),
            Event(event_type="verify_entity",
                  params={"entity_id": "{{nfd_entity}}"},
                  auth_as="admin",
                  captures={"nfd_aliases": "data.aliases", "nfd_name": "data.name"}),
        ],
        oracle_checks=[
            OracleCheck(check_id="unicode_collision", invariant="I4",
                       assertion="nfc_entity != nfd_entity",
                       violation_description="NFC and NFD forms of same string mapped to same entity — unicode normalization collision"),
        ],
    ))


# ====================================================================
# Test 3: group claim type confusion — string "admins" vs array ["admins"]
# ====================================================================
def test_groups_type_confusion(executor):
    return run_sequence(executor, EventSequence(
        sequence_id="manual_i5_groups_type",
        description="groups claim as string vs array — same group mapping?",
        invariant_hypothesis="I5: string 'admins' should not map to group 'admins' (type mismatch)",
        primary_invariant="I5", cve_analog="CVE-2024-5798",
        events=[
            Event(event_type="setup_jwt_role",
                  params={"mount": MOUNT, "role_name": "groups-type-test",
                          "user_claim": "sub", "groups_claim": "groups",
                          "bound_audiences": ["vault"], "token_policies": ["default"]},
                  auth_as="admin"),
            Event(event_type="login_jwt",
                  params={"mount": MOUNT, "role": "groups-type-test",
                          "jwt_claims": {"sub": "user-array", "aud": "vault",
                                         "groups": ["engineers"]}},
                  auth_as="user_array",
                  captures={"array_policies": "auth.policies", "array_entity": "auth.entity_id"}),
            Event(event_type="login_jwt",
                  params={"mount": MOUNT, "role": "groups-type-test",
                          "jwt_claims": {"sub": "user-string", "aud": "vault",
                                         "groups": "engineers"}},
                  auth_as="user_string",
                  captures={"string_policies": "auth.policies", "string_entity": "auth.entity_id"},
                  expected_outcome="any"),
        ],
        oracle_checks=[
            OracleCheck(check_id="groups_type", invariant="I5",
                       assertion="user_string_login_success == False",
                       violation_description="String groups claim accepted — type confusion may affect group mapping",
                       cve_analog="CVE-2024-5798"),
        ],
    ))


# ====================================================================
# Test 4: bound_claims with glob wildcard in claim VALUE
# ====================================================================
def test_bound_claims_glob(executor):
    return run_sequence(executor, EventSequence(
        sequence_id="manual_i4_glob",
        description="bound_claims={'department': 'engineering'}, JWT sends department='*'",
        invariant_hypothesis="I4: glob wildcard in claim value should not match bound_claims pattern",
        primary_invariant="I4", cve_analog="CVE-2025-11621",
        events=[
            Event(event_type="setup_jwt_role",
                  params={"mount": MOUNT, "role_name": "glob-test",
                          "user_claim": "sub", "bound_audiences": ["vault"],
                          "bound_claims": {"department": ["engineering"]},
                          "token_policies": ["default"]},
                  auth_as="admin"),
            Event(event_type="login_jwt",
                  params={"mount": MOUNT, "role": "glob-test",
                          "jwt_claims": {"sub": "attacker", "aud": "vault",
                                         "department": "*"}},
                  auth_as="attacker_glob",
                  captures={"glob_entity": "auth.entity_id"},
                  expected_outcome="any"),
        ],
        oracle_checks=[
            OracleCheck(check_id="glob_bypass", invariant="I4",
                       assertion="attacker_glob_login_success == False",
                       violation_description="Wildcard '*' in claim value matched bound_claims — glob injection",
                       cve_analog="CVE-2025-11621"),
        ],
    ))


# ====================================================================
# Test 5: cross-role isolation
# ====================================================================
def test_cross_role_isolation(executor):
    return run_sequence(executor, EventSequence(
        sequence_id="manual_i5_cross_role",
        description="Role A gives read-only, role B gives admin. Login to A, try admin secrets.",
        invariant_hypothesis="I5: EffectivePerms(session) ⊆ role_A.token_policies",
        primary_invariant="I5",
        events=[
            Event(event_type="setup_policy",
                  params={"policy_name": "test-readonly",
                          "policy": 'path "secret/data/public/*" { capabilities = ["read"] }'},
                  auth_as="admin"),
            Event(event_type="setup_policy",
                  params={"policy_name": "test-admin",
                          "policy": 'path "secret/data/admin/*" { capabilities = ["read","create","update"] }'},
                  auth_as="admin"),
            Event(event_type="setup_secret",
                  params={"secret_path": "admin/flag", "data": {"flag": "admin-only"}},
                  auth_as="admin"),
            Event(event_type="setup_jwt_role",
                  params={"mount": MOUNT, "role_name": "role-readonly",
                          "user_claim": "sub", "bound_audiences": ["vault"],
                          "token_policies": ["test-readonly"]},
                  auth_as="admin"),
            Event(event_type="login_jwt",
                  params={"mount": MOUNT, "role": "role-readonly",
                          "jwt_claims": {"sub": "reader", "aud": "vault"}},
                  auth_as="reader",
                  captures={"reader_policies": "auth.policies"}),
            Event(event_type="verify_read_secret",
                  params={"secret_path": "admin/flag"},
                  auth_as="session_reader",
                  captures={"admin_access_status": "http_status"},
                  expected_outcome="failure"),
        ],
        oracle_checks=[
            OracleCheck(check_id="cross_role", invariant="I5",
                       assertion="admin_access_status == 403",
                       violation_description="Reader role accessed admin secrets — cross-role policy leak"),
        ],
    ))


# ====================================================================
# Test 6: entity policy escalation via pre-provisioned entity
# ====================================================================
def test_entity_policy_injection(executor):
    """Pre-create entity with admin policies, then login as that identity."""
    import requests
    headers = {"X-Vault-Token": ADMIN_TOKEN}

    r = requests.get(f"{VAULT_URL}/v1/sys/auth", headers=headers)
    accessor = r.json().get("data", r.json()).get(f"{MOUNT}/", {}).get("accessor", "")
    if not accessor:
        print("  SKIP: cannot get mount accessor")
        return None, []

    return run_sequence(executor, EventSequence(
        sequence_id="manual_i5_entity_inject",
        description="Pre-create entity with admin policy, login should NOT inherit it",
        invariant_hypothesis="I5: token_policies from role should not be overridden by entity policies",
        primary_invariant="I5",
        events=[
            Event(event_type="setup_policy",
                  params={"policy_name": "injected-admin",
                          "policy": 'path "secret/*" { capabilities = ["read","create","update","delete","list","sudo"] }'},
                  auth_as="admin"),
            Event(event_type="setup_entity",
                  params={"name": "preprovisioned-user", "policies": ["injected-admin"]},
                  auth_as="admin",
                  captures={"pre_entity_id": "data.id"}),
            Event(event_type="setup_entity_alias",
                  params={"name": "evil-user", "canonical_id": "{{pre_entity_id}}",
                          "mount_accessor": accessor},
                  auth_as="admin"),
            Event(event_type="setup_jwt_role",
                  params={"mount": MOUNT, "role_name": "entity-inject-test",
                          "user_claim": "sub", "bound_audiences": ["vault"],
                          "token_policies": ["default"]},
                  auth_as="admin"),
            Event(event_type="login_jwt",
                  params={"mount": MOUNT, "role": "entity-inject-test",
                          "jwt_claims": {"sub": "evil-user", "aud": "vault"}},
                  auth_as="evil",
                  captures={"evil_policies": "auth.policies",
                           "evil_identity_policies": "auth.identity_policies",
                           "evil_entity": "auth.entity_id"}),
            Event(event_type="verify_token_self",
                  params={},
                  auth_as="session_evil",
                  captures={"evil_all_policies": "data.policies",
                           "evil_id_policies": "data.identity_policies"}),
        ],
        oracle_checks=[
            OracleCheck(check_id="entity_inject", invariant="I5",
                       assertion='"injected-admin" not in evil_policies',
                       violation_description="Pre-provisioned entity policies leaked into token — policy injection via entity"),
        ],
    ))


def main():
    executor = setup()
    all_findings = []

    tests = [
        test_empty_sub,
        test_unicode_normalization,
        test_groups_type_confusion,
        test_bound_claims_glob,
        test_cross_role_isolation,
        test_entity_policy_injection,
    ]

    for test_fn in tests:
        try:
            result, findings = test_fn(executor)
            if findings:
                all_findings.extend(findings)
        except Exception as e:
            print(f"  ERROR in {test_fn.__name__}: {e}")
            import traceback; traceback.print_exc()

    print(f"\n{'='*60}")
    print(f"  MANUAL TESTS COMPLETE")
    print(f"  Total findings: {len(all_findings)}")
    print(f"{'='*60}")
    for f in all_findings:
        print(f"  [{f.invariant}] {f.verdict_type.value}: {f.description[:100]}")

    # Cleanup
    import requests
    requests.delete(f"{VAULT_URL}/v1/sys/auth/{MOUNT}",
                   headers={"X-Vault-Token": ADMIN_TOKEN})
    print("\nCleanup: mount removed.")


if __name__ == "__main__":
    main()
