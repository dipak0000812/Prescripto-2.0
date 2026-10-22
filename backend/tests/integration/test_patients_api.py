import pytest
from fastapi.testclient import TestClient
from prescripto.db.models.patient import Patient
from prescripto.db.models.document import PrescriptionDocument
from prescripto.db.models.analysis import Analysis
from prescripto.db.models.medication import PrescriptionMedication
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
