import pytest
from prescripto.auth.crypto import hash_password
from prescripto.db.models.users import User
from prescripto.auth.otp_provider import DevelopmentOtpProvider
from prescripto.auth.service import AuthService, otp_crypto_module


def test_patient_otp_registration_and_login_workflow(client, seeded_users):
    """Test the new patient registration and login flow via OTP."""
    AuthService.set_otp_provider(DevelopmentOtpProvider())

    phone = "9988776655"

    # Mock OTP generation to return a known value
    original_generate = otp_crypto_module.generate_secure_otp
    otp_crypto_module.generate_secure_otp = lambda length=6: "123456"

    try:
        # 1. Request OTP for registration
        from prescripto.auth.service import _last_otp_sent_time
        _last_otp_sent_time.pop(phone, None)
        res_send = client.post("/api/v1/auth/patient/request-otp", json={"phone_number": phone})
        assert res_send.status_code == 200
        assert res_send.json()["status"] == "SENT"

        # 2. Register with valid OTP
        res_register = client.post("/api/v1/auth/patient/register", json={
            "phone_number": phone,
            "otp": "123456",
            "name": "Rahul Verma"
        })
        assert res_register.status_code == 200
        data_register = res_register.json()
        assert "access_token" in data_register
        assert data_register["user"]["patient_name"] == "Rahul Verma"
        assert data_register["user"]["role"] == "PATIENT"

        # 3. Check /auth/me
        token = data_register["access_token"]
        res_me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert res_me.status_code == 200
        me = res_me.json()
        assert me["patient"]["name"] == "Rahul Verma"
        assert me["patient"]["patient_id"] == "PAT-1001"

        # 4. Test login flow for existing patient
        _last_otp_sent_time.pop(phone, None)
        client.post("/api/v1/auth/patient/request-otp", json={"phone_number": phone})

        res_login = client.post("/api/v1/auth/patient/login", json={
            "phone_number": phone,
            "otp": "123456"
        })
        assert res_login.status_code == 200
        assert "access_token" in res_login.json()
    finally:
        otp_crypto_module.generate_secure_otp = original_generate


def test_doctor_email_login(client, seeded_users, db_session):
    # Ensure doctor exists in test DB session
    doc = db_session.query(User).filter(User.email == "doctor.sharma@prescripto.local").first()
    if not doc:
        doc = User(
            username="doctor_sharma",
            email="doctor.sharma@prescripto.local",
            hashed_password=hash_password("DoctorPass123!"),
            role="REVIEWER",
            is_active=True,
        )
        db_session.add(doc)
        db_session.commit()

    res = client.post(
        "/api/v1/auth/doctor/login",
        json={"email": "doctor.sharma@prescripto.local", "password": "DoctorPass123!"},
    )
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data["user"]["role"] == "REVIEWER"

    token = data["access_token"]
    res_me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert res_me.status_code == 200
    assert res_me.json()["role"] == "REVIEWER"
