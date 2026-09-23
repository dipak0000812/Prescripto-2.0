"""
Tests for Alembic migration upgrade and downgrade cycle.
"""
import pytest
from sqlalchemy import create_engine
from alembic.config import Config
from alembic import command
import os
import tempfile

def test_alembic_upgrade_and_downgrade():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    
    engine = None
    try:
        sqlite_url = f"sqlite:///{db_path}"
        os.environ["DATABASE_URL"] = sqlite_url
        
        from prescripto.config.settings import settings
        settings.DATABASE_URL = sqlite_url

        alembic_cfg = Config("alembic.ini")
        alembic_cfg.set_main_option("sqlalchemy.url", sqlite_url)

        # 1. Test Upgrade
        command.upgrade(alembic_cfg, "head")

        # Verify tables exist
        engine = create_engine(sqlite_url)
        with engine.connect() as conn:
            from sqlalchemy import inspect
            inspector = inspect(conn)
            tables = inspector.get_table_names()
            assert "users" in tables
            assert "prescription_documents" in tables
            assert "prescription_medications" in tables
            assert "medications" in tables
            assert "risk_findings" in tables
            assert "token_blocklist" in tables

            # Verify C-3 fix columns in prescription_medications
            cols = [col["name"] for col in inspector.get_columns("prescription_medications")]
            assert "unit_raw" in cols
            assert "unit_state" in cols
            assert "instructions_raw" in cols
            assert "instructions_state" in cols

        # 2. Test Downgrade
        command.downgrade(alembic_cfg, "base")

        with engine.connect() as conn:
            inspector = inspect(conn)
            tables_after = inspector.get_table_names()
            assert "prescription_medications" not in tables_after
            assert "users" not in tables_after

        # 3. Test Re-Upgrade
        command.upgrade(alembic_cfg, "head")
        with engine.connect() as conn:
            inspector = inspect(conn)
            assert "prescription_medications" in inspector.get_table_names()

    finally:
        if engine:
            engine.dispose()
        if os.path.exists(db_path):
            try:
                os.remove(db_path)
            except OSError:
                pass
