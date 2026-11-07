"""
Audit Service: Tamper-resistant logging for security-sensitive events.
"""
import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from prescripto.db.models.audit import AuditEvent
from prescripto.db.models.users import User


class AuditService:
    @staticmethod
    def log_event(
        db: Session,
        event_type: str,
        actor: Optional[User],
        resource_type: str,
        resource_id: uuid.UUID,
        metadata: Optional[Dict[str, Any]] = None
    ) -> AuditEvent:
        """
        Logs an immutable audit event.
        Does NOT commit the session; caller must commit.
        """
        audit = AuditEvent(
            event_type=event_type,
            actor_id=actor.id if actor else None,
            resource_type=resource_type,
            resource_id=resource_id,
            occurred_at=datetime.now(timezone.utc),
            metadata=metadata or {},
        )
        db.add(audit)
        return audit

    @staticmethod
    def log_authentication(db: Session, user: User, success: bool, details: Optional[Dict[str, Any]] = None) -> None:
        AuditService.log_event(
            db,
            event_type="AUTHENTICATION",
            actor=user if success else None,
            resource_type="User",
            resource_id=user.id if user else uuid.uuid4(),
            metadata={"success": success, "details": details or {}}
        )

    @staticmethod
    def log_patient_record_access(
        db: Session,
        actor: User,
        patient_id: uuid.UUID,
        access_type: str,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        AuditService.log_event(
            db,
            event_type="PATIENT_RECORD_ACCESS",
            actor=actor,
            resource_type="Patient",
            resource_id=patient_id,
            metadata={"access_type": access_type, "details": details or {}}
        )

    @staticmethod
    def log_medical_history_modification(
        db: Session,
        actor: User,
        patient_id: uuid.UUID,
        modification_type: str,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        AuditService.log_event(
            db,
            event_type="MEDICAL_HISTORY_MODIFICATION",
            actor=actor,
            resource_type="Patient",
            resource_id=patient_id,
            metadata={"modification_type": modification_type, "details": details or {}}
        )

    @staticmethod
    def log_prescription_action(
        db: Session,
        actor: User,
        document_id: uuid.UUID,
        action: str,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        AuditService.log_event(
            db,
            event_type="PRESCRIPTION_ACTION",
            actor=actor,
            resource_type="PrescriptionDocument",
            resource_id=document_id,
            metadata={"action": action, "details": details or {}}
        )

    @staticmethod
    def log_doctor_verification(
        db: Session,
        admin: User,
        doctor_id: uuid.UUID,
        action: str,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        AuditService.log_event(
            db,
            event_type="DOCTOR_VERIFICATION",
            actor=admin,
            resource_type="User",
            resource_id=doctor_id,
            metadata={"action": action, "details": details or {}}
        )

    @staticmethod
    def log_permission_change(
        db: Session,
        actor: User,
        target_user_id: uuid.UUID,
        change_type: str,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        AuditService.log_event(
            db,
            event_type="PERMISSION_CHANGE",
            actor=actor,
            resource_type="User",
            resource_id=target_user_id,
            metadata={"change_type": change_type, "details": details or {}}
        )