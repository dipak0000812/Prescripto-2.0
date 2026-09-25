"""
FastAPI Authentication and RBAC Security Dependencies.
"""
import uuid
from typing import Callable, Sequence
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
import jwt

from prescripto.db.session import get_db
from prescripto.db.models.users import User
from prescripto.db.models.enums import Role
from prescripto.auth.crypto import decode_token
from prescripto.auth.exceptions import (
    InvalidCredentialsException,
    TokenExpiredException,
    InsufficientRoleException,
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Extracts and validates the current user from the RS256 Bearer JWT."""
    try:
        payload = decode_token(token)
    except jwt.ExpiredSignatureError:
        raise TokenExpiredException()
    except jwt.InvalidTokenError:
        raise InvalidCredentialsException()

    if payload.get("type") != "access":
        raise InvalidCredentialsException("Invalid token type")

    user_id_str = payload.get("sub")
    if not user_id_str:
        raise InvalidCredentialsException("Token missing subject identifier")

    try:
        user_uuid = uuid.UUID(user_id_str)
    except ValueError:
        raise InvalidCredentialsException("Malformed user identifier")

    user = db.query(User).filter(User.id == user_uuid, User.is_active == True).first()
    if not user:
        raise InvalidCredentialsException("User inactive or no longer exists")

    return user


def require_role(*allowed_roles: Role) -> Callable[[User], User]:
    """Dependency factory enforcing Role-Based Access Control (RBAC)."""
    allowed_values = {role.value for role in allowed_roles}
    # ADMIN role implicitly has all permissions
    allowed_values.add(Role.ADMIN.value)

    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_values:
            raise InsufficientRoleException(
                f"Role '{current_user.role}' is not authorized. Allowed: {', '.join(allowed_values)}"
            )
        return current_user

    return role_checker
