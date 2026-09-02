"""Fetch platform documentation via GitHub API directory listing.

For each platform, we specify:
  - A GitHub repo + directory path containing API docs
  - File extension filter (.mdx, .md, .html)
  - Optional keyword filter (to skip obviously irrelevant docs)

The script:
  1. Lists ALL files in the directory (recursively) via GitHub API
  2. Downloads ALL matching files
  3. Cleans them (strip MDX/JSX/HTML noise)
  4. Concatenates into ALL_DOCS.md for LLM input

This is MUCH better than hardcoding URLs because:
  - We never miss a doc page
  - New docs added by the platform are automatically included
  - URL structure changes don't break us (we discover by directory listing)

Usage:
    python -m src.extraction.fetch_docs --platform vault
    python -m src.extraction.fetch_docs --platform vault --force
    python -m src.extraction.fetch_docs --platform vault --list-only
"""
import json
import logging
import os
import re
import time
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Platform documentation sources (discovery-based)
# ---------------------------------------------------------------------------

PLATFORM_DOC_SOURCES = {
    "vault": {
        "oidc_jwt": {
            "github_repos": [
                {
                    "repo": "hashicorp/web-unified-docs",
                    "branch": "main",
                    "paths": [
                        "content/vault/v1.21.x/content/api-docs/auth",
                        "content/vault/v1.21.x/content/api-docs/secret/identity",
                        "content/vault/v1.21.x/content/api-docs/system",
                        "content/vault/v1.21.x/content/api-docs/secret/kv",
                    ],
                    "extensions": [".mdx", ".md"],
                },
            ],
            "direct_urls": [],
            "local_paths": [
                "src/extraction/local-docs/vault/content/vault/v1.21.x/content/api-docs/auth",
                "src/extraction/local-docs/vault/content/vault/v1.21.x/content/api-docs/secret/identity",
                "src/extraction/local-docs/vault/content/vault/v1.21.x/content/api-docs/system",
                "src/extraction/local-docs/vault/content/vault/v1.21.x/content/api-docs/secret/kv",
            ],
        },
        "saml": {
            "github_repos": [
                {
                    "repo": "hashicorp/web-unified-docs",
                    "branch": "main",
                    "paths": [
                        "content/vault/v1.21.x/content/api-docs/auth",
                        "content/vault/v1.21.x/content/api-docs/secret/identity",
                        "content/vault/v1.21.x/content/api-docs/system",
                        "content/vault/v1.21.x/content/api-docs/secret/kv",
                    ],
                    "extensions": [".mdx", ".md"],
                },
            ],
            "direct_urls": [],
            "local_paths": [
                "src/extraction/local-docs/vault/content/vault/v1.21.x/content/api-docs/auth",
                "src/extraction/local-docs/vault/content/vault/v1.21.x/content/api-docs/secret/identity",
                "src/extraction/local-docs/vault/content/vault/v1.21.x/content/api-docs/system",
                "src/extraction/local-docs/vault/content/vault/v1.21.x/content/api-docs/secret/kv",
            ],
        },
    },
    "keycloak": {
        "oidc_jwt": {
            "github_repos": [
                {
                    "repo": "keycloak/keycloak",
                    "branch": "main",
                    "paths": [
                        "docs/documentation/server_admin",
                        "docs/documentation/authorization_services",
                        "docs/documentation/server_development",
                        "docs/documentation/upgrading",
                        "docs/documentation/api_documentation",
                        "docs/documentation/topics",
                    ],
                    "extensions": [".adoc", ".md"],
                },
            ],
            "direct_urls": [
                "https://www.keycloak.org/docs-api/latest/rest-api/openapi.json",
            ],
            "local_paths": [
                "src/extraction/local-docs/keycloak/docs/documentation/server_admin",
                "src/extraction/local-docs/keycloak/docs/documentation/authorization_services",
                "src/extraction/local-docs/keycloak/docs/documentation/server_development",
                "src/extraction/local-docs/keycloak/docs/documentation/upgrading",
                "src/extraction/local-docs/keycloak/docs/documentation/api_documentation",
                "src/extraction/local-docs/keycloak/docs/documentation/topics",
            ],
        },
        "saml": {
            "github_repos": [
                {
                    "repo": "keycloak/keycloak",
                    "branch": "main",
                    "paths": [
                        "docs/documentation/server_admin",
                        "docs/documentation/authorization_services",
                        "docs/documentation/server_development",
                        "docs/documentation/upgrading",
                        "docs/documentation/api_documentation",
                        "docs/documentation/topics",
                    ],
                    "extensions": [".adoc", ".md"],
                },
            ],
            "direct_urls": [
                "https://www.keycloak.org/docs-api/latest/rest-api/openapi.json",
            ],
            "local_paths": [
                "src/extraction/local-docs/keycloak/docs/documentation/server_admin",
                "src/extraction/local-docs/keycloak/docs/documentation/authorization_services",
                "src/extraction/local-docs/keycloak/docs/documentation/server_development",
                "src/extraction/local-docs/keycloak/docs/documentation/upgrading",
                "src/extraction/local-docs/keycloak/docs/documentation/api_documentation",
                "src/extraction/local-docs/keycloak/docs/documentation/topics",
            ],
        },
    },
    "dex": {
        "oidc_jwt": {
            "github_repos": [],
            "direct_urls": [],
            "local_paths": [
                "src/extraction/local-docs/dex/content/docs",
            ],
        },
        "saml": {
            "github_repos": [],
            "direct_urls": [],
            "local_paths": [
                "src/extraction/local-docs/dex/content/docs",
            ],
        },
    },
    "authentik": {
        "oidc_jwt": {
            "github_repos": [],
            "direct_urls": [],
            "local_paths": [
                "src/extraction/local-docs/authentik/website/docs/add-secure-apps",
                "src/extraction/local-docs/authentik/website/docs/core",
                "src/extraction/local-docs/authentik/website/docs/developer-docs",
                "src/extraction/local-docs/authentik/website/docs/users-sources",
                "src/extraction/local-docs/authentik/website/docs/security",
                "src/extraction/local-docs/authentik/website/docs/expressions",
                "src/extraction/local-docs/authentik/website/docs/install-config",
            ],
        },
        "saml": {
            "github_repos": [],
            "direct_urls": [],
            "local_paths": [
                "src/extraction/local-docs/authentik/website/docs/add-secure-apps",
                "src/extraction/local-docs/authentik/website/docs/core",
                "src/extraction/local-docs/authentik/website/docs/developer-docs",
                "src/extraction/local-docs/authentik/website/docs/users-sources",
                "src/extraction/local-docs/authentik/website/docs/security",
                "src/extraction/local-docs/authentik/website/docs/expressions",
                "src/extraction/local-docs/authentik/website/docs/install-config",
            ],
        },
    },
    "zitadel": {
        "oidc_jwt": {
            "github_repos": [],
            "direct_urls": [],
            "local_paths": [
                "src/extraction/local-docs/zitadel/apps/docs/content/apis",
                "src/extraction/local-docs/zitadel/apps/docs/content/concepts",
                "src/extraction/local-docs/zitadel/apps/docs/content/guides",
                "src/extraction/local-docs/zitadel/apps/docs/content/self-hosting",
                "src/extraction/local-docs/zitadel/proto/zitadel/oidc",
                "src/extraction/local-docs/zitadel/proto/zitadel/session",
                "src/extraction/local-docs/zitadel/proto/zitadel/user",
                "src/extraction/local-docs/zitadel/proto/zitadel/idp",
                "src/extraction/local-docs/zitadel/proto/zitadel/app",
                "src/extraction/local-docs/zitadel/proto/zitadel/authorization",
            ],
        },
        "saml": {
            "github_repos": [],
            "direct_urls": [],
            "local_paths": [
                "src/extraction/local-docs/zitadel/apps/docs/content/apis",
                "src/extraction/local-docs/zitadel/apps/docs/content/concepts",
                "src/extraction/local-docs/zitadel/apps/docs/content/guides",
                "src/extraction/local-docs/zitadel/proto/zitadel/saml",
                "src/extraction/local-docs/zitadel/proto/zitadel/session",
                "src/extraction/local-docs/zitadel/proto/zitadel/user",
                "src/extraction/local-docs/zitadel/proto/zitadel/idp",
                "src/extraction/local-docs/zitadel/proto/zitadel/app",
            ],
        },
    },
    "logto": {
        "oidc_jwt": {
            "github_repos": [],
            "direct_urls": [],
            "local_paths": [
                "src/extraction/local-docs/lgoto/docs/api-protection",
                "src/extraction/local-docs/lgoto/docs/authorization",
                "src/extraction/local-docs/lgoto/docs/concepts",
                "src/extraction/local-docs/lgoto/docs/connectors",
                "src/extraction/local-docs/lgoto/docs/developers",
                "src/extraction/local-docs/lgoto/docs/end-user-flows",
                "src/extraction/local-docs/lgoto/docs/integrate-logto",
                "src/extraction/local-docs/lgoto/docs/introduction",
                "src/extraction/local-docs/lgoto/docs/security",
                "src/extraction/local-docs/lgoto/docs/user-management",
                "src/extraction/local-docs/lgoto/docs/organizations",
            ],
        },
        "saml": {
            "github_repos": [],
            "direct_urls": [],
            "local_paths": [
                "src/extraction/local-docs/lgoto/docs/api-protection",
                "src/extraction/local-docs/lgoto/docs/concepts",
                "src/extraction/local-docs/lgoto/docs/connectors",
                "src/extraction/local-docs/lgoto/docs/developers",
                "src/extraction/local-docs/lgoto/docs/integrate-logto",
                "src/extraction/local-docs/lgoto/docs/introduction",
                "src/extraction/local-docs/lgoto/docs/security",
                "src/extraction/local-docs/lgoto/docs/user-management",
            ],
        },
    },
    "casdoor": {
        "oidc_jwt": {
            "github_repos": [],
            "direct_urls": [],
            "local_paths": [
                "src/extraction/local-docs/casdoor-website/docs/basic",
                "src/extraction/local-docs/casdoor-website/docs/how-to-connect",
                "src/extraction/local-docs/casdoor-website/docs/permission",
                "src/extraction/local-docs/casdoor-website/docs/organization",
                "src/extraction/local-docs/casdoor-website/docs/application",
                "src/extraction/local-docs/casdoor-website/docs/provider",
                "src/extraction/local-docs/casdoor-website/docs/user",
                "src/extraction/local-docs/casdoor-website/docs/token",
                "src/extraction/local-docs/casdoor-website/docs/cert",
                "src/extraction/local-docs/casdoor-website/docs/session",
                "src/extraction/local-docs/casdoor-website/docs/webhooks",
                "src/extraction/local-docs/casdoor-website/docs/developer-guide",
            ],
        },
        "saml": {
            "github_repos": [],
            "direct_urls": [],
            "local_paths": [
                "src/extraction/local-docs/casdoor-website/docs/basic",
                "src/extraction/local-docs/casdoor-website/docs/how-to-connect",
                "src/extraction/local-docs/casdoor-website/docs/provider",
                "src/extraction/local-docs/casdoor-website/docs/application",
                "src/extraction/local-docs/casdoor-website/docs/user",
                "src/extraction/local-docs/casdoor-website/docs/session",
                "src/extraction/local-docs/casdoor-website/docs/webhooks",
                "src/extraction/local-docs/casdoor-website/docs/developer-guide",
                "src/extraction/local-docs/casdoor-website/docs/organization",
            ],
        },
    },
}

