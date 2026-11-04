"""
Clinical LLM Explainer & Patient-Friendly Report Synthesizer.
Transforms prescription extractions and clinical findings into clear, simple,
patient-friendly summaries strictly conforming to Section 6 safety rules.
"""
from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional
from google import genai
from google.genai import types
from prescripto.config.settings import settings

logger = logging.getLogger(__name__)

# Common medications plain-language explanation dictionary
COMMON_DRUG_EXPLANATIONS: Dict[str, str] = {
    "paracetamol": "Pain reliever and fever reducer.",
    "dolo": "Pain reliever and fever reducer (Paracetamol formulation).",
    "crocin": "Pain reliever and fever reducer.",
    "dextrose": "Sterile glucose solution given intravenously for hydration, energy, or low blood sugar.",
    "10% dextrose": "Sterile 10% glucose solution administered intravenously (IV) for hydration and energy.",
    "amoxicillin": "Antibiotic used to treat bacterial infections.",
    "augmentin": "Antibiotic combination used to treat various bacterial infections.",
    "azithromycin": "Antibiotic used to treat respiratory, skin, and throat infections.",
    "cetirizine": "Antihistamine that relieves allergy symptoms, sneezing, and runny nose.",
    "pantoprazole": "Proton pump inhibitor (PPI) that reduces stomach acid production.",
    "omeprazole": "Medicine that reduces stomach acid for acidity, heartburn, and reflux.",
    "metformin": "Oral medicine used to lower and control blood sugar in diabetes.",
    "atorvastatin": "Statin medication used to lower cholesterol and protect heart health.",
    "ors": "Oral Rehydration Salts to replace lost electrolytes and fluids during dehydration.",
    "ciprofloxacin": "Broad-spectrum antibiotic for bacterial infections.",
    "ondansetron": "Anti-nausea and anti-vomiting medication.",
    "domperidone": "Relieves nausea, vomiting, and fullness in the stomach.",
    "ibuprofen": "Non-steroidal anti-inflammatory drug (NSAID) for pain and swelling.",
}


def get_plain_explanation(name: str) -> str:
    """Returns a simple everyday explanation for common medicines."""
    lower = name.lower().strip()
    for drug_key, explanation in COMMON_DRUG_EXPLANATIONS.items():
        if drug_key in lower:
            return explanation
    return "Prescription medicine; confirm its purpose with a healthcare professional."


