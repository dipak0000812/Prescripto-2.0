"""Vision and OCR providers with conservative prescription entity classification."""
from __future__ import annotations

import json
import logging
import re
import time
from abc import ABC, abstractmethod
from io import BytesIO
from typing import Any, Dict, List, Optional, Tuple

from google import genai
from google.genai import types
from pydantic import BaseModel, ConfigDict, Field, ValidationError
from PIL import Image, UnidentifiedImageError
import httpx

from prescripto.config.settings import settings
from prescripto.domain.recognition.models import (
    DocumentFieldType,
    DocumentItem,
    DocumentRecognitionResult,
)
from prescripto.ml.extraction import extract_prescription_fields, is_form_boilerplate

logger = logging.getLogger("prescripto.recognition")


class RecognitionError(Exception):
    """Base exception for recognition provider failures."""

    def __init__(
        self,
        message: str,
        attempts: int = 1,
        model_used: Optional[str] = None,
    ) -> None:
        super().__init__(message)
        self.attempts = attempts
        self.model_used = model_used


class RecognitionNonRetryableError(RecognitionError):
    """Recognition failures that will not recover with a worker retry."""
    pass


class RecognitionConfigurationError(RecognitionNonRetryableError):
    """Raised when the selected recognition provider is not configured."""
    pass


class RecognitionAuthenticationError(RecognitionNonRetryableError):
    """Raised when Gemini rejects backend credentials."""
    pass


class RecognitionQuotaError(RecognitionNonRetryableError):
    """Raised when Gemini reports a rate or quota limit."""
    pass


class RecognitionTimeoutError(RecognitionError):
    """Raised when Gemini does not respond before the request timeout."""
    pass


class RecognitionModelUnavailableError(RecognitionNonRetryableError):
    """Raised when the configured Gemini model is unavailable."""
    pass


class RecognitionInvalidImageError(RecognitionNonRetryableError):
    """Raised when the uploaded image cannot be decoded for model input."""
    pass


class RecognitionMalformedResponseError(RecognitionNonRetryableError):
    """Raised when the model response does not match the extraction schema."""
    pass


# ---------------------------------------------------------------------------
# Clinical Semantic Classifier for Local OCR & Text Extraction
# ---------------------------------------------------------------------------

DATE_REGEX = re.compile(
    r"\b(?:"
    r"\d{1,2}[/-]\d{1,2}[/-]\d{2,4}"
    r"|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{4}"
    r"|\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{2,4}"
    r")\b",
    re.IGNORECASE,
)

VITALS_REGEX = re.compile(
    r"\b(?:"
    r"BP\s*[:=\-–]?\s*\d{2,3}\s*/\s*\d{2,3}"
    r"|BP\s*[:=\-–]?\s*\d{4,6}"
    r"|Pulse\s*[:=\-–]?\s*\d{2,3}"
    r"|HR\s*[:=\-–]?\s*\d{2,3}"
    r"|Temp(?:erature)?\s*[:=\-–]?\s*\d{2,3}(?:\.\d+)?\s*(?:F|C)?"
    r"|SpO2\s*[:=\-–]?\s*\d{2,3}%?"
    r"|Weight\s*[:=\-–]?\s*\d{2,3}(?:\.\d+)?\s*(?:kg|lbs)?"
    r"|Wt\s*[:=\-–]?\s*\d{2,3}"
    r"|Height\s*[:=\-–]?\s*\d{2,3}(?:\.\d+)?\s*(?:cm|ft)?"
    r"|R/?R\s*[:=\-–]?\s*\d{1,2}"
    r")\b",
    re.IGNORECASE,
)

# Common symptoms; corrupted strings are deliberately not corrected by guesswork.
SYMPTOMS_KEYWORDS = [
    "giddiness", "restlessness", "headache", "fever",
    "cough", "cold", "nausea", "vomiting", "vomitting", "chest pain", "abdominal pain",
    "stomach ache", "weakness", "dizziness", "fatigue", "body ache", "dyspnea",
    "breathlessness", "diarrhea", "diarrhoea", "loose motion", "constipation",
    "rash", "itching", "swelling", "edema", "throat pain", "sore throat", "chills",
]

DIAGNOSIS_KEYWORDS = [
    "acute gastroenteritis", "gastroenteritis", "hypertension", "htn", "diabetes",
    "t2dm", "urti", "lrti", "bronchitis", "pneumonia", "typhoid", "malaria",
    "dengue", "migraine", "asthma", "gerd", "gastritis", "pharyngitis", "tonsillitis",
    "viral fever", "uti", "urinary tract infection", "allergic rhinitis",
]

ADVICE_KEYWORDS = [
    "adequate fluid intake", "fluid intake", "drink plenty of water", "drink water",
    "ors 2 sachets", "ors",
    "bed rest", "rest for", "light diet", "soft diet", "low salt", "avoid oily",
    "avoid spicy", "steam inhalation", "salt water gargle", "warm water",
    "review after", "review in", "follow up", "visit if pain",
]

