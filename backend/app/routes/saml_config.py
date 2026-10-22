"""SAML configuration helper and examples."""

from typing import Optional
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(tags=["SAML Config"])


class SAMLConfig(BaseModel):
    """SAML configuration model."""
    entity_id: str
    metadata_url: str
    cert_path: str
    key_path: str
    sso_url: str
    slo_url: Optional[str] = None


# Example configurations for common IdPs
EXAMPLE_CONFIGS = {
    "azure_ad": {
        "name": "Azure Active Directory",
        "entity_id": "https://login.microsoftonline.com/{tenant_id}/v2.0",
        "metadata_url": "https://login.microsoftonline.com/{tenant_id}/federationmetadata/2007-06/federationmetadata.xml",
        "cert_path": "/path/to/azure_cert.pem",
        "key_path": "/path/to/azure_key.pem",
        "sso_url": "https://login.microsoftonline.com/{tenant_id}/saml2",
        "slo_url": "https://login.microsoftonline.com/{tenant_id}/saml2",
        "notes": [
            "Replace {tenant_id} with your Azure AD tenant ID",
            "Download the federation metadata from Azure AD portal",
            "Extract the certificate from the metadata XML",
        ]
    },
    "okta": {
        "name": "Okta",
        "entity_id": "http://www.okta.com/{org_id}",
        "metadata_url": "https://{org}.okta.com/app/{app_id}/sso/saml/metadata",
        "cert_path": "/path/to/okta_cert.pem",
        "key_path": "/path/to/okta_key.pem",
        "sso_url": "https://{org}.okta.com/app/{app_id}/sso/saml/sso",
        "slo_url": "https://{org}.okta.com/app/{app_id}/sso/saml/logout",
        "notes": [
            "Replace {org} with your Okta organization name",
            "Replace {app_id} with your app ID",
            "Create a new SAML app in Okta dashboard",
        ]
    },
    "auth0": {
        "name": "Auth0",
        "entity_id": "urn:{domain}",
        "metadata_url": "https://{domain}/samlp/metadata/{client_id}",
        "cert_path": "/path/to/auth0_cert.pem",
        "key_path": "/path/to/auth0_key.pem",
        "sso_url": "https://{domain}/samlp/{client_id}/sso",
        "slo_url": "https://{domain}/samlp/{client_id}/logout",
        "notes": [
            "Replace {domain} with your Auth0 domain",
            "Replace {client_id} with your application client ID",
            "Enable SAML in your Auth0 application settings",
        ]
    },
    "keycloak": {
        "name": "Keycloak",
        "entity_id": "https://{keycloak_host}/realms/{realm}",
        "metadata_url": "https://{keycloak_host}/realms/{realm}/protocol/saml/descriptor",
        "cert_path": "/path/to/keycloak_cert.pem",
        "key_path": "/path/to/keycloak_key.pem",
        "sso_url": "https://{keycloak_host}/realms/{realm}/protocol/saml",
        "slo_url": "https://{keycloak_host}/realms/{realm}/protocol/saml",
        "notes": [
            "Replace {keycloak_host} with your Keycloak server host",
            "Replace {realm} with your realm name",
            "Create a new SAML client in Keycloak admin console",
        ]
    },
}


def get_example_config(provider: str) -> Optional[SAMLConfig]:
    """Get example configuration for a specific IdP."""
    config = EXAMPLE_CONFIGS.get(provider.lower())
    if config:
        return SAMLConfig(**config)
    return None


def list_supported_idps() -> list[str]:
    """List all supported IdP providers."""
    return list(EXAMPLE_CONFIGS.keys())


@router.get("/providers")
async def list_saml_providers():
    """List all supported SAML IdP providers."""
    return {"providers": list(EXAMPLE_CONFIGS.keys())}


@router.get("/config/{provider}")
async def get_saml_config(provider: str):
    """Get example configuration for a specific IdP."""
    config = EXAMPLE_CONFIGS.get(provider.lower())
    if not config:
        return {"error": f"Provider '{provider}' not found"}
    return config


def generate_env_template(provider: str) -> str:
    """Generate .env template for a specific IdP."""
    config = EXAMPLE_CONFIGS.get(provider.lower())
    if not config:
        return ""
    
    template = f"""# SAML 2.0 SSO Configuration for {config['name']}
ENABLE_SAML=true
SAML_ENTITY_ID={config['entity_id']}
SAML_METADATA_URL={config['metadata_url']}
SAML_CERT_PATH={config['cert_path']}
SAML_KEY_PATH={config['key_path']}

# Notes:
"""
    for note in config.get('notes', []):
        template += f"# - {note}\n"
    
    return template
