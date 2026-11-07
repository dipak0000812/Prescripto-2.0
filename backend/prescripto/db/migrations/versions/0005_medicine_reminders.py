"""add_medicine_reminders_tables

Revision ID: 0005
Revises: 0004
Create Date: 2026-11-05 01:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0005"
down_revision: Union[str, None] = "0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    is_postgres = bind.dialect.name == "postgresql"
    uuid_type = postgresql.UUID(as_uuid=True) if is_postgres else sa.String(36)
    json_type = postgresql.JSONB if is_postgres else sa.JSON()

    # 1. reminder_plans table
    op.create_table(
        "reminder_plans",
        sa.Column("id", uuid_type, primary_key=True, nullable=False),
        sa.Column(
            "user_id",
            uuid_type,
            sa.ForeignKey("users.id", name="fk_reminder_plans_user_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "patient_id",
            uuid_type,
            sa.ForeignKey("patients.id", name="fk_reminder_plans_patient_id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "analysis_id",
            uuid_type,
            sa.ForeignKey("analyses.id", name="fk_reminder_plans_analysis_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "prescription_med_id",
            uuid_type,
            sa.ForeignKey("prescription_medications.id", name="fk_reminder_plans_med_id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("medicine_name", sa.String(255), nullable=False),
        sa.Column("dosage_text", sa.String(255), nullable=True),
        sa.Column("local_times", json_type, nullable=False),
        sa.Column("start_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("timezone", sa.String(64), nullable=False, server_default="Asia/Kolkata"),
        sa.Column(
            "status",
            sa.String(32),
            sa.CheckConstraint("status IN ('ACTIVE', 'PAUSED', 'COMPLETED')", name="chk_reminder_plan_status"),
            nullable=False,
            server_default="ACTIVE",
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("idx_reminder_plans_user_status", "reminder_plans", ["user_id", "status"])
    op.create_index("idx_reminder_plans_analysis", "reminder_plans", ["analysis_id"])

    # 2. reminder_events table
    op.create_table(
        "reminder_events",
        sa.Column("id", uuid_type, primary_key=True, nullable=False),
        sa.Column(
            "plan_id",
            uuid_type,
            sa.ForeignKey("reminder_plans.id", name="fk_reminder_events_plan_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("due_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "status",
            sa.String(32),
            sa.CheckConstraint(
                "status IN ('PENDING', 'SENT', 'TAKEN', 'SNOOZED', 'SKIPPED', 'MISSED')",
                name="chk_reminder_event_status",
            ),
            nullable=False,
            server_default="PENDING",
        ),
        sa.Column("acted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("sent_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("idx_reminder_events_due_status", "reminder_events", ["due_at", "status"])
    op.create_index("idx_reminder_events_plan_id", "reminder_events", ["plan_id"])

    # 3. push_subscriptions table
    op.create_table(
        "push_subscriptions",
        sa.Column("id", uuid_type, primary_key=True, nullable=False),
        sa.Column(
            "user_id",
            uuid_type,
            sa.ForeignKey("users.id", name="fk_push_sub_user_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("endpoint", sa.Text(), nullable=False, unique=True),
        sa.Column("keys_p256dh", sa.Text(), nullable=False),
        sa.Column("keys_auth", sa.Text(), nullable=False),
        sa.Column("user_agent", sa.String(512), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("idx_push_sub_user", "push_subscriptions", ["user_id"])


def downgrade() -> None:
    op.drop_table("push_subscriptions")
    op.drop_table("reminder_events")
    op.drop_table("reminder_plans")

