"""
Use cases for fetching Analysis Status and Full Analysis Result.
Conforms strictly to docs/API-CONTRACT.md and docs/ERROR-CONTRACT.md.
"""
import uuid
from typing import List
from sqlalchemy.orm import Session

from prescripto.db.models.analysis import Analysis, AnalysisStage
from prescripto.db.models.document import PrescriptionDocument
from prescripto.db.models.medication import PrescriptionMedication, MedicationCandidate
from prescripto.db.models.safety import RiskFinding
from prescripto.db.models.registry import KnowledgeSnapshot
from prescripto.db.models.users import User
from prescripto.db.models.enums import Role
from prescripto.domain.review.models import MANDATORY_COVERAGE_DISCLAIMER
from prescripto.domain.analysis.models import AnalysisStatus as DomainAnalysisStatus
from prescripto.domain.medication.models import ResolutionStatus
from prescripto.application.exceptions import (
    ResourceNotFoundException,
    AnalysisNotReadyException,
)
from prescripto.api.v1.schemas.analysis import (
    AnalysisStatus,
    AnalysisStageOut,
    AnalysisResult,
    MedicationLine,
    FieldValue,
    RiskFindingOut,
    NotEvaluatedItem,
    PrescriptionExtractionOut,
)


class GetAnalysisStatusUseCase:
    """Retrieves current analysis status and stage breakdown."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def execute(self, analysis_id: uuid.UUID, caller: User) -> AnalysisStatus:
        analysis = self.db.query(Analysis).filter(Analysis.id == analysis_id).first()
        if not analysis:
            raise ResourceNotFoundException(f"Analysis {analysis_id} not found")

        doc = self.db.query(PrescriptionDocument).filter(
            PrescriptionDocument.id == analysis.document_id
        ).first()

        # 404-over-403 security rule
        if caller.role == Role.OPERATOR.value and doc and doc.uploader_id != caller.id:
            raise ResourceNotFoundException(f"Analysis {analysis_id} not found")

        stages = self.db.query(AnalysisStage).filter(
            AnalysisStage.analysis_id == analysis_id
        ).order_by(AnalysisStage.started_at).all()

        provider_used = None
        model_used = None
        attempts = None
        fallback_reason = None
        fallback_used = False

        for s in stages:
            if s.output_json and isinstance(s.output_json, dict):
                if s.output_json.get("provider_used"):
                    provider_used = s.output_json.get("provider_used")
                if s.output_json.get("model_used"):
                    model_used = s.output_json.get("model_used")
                if s.output_json.get("attempts") is not None:
                    attempts = s.output_json.get("attempts")
                if s.output_json.get("fallback_reason"):
                    fallback_reason = s.output_json.get("fallback_reason")
                if s.output_json.get("recognition_fallback_used") or s.output_json.get("fallback_occurred"):
                    fallback_used = True

        return AnalysisStatus(
            analysis_id=analysis.id,
            status=analysis.status,
            stages=[
                AnalysisStageOut(
                    stage_name=s.stage_name,
                    status=s.status,
                    error_code=s.error_code,
                )
                for s in stages
            ],
            error_message=self._user_facing_error(analysis.error_detail),
            provider_used=provider_used,
            model_used=model_used,
            attempts=attempts,
            fallback_reason=fallback_reason,
            recognition_fallback_used=fallback_used,
            recognition_fallback_reason=fallback_reason,
        )

    @staticmethod
    def _user_facing_error(error_detail: str | None) -> str | None:
        if not error_detail:
            return None
        if error_detail.startswith("GEMINI_QUOTA_EXCEEDED:"):
            return "Gemini's current free-tier rate or quota limit was reached. Please retry later."
        if error_detail.startswith("GEMINI_TIMEOUT:"):
            return "Prescription recognition timed out. Please try again later."
        if error_detail.startswith("GEMINI_CONFIGURATION_ERROR:"):
            return "Gemini recognition is not configured on the backend. Contact the administrator."
        if error_detail.startswith("GEMINI_AUTHENTICATION_ERROR:"):
            return "The backend could not authenticate with Gemini. Contact the administrator."
        if error_detail.startswith("GEMINI_MODEL_UNAVAILABLE:"):
            return "The configured Gemini model is unavailable. Contact the administrator."
        if error_detail.startswith("GEMINI_MALFORMED_RESPONSE:"):
            return "Prescription recognition returned an unreadable result. Please retry later."
        return "Prescription analysis could not be completed. Please retry later or contact support."


class GetAnalysisResultUseCase:
    """
    Retrieves full structured analysis result.
    Enforces result gating: returns 404 ANALYSIS_NOT_READY for QUEUED, PROCESSING, FAILED.
    """

    def __init__(self, db: Session) -> None:
        self.db = db

    def execute(self, analysis_id: uuid.UUID, caller: User) -> AnalysisResult:
        analysis = self.db.query(Analysis).filter(Analysis.id == analysis_id).first()
        if not analysis:
            raise ResourceNotFoundException(f"Analysis {analysis_id} not found")

        doc = self.db.query(PrescriptionDocument).filter(
            PrescriptionDocument.id == analysis.document_id
        ).first()

        # 404-over-403 rule
        if caller.role == Role.OPERATOR.value and doc and doc.uploader_id != caller.id:
            raise ResourceNotFoundException(f"Analysis {analysis_id} not found")

        # Result gating check (API-CONTRACT §Behavior not in the schema)
        if analysis.status in ["QUEUED", "PROCESSING", "FAILED"]:
            raise AnalysisNotReadyException(
                f"Analysis {analysis_id} is in status '{analysis.status}' and not ready"
            )

        # 1. Fetch prescription medications
        db_meds = self.db.query(PrescriptionMedication).filter(
            PrescriptionMedication.analysis_id == analysis_id
        ).order_by(PrescriptionMedication.line_index).all()

        medication_lines: List[MedicationLine] = []
        for m in db_meds:
            # Query candidate resolution if present
            candidate = self.db.query(MedicationCandidate).filter(
                MedicationCandidate.prescription_med_id == m.id
            ).first()

            res_id = candidate.resolved_medication_id if candidate else None
            res_status = candidate.resolution_status if candidate else ResolutionStatus.UNRESOLVED.value
            medication_lines.append(
                MedicationLine(
                    line_index=m.line_index,
                    name=FieldValue(value=m.name_raw, state=m.name_state, confidence=m.name_confidence),
                    strength=FieldValue(value=m.strength_raw, state=m.strength_state, confidence=m.strength_confidence),
                    dose=FieldValue(value=m.dose_raw, state=m.dose_state, confidence=m.dose_confidence),
                    unit=FieldValue(value=m.unit_raw, state=m.unit_state, confidence=m.unit_confidence),
                    frequency=FieldValue(value=m.frequency_raw, state=m.frequency_state, confidence=m.frequency_confidence),
                    route=FieldValue(value=m.route_raw, state=m.route_state, confidence=m.route_confidence),
                    duration=FieldValue(value=m.duration_raw, state=m.duration_state, confidence=m.duration_confidence),
                    instructions=FieldValue(value=m.instructions_raw, state=m.instructions_state, confidence=m.instructions_confidence),
                    resolved_medication_id=res_id,
                    resolution_status=res_status,
                )
            )

        # 2. Fetch risk findings
        db_findings = self.db.query(RiskFinding).filter(
            RiskFinding.analysis_id == analysis_id
        ).all()

        findings_out: List[RiskFindingOut] = []
        not_evaluated_out: List[NotEvaluatedItem] = []

        for f in db_findings:
            if f.finding_status == "NOT_EVALUATED":
                not_evaluated_out.append(
                    NotEvaluatedItem(
                        medication_ids=list(f.medication_ids or []),
                        reason=f.not_evaluated_reason or "PROVIDER_LACKS_CAPABILITY",
                    )
                )

            findings_out.append(
                RiskFindingOut(
                    finding_id=f.id,
                    finding_status=f.finding_status,
                    check_type=f.check_type,
                    medication_ids=list(f.medication_ids or []),
                    evidence_text=f.evidence_text,
                    source_name=f.source_name,
                    source_version=f.source_version,
                    confidence_score=f.confidence_score,
                    check_timestamp=f.check_timestamp,
                    not_evaluated_reason=f.not_evaluated_reason,
                )
            )

        # 3. Model versions and knowledge snapshots
        model_versions = [f"pipeline:{analysis.pipeline_version}"]
        snapshots = self.db.query(KnowledgeSnapshot).all()
        knowledge_names = [f"{s.source_name} {s.source_version}" for s in snapshots] or ["CDSCO 2024.1", "OPENFDA 2024-Q1"]
        extraction_stage = self.db.query(AnalysisStage).filter(
            AnalysisStage.analysis_id == analysis_id,
            AnalysisStage.stage_name == "STRUCTURED_EXTRACTION",
        ).first()
        extraction_out = extraction_stage.output_json if (extraction_stage and extraction_stage.output_json) else {}
        document_extraction = (
            PrescriptionExtractionOut.model_validate(extraction_out)
            if extraction_out
            else None
        )
        provider_used = extraction_out.get("provider_used")
        model_used = extraction_out.get("model_used")
        attempts = extraction_out.get("attempts")
        fallback_reason = extraction_out.get("fallback_reason")
        fallback_used = bool(extraction_out.get("recognition_fallback_used") or extraction_out.get("fallback_occurred"))

        return AnalysisResult(
            analysis_id=analysis.id,
            status=analysis.status,
            analysis_timestamp=analysis.completed_at or analysis.created_at,
            model_versions=model_versions,
            knowledge_snapshots=knowledge_names,
            medications=medication_lines,
            document_extraction=document_extraction,
            findings=findings_out,
            not_evaluated=not_evaluated_out,
            coverage_disclaimer=MANDATORY_COVERAGE_DISCLAIMER,
            provider_used=provider_used,
            model_used=model_used,
            attempts=attempts,
            fallback_reason=fallback_reason,
            recognition_fallback_used=fallback_used,
            recognition_fallback_reason=fallback_reason,
        )