# Cache lifetime: 24 hours
CACHE_MAX_AGE_SECONDS = 86400

GITHUB_API = "https://api.github.com"


# ---------------------------------------------------------------------------
# GitHub API directory listing
# ---------------------------------------------------------------------------

def list_github_directory(repo: str, path: str, branch: str = "main",
                          extensions: list[str] = None,
                          token: str = None) -> list[dict]:
    """List all files in a GitHub directory recursively.

    Uses GitHub Contents API. Falls back to Trees API for large directories.

    Returns list of {"path": "relative/path.mdx", "download_url": "https://raw.../..."}
    """
    import requests

    headers = {"Accept": "application/vnd.github.v3+json"}
    if token:
        headers["Authorization"] = f"token {token}"

    files = []

    url = f"{GITHUB_API}/repos/{repo}/contents/{path}?ref={branch}"
    resp = requests.get(url, headers=headers, timeout=30)

    if resp.status_code == 403:
        logger.warning("GitHub API rate limited. Set GITHUB_TOKEN env var for higher limits.")
        return files

    if resp.status_code != 200:
        logger.warning(f"GitHub API error {resp.status_code} for {repo}/{path}")
        return files

    items = resp.json()
    if not isinstance(items, list):
        # Single file, not directory
        if _matches_extensions(items.get("name", ""), extensions):
            files.append({
                "path": items["path"],
                "download_url": items.get("download_url"),
                "size": items.get("size", 0),
            })
        return files

    for item in items:
        if item["type"] == "file":
            if _matches_extensions(item["name"], extensions):
                files.append({
                    "path": item["path"],
                    "download_url": item.get("download_url"),
                    "size": item.get("size", 0),
                })
        elif item["type"] == "dir":
            time.sleep(0.1)  # Respect rate limits
            subfiles = list_github_directory(
                repo, item["path"], branch, extensions, token
            )
            files.extend(subfiles)

    return files


