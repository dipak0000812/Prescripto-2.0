"""
Prescripto AI 2.0 — Prescription Retrieval Use Cases.
Handles caller-scoped pagination and detailed retrieval with 60-second presigned URLs.
Enforces the 404-over-403 rule and DPDPA deletion checks.
"""
import uuid
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import desc

from prescripto.storage.client import StorageClient
from prescripto.db.models.document import PrescriptionDocument
from prescripto.db.models.analysis import Analysis
from prescripto.db.models.users import User
from prescripto.db.models.enums import Role
from prescripto.domain.prescription.models import DocumentStatus
from prescripto.application.dtos.prescription import (
    PrescriptionSummaryDTO,
    AnalysisSummaryDTO,
    PrescriptionDetailDTO,
)
from prescripto.application.exceptions import (
    ResourceNotFoundException,
    DeletionInProgressException,
)


class ListPrescriptionsUseCase:
    """Retrieves a paginated list of prescription documents scoped to the caller."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def execute(
        self, caller: User, page: int = 1, page_size: int = 20
    ) -> Tuple[List[PrescriptionSummaryDTO], int]:
        query = self.db.query(PrescriptionDocument)

        # Scoping rule: OPERATOR only sees their own documents. ADMIN and REVIEWER see all.
        if caller.role not in (Role.ADMIN.value, Role.REVIEWER.value):
            query = query.filter(PrescriptionDocument.uploader_id == caller.id)

        # Exclude completely deleted records
        query = query.filter(PrescriptionDocument.status != DocumentStatus.DELETED.value)

        total = query.count()
        offset = max(0, (page - 1) * page_size)
        documents = (
            query.order_by(desc(PrescriptionDocument.uploaded_at))
            .offset(offset)
            .limit(page_size)
            .all()
        )

        items: List[PrescriptionSummaryDTO] = []
        for doc in documents:
            latest_analysis = (
                self.db.query(Analysis)
                .filter(Analysis.document_id == doc.id)
                .order_by(desc(Analysis.created_at))
                .first()
            )
            items.append(
                PrescriptionSummaryDTO(
                    prescription_id=doc.id,
                    uploaded_at=doc.uploaded_at,
                    status=doc.status,
                    latest_analysis_status=latest_analysis.status if latest_analysis else None,
                )
            )

        return items, total


class GetPrescriptionDetailUseCase:
    """Retrieves document detail and generates ephemeral 60s presigned URL."""

    def __init__(self, db: Session, storage_client: StorageClient) -> None:
        self.db = db
        self.storage = storage_client

    def execute(self, document_id: uuid.UUID, caller: User) -> PrescriptionDetailDTO:
        doc = self.db.query(PrescriptionDocument).filter(PrescriptionDocument.id == document_id).first()

        # 404-over-403 rule: If not found or not visible to caller, return 404
        if not doc:
            raise ResourceNotFoundException("Prescription document not found")

        if caller.role not in (Role.ADMIN.value, Role.REVIEWER.value) and doc.uploader_id != caller.id:
            raise ResourceNotFoundException("Prescription document not found")

        if doc.status == DocumentStatus.DELETION_IN_PROGRESS.value:
            raise DeletionInProgressException()

        # Presigned URL generation (60s TTL)
        image_url: Optional[str] = None
        if doc.status == DocumentStatus.UPLOADED.value and doc.storage_key and not doc.deleted_at:
            try:
                image_url = self.storage.generate_presigned_url(doc.storage_key, expires_in=60)
            except Exception:
                image_url = None

        # Associated analyses
        analyses_rows = (
            self.db.query(Analysis)
            .filter(Analysis.document_id == doc.id)
            .order_by(desc(Analysis.created_at))
            .all()
        )
        analyses_dto = [
            AnalysisSummaryDTO(
                analysis_id=a.id,
                status=a.status,
                created_at=a.created_at,
            )
            for a in analyses_rows
        ]

        return PrescriptionDetailDTO(
            prescription_id=doc.id,
            status=doc.status,
            uploaded_at=doc.uploaded_at,
            mime_type=doc.mime_type,
            file_size_bytes=doc.file_size_bytes,
            patient_ref=doc.patient_ref,
            image_url=image_url,
            analyses=analyses_dto,
        )
