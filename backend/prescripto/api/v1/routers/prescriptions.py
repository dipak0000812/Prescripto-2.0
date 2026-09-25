"""
Prescripto AI 2.0 — Prescriptions Router.
Implements POST /prescriptions (202 Accepted, idempotent upload),
GET /prescriptions (caller-scoped paginated list), and
GET /prescriptions/{id} (document detail with 60-second presigned URL).
"""
import uuid
from typing import Optional
from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    Header,
    Query,
    UploadFile,
    status,
)
from sqlalchemy.orm import Session

from prescripto.db.session import get_db
from prescripto.db.models.users import User
from prescripto.auth.dependencies import get_current_user
from prescripto.storage.client import StorageClient, get_storage_client
from prescripto.application.dtos.prescription import IngestPrescriptionInput
from prescripto.application.use_cases.ingest_prescription import IngestPrescriptionUseCase
from prescripto.application.use_cases.get_prescriptions import (
    ListPrescriptionsUseCase,
    GetPrescriptionDetailUseCase,
)
from prescripto.application.exceptions import MissingIdempotencyKeyException
from prescripto.api.v1.schemas.prescription import (
    UploadAccepted,
    PrescriptionList,
    PrescriptionDetail,
)

router = APIRouter(prefix="/prescriptions", tags=["Prescriptions"])


@router.post(
    "",
    response_model=UploadAccepted,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Upload a prescription document",
    operation_id="createPrescription",
)
async def create_prescription(
    file: UploadFile = File(...),
    patient_external_id: Optional[str] = Form(None),
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    storage_client: StorageClient = Depends(get_storage_client),
) -> UploadAccepted:
    """
    Accepts multipart/form-data upload with required Idempotency-Key.
    Persists document and queues analysis job. Returns 202 Accepted.
    """
    if not idempotency_key or not idempotency_key.strip():
        raise MissingIdempotencyKeyException()

    file_bytes = await file.read()

    use_case = IngestPrescriptionUseCase(db=db, storage_client=storage_client)
    cmd = IngestPrescriptionInput(
        file_bytes=file_bytes,
        uploader_id=current_user.id,
        idempotency_key=idempotency_key.strip(),
        patient_external_id=patient_external_id,
    )
    result = use_case.execute(cmd)

    return UploadAccepted(
        analysis_id=result.analysis_id,
        prescription_id=result.prescription_id,
    )


@router.get(
    "",
    response_model=PrescriptionList,
    status_code=status.HTTP_200_OK,
    summary="List prescriptions (caller-scoped, paginated)",
    operation_id="listPrescriptions",
)
def list_prescriptions(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PrescriptionList:
    """Lists prescription documents scoped to the caller with pagination."""
    use_case = ListPrescriptionsUseCase(db=db)
    items, total = use_case.execute(caller=current_user, page=page, page_size=page_size)

    return PrescriptionList(
        items=[
            {
                "prescription_id": item.prescription_id,
                "uploaded_at": item.uploaded_at,
                "status": item.status,
                "latest_analysis_status": item.latest_analysis_status,
            }
            for item in items
        ],
        page=page,
        page_size=page_size,
        total=total,
    )


@router.get(
    "/{id}",
    response_model=PrescriptionDetail,
    status_code=status.HTTP_200_OK,
    summary="Get one document's metadata and a presigned image URL",
    operation_id="getPrescription",
)
def get_prescription(
    id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    storage_client: StorageClient = Depends(get_storage_client),
) -> PrescriptionDetail:
    """
    Returns prescription document metadata along with an ephemeral 60s presigned GET URL.
    Enforces 404-over-403 security rule for callers without access.
    """
    use_case = GetPrescriptionDetailUseCase(db=db, storage_client=storage_client)
    detail = use_case.execute(document_id=id, caller=current_user)

    return PrescriptionDetail(
        prescription_id=detail.prescription_id,
        status=detail.status,
        uploaded_at=detail.uploaded_at,
        mime_type=detail.mime_type,
        file_size_bytes=detail.file_size_bytes,
        patient_ref=detail.patient_ref,
        image_url=detail.image_url,
        analyses=[
            {
                "analysis_id": a.analysis_id,
                "status": a.status,
                "created_at": a.created_at,
            }
            for a in detail.analyses
        ],
    )
