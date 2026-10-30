"""OAuth endpoints, disabled until a provider can be verified safely."""

from fastapi import APIRouter, Depends, HTTPException, Request

from app.services.auth import get_current_user

router = APIRouter(prefix="/api/v1/auth/oauth", tags=["OAuth"])
_UNSUPPORTED_DETAIL = "OAuth/OIDC is not configured with verified providers"


def _oauth_unavailable() -> None:
    """Fail closed rather than issue sessions from unverified provider data."""
    raise HTTPException(status_code=501, detail=_UNSUPPORTED_DETAIL)


@router.get("/{provider}/authorize")
async def oauth_authorize(provider: str, request: Request):
    _oauth_unavailable()


@router.get("/{provider}/callback")
async def oauth_callback(provider: str, code: str, state: str, request: Request):
    _oauth_unavailable()


@router.post("/link")
async def link_oauth_account(
    request: Request,
    provider: str,
    code: str,
    email: str = Depends(get_current_user),
):
    _oauth_unavailable()


@router.delete("/unlink")
async def unlink_oauth_account(
    request: Request,
    provider: str,
    email: str = Depends(get_current_user),
):
    _oauth_unavailable()


@router.get("/accounts")
async def get_linked_oauth_accounts(email: str = Depends(get_current_user)):
    _oauth_unavailable()
