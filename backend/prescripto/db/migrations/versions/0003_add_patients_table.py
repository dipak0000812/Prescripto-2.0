"""add_patients_table

Revision ID: 0003
Revises: 0002
Create Date: 2026-10-25 10:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    is_postgres = bind.dialect.name == "postgresql"

    # 1. Update chk_user_role constraint on users table to allow 'PATIENT'
    if is_postgres:
        op.drop_constraint("chk_user_role", "users", type_="check")
        op.create_check_constraint(
            "chk_user_role",
            "users",
            "role IN ('OPERATOR', 'REVIEWER', 'ADMIN', 'PATIENT')",
        )

    # 2. Create patients table
    op.create_table(
        "patients",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("patient_id", sa.String(50), nullable=False, unique=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("phone_number", sa.String(50), nullable=False, unique=True),
        sa.Column("age", sa.Integer(), nullable=True),
        sa.Column("gender", sa.String(20), nullable=True),
        sa.Column("blood_group", sa.String(10), nullable=True),
        sa.Column("address", sa.String(500), nullable=True),
        sa.Column("medical_history", sa.String(2000), nullable=True),
        sa.Column("allergies", sa.String(500), nullable=True),
        sa.Column("emergency_contact", sa.String(100), nullable=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index("idx_patients_patient_id", "patients", ["patient_id"])
    op.create_index("idx_patients_name", "patients", ["name"])
    op.create_index("idx_patients_phone_number", "patients", ["phone_number"])
    op.create_index("idx_patients_user_id", "patients", ["user_id"])
    op.create_index("idx_patients_search", "patients", ["name", "phone_number", "patient_id"])


def downgrade() -> None:
    op.drop_index("idx_patients_search", table_name="patients")
    op.drop_index("idx_patients_user_id", table_name="patients")
    op.drop_index("idx_patients_phone_number", table_name="patients")
    op.drop_index("idx_patients_name", table_name="patients")
    op.drop_index("idx_patients_patient_id", table_name="patients")
    op.drop_table("patients")

    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.drop_constraint("chk_user_role", "users", type_="check")
        op.create_check_constraint(
            "chk_user_role",
            "users",
            "role IN ('OPERATOR', 'REVIEWER', 'ADMIN')",
        )

