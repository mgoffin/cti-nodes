"""OIDC provider configurations for multi-provider SSO support."""

from dataclasses import dataclass
from typing import Literal


@dataclass
class OIDCProvider:
    """Configuration for an OIDC provider."""

    name: str
    authorization_endpoint: str
    token_endpoint: str
    userinfo_endpoint: str
    scopes: str
    username_claim: str = "preferred_username"  # JWT claim to use for username
    email_claim: str = "email"
    display_name_claim: str = "name"


def get_oidc_provider(
    provider_name: Literal["duo", "okta", "azure", "google"],
    base_url: str = "",
) -> OIDCProvider:
    """
    Get OIDC configuration for a specific provider.

    Args:
        provider_name: The SSO provider identifier
        base_url: Provider-specific base URL (e.g., https://api-xxx.duosecurity.com)

    Returns:
        OIDCProvider with endpoint URLs and configuration

    Raises:
        ValueError: If provider is not supported
    """
    if provider_name == "duo":
        return OIDCProvider(
            name="Duo",
            authorization_endpoint=f"{base_url}/oauth/v1/authorize",
            token_endpoint=f"{base_url}/oauth/v1/token",
            userinfo_endpoint=f"{base_url}/oauth/v1/userinfo",
            scopes="openid profile email",
            username_claim="preferred_username",
            email_claim="email",
            display_name_claim="name",
        )

    elif provider_name == "okta":
        return OIDCProvider(
            name="Okta",
            authorization_endpoint=f"{base_url}/oauth2/v1/authorize",
            token_endpoint=f"{base_url}/oauth2/v1/token",
            userinfo_endpoint=f"{base_url}/oauth2/v1/userinfo",
            scopes="openid profile email",
            username_claim="preferred_username",
            email_claim="email",
            display_name_claim="name",
        )

    elif provider_name == "azure":
        # base_url should be: https://login.microsoftonline.com/{tenant-id}/v2.0
        return OIDCProvider(
            name="Azure AD",
            authorization_endpoint=f"{base_url}/authorize",
            token_endpoint=f"{base_url}/token",
            userinfo_endpoint="https://graph.microsoft.com/oidc/userinfo",
            scopes="openid profile email",
            username_claim="preferred_username",
            email_claim="email",
            display_name_claim="name",
        )

    elif provider_name == "google":
        return OIDCProvider(
            name="Google",
            authorization_endpoint="https://accounts.google.com/o/oauth2/v2/auth",
            token_endpoint="https://oauth2.googleapis.com/token",
            userinfo_endpoint="https://openidconnect.googleapis.com/v1/userinfo",
            scopes="openid profile email",
            username_claim="email",  # Google uses email as username
            email_claim="email",
            display_name_claim="name",
        )

    else:
        raise ValueError(
            f"Unsupported SSO provider: {provider_name}. "
            f"Supported providers: duo, okta, azure, google"
        )
