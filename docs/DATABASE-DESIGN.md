# DATABASE-DESIGN.md

**DDL is canonical in `SYSTEM-ARCHITECTURE.md` v1.1 §9 and is not duplicated here.** This document covers what the DDL doesn't state: index strategy, migration policy, and the retention/partitioning plan.

## Required amendment before first migration

PROJECT-SPEC §4 — `prescription_medications` must gain `unit_*` and `instructions_*` field groups. Land this in migration `0001`, not as a later `ALTER`: Tier B annotation schemas derive from these columns, and retrofitting after annotation starts means re-annotating.

## Index strategy

| Index | Table | Rationale |
|---|---|---|
| `idx_analysis_jobs_claimable (status, backoff_until, created_at) WHERE status IN ('PENDING','FAILED')` | analysis_jobs | Partial index — the claim query's hot path. Excludes terminal rows, which dominate the table over time |
| `idx_medications_search` GIN on `to_tsvector(brand_name \|\| ' ' \|\| generic_name)` | medications | Fuzzy candidate generation. ADR-11: FTS before vector DB |
| `idx_token_blocklist_expiry (expires_at)` | token_blocklist | Cleanup sweep |
| **Add:** `(document_id, status)` | analyses | Deletion concurrency check queries this on every DeletionJob tick |
| **Add:** `(analysis_id)` | risk_findings, prescription_medications | Result assembly joins; FKs are not auto-indexed in PostgreSQL |
| **Add:** `(resource_type, resource_id, occurred_at)` | audit.events | Audit lookup by resource |

The four `Add` rows are gaps in v1.1 — FK columns without indexes are the most common cause of slow cascade deletes.

## Migration policy

- Alembic, one migration per PR, forward-only. No editing a merged migration.
- Every migration has a tested `downgrade()`. Untested downgrades are how you discover at 2am that you can't roll back.
- Enum values live in `CHECK` constraints, not PostgreSQL `ENUM` types — adding a value to a native enum is a lock-taking DDL operation; a `CHECK` swap is not.
- Data migrations separate from schema migrations.
- `medications` and `knowledge_snapshots` seeded by idempotent scripts (`scripts/seed_*.py`), never by migrations — seed data is versioned content, not schema.

## Constraint inventory (beyond PKs/FKs)

| Constraint | Purpose |
|---|---|
| `chk_not_evaluated_reason` | NOT_EVALUATED cannot exist without a reason |
| `UNIQUE(analysis_id, stage_name)` | Stage fence |
| `UNIQUE(analysis_id, line_index)` | Extraction idempotency |
| `UNIQUE(prescription_med_id, matching_strategy, source_vocabulary)` | Normalization idempotency |
| `UNIQUE(analysis_id, check_type, source_name, finding_key)` | Safety screening idempotency |
| `UNIQUE(brand_name, generic_name, strength, dosage_form, route)` | Medication Master dedup |
| `file_size_bytes <= 20971520` | Upload limit at the storage layer, not only the API |
| All status columns | `CHECK ... IN (...)` matching PROJECT-SPEC §3 enums exactly |

Enum drift between `CHECK` constraints and Python enums is a CI check, not a convention — see CI-CD.md.

## JSONB usage — justified only

| Column | Why JSONB and not columns |
|---|---|
| `analysis_stages.output_json` | Stage outputs are heterogeneous per stage; never queried by inner field |
| `medications.provenance_metadata` | Variable per source_class; audit trail, not query surface |
| `calibration_snapshots.calibration_curve_data` | Opaque fitted model artifact |
| `reviews.corrections` | Sparse, reviewer-shaped, replayed whole |
| `audit.events.metadata` | Polymorphic by event_type |

Everything else is a typed column. No JSONB is filtered on in a hot path; if that changes, promote to a column.

## Growth and retention

At the planning assumption of 10–50 uploads/day and 50–200 rows/analysis, the database is not a bottleneck in V1 and needs no partitioning. Two tables grow unbounded regardless of prescription deletion:

- `audit.events` — append-only, never deleted. Hourly export to cold storage (Arch §18); **retain 90 days hot, then delete exported rows.** Without this it is the first table to need partitioning.
- `token_blocklist` — swept by scheduled job, rows past `expires_at + 1 day`.

`analysis_stages.output_json` is the largest per-analysis payload. If it dominates, truncate `output_json` for `COMPLETED` stages older than the retention window — the stage status is the audit-relevant part, not the payload.

## Backup and restore

Daily `pg_dump`, 30-day retention. **Restore is not complete until the manifest re-application script runs** (Arch §17) — a bare restore resurrects deleted patient data. This step belongs in the DR runbook as a mandatory, not optional, post-restore action.