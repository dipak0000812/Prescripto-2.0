"""
Integration tests for Prescription Ingestion and Retrieval API (Phase 2 / Slice 1).
Validates idempotency, format verification, security rules, 404-over-403, and presigned URLs.
"""
import io
import uuid
import pytest
from prescripto.db.models.users import User
from prescripto.db.models.enums import Role
from prescripto.auth.crypto import hash_password


VALID_JPEG_BYTES = b"\xFF\xD8\xFF\xE0\x00\x10JFIF" + b"\x00" * 100
VALID_PNG_BYTES = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR" + b"\x00" * 100
VALID_PDF_BYTES = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog >>\nendobj"
MALICIOUS_PDF_BYTES = b"%PDF-1.4\n<< /S /JavaScript /JS (app.alert('evil');) >>"


def get_auth_header(client, username, password):
    res = client.post("/api/v1/auth/token", data={"username": username, "password": password})
    assert res.status_code == 200
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


def test_upload_valid_prescription_success(client, seeded_users):
    headers = get_auth_header(client, "test_operator", "OperatorPass123!")
    headers["Idempotency-Key"] = f"test-key-{uuid.uuid4()}"

    files = {"file": ("rx_test.jpg", io.BytesIO(VALID_JPEG_BYTES), "image/jpeg")}
    data = {"patient_external_id": "PT-98765"}

    response = client.post("/api/v1/prescriptions", headers=headers, files=files, data=data)
    assert response.status_code == 202
    res_data = response.json()
    assert "prescription_id" in res_data
    assert "analysis_id" in res_data
    assert "X-Request-ID" in response.headers


def test_upload_missing_idempotency_key(client, seeded_users):
    headers = get_auth_header(client, "test_operator", "OperatorPass123!")
    # No Idempotency-Key header provided

    files = {"file": ("rx_test.jpg", io.BytesIO(VALID_JPEG_BYTES), "image/jpeg")}
    response = client.post("/api/v1/prescriptions", headers=headers, files=files)
    assert response.status_code == 400
    res_data = response.json()
    assert res_data["error"]["code"] == "MISSING_IDEMPOTENCY_KEY"


def test_upload_idempotency_replay(client, seeded_users):
    headers = get_auth_header(client, "test_operator", "OperatorPass123!")
    idem_key = f"replay-key-{uuid.uuid4()}"
    headers["Idempotency-Key"] = idem_key

    files1 = {"file": ("rx.jpg", io.BytesIO(VALID_JPEG_BYTES), "image/jpeg")}
    res1 = client.post("/api/v1/prescriptions", headers=headers, files=files1)
    assert res1.status_code == 202
    data1 = res1.json()

    # Replay request with same key and identical file content
    files2 = {"file": ("rx.jpg", io.BytesIO(VALID_JPEG_BYTES), "image/jpeg")}
    res2 = client.post("/api/v1/prescriptions", headers=headers, files=files2)
    assert res2.status_code == 202
    data2 = res2.json()

    # Both IDs must match exactly
    assert data1["prescription_id"] == data2["prescription_id"]
    assert data1["analysis_id"] == data2["analysis_id"]


def test_upload_idempotency_conflict(client, seeded_users):
    headers = get_auth_header(client, "test_operator", "OperatorPass123!")
    idem_key = f"conflict-key-{uuid.uuid4()}"
    headers["Idempotency-Key"] = idem_key

    # First upload: JPEG
    files1 = {"file": ("rx.jpg", io.BytesIO(VALID_JPEG_BYTES), "image/jpeg")}
    res1 = client.post("/api/v1/prescriptions", headers=headers, files=files1)
    assert res1.status_code == 202

    # Second upload: Same Idempotency-Key, different file content (PNG)
    files2 = {"file": ("rx.png", io.BytesIO(VALID_PNG_BYTES), "image/png")}
    res2 = client.post("/api/v1/prescriptions", headers=headers, files=files2)
    assert res2.status_code == 409
    assert res2.json()["error"]["code"] == "IDEMPOTENCY_KEY_CONFLICT"


def test_upload_unsupported_media_type(client, seeded_users):
    headers = get_auth_header(client, "test_operator", "OperatorPass123!")
    headers["Idempotency-Key"] = f"unsupported-{uuid.uuid4()}"

    plain_text = b"Prescription: Paracetamol 500mg TDS"
    files = {"file": ("rx.txt", io.BytesIO(plain_text), "text/plain")}
    res = client.post("/api/v1/prescriptions", headers=headers, files=files)
    assert res.status_code == 415
    assert res.json()["error"]["code"] == "UNSUPPORTED_MEDIA_TYPE"


def test_upload_pdf_active_content_rejected(client, seeded_users):
    headers = get_auth_header(client, "test_operator", "OperatorPass123!")
    headers["Idempotency-Key"] = f"malicious-pdf-{uuid.uuid4()}"

    files = {"file": ("rx.pdf", io.BytesIO(MALICIOUS_PDF_BYTES), "application/pdf")}
    res = client.post("/api/v1/prescriptions", headers=headers, files=files)
    assert res.status_code == 422
    assert res.json()["error"]["code"] == "PDF_ACTIVE_CONTENT_REJECTED"


