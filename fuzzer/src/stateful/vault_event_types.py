# DEAD CODE — kept temporarily until we verify safe to delete after tests pass.
"""Registry of Vault API operations for stateful testing.

Each event type maps to a concrete Vault HTTP API call.
Paths and fields are from vault_api_spec.json.
"""

EVENT_REGISTRY = {
    # ===================== SETUP (admin operations) =====================

    "setup_jwt_config": {
        "description": "Configure JWT auth backend (JWKS URL, issuer, etc.)",
        "method": "POST",
        "path": "/v1/auth/{mount}/config",
        "auth": "admin",
        "params_schema": {
            "mount": {"type": "string", "default": "jwt", "in": "path"},
            "jwks_url": {"type": "string", "in": "body", "required": False},
            "oidc_discovery_url": {"type": "string", "in": "body", "required": False},
            "jwt_validation_pubkeys": {"type": "list", "in": "body", "required": False},
            "bound_issuer": {"type": "string", "in": "body", "required": False},
            "default_role": {"type": "string", "in": "body", "required": False},
        },
        "category": "admin_audit",
    },

    "setup_jwt_role": {
        "description": "Create/update a JWT auth role with claim bindings and policies",
        "method": "POST",
        "path": "/v1/auth/{mount}/role/{role_name}",
        "auth": "admin",
        "params_schema": {
            "mount": {"type": "string", "default": "jwt", "in": "path"},
            "role_name": {"type": "string", "in": "path", "required": True},
            "role_type": {"type": "string", "in": "body", "default": "jwt"},
            "user_claim": {"type": "string", "in": "body", "default": "sub"},
            "user_claim_json_pointer": {"type": "bool", "in": "body"},
            "groups_claim": {"type": "string", "in": "body", "default": ""},
            "bound_audiences": {"type": "list", "in": "body", "default": []},
            "bound_claims": {"type": "dict", "in": "body", "default": {}},
            "bound_claims_type": {"type": "string", "in": "body", "default": "string"},
            "bound_subject": {"type": "string", "in": "body", "default": ""},
            "claim_mappings": {"type": "dict", "in": "body", "default": {}},
            "token_policies": {"type": "list", "in": "body", "default": ["default"]},
            "token_ttl": {"type": "string", "in": "body", "default": "1h"},
            "token_max_ttl": {"type": "string", "in": "body", "default": ""},
            "token_num_uses": {"type": "int", "in": "body", "default": 0},
            "allowed_redirect_uris": {"type": "list", "in": "body"},
        },
        "category": "admin_audit",
    },

    "setup_policy": {
        "description": "Create/update an ACL policy",
        "method": "PUT",
        "path": "/v1/sys/policies/acl/{policy_name}",
        "auth": "admin",
        "params_schema": {
            "policy_name": {"type": "string", "in": "path", "required": True},
            "policy": {"type": "string", "in": "body", "required": True},
        },
        "category": "permission_check",
    },

    "setup_entity": {
        "description": "Create an identity entity (pre-provision before login)",
        "method": "POST",
        "path": "/v1/identity/entity",
        "auth": "admin",
        "params_schema": {
            "name": {"type": "string", "in": "body", "required": True},
            "policies": {"type": "list", "in": "body", "default": []},
            "metadata": {"type": "dict", "in": "body", "default": {}},
            "disabled": {"type": "bool", "in": "body", "default": False},
        },
        "response_captures": {
            "entity_id": "data.id",
        },
        "category": "identity_lookup",
    },

    "setup_entity_alias": {
        "description": "Create an entity alias linking an auth mount to an entity",
        "method": "POST",
        "path": "/v1/identity/entity-alias",
        "auth": "admin",
        "params_schema": {
            "name": {"type": "string", "in": "body", "required": True},
            "canonical_id": {"type": "string", "in": "body", "required": True},
            "mount_accessor": {"type": "string", "in": "body", "required": True},
        },
        "response_captures": {
            "alias_id": "data.id",
        },
        "category": "identity_lookup",
    },

    "setup_group": {
        "description": "Create an identity group with policies",
        "method": "POST",
        "path": "/v1/identity/group",
        "auth": "admin",
        "params_schema": {
            "name": {"type": "string", "in": "body", "required": True},
            "policies": {"type": "list", "in": "body", "default": []},
            "member_entity_ids": {"type": "list", "in": "body", "default": []},
            "type": {"type": "string", "in": "body", "default": "internal"},
            "metadata": {"type": "dict", "in": "body", "default": {}},
        },
        "response_captures": {
            "group_id": "data.id",
        },
        "category": "permission_check",
    },

    "setup_group_alias": {
        "description": "Create a group alias (maps external group name to internal group)",
        "method": "POST",
        "path": "/v1/identity/group-alias",
        "auth": "admin",
        "params_schema": {
            "name": {"type": "string", "in": "body", "required": True},
            "mount_accessor": {"type": "string", "in": "body", "required": True},
            "canonical_id": {"type": "string", "in": "body", "required": True},
        },
        "category": "permission_check",
    },

    "setup_secret": {
        "description": "Seed a KV v2 secret for access testing",
        "method": "POST",
        "path": "/v1/secret/data/{secret_path}",
        "auth": "admin",
        "params_schema": {
            "secret_path": {"type": "string", "in": "path", "required": True},
            "data": {"type": "dict", "in": "body", "required": True},
        },
        "category": "access_test",
    },

    "setup_get_mount_accessor": {
        "description": "Get the mount accessor for the JWT auth mount (needed for aliases)",
        "method": "GET",
        "path": "/v1/sys/auth",
        "auth": "admin",
        "params_schema": {},
        "category": "admin_audit",
    },

    # ===================== AUTH (login attempts) =====================

    "login_jwt": {
        "description": "Authenticate with a signed JWT",
        "method": "POST",
        "path": "/v1/auth/{mount}/login",
        "auth": "none",
        "params_schema": {
            "mount": {"type": "string", "default": "jwt", "in": "path"},
            "role": {"type": "string", "in": "body", "required": True},
            "jwt": {"type": "string", "in": "body", "required": True},
        },
        "response_captures": {
            "client_token": "auth.client_token",
            "accessor": "auth.accessor",
            "policies": "auth.policies",
            "entity_id": "auth.entity_id",
            "lease_duration": "auth.lease_duration",
            "metadata": "auth.metadata",
        },
        "category": "session_token_inspect",
    },

    # ===================== VERIFY (post-auth checks) =====================

    "verify_token_self": {
        "description": "Inspect the current session token (identity_lookup + session_token_inspect)",
        "method": "GET",
        "path": "/v1/auth/token/lookup-self",
        "auth": "session",
        "params_schema": {},
        "response_captures": {
            "display_name": "data.display_name",
            "entity_id": "data.entity_id",
            "policies": "data.policies",
            "identity_policies": "data.identity_policies",
            "meta": "data.meta",
            "path": "data.path",
            "creation_time": "data.creation_time",
            "expire_time": "data.expire_time",
            "ttl": "data.ttl",
            "num_uses": "data.num_uses",
            "renewable": "data.renewable",
        },
        "category": "session_token_inspect",
    },

    "verify_entity": {
        "description": "Look up identity entity by ID (identity_lookup)",
        "method": "GET",
        "path": "/v1/identity/entity/id/{entity_id}",
        "auth": "admin",
        "params_schema": {
            "entity_id": {"type": "string", "in": "path", "required": True},
        },
        "response_captures": {
            "entity_name": "data.name",
            "entity_policies": "data.policies",
            "entity_aliases": "data.aliases",
            "entity_group_ids": "data.group_ids",
            "entity_disabled": "data.disabled",
            "entity_metadata": "data.metadata",
        },
        "category": "identity_lookup",
    },

    "verify_entity_by_name": {
        "description": "Look up identity entity by name",
        "method": "GET",
        "path": "/v1/identity/entity/name/{entity_name}",
        "auth": "admin",
        "params_schema": {
            "entity_name": {"type": "string", "in": "path", "required": True},
        },
        "response_captures": {
            "entity_id": "data.id",
            "entity_policies": "data.policies",
            "entity_group_ids": "data.group_ids",
        },
        "category": "identity_lookup",
    },

    "verify_group": {
        "description": "Look up identity group by ID (permission_check)",
        "method": "GET",
        "path": "/v1/identity/group/id/{group_id}",
        "auth": "admin",
        "params_schema": {
            "group_id": {"type": "string", "in": "path", "required": True},
        },
        "response_captures": {
            "group_name": "data.name",
            "group_policies": "data.policies",
            "group_member_entity_ids": "data.member_entity_ids",
        },
        "category": "permission_check",
    },

    "verify_policy": {
        "description": "Read an ACL policy document (permission_check)",
        "method": "GET",
        "path": "/v1/sys/policies/acl/{policy_name}",
        "auth": "admin",
        "params_schema": {
            "policy_name": {"type": "string", "in": "path", "required": True},
        },
        "response_captures": {
            "policy_rules": "data.policy",
        },
        "category": "permission_check",
    },

    "verify_read_secret": {
        "description": "Attempt to read a KV v2 secret (access_test)",
        "method": "GET",
        "path": "/v1/secret/data/{secret_path}",
        "auth": "session",
        "params_schema": {
            "secret_path": {"type": "string", "in": "path", "required": True},
        },
        "response_captures": {
            "secret_data": "data.data",
            "secret_version": "data.metadata.version",
        },
        "category": "access_test",
    },

    "verify_write_secret": {
        "description": "Attempt to write a KV v2 secret (access_test)",
        "method": "POST",
        "path": "/v1/secret/data/{secret_path}",
        "auth": "session",
        "params_schema": {
            "secret_path": {"type": "string", "in": "path", "required": True},
            "data": {"type": "dict", "in": "body", "required": True},
        },
        "category": "access_test",
    },

    "verify_list_secrets": {
        "description": "Attempt to list KV v2 secrets (access_test)",
        "method": "LIST",
        "path": "/v1/secret/metadata/{secret_path}",
        "auth": "session",
        "params_schema": {
            "secret_path": {"type": "string", "in": "path", "default": ""},
        },
        "category": "access_test",
    },

    # ===================== MODIFY (mid-test state changes) =====================

    "modify_role": {
        "description": "Change a JWT role configuration mid-test",
        "method": "POST",
        "path": "/v1/auth/{mount}/role/{role_name}",
        "auth": "admin",
        "params_schema": {
            "mount": {"type": "string", "default": "jwt", "in": "path"},
            "role_name": {"type": "string", "in": "path", "required": True},
        },
        "category": "admin_audit",
    },

    "modify_entity": {
        "description": "Modify an identity entity mid-test (disable, change policies)",
        "method": "POST",
        "path": "/v1/identity/entity/id/{entity_id}",
        "auth": "admin",
        "params_schema": {
            "entity_id": {"type": "string", "in": "path", "required": True},
            "disabled": {"type": "bool", "in": "body"},
            "policies": {"type": "list", "in": "body"},
            "metadata": {"type": "dict", "in": "body"},
        },
        "category": "identity_lookup",
    },

    "delete_role": {
        "description": "Delete a JWT auth role",
        "method": "DELETE",
        "path": "/v1/auth/{mount}/role/{role_name}",
        "auth": "admin",
        "params_schema": {
            "mount": {"type": "string", "default": "jwt", "in": "path"},
            "role_name": {"type": "string", "in": "path", "required": True},
        },
        "category": "admin_audit",
    },

    "revoke_token": {
        "description": "Revoke a specific token",
        "method": "POST",
        "path": "/v1/auth/token/revoke",
        "auth": "admin",
        "params_schema": {
            "token": {"type": "string", "in": "body", "required": True},
        },
        "category": "session_token_inspect",
    },
}


def get_event_types_summary() -> str:
    """Return a compact summary for LLM prompts (event_type: description)."""
    lines = []
    for name, info in EVENT_REGISTRY.items():
        auth = info["auth"]
        params = [k for k, v in info["params_schema"].items() if v.get("required")]
        lines.append(f"  {name} [{auth}]: {info['description']}")
        if params:
            lines.append(f"    required: {', '.join(params)}")
    return "\n".join(lines)


def get_event_types_json() -> dict:
    """Return registry as JSON-serializable dict for LLM prompt."""
    compact = {}
    for name, info in EVENT_REGISTRY.items():
        compact[name] = {
            "method": info["method"],
            "path": info["path"],
            "auth": info["auth"],
            "description": info["description"],
            "key_params": [
                k for k in info["params_schema"]
                if info["params_schema"][k].get("in") == "body"
            ],
        }
    return compact