class LLMExplainerService:
    def __init__(
        self,
        gemini_key: Optional[str] = None,
    ):
        self.gemini_key = gemini_key

    @property
    def effective_api_key(self) -> Optional[str]:
        if self.gemini_key is not None:
            return self.gemini_key.strip() or None
        return (settings.GEMINI_API_KEY or "").strip() or None

    def explain(
        self,
        medications: List[Dict[str, Any]],
        findings: Optional[List[Dict[str, Any]]] = None,
        patient_info: Optional[Dict[str, Any]] = None,
        document_context: Optional[Dict[str, Any]] = None,
        safety_findings: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Generates simple, patient-friendly report sections and clinical summary.
        Attempts Generative LLM if API keys are configured; otherwise produces
        deterministic clinical synthesis.
        """
        if findings is None:
            findings = safety_findings or []
        if not settings.LLM_ENABLED:
            return self._generate_deterministic_synthesis(
                medications, findings, patient_info, document_context
            )

        key = self.effective_api_key
        if not key:
            result = self._generate_deterministic_synthesis(
                medications, findings, patient_info, document_context
            )
            result["summary_source"] = "Deterministic synthesis; Gemini commentary unavailable"
            result["summary_warning"] = "Gemini commentary is enabled but not configured; this summary is deterministic."
            return result

        try:
            result = self._call_gemini(medications, findings, patient_info, document_context)
            if result:
                result["engine"] = f"Google Gemini ({settings.GEMINI_MODEL})"
                return self._normalize_report_structure(result, medications, findings, patient_info, document_context)
            warning = "Gemini returned no summary; the displayed summary is deterministic."
        except Exception as error:
            logger.warning(
                "Gemini LLM call failed (%s); returning an explicitly labeled deterministic summary",
                type(error).__name__,
            )
            warning = "Gemini could not generate a summary; the displayed summary is deterministic."

        fallback = self._generate_deterministic_synthesis(
            medications, findings, patient_info, document_context
        )
        fallback["summary_source"] = "Deterministic synthesis; Gemini commentary unavailable"
        fallback["summary_warning"] = warning
        return fallback

    def _call_gemini(
        self,
        medications: List[Dict[str, Any]],
        findings: List[Dict[str, Any]],
        patient_info: Optional[Dict[str, Any]],
        document_context: Optional[Dict[str, Any]],
    ) -> Optional[Dict[str, Any]]:
        client = genai.Client(
            api_key=self.effective_api_key,
            http_options=types.HttpOptions(
                timeout=10_000,
                retry_options=types.HttpRetryOptions(attempts=1),
            ),
        )
        response = client.models.generate_content(
            model=settings.GEMINI_MODEL,
            contents=self._build_prompt(medications, findings, patient_info, document_context),
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.2,
            ),
        )
        response_text = getattr(response, "text", None)
        if not isinstance(response_text, str) or not response_text.strip():
            return None
        text = response_text.strip()
        if text.startswith("```"):
            lines = text.splitlines()
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            text = "\n".join(lines).strip()
        return json.loads(text)

    def _build_prompt(
        self,
        medications: List[Dict[str, Any]],
        findings: List[Dict[str, Any]],
        patient_info: Optional[Dict[str, Any]],
        document_context: Optional[Dict[str, Any]],
    ) -> str:
        return f"""Analyze this prescription and return structured JSON with:
1. "prescription_summary": string (plain language summary)
2. "what_doctor_wrote": object with "symptoms" (list of strings), "clinical_impression" (list of strings), "vitals" (list of strings)
3. "medicines_and_treatments": list of medication objects
4. "other_advice": list of strings (general non-medication instructions)
5. "needs_confirmation": list of strings (items requiring doctor or pharmacist clarification)
6. "safety_notice": string

CRITICAL RULES:
- Never fabricate frequencies, doses, or durations if not present.
- Never output "as directed" if frequency is not specified.
- Never classify symptoms, vital signs, or advice as medications.

Patient Info: {json.dumps(patient_info or {})}
Document Context: {json.dumps(document_context or {})}
Prescribed Medications: {json.dumps(medications)}
Safety Findings: {json.dumps(findings)}
"""

    def _normalize_report_structure(
        self,
        raw_result: Dict[str, Any],
        medications: List[Dict[str, Any]],
        findings: List[Dict[str, Any]],
        patient_info: Optional[Dict[str, Any]],
        document_context: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Keeps extracted source fields authoritative while allowing a generated summary."""
        base = self._generate_deterministic_synthesis(medications, findings, patient_info, document_context)
        summary = raw_result.get("prescription_summary")
        if isinstance(summary, str) and summary.strip():
            base["prescription_summary"] = summary.strip()
            base["executive_summary"] = summary.strip()
            base["plain_english_summary"] = summary.strip()
        if raw_result.get("engine"):
            base["engine"] = raw_result["engine"]
        base["summary_source"] = "AI-generated; not a transcription"
        return base

    def _generate_deterministic_synthesis(
        self,
        medications: List[Dict[str, Any]],
        findings: List[Dict[str, Any]],
        patient_info: Optional[Dict[str, Any]] = None,
        document_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Generates strict, clinical safety-compliant, plain-English patient-friendly output.
        Follows Sections 4, 5, 6 of specification.
        """
        doc_ctx = document_context or {}
        patient_name = (patient_info or {}).get("name") or "Patient"

        symptoms = list(doc_ctx.get("symptoms") or [])
        diagnosis = list(doc_ctx.get("diagnosis") or doc_ctx.get("clinical_impression") or [])
        vitals = list(doc_ctx.get("vitals") or doc_ctx.get("vital_signs") or [])
        general_advice = list(doc_ctx.get("general_advice") or [])
        uncertain_items = list(doc_ctx.get("uncertain_items") or [])

        # Filter active clinical risk alerts (Exclude NOT_EVALUATED coverage items from alarming the patient)
        active_alerts: List[str] = []
        for f in findings:
            status = f.get("finding_status")
            ev = f.get("evidence_text")
            if status in ("POTENTIAL", "CONFIRMED", "CONFIRMED_BY_SOURCE", "HIGH_RISK") and ev:
                active_alerts.append(ev)

        # -------------------------------------------------------------------
        # Section C: Medicines and Treatments
        # -------------------------------------------------------------------
        medicine_items: List[Dict[str, Any]] = []
        instructions_list: List[str] = []
        confirmation_needed: List[str] = []

        for m in medications:
            name = (m.get("normalized_name") or m.get("name_raw") or m.get("name") or "").strip()
            if not name or name.lower() in ("medication", "medicine"):
                continue

            orig_text = m.get("original_text") or m.get("name_raw") or name
            strength = m.get("strength_raw") or m.get("strength")
            dose = m.get("dose_raw") or m.get("dose")
            route = m.get("route_raw") or m.get("route")
            frequency = m.get("frequency_raw") or m.get("frequency")
            duration = m.get("duration_raw") or m.get("duration")
            special_inst = m.get("instructions_raw") or m.get("instructions")

            missing_details: List[str] = []
            if not strength and not dose:
                missing_details.append("Strength / Dosage not specified")
                confirmation_needed.append(f"{name}: Confirm strength/dosage with doctor or pharmacist.")
            if not frequency:
                missing_details.append("Dosing schedule / frequency not specified")
                confirmation_needed.append(f"{name}: Confirm how often to take with doctor or pharmacist.")

            plain_exp = get_plain_explanation(name)

            med_obj = {
                "name": name,
                "original_text": orig_text,
                "plain_explanation": plain_exp,
                "strength": strength,
                "dose": dose,
                "route": route,
                "frequency": frequency,  # Only included when present; NO 'as directed' fallback!
                "duration": duration,
                "instructions": special_inst,
                "missing_details": missing_details,
                "needs_confirmation": len(missing_details) > 0,
            }
            medicine_items.append(med_obj)

            instructions_list.append(f"Prescription wording: {orig_text}")

        # Check for unclear handwriting requiring confirmation
        for unc in uncertain_items:
            orig = unc.get("original_text") if isinstance(unc, dict) else str(unc)
            if orig:
                confirmation_needed.append(f"Unclear handwriting on prescription ('{orig}'). Requires professional confirmation.")

        # -------------------------------------------------------------------
        # Section A: Prescription Summary
        # -------------------------------------------------------------------
        med_count = len(medicine_items)
        if med_count > 0:
            names_summary = ", ".join([m["name"] for m in medicine_items[:3]])
            summary = f"Prescription for {patient_name} containing {med_count} medication order(s) ({names_summary})"
            if len(medicine_items) > 3:
                summary += f" and {med_count - 3} more."
            else:
                summary += "."
        else:
            summary = f"Prescription scan for {patient_name}. No explicit medication orders detected."

        if symptoms:
            summary += f" Primary symptoms noted: {', '.join(symptoms[:2])}."

        # -------------------------------------------------------------------
        # Assemble Complete 6-Section Report Payload
        # -------------------------------------------------------------------
        provider_used = doc_ctx.get("provider_used") or "RapidOCR Local Engine"
        fallback_occurred = doc_ctx.get("fallback_occurred", False)
        fallback_reason = doc_ctx.get("fallback_reason")

        safety_notice = (
            "Safety Notice: Prescripto AI assists in reading handwritten prescriptions, but cannot "
            "replace a licensed healthcare professional. Handwriting variations can lead to transcription "
            "errors. Always confirm medication names, dosages, and dosing schedules with your doctor or "
            "dispensing pharmacist before taking any medication."
        )

        return {
            # Section A: Prescription Summary
            "prescription_summary": summary,
            "executive_summary": summary,  # Backwards compatibility
            "plain_english_summary": summary,
            "summary_source": "Generated synthesis; not a transcription",

            # Section B: What the Doctor Wrote
            "what_doctor_wrote": {
                "symptoms": symptoms,
                "clinical_impression": diagnosis,
                "vitals": vitals,
                "vital_signs": vitals,
            },

            # Section C: Medicines and Treatments
            "medicines_and_treatments": medicine_items,
            "patient_instructions": instructions_list,

            # Section D: Other Advice
            "other_advice": general_advice,

            # Section E: Needs Confirmation
            "needs_confirmation": confirmation_needed,

            # Section F: Safety Notice
            "safety_notice": safety_notice,

            # Clinical Advisories
            "clinical_alerts": (
                active_alerts
                if active_alerts
                else ["No safety conclusions are provided by this extraction."]
            ),
            "doctor_recommendations": [],

            # Recognition Metadata
            "recognition_metadata": {
                "provider_used": provider_used,
                "fallback_occurred": fallback_occurred,
                "fallback_reason": fallback_reason,
            },

            "engine": f"Prescripto Clinical Synthesizer ({provider_used})",
            "llm_ready": True,
            "note": "AI handwriting recognition is assistive. Always confirm unverified instructions with a pharmacist or physician.",
        }


llm_explainer = LLMExplainerService()
ClinicalExplainerService = LLMExplainerService
