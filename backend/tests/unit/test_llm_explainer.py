import json
from unittest.mock import MagicMock

from prescripto.application.services.llm_explainer import LLMExplainerService
from prescripto.config.settings import settings


def test_llm_disabled_uses_deterministic_synthesis_even_with_gemini_key(monkeypatch):
    monkeypatch.setattr(settings, "LLM_ENABLED", False)
    service = LLMExplainerService(gemini_key="test-key")

    def fail_if_called(*args, **kwargs):
        raise AssertionError("Gemini must not be called while LLM is disabled")

    monkeypatch.setattr(service, "_call_gemini", fail_if_called)
    result = service.explain([{"name_raw": "Paracetamol"}])

    assert result["medicines_and_treatments"][0]["name"] == "Paracetamol"
    assert result["engine"].startswith("Prescripto Clinical Synthesizer")


def test_enabled_llm_uses_gemini_for_commentary_only(monkeypatch):
    monkeypatch.setattr(settings, "LLM_ENABLED", True)
    service = LLMExplainerService(gemini_key="test-key")
    monkeypatch.setattr(
        service,
        "_call_gemini",
        lambda *args: {"prescription_summary": "A patient-friendly summary."},
    )

    result = service.explain([{"name_raw": "Paracetamol", "frequency_raw": "twice daily"}])

    assert result["engine"] == f"Google Gemini ({settings.GEMINI_MODEL})"
    assert result["prescription_summary"] == "A patient-friendly summary."
    assert result["medicines_and_treatments"][0]["name"] == "Paracetamol"
    assert result["medicines_and_treatments"][0]["frequency"] == "twice daily"
    assert result["what_doctor_wrote"]["symptoms"] == []
    assert result["summary_source"] == "AI-generated; not a transcription"
    assert result["patient_instructions"] == ["Prescription wording: Paracetamol"]


def test_enabled_llm_failure_is_reported_with_deterministic_source(monkeypatch):
    monkeypatch.setattr(settings, "LLM_ENABLED", True)
    service = LLMExplainerService(gemini_key="test-key")

    def fail(*args):
        raise RuntimeError("provider unavailable")

    monkeypatch.setattr(service, "_call_gemini", fail)
    result = service.explain([{"name_raw": "Paracetamol"}])

    assert result["summary_source"] == "Deterministic synthesis; Gemini commentary unavailable"
    assert "displayed summary is deterministic" in result["summary_warning"]
    assert result["medicines_and_treatments"][0]["name"] == "Paracetamol"


def test_enabled_llm_without_key_is_reported(monkeypatch):
    monkeypatch.setattr(settings, "LLM_ENABLED", True)
    monkeypatch.setattr(settings, "GEMINI_API_KEY", None)
    result = LLMExplainerService(gemini_key="").explain([{"name_raw": "Paracetamol"}])

    assert result["summary_warning"]
    assert "not configured" in result["summary_warning"]


def test_gemini_sdk_uses_backend_key_and_configured_model(monkeypatch):
    service = LLMExplainerService(gemini_key="test-key")
    monkeypatch.setattr(settings, "GEMINI_MODEL", "test-gemini-model")
    response = MagicMock()
    response.text = json.dumps({"prescription_summary": "OK"})
    client = MagicMock()
    client.models.generate_content.return_value = response
    monkeypatch.setattr("prescripto.application.services.llm_explainer.genai.Client", lambda **kwargs: client)

    result = service._call_gemini([], [], None, None)

    client.models.generate_content.assert_called_once()
    call = client.models.generate_content.call_args
    assert call.kwargs["model"] == "test-gemini-model"
    assert call.kwargs["config"].response_mime_type == "application/json"
    assert result == {"prescription_summary": "OK"}


def test_gemini_markdown_fences_stripped(monkeypatch):
    service = LLMExplainerService(gemini_key="test-key")
    response = MagicMock()
    response.text = "```json\n" + json.dumps({"prescription_summary": "Cleaned summary"}) + "\n```"
    client = MagicMock()
    client.models.generate_content.return_value = response
    monkeypatch.setattr("prescripto.application.services.llm_explainer.genai.Client", lambda **kwargs: client)

    result = service._call_gemini([], [], None, None)
    assert result == {"prescription_summary": "Cleaned summary"}

