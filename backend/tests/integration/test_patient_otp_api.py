"""
Integration tests for Patient Registration & Login via OTP API.
"""
import pytest
from prescripto.auth.otp_provider import DevelopmentOtpProvider
from prescripto.auth.service import AuthService, _last_otp_sent_time, otp_crypto_module

def test_patient_otp_registration_and_login_flow(client):
    # Set dev provider
    AuthService.set_otp_provider(DevelopmentOtpProvider())

    phone = "9988776655"
    _last_otp_sent_time.pop(phone, None)

    # 1. Request OTP
    req_resp = client.post("/api/v1/auth/patient/request-otp", json={"phone_number": phone})
    assert req_resp.status_code == 200
    assert req_resp.json()["status"] == "SENT"

    # Fetch generated OTP from store for testing
    from prescripto.auth.service import _otp_store
    stored = _otp_store.get(phone)
    assert stored is not None

    # Test failure with wrong OTP
    fail_reg = client.post("/api/v1/auth/patient/register", json={
        "phone_number": phone,
        "otp": "000000",
        "name": "Integration Test Patient"
    })
    assert fail_reg.status_code == 401

    # 2. Re-request OTP with mocked generator for valid deterministic flow
    from unittest.mock import patch
    with patch.object(otp_crypto_module, "generate_secure_otp", return_value="123456"):
        _last_otp_sent_time.pop(phone, None)
        client.post("/api/v1/auth/patient/request-otp", json={"phone_number": phone})

        # Register patient
        reg_resp = client.post("/api/v1/auth/patient/register", json={
            "phone_number": phone,
            "otp": "123456",
            "name": "Integration Test Patient"
        })
        assert reg_resp.status_code == 200
        reg_data = reg_resp.json()
        assert "access_token" in reg_data
        assert reg_data["user"]["role"] == "PATIENT"

        # Attempt duplicate registration -> should fail with 401 (already registered)
        _last_otp_sent_time.pop(phone, None)
        client.post("/api/v1/auth/patient/request-otp", json={"phone_number": phone})
        dup_reg = client.post("/api/v1/auth/patient/register", json={
            "phone_number": phone,
            "otp": "123456",
            "name": "Integration Test Patient"
        })
        assert dup_reg.status_code == 401

        # Patient Login flow
        _last_otp_sent_time.pop(phone, None)
        client.post("/api/v1/auth/patient/request-otp", json={"phone_number": phone})
        login_resp = client.post("/api/v1/auth/patient/login", json={
            "phone_number": phone,
            "otp": "123456"
        })
        assert login_resp.status_code == 200
        assert "access_token" in login_resp.json()
