"""add_medication_audit_trail

Revision ID: 0004
Revises: 0003
Create Date: 2026-11-04 18:30:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    is_postgres = bind.dialect.name == "postgresql"
    uuid_type = postgresql.UUID(as_uuid=True) if is_postgres else sa.String(36)

    # Backward-compatible nullable / default columns on prescription_medications
    with op.batch_alter_table("prescription_medications") as batch_op:
        batch_op.add_column(sa.Column("original_name_raw", sa.String(255), nullable=True))
        batch_op.add_column(sa.Column("original_strength_raw", sa.String(100), nullable=True))
        batch_op.add_column(sa.Column("original_dose_raw", sa.String(100), nullable=True))
        batch_op.add_column(sa.Column("original_frequency_raw", sa.String(100), nullable=True))
        batch_op.add_column(sa.Column("original_route_raw", sa.String(100), nullable=True))
        batch_op.add_column(sa.Column("original_duration_raw", sa.String(100), nullable=True))
        batch_op.add_column(sa.Column("original_instructions_raw", sa.String(500), nullable=True))
        batch_op.add_column(
            sa.Column(
                "is_edited",
                sa.Boolean(),
                nullable=False,
                server_default=sa.text("0" if not is_postgres else "false"),
            )
        )
        batch_op.add_column(
            sa.Column(
                "edited_by_user_id",
                uuid_type,
                sa.ForeignKey("users.id", name="fk_prescription_meds_edited_by", ondelete="SET NULL"),
                nullable=True,
            )
        )
        batch_op.add_column(
            sa.Column(
                "edited_at",
                sa.DateTime(timezone=True),
                nullable=True,
            )
        )


def downgrade() -> None:
    with op.batch_alter_table("prescription_medications") as batch_op:
        batch_op.drop_column("edited_at")
        batch_op.drop_column("edited_by_user_id")
        batch_op.drop_column("is_edited")
        batch_op.drop_column("original_instructions_raw")
        batch_op.drop_column("original_duration_raw")
        batch_op.drop_column("original_route_raw")
        batch_op.drop_column("original_frequency_raw")
        batch_op.drop_column("original_dose_raw")
        batch_op.drop_column("original_strength_raw")
        batch_op.drop_column("original_name_raw")
