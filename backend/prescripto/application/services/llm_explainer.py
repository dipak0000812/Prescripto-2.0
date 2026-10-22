"""
Clinical LLM Explainer Service.
Transforms complex prescription extractions and safety findings into clear,
patient-friendly instructions and doctor-facing clinical summaries.

Supports Generative LLM via Gemini API or OpenAI API when keys are configured,
with an intelligent deterministic clinical synthesis fallback for instant offline use.
"""
import json
import logging
import urllib.request
import urllib.error
from typing import Any, Dict, List, Optional
from prescripto.config.settings import settings

logger = logging.getLogger(__name__)


class LLMExplainerService:
    def __init__(self, gemini_key: Optional[str] = None, openai_key: Optional[str] = None):
        self.gemini_key = gemini_key or settings.GEMINI_API_KEY
        self.openai_key = openai_key or settings.OPENAI_API_KEY

    def explain(
        self,
        medications: List[Dict[str, Any]],
        findings: List[Dict[str, Any]],
        patient_info: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Generates clinical summary, safety alerts, and patient instructions.
        Attempts generative LLM if configured; otherwise produces deterministic synthesis.
        """
        # Try Gemini if key is provided
        if self.gemini_key:
            try:
                result = self._call_gemini(medications, findings, patient_info)
                if result:
                    result["engine"] = "Gemini Generative AI"
                    return result
            except Exception as e:
                logger.warning(f"Gemini LLM call failed, falling back to deterministic synthesis: {e}")

        # Try OpenAI if key is provided
        if self.openai_key:
            try:
                result = self._call_openai(medications, findings, patient_info)
                if result:
                    result["engine"] = "OpenAI Generative AI"
                    return result
            except Exception as e:
                logger.warning(f"OpenAI LLM call failed, falling back to deterministic synthesis: {e}")

        # Fallback to rich deterministic clinical synthesis
        return self._generate_deterministic_synthesis(medications, findings, patient_info)

    def _call_gemini(
        self,
        medications: List[Dict[str, Any]],
        findings: List[Dict[str, Any]],
        patient_info: Optional[Dict[str, Any]],
    ) -> Optional[Dict[str, Any]]:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={self.gemini_key}"
        prompt = self._build_prompt(medications, findings, patient_info)

        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.2, "responseMimeType": "application/json"},
        }
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            text = data["candidates"][0]["content"]["parts"][0]["text"]
            return json.loads(text)

    def _call_openai(
        self,
        medications: List[Dict[str, Any]],
        findings: List[Dict[str, Any]],
        patient_info: Optional[Dict[str, Any]],
    ) -> Optional[Dict[str, Any]]:
        url = "https://api.openai.com/v1/chat/completions"
        prompt = self._build_prompt(medications, findings, patient_info)

        payload = {
            "model": "gpt-4o-mini",
            "messages": [
                {"role": "system", "content": "You are a clinical decision support system. Return only valid JSON."},
                {"role": "user", "content": prompt},
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.2,
        }
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.openai_key}",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            content = data["choices"][0]["message"]["content"]
            return json.loads(content)

    def _build_prompt(
        self,
        medications: List[Dict[str, Any]],
        findings: List[Dict[str, Any]],
        patient_info: Optional[Dict[str, Any]],
    ) -> str:
        return f"""Analyze this prescription and return structured JSON with:
1. "executive_summary": string
2. "patient_instructions": list of strings (simple everyday language for patient)
3. "clinical_alerts": list of strings (safety warnings for doctor/pharmacist)
4. "doctor_recommendations": list of strings

Patient Info: {json.dumps(patient_info or {})}
Prescribed Medications: {json.dumps(medications)}
Safety Findings: {json.dumps(findings)}
"""

    def _generate_deterministic_synthesis(
        self,
        medications: List[Dict[str, Any]],
        findings: List[Dict[str, Any]],
        patient_info: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        patient_name = (patient_info or {}).get("name") or "Patient"
        med_names = [m.get("name_raw") or m.get("name") or "Medication" for m in medications]

        alerts: List[str] = []
        for f in findings:
            ev = f.get("evidence_text")
            if ev:
                alerts.append(ev)

        instructions: List[str] = []
        for m in medications:
            name = m.get("name_raw") or m.get("name") or "Medication"
            strength = m.get("strength_raw") or m.get("strength") or ""
            freq = m.get("frequency_raw") or m.get("frequency") or "as directed"
            dur = m.get("duration_raw") or m.get("duration") or ""
            inst = f"Take {name} {strength}".strip()
            if freq:
                inst += f" - {freq}"
            if dur:
                inst += f" for {dur}"
            instructions.append(inst)

        if not instructions:
            instructions.append("Follow standard dosing guidance and consult your healthcare provider.")

        summary = (
            f"Prescription for {patient_name} containing {len(medications)} medication(s): "
            + ", ".join(med_names[:4])
            + ("." if len(med_names) <= 4 else f" and {len(med_names) - 4} more.")
        )

        return {
            "engine": "Prescripto Deterministic Clinical Synthesizer (LLM Ready)",
            "executive_summary": summary,
            "patient_instructions": instructions,
            "clinical_alerts": alerts if alerts else ["No active safety contraindications or duplicate therapies detected."],
            "doctor_recommendations": [
                "Verify indicated patient allergy history before dispensing.",
                "Confirm therapeutic dosage matches patient age, weight, and renal profile.",
            ],
            "llm_ready": True,
            "note": "Generative LLM is configured and ready. Supply GEMINI_API_KEY or OPENAI_API_KEY in .env to activate real-time LLM reasoning.",
        }


llm_explainer = LLMExplainerService()
