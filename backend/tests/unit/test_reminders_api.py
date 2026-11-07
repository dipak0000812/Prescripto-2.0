"""
Unit and API integration tests for Prescripto 2.0 Medicine Reminders.
"""
import uuid
import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from prescripto.api.main import app
from prescripto.db.session import SessionLocal
from prescripto.db.models.users import User
from prescripto.db.models.document import PrescriptionDocument
from prescripto.db.models.analysis import Analysis
from prescripto.db.models.medication import PrescriptionMedication
from prescripto.auth.crypto import hash_password, create_access_token


@pytest.fixture
def test_user(db_session: Session):
    u = db_session.query(User).filter(User.username == "test_reminders_user").first()
    if not u:
        u = User(
            id=uuid.uuid4(),
            username="test_reminders_user",
            email="reminders_user@prescripto.local",
            hashed_password=hash_password("UserPass123!"),
            role="OPERATOR",
            is_active=True,
        )
        db_session.add(u)
        db_session.flush()
    return u


@pytest.fixture
def other_user(db_session: Session):
    u = db_session.query(User).filter(User.username == "other_reminders_user").first()
    if not u:
        u = User(
            id=uuid.uuid4(),
            username="other_reminders_user",
            email="other_user@prescripto.local",
            hashed_password=hash_password("UserPass123!"),
            role="OPERATOR",
            is_active=True,
        )
        db_session.add(u)
        db_session.flush()
    return u


@pytest.fixture
def user_headers(test_user: User):
    token, _ = create_access_token(test_user.id, test_user.username, test_user.role)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def other_headers(other_user: User):
    token, _ = create_access_token(other_user.id, other_user.username, other_user.role)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def sample_analysis(db_session: Session, test_user: User):
    doc = PrescriptionDocument(
        id=uuid.uuid4(),
        uploader_id=test_user.id,
        file_size_bytes=1024,
        mime_type="image/png",
        file_hash_sha256="b" * 64,
        storage_key="prescriptions/test-reminders.png",
        status="UPLOADED",
    )
    db_session.add(doc)

    an = Analysis(
        id=uuid.uuid4(),
        document_id=doc.id,
        status="COMPLETED",
        pipeline_version="1.0.0",
        model_snapshot_id=uuid.uuid4(),
        review_required=False,
    )
    db_session.add(an)

    med = PrescriptionMedication(
        id=uuid.uuid4(),
        analysis_id=an.id,
        line_index=0,
        name_raw="Amoxicillin 500mg",
        name_state="CLEAR",
        strength_raw="500mg",
        strength_state="CLEAR",
        frequency_raw="1-0-1",
        frequency_state="CLEAR",
    )
    db_session.add(med)
    db_session.flush()
    return an, med


def test_vapid_public_key_endpoint(client: TestClient):
    resp = client.get("/api/v1/reminders/vapid-public-key")
    assert resp.status_code == 200
    data = resp.json()
    assert "public_key" in data
    assert len(data["public_key"]) > 20


def test_create_plans_and_get_today(client: TestClient, test_user, user_headers, other_headers, sample_analysis):
    an, med = sample_analysis

    # 1. Create reminder plan
    create_payload = {
        "analysis_id": str(an.id),
        "timezone": "Asia/Kolkata",
        "medications": [
            {
                "medication_line_id": str(med.id),
                "medicine_name": "Amoxicillin 500mg",
                "dosage_text": "1 cap after food",
                "local_times": ["08:30", "21:30"],
                "duration_days": 5,
            }
        ],
    }
    resp = client.post("/api/v1/reminders/plans", json=create_payload, headers=user_headers)
    assert resp.status_code == 201
    plans = resp.json()
    assert len(plans) == 1
    plan_id = plans[0]["id"]
    assert plans[0]["medicine_name"] == "Amoxicillin 500mg"
    assert plans[0]["status"] == "ACTIVE"

    # 2. Get today's reminders
    today_resp = client.get("/api/v1/reminders/today", headers=user_headers)
    assert today_resp.status_code == 200
    today_data = today_resp.json()
    assert "upcoming" in today_data
    assert "overdue" in today_data
    assert "completed" in today_data
    assert today_data["total_due"] >= 0

    # 3. Unauthorized access check: other user sees empty today
    other_today = client.get("/api/v1/reminders/today", headers=other_headers)
    assert other_today.status_code == 200
    assert other_today.json()["total_due"] == 0

    # 4. Actioning an event
    all_events = today_data["upcoming"] + today_data["overdue"]
    if all_events:
        target_event = all_events[0]
        ev_id = target_event["id"]

        # Action: TAKEN
        take_resp = client.patch(
            f"/api/v1/reminders/events/{ev_id}",
            json={"action": "TAKEN"},
            headers=user_headers,
        )
        assert take_resp.status_code == 200
        assert take_resp.json()["status"] == "TAKEN"

        # Other user cannot modify event (403)
        forbidden_resp = client.patch(
            f"/api/v1/reminders/events/{ev_id}",
            json={"action": "SKIP"},
            headers=other_headers,
        )
        assert forbidden_resp.status_code == 403

    # 5. Export ICS calendar
    ics_resp = client.get(f"/api/v1/reminders/plans/{plan_id}/calendar.ics", headers=user_headers)
    assert ics_resp.status_code == 200
    assert "text/calendar" in ics_resp.headers["content-type"]
    assert "BEGIN:VCALENDAR" in ics_resp.text
    assert "Amoxicillin 500mg" in ics_resp.text

    # 6. Web Push subscribe / unsubscribe
    sub_payload = {
        "endpoint": f"https://push.example.com/sub/{uuid.uuid4()}",
        "keys_p256dh": "test-p256dh-key",
        "keys_auth": "test-auth-key",
        "user_agent": "Mozilla/5.0 TestBrowser",
    }
    sub_resp = client.post("/api/v1/reminders/push/subscribe", json=sub_payload, headers=user_headers)
    assert sub_resp.status_code == 204

    unsub_resp = client.delete(
        f"/api/v1/reminders/push/subscribe?endpoint={sub_payload['endpoint']}",
        headers=user_headers,
    )
    assert unsub_resp.status_code == 204

    # 7. Adherence report
    adh_resp = client.get("/api/v1/reminders/adherence", headers=user_headers)
    assert adh_resp.status_code == 200
    adh_data = adh_resp.json()
    assert "overall_adherence_rate" in adh_data
    assert len(adh_data["items"]) >= 1

    # 8. Delete plan
    del_resp = client.delete(f"/api/v1/reminders/plans/{plan_id}", headers=user_headers)
    assert del_resp.status_code == 204