def _matches_extensions(filename: str, extensions: list[str] = None) -> bool:
    if not extensions:
        return True
    return any(filename.endswith(ext) for ext in extensions)


# ---------------------------------------------------------------------------
# Cleaning functions
# ---------------------------------------------------------------------------

def clean_mdx(content: str) -> str:
    """Strip MDX/JSX components from Vault docs, keep markdown content."""
    lines = []
    skip_block = False
    for line in content.split("\n"):
        stripped = line.strip()
        # Skip import/export statements
        if stripped.startswith(("import ", "export ")):
            continue
        # Close an open JSX block — MUST be checked before the generic '<' handler
        if skip_block and stripped.startswith("</"):
            skip_block = False
            continue
        # Skip lines inside an open JSX block
        if skip_block:
            continue
        # Skip self-closing and opening JSX tags (not plain URLs like <https://...>)
        if stripped.startswith("<") and not stripped.startswith("<http"):
            if "/>" in stripped:
                continue  # self-closing tag
            if stripped.startswith("</"):
                continue  # orphaned closing tag
            # Opening tag — start skipping until the matching close
            skip_block = True
            continue
        lines.append(line)
    return "\n".join(lines)


def clean_html(content: str) -> str:
    """Extract main content from HTML API docs."""
    # Remove script/style blocks
    content = re.sub(r'<(script|style)[^>]*>.*?</\1>', '', content, flags=re.DOTALL)
    # Remove HTML tags but keep text
    content = re.sub(r'<[^>]+>', ' ', content)
    # Collapse whitespace
    content = re.sub(r'\s+', ' ', content)
    return content.strip()