NON_MED_TREATMENT_KEYWORDS = [
    "cold compress", "warm compress", "wound dressing", "dressing", "bandage",
    "steam inhalation", "hot water bag", "physiotherapy", "ice pack",
]

MEDICATION_SIGNS = [
    r"\btab(?:let)?s?\b", r"\bcap(?:sule)?s?\b", r"\bsyr(?:up)?\b",
    r"\binj(?:ection)?\b", r"\bointment\b", r"\bcream\b", r"\bdrops?\b",
    r"\bmg\b", r"\bmcg\b", r"\bml\b", r"\b%\b", r"\biv\b", r"\bim\b",
    r"\bstat\b", r"\bod\b", r"\bbd\b", r"\bbid\b", r"\btds\b", r"\btid\b",
    r"\bqid\b", r"\bsos\b", r"\bhs\b", r"\bdextrose\b", r"\bparacetamol\b",
    r"\bamoxicillin\b", r"\bomeprazole\b", r"\bpantoprazole\b", r"\bcetirizine\b",
    r"\bmetformin\b", r"\batorvastatin\b", r"\bazithromycin\b", r"\bcrocin\b",
    r"\bdolo\b", r"\baugmentin\b", r"\bcipro\b",
]


def classify_text_line(text: str) -> Tuple[DocumentFieldType, str, Optional[str]]:
    """
    Classifies a raw text line into a clinical document entity type.
    Returns: (field_type, interpreted_text, uncertainty_reason)
    """
    cleaned = text.strip()
    lower = cleaned.lower()

    if not cleaned or len(cleaned) < 2:
        return DocumentFieldType.UNCERTAIN_UNREADABLE, cleaned, "Line too short or empty"

    # 1. Boilerplate or administrative lines
    if is_form_boilerplate(cleaned):
        return DocumentFieldType.HOSPITAL_DETAILS, cleaned, None

    # 2. Hospital / Doctor headers
    if re.search(r"\b(?:Dr\.|MBBS|MD|MS|Clinic|Hospital|Center|Centre|Reg\.?\s*No|Ph:|Phone|Department)\b", cleaned, re.IGNORECASE):
        return DocumentFieldType.HOSPITAL_DETAILS, cleaned, None

    # 3. Patient identity lines
    if re.search(r"\b(?:Patient(?:\s+Name)?|Pt\.?\s*Name|Age|Gender|Sex|DOB|UHID|IPD|OPD\s*No)\b", cleaned, re.IGNORECASE) and not re.search(r"\b(?:\d+mg|\d+ml|tabs?|caps?)\b", cleaned, re.IGNORECASE):
        return DocumentFieldType.PATIENT_DETAILS, cleaned, None

    # 4. Explicit date lines; unlabelled digit strings may instead be identifiers.
    if cleaned.lower().startswith("date:") or cleaned.lower().startswith("dt:") or (DATE_REGEX.search(cleaned) and len(cleaned.split()) <= 2):
        match = DATE_REGEX.search(cleaned)
        return DocumentFieldType.DATE, cleaned, None

    # 5. Vital signs (e.g. BP 110/70, or OCR 07011, Pulse 72, etc.)
    if VITALS_REGEX.search(cleaned) or (len(cleaned) <= 7 and re.match(r"^\d{2,3}/\d{2,3}$", cleaned)):
        return DocumentFieldType.VITAL_SIGNS, cleaned, None

    # A sig line is not a second medicine; it is unlinked until human/model grouping.
    if re.match(r"^(?:sig|directions?|instructions?)\s*:", cleaned, re.IGNORECASE):
        return DocumentFieldType.GENERAL_ADVICE, cleaned, None

    # 6. Symptoms and Complaints with explicit prefix
    if re.search(r"\b(?:C/o|Complaints?|Symptoms?)\b", cleaned, re.IGNORECASE):
        clean_sym = re.sub(r"^(?:C/o|Complaints?|Symptoms?)\s*[:\-]?\s*", "", cleaned, flags=re.IGNORECASE)
        return DocumentFieldType.SYMPTOMS_COMPLAINTS, clean_sym or cleaned, None

    # 7. Diagnosis / Clinical Impression with explicit prefix
    if re.search(r"\b(?:Impression|Imp|Diagnosis|Diag|Dx|Provisional)\s*[:\-]", cleaned, re.IGNORECASE):
        clean_diag = re.sub(r"^(?:Impression|Imp|Diagnosis|Diag|Dx|Provisional)\s*[:\-]?\s*", "", cleaned, flags=re.IGNORECASE)
        return DocumentFieldType.DIAGNOSIS, clean_diag or cleaned, None

    # 8. Check for Genuine Medication Order (Tab, Cap, mg, ml, Paracetamol, etc.)
    has_med_sign = any(re.search(pattern, cleaned, re.IGNORECASE) for pattern in MEDICATION_SIGNS)
    has_dose_sign = bool(re.search(r"\b\d+(?:\.\d+)?\s*(?:mg|mcg|g|ml|%|tab|cap)\b", cleaned, re.IGNORECASE))
    if (has_med_sign or has_dose_sign) and not re.search(r"\b(?:Adv(?:ice)?|Diet|Precautions?)\s*[:\-]", cleaned, re.IGNORECASE):
        return DocumentFieldType.MEDICATION_ORDER, cleaned, None

    # Check legible symptom keywords without rewriting corrupted OCR (only if not a medication).
    for sym in SYMPTOMS_KEYWORDS:
        if sym in lower:
            return DocumentFieldType.SYMPTOMS_COMPLAINTS, cleaned, None

    for diag in DIAGNOSIS_KEYWORDS:
        if diag in lower:
            return DocumentFieldType.DIAGNOSIS, cleaned, None

    # 9. General Advice (e.g. Adequate fluid intake, ORS 2 sachets, Bed rest)
    if re.search(r"\b(?:Adv(?:ice)?|Diet|Precautions?)\s*[:\-]", cleaned, re.IGNORECASE):
        clean_adv = re.sub(r"^(?:Adv(?:ice)?|Diet|Precautions?)\s*[:\-]?\s*", "", cleaned, flags=re.IGNORECASE)
        return DocumentFieldType.GENERAL_ADVICE, clean_adv or cleaned, None

    for adv in ADVICE_KEYWORDS:
        if adv in lower:
            return DocumentFieldType.GENERAL_ADVICE, cleaned, None

    # 10. Non-Medication Treatments (Cold compress, steam inhalation)
    for nmt in NON_MED_TREATMENT_KEYWORDS:
        if nmt in lower:
            return DocumentFieldType.NON_MEDICATION_TREATMENT, cleaned, None

    # 12. Fallback: Standalone text without dosage or medical context
    # If it looks like illegible cursive or symbols, mark as UNCERTAIN_UNREADABLE
    if (
        not re.search(r"[aeiouAEIOU]", cleaned)
        or re.search(r"^[^\w\s]+$", cleaned)
        or len(cleaned.split()) > 7
        or re.fullmatch(r"\d{4,}", cleaned)
    ):
        return DocumentFieldType.UNCERTAIN_UNREADABLE, cleaned, "Unclear handwriting without identifiable medical context"

    return DocumentFieldType.UNCERTAIN_UNREADABLE, cleaned, "Unclassified text; human review required"


