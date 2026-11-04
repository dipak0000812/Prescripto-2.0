import pytest
from fastapi.testclient import TestClient
from prescripto.db.models.patient import Patient
from prescripto.db.models.document import PrescriptionDocument
from prescripto.db.models.analysis import Analysis
from prescripto.db.models.medication import PrescriptionMedication
from prescripto.db.models.review import Review
from prescripto.db.models.users import User
from prescripto.auth.crypto import create_access_token
from prescripto.db.base import utc_now
import uuid


def test_patients_search_and_timeline(client, seeded_users, db_session):
    # Ensure a patient exists
    p = db_session.query(Patient).filter(Patient.patient_id == "PAT-TEST-99").first()
    if not p:
        p = Patient(
            id=uuid.uuid4(),
            patient_id="PAT-TEST-99",
            name="Siddharth Gupta",
            phone_number="9988776655",
            age=40,
            gender="Male",
            blood_group="O+",
            allergies="Ciprofloxacin",
            medical_history="Asthma",
            created_at=utc_now(),
            updated_at=utc_now(),
        )
        db_session.add(p)
        db_session.flush()

    # Link a prescription document and analysis to this patient
    uploader = seeded_users["operator"]
    doc = PrescriptionDocument(
        id=uuid.uuid4(),
        uploader_id=uploader.id,
        patient_ref="PAT-TEST-99",
        storage_key="prescriptions/test/original.png",
        file_hash_sha256="fakehash998877",
        mime_type="image/png",
        file_size_bytes=1024,
        status="UPLOADED",
        uploaded_at=utc_now(),
    )
    db_session.add(doc)
    db_session.flush()

    from prescripto.db.models.registry import ModelVersion
    active_model = db_session.query(ModelVersion).first()
    if not active_model:
        active_model = ModelVersion(
            id=uuid.uuid4(),
            model_name="test-ocr",
            model_version="1.0.0",
            checkpoint_sha256="fake_sha",
            artifact_storage_key="models/test",
            framework="ONNX",
            license="Apache-2.0",
            registered_at=utc_now(),
        )
        db_session.add(active_model)
        db_session.flush()

    analysis = Analysis(
        id=uuid.uuid4(),
        document_id=doc.id,
        status="COMPLETED",
        pipeline_version="1.0.0",
        model_snapshot_id=active_model.id,
        review_required=False,
        review_reasons=[],
        created_at=utc_now(),
    )
    db_session.add(analysis)
    db_session.flush()

    med = PrescriptionMedication(
        id=uuid.uuid4(),
        analysis_id=analysis.id,
        line_index=0,
        name_raw="Amoxicillin",
        name_state="CLEAR",
        strength_raw="500mg",
        strength_state="CLEAR",
        frequency_raw="TDS",
        frequency_state="CLEAR",
    )
    db_session.add(med)
    db_session.commit()

    # 1. Login as reviewer/doctor
    login_res = client.post(
        "/api/v1/auth/token",
        data={"username": "test_reviewer", "password": "ReviewerPass123!"},
    )
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Search by name
    res_search = client.get("/api/v1/patients/search?q=Siddharth", headers=headers)
    assert res_search.status_code == 200
    results = res_search.json()
    assert len(results) >= 1
    assert any(pt["patient_id"] == "PAT-TEST-99" for pt in results)

    # 3. Search by patient ID
    res_id = client.get("/api/v1/patients/search?q=PAT-TEST-99", headers=headers)
    assert res_id.status_code == 200
    assert len(res_id.json()) == 1

    # 4. Get full timeline
    res_tl = client.get("/api/v1/patients/PAT-TEST-99", headers=headers)
    assert res_tl.status_code == 200
    data = res_tl.json()
    assert data["name"] == "Siddharth Gupta"
    assert data["allergies"] == "Ciprofloxacin"
    assert data["total_prescriptions"] >= 1
    assert len(data["timeline"]) >= 1
    assert data["timeline"][0]["document_id"] == str(doc.id)
    assert any(m["name"] == "Amoxicillin" for m in data["timeline"][0]["medications"])
    assert any(m["name"] == "Amoxicillin" for m in data["active_medications"])


