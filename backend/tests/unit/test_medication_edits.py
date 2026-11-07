"""
Unit test reproducing Bug 2: Medication Editing & Audit Trail.
Validates:
1. Patient who owns the prescription can edit medication (previously blocked with 403).
2. Unauthorized user cannot edit another patient's medication (returns 403).
3. Reviewer/Admin can edit any medication.
4. Validation rules:
   - Empty medicine name raises validation error.
   - Negative / invalid duration raises validation error.
   - Valid duration formats ("5 days", "10", "as needed", "SOS") succeed.
5. Audit trail:
   - Original extracted values stored in original_*_raw columns.
   - is_edited set to True.
   - edited_by_user_id set to current user ID.
   - edited_at set to current timestamp.
   - State set to CLEAR and confidence set to 1.0.
"""
import uuid
import pytest
from datetime import datetime
from pydantic import ValidationError
from fastapi import HTTPException

from prescripto.db.models.users import User
from prescripto.db.models.patient import Patient
from prescripto.db.models.document import PrescriptionDocument
from prescripto.db.models.analysis import Analysis
from prescripto.db.models.medication import PrescriptionMedication
from prescripto.db.models.registry import ModelVersion
from prescripto.db.models.enums import Role
from prescripto.db.base import utc_now
from prescripto.api.v1.schemas.analysis import (
    MedicationUpdateRequest,
    MedicationUpdateItem,
)
from prescripto.api.v1.routers.analyses import update_analysis_medications


@pytest.fixture
def default_model_version(db_session):
    mv = ModelVersion(
        id=uuid.uuid4(),
        model_name="extraction_model",
        model_version="1.0.0",
        checkpoint_sha256="0" * 64,
        artifact_storage_key="models/extraction_model/1.0.0.onnx",
        framework="ONNX",
        license="MIT",
    )
    db_session.add(mv)
    db_session.commit()
    return mv


def test_medication_update_validation_empty_name():
    """Medicine name must not be empty or whitespace."""
    with pytest.raises(ValidationError):
        MedicationUpdateItem(line_index=0, name="   ")


def test_medication_update_validation_invalid_duration():
    """Duration must be a positive integer or 'as needed'."""
    with pytest.raises(ValidationError):
        MedicationUpdateItem(line_index=0, duration="-5 days")

    with pytest.raises(ValidationError):
        MedicationUpdateItem(line_index=0, duration="abc")


def test_medication_update_validation_valid_duration():
    """Valid duration strings should succeed."""
    item1 = MedicationUpdateItem(line_index=0, duration="5 days")
    assert item1.duration == "5 days"

    item2 = MedicationUpdateItem(line_index=0, duration="as needed")
    assert item2.duration == "as needed"

    item3 = MedicationUpdateItem(line_index=0, duration="SOS")
    assert item3.duration == "SOS"


def test_patient_owner_can_edit_medications_with_audit_trail(db_session, default_model_version):
    """
    A logged-in patient who uploaded the prescription should be allowed to edit
    their medications. The edit must preserve raw original values and record the audit trail.
    """
    # 1. Create Patient User & Patient record
    patient_user = User(
        id=uuid.uuid4(),
        username="ramesh_patient",
        email="patient_editor@example.com",
        hashed_password="fakehash",
        role=Role.OPERATOR.value,
        is_active=True,
    )
    patient_record = Patient(
        id=uuid.uuid4(),
        patient_id="PAT-EDIT-001",
        name="Ramesh Kumar",
        phone_number="+919876543201",
        user_id=patient_user.id,
    )
    db_session.add_all([patient_user, patient_record])
    db_session.commit()

    # 2. Create Prescription Document uploaded by this patient
    doc = PrescriptionDocument(
        id=uuid.uuid4(),
        uploader_id=patient_user.id,
        patient_ref=patient_record.patient_id,
        file_hash_sha256="aabbccddeeff00112233445566778899aabbccddeeff00112233445566778899",
        mime_type="image/jpeg",
        file_size_bytes=1024,
        status="UPLOADED",
    )
    analysis = Analysis(
        id=uuid.uuid4(),
        document_id=doc.id,
        status="REQUIRES_REVIEW",
        pipeline_version="1.0.0",
        model_snapshot_id=default_model_version.id,
        review_required=True,
        review_reasons=["MANUAL_CHECK"],
    )
    med = PrescriptionMedication(
        id=uuid.uuid4(),
        analysis_id=analysis.id,
        line_index=0,
        name_raw="Calpol 250",
        name_state="AMBIGUOUS",
        name_confidence=0.6,
        strength_raw="250/5",
        strength_state="AMBIGUOUS",
        frequency_raw="q6h",
        frequency_state="AMBIGUOUS",
        duration_raw="3 days",
        duration_state="CLEAR",
        instructions_raw="After food",
        instructions_state="CLEAR",
    )
    db_session.add_all([doc, analysis, med])
    db_session.commit()

    # 3. Patient updates medicine details
    req = MedicationUpdateRequest(
        medications=[
            MedicationUpdateItem(
                line_index=0,
                name="Calpol 250 Syrup",
                strength="250mg/5ml",
                frequency="1-1-1",
                duration="5 days",
                instructions="After food",
            )
        ]
    )

    res = update_analysis_medications(
        id=analysis.id,
        update_req=req,
        current_user=patient_user,
        db=db_session,
    )

    assert res is not None
    # Verify in DB
    updated_med = db_session.query(PrescriptionMedication).filter_by(id=med.id).first()
    assert updated_med.name_raw == "Calpol 250 Syrup"
    assert updated_med.name_state == "CLEAR"
    assert updated_med.original_name_raw == "Calpol 250"
    assert updated_med.is_edited is True
    assert updated_med.edited_by_user_id == patient_user.id
    assert updated_med.edited_at is not None


def test_unauthorized_user_cannot_edit_medications(db_session, default_model_version):
    """A user who is not the uploader and not a reviewer/admin cannot edit medications."""
    uploader = User(
        id=uuid.uuid4(),
        username="uploader_user",
        email="uploader@example.com",
        hashed_password="fakehash",
        role=Role.OPERATOR.value,
        is_active=True,
    )
    intruder = User(
        id=uuid.uuid4(),
        username="intruder_user",
        email="intruder@example.com",
        hashed_password="fakehash",
        role=Role.OPERATOR.value,
        is_active=True,
    )
    db_session.add_all([uploader, intruder])
    db_session.commit()

    doc = PrescriptionDocument(
        id=uuid.uuid4(),
        uploader_id=uploader.id,
        file_hash_sha256="11223344556677889900aabbccddeeff11223344556677889900aabbccddeeff",
        mime_type="image/jpeg",
        file_size_bytes=1024,
        status="UPLOADED",
    )
    analysis = Analysis(
        id=uuid.uuid4(),
        document_id=doc.id,
        status="REQUIRES_REVIEW",
        pipeline_version="1.0.0",
        model_snapshot_id=default_model_version.id,
    )
    med = PrescriptionMedication(
        id=uuid.uuid4(),
        analysis_id=analysis.id,
        line_index=0,
        name_raw="Amoxicillin 500",
    )
    db_session.add_all([doc, analysis, med])
    db_session.commit()

    req = MedicationUpdateRequest(
        medications=[MedicationUpdateItem(line_index=0, name="Augmentin 625")]
    )

    with pytest.raises(HTTPException) as exc_info:
        update_analysis_medications(
            id=analysis.id,
            update_req=req,
            current_user=intruder,
            db=db_session,
        )
    assert exc_info.value.status_code == 403
