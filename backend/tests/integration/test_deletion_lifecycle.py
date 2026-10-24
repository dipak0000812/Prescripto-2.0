"""
Integration tests for DPDPA 2023 Verifiable Deletion Lifecycle:
- DELETE /prescriptions/{id} (Endpoint)
- DeletionWorker (DB cascade, S3 purge, manifest vault)
- Post-restore manifest re-application
"""
import uuid
import json
import hmac
import hashlib
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from prescripto.config.settings import settings
from prescripto.db.models.document import PrescriptionDocument
from prescripto.db.models.analysis import Analysis, AnalysisJob, AnalysisStage
from prescripto.db.models.medication import Medication, PrescriptionMedication, MedicationCandidate
from prescripto.db.models.safety import RiskFinding
from prescripto.db.models.retention import DeletionJob
from prescripto.db.models.registry import ModelVersion
from prescripto.auth.crypto import create_access_token
from prescripto.retention.worker import process_deletion_job, DeletionWorkerRunner
from scripts.apply_deletion_manifests import apply_manifests


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
def populated_prescription(db_session: Session, seeded_users, mock_storage):
    # 1. Global medication master entry (must NOT be deleted)
    global_med = Medication(
        id=uuid.uuid4(),
        brand_name="Global Drug Master",
        generic_name="Canonical Drug",
        active_ingredients=["Active One"],
        source_class="CDSCO_REGULATORY",
        source_version="2024.1",
        verification_status="VERIFIED_AUTHORITY",
    )
    db_session.add(global_med)

    model = ModelVersion(
        id=uuid.uuid4(),
        model_name="test-model",
        model_version="1.0.0",
        checkpoint_sha256="0" * 64,
        artifact_storage_key="models/m.onnx",
        framework="PyTorch",
        license="MIT",
    )
    db_session.add(model)

    doc_id = uuid.uuid4()
    storage_key = f"prescriptions/{doc_id}/original.jpg"
    mock_storage.put_object(storage_key, b"fake image bytes", content_type="image/jpeg")

    doc = PrescriptionDocument(
        id=doc_id,
        uploader_id=seeded_users["operator"].id,
        storage_key=storage_key,
        file_hash_sha256="2" * 64,
        mime_type="image/jpeg",
        file_size_bytes=1024,
        status="UPLOADED",
    )
    db_session.add(doc)

    analysis = Analysis(
        id=uuid.uuid4(),
        document_id=doc.id,
        model_snapshot_id=model.id,
        pipeline_version="1.0.0",
        status="COMPLETED",
    )
    db_session.add(analysis)

    med = PrescriptionMedication(
        id=uuid.uuid4(),
        analysis_id=analysis.id,
        line_index=0,
        name_raw="Test Line",
        name_state="CLEAR",
        name_confidence=0.9,
    )
    db_session.add(med)

    cand = MedicationCandidate(
        id=uuid.uuid4(),
        prescription_med_id=med.id,
        analysis_id=analysis.id,
        extracted_text="Test Line",
        matching_strategy="EXACT",
        candidate_score=1.0,
        source_vocabulary="CDSCO",
        resolved_medication_id=global_med.id,
        resolution_status="RESOLVED",
    )
    db_session.add(cand)

    finding = RiskFinding(
        id=uuid.uuid4(),
        analysis_id=analysis.id,
        check_type="ADVERSE_EFFECT",
        finding_key="test_risk",
        finding_status="CONFIRMED_BY_SOURCE",
        medication_ids=[med.id],
        source_name="OPENFDA",
        source_version="2024",
        confidence_score=0.9,
    )
    db_session.add(finding)
    db_session.commit()

    return {
        "doc": doc,
        "analysis": analysis,
        "global_med": global_med,
        "storage_key": storage_key,
    }


def test_delete_prescription_api_unauthorized(client: TestClient, populated_prescription, db_session: Session):
    from prescripto.db.models.users import User
    from prescripto.auth.crypto import hash_password

    other_user = User(
        id=uuid.uuid4(),
        username="other_operator",
        email="other_op@prescripto.local",
        hashed_password=hash_password("Pass123!"),
        role="OPERATOR",
        is_active=True,
    )
    db_session.add(other_user)
    db_session.commit()

    doc_id = populated_prescription["doc"].id
    other_tok, _ = create_access_token(user_id=other_user.id, username=other_user.username, role=other_user.role)
    headers = {"Authorization": f"Bearer {other_tok}"}

    response = client.delete(f"/api/v1/prescriptions/{doc_id}", headers=headers)
    assert response.status_code == 404  # 404-over-403 security rule



def test_delete_prescription_api_success(client: TestClient, populated_prescription, auth_tokens, db_session):
    doc = populated_prescription["doc"]
    headers = {"Authorization": f"Bearer {auth_tokens['operator']}"}

    response = client.delete(f"/api/v1/prescriptions/{doc.id}", headers=headers)
    assert response.status_code == 202
    data = response.json()
    assert "deletion_job_id" in data

    # Document should be marked DELETION_REQUESTED
    db_session.refresh(doc)
    assert doc.status == "DELETION_REQUESTED"

    # Attempting to delete again must return 409 DELETION_IN_PROGRESS
    dup_res = client.delete(f"/api/v1/prescriptions/{doc.id}", headers=headers)
    assert dup_res.status_code == 409
    assert dup_res.json()["error"]["code"] == "DELETION_IN_PROGRESS"


def test_deletion_worker_execution_lifecycle(db_session: Session, populated_prescription, mock_storage):
    doc = populated_prescription["doc"]
    global_med = populated_prescription["global_med"]
    storage_key = populated_prescription["storage_key"]

    # 1. Create deletion job
    job = DeletionJob(
        id=uuid.uuid4(),
        document_id=doc.id,
        status="REQUESTED",
    )
    db_session.add(job)
    db_session.commit()

    # 2. Execute deletion protocol
    result = process_deletion_job(db=db_session, storage_client=mock_storage, job_id=job.id)
    assert result["status"] == "COMPLETE"
    assert result["manifest_written"] is True

    # 3. Check DB records
    db_session.refresh(doc)
    assert doc.status == "DELETED"
    assert doc.storage_key is None

    # Prescription scoped analyses, meds, findings MUST be gone
    assert db_session.query(Analysis).filter(Analysis.document_id == doc.id).count() == 0
    assert db_session.query(PrescriptionMedication).count() == 0
    assert db_session.query(RiskFinding).count() == 0

    # Global Medication Master MUST remain intact
    assert db_session.query(Medication).filter(Medication.id == global_med.id).count() == 1

    # 4. Storage object MUST be deleted
    assert not mock_storage.object_exists(storage_key)

    # 5. Manifest MUST be written to retention vault
    manifest_key = f"manifests/{doc.id}.json"
    assert mock_storage.object_exists(manifest_key)
    raw_manifest = mock_storage.get_object(manifest_key)
    manifest_json = json.loads(raw_manifest.decode("utf-8"))
    assert manifest_json["document_id"] == str(doc.id)
    assert "signature" in manifest_json


def test_apply_deletion_manifests_restored_db(db_session: Session, populated_prescription, mock_storage):
    doc = populated_prescription["doc"]
    manifest = {
        "manifest_id": str(uuid.uuid4()),
        "document_id": str(doc.id),
    }

    reapplied = apply_manifests(db=db_session, storage_client=mock_storage, manifests=[manifest])
    assert reapplied == 1

    db_session.refresh(doc)
    assert doc.status == "DELETED"
    assert doc.storage_key is None
    assert db_session.query(Analysis).filter(Analysis.document_id == doc.id).count() == 0