# ---------------------------------------------------------------------------
# Recognition Provider Abstraction
# ---------------------------------------------------------------------------

class RecognitionProvider(ABC):
    """Abstract base class for vision and OCR prescription recognition."""

    @abstractmethod
    def recognize_document(
        self, image_bytes: bytes, mime_type: str = "image/jpeg"
    ) -> DocumentRecognitionResult:
        """Processes prescription image bytes and returns structured recognition result."""
        pass


class LocalRapidOCRProvider(RecognitionProvider):
    """
    Local OCR engine using ONNX PaddleOCR (RapidOCR) with conservative
    rule-based clinical entity classification and safety filtering.
    """

    def __init__(self, ocr_runtime: Optional[object] = None) -> None:
        if ocr_runtime is not None:
            self._runtime = ocr_runtime
        else:
            from prescripto.ml.rapid_runtime import RapidOCRRuntime
            self._runtime = RapidOCRRuntime()

    def classify_text_line(self, text: str) -> DocumentItem:
        field_type, interpreted, uncertainty_reason = classify_text_line(text)
        return DocumentItem(
            field_type=field_type,
            original_text=text,
            interpreted_text=interpreted,
            needs_review=(uncertainty_reason is not None or field_type == DocumentFieldType.UNCERTAIN_UNREADABLE),
            uncertainty_reason=uncertainty_reason,
        )


    def recognize_document(
        self, image_bytes: bytes, mime_type: str = "image/jpeg"
    ) -> DocumentRecognitionResult:
        start_time = time.time()
        try:
            lines = self._runtime.recognize_document(image_bytes)
        except Exception as e:
            logger.error("Local OCR recognition failed (%s)", type(e).__name__)
            raise RecognitionError(
                "LOCAL_OCR_ERROR: Local prescription recognition failed."
            ) from e

        items: List[DocumentItem] = []
        hospital_details: List[str] = []
        patient_details: Dict[str, Any] = {}
        prescription_date: Optional[str] = None
        symptoms: List[str] = []
        diagnosis: List[str] = []
        vitals: List[str] = []
        medications: List[DocumentItem] = []
        non_med_treatments: List[DocumentItem] = []
        general_advice: List[str] = []
        uncertain_items: List[DocumentItem] = []

        for line in lines:
            raw_text = str(line.text or "").strip()
            if not raw_text:
                continue

            field_type, interpreted, uncertainty_reason = classify_text_line(raw_text)

            item = DocumentItem(
                field_type=field_type,
                original_text=raw_text,
                interpreted_text=interpreted,
                confidence=None,
                confidence_is_calibrated=False,
                needs_review=(uncertainty_reason is not None or field_type == DocumentFieldType.UNCERTAIN_UNREADABLE),
                uncertainty_reason=uncertainty_reason,
                line_index=line.line_index,
                box=list(line.box) if line.box else None,
            )

            if field_type == DocumentFieldType.HOSPITAL_DETAILS:
                hospital_details.append(interpreted)
            elif field_type == DocumentFieldType.PATIENT_DETAILS:
                # Extract patient info if possible
                if re.search(r"\b(?:Name|Patient)\b", raw_text, re.IGNORECASE):
                    patient_details["name"] = interpreted
                else:
                    patient_details["meta"] = interpreted
            elif field_type == DocumentFieldType.DATE:
                if not prescription_date:
                    prescription_date = interpreted
            elif field_type == DocumentFieldType.SYMPTOMS_COMPLAINTS:
                symptoms.append(interpreted)
            elif field_type == DocumentFieldType.DIAGNOSIS:
                diagnosis.append(interpreted)
            elif field_type == DocumentFieldType.VITAL_SIGNS:
                vitals.append(interpreted)
            elif field_type == DocumentFieldType.MEDICATION_ORDER:
                # Extract specific field spans
                fields = extract_prescription_fields(raw_text)
                name_val = fields.get("name", {}).get("raw") or raw_text
                strength_val = fields.get("strength", {}).get("raw")
                dose_val = fields.get("dose", {}).get("raw")
                route_val = fields.get("route", {}).get("raw")
                freq_val = fields.get("frequency", {}).get("raw")
                dur_val = fields.get("duration", {}).get("raw")
                inst_val = fields.get("instructions", {}).get("raw")

                item.name = name_val
                item.strength = strength_val
                item.dose = dose_val
                item.route = route_val
                item.frequency = freq_val
                item.duration = dur_val
                item.instructions = inst_val

                medications.append(item)
            elif field_type == DocumentFieldType.NON_MEDICATION_TREATMENT:
                non_med_treatments.append(item)
            elif field_type == DocumentFieldType.GENERAL_ADVICE:
                general_advice.append(interpreted)
            elif field_type == DocumentFieldType.UNCERTAIN_UNREADABLE:
                uncertain_items.append(item)

            items.append(item)

        duration = round(time.time() - start_time, 3)
        logger.info(
            "local_ocr_completed",
            extra={"items_count": len(items), "duration_s": duration, "meds_count": len(medications)},
        )

        return DocumentRecognitionResult(
            items=items,
            hospital_details=hospital_details,
            patient_details=patient_details,
            date=prescription_date,
            symptoms=symptoms,
            diagnosis=diagnosis,
            vitals=vitals,
            medications=medications,
            non_medication_treatments=non_med_treatments,
            general_advice=general_advice,
            uncertain_items=uncertain_items,
            provider_used="rapidocr",
            model_used="rapidocr",
            attempts=1,
            fallback_occurred=False,
            fallback_reason=None,
            source_type="local_ocr_transcription_unverified",
            processing_status="needs_review",
            warnings=["OCR text is not verified; a clinician or pharmacist must review it."],
        )


