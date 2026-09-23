"""
Pytest Fixtures and Test Setup.
"""
import uuid
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from fastapi.testclient import TestClient

from prescripto.db.base import Base
from prescripto.db.session import get_db
from prescripto.db.models.users import User
from prescripto.db.models.enums import Role
from prescripto.auth.crypto import hash_password
from prescripto.api.main import app

# In-memory SQLite for fast testing
TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session():
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def seeded_users(db_session: Session):
    operator = User(
        id=uuid.uuid4(),
        username="test_operator",
        email="operator@prescripto.local",
        hashed_password=hash_password("OperatorPass123!"),
        role=Role.OPERATOR.value,
        is_active=True,
    )
    reviewer = User(
        id=uuid.uuid4(),
        username="test_reviewer",
        email="reviewer@prescripto.local",
        hashed_password=hash_password("ReviewerPass123!"),
        role=Role.REVIEWER.value,
        is_active=True,
    )
    admin = User(
        id=uuid.uuid4(),
        username="test_admin",
        email="admin@prescripto.local",
        hashed_password=hash_password("AdminPass123!"),
        role=Role.ADMIN.value,
        is_active=True,
    )
    db_session.add_all([operator, reviewer, admin])
    db_session.commit()
    return {"operator": operator, "reviewer": reviewer, "admin": admin}
