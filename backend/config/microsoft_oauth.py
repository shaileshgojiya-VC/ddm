"""
Microsoft OAuth configuration.

This module handles Microsoft OAuth configuration including
client credentials, redirect URIs, and tenant-based authorization.
"""

from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings
from pydantic import ConfigDict

from config.env_config import get_settings


class MicrosoftOAuthConfig(BaseSettings):
    """
    Microsoft OAuth configuration settings.

    Attributes:
        CLIENT_ID: Microsoft application client ID
        CLIENT_SECRET: Microsoft application client secret
        REDIRECT_URI: OAuth callback redirect URI
        TENANT_ID: Optional tenant ID for tenant-specific authorization
        AUTHORITY_BASE: Microsoft authority base URL
    """

    CLIENT_ID: str
    CLIENT_SECRET: str
    REDIRECT_URI: str
    TENANT_ID: Optional[str] = None
    AUTHORITY_BASE: str = "https://login.microsoftonline.com"

    model_config = ConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore",
    )

    def get_authority_url(self) -> str:
        """
        Get Microsoft authority URL based on tenant configuration.

        Returns:
            str: Authority URL (common or tenant-specific)
        """
        if self.TENANT_ID:
            return f"{self.AUTHORITY_BASE}/{self.TENANT_ID}"
        return f"{self.AUTHORITY_BASE}/common"

    def get_authorization_url(self, state: str, scopes: list[str]) -> str:
        """
        Generate Microsoft OAuth authorization URL.

        Args:
            state: OAuth state parameter for CSRF protection
            scopes: List of Microsoft Graph API scopes

        Returns:
            str: Complete authorization URL
        """
        authority = self.get_authority_url()
        scope_string = " ".join(scopes)
        redirect_uri_encoded = self.REDIRECT_URI.replace(":", "%3A").replace("/", "%2F")

        return (
            f"{authority}/oauth2/v2.0/authorize?"
            f"client_id={self.CLIENT_ID}&"
            f"response_type=code&"
            f"redirect_uri={redirect_uri_encoded}&"
            f"response_mode=query&"
            f"scope={scope_string}&"
            f"state={state}"
        )

    def get_token_url(self) -> str:
        """
        Get Microsoft token endpoint URL.

        Returns:
            str: Token endpoint URL
        """
        authority = self.get_authority_url()
        return f"{authority}/oauth2/v2.0/token"


@lru_cache()
def get_microsoft_oauth_config() -> MicrosoftOAuthConfig:
    """
    Get cached Microsoft OAuth configuration instance.

    Returns:
        MicrosoftOAuthConfig: Cached configuration instance
    """
    return MicrosoftOAuthConfig()


# Fallback to env_config if microsoft-specific env vars not set
def get_microsoft_config() -> MicrosoftOAuthConfig:
    """
    Get Microsoft OAuth config with fallback to global settings.

    Returns:
        MicrosoftOAuthConfig: Configuration instance
    """
    try:
        return get_microsoft_oauth_config()
    except Exception:
        # Fallback to global settings
        settings = get_settings()
        return MicrosoftOAuthConfig(
            CLIENT_ID=settings.CLIENT_ID or "",
            CLIENT_SECRET=settings.CLIENT_SECRET or "",
            REDIRECT_URI=settings.OUTLOOK_WEBHOOK_URL or "",
            TENANT_ID=settings.TENANT_ID,
        )