def clean_openapi_json(content: str) -> str:
    """Filter OpenAPI JSON to security-relevant paths only."""
    try:
        spec = json.loads(content)
    except Exception:
        return content  # Return as-is if not valid JSON

    # Keep only security-relevant path prefixes
    security_prefixes = [
        "/auth/", "/realms/", "/admin/realms/",
        "/token", "/userinfo", "/introspect",
        "/protocol/openid-connect",
        "/identity-provider", "/clients", "/roles", "/users", "/groups",
    ]

    if "paths" in spec:
        filtered_paths = {
            path: methods
            for path, methods in spec["paths"].items()
            if any(path.startswith(prefix) or prefix in path
                   for prefix in security_prefixes)
        }
        spec["paths"] = filtered_paths

    return json.dumps(spec, indent=2)


def clean_go_source(content: str) -> str:
    """Extract API-relevant info from Go source files (Dex handlers)."""
    lines = []
    for line in content.split("\n"):
        stripped = line.strip()
        if (stripped.startswith("func ") or
            stripped.startswith("type ") or
            stripped.startswith("//") or
            "HandleFunc" in stripped or
            "Handle(" in stripped or
            "r.Path(" in stripped or
            "router." in stripped or
            stripped.startswith("package ")):
            lines.append(line)
    return "\n".join(lines)


def clean_asciidoc(content: str) -> str:
    """Clean AsciiDoc format (used by Keycloak docs)."""
    lines = []
    for line in content.split("\n"):
        stripped = line.strip()
        if stripped.startswith(("ifdef::", "ifndef::", "endif::", "include::")):
            continue
        if stripped.startswith(":") and "::" in stripped:
            continue  # AsciiDoc attributes
        lines.append(line)
    return "\n".join(lines)


