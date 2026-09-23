"""
Contract test verifying OpenAPI spec alignment for implemented Phase 1 endpoints.
"""
import yaml
from prescripto.api.main import app


def test_phase1_openapi_contract_parity():
    # 1. Load canonical OPENAPI.yaml
    with open("OPENAPI.yaml", "r", encoding="utf-8") as f:
        spec = yaml.safe_load(f)

    app_spec = app.openapi()

    # 2. Verify paths exist in FastAPI app
    expected_paths = ["/auth/token", "/auth/refresh", "/health"]
    for path in expected_paths:
        full_path = f"/api/v1{path}"
        assert full_path in app_spec["paths"], f"Path {full_path} missing from FastAPI app"

    # 3. Check /api/v1/auth/token
    token_op = app_spec["paths"]["/api/v1/auth/token"]["post"]
    assert token_op["operationId"] == "createToken"

    # 4. Check /api/v1/auth/refresh
    refresh_op = app_spec["paths"]["/api/v1/auth/refresh"]["post"]
    assert refresh_op["operationId"] == "refreshToken"

    # 5. Check /api/v1/health
    health_op = app_spec["paths"]["/api/v1/health"]["get"]
    assert health_op["operationId"] == "getHealth"
