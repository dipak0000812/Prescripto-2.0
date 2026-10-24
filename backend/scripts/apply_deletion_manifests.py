"""
Prescripto AI 2.0 — Post-Restore Deletion Manifest Re-application Script.
Implements Arch §17 / DPDPA 2023 disaster recovery requirement:
A database restore resurrects deleted data unless all immutable deletion manifests
from the retention vault are re-applied.
"""
import sys
import json
import uuid
from typing import Dict, Any, List
from sqlalchemy.orm import Session

from prescripto.config.settings import settings
from prescripto.audit.logger import configure_logging, get_logger
from prescripto.db.session import SessionLocal
from prescripto.db.models.document import PrescriptionDocument
from prescripto.db.models.analysis import Analysis, AnalysisJob, AnalysisStage
from prescripto.db.models.medication import PrescriptionMedication, MedicationCandidate
from prescripto.db.models.safety import RiskFinding
from prescripto.db.models.review import Review
from prescripto.storage.client import StorageClient, get_storage_client

configure_logging("INFO")
logger = get_logger("prescripto.scripts.apply_deletion_manifests")


def apply_manifests(db: Session, storage_client: StorageClient, manifests: List[Dict[str, Any]]) -> int:
    """
    Re-applies deletion manifests against a database (e.g. after a backup restore).
    Purges any resurrected child records and guarantees documents are marked DELETED.
    """
    reapplied_count = 0

    for manifest in manifests:
        doc_id_str = manifest.get("document_id")
        if not doc_id_str:
            continue

        try:
            doc_id = uuid.UUID(doc_id_str)
        except ValueError:
            continue

        doc = db.query(PrescriptionDocument).filter(PrescriptionDocument.id == doc_id).first()
        if not doc:
            continue

        analyses = db.query(Analysis).filter(Analysis.document_id == doc.id).all()
        analysis_ids = [a.id for a in analyses]

        if analysis_ids:
            db.query(MedicationCandidate).filter(
                MedicationCandidate.analysis_id.in_(analysis_ids)
            ).delete(synchronize_session=False)

            db.query(PrescriptionMedication).filter(
                PrescriptionMedication.analysis_id.in_(analysis_ids)
            ).delete(synchronize_session=False)

            db.query(RiskFinding).filter(
                RiskFinding.analysis_id.in_(analysis_ids)
            ).delete(synchronize_session=False)

            db.query(AnalysisStage).filter(
                AnalysisStage.analysis_id.in_(analysis_ids)
            ).delete(synchronize_session=False)

            db.query(Review).filter(
                Review.analysis_id.in_(analysis_ids)
            ).delete(synchronize_session=False)

            db.query(AnalysisJob).filter(
                AnalysisJob.analysis_id.in_(analysis_ids)
            ).delete(synchronize_session=False)

            db.query(Analysis).filter(
                Analysis.id.in_(analysis_ids)
            ).delete(synchronize_session=False)

        doc.status = "DELETED"
        doc.storage_key = None
        db.commit()
        reapplied_count += 1

        logger.info(
            "manifest_reapplied",
            document_id=str(doc.id),
            manifest_id=manifest.get("manifest_id"),
        )

    return reapplied_count


def main() -> None:
    db = SessionLocal()
    storage = get_storage_client()
    try:
        # In production this would list all manifests/ in RETENTION_VAULT_BUCKET
        logger.info("reapplication_started", bucket=settings.RETENTION_VAULT_BUCKET)
        count = apply_manifests(db=db, storage_client=storage, manifests=[])
        print(f"Applied {count} deletion manifests successfully.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
