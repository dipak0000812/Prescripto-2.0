"""initial_schema

Revision ID: 0001
Revises: 
Create Date: 2026-09-23 20:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    is_postgres = bind.dialect.name == "postgresql"

    if is_postgres:
        op.execute('CREATE EXTENSION IF NOT EXISTS "pgcrypto"')

    # 1. users
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("username", sa.String(100), nullable=False, unique=True),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("role", sa.String(50), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("role IN ('OPERATOR', 'REVIEWER', 'ADMIN')", name="chk_user_role"),
    )
    op.create_index("idx_users_username", "users", ["username"])
    op.create_index("idx_users_email", "users", ["email"])

    # 2. prescription_documents
    op.create_table(
        "prescription_documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("uploader_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("patient_ref", sa.String(255), nullable=True),
        sa.Column("storage_key", sa.String(500), nullable=True),
        sa.Column("file_hash_sha256", sa.String(64), nullable=False),
        sa.Column("mime_type", sa.String(50), nullable=False),
        sa.Column("file_size_bytes", sa.BigInteger(), nullable=False),
        sa.Column("status", sa.String(50), nullable=False, server_default="UPLOAD_PENDING"),
        sa.Column("uploaded_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("mime_type IN ('image/jpeg', 'image/png', 'image/tiff', 'application/pdf')", name="chk_prescription_mime_type"),
        sa.CheckConstraint("file_size_bytes > 0 AND file_size_bytes <= 20971520", name="chk_prescription_file_size"),
        sa.CheckConstraint("status IN ('UPLOAD_PENDING', 'UPLOADED', 'DELETION_REQUESTED', 'DELETION_IN_PROGRESS', 'DELETED')", name="chk_prescription_status"),
    )
    op.create_index("idx_prescription_documents_uploader", "prescription_documents", ["uploader_id"])
    op.create_index("idx_prescription_documents_status", "prescription_documents", ["status"])
    op.create_index("idx_prescription_documents_hash", "prescription_documents", ["file_hash_sha256"])

    # 3. model_versions
    op.create_table(
        "model_versions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("model_name", sa.String(100), nullable=False),
        sa.Column("model_version", sa.String(50), nullable=False),
        sa.Column("checkpoint_sha256", sa.String(64), nullable=False),
        sa.Column("artifact_storage_key", sa.String(500), nullable=False),
        sa.Column("framework", sa.String(50), nullable=False),
        sa.Column("license", sa.String(100), nullable=False),
        sa.Column("registered_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("model_name", "model_version", name="uq_model_name_version"),
    )

    # 4. calibration_snapshots
    op.create_table(
        "calibration_snapshots",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("model_version_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("model_versions.id"), nullable=False),
        sa.Column("calibration_dataset_ver", sa.String(100), nullable=False),
        sa.Column("review_threshold", sa.Float(), nullable=False),
        sa.Column("calibration_curve_data", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("idx_calibration_model_ver", "calibration_snapshots", ["model_version_id"])

    # 5. knowledge_snapshots
    op.create_table(
        "knowledge_snapshots",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("source_name", sa.String(100), nullable=False),
        sa.Column("source_version", sa.String(50), nullable=False),
        sa.Column("license_mode", sa.String(50), nullable=False),
        sa.Column("snapshot_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("record_count", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("license_mode IN ('COMMERCIAL_PERMISSIVE', 'RESEARCH_ONLY', 'PUBLIC_DOMAIN')", name="chk_knowledge_license_mode"),
    )

    # 6. analyses
    op.create_table(
        "analyses",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("document_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("prescription_documents.id"), nullable=False),
        sa.Column("status", sa.String(50), nullable=False, server_default="QUEUED"),
        sa.Column("pipeline_version", sa.String(50), nullable=False),
        sa.Column("model_snapshot_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("model_versions.id"), nullable=False),
        sa.Column("review_required", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("review_reasons", postgresql.ARRAY(sa.String()).with_variant(sa.JSON(), "sqlite"), nullable=False),
        sa.Column("error_detail", sa.String(1000), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint(
            "status IN ('QUEUED', 'PROCESSING', 'COMPLETED', 'REQUIRES_REVIEW', 'REVIEWING', 'REVIEWED_COMPLETE', 'REVIEWED_ESCALATED', 'FAILED')",
            name="chk_analysis_status",
        ),
    )
    op.create_index("idx_analyses_document_id", "analyses", ["document_id"])
    op.create_index("idx_analyses_doc_status", "analyses", ["document_id", "status"])

    # 7. analysis_jobs
    op.create_table(
        "analysis_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("analysis_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("analyses.id"), nullable=False),
        sa.Column("status", sa.String(50), nullable=False, server_default="PENDING"),
        sa.Column("lease_owner", sa.String(255), nullable=True),
        sa.Column("lease_token", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("lease_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("heartbeat_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("max_retries", sa.Integer(), nullable=False, server_default="3"),
        sa.Column("backoff_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error", sa.String(1000), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("status IN ('PENDING', 'CLAIMED', 'RUNNING', 'SUCCEEDED', 'FAILED', 'DEAD', 'CANCELLED')", name="chk_job_status"),
    )
    op.create_index("idx_analysis_jobs_analysis_id", "analysis_jobs", ["analysis_id"])
    if is_postgres:
        op.create_index(
            "idx_analysis_jobs_claimable",
            "analysis_jobs",
            ["status", "backoff_until", "created_at"],
            postgresql_where=sa.text("status IN ('PENDING', 'FAILED')"),
        )
    else:
        op.create_index("idx_analysis_jobs_claimable", "analysis_jobs", ["status", "backoff_until", "created_at"])

    # 8. analysis_stages
    op.create_table(
        "analysis_stages",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("analysis_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("analyses.id"), nullable=False),
        sa.Column("stage_name", sa.String(100), nullable=False),
        sa.Column("lease_token", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(50), nullable=False, server_default="RUNNING"),
        sa.Column("output_json", sa.JSON(), nullable=True),
        sa.Column("error_code", sa.String(100), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("status IN ('RUNNING', 'COMPLETED', 'FAILED', 'SKIPPED')", name="chk_stage_status"),
        sa.UniqueConstraint("analysis_id", "stage_name", name="uq_analysis_stage"),
    )
    op.create_index("idx_analysis_stages_analysis_id", "analysis_stages", ["analysis_id"])

    # 9. medications (Global Master)
    op.create_table(
        "medications",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("brand_name", sa.String(255), nullable=False),
        sa.Column("generic_name", sa.String(255), nullable=False),
        sa.Column("active_ingredients", postgresql.ARRAY(sa.String()).with_variant(sa.JSON(), "sqlite"), nullable=False),
        sa.Column("strength", sa.String(100), nullable=True),
        sa.Column("dosage_form", sa.String(100), nullable=True),
        sa.Column("route", sa.String(100), nullable=True),
        sa.Column("rxnorm_cui", sa.String(50), nullable=True),
        sa.Column("source_class", sa.String(50), nullable=False),
        sa.Column("source_version", sa.String(50), nullable=False),
        sa.Column("verification_status", sa.String(50), nullable=False, server_default="UNVERIFIED"),
        sa.Column("provenance_metadata", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint(
            "source_class IN ('CDSCO_REGULATORY', 'RXNORM', 'MANUFACTURER_VERIFIED', 'RESEARCH_VOCABULARY', 'MANUAL_EXPERT')",
            name="chk_medication_source_class",
        ),
        sa.CheckConstraint(
            "verification_status IN ('VERIFIED_AUTHORITY', 'PROVISIONAL', 'EXPERT_CONFIRMED', 'UNVERIFIED')",
            name="chk_medication_verification_status",
        ),
        sa.UniqueConstraint("brand_name", "generic_name", "strength", "dosage_form", "route", name="uq_medication_identity"),
    )
    if is_postgres:
        op.execute(
            "CREATE INDEX idx_medications_search ON medications USING gin (to_tsvector('english', brand_name || ' ' || generic_name))"
        )

    # 10. prescription_medications (WITH C-3 FIX: unit_* and instructions_*)
    f_check = "('CLEAR', 'AMBIGUOUS', 'UNREADABLE', 'NOT_PRESENT')"
    op.create_table(
        "prescription_medications",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("analysis_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("analyses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("line_index", sa.Integer(), nullable=False),
        sa.Column("name_raw", sa.String(255), nullable=True),
        sa.Column("name_state", sa.String(20), nullable=False, server_default="NOT_PRESENT"),
        sa.Column("name_confidence", sa.Float(), nullable=True),
        sa.Column("strength_raw", sa.String(100), nullable=True),
        sa.Column("strength_state", sa.String(20), nullable=False, server_default="NOT_PRESENT"),
        sa.Column("strength_confidence", sa.Float(), nullable=True),
        sa.Column("dose_raw", sa.String(100), nullable=True),
        sa.Column("dose_state", sa.String(20), nullable=False, server_default="NOT_PRESENT"),
        sa.Column("dose_confidence", sa.Float(), nullable=True),
        # C-3 Fix columns
        sa.Column("unit_raw", sa.String(50), nullable=True),
        sa.Column("unit_state", sa.String(20), nullable=False, server_default="NOT_PRESENT"),
        sa.Column("unit_confidence", sa.Float(), nullable=True),
        sa.Column("frequency_raw", sa.String(100), nullable=True),
        sa.Column("frequency_state", sa.String(20), nullable=False, server_default="NOT_PRESENT"),
        sa.Column("frequency_confidence", sa.Float(), nullable=True),
        sa.Column("route_raw", sa.String(100), nullable=True),
        sa.Column("route_state", sa.String(20), nullable=False, server_default="NOT_PRESENT"),
        sa.Column("route_confidence", sa.Float(), nullable=True),
        sa.Column("duration_raw", sa.String(100), nullable=True),
        sa.Column("duration_state", sa.String(20), nullable=False, server_default="NOT_PRESENT"),
        sa.Column("duration_confidence", sa.Float(), nullable=True),
        # C-3 Fix columns
        sa.Column("instructions_raw", sa.String(500), nullable=True),
        sa.Column("instructions_state", sa.String(20), nullable=False, server_default="NOT_PRESENT"),
        sa.Column("instructions_confidence", sa.Float(), nullable=True),
        sa.CheckConstraint(f"name_state IN {f_check}", name="chk_name_state"),
        sa.CheckConstraint(f"strength_state IN {f_check}", name="chk_strength_state"),
        sa.CheckConstraint(f"dose_state IN {f_check}", name="chk_dose_state"),
        sa.CheckConstraint(f"unit_state IN {f_check}", name="chk_unit_state"),
        sa.CheckConstraint(f"frequency_state IN {f_check}", name="chk_frequency_state"),
        sa.CheckConstraint(f"route_state IN {f_check}", name="chk_route_state"),
        sa.CheckConstraint(f"duration_state IN {f_check}", name="chk_duration_state"),
        sa.CheckConstraint(f"instructions_state IN {f_check}", name="chk_instructions_state"),
        sa.UniqueConstraint("analysis_id", "line_index", name="uq_prescription_med_line"),
    )
    op.create_index("idx_presc_med_analysis_id", "prescription_medications", ["analysis_id"])

    # 11. medication_candidates
    op.create_table(
        "medication_candidates",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("prescription_med_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("prescription_medications.id", ondelete="CASCADE"), nullable=False),
        sa.Column("analysis_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("analyses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("extracted_text", sa.String(255), nullable=False),
        sa.Column("matching_strategy", sa.String(50), nullable=False),
        sa.Column("candidate_score", sa.Float(), nullable=False),
        sa.Column("source_vocabulary", sa.String(100), nullable=False),
        sa.Column("resolved_medication_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("medications.id"), nullable=True),
        sa.Column("resolution_status", sa.String(20), nullable=False),
        sa.CheckConstraint("resolution_status IN ('RESOLVED', 'UNRESOLVED', 'AMBIGUOUS')", name="chk_candidate_resolution_status"),
        sa.UniqueConstraint("prescription_med_id", "matching_strategy", "source_vocabulary", name="uq_candidate_strategy_vocab"),
    )
    op.create_index("idx_med_cand_presc_med_id", "medication_candidates", ["prescription_med_id"])
    op.create_index("idx_med_cand_analysis_id", "medication_candidates", ["analysis_id"])

    # 12. risk_findings
    op.create_table(
        "risk_findings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("analysis_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("analyses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("check_type", sa.String(50), nullable=False),
        sa.Column("finding_key", sa.String(255), nullable=False),
        sa.Column("finding_status", sa.String(50), nullable=False),
        sa.Column("medication_ids", postgresql.ARRAY(postgresql.UUID(as_uuid=True)).with_variant(sa.JSON(), "sqlite"), nullable=False),
        sa.Column("evidence_text", sa.String(2000), nullable=True),
        sa.Column("source_name", sa.String(100), nullable=False),
        sa.Column("source_version", sa.String(50), nullable=False),
        sa.Column("knowledge_snapshot_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("knowledge_snapshots.id"), nullable=True),
        sa.Column("confidence_score", sa.Float(), nullable=True),
        sa.Column("check_timestamp", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("not_evaluated_reason", sa.String(100), nullable=True),
        sa.CheckConstraint("check_type IN ('DUPLICATE_MEDICATION', 'EVIDENCE_LOOKUP', 'ADVERSE_EFFECT')", name="chk_finding_check_type"),
        sa.CheckConstraint(
            "finding_status IN ('CONFIRMED_BY_SOURCE', 'POTENTIAL', 'INSUFFICIENT_EVIDENCE', 'NOT_EVALUATED', 'REQUIRES_REVIEW')",
            name="chk_finding_status",
        ),
        sa.CheckConstraint("finding_status != 'NOT_EVALUATED' OR not_evaluated_reason IS NOT NULL", name="chk_not_evaluated_reason"),
        sa.UniqueConstraint("analysis_id", "check_type", "source_name", "finding_key", name="uq_finding_identity"),
    )
    op.create_index("idx_risk_findings_analysis_id", "risk_findings", ["analysis_id"])

    # 13. reviews
    op.create_table(
        "reviews",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("analysis_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("analyses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("reviewer_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("status", sa.String(50), nullable=False, server_default="PENDING_ASSIGNMENT"),
        sa.Column("corrections", sa.JSON(), nullable=True),
        sa.Column("notes", sa.String(2000), nullable=True),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("status IN ('PENDING_ASSIGNMENT', 'ASSIGNED', 'IN_PROGRESS', 'SUBMITTED', 'ESCALATED')", name="chk_review_status"),
    )
    op.create_index("idx_reviews_analysis_id", "reviews", ["analysis_id"])
    op.create_index("idx_reviews_reviewer_id", "reviews", ["reviewer_id"])

    # 14. deletion_jobs
    op.create_table(
        "deletion_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("document_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("prescription_documents.id"), nullable=False),
        sa.Column("status", sa.String(50), nullable=False, server_default="REQUESTED"),
        sa.Column("manifest_written", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_detail", sa.String(1000), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint(
            "status IN ('REQUESTED', 'DB_TOMBSTONED', 'STORAGE_DELETING', 'VERIFYING', 'COMPLETE', 'PARTIAL_FAILURE')",
            name="chk_deletion_job_status",
        ),
    )
    op.create_index("idx_deletion_jobs_document_id", "deletion_jobs", ["document_id"])

    # 15. token_blocklist
    op.create_table(
        "token_blocklist",
        sa.Column("jti", sa.String(255), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("idx_token_blocklist_expiry", "token_blocklist", ["expires_at"])
    op.create_index("idx_token_blocklist_user", "token_blocklist", ["user_id"])

    # 16. audit_events
    op.create_table(
        "audit_events",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("event_type", sa.String(100), nullable=False),
        sa.Column("actor_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("resource_type", sa.String(100), nullable=False),
        sa.Column("resource_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("metadata", sa.JSON(), nullable=False),
    )
    op.create_index("idx_audit_events_type", "audit_events", ["event_type"])
    op.create_index("idx_audit_resource_lookup", "audit_events", ["resource_type", "resource_id", "occurred_at"])


def downgrade() -> None:
    bind = op.get_bind()
    is_postgres = bind.dialect.name == "postgresql"

    # Drop in reverse topological order
    op.drop_table("audit_events")
    op.drop_table("token_blocklist")
    op.drop_table("deletion_jobs")
    op.drop_table("reviews")
    op.drop_table("risk_findings")
    op.drop_table("medication_candidates")
    op.drop_table("prescription_medications")
    if is_postgres:
        op.execute("DROP INDEX IF EXISTS idx_medications_search")
    op.drop_table("medications")
    op.drop_table("analysis_stages")
    op.drop_table("analysis_jobs")
    op.drop_table("analyses")
    op.drop_table("knowledge_snapshots")
    op.drop_table("calibration_snapshots")
    op.drop_table("model_versions")
    op.drop_table("prescription_documents")
    op.drop_table("users")