def auto_clean(content: str, source_path: str) -> str:
    """Auto-detect file type and apply appropriate cleaning."""
    lower = source_path.lower()
    if lower.endswith((".mdx", ".md")):
        return clean_mdx(content)
    elif lower.endswith((".html", ".htm")):
        return clean_html(content)
    elif lower.endswith(".json"):
        return clean_openapi_json(content)
    elif lower.endswith(".go"):
        return clean_go_source(content)
    elif lower.endswith(".adoc"):
        return clean_asciidoc(content)
    else:
        return clean_mdx(content)  # Default: try MDX cleaning


# ---------------------------------------------------------------------------
# Fetch with caching
# ---------------------------------------------------------------------------

def _is_cache_fresh(cache_path: Path, max_age: int = CACHE_MAX_AGE_SECONDS) -> bool:
    """Return True if cache file exists and is less than max_age seconds old."""
    if not cache_path.exists():
        return False
    age = time.time() - cache_path.stat().st_mtime
    return age < max_age


def fetch_url(url: str, cache_path: Path, force: bool = False) -> Optional[str]:
    """Fetch URL with file-based caching. Returns content or None on error."""
    import requests

    if not force and _is_cache_fresh(cache_path):
        logger.debug(f"Cache hit: {cache_path}")
        return cache_path.read_text(encoding="utf-8")

    logger.info(f"Fetching: {url}")
    try:
        resp = requests.get(url, timeout=30)
        if resp.status_code == 404:
            logger.warning(f"404 Not Found: {url}")
            return None
        resp.raise_for_status()
        content = resp.text
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_text(content, encoding="utf-8")
        return content
    except Exception as e:
        logger.error(f"Failed to fetch {url}: {e}")
        return None


# ---------------------------------------------------------------------------
# Main fetch pipeline
# ---------------------------------------------------------------------------