class GeminiMedication(BaseModel):
    model_config = ConfigDict(extra="ignore")

    original_text: str
    name: Optional[str] = None
    strength: Optional[str] = None
    dose: Optional[str] = None
    route: Optional[str] = None
    frequency: Optional[str] = None
    duration: Optional[str] = None
    instructions: Optional[str] = None


class GeminiUncertainItem(BaseModel):
    model_config = ConfigDict(extra="ignore")

    original_text: str
    uncertainty_reason: str = "Unclear or unclassified text"


class GeminiPatientDetails(BaseModel):
    model_config = ConfigDict(extra="ignore")

    name: Optional[str] = None
    age: Optional[str] = None
    gender: Optional[str] = None
    patient_id: Optional[str] = None
    other: List[str] = Field(default_factory=list)


class GeminiPrescriptionOutput(BaseModel):
    model_config = ConfigDict(extra="ignore")

    hospital_details: List[str] = Field(default_factory=list)
    patient_details: GeminiPatientDetails = Field(default_factory=GeminiPatientDetails)
    date: Optional[str] = None
    symptoms: List[str] = Field(default_factory=list)
    diagnosis: List[str] = Field(default_factory=list)
    vitals: List[str] = Field(default_factory=list)
    medications: List[GeminiMedication] = Field(default_factory=list)
    non_medication_treatments: List[str] = Field(default_factory=list)
    general_advice: List[str] = Field(default_factory=list)
    uncertain_items: List[GeminiUncertainItem] = Field(default_factory=list)


