# OBSERVABILITY.md

Goal: debug a failed analysis without ever seeing its contents.

## Structured logging

`structlog`, JSON, one event per stage transition.

```json
{"timestamp":"...","level":"INFO","request_id":"uuid","analysis_id":"uuid",
 "pipeline_stage":"OCR_RECOGNITION","model_version_id":"uuid",
 "status":"COMPLETED","duration_ms":1240,"error_code":null}
```

**Whitelist processor.** Permitted keys only: `timestamp`, `level`, `request_id`, `analysis_id`, `document_id`, `job_id`, `lease_token`, `pipeline_stage`, `model_version_id`, `status`, `duration_ms`, `error_code`, `actor_id`, `provider_name`, `retry_count`.

Anything else is dropped and `prescripto_log_field_dropped_total` increments. A blacklist would require predicting every field a future developer might add; the whitelist fails safe by default and the metric tells you when someone tried.

**Never logged:** image bytes, OCR text, medication names, dosages, `patient_ref`, presigned URLs, tokens, production stack traces.

`request_id` generated at API ingress, propagated into the job row, and re-emitted by the worker — so an async analysis is traceable back to the request that created it.

## Metrics (Prometheus)

| Metric | Type | Labels |
|---|---|---|
| `prescripto_upload_total` | Counter | status |
| `prescripto_analysis_duration_seconds` | Histogram | status |
| `prescripto_pipeline_stage_duration_seconds` | Histogram | stage_name, status |
| `prescripto_stage_failures_total` | Counter | stage_name, error_code |
| `prescripto_job_queue_depth` | Gauge | — |
| `prescripto_job_dead_total` | Counter | — |
| `prescripto_worker_fenced_total` | Counter | — |
| `prescripto_lease_expired_total` | Counter | — |
| `prescripto_safety_provider_errors_total` | Counter | provider_name |
| `prescripto_findings_total` | Counter | check_type, finding_status |
| `prescripto_not_evaluated_total` | Counter | reason |
| `prescripto_review_routing_total` | Counter | review_reason |
| `prescripto_unresolved_medications_total` | Counter | — |
| `prescripto_field_state_total` | Counter | field_name, state |
| `prescripto_deletion_status_total` | Counter | status |
| `prescripto_log_field_dropped_total` | Counter | — |

### The ML-health metrics worth watching

`prescripto_field_state_total{field_name, state}` and `prescripto_unresolved_medications_total` are the early-warning system for model drift. A rising `AMBIGUOUS` rate or `UNRESOLVED` rate means extraction quality is degrading — from a model change, a shift in input quality, or a vocabulary gap — and it shows up here long before anyone notices in review.

`prescripto_not_evaluated_total{reason}` matters for a different reason: if `SOURCE_NOT_COVERING` dominates, the product is honestly reporting that it knows very little about the drugs it's seeing. That's a product-scope signal, not an ops alert.

## Alerts

| Condition | Severity | Action |
|---|---|---|
| Job reaches `DEAD` | High | Operator investigates; analysis will not complete |
| `DeletionJob` in `PARTIAL_FAILURE` > 1h | High | DPDPA erasure obligation at risk |
| Queue depth > 50 sustained | Medium | Second worker (Arch §20 trigger) |
| Worker heartbeat stale > 5 min | High | Worker down |
| Stage failure rate > 20% / 15 min | Medium | Model or input-quality problem |
| `log_field_dropped` > 0 | Medium | Someone tried to log a non-whitelisted field — review the change |
| Storage or DB health check failing | High | |

Deletion `PARTIAL_FAILURE` is high severity for a legal reason, not a technical one: the user asked for erasure and it hasn't completed.

## Health check

`GET /api/v1/health` → `{database, object_storage, worker_heartbeat}`, each `ok|degraded|down`. No auth. Returns 200 with degraded components listed rather than 503 — an orchestrator needs to distinguish "API is up, worker is down" from "everything is down."

## Tracing

Not in V1. Single-process-per-role, and `request_id` correlation covers the debugging need. Reversal trigger: more than one worker type, or a cross-service call worth timing.

## Audit vs logs — different things

| | Audit events | Application logs |
|---|---|---|
| Purpose | Who did what to which resource | Debugging |
| Store | `audit.events` + signed cold export | stdout → log aggregator |
| Retention | Permanent (90d hot + archive) | Rotational |
| Mutability | Append-only | Ephemeral |

Audit records are designed, not "logs we decided to keep." Deriving one from the other is how audit trails end up incomplete.

## Debugging without content

Given a failed `analysis_id`: query `analysis_stages` for which stage and `error_code`; `analysis_jobs` for `retry_count`, `lease_token`, `last_error`; logs by `analysis_id` for timing and model version; `output_json` of prior stages for shape. All without reading a medication name — which is the design goal, not a limitation.