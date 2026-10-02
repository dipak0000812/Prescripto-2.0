"""
Integration tests for Analyses API:
- GET /analyses/{id} (Status & stages)
- GET /analyses/{id}/result (Result gating & full payload)
- POST /analyses/{id}/review (Review submission & status transition)
"""
import uuid
from datetime import datetime, timezone
import pytest
from fastapi.testclient import TestClient

from prescripto.db.models.document import PrescriptionDocument
from prescripto.db.models.analysis import Analysis, AnalysisStage
from prescripto.db.models.medication import PrescriptionMedication, MedicationCandidate
from prescripto.db.models.safety import RiskFinding
from prescripto.db.models.registry import ModelVersion
from prescripto.auth.crypto import create_access_token


@pytest.fixture
def auth_tokens(seeded_users):
    op_tok, _ = create_access_token(user_id=seeded_users["operator"].id, username=seeded_users["operator"].username, role=seeded_users["operator"].role)
    rev_tok, _ = create_access_token(user_id=seeded_users["reviewer"].id, username=seeded_users["reviewer"].username, role=seeded_users["reviewer"].role)
    adm_tok, _ = create_access_token(user_id=seeded_users["admin"].id, username=seeded_users["admin"].username, role=seeded_users["admin"].role)
    return {
        "operator": op_tok,
        "reviewer": rev_tok,
        "admin": adm_tok,
    }



@pytest.fixture
def sample_analysis(db_session, seeded_users):
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

    doc = PrescriptionDocument(
        id=uuid.uuid4(),
        uploader_id=seeded_users["operator"].id,
        file_hash_sha256="1" * 64,
        mime_type="image/jpeg",
        file_size_bytes=1024,
        status="UPLOADED",
        storage_key="prescriptions/test/original.jpg",
    )
    db_session.add(doc)

    analysis = Analysis(
        id=uuid.uuid4(),
        document_id=doc.id,
        model_snapshot_id=model.id,
        pipeline_version="1.0.0",
        status="QUEUED",
    )
    db_session.add(analysis)

    stage = AnalysisStage(
        id=uuid.uuid4(),
        analysis_id=analysis.id,
        stage_name="INGESTION",
        status="COMPLETED",
    )
    db_session.add(stage)
    db_session.commit()

    return {"doc": doc, "analysis": analysis, "model": model}