def fetch_platform_docs(
    platform: str,
    protocol: str = "oidc_jwt",
    output_dir: str = "src/extraction",
    force: bool = False,
) -> dict:
    """Discover and download ALL documentation for a platform/protocol.

    Returns {"total_files": N, "total_chars": N, "all_docs_path": "path/to/ALL_DOCS.md"}
    """
    config = PLATFORM_DOC_SOURCES.get(platform, {}).get(protocol, {})
    if not config:
        raise ValueError(f"No doc sources configured for {platform}/{protocol}")

    raw_dir = Path(output_dir) / "raw_docs" / platform / protocol
    cleaned_dir = Path(output_dir) / "cleaned_docs" / platform / protocol
    raw_dir.mkdir(parents=True, exist_ok=True)
    cleaned_dir.mkdir(parents=True, exist_ok=True)

    all_files = {}  # filename -> cleaned_content
    github_token = os.environ.get("GITHUB_TOKEN")

    # 1. Discover and download from GitHub repos
    for repo_config in config.get("github_repos", []):
        repo = repo_config["repo"]
        branch = repo_config.get("branch", "main")
        extensions = repo_config.get("extensions", [".mdx", ".md"])

        for dir_path in repo_config["paths"]:
            logger.info(f"Discovering files in {repo}/{dir_path}...")
            files = list_github_directory(repo, dir_path, branch, extensions, github_token)
            logger.info(f"  Found {len(files)} files")

            for file_info in files:
                filename = file_info["path"].replace("/", "_")
                cache_path = raw_dir / filename

                # Download with caching
                content = fetch_url(file_info["download_url"], cache_path, force=force)
                if content:
                    cleaned = auto_clean(content, file_info["path"])
                    if cleaned and len(cleaned.strip()) > 100:  # Skip near-empty files
                        all_files[file_info["path"]] = cleaned
                        (cleaned_dir / filename).write_text(cleaned, encoding="utf-8")

    # 2. Download direct URLs
    for url in config.get("direct_urls", []):
        filename = url.split("/")[-1]
        cache_path = raw_dir / filename
        content = fetch_url(url, cache_path, force=force)
        if content:
            cleaned = auto_clean(content, url)
            if cleaned:
                all_files[url] = cleaned
                (cleaned_dir / filename).write_text(cleaned, encoding="utf-8")

    # 3. Read local paths
    for local_path in config.get("local_paths", []):
        p = Path(local_path)
        if p.is_file():
            content = p.read_text(encoding="utf-8")
            cleaned = auto_clean(content, str(p))
            if cleaned:
                all_files[str(p)] = cleaned
        elif p.is_dir():
            for f in p.rglob("*"):
                if f.is_file() and _matches_extensions(f.name, [".mdx", ".md", ".go", ".json"]):
                    content = f.read_text(encoding="utf-8")
                    cleaned = auto_clean(content, str(f))
                    if cleaned:
                        all_files[str(f)] = cleaned

    # 4. Concatenate ALL cleaned docs into one file, most relevant first.
    # Relevance is measured by how many protocol/identity/policy terms appear in
    # the source path — so jwt.mdx, identity/, kv/ etc. float to the top and are
    # not truncated out of the LLM context window by irrelevant auth-method files.
    def _relevance_score(source: str) -> int:
        s = source.lower()
        score = 0
        # Protocol name terms (e.g. "jwt", "oidc" for oidc_jwt)
        for term in protocol.replace("_", "/").split("/") + [protocol]:
            if term in s:
                score += 100
        # Critical API reference files (endpoints, scopes, claims, user mgmt)
        # These define the actual API surface and MUST be within truncation window
        for term in ["endpoint", "openid", "oauth", "userinfo",
                     "user_service", "user-service", "application_service",
                     "session_service", "idp_service"]:
            if term in s:
                score += 200
        # Generally relevant terms for any IAM fuzzing
        for term in ["identity", "entity", "group", "token", "policy", "polic", "kv",
                     "secret", "alias", "auth", "saml", "ldap", "userpass", "acl",
                     "callback", "connector", "claim", "scope"]:
            if term in s:
                score += 20
        return score

    all_docs_parts = []
    for source, content in sorted(all_files.items(),
                                  key=lambda kv: _relevance_score(kv[0]),
                                  reverse=True):
        all_docs_parts.append(f"\n\n{'='*80}\nSOURCE: {source}\n{'='*80}\n\n{content}")

    all_docs_text = "\n".join(all_docs_parts)
    all_docs_path = cleaned_dir / "ALL_DOCS.md"
    all_docs_path.write_text(all_docs_text, encoding="utf-8")

    total_chars = len(all_docs_text)
    approx_tokens = total_chars // 4

    print(f"\n{'='*60}")
    print(f"Documentation fetch complete for {platform}/{protocol}")
    print(f"  Files discovered: {len(all_files)}")
    print(f"  Total characters: {total_chars:,}")
    print(f"  Approx tokens:    {approx_tokens:,}")
    print(f"  Output: {all_docs_path}")
    print(f"{'='*60}\n")

    if approx_tokens > 350000:
        logger.warning(f"Total docs ({approx_tokens} tokens) may exceed LLM context. "
                       "Consider filtering or splitting.")

    return {
        "total_files": len(all_files),
        "total_chars": total_chars,
        "approx_tokens": approx_tokens,
        "all_docs_path": str(all_docs_path),
        "file_list": list(all_files.keys()),
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    import argparse
    parser = argparse.ArgumentParser(
        description="Fetch platform documentation for VALENCE API extraction"
    )
    parser.add_argument("--platform", required=True,
                        help="Platform name (vault, keycloak, dex)")
    parser.add_argument("--protocol", default="oidc_jwt",
                        help="Protocol (oidc_jwt, saml, ldap)")
    parser.add_argument("--output-dir", default="src/extraction",
                        help="Output directory")
    parser.add_argument("--force", action="store_true",
                        help="Force re-download (ignore cache)")
    parser.add_argument("--list-only", action="store_true",
                        help="Only list discovered files, don't download")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    if args.list_only:
        config = PLATFORM_DOC_SOURCES.get(args.platform, {}).get(args.protocol, {})
        for repo_config in config.get("github_repos", []):
            for dir_path in repo_config["paths"]:
                files = list_github_directory(
                    repo_config["repo"], dir_path,
                    repo_config.get("branch", "main"),
                    repo_config.get("extensions"),
                    os.environ.get("GITHUB_TOKEN")
                )
                for f in files:
                    print(f"  {f['path']} ({f['size']} bytes)")
        return

    result = fetch_platform_docs(
        args.platform, args.protocol, args.output_dir, args.force
    )
    print(f"\nReady for extraction. Next step:")
    print(f"  python -m src.extraction.extract_specs --platform {args.platform} --protocol {args.protocol}")


if __name__ == "__main__":
    main()