def test_patient_timeline_with_real_review_row(client, seeded_users, db_session):
    """Test 2: Ensure timeline builds correctly with a real Review row."""
    reviewer = seeded_users["reviewer"]
    p_id = f"PAT-REV-{uuid.uuid4().hex[:6]}"
    patient = Patient(
        id=uuid.uuid4(),
        patient_id=p_id,
        name="Review Test Patient",
        phone_number="9123456780",
        created_at=utc_now(),
        updated_at=utc_now(),
    )
    db_session.add(patient)
    db_session.flush()

    doc = PrescriptionDocument(
        id=uuid.uuid4(),
        uploader_id=reviewer.id,
        patient_ref=p_id,
        storage_key="prescriptions/rev/original.png",
        file_hash_sha256="revhash12345",
        mime_type="image/png",
        file_size_bytes=1024,
        status="UPLOADED",
        uploaded_at=utc_now(),
    )
    db_session.add(doc)
    db_session.flush()

    from prescripto.db.models.registry import ModelVersion
    active_model = db_session.query(ModelVersion).first()
    if not active_model:
        active_model = ModelVersion(
            id=uuid.uuid4(),
            model_name="test-ocr",
            model_version="1.0.0",
            checkpoint_sha256="fake_sha",
            artifact_storage_key="models/test",
            framework="ONNX",
            license="Apache-2.0",
            registered_at=utc_now(),
        )
        db_session.add(active_model)
        db_session.flush()

    analysis = Analysis(
        id=uuid.uuid4(),
        document_id=doc.id,
        status="COMPLETED",
        pipeline_version="1.0.0",
        model_snapshot_id=active_model.id,
        created_at=utc_now(),
    )
    db_session.add(analysis)
    db_session.flush()

    real_review = Review(
        id=uuid.uuid4(),
        analysis_id=analysis.id,
        reviewer_id=reviewer.id,
        status="SUBMITTED",
        notes="Dosage verified against formulary",
        submitted_at=utc_now(),
        created_at=utc_now(),
    )
    db_session.add(real_review)
    db_session.commit()

    token, _ = create_access_token(user_id=reviewer.id, username=reviewer.username, role=reviewer.role)
    res = client.get(f"/api/v1/patients/{p_id}", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    timeline = res.json()["timeline"]
    assert len(timeline) >= 1
    reviews = timeline[0]["clinical_reviews"]
    assert len(reviews) == 1
    assert reviews[0]["action"] == "SUBMITTED"
    assert reviews[0]["notes"] == "Dosage verified against formulary"
    assert "reviewed_at" in reviews[0]


def test_patients_search_role_enforcement(client, seeded_users):
    """Test 3a: search_patients requires REVIEWER or ADMIN role."""
    operator = seeded_users["operator"]
    op_token, _ = create_access_token(user_id=operator.id, username=operator.username, role=operator.role)

    # Operator should be rejected with 403 INSUFFICIENT_ROLE
    res_denied = client.get(
        "/api/v1/patients/search?q=Test",
        headers={"Authorization": f"Bearer {op_token}"},
    )
    assert res_denied.status_code == 403
    body = res_denied.json()
    assert body["error"]["code"] == "INSUFFICIENT_ROLE"

    # Reviewer should be allowed
    reviewer = seeded_users["reviewer"]
    rev_token, _ = create_access_token(user_id=reviewer.id, username=reviewer.username, role=reviewer.role)
    res_allowed = client.get(
        "/api/v1/patients/search?q=Test",
        headers={"Authorization": f"Bearer {rev_token}"},
    )
    assert res_allowed.status_code == 200


def test_patient_timeline_access_control(client, seeded_users, db_session):
    """Test 3b: get_patient_timeline allows REVIEWER/ADMIN or own PATIENT; rejects others with 403."""
    # Create patient user and linked patient record
    patient_user = User(
        id=uuid.uuid4(),
        username=f"pt_user_{uuid.uuid4().hex[:6]}",
        email=f"pt_{uuid.uuid4().hex[:6]}@example.com",
        hashed_password="pw",
        role="OPERATOR",
        is_active=True,
    )
    other_user = User(
        id=uuid.uuid4(),
        username=f"other_{uuid.uuid4().hex[:6]}",
        email=f"other_{uuid.uuid4().hex[:6]}@example.com",
        hashed_password="pw",
        role="OPERATOR",
        is_active=True,
    )
    db_session.add_all([patient_user, other_user])
    db_session.flush()

    p_id = f"PAT-OWN-{uuid.uuid4().hex[:6]}"
    patient = Patient(
        id=uuid.uuid4(),
        patient_id=p_id,
        user_id=patient_user.id,
        name="Self Patient",
        phone_number="9876543210",
        created_at=utc_now(),
        updated_at=utc_now(),
    )
    db_session.add(patient)
    db_session.commit()

    pt_token, _ = create_access_token(user_id=patient_user.id, username=patient_user.username, role=patient_user.role)
    other_token, _ = create_access_token(user_id=other_user.id, username=other_user.username, role=other_user.role)
    rev_token, _ = create_access_token(user_id=seeded_users["reviewer"].id, username=seeded_users["reviewer"].username, role=seeded_users["reviewer"].role)

    # 1. Unlinked operator/patient -> 403 INSUFFICIENT_ROLE
    res_denied = client.get(f"/api/v1/patients/{p_id}", headers={"Authorization": f"Bearer {other_token}"})
    assert res_denied.status_code == 403
    assert res_denied.json()["error"]["code"] == "INSUFFICIENT_ROLE"

    # 2. Linked own patient user -> 200 OK
    res_own = client.get(f"/api/v1/patients/{p_id}", headers={"Authorization": f"Bearer {pt_token}"})
    assert res_own.status_code == 200
    assert res_own.json()["patient_id"] == p_id

    # 3. Reviewer -> 200 OK
    res_rev = client.get(f"/api/v1/patients/{p_id}", headers={"Authorization": f"Bearer {rev_token}"})
    assert res_rev.status_code == 200
    assert res_rev.json()["patient_id"] == p_id
