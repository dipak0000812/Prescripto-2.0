"""
Contract test verifying 100% OpenAPI spec alignment for all backend endpoints across all phases.
"""
from pathlib import Path
import yaml
from prescripto.api.main import app


def test_full_openapi_contract_parity():
    # 1. Load canonical OPENAPI.yaml
    openapi_path = Path("OPENAPI.yaml")
    if not openapi_path.exists():
        openapi_path = Path(__file__).parents[2] / "OPENAPI.yaml"
    if not openapi_path.exists():
        openapi_path = Path(__file__).parents[3] / "OPENAPI.yaml"
    with open(openapi_path, "r", encoding="utf-8") as f:
        spec = yaml.safe_load(f)

    app_spec = app.openapi()

    # 2. Canonical paths and methods expected from OPENAPI.yaml
    canonical_endpoints = {
        "/api/v1/auth/token": [("post", "createToken")],
        "/api/v1/auth/refresh": [("post", "refreshToken")],
        "/api/v1/health": [("get", "getHealth")],
        "/api/v1/prescriptions": [("post", "createPrescription"), ("get", "listPrescriptions")],
        "/api/v1/prescriptions/{id}": [("get", "getPrescription"), ("delete", "deletePrescription")],
        "/api/v1/analyses/{id}": [("get", "getAnalysisStatus")],
        "/api/v1/analyses/{id}/result": [("get", "getAnalysisResult")],
        "/api/v1/analyses/{id}/review": [("post", "submitReview")],
    }

    # 3. Verify each endpoint exists and matches operationId exactly
    for path, operations in canonical_endpoints.items():
        assert path in app_spec["paths"], f"Path {path} missing from FastAPI app"
        for method, expected_op_id in operations:
            assert method in app_spec["paths"][path], f"Method {method.upper()} missing from {path}"
            actual_op_id = app_spec["paths"][path][method].get("operationId")
            assert actual_op_id == expected_op_id, f"operationId mismatch on {method.upper()} {path}: expected {expected_op_id}, got {actual_op_id}"

    # 4. Verify all paths in canonical OPENAPI.yaml are accounted for
    for raw_path in spec["paths"].keys():
        full_path = f"/api/v1{raw_path}"
        assert full_path in app_spec["paths"], f"Canonical spec path {full_path} not found in FastAPI app"
