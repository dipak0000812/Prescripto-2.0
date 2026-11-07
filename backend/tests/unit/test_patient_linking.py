"""
Unit test verifying patient linking at prescription upload intake.
"""
import uuid
import pytest
from prescripto.application.use_cases.ingest_prescription import (
    IngestPrescriptionUseCase,
    IngestPrescriptionInput,
)
from prescripto.db.models.users import User
from prescripto.db.models.patient import Patient
from prescripto.db.models.document import PrescriptionDocument
from prescripto.db.models.registry import ModelVersion
from prescripto.db.models.enums import Role
from prescripto.auth.crypto import hash_password


def make_dummy_jpeg() -> bytes:
    from PIL import Image
    from io import BytesIO
    buf = BytesIO()
    img = Image.new("RGB", (100, 100), color="white")
    img.save(buf, format="JPEG")
    return buf.getvalue()


def test_patient_auto_linked_on_upload_when_patient_user_logged_in(db_session, mock_storage):
    # 1. Create a Patient user and linked Patient profile
    patient_user = User(
        id=uuid.uuid4(),
        username="test_patient_auto",
        email="patient_auto@example.com",
        hashed_password=hash_password("Pass123!"),
        role=Role.OPERATOR.value,
        is_active=True,
    )
    db_session.add(patient_user)
    db_session.flush()

    patient_profile = Patient(
        id=uuid.uuid4(),
        patient_id="PAT-AUTO-999",
        name="Auto Linked Patient",
        phone_number="+919999900001",
        user_id=patient_user.id,
    )
    db_session.add(patient_profile)

    # Ensure active model version exists
    model = db_session.query(ModelVersion).first()
    if not model:
        model = ModelVersion(
            id=uuid.uuid4(),
            model_name="prescripto-v1",
            model_version="1.0.0",
            checkpoint_sha256="0" * 64,
            artifact_storage_key="models/v1.onnx",
            framework="PyTorch",
            license="COMMERCIAL_PERMISSIVE",
        )
        db_session.add(model)
    db_session.commit()

    # 2. Ingest prescription without specifying patient_external_id
    use_case = IngestPrescriptionUseCase(db=db_session, storage_client=mock_storage)
    cmd = IngestPrescriptionInput(
        file_bytes=make_dummy_jpeg(),
        uploader_id=patient_user.id,
        idempotency_key=str(uuid.uuid4()),
        patient_external_id=None,
    )
    result = use_case.execute(cmd)

    # 3. Verify prescription document was auto-linked with PAT-AUTO-999
    doc = db_session.query(PrescriptionDocument).filter(
        PrescriptionDocument.id == result.prescription_id
    ).first()
    assert doc is not None
    assert doc.patient_ref == "PAT-AUTO-999"

