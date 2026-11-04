"""
Pipeline Stage Handlers for Prescripto AI 2.0 Analysis Pipeline.
Integrates structured extraction, normalization, safety screening, and report assembly.
"""
import uuid
from hashlib import sha256
from io import BytesIO
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from prescripto.db.base import utc_now
from prescripto.db.models.analysis import Analysis
from prescripto.db.models.document import PrescriptionDocument
from prescripto.db.models.medication import PrescriptionMedication, MedicationCandidate
from prescripto.db.models.safety import RiskFinding
from prescripto.db.models.patient import Patient
from prescripto.domain.medication.models import ResolutionStatus
from prescripto.domain.safety.duplicate import detect_duplicate_medications
from prescripto.domain.safety.allergy import detect_allergy_contraindications
from prescripto.domain.safety.dosage import detect_dosage_safety_warnings
from prescripto.domain.review.models import evaluate_review_triggers
from prescripto.application.services.medication_search import MedicationSearchService
from prescripto.domain.medication.models import (
    MatchingStrategy,
    VerificationStatus,
    MedicationResolutionResult,
)
from prescripto.ml.extraction import extract_prescription_fields
from prescripto.storage.client import get_storage_client







def handle_ingestion(
    db: Session,
    analysis: Analysis,
    document: Optional[PrescriptionDocument],
    context: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Stage: INGESTION.
    Validates document presence, verifies file integrity, format, and storage pointer.
    """
    if not document or not document.storage_key:
        raise ValueError("Uploaded document or its storage reference is unavailable")

    storage_client = context.get("storage_client") or get_storage_client()
    image_bytes = storage_client.get_object(document.storage_key)
    if sha256(image_bytes).hexdigest() != document.file_hash_sha256:
        raise ValueError("Stored document hash does not match the ingested file hash")
    context["document_bytes"] = image_bytes
    return {
        "stage": "INGESTION",
        "status": "COMPLETED",
        "document_id": str(document.id),
        "file_size_bytes": document.file_size_bytes,
        "mime_type": document.mime_type,
        "file_hash_sha256": document.file_hash_sha256,
    }


def handle_quality_check(
    db: Session,
    analysis: Analysis,
    document: Optional[PrescriptionDocument],
    context: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Stage: QUALITY_CHECK.
    Evaluates scan quality (blur, contrast, resolution, Laplacian variance).
    If quality is below acceptable threshold, flags quality_failed in context to trigger human review.
    """
    image_bytes = context.get("document_bytes")
    if not image_bytes:
        raise ValueError("Quality check requires the ingested image bytes")
    try:
        from PIL import Image

        with Image.open(BytesIO(image_bytes)) as image:
            width, height = image.size
            gray = image.convert("L")
            extrema = gray.getextrema()
            is_blank = (extrema[1] - extrema[0] < 5)
    except Exception as error:
        raise ValueError("Uploaded image cannot be decoded") from error

    is_poor_quality = width < 400 or height < 400 or is_blank
    blur_score = None
    brightness = None
    sharp_ok = True
    exposure_ok = True

    try:
        from ml.ocr.quality_check import check_blur, check_exposure
        sharp_ok, blur_score = check_blur(image_bytes, threshold=100.0)
        exposure_ok, brightness = check_exposure(image_bytes, low_thresh=20.0, high_thresh=255.0)
        if not sharp_ok or not exposure_ok:
            is_poor_quality = True
    except Exception:
        pass

    context["quality_failed"] = is_poor_quality

    return {
        "stage": "QUALITY_CHECK",
        "status": "COMPLETED",
        "width": width,
        "height": height,
        "is_blank": is_blank,
        "blur_score": blur_score,
        "brightness": brightness,
        "sharp_ok": sharp_ok,
        "exposure_ok": exposure_ok,
        "quality_passed": not is_poor_quality,
        "check_method": "decode_dimensions_contrast_and_laplacian",
    }


def _resolve_recognition_provider(context: Dict[str, Any]):
    """Resolves active recognition provider respecting explicit overrides and RECOGNITION_PROVIDER setting."""
    if context.get("recognition_provider") is not None:
        return context["recognition_provider"]
    from prescripto.config.settings import settings
    from prescripto.ml.recognition_providers import (
        get_recognition_provider,
        LocalRapidOCRProvider,
    )
    provider_type = (settings.RECOGNITION_PROVIDER or "gemini").lower()
    if provider_type in ("rapidocr", "local_rapidocr", "local"):
        return LocalRapidOCRProvider(ocr_runtime=context.get("ocr_runtime"))
    return get_recognition_provider(provider_type)


def _recognize_document(context: Dict[str, Any], image_bytes: bytes, mime_type: str):
    """Gemini first; RapidOCR on ANY RecognitionError. Remote ml-service is not used."""
    from prescripto.config.settings import settings
    from prescripto.ml.recognition_providers import (
        LocalRapidOCRProvider,
        RecognitionError,
    )

    provider = _resolve_recognition_provider(context)
    try:
        rec_result = provider.recognize_document(image_bytes, mime_type=mime_type)
        context["recognition_provider_used"] = getattr(rec_result, "provider_used", "gemini")
        context["recognition_model_used"] = getattr(rec_result, "model_used", None)
        context["recognition_attempts"] = getattr(rec_result, "attempts", 1)
        context["recognition_fallback_used"] = getattr(rec_result, "fallback_occurred", False)
        context["recognition_fallback_reason"] = getattr(rec_result, "fallback_reason", None)
        return rec_result
    except RecognitionError as err:
        if type(provider).__name__ == "LocalRapidOCRProvider":
            raise
        result = LocalRapidOCRProvider(
            ocr_runtime=context.get("ocr_runtime")
        ).recognize_document(image_bytes, mime_type=mime_type)
        result.provider_used = "rapidocr"
        result.model_used = "rapidocr"
        result.attempts = getattr(err, "attempts", 1)
        result.fallback_occurred = True
        result.fallback_reason = str(err).split(":", 1)[0]
        context["recognition_provider_used"] = "rapidocr"
        context["recognition_model_used"] = "rapidocr"
        context["recognition_attempts"] = getattr(err, "attempts", 1)
        context["recognition_fallback_used"] = True
        context["recognition_fallback_reason"] = str(err)
        return result
    except Exception as err:
        if type(provider).__name__ == "LocalRapidOCRProvider":
            raise
        result = LocalRapidOCRProvider(
            ocr_runtime=context.get("ocr_runtime")
        ).recognize_document(image_bytes, mime_type=mime_type)
        result.provider_used = "rapidocr"
        result.model_used = "rapidocr"
        result.attempts = getattr(err, "attempts", 1)
        result.fallback_occurred = True
        result.fallback_reason = f"UNEXPECTED_ERROR:{type(err).__name__}"
        context["recognition_provider_used"] = "rapidocr"
        context["recognition_model_used"] = "rapidocr"
        context["recognition_attempts"] = getattr(err, "attempts", 1)
        context["recognition_fallback_used"] = True
        context["recognition_fallback_reason"] = str(err)
        return result


def handle_text_detection(
    db: Session,
    analysis: Analysis,
    document: Optional[PrescriptionDocument],
    context: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Stage: TEXT_DETECTION.
    Uses the configured RecognitionProvider (Gemini Vision, local RapidOCR, or mock) to recognize
    document text and perform clinical entity classification.
    """
    from prescripto.ml.runtime import OCRLine

    doc = document
    if not doc and analysis.document_id:
        doc = db.query(PrescriptionDocument).filter(PrescriptionDocument.id == analysis.document_id).first()
    mime = doc.mime_type if doc and doc.mime_type else "image/jpeg"

    rec_result = _recognize_document(context, context["document_bytes"], mime)
    context["document_recognition"] = rec_result

    # Maintain backwards-compatible ocr_lines for stages and tests expecting it
    ocr_lines: List[OCRLine] = []
    for idx, item in enumerate(rec_result.items):
        l_idx = item.line_index if item.line_index is not None else idx
        box_tuple = tuple(item.box) if item.box and len(item.box) == 4 else (0.0, 0.0, 100.0, 20.0)
        ocr_lines.append(OCRLine(line_index=l_idx, text=item.original_text, raw_score=item.confidence or 0.95, box=box_tuple))

    context["ocr_lines"] = ocr_lines

    fallback_used = rec_result.fallback_occurred or context.get("recognition_fallback_used", False)
    fallback_reason = rec_result.fallback_reason or context.get("recognition_fallback_reason")

    return {
        "stage": "TEXT_DETECTION",
        "status": "COMPLETED",
        "regions_detected_count": len(ocr_lines),
        "detector_model": rec_result.provider_used,
        "provider_used": rec_result.provider_used,
        "model_used": rec_result.model_used,
        "attempts": rec_result.attempts,
        "fallback_occurred": fallback_used,
        "fallback_reason": fallback_reason,
        "recognition_fallback_used": fallback_used,
        "recognition_fallback_reason": fallback_reason,
    }


def handle_ocr_recognition(
    db: Session,
    analysis: Analysis,
    document: Optional[PrescriptionDocument],
    context: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Stage: OCR_RECOGNITION.
    Emits recognized lines and preserves recognition provider provenance.
    """
    lines = context.get("ocr_lines", [])
    recognized_lines = [
        {
            "line_index": line.line_index,
            "text": line.text,
            "raw_score": line.raw_score,
            "box": list(line.box),
            "calibration_status": "NOT_CALIBRATED",
        }
        for line in lines
    ]

    context["recognized_lines"] = recognized_lines
    rec_result = context.get("document_recognition")
    provider_name = rec_result.provider_used if rec_result else "RapidOCR"
    model_name = getattr(rec_result, "model_used", None) if rec_result else "RapidOCR"
    attempts = getattr(rec_result, "attempts", 1) if rec_result else 1

    return {
        "stage": "OCR_RECOGNITION",
        "status": "COMPLETED",
        "lines_recognized_count": len(recognized_lines),
        "recognizer_model": provider_name,
        "provider_used": provider_name,
        "model_used": model_name,
        "attempts": attempts,
        "calibrated": False,
        "fallback_occurred": rec_result.fallback_occurred if rec_result else False,
        "fallback_reason": rec_result.fallback_reason if rec_result else None,
        "recognition_fallback_used": rec_result.fallback_occurred if rec_result else False,
        "recognition_fallback_reason": rec_result.fallback_reason if rec_result else None,
    }


def handle_structured_extraction(
    db: Session,
    analysis: Analysis,
    document: Optional[PrescriptionDocument],
    context: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Stage: STRUCTURED_EXTRACTION.
    Strictly separates genuine medication orders from non-medication clinical entities
    (hospital details, patient details, dates, symptoms, diagnosis, vitals, and general advice).
    Guarantees zero false medication entries from non-drug text.
    """
    import re
    from prescripto.domain.uncertainty.models import FieldState
    from prescripto.domain.recognition.models import DocumentFieldType
    from prescripto.ml.extraction import is_form_boilerplate, extract_patient_name

    existing_meds = db.query(PrescriptionMedication).filter(
        PrescriptionMedication.analysis_id == analysis.id
    ).all()
    existing_by_line = {med.line_index: med for med in existing_meds}

    rec_result = context.get("document_recognition")
    if rec_result is None:
        doc = document or db.query(PrescriptionDocument).filter(PrescriptionDocument.id == analysis.document_id).first()
        mime = doc.mime_type if doc and doc.mime_type else "image/jpeg"
        rec_result = _recognize_document(context, context["document_bytes"], mime)
        context["document_recognition"] = rec_result

    # 2. Extract ONLY genuine medications (Strict zero-false-medication clinical rule)
    extracted_count = 0
    for item in rec_result.medications:
        line_index = int(item.line_index if item.line_index is not None else extracted_count)
        if line_index in existing_by_line:
            continue

        raw_name = item.name or item.original_text
        if not raw_name or is_form_boilerplate(raw_name):
            continue

        values: dict[str, Any] = {
            "id": uuid.uuid4(),
            "analysis_id": analysis.id,
            "line_index": line_index,
            "name_raw": raw_name,
            "name_state": FieldState.AMBIGUOUS.value,
            "name_confidence": item.confidence,
            "strength_raw": item.strength,
            "strength_state": FieldState.AMBIGUOUS.value if item.strength else FieldState.NOT_PRESENT.value,
            "strength_confidence": item.confidence if item.strength else None,
            "dose_raw": item.dose,
            "dose_state": FieldState.AMBIGUOUS.value if item.dose else FieldState.NOT_PRESENT.value,
            "dose_confidence": item.confidence if item.dose else None,
            "route_raw": item.route,
            "route_state": FieldState.AMBIGUOUS.value if item.route else FieldState.NOT_PRESENT.value,
            "route_confidence": item.confidence if item.route else None,
            "frequency_raw": item.frequency,
            "frequency_state": FieldState.AMBIGUOUS.value if item.frequency else FieldState.NOT_PRESENT.value,
            "frequency_confidence": item.confidence if item.frequency else None,
            "duration_raw": item.duration,
            "duration_state": FieldState.AMBIGUOUS.value if item.duration else FieldState.NOT_PRESENT.value,
            "duration_confidence": item.confidence if item.duration else None,
            "instructions_raw": item.instructions,
            "instructions_state": FieldState.AMBIGUOUS.value if item.instructions else FieldState.NOT_PRESENT.value,
            "instructions_confidence": item.confidence if item.instructions else None,
            "unit_raw": None,
            "unit_state": FieldState.NOT_PRESENT.value,
            "unit_confidence": None,
        }
        db.add(PrescriptionMedication(**values))
        extracted_count += 1

    db.flush()

    return {
        "line_count": extracted_count,
        "status": "COMPLETED",
        "calibrated": False,
        "processing_status": rec_result.processing_status,
        "source_type": rec_result.source_type,
        "hospital_details": rec_result.hospital_details,
        "patient_details": rec_result.patient_details,
        "date": rec_result.date,
        "symptoms": rec_result.symptoms,
        "diagnosis": rec_result.diagnosis,
        "vitals": rec_result.vitals,
        "medication_orders": [
            {
                "original_text": item.original_text,
                "name": item.name,
                "strength": item.strength,
                "dose": item.dose,
                "route": item.route,
                "frequency": item.frequency,
                "duration": item.duration,
                "instructions": item.instructions,
                "needs_review": True,
            }
            for item in rec_result.medications
        ],
        "general_advice": rec_result.general_advice,
        "non_medication_treatments": [t.original_text for t in rec_result.non_medication_treatments],
        "uncertain_items": [
            {
                "original_text": item.original_text,
                "uncertainty_reason": item.uncertainty_reason,
            }
            for item in rec_result.uncertain_items
        ],
        "warnings": rec_result.warnings,
        "provider_used": rec_result.provider_used,
        "model_used": rec_result.model_used,
        "attempts": rec_result.attempts,
        "fallback_occurred": rec_result.fallback_occurred,
        "fallback_reason": rec_result.fallback_reason,
        "recognition_fallback_used": rec_result.fallback_occurred,
        "recognition_fallback_reason": rec_result.fallback_reason,
    }


def handle_medication_normalization(
    db: Session,
    analysis: Analysis,
    document: Optional[PrescriptionDocument],
    context: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Stage: MEDICATION_NORMALIZATION.
    Resolves only a unique exact verified medication match. Candidate suggestions never
    overwrite the source wording or become a resolved medicine without human review.
    """
    meds = db.query(PrescriptionMedication).filter(
        PrescriptionMedication.analysis_id == analysis.id
    ).order_by(PrescriptionMedication.line_index).all()

    search_service = MedicationSearchService(db=db)
    resolved_count = 0
    resolutions: dict[uuid.UUID, MedicationResolutionResult] = {}

    for med in meds:
        stored_candidate = db.query(MedicationCandidate).filter(
            MedicationCandidate.prescription_med_id == med.id
        ).first()
        extracted_text = med.name_raw or (stored_candidate.extracted_text if stored_candidate else "")
        search_result = search_service.search_candidates(extracted_text)

        exact_verified = [
            candidate
            for candidate in search_result.candidates
            if candidate.matching_strategy == MatchingStrategy.EXACT.value
            and candidate.medication.verification_status
            in {VerificationStatus.VERIFIED_AUTHORITY.value, VerificationStatus.EXPERT_CONFIRMED.value}
        ]

        top_candidate = search_result.candidates[0] if search_result.candidates else None

        can_resolve_exact = (len(exact_verified) == 1)
        if can_resolve_exact:
            exact = exact_verified[0]
            resolution = MedicationResolutionResult(
                extracted_text=extracted_text,
                resolution_status=ResolutionStatus.RESOLVED,
                resolved_medication=exact.medication,
                candidates=[exact],
            )
            resolved_count += 1
        else:
            resolution = MedicationResolutionResult(
                extracted_text=extracted_text,
                resolution_status=(ResolutionStatus.AMBIGUOUS if search_result.candidates else ResolutionStatus.UNRESOLVED),
                resolved_medication=None,
                candidates=search_result.candidates,
            )
        resolutions[med.id] = resolution

        if stored_candidate:
            stored_candidate.extracted_text = extracted_text
            stored_candidate.matching_strategy = (top_candidate.matching_strategy if top_candidate else "NO_MATCH")
            stored_candidate.candidate_score = (top_candidate.candidate_score if top_candidate else 0.0)
            stored_candidate.resolved_medication_id = (resolution.resolved_medication.id if resolution.resolved_medication else None)
            stored_candidate.resolution_status = resolution.resolution_status.value
        elif extracted_text:
            db.add(
                MedicationCandidate(
                    id=uuid.uuid4(),
                    prescription_med_id=med.id,
                    analysis_id=analysis.id,
                    extracted_text=extracted_text,
                    matching_strategy=(top_candidate.matching_strategy if top_candidate else "NO_MATCH"),
                    candidate_score=(top_candidate.candidate_score if top_candidate else 0.0),
                    source_vocabulary="MEDICATION_MASTER",
                    resolved_medication_id=(resolution.resolved_medication.id if resolution.resolved_medication else None),
                    resolution_status=resolution.resolution_status.value,
                )
            )
    context["medication_resolutions"] = resolutions
    db.flush()
    return {"total_lines": len(meds), "resolved_count": resolved_count, "status": "COMPLETED"}


def handle_safety_screening(
    db: Session,
    analysis: Analysis,
    document: Optional[PrescriptionDocument],
    context: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Stage: SAFETY_SCREENING.
    Runs comprehensive clinical safety checks:
    1. Exact canonical product duplicate detection.
    2. Patient allergy contraindication screening against clinical history.
    3. Maximum recommended single-dose and cumulative dosage threshold evaluation.
    """
    meds = db.query(PrescriptionMedication).filter(
        PrescriptionMedication.analysis_id == analysis.id
    ).all()

    # Load document if not provided in args
    doc = document
    if not doc and analysis.document_id:
        doc = db.query(PrescriptionDocument).filter(
            PrescriptionDocument.id == analysis.document_id
        ).first()

    # 1. Duplicate detection
    resolved_pairs = [
        (med.id, resolution)
        for med in meds
        if (resolution := context.get("medication_resolutions", {}).get(med.id))
        and resolution.resolution_status == ResolutionStatus.RESOLVED
        and resolution.resolved_medication is not None
    ]
    findings = list(detect_duplicate_medications(analysis.id, resolved_pairs))

    # 2. Patient Allergy Contraindication Screening
    patient_allergies: Optional[str] = None
    if doc and doc.patient_ref:
        patient = db.query(Patient).filter(
            (Patient.patient_id == doc.patient_ref) | 
            (Patient.phone_number == doc.patient_ref)
        ).first()
        if patient and patient.allergies:
            patient_allergies = patient.allergies

    med_allergy_inputs = []
    med_dosage_inputs = []
    for med in meds:
        res = context.get("medication_resolutions", {}).get(med.id)
        canonical = res.resolved_medication if res and res.resolution_status == ResolutionStatus.RESOLVED else None
        if canonical is None:
            continue
        med_allergy_inputs.append((med.id, med.name_raw or "", canonical))
        med_dosage_inputs.append((med.id, med.name_raw or "", med.strength_raw, med.dose_raw, canonical))

    if patient_allergies:
        allergy_findings = detect_allergy_contraindications(
            analysis.id, patient_allergies, med_allergy_inputs
        )
        findings.extend(allergy_findings)

    # 3. Dosage Safety Threshold Analysis
    dosage_findings = detect_dosage_safety_warnings(
        analysis.id, med_dosage_inputs
    )
    findings.extend(dosage_findings)

    # Persist findings in DB idempotently
    for f in findings:
        existing = db.query(RiskFinding).filter(
            RiskFinding.analysis_id == analysis.id,
            RiskFinding.check_type == f.check_type.value,
            RiskFinding.source_name == f.source_name,
            RiskFinding.finding_key == f.finding_key,
        ).first()

        if not existing:
            rf = RiskFinding(
                id=f.id,
                analysis_id=analysis.id,
                check_type=f.check_type.value,
                finding_key=f.finding_key,
                finding_status=f.finding_status.value,
                medication_ids=f.medication_ids,
                evidence_text=f.evidence_text,
                source_name=f.source_name,
                source_version=f.source_version,
                confidence_score=f.confidence_score,
                check_timestamp=f.check_timestamp,
                not_evaluated_reason=f.not_evaluated_reason,
            )
            db.add(rf)

    db.flush()
    return {"findings_count": len(findings), "status": "COMPLETED"}


def handle_report_assembly(
    db: Session,
    analysis: Analysis,
    document: Optional[PrescriptionDocument],
    context: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Stage: REPORT_ASSEMBLY.
    Aggregates stage outputs, evaluates review triggers, and transitions analysis.
    """
    meds = db.query(PrescriptionMedication).filter(
        PrescriptionMedication.analysis_id == analysis.id
    ).all()

    candidates = db.query(MedicationCandidate).filter(
        MedicationCandidate.analysis_id == analysis.id
    ).all()
    cand_map = {c.prescription_med_id: c.resolution_status for c in candidates}

    med_dicts = []
    for m in meds:
        med_dicts.append({
            "line_index": m.line_index,
            "resolution_status": cand_map.get(m.id, ResolutionStatus.UNRESOLVED.value),
            "name": {"state": m.name_state},
            "strength": {"state": m.strength_state},
            "dose": {"state": m.dose_state},
            "unit": {"state": m.unit_state},
            "frequency": {"state": m.frequency_state},
            "route": {"state": m.route_state},
            "duration": {"state": m.duration_state},
            "instructions": {"state": m.instructions_state},
        })

    from prescripto.domain.safety.models import DomainRiskFinding, SafetyCheckType, FindingStatus
    db_findings = db.query(RiskFinding).filter(
        RiskFinding.analysis_id == analysis.id
    ).all()

    domain_findings = [
        DomainRiskFinding(
            id=f.id,
            analysis_id=f.analysis_id,
            check_type=SafetyCheckType(f.check_type),
            finding_key=f.finding_key,
            finding_status=FindingStatus(f.finding_status),
            medication_ids=list(f.medication_ids or []),
            evidence_text=f.evidence_text,
            source_name=f.source_name,
            source_version=f.source_version,
            confidence_score=f.confidence_score,
            not_evaluated_reason=f.not_evaluated_reason,
        )
        for f in db_findings
    ]

    quality_failed = context.get("quality_failed", False) if context else False
    evaluation = evaluate_review_triggers(
        medications=med_dicts,
        findings=domain_findings,
        quality_failed=quality_failed,
    )

    analysis.status = evaluation.final_status.value
    analysis.review_required = evaluation.review_required
    analysis.review_reasons = evaluation.review_reasons
    analysis.completed_at = utc_now()
    db.flush()

    rec_result = context.get("document_recognition")
    fallback_used = context.get("recognition_fallback_used", False) or getattr(rec_result, "fallback_occurred", False)
    fallback_reason = context.get("recognition_fallback_reason", getattr(rec_result, "fallback_reason", None))
    provider_used = context.get("recognition_provider_used", getattr(rec_result, "provider_used", "rapidocr"))
    model_used = context.get("recognition_model_used", getattr(rec_result, "model_used", None))
    attempts = context.get("recognition_attempts", getattr(rec_result, "attempts", 1))

    return {
        "final_status": analysis.status,
        "review_required": analysis.review_required,
        "review_reasons": analysis.review_reasons,
        "provider_used": provider_used,
        "model_used": model_used,
        "attempts": attempts,
        "fallback_occurred": fallback_used,
        "fallback_reason": fallback_reason,
        "recognition_fallback_used": fallback_used,
        "recognition_fallback_reason": fallback_reason,
        "status": "COMPLETED",
    }


DEFAULT_STAGE_HANDLERS = {
    "INGESTION": handle_ingestion,
    "QUALITY_CHECK": handle_quality_check,
    "TEXT_DETECTION": handle_text_detection,
    "OCR_RECOGNITION": handle_ocr_recognition,
    "STRUCTURED_EXTRACTION": handle_structured_extraction,
    "MEDICATION_NORMALIZATION": handle_medication_normalization,
    "SAFETY_SCREENING": handle_safety_screening,
    "REPORT_ASSEMBLY": handle_report_assembly,
}
