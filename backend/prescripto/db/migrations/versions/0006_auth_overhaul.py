"""
Auth System Overhaul - Add email to Patient, OTP table, Password Reset tokens, Doctor registration fields.
"""
import uuid
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add email column to patients table
    op.add_column("patients", sa.Column("email", sa.String(255), nullable=True, unique=True, index=True))
    op.add_column("patients", sa.Column("hashed_password", sa.String(255), nullable=True))
    op.add_column("patients", sa.Column("email_verified", sa.Boolean(), nullable=False, server_default=sa.false()))

    # Create OTP table for persistent OTP storage
    op.create_table(
        "otp_codes",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("code_hash", sa.String(255), nullable=False),
        sa.Column("salt", sa.String(32), nullable=False),
        sa.Column("channel", sa.String(10), nullable=False),  # 'EMAIL' or 'SMS'
        sa.Column("purpose", sa.String(20), nullable=False),  # 'LOGIN', 'REGISTER', 'PASSWORD_RESET'
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False, index=True),
        sa.Column("attempts", sa.Integer(), nullable=False, default=0),
        sa.Column("max_attempts", sa.Integer(), nullable=False, default=3),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
    )

    # Create password reset tokens table
    op.create_table(
        "password_reset_tokens",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("token_hash", sa.String(255), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False, index=True),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    # Add doctor-specific fields to users table
    op.add_column("users", sa.Column("specialization", sa.String(100), nullable=True))
    op.add_column("users", sa.Column("license_number", sa.String(50), nullable=True))
    op.add_column("users", sa.Column("clinic_name", sa.String(255), nullable=True))
    op.add_column("users", sa.Column("clinic_address", sa.String(500), nullable=True))
    op.add_column("users", sa.Column("phone_number", sa.String(50), nullable=True))
    op.add_column("users", sa.Column("bio", sa.Text(), nullable=True))

    # Add email column to users table if not exists (should already exist)
    # Add is_verified column for email verification
    op.add_column("users", sa.Column("is_verified", sa.Boolean(), nullable=False, server_default=sa.false()))


def downgrade() -> None:
    op.drop_column("patients", "email")
    op.drop_column("patients", "hashed_password")
    op.drop_column("patients", "email_verified")
    op.drop_table("otp_codes")
    op.drop_table("password_reset_tokens")
    op.drop_column("users", "specialization")
    op.drop_column("users", "license_number")
    op.drop_column("users", "clinic_name")
    op.drop_column("users", "clinic_address")
    op.drop_column("users", "phone_number")
    op.drop_column("users", "bio")
    op.drop_column("users", "is_verified")