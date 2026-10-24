"""
Fixture Contract Test:
Validates that db_session fixture correctly isolates tests and that
session.rollback() rolls back uncommitted flushed changes to the savepoint
without destroying seeded fixture data, on both SQLite and PostgreSQL.
"""
import uuid
import pytest
from sqlalchemy.orm import Session
from prescripto.db.models.users import User


def test_fixture_contract_rollback_preserves_seeded_data(db_session: Session):
    # 1. Seed initial data and commit (simulating fixture setup)
    user = User(
        id=uuid.uuid4(),
        username=f"contract_user_{uuid.uuid4().hex[:8]}",
        email=f"contract_{uuid.uuid4().hex[:8]}@example.com",
        hashed_password="test_password_hash",
        role="OPERATOR",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()

    user_id = user.id

    # Verify seeded user exists
    assert db_session.get(User, user_id) is not None

    # 2. Add uncommitted / flushed data (simulating a pipeline run that fails mid-way)
    temp_user = User(
        id=uuid.uuid4(),
        username=f"temp_user_{uuid.uuid4().hex[:8]}",
        email=f"temp_{uuid.uuid4().hex[:8]}@example.com",
        hashed_password="temp_password_hash",
        role="OPERATOR",
        is_active=True,
    )
    db_session.add(temp_user)
    db_session.flush()

    temp_user_id = temp_user.id
    assert db_session.get(User, temp_user_id) is not None

    # 3. Code under test triggers db.rollback()
    db_session.rollback()

    # 4. Assert:
    # - Flushed data was rolled back
    # - Seeded fixture data remains intact
    assert db_session.get(User, temp_user_id) is None, "Uncommitted data must be rolled back"
    assert db_session.get(User, user_id) is not None, "Seeded fixture data must survive rollback"
