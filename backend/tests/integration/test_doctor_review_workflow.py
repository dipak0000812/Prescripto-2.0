"""
Integration test for Doctor Medication Editing and Clinical Review Sign-off.
Tests:
- PATCH /api/v1/analyses/{id}/medications (doctor correction)
- Automatic normalization & safety re-screening upon edit
- POST /api/v1/analyses/{id}/review (physician sign-off)
"""
import uuid
import pytest
from prescripto.db.base import utc_now
from prescripto.db.models.document import PrescriptionDocument
from prescripto.db.models.analysis import Analysis
from prescripto.db.models.medication import PrescriptionMedication, MedicationCandidate
from prescripto.db.models.registry import ModelVersion
from prescripto.auth.crypto import create_access_token


def test_doctor_medication_editing_and_review_signoff(client, seeded_users, db_session):
    # 1. Setup document & model version
    uploader = seeded_users["operator"]
    doc = PrescriptionDocument(
        id=uuid.uuid4(),
        uploader_id=uploader.id,
        patient_ref="PAT-1001",
        storage_key="prescriptions/test_edit.png",
        file_hash_sha256="abc456edithash",
        mime_type="image/png",
        file_size_bytes=2048,
        status="UPLOADED",
        uploaded_at=utc_now(),
    )
    db_session.add(doc)

    model = ModelVersion(
        id=uuid.uuid4(),
        model_name="prescripto-v1",
        model_version="1.0.0",
        checkpoint_sha256="0" * 64,
        artifact_storage_key="models/v1.pt",
        framework="PyTorch",
        license="COMMERCIAL_PERMISSIVE",
    )
    db_session.add(model)
    db_session.flush()

    # 2. Setup analysis in REQUIRES_REVIEW state
    analysis = Analysis(
        id=uuid.uuid4(),
        document_id=doc.id,
        model_snapshot_id=model.id,
        status="REQUIRES_REVIEW",
        pipeline_version="1.0.0",
        review_required=True,
        review_reasons=["AMBIGUOUS_MEDICATION: Line 1 has unresolved text."],
        created_at=utc_now(),
    )
    db_session.add(analysis)
    db_session.flush()

    # 3. Add ambiguous/misread medication line
    med = PrescriptionMedication(
        id=uuid.uuid4(),
        analysis_id=analysis.id,
        line_index=0,
        name_raw="Amox-bad-ocr",
        name_state="AMBIGUOUS",
        name_confidence=0.45,
        strength_raw="???",
        strength_state="AMBIGUOUS",
        strength_confidence=0.40,
    )
    db_session.add(med)
    db_session.flush()

    # Generate reviewer token
    reviewer = seeded_users["reviewer"]
    token, _ = create_access_token(
        user_id=reviewer.id,
        username=reviewer.username,
        role=reviewer.role,
    )
    headers = {"Authorization": f"Bearer {token}"}

    # 4. Doctor corrects medication line via PATCH /api/v1/analyses/{id}/medications
    edit_payload = {
        "medications": [
            {
                "line_index": 0,
                "name": "Amoxicillin",
                "strength": "500mg",
                "frequency": "TDS",
                "duration": "5 days",
                "instructions": "Take after food",
            }
        ]
    }
    patch_resp = client.patch(
        f"/api/v1/analyses/{analysis.id}/medications",
        json=edit_payload,
        headers=headers,
    )
    assert patch_resp.status_code == 200
    res_data = patch_resp.json()
    assert len(res_data["medications"]) == 1
    assert res_data["medications"][0]["name"]["value"] == "Amoxicillin"
    assert res_data["medications"][0]["strength"]["value"] == "500mg"
    assert res_data["medications"][0]["name"]["state"] == "CLEAR"

    # 5. Doctor submits sign-off via POST /api/v1/analyses/{id}/review
    # If there are findings, approve them; otherwise approve empty list
    review_payload = {
        "decisions": [
            {
                "finding_id": f["finding_id"],
                "action": "APPROVED",
                "notes": "Verified against patient chart and clinical guidelines.",
            }
            for f in res_data.get("findings", [])
        ]
    }
    review_resp = client.post(
        f"/api/v1/analyses/{analysis.id}/review",
        json=review_payload,
        headers=headers,
    )
    assert review_resp.status_code == 201
    record = review_resp.json()
    assert record["overall_status"] == "REVIEWED_COMPLETE"

    # 6. Verify in DB that status transitioned
    db_session.expire_all()
    updated_analysis = db_session.query(Analysis).filter(Analysis.id == analysis.id).first()
    assert updated_analysis.status == "REVIEWED_COMPLETE"
