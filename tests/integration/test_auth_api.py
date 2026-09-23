"""
Integration tests for /auth endpoints and RBAC guards.
"""
from fastapi import Depends
from prescripto.api.main import app
from prescripto.auth.dependencies import require_role
from prescripto.db.models.enums import Role
from prescripto.db.models.users import User

# Register a temporary test route to test require_role
@app.get("/test/reviewer-only")
def reviewer_only_endpoint(user: User = Depends(require_role(Role.REVIEWER))):
    return {"message": f"Welcome reviewer {user.username}"}


def test_login_success(client, seeded_users):
    response = client.post(
        "/api/v1/auth/token",
        data={"username": "test_operator", "password": "OperatorPass123!"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"
    assert data["expires_in"] == 900
    assert "X-Request-ID" in response.headers


def test_login_invalid_credentials(client, seeded_users):
    response = client.post(
        "/api/v1/auth/token",
        data={"username": "test_operator", "password": "WrongPassword!"},
    )
    assert response.status_code == 401
    data = response.json()
    assert data["error"]["code"] == "INVALID_CREDENTIALS"
    assert "request_id" in data["error"]


def test_refresh_token_lifecycle_and_revocation(client, seeded_users):
    # 1. Login
    login_resp = client.post(
        "/api/v1/auth/token",
        data={"username": "test_operator", "password": "OperatorPass123!"},
    )
    refresh_token = login_resp.json()["refresh_token"]

    # 2. Exchange refresh token
    refresh_resp = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert refresh_resp.status_code == 200
    new_data = refresh_resp.json()
    assert "access_token" in new_data
    assert "refresh_token" in new_data

    # 3. Attempting to reuse the revoked refresh token must return 401 TOKEN_REVOKED
    reused_resp = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert reused_resp.status_code == 401
    assert reused_resp.json()["error"]["code"] == "TOKEN_REVOKED"


def test_rbac_guard_blocks_unauthorized_role(client, seeded_users):
    # Operator logs in
    op_login = client.post(
        "/api/v1/auth/token",
        data={"username": "test_operator", "password": "OperatorPass123!"},
    )
    op_token = op_login.json()["access_token"]

    # Operator hits reviewer-only route -> 403 INSUFFICIENT_ROLE
    resp = client.get(
        "/test/reviewer-only",
        headers={"Authorization": f"Bearer {op_token}"},
    )
    assert resp.status_code == 403
    assert resp.json()["error"]["code"] == "INSUFFICIENT_ROLE"

    # Reviewer logs in
    rev_login = client.post(
        "/api/v1/auth/token",
        data={"username": "test_reviewer", "password": "ReviewerPass123!"},
    )
    rev_token = rev_login.json()["access_token"]

    # Reviewer hits reviewer-only route -> 200 OK
    resp_ok = client.get(
        "/test/reviewer-only",
        headers={"Authorization": f"Bearer {rev_token}"},
    )
    assert resp_ok.status_code == 200
    assert resp_ok.json()["message"] == "Welcome reviewer test_reviewer"