def test_get_prescription_detail_success(client, seeded_users):
    headers = get_auth_header(client, "test_operator", "OperatorPass123!")
    headers["Idempotency-Key"] = f"detail-test-{uuid.uuid4()}"

    files = {"file": ("rx.jpg", io.BytesIO(VALID_JPEG_BYTES), "image/jpeg")}
    upload_res = client.post("/api/v1/prescriptions", headers=headers, files=files)
    assert upload_res.status_code == 202
    doc_id = upload_res.json()["prescription_id"]

    # Retrieve document detail
    get_res = client.get(f"/api/v1/prescriptions/{doc_id}", headers=headers)
    assert get_res.status_code == 200
    detail = get_res.json()
    assert detail["prescription_id"] == doc_id
    assert detail["status"] == "UPLOADED"
    assert detail["mime_type"] == "image/jpeg"
    assert detail["image_url"] is not None
    assert "https://mock-storage.prescripto.local" in detail["image_url"]
    assert len(detail["analyses"]) >= 1


def test_get_prescription_404_over_403_security_rule(client, db_session, seeded_users):
    # Operator 1 uploads a prescription
    headers1 = get_auth_header(client, "test_operator", "OperatorPass123!")
    headers1["Idempotency-Key"] = f"scoped-{uuid.uuid4()}"
    files = {"file": ("rx.jpg", io.BytesIO(VALID_JPEG_BYTES), "image/jpeg")}
    upload_res = client.post("/api/v1/prescriptions", headers=headers1, files=files)
    doc_id = upload_res.json()["prescription_id"]

    # Seed Operator 2
    op2 = User(
        id=uuid.uuid4(),
        username="other_operator",
        email="other@prescripto.local",
        hashed_password=hash_password("OtherPass123!"),
        role=Role.OPERATOR.value,
        is_active=True,
    )
    db_session.add(op2)
    db_session.commit()

    headers2 = get_auth_header(client, "other_operator", "OtherPass123!")

    # Operator 2 tries to view Operator 1's prescription
    # Enforces 404-over-403: Must return 404 RESOURCE_NOT_FOUND, NOT 403
    res = client.get(f"/api/v1/prescriptions/{doc_id}", headers=headers2)
    assert res.status_code == 404
    assert res.json()["error"]["code"] == "RESOURCE_NOT_FOUND"


def test_admin_and_reviewer_can_access_any_prescription(client, seeded_users):
    # Operator uploads prescription
    op_headers = get_auth_header(client, "test_operator", "OperatorPass123!")
    op_headers["Idempotency-Key"] = f"admin-view-{uuid.uuid4()}"
    files = {"file": ("rx.jpg", io.BytesIO(VALID_JPEG_BYTES), "image/jpeg")}
    upload_res = client.post("/api/v1/prescriptions", headers=op_headers, files=files)
    doc_id = upload_res.json()["prescription_id"]

    # Reviewer views prescription
    rev_headers = get_auth_header(client, "test_reviewer", "ReviewerPass123!")
    rev_res = client.get(f"/api/v1/prescriptions/{doc_id}", headers=rev_headers)
    assert rev_res.status_code == 200
    assert rev_res.json()["prescription_id"] == doc_id

    # Admin views prescription
    adm_headers = get_auth_header(client, "test_admin", "AdminPass123!")
    adm_res = client.get(f"/api/v1/prescriptions/{doc_id}", headers=adm_headers)
    assert adm_res.status_code == 200
    assert adm_res.json()["prescription_id"] == doc_id


def test_list_prescriptions_scoped_and_paginated(client, db_session, seeded_users):
    op1_headers = get_auth_header(client, "test_operator", "OperatorPass123!")

    # Operator 1 uploads 2 prescriptions
    for i in range(2):
        op1_headers["Idempotency-Key"] = f"list-op1-{i}-{uuid.uuid4()}"
        client.post(
            "/api/v1/prescriptions",
            headers=op1_headers,
            files={"file": (f"rx{i}.jpg", io.BytesIO(VALID_JPEG_BYTES), "image/jpeg")},
        )

    # Operator 1 lists prescriptions
    res_op1 = client.get("/api/v1/prescriptions?page=1&page_size=10", headers=op1_headers)
    assert res_op1.status_code == 200
    data_op1 = res_op1.json()
    assert data_op1["total"] >= 2
    assert len(data_op1["items"]) >= 2
    assert data_op1["page"] == 1
    assert data_op1["page_size"] == 10

    # Test pagination page_size=1
    res_page1 = client.get("/api/v1/prescriptions?page=1&page_size=1", headers=op1_headers)
    assert res_page1.status_code == 200
    assert len(res_page1.json()["items"]) == 1


def test_get_prescription_not_found(client, seeded_users):
    headers = get_auth_header(client, "test_admin", "AdminPass123!")
    non_existent = uuid.uuid4()
    res = client.get(f"/api/v1/prescriptions/{non_existent}", headers=headers)
    assert res.status_code == 404
    assert res.json()["error"]["code"] == "RESOURCE_NOT_FOUND"


def test_get_prescription_malformed_uuid(client, seeded_users):
    headers = get_auth_header(client, "test_operator", "OperatorPass123!")
    res = client.get("/api/v1/prescriptions/not-a-valid-uuid", headers=headers)
    assert res.status_code == 400
    assert res.json()["error"]["code"] == "MALFORMED_REQUEST"
