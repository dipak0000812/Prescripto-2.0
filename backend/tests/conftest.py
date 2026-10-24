"""
Pytest Fixtures and Test Setup.

T1.2: DATABASE_URL and JWT keys are injected BEFORE any prescripto module is imported.
pydantic-settings instantiates `settings = Settings()` at the bottom of settings.py, which
runs at first import. The env-var defaulting below happens at conftest import time; as long
as conftest is the first file collected, this wins. For belt-and-suspenders we also patch the
already-live settings object in the autouse session fixture so any test that imports crypto
after the session begins also gets valid keys.

T2.1: Support TEST_DATABASE_URL env var.
- If unset → SQLite in-memory (existing behaviour, unchanged).
- If set to a PostgreSQL URL → run `alembic upgrade head` once per session and give each
  test savepoint-based isolation.

Savepoint vs. truncate decision:
  We use SAVEPOINT (nested transaction) isolation on Postgres. A plain transaction wrapping
  each test would prevent tests from issuing their own COMMITs (e.g. claim_next_job commits
  after claiming). Instead we use SQLAlchemy's `join_transaction_mode="create_savepoint"` so
  the outer fixture transaction becomes the container and each test COMMIT rolls back to the
  savepoint rather than actually committing. This is the standard pytest-sqlalchemy pattern
  for tests that need real COMMITs within a test while keeping isolation.
"""
# ── Must be FIRST — before any prescripto import ──────────────────────────
import os

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization as _serial


def _make_rsa_keypair() -> tuple[str, str]:
    """Return (private_pem, public_pem). Never writes to disk."""
    priv = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    priv_pem = priv.private_bytes(
        encoding=_serial.Encoding.PEM,
        format=_serial.PrivateFormat.PKCS8,
        encryption_algorithm=_serial.NoEncryption(),
    ).decode("utf-8")
    pub_pem = priv.public_key().public_bytes(
        encoding=_serial.Encoding.PEM,
        format=_serial.PublicFormat.SubjectPublicKeyInfo,
    ).decode("utf-8")
    return priv_pem, pub_pem


_PRIVATE_PEM, _PUBLIC_PEM = _make_rsa_keypair()
os.environ.setdefault("JWT_PRIVATE_KEY", _PRIVATE_PEM)
os.environ.setdefault("JWT_PUBLIC_KEY", _PUBLIC_PEM)

# ── T2.1: Determine whether we run against SQLite or PostgreSQL ────────────
import json
import uuid
import pytest
from pathlib import Path
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from fastapi.testclient import TestClient

_TEST_DB_URL: str = os.environ.get("TEST_DATABASE_URL", "")
_USE_POSTGRES: bool = _TEST_DB_URL.startswith("postgresql")

# ── Now safe to import prescripto modules ─────────────────────────────────
from prescripto.db.base import Base
from prescripto.db.session import get_db
from prescripto.db.models.users import User
from prescripto.db.models.enums import Role
from prescripto.auth.crypto import hash_password
from prescripto.config.settings import settings
from prescripto.storage.client import get_storage_client
from prescripto.storage.exceptions import StorageObjectNotFoundException
from prescripto.api.main import app


# ── T1.2: Patch live settings singleton with in-memory keys ───────────────
@pytest.fixture(scope="session", autouse=True)
def _inject_jwt_keys_into_settings():
    """
    Patch the live settings singleton so crypto.py reads valid PEM keys
    regardless of when settings.py was first imported.
    """
    original_priv = settings.JWT_PRIVATE_KEY
    original_pub = settings.JWT_PUBLIC_KEY
    settings.JWT_PRIVATE_KEY = _PRIVATE_PEM      # type: ignore[misc]
    settings.JWT_PUBLIC_KEY = _PUBLIC_PEM         # type: ignore[misc]
    yield
    settings.JWT_PRIVATE_KEY = original_priv      # type: ignore[misc]
    settings.JWT_PUBLIC_KEY = original_pub         # type: ignore[misc]


# ── T2.1: Register the `postgres` marker ─────────────────────────────────
def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "postgres: mark test as requiring a real PostgreSQL database via TEST_DATABASE_URL",
    )


def pytest_collection_modifyitems(config, items):
    """Skip @pytest.mark.postgres tests when TEST_DATABASE_URL is not PostgreSQL."""
    if not _USE_POSTGRES:
        skip_pg = pytest.mark.skip(reason="TEST_DATABASE_URL is not a PostgreSQL URL")
        for item in items:
            if item.get_closest_marker("postgres"):
                item.add_marker(skip_pg)


# ── T2.1: Build the test engine (SQLite or Postgres) ─────────────────────
if _USE_POSTGRES:
    _engine_url = _TEST_DB_URL
    _engine_kwargs: dict = {"pool_pre_ping": True}
else:
    _engine_url = "sqlite:///:memory:"
    _engine_kwargs = {
        "connect_args": {"check_same_thread": False},
    }

engine = create_engine(
    _engine_url,
    json_serializer=lambda obj: json.dumps(obj, default=str),
    **_engine_kwargs,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# ── T2.1: Schema setup (once per session) ────────────────────────────────
@pytest.fixture(scope="session", autouse=True)
def setup_database(_inject_jwt_keys_into_settings):
    """
    SQLite: create tables via SQLAlchemy metadata (fast, no Alembic needed).
    PostgreSQL: run `alembic upgrade head` once using Alembic's Python API so
                the migrated DB is the test target — this also verifies migrations work.
    """
    if _USE_POSTGRES:
        from alembic.config import Config
        from alembic import command as alembic_command

        # Locate alembic.ini relative to this conftest (backend/ dir)
        alembic_ini = Path(__file__).parent.parent / "alembic.ini"
        alembic_cfg = Config(str(alembic_ini))
        alembic_cfg.set_main_option("sqlalchemy.url", _TEST_DB_URL)
        # Inject URL into settings so env.py picks it up
        settings.DATABASE_URL = _TEST_DB_URL  # type: ignore[misc]
        alembic_command.upgrade(alembic_cfg, "head")
        yield
        # Leave the schema in place — Docker container is ephemeral
    else:
        Base.metadata.create_all(bind=engine)
        yield
        Base.metadata.drop_all(bind=engine)


# ── SQLite Savepoint Support Hooks ─────────────────────────────────────────
from sqlalchemy import event


if not _USE_POSTGRES:
    @event.listens_for(engine, "connect")
    def _do_connect(dbapi_connection, connection_record):
        # Disable pysqlite's implicit BEGIN so savepoint management works cleanly
        dbapi_connection.isolation_level = None

    @event.listens_for(engine, "begin")
    def _do_begin(conn):
        conn.exec_driver_sql("BEGIN")


# ── T2.1: Per-test isolation ──────────────────────────────────────────────
@pytest.fixture
def db_session(setup_database):
    """
    Wrap each test in a connection-level transaction + savepoint.
    `join_transaction_mode="create_savepoint"` ensures COMMITs inside the test
    roll back to the savepoint rather than committing to the real DB,
    and a `session.rollback()` in the code under test rolls back to the
    current savepoint and starts a new one, keeping fixture isolation intact.
    """
    connection = engine.connect()
    trans = connection.begin()
    session = TestingSessionLocal(
        bind=connection,
        join_transaction_mode="create_savepoint",
    )
    yield session
    session.close()
    trans.rollback()
    connection.close()


# ── Storage mock ──────────────────────────────────────────────────────────
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
