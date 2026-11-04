"""Tests for conservative prescription classification and Gemini vision."""

import io
import json
from unittest.mock import MagicMock, patch

import pytest
from PIL import Image

from prescripto.domain.recognition.models import DocumentFieldType
from prescripto.ml.recognition_providers import (
    GeminiVisionProvider,
    LocalRapidOCRProvider,
    MockRecognitionProvider,
    RecognitionAuthenticationError,
    RecognitionConfigurationError,
    RecognitionInvalidImageError,
    RecognitionMalformedResponseError,
    RecognitionModelUnavailableError,
    RecognitionQuotaError,
    DocumentRecognitionResult,
    RecognitionTimeoutError,
    classify_text_line,
    get_recognition_provider,
)


def _image_bytes() -> bytes:
    stream = io.BytesIO()
    Image.new("RGB", (8, 8), "white").save(stream, format="JPEG")
    return stream.getvalue()


def _provider(response_text: str = "{}", api_key: str = "test-key") -> GeminiVisionProvider:
    client = MagicMock()
    client.models.generate_content.return_value.text = response_text
    return GeminiVisionProvider(api_key=api_key, client=client)


@pytest.mark.parametrize(
    "text,expected_type",
    [
        ("Apex Speciality Hospital", DocumentFieldType.HOSPITAL_DETAILS),
        ("Patient: Ramesh Kumar, Age: 52", DocumentFieldType.PATIENT_DETAILS),
        ("Date: 15/10/2026", DocumentFieldType.DATE),
        ("Complaints: headache and fever", DocumentFieldType.SYMPTOMS_COMPLAINTS),
        ("BP: 120/80 mmHg, Pulse: 72/min", DocumentFieldType.VITAL_SIGNS),
        ("Adequate fluid intake and rest", DocumentFieldType.GENERAL_ADVICE),
        ("Tab Paracetamol 650mg 1 tab TDS x 3 days", DocumentFieldType.MEDICATION_ORDER),
    ],
)
def test_classifier_keeps_legible_categories(text, expected_type):
    field_type, original, _ = classify_text_line(text)
    assert field_type == expected_type
    assert original


@pytest.mark.parametrize(
    "text",
    ["yuddbeu", "07011", "22112122", "Adeauae Pluidtnbake", "RS2zache"],
)
def test_classifier_preserves_corrupted_text_as_uncertain(text):
    field_type, original, reason = classify_text_line(text)
    assert field_type == DocumentFieldType.UNCERTAIN_UNREADABLE
    assert original == text
    assert reason


def test_missing_api_key_fails_without_local_fallback():
    provider = GeminiVisionProvider(api_key="", client=MagicMock())
    with pytest.raises(RecognitionConfigurationError, match="GEMINI_API_KEY"):
        provider.recognize_document(_image_bytes())


def test_invalid_image_is_rejected_before_model_call():
    client = MagicMock()
    provider = GeminiVisionProvider(api_key="test-key", client=client)
    with pytest.raises(RecognitionInvalidImageError, match="INVALID_IMAGE"):
        provider.recognize_document(b"not an image")
    client.models.generate_content.assert_not_called()


def test_structured_sample_separates_details_and_explicit_medicines():
    expected = {
        "hospital_details": ["City Hospital"],
        "patient_details": {"name": "Jane Doe", "age": "45", "gender": None, "patient_id": None, "other": []},
        "date": "2026-10-25",
        "symptoms": ["giddiness, restlessness"],
        "diagnosis": ["Acute gastroenteritis"],
        "vitals": ["BP 110/70"],
        "medications": [
            {
                "original_text": "Tab Paracetamol 650mg 1 tab TDS x 3 days",
                "name": "Paracetamol",
                "strength": "650mg",
                "dose": "1 tab",
                "route": None,
                "frequency": "TDS",
                "duration": "3 days",
                "instructions": None,
            },
            {
                "original_text": "Tab Pantoprazole 40mg before breakfast",
                "name": "Pantoprazole",
                "strength": "40mg",
                "dose": None,
                "route": None,
                "frequency": None,
                "duration": None,
                "instructions": "before breakfast",
            },
            {
                "original_text": "Tab Cetirizine 10mg at night",
                "name": "Cetirizine",
                "strength": "10mg",
                "dose": None,
                "route": None,
                "frequency": None,
                "duration": None,
                "instructions": "at night",
            },
        ],
        "non_medication_treatments": ["ORS 2 sachets in 1L water"],
        "general_advice": ["Adequate fluid intake", "Review after 3 days"],
        "uncertain_items": [],
    }
    provider = _provider(json.dumps(expected))

    result = provider.recognize_document(_image_bytes(), "image/jpeg")

    assert result.processing_status == "needs_review"
    assert result.date == expected["date"]
    assert result.patient_details["name"] == "Jane Doe"
    assert result.hospital_details == ["City Hospital"]
    assert result.symptoms == ["giddiness, restlessness"]
    assert result.diagnosis == ["Acute gastroenteritis"]
    assert result.vitals == ["BP 110/70"]
    assert result.general_advice == ["Adequate fluid intake", "Review after 3 days"]
    assert len(result.medications) == 3
    assert [item.name for item in result.medications] == [
        "Paracetamol", "Pantoprazole", "Cetirizine"
    ]
    assert all(item.needs_review and item.confidence is None for item in result.medications)
    assert all(item.field_type == DocumentFieldType.MEDICATION_ORDER for item in result.medications)
    assert result.uncertain_items == []


