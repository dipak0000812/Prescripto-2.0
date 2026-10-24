"""
Auth Router: /auth/token and /auth/refresh endpoints.
"""
from fastapi import APIRouter, Depends, Form
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from prescripto.db.session import get_db
from prescripto.auth.service import AuthService
from prescripto.api.v1.schemas.auth import TokenResponse, RefreshTokenRequest

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/token",
    response_model=TokenResponse,
    summary="Obtain a JWT access/refresh token pair",
    operation_id="createToken",
)
def create_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
) -> TokenResponse:
    """OAuth2 password login granting RS256 access and refresh token pair."""
    user = AuthService.authenticate_user(db, form_data.username, form_data.password)
    tokens = AuthService.create_token_pair(user)
    return TokenResponse(**tokens)


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Exchange a refresh token for a new access token",
    operation_id="refreshToken",
)
def refresh_token(
    request: RefreshTokenRequest,
    db: Session = Depends(get_db),
) -> TokenResponse:
    """Exchanges a valid refresh token for a new token pair while revoking the old token in blocklist."""
    tokens = AuthService.refresh_session(db, request.refresh_token)
    return TokenResponse(**tokens)