def test_get_analysis_status_success(client: TestClient, sample_analysis, auth_tokens):
    analysis_id = sample_analysis["analysis"].id
    headers = {"Authorization": f"Bearer {auth_tokens['operator']}"}

    response = client.get(f"/api/v1/analyses/{analysis_id}", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["analysis_id"] == str(analysis_id)
    assert data["status"] == "QUEUED"
    assert len(data["stages"]) == 1
    assert data["stages"][0]["stage_name"] == "INGESTION"


def test_get_analysis_status_not_found(client: TestClient, auth_tokens):
    headers = {"Authorization": f"Bearer {auth_tokens['operator']}"}
    fake_id = uuid.uuid4()
    response = client.get(f"/api/v1/analyses/{fake_id}", headers=headers)
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "RESOURCE_NOT_FOUND"


def test_get_analysis_result_gating(client: TestClient, sample_analysis, auth_tokens):
    analysis_id = sample_analysis["analysis"].id
    headers = {"Authorization": f"Bearer {auth_tokens['operator']}"}

    # Analysis is QUEUED -> Must return 404 with code ANALYSIS_NOT_READY
    response = client.get(f"/api/v1/analyses/{analysis_id}/result", headers=headers)
    assert response.status_code == 404
    data = response.json()
    assert data["error"]["code"] == "ANALYSIS_NOT_READY"


def test_get_analysis_result_completed(client: TestClient, sample_analysis, auth_tokens, db_session):
    analysis = sample_analysis["analysis"]
    analysis.status = "COMPLETED"

    # Add medication line
    med = PrescriptionMedication(
        id=uuid.uuid4(),
        analysis_id=analysis.id,
        line_index=0,
        name_raw="Augmentin 625",
        name_state="CLEAR",
        name_confidence=0.95,
        strength_raw="625mg",
        strength_state="CLEAR",
        strength_confidence=0.95,
        dose_raw="1 tablet",
        dose_state="CLEAR",
        dose_confidence=0.95,
        unit_raw="tablet",
        unit_state="CLEAR",
        unit_confidence=0.95,
        frequency_raw="BID",
        frequency_state="CLEAR",
        frequency_confidence=0.95,
        route_raw="oral",
        route_state="CLEAR",
        route_confidence=0.95,
        duration_raw="5 days",
        duration_state="CLEAR",
        duration_confidence=0.95,
        instructions_raw="after food",
        instructions_state="CLEAR",
        instructions_confidence=0.95,
    )
    db_session.add(med)

    cand = MedicationCandidate(
        id=uuid.uuid4(),
        prescription_med_id=med.id,
        analysis_id=analysis.id,
        extracted_text="Augmentin 625",
        matching_strategy="EXACT",
        candidate_score=0.95,
        source_vocabulary="CDSCO",
        resolution_status="RESOLVED",
    )
    db_session.add(cand)

    # Add finding
    finding = RiskFinding(
        id=uuid.uuid4(),
        analysis_id=analysis.id,
        check_type="ADVERSE_EFFECT",
        finding_key="adv_amoxicillin_allergy",
        finding_status="CONFIRMED_BY_SOURCE",
        medication_ids=[med.id],
        evidence_text="Risk of hypersensitivity",
        source_name="OPENFDA",
        source_version="2024-Q1",
        confidence_score=0.9,
    )
    db_session.add(finding)
    db_session.commit()

    headers = {"Authorization": f"Bearer {auth_tokens['operator']}"}
    response = client.get(f"/api/v1/analyses/{analysis.id}/result", headers=headers)
    assert response.status_code == 200
    data = response.json()

    assert data["analysis_id"] == str(analysis.id)
    assert data["status"] == "COMPLETED"
    assert len(data["medications"]) == 1
    assert data["medications"][0]["name"]["value"] == "Augmentin 625"
    assert len(data["findings"]) == 1
    assert data["findings"][0]["check_type"] == "ADVERSE_EFFECT"
    assert len(data["coverage_disclaimer"]) > 0


def test_submit_review_unauthorized_role(client: TestClient, sample_analysis, auth_tokens):
    analysis_id = sample_analysis["analysis"].id
    # OPERATOR cannot submit reviews
    headers = {"Authorization": f"Bearer {auth_tokens['operator']}"}
    body = {
        "decisions": [
            {"finding_id": str(uuid.uuid4()), "action": "APPROVED", "notes": "Looks good"}
        ]
    }
    response = client.post(f"/api/v1/analyses/{analysis_id}/review", json=body, headers=headers)
    assert response.status_code == 403


def test_submit_review_non_reviewable_analysis(client: TestClient, sample_analysis, auth_tokens):
    analysis = sample_analysis["analysis"]
    analysis.status = "COMPLETED"  # Not reviewable
    headers = {"Authorization": f"Bearer {auth_tokens['reviewer']}"}
    body = {
        "decisions": [
            {"finding_id": str(uuid.uuid4()), "action": "APPROVED"}
        ]
    }
    response = client.post(f"/api/v1/analyses/{analysis.id}/review", json=body, headers=headers)
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "ANALYSIS_NOT_REVIEWABLE"


def test_submit_review_success_complete(client: TestClient, sample_analysis, auth_tokens, db_session):
    analysis = sample_analysis["analysis"]
    analysis.status = "REQUIRES_REVIEW"
    db_session.commit()

    headers = {"Authorization": f"Bearer {auth_tokens['reviewer']}"}
    body = {
        "decisions": [
            {"finding_id": str(uuid.uuid4()), "action": "APPROVED", "notes": "Approved by reviewer"}
        ]
    }
    response = client.post(f"/api/v1/analyses/{analysis.id}/review", json=body, headers=headers)
    assert response.status_code == 201
    data = response.json()
    assert data["analysis_id"] == str(analysis.id)
    assert data["overall_status"] == "REVIEWED_COMPLETE"

    # Verify DB transition
    db_session.refresh(analysis)
    assert analysis.status == "REVIEWED_COMPLETE"


def test_submit_review_success_escalated(client: TestClient, sample_analysis, auth_tokens, db_session):
    analysis = sample_analysis["analysis"]
    analysis.status = "REQUIRES_REVIEW"
    db_session.commit()

    headers = {"Authorization": f"Bearer {auth_tokens['reviewer']}"}
    body = {
        "decisions": [
            {"finding_id": str(uuid.uuid4()), "action": "ESCALATED", "notes": "Requires senior review"}
        ]
    }
    response = client.post(f"/api/v1/analyses/{analysis.id}/review", json=body, headers=headers)
    assert response.status_code == 201
    data = response.json()
    assert data["analysis_id"] == str(analysis.id)
    assert data["overall_status"] == "REVIEWED_ESCALATED"

    # Verify DB transition
    db_session.refresh(analysis)
    assert analysis.status == "REVIEWED_ESCALATED"