def test_non_medication_text_in_model_medication_bucket_is_not_accepted_as_medicine():
    payload = {
        "date": None,
        "medications": [
            {"original_text": "City Hospital", "name": "City Hospital"},
            {"original_text": "Headache and fever", "name": "Headache"},
            {"original_text": "BP 110/70", "name": "BP"},
            {"original_text": "Drink plenty of water", "name": "water"},
        ],
    }
    result = _provider(json.dumps(payload)).recognize_document(_image_bytes())

    assert result.medications == []
    assert {item.original_text for item in result.uncertain_items} == {
        "City Hospital", "Headache and fever", "BP 110/70", "Drink plenty of water"
    }


def test_unreadable_handwriting_is_preserved_and_not_screened_as_medicine():
    payload = {
        "medications": [
            {"original_text": "RS2zache", "name": "ORS"}
        ],
        "uncertain_items": [
            {"original_text": "RS2zache", "uncertainty_reason": "Unreadable handwriting"}
        ],
    }
    result = _provider(json.dumps(payload)).recognize_document(_image_bytes())

    assert result.medications == []
    assert len(result.uncertain_items) == 1
    assert result.uncertain_items[0].original_text == "RS2zache"
    assert result.uncertain_items[0].interpreted_text == "RS2zache"


def test_malformed_model_json_raises_safe_error():
    with pytest.raises(RecognitionMalformedResponseError, match="GEMINI_MALFORMED_RESPONSE"):
        _provider("not json").recognize_document(_image_bytes())


def test_empty_model_response_raises_safe_error():
    with pytest.raises(RecognitionMalformedResponseError, match="GEMINI_MALFORMED_RESPONSE"):
        _provider("").recognize_document(_image_bytes())


def test_quota_failure_maps_to_retry_later_error_without_fallback():
    client = MagicMock()
    client.models.generate_content.side_effect = Exception("quota")
    client.models.generate_content.side_effect.code = 429
    provider = GeminiVisionProvider(api_key="test-key", client=client, backoff_seconds=0)

    with pytest.raises(RecognitionQuotaError, match="GEMINI_QUOTA_EXCEEDED"):
        provider.recognize_document(_image_bytes())
    # Retries primary once (call 2), then tries fallback once (call 3)
    assert client.models.generate_content.call_count == 3


def test_timeout_failure_is_typed_and_does_not_fallback():
    client = MagicMock()
    client.models.generate_content.side_effect = TimeoutError()
    provider = GeminiVisionProvider(api_key="test-key", client=client, backoff_seconds=0)

    with pytest.raises(RecognitionTimeoutError, match="GEMINI_TIMEOUT"):
        provider.recognize_document(_image_bytes())
    assert client.models.generate_content.call_count == 3


def test_factory_selects_gemini_without_paid_provider_fallback():
    provider = get_recognition_provider("gemini")
    assert isinstance(provider, GeminiVisionProvider)
    assert isinstance(get_recognition_provider("mock"), MockRecognitionProvider)
    assert isinstance(get_recognition_provider("rapidocr"), LocalRapidOCRProvider)