class GeminiVisionProvider(RecognitionProvider):
    """Transcribes prescription images with Google's official GenAI SDK."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: Optional[str] = None,
        fallback_model: Optional[str] = None,
        timeout_seconds: float = 20.0,
        backoff_seconds: float = 2.0,
        client: Optional[genai.Client] = None,
    ) -> None:
        self.api_key = api_key if api_key is not None else settings.GEMINI_API_KEY
        self.model_name = model_name or settings.GEMINI_MODEL
        self.fallback_model = fallback_model or settings.GEMINI_FALLBACK_MODEL
        self.timeout_seconds = timeout_seconds
        self.backoff_seconds = backoff_seconds
        self.client = client

    @staticmethod
    def _classify_exception(error: Exception) -> Tuple[Optional[int], str, bool, bool, bool]:
        """
        Extracts code, message, and error category flags:
        (code, message, is_auth, is_not_found, is_transient)
        """
        code = getattr(error, "code", None) or getattr(error, "status_code", None)
        if isinstance(code, str) and code.isdigit():
            code = int(code)
        code_text = str(code).upper() if code is not None else ""
        msg = str(error).upper()

        if isinstance(error, (TimeoutError, httpx.TimeoutException)):
            return 504, str(error), False, False, True

        is_auth = (
            code in (401, 403)
            or code_text in ("UNAUTHENTICATED", "PERMISSION_DENIED")
            or "API KEY NOT VALID" in msg
            or "API_KEY_INVALID" in msg
            or "INVALID API KEY" in msg
        )
        if is_auth:
            return code or 401, str(error), True, False, False

        is_not_found = (
            code == 404
            or code_text == "NOT_FOUND"
            or "NOT_FOUND" in msg
            or "MODEL_NOT_FOUND" in msg
        )
        if is_not_found:
            return 404, str(error), False, True, False

        is_transient = (
            code in (503, 504, 429)
            or code_text in ("UNAVAILABLE", "DEADLINE_EXCEEDED", "RESOURCE_EXHAUSTED", "TOO MANY REQUESTS")
            or "RESOURCE_EXHAUSTED" in msg
            or "TOO MANY REQUESTS" in msg
            or "UNAVAILABLE" in msg
            or "DEADLINE_EXCEEDED" in msg
            or "HIGH DEMAND" in msg
            or "503" in msg
            or "504" in msg
            or "429" in msg
        )
        return code, str(error), False, False, is_transient

    def _execute_gemini_call(
        self,
        client: genai.Client,
        model: str,
        prompt: str,
        image_bytes: bytes,
        mime_type: str,
        config: types.GenerateContentConfig,
    ) -> GeminiPrescriptionOutput:
        response = client.models.generate_content(
            model=model,
            contents=[prompt, types.Part.from_bytes(data=image_bytes, mime_type=mime_type)],
            config=config,
        )
        response_text = getattr(response, "text", None)
        if not isinstance(response_text, str) or not response_text.strip():
            raise RecognitionMalformedResponseError(
                "GEMINI_MALFORMED_RESPONSE: Gemini returned no structured prescription text."
            )
        cleaned_text = response_text.strip()
        if cleaned_text.startswith("```"):
            lines = cleaned_text.splitlines()
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            cleaned_text = "\n".join(lines).strip()
        try:
            return GeminiPrescriptionOutput.model_validate_json(cleaned_text)
        except (ValidationError, ValueError, json.JSONDecodeError) as error:
            raise RecognitionMalformedResponseError(
                "GEMINI_MALFORMED_RESPONSE: Gemini returned data that did not match the prescription schema."
            ) from error

    @staticmethod
    def _prepare_image(image_bytes: bytes, mime_type: str) -> Tuple[bytes, str]:
        if not image_bytes:
            raise RecognitionInvalidImageError(
                "INVALID_IMAGE: The uploaded image is empty or unreadable."
            )
        try:
            with Image.open(BytesIO(image_bytes)) as image:
                image.verify()
            with Image.open(BytesIO(image_bytes)) as image:
                if image.format == "TIFF":
                    converted = BytesIO()
                    image.convert("RGB").save(converted, format="PNG")
                    return converted.getvalue(), "image/png"
                if mime_type not in {"image/jpeg", "image/png", "image/webp"}:
                    raise RecognitionInvalidImageError(
                        "INVALID_IMAGE: Use a valid JPEG, PNG, or TIFF prescription image."
                    )
                return image_bytes, mime_type
        except RecognitionInvalidImageError:
            raise
        except (UnidentifiedImageError, OSError, Image.DecompressionBombError) as error:
            raise RecognitionInvalidImageError(
                "INVALID_IMAGE: The uploaded file is not a readable image. Upload a JPEG, PNG, or TIFF."
            ) from error

    def recognize_document(
        self, image_bytes: bytes, mime_type: str = "image/jpeg"
    ) -> DocumentRecognitionResult:
        effective_key = (self.api_key if self.api_key is not None else settings.GEMINI_API_KEY) or ""
        if not effective_key.strip():
            raise RecognitionConfigurationError(
                "GEMINI_CONFIGURATION_ERROR: GEMINI_API_KEY is not configured on the backend."
            )

        image_bytes, mime_type = self._prepare_image(image_bytes, mime_type)
        client = self.client or genai.Client(
            api_key=effective_key.strip(),
            http_options=types.HttpOptions(
                timeout=int(self.timeout_seconds * 1000),
            ),
        )
        prompt = (
            "Transcribe this prescription image into the requested JSON schema. Keep each text span "
            "in its correct category. Only list medicines or treatments as medicines when an explicit "
            "medicine order is visible; never put dates, IDs, hospital or clinician names, symptoms, "
            "diagnoses, vitals, or general advice in medications. A medicine's original_text must "
            "quote its visible order, including any legible sig text. Do not infer or complete handwriting. "
            "Copy uncertain text verbatim into uncertain_items. Only include a name, strength, dose, route, "
            "frequency, duration, or instruction if that value is explicitly legible in the image. Never "
            "invent a diagnosis, advice, or dosing. This output is unverified and requires human review."
        )
        config = types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=GeminiPrescriptionOutput,
            temperature=0,
        )

        attempts = 0
        last_error: Optional[Exception] = None
        parsed_output: Optional[GeminiPrescriptionOutput] = None
        model_succeeded: Optional[str] = None
        fallback_occurred = False
        fallback_reason: Optional[str] = None

        # Attempt 1: Call primary model
        attempts += 1
        try:
            parsed_output = self._execute_gemini_call(
                client, self.model_name, prompt, image_bytes, mime_type, config
            )
            model_succeeded = self.model_name
        except Exception as error:
            last_error = error
            code, msg, is_auth, is_not_found, is_transient = self._classify_exception(error)

            if is_auth:
                logger.warning("Gemini credentials rejected on primary model '%s'", self.model_name)
                raise RecognitionAuthenticationError(
                    f"GEMINI_AUTHENTICATION_ERROR: Backend Gemini credentials were rejected ({error}).",
                    attempts=attempts,
                    model_used=self.model_name,
                ) from error

            primary_failed_reason = f"Primary model {self.model_name} failed: {error}"

            if is_transient:
                logger.info(
                    "Gemini transient failure (%s) on '%s'. Retrying in %ss...",
                    code, self.model_name, self.backoff_seconds,
                )
                if self.backoff_seconds > 0:
                    time.sleep(self.backoff_seconds)
                attempts += 1
                try:
                    parsed_output = self._execute_gemini_call(
                        client, self.model_name, prompt, image_bytes, mime_type, config
                    )
                    model_succeeded = self.model_name
                except Exception as retry_err:
                    last_error = retry_err
                    r_code, r_msg, r_auth, _, _ = self._classify_exception(retry_err)
                    if r_auth:
                        raise RecognitionAuthenticationError(
                            f"GEMINI_AUTHENTICATION_ERROR: Backend Gemini credentials were rejected ({retry_err}).",
                            attempts=attempts,
                            model_used=self.model_name,
                        ) from retry_err
                    primary_failed_reason = f"Primary model {self.model_name} failed after retry: {retry_err}"
            elif is_not_found:
                logger.warning(
                    "Gemini primary model '%s' not found (404). Skipping retry to try fallback model...",
                    self.model_name,
                )
                primary_failed_reason = f"Primary model {self.model_name} not found (404)"

            # If primary model failed, try fallback model once
            if parsed_output is None and self.fallback_model and self.fallback_model != self.model_name:
                attempts += 1
                logger.info(
                    "Trying Gemini fallback model '%s' after primary model '%s' failed...",
                    self.fallback_model, self.model_name,
                )
                try:
                    parsed_output = self._execute_gemini_call(
                        client, self.fallback_model, prompt, image_bytes, mime_type, config
                    )
                    model_succeeded = self.fallback_model
                    fallback_occurred = True
                    fallback_reason = primary_failed_reason
                except Exception as fb_err:
                    last_error = fb_err
                    fb_code, fb_msg, fb_auth, _, _ = self._classify_exception(fb_err)
                    if fb_auth:
                        raise RecognitionAuthenticationError(
                            f"GEMINI_AUTHENTICATION_ERROR: Backend Gemini credentials were rejected ({fb_err}).",
                            attempts=attempts,
                            model_used=self.fallback_model,
                        ) from fb_err
                    fallback_failed_reason = f"{primary_failed_reason}; Fallback model {self.fallback_model} failed: {fb_err}"
            else:
                fallback_failed_reason = primary_failed_reason

        # If still failed after fallback model attempt, raise RecognitionError so engine falls back to RapidOCR
        if parsed_output is None:
            code, msg, is_auth, is_not_found, is_transient = (
                self._classify_exception(last_error) if last_error else (None, "", False, False, False)
            )
            if is_auth:
                raise RecognitionAuthenticationError(
                    f"GEMINI_AUTHENTICATION_ERROR: {last_error}",
                    attempts=attempts,
                    model_used=self.model_name,
                ) from last_error
            if code == 429 or "RESOURCE_EXHAUSTED" in msg:
                raise RecognitionQuotaError(
                    f"GEMINI_QUOTA_EXCEEDED: Gemini rate or quota limit reached ({last_error}).",
                    attempts=attempts,
                    model_used=self.model_name,
                ) from last_error
            if code in (503, 504) or is_transient or isinstance(last_error, (TimeoutError, httpx.TimeoutException)):
                raise RecognitionTimeoutError(
                    f"GEMINI_TIMEOUT: Gemini service is unavailable ({last_error}).",
                    attempts=attempts,
                    model_used=self.model_name,
                ) from last_error
            if is_not_found:
                raise RecognitionModelUnavailableError(
                    f"GEMINI_MODEL_UNAVAILABLE: Configured Gemini model unavailable ({last_error}).",
                    attempts=attempts,
                    model_used=self.model_name,
                ) from last_error
            if isinstance(last_error, RecognitionMalformedResponseError):
                raise RecognitionMalformedResponseError(
                    str(last_error),
                    attempts=attempts,
                    model_used=self.model_name,
                ) from last_error
            raise RecognitionError(
                f"GEMINI_ERROR: {fallback_failed_reason or last_error}",
                attempts=attempts,
                model_used=self.model_name,
            ) from last_error

        result = self._build_result_from_json(parsed_output.model_dump(), model_name=model_succeeded)
        result.provider_used = "gemini"
        result.model_used = model_succeeded
        result.attempts = attempts
        result.fallback_occurred = fallback_occurred
        result.fallback_reason = fallback_reason
        return result

    def _build_result_from_json(
        self, data: Dict[str, Any], model_name: Optional[str] = None
    ) -> DocumentRecognitionResult:
        items: List[DocumentItem] = []
        hospital_details = [str(x).strip() for x in data.get("hospital_details", []) if x]
        patient_details = data.get("patient_details") or {}
        if isinstance(patient_details, BaseModel):
            patient_details = patient_details.model_dump(exclude_none=True)
        prescription_date = data.get("date")
        symptoms = [str(x).strip() for x in data.get("symptoms", []) if x]
        diagnosis = [str(x).strip() for x in data.get("diagnosis", []) if x]
        vitals = [str(x).strip() for x in data.get("vitals", []) if x]
        general_advice = [str(x).strip() for x in data.get("general_advice", []) if x]
        medications: List[DocumentItem] = []
        non_med_treatments: List[DocumentItem] = []
        uncertain_items: List[DocumentItem] = []
        seen_uncertain_text: set[str] = set()

        def add_text_item(field_type: DocumentFieldType, text: str) -> None:
            items.append(DocumentItem(
                field_type=field_type,
                original_text=text,
                interpreted_text=text,
                needs_review=True,
                uncertainty_reason="AI transcription is unverified and requires human review",
            ))

        def add_uncertain_item(original_text: str, reason: str) -> None:
            original = original_text.strip()
            normalized = original.casefold()
            if not original or normalized in seen_uncertain_text:
                return
            seen_uncertain_text.add(normalized)
            uncertain = DocumentItem(
                field_type=DocumentFieldType.UNCERTAIN_UNREADABLE,
                original_text=original,
                interpreted_text=original,
                needs_review=True,
                uncertainty_reason=reason,
            )
            uncertain_items.append(uncertain)
            items.append(uncertain)

        for text in hospital_details:
            add_text_item(DocumentFieldType.HOSPITAL_DETAILS, text)
        for text in symptoms:
            add_text_item(DocumentFieldType.SYMPTOMS_COMPLAINTS, text)
        for text in vitals:
            add_text_item(DocumentFieldType.VITAL_SIGNS, text)
        for text in diagnosis:
            add_text_item(DocumentFieldType.DIAGNOSIS, text)

        for index, raw in enumerate(data.get("medications", [])):
            if not isinstance(raw, dict):
                continue
            original = str(raw.get("original_text") or "").strip()
            name = str(raw.get("name") or "").strip()
            if not original:
                continue
            field_type, _, reason = classify_text_line(original)
            if field_type != DocumentFieldType.MEDICATION_ORDER or not name or name.casefold() not in original.casefold():
                add_uncertain_item(
                    original,
                    reason or "Medicine identity is not explicit in the source text",
                )
                continue

            explicit_fields: Dict[str, Optional[str]] = {}
            for key in ("strength", "dose", "route", "frequency", "duration", "instructions"):
                value = raw.get(key)
                explicit_fields[key] = (
                    str(value) if value and str(value).casefold() in original.casefold() else None
                )
            medicine = DocumentItem(
                field_type=DocumentFieldType.MEDICATION_ORDER,
                original_text=original,
                interpreted_text=original,
                confidence=None,
                confidence_is_calibrated=False,
                needs_review=True,
                uncertainty_reason="AI transcription is unverified and requires human review",
                line_index=index,
                name=name,
                **explicit_fields,
            )
            medications.append(medicine)
            items.append(medicine)

        for text in data.get("non_medication_treatments", []):
            if isinstance(text, str) and text.strip():
                item = DocumentItem(
                    field_type=DocumentFieldType.NON_MEDICATION_TREATMENT,
                    original_text=text.strip(),
                    interpreted_text=text.strip(),
                    needs_review=True,
                    uncertainty_reason="AI transcription is unverified and requires human review",
                )
                non_med_treatments.append(item)
                items.append(item)
        for text in general_advice:
            add_text_item(DocumentFieldType.GENERAL_ADVICE, text)

        for raw in data.get("uncertain_items", []):
            if not isinstance(raw, dict):
                continue
            original = str(raw.get("original_text") or "").strip()
            add_uncertain_item(
                original,
                str(raw.get("uncertainty_reason") or "Unclear handwriting"),
            )

        date_item = None
        if prescription_date:
            date_item = DocumentItem(
                field_type=DocumentFieldType.DATE,
                original_text=str(prescription_date),
                interpreted_text=str(prescription_date),
                needs_review=True,
                uncertainty_reason="AI transcription is unverified and requires human review",
            )
            items.append(date_item)

        return DocumentRecognitionResult(
            items=items,
            hospital_details=hospital_details,
            patient_details=patient_details,
            date=prescription_date,
            symptoms=symptoms,
            diagnosis=diagnosis,
            vitals=vitals,
            medications=medications,
            non_medication_treatments=non_med_treatments,
            general_advice=general_advice,
            uncertain_items=uncertain_items,
            provider_used="gemini",
            model_used=model_name or self.model_name,
            attempts=1,
            fallback_occurred=False,
            fallback_reason=None,
            source_type="ai_transcription_unverified",
            processing_status="needs_review",
            warnings=["AI transcription is not verified; a clinician or pharmacist must review it."],
        )


class MockRecognitionProvider(RecognitionProvider):
    """Hermetic mock recognition provider for deterministic unit testing."""

    def __init__(self, mock_result: Optional[DocumentRecognitionResult] = None) -> None:
        self.mock_result = mock_result

    def recognize_document(
        self, image_bytes: bytes, mime_type: str = "image/jpeg"
    ) -> DocumentRecognitionResult:
        if self.mock_result is not None:
            return self.mock_result
        return DocumentRecognitionResult(
            items=[
                DocumentItem(
                    field_type=DocumentFieldType.MEDICATION_ORDER,
                    original_text="10% Dextrose (IV) stat",
                    interpreted_text="Dextrose 10% IV stat",
                    name="Dextrose",
                    strength="10%",
                    route="IV",
                    frequency="stat",
                )
            ],
            medications=[
                DocumentItem(
                    field_type=DocumentFieldType.MEDICATION_ORDER,
                    original_text="10% Dextrose (IV) stat",
                    interpreted_text="Dextrose 10% IV stat",
                    name="Dextrose",
                    strength="10%",
                    route="IV",
                    frequency="stat",
                )
            ],
            symptoms=["Giddiness, restlessness"],
            vitals=["Blood Pressure: 110/70 mmHg"],
            general_advice=["Adequate fluid intake", "ORS 2 sachets"],
            provider_used="mock",
            model_used="mock",
            attempts=1,
        )


def get_recognition_provider(provider_type: Optional[str] = None) -> RecognitionProvider:
    """Factory resolving the active recognition provider."""
    ptype = (provider_type or settings.RECOGNITION_PROVIDER or "gemini").lower()
    if ptype == "gemini":
        return GeminiVisionProvider()
    if ptype == "mock":
        return MockRecognitionProvider()
    if ptype in ("rapidocr", "local_rapidocr", "local"):
        return LocalRapidOCRProvider()
    raise RecognitionConfigurationError(
        f"Unsupported RECOGNITION_PROVIDER '{ptype}'. Use gemini, rapidocr, or mock."
    )
