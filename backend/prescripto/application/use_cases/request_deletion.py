"""
Prescripto AI 2.0 — Request Prescription Deletion Use Case.
Implements DPDPA 2023 verifiable deletion entry point.
"""
import uuid
from sqlalchemy.orm import Session

from prescripto.db.models.document import PrescriptionDocument
from prescripto.db.models.retention import DeletionJob
from prescripto.db.models.users import User
from prescripto.db.models.enums import Role
from prescripto.application.exceptions import (
    ResourceNotFoundException,
    DeletionInProgressException,
)


class RequestDeletionUseCase:
    """Marks document for deletion and enqueues a DeletionJob."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def execute(self, document_id: uuid.UUID, caller: User) -> uuid.UUID:
        doc = self.db.query(PrescriptionDocument).filter(
            PrescriptionDocument.id == document_id
        ).first()

        if not doc:
            raise ResourceNotFoundException(f"Prescription {document_id} not found")

        # 404-over-403 security rule
        if caller.role != Role.ADMIN.value and doc.uploader_id != caller.id:
            raise ResourceNotFoundException(f"Prescription {document_id} not found")

        if doc.status in ["DELETION_REQUESTED", "DELETION_IN_PROGRESS", "DELETED"]:
            raise DeletionInProgressException(
                f"Prescription {document_id} is already in state '{doc.status}'"
            )

        doc.status = "DELETION_REQUESTED"

        job = DeletionJob(
            id=uuid.uuid4(),
            document_id=doc.id,
            status="REQUESTED",
        )
        self.db.add(job)
        self.db.commit()

        return job.id