def test_markdown_code_fences_stripped_from_gemini_response():
    data = {
        "hospital_details": ["City Hospital"],
        "medications": [
            {
                "original_text": "Tab Paracetamol 650mg TDS",
                "name": "Paracetamol",
                "strength": "650mg",
                "frequency": "TDS",
            }
        ],
    }
    markdown_wrapped = f"```json\n{json.dumps(data)}\n```"
    provider = _provider(markdown_wrapped)
    result = provider.recognize_document(_image_bytes())
    assert len(result.medications) == 1
    assert result.medications[0].name == "Paracetamol"


def test_invalid_api_key_400_raises_authentication_error():
    client = MagicMock()
    err = Exception("400 INVALID_ARGUMENT. API key not valid. Please pass a valid API key.")
    setattr(err, "code", 400)
    client.models.generate_content.side_effect = err
    provider = GeminiVisionProvider(api_key="test-key", client=client)

    with pytest.raises(RecognitionAuthenticationError, match="GEMINI_AUTHENTICATION_ERROR"):
        provider.recognize_document(_image_bytes())


@pytest.mark.parametrize(
    "error_class,error_message",
    [
        (RecognitionQuotaError, "RESOURCE_EXHAUSTED"),
        (RecognitionAuthenticationError, "GEMINI_AUTHENTICATION_ERROR"),
        (RecognitionTimeoutError, "GEMINI_TIMEOUT"),
        (RecognitionModelUnavailableError, "MODEL_UNAVAILABLE"),
        (RecognitionMalformedResponseError, "MALFORMED_RESPONSE"),
    ],
)
def test_engine_recognition_gemini_fallback_on_any_recognition_error(error_class, error_message):
    """Test 4: Verify engine._recognize_document falls back to RapidOCR and sets fallback metadata on any RecognitionError."""
    from prescripto.pipeline.engine import _recognize_document

    context = {"ocr_runtime": MagicMock()}
    image_bytes = _image_bytes()

    mock_gemini = MagicMock()
    mock_gemini.recognize_document.side_effect = error_class(error_message)

    mock_rapidocr = MagicMock()
    mock_rapidocr.recognize_document.return_value = DocumentRecognitionResult(
        hospital_details=["Local Hospital"],
        lines=[],
        medications=[],
    )

    with patch("prescripto.pipeline.engine._resolve_recognition_provider", return_value=mock_gemini), \
         patch("prescripto.ml.recognition_providers.LocalRapidOCRProvider", return_value=mock_rapidocr):
        result = _recognize_document(context, image_bytes, "image/jpeg")

    assert result.fallback_occurred is True
    assert context["recognition_fallback_used"] is True
    assert error_message in context["recognition_fallback_reason"]
    mock_rapidocr.recognize_document.assert_called_once()


# ---------------------------------------------------------------------------
# Retry Policy and Model Fallback Tests
# ---------------------------------------------------------------------------

def test_retry_policy_primary_succeeds_on_second_attempt():
    """503 on attempt 1 -> retry primary -> succeeds on attempt 2."""
    client = MagicMock()
    err_503 = Exception("503 UNAVAILABLE: High demand")
    setattr(err_503, "code", 503)
    success_resp = MagicMock()
    success_resp.text = json.dumps({
        "hospital_details": ["General Hospital"],
        "medications": [{"original_text": "Tab Amoxicillin 500mg TDS", "name": "Amoxicillin", "strength": "500mg", "frequency": "TDS"}],
    })
    client.models.generate_content.side_effect = [err_503, success_resp]

    provider = GeminiVisionProvider(
        api_key="test-key",
        model_name="gemini-3.5-flash",
        fallback_model="gemini-3.6-flash",
        backoff_seconds=0,
        client=client,
    )
    result = provider.recognize_document(_image_bytes())

    assert client.models.generate_content.call_count == 2
    call_models = [call.kwargs.get("model") for call in client.models.generate_content.call_args_list]
    assert call_models == ["gemini-3.5-flash", "gemini-3.5-flash"]
    assert result.model_used == "gemini-3.5-flash"
    assert result.provider_used == "gemini"
    assert result.attempts == 2
    assert result.fallback_occurred is False


