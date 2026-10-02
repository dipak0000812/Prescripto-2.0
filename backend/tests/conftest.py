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
from prescripto.storage.client import get_storage_client
from prescripto.storage.exceptions import StorageObjectNotFoundException
from prescripto.api.main import app

# In-memory SQLite for fast testing
import json
TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    TEST_DATABASE_URL,

    connect_args={"check_same_thread": False},
    json_serializer=lambda obj: json.dumps(obj, default=str),
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)



class InMemoryStorageClient:
    """Mock storage client storing objects in-memory for testing."""
    def __init__(self):
        self.objects = {}

    @staticmethod
    def generate_prescription_key(document_id, extension):
        clean_ext = extension.lstrip(".").lower()
        return f"prescriptions/{document_id}/original.{clean_ext}"

    def ensure_bucket_exists(self, bucket_name=None):
        pass

    def put_object(self, key, data, content_type, bucket_name=None):
        self.objects[key] = (data, content_type)

    def get_object(self, key, bucket_name=None):
        if key not in self.objects:
            raise StorageObjectNotFoundException(f"Object {key} not found")
        return self.objects[key][0]

    def delete_object(self, key, bucket_name=None):
        self.objects.pop(key, None)

    def object_exists(self, key, bucket_name=None):
        return key in self.objects

    def generate_presigned_url(self, key, expires_in=60, bucket_name=None):
        return f"https://mock-storage.prescripto.local/{key}?expires={expires_in}&token=dummy"


@pytest.fixture
def mock_storage():
    return InMemoryStorageClient()


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
def client(db_session, mock_storage):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_storage_client] = lambda: mock_storage
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
