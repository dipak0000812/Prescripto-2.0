"""
Unit tests for robust OTP authentication, provider abstraction, rate limiting, and registration/login separation.
"""
import pytest
from unittest.mock import AsyncMock
from prescripto.auth.otp_provider import IOtpProvider, DevelopmentOtpProvider, ProductionOtpProvider
from prescripto.auth.otp_crypto import generate_secure_otp, hash_otp, verify_otp_secure
from prescripto.auth.service import AuthService
from prescripto.auth.exceptions import InvalidCredentialsException, RateLimitExceededException

class MockSmsProvider(IOtpProvider):
    def __init__(self, should_succeed=True):
        self.should_succeed = should_succeed
        self.last_sent = None

    async def send_otp(self, recipient: str, otp: str, channel: str) -> bool:
        self.last_sent = (recipient, otp, channel)
        return self.should_succeed

@pytest.mark.asyncio
async def test_otp_generation_and_hashing():
    otp = generate_secure_otp(6)
    assert len(otp) == 6
    assert otp.isdigit()

    salt = "testsalt"
    h = hash_otp(otp, salt)
    assert verify_otp_secure(otp, h, salt) is True
    assert verify_otp_secure("000000", h, salt) is False

@pytest.mark.asyncio
async def test_auth_service_request_otp_success():
    mock_provider = MockSmsProvider(should_succeed=True)
    AuthService.set_otp_provider(mock_provider)

    res = await AuthService.request_otp("9876543210")
    assert res["status"] == "SENT"
    assert res["phone_number"] == "9876543210"
    assert mock_provider.last_sent is not None
    assert mock_provider.last_sent[0] == "9876543210"
    assert len(mock_provider.last_sent[1]) == 6

@pytest.mark.asyncio
async def test_auth_service_resend_cooldown():
    mock_provider = MockSmsProvider(should_succeed=True)
    AuthService.set_otp_provider(mock_provider)

    # First request succeeds
    await AuthService.request_otp("9112233445")

    # Immediate second request should raise RateLimitExceededException due to 60s cooldown
    with pytest.raises(RateLimitExceededException):
        await AuthService.request_otp("9112233445")

def test_production_provider_raises_not_implemented():
    prod_provider = ProductionOtpProvider()
    import asyncio
    with pytest.raises(NotImplementedError):
        asyncio.run(prod_provider.send_otp("1234567890", "123456", "SMS"))