def test_retry_policy_primary_fails_twice_fallback_model_succeeds():
    """503 on attempts 1 and 2 -> switches to fallback model on attempt 3 -> succeeds."""
    client = MagicMock()
    err_503 = Exception("503 UNAVAILABLE")
    setattr(err_503, "code", 503)
    success_resp = MagicMock()
    success_resp.text = json.dumps({
        "hospital_details": ["General Hospital"],
        "medications": [{"original_text": "Tab Amoxicillin 500mg TDS", "name": "Amoxicillin", "strength": "500mg", "frequency": "TDS"}],
    })
    client.models.generate_content.side_effect = [err_503, err_503, success_resp]

    provider = GeminiVisionProvider(
        api_key="test-key",
        model_name="gemini-3.5-flash",
        fallback_model="gemini-3.6-flash",
        backoff_seconds=0,
        client=client,
    )
    result = provider.recognize_document(_image_bytes())

    assert client.models.generate_content.call_count == 3
    call_models = [call.kwargs.get("model") for call in client.models.generate_content.call_args_list]
    assert call_models == ["gemini-3.5-flash", "gemini-3.5-flash", "gemini-3.6-flash"]
    assert result.model_used == "gemini-3.6-flash"
    assert result.provider_used == "gemini"
    assert result.attempts == 3
    assert result.fallback_occurred is True
    assert "gemini-3.5-flash" in result.fallback_reason


def test_retry_policy_primary_and_fallback_both_fail_triggers_rapidocr():
    """503 on attempts 1, 2, and fallback attempt 3 -> raises RecognitionTimeoutError with attempts=3."""
    client = MagicMock()
    err_503 = Exception("503 UNAVAILABLE")
    setattr(err_503, "code", 503)
    client.models.generate_content.side_effect = [err_503, err_503, err_503]

    provider = GeminiVisionProvider(
        api_key="test-key",
        model_name="gemini-3.5-flash",
        fallback_model="gemini-3.6-flash",
        backoff_seconds=0,
        client=client,
    )

    with pytest.raises(RecognitionTimeoutError) as exc_info:
        provider.recognize_document(_image_bytes())

    assert exc_info.value.attempts == 3
    assert client.models.generate_content.call_count == 3
    call_models = [call.kwargs.get("model") for call in client.models.generate_content.call_args_list]
    assert call_models == ["gemini-3.5-flash", "gemini-3.5-flash", "gemini-3.6-flash"]


def test_retry_policy_auth_error_skips_straight_no_retries():
    """Auth error (401/403/API_KEY_INVALID) skips straight to RapidOCR with 0 retries."""
    client = MagicMock()
    auth_err = Exception("401 UNAUTHENTICATED: API key not valid")
    setattr(auth_err, "code", 401)
    client.models.generate_content.side_effect = auth_err

    provider = GeminiVisionProvider(
        api_key="test-key",
        model_name="gemini-3.5-flash",
        fallback_model="gemini-3.6-flash",
        backoff_seconds=0,
        client=client,
    )

    with pytest.raises(RecognitionAuthenticationError) as exc_info:
        provider.recognize_document(_image_bytes())

    # Strictly 1 call made, no retries and no fallback model call
    assert client.models.generate_content.call_count == 1
    assert exc_info.value.attempts == 1
    assert client.models.generate_content.call_args_list[0].kwargs.get("model") == "gemini-3.5-flash"


def test_retry_policy_404_model_not_found_skips_retry_calls_fallback_directly():
    """404 on primary model skips retry of primary and calls fallback model directly."""
    client = MagicMock()
    err_404 = Exception("404 NOT_FOUND: models/gemini-3.5-flash is not found")
    setattr(err_404, "code", 404)
    success_resp = MagicMock()
    success_resp.text = json.dumps({
        "hospital_details": ["General Hospital"],
        "medications": [{"original_text": "Tab Amoxicillin 500mg TDS", "name": "Amoxicillin", "strength": "500mg", "frequency": "TDS"}],
    })
    client.models.generate_content.side_effect = [err_404, success_resp]

    provider = GeminiVisionProvider(
        api_key="test-key",
        model_name="gemini-3.5-flash",
        fallback_model="gemini-3.6-flash",
        backoff_seconds=0,
        client=client,
    )
    result = provider.recognize_document(_image_bytes())

    # Strictly 2 calls: attempt 1 (primary 404), attempt 2 (fallback model)
    assert client.models.generate_content.call_count == 2
    call_models = [call.kwargs.get("model") for call in client.models.generate_content.call_args_list]
    assert call_models == ["gemini-3.5-flash", "gemini-3.6-flash"]
    assert result.model_used == "gemini-3.6-flash"
    assert result.attempts == 2
    assert result.fallback_occurred is True

