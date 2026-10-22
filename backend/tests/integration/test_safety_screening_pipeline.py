"""
Integration test for Safety Screening Pipeline Stage & Clinical Summary Endpoint.
"""
import uuid
import pytest
from prescripto.db.base import utc_now
from prescripto.db.models.patient import Patient
from prescripto.db.models.document import PrescriptionDocument
from prescripto.db.models.analysis import Analysis
from prescripto.db.models.medication import PrescriptionMedication
from prescripto.db.models.safety import RiskFinding
from prescripto.pipeline.engine import handle_safety_screening, handle_report_assembly
from prescripto.domain.medication.models import MedicationResolutionResult, CanonicalMedication, ResolutionStatus


def test_safety_screening_allergy_and_dosage_pipeline(client, seeded_users, db_session):
    # 1. Setup patient with allergy
    patient = Patient(
        id=uuid.uuid4(),
        patient_id="PAT-ALLERGY-01",
        name="Vikram Sethi",
        phone_number="9112233445",
        age=35,
        gender="Male",
        blood_group="A+",
        allergies="Penicillin",
        medical_history="Seasonal allergies",
        created_at=utc_now(),
        updated_at=utc_now(),
    )
    db_session.add(patient)
    db_session.flush()

    # 2. Setup document linked to patient
    uploader = seeded_users["operator"]
    doc = PrescriptionDocument(
        id=uuid.uuid4(),
        uploader_id=uploader.id,
        patient_ref="PAT-ALLERGY-01",
        storage_key="prescriptions/test_allergy.png",
        file_hash_sha256="abc123allergyhash",
        mime_type="image/png",
        file_size_bytes=2048,
        status="UPLOADED",
        uploaded_at=utc_now(),
    )
    db_session.add(doc)
    db_session.flush()

    from prescripto.db.models.registry import ModelVersion
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

    # 3. Setup analysis
    analysis = Analysis(
        id=uuid.uuid4(),
        document_id=doc.id,
        model_snapshot_id=model.id,
        status="PROCESSING",
        pipeline_version="1.0.0",
        created_at=utc_now(),
    )
    db_session.add(analysis)
    db_session.flush()

    # 4. Add medication lines: Augmentin (penicillin class) and Paracetamol 1500mg (high dose)
    med1 = PrescriptionMedication(
        id=uuid.uuid4(),
        analysis_id=analysis.id,
        line_index=1,
        name_raw="Augmentin 625",
        name_state="CLEAR",
        name_confidence=0.95,
        strength_raw="625mg",
        strength_state="CLEAR",
        strength_confidence=0.90,
    )
    med2 = PrescriptionMedication(
        id=uuid.uuid4(),
        analysis_id=analysis.id,
        line_index=2,
        name_raw="Calpol",
        name_state="CLEAR",
        name_confidence=0.95,
        strength_raw="1500mg",
        strength_state="CLEAR",
        strength_confidence=0.90,
    )
    db_session.add_all([med1, med2])
    db_session.flush()

    # Mock canonical resolution for med1 and med2
    canonical_amox = CanonicalMedication(
        id=uuid.uuid4(),
        brand_name="Augmentin 625",
        generic_name="Amoxicillin and Clavulanate Potassium",
        active_ingredients=["Amoxicillin", "Clavulanic Acid"],
        strength="625mg",
    )
    canonical_pcm = CanonicalMedication(
        id=uuid.uuid4(),
        brand_name="Calpol",
        generic_name="Paracetamol",
        active_ingredients=["Paracetamol"],
        strength="1500mg",
    )
    context = {
        "medication_resolutions": {
            med1.id: MedicationResolutionResult("Augmentin", ResolutionStatus.RESOLVED, canonical_amox),
            med2.id: MedicationResolutionResult("Calpol", ResolutionStatus.RESOLVED, canonical_pcm),
        }
    }

    # 5. Execute handle_safety_screening
    safety_result = handle_safety_screening(db_session, analysis, doc, context)
    assert safety_result["status"] == "COMPLETED"
    assert safety_result["findings_count"] >= 2

    # Verify findings in database
    findings = db_session.query(RiskFinding).filter(RiskFinding.analysis_id == analysis.id).all()
    allergy_finding = next((f for f in findings if "allergy" in f.finding_key), None)
    dosage_finding = next((f for f in findings if "dosage" in f.finding_key), None)

    assert allergy_finding is not None
    assert "CRITICAL ALLERGY CONTRAINDICATION" in allergy_finding.evidence_text
    assert dosage_finding is not None
    assert "DOSAGE SAFETY WARNING" in dosage_finding.evidence_text

    # 6. Execute handle_report_assembly
    assembly_result = handle_report_assembly(db_session, analysis, doc, context)
    assert assembly_result["review_required"] is True
    assert assembly_result["final_status"] == "REQUIRES_REVIEW"

    # 7. Test clinical summary API endpoint
    from prescripto.auth.crypto import create_access_token
    token, _ = create_access_token(
        user_id=seeded_users["reviewer"].id,
        username=seeded_users["reviewer"].username,
        role=seeded_users["reviewer"].role,
    )
    auth_headers = {"Authorization": f"Bearer {token}"}
    resp = client.get(f"/api/v1/analyses/{analysis.id}/clinical-summary", headers=auth_headers)
    assert resp.status_code == 200
    summary_data = resp.json()
    assert summary_data["llm_ready"] is True
    assert "Vikram Sethi" in summary_data["executive_summary"]
    assert len(summary_data["patient_instructions"]) == 2
    assert any("ALLERGY" in a for a in summary_data["clinical_alerts"])
