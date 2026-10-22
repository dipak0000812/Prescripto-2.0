import pytest
from prescripto.auth.crypto import hash_password
from prescripto.db.models.users import User


def test_patient_otp_workflow(client, seeded_users):
    # 1. Send OTP
    res_send = client.post("/api/v1/auth/send-otp", json={"phone_number": "9876543210"})
    assert res_send.status_code == 200
    data_send = res_send.json()
    assert data_send["status"] == "SENT"
    assert data_send["mock_otp"] == "123456"

    # 2. Verify with wrong OTP
    res_bad = client.post("/api/v1/auth/verify-otp", json={"phone_number": "9876543210", "otp": "999999"})
    assert res_bad.status_code == 401

    # 3. Verify with valid OTP
    res_verify = client.post(
        "/api/v1/auth/verify-otp",
        json={"phone_number": "9876543210", "otp": "123456", "name": "Rahul Verma"},
    )
    assert res_verify.status_code == 200
    data_verify = res_verify.json()
    assert "access_token" in data_verify
    assert data_verify["token_type"] == "bearer"
    assert data_verify["user"]["patient_name"] == "Rahul Verma"

    # 4. Check /auth/me
    token = data_verify["access_token"]
    res_me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert res_me.status_code == 200
    me = res_me.json()
    assert me["patient"]["name"] == "Rahul Verma"
    assert me["patient"]["patient_id"] == "PAT-1001"


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
