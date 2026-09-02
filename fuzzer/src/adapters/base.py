"""Abstract base class for platform adapters."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime

from src.models.types import AuthResult, Credential, Platform, Protocol


class BrokerAdapter(ABC):
    """Base adapter that each platform (Vault, Keycloak, Dex) must implement."""

    def __init__(self, platform: Platform, config: dict):
        self.platform = platform
        self.config = config

    @abstractmethod
    def setup(self) -> None:
        """Initialize platform connection. Verify it is running."""

    @abstractmethod
    def health_check(self) -> bool:
        """Return True if the platform is reachable and healthy."""

    @abstractmethod
    def configure_auth_method(self, protocol: Protocol, auth_config: dict) -> None:
        """Configure an authentication method on the platform."""

    @abstractmethod
    def authenticate(self, credential: Credential) -> AuthResult:
        """Submit a credential to the platform and return the result."""

    @abstractmethod
    def get_token_metadata(self, token: str) -> dict:
        """Parse and return metadata from a downstream token."""

    @abstractmethod
    def reset_state(self) -> None:
        """Reset platform state (clear caches, sessions, nonces)."""

    @abstractmethod
    def get_server_logs(self, since: datetime) -> list[str]:
        """Retrieve server logs since a given timestamp."""

    @property
    @abstractmethod
    def supported_protocols(self) -> list[Protocol]:
        """Return list of protocols this adapter supports."""
