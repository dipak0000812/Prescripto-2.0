# API-CONTRACT.md

Machine-readable schema: [`openapi.yaml`](openapi.yaml) — canonical. This covers behavior the spec can't express, plus the layer-crossing contract matrix.

**Aligned to:** Arch v1.1 + PROJECT-SPEC v1.0. LLM explanation absent (ADR-09); check types limited to three (ADR-08).

## Contract matrix

No endpoint exists without a row here. No row exists without an endpoint. Change both together or neither.

| Frontend operation | Endpoint | Handler | Domain service | DB effect |
|---|---|---|---|---|
| Log in | `POST /auth/token` | `AuthRouter.token` | `AuthService.authenticate()` | `users` read |
| Refresh session | `POST /auth/refresh` | `AuthRouter.refresh` | `AuthService.refresh()` | `token_blocklist` read |
| Upload | `POST /prescriptions` | `PrescriptionRouter.create` | `IngestPrescription` use case | `prescription_documents` + `analyses` + `analysis_jobs` insert |
| List documents | `GET /prescriptions` | `PrescriptionRouter.list` | `PrescriptionService.list_for_caller()` | `prescription_documents` read |
| View document + image | `GET /prescriptions/{id}` | `PrescriptionRouter.get` | `PrescriptionService.get()` + `StorageService.presign()` | read + presign |
| Poll status | `GET /analyses/{id}` | `AnalysisRouter.status` | `AnalysisService.get_status()` | `analyses` + `analysis_stages` read |
| View result | `GET /analyses/{id}/result` | `AnalysisRouter.result` | `AnalysisService.get_result()` | `analyses` + `prescription_medications` + `medication_candidates` + `risk_findings` read |
| Submit review | `POST /analyses/{id}/review` | `ReviewRouter.submit` | `ReviewService.submit()` | `reviews` insert + `analyses` status update |
| Delete | `DELETE /prescriptions/{id}` | `PrescriptionRouter.delete` | `TombstoneDocument` use case | `deletion_jobs` insert + status update |
| *(no endpoint — async)* | — | `AnalysisWorker` | full pipeline | stage/line/candidate/finding writes |

## Behavior not in the schema

**Result gating.** `GET /analyses/{id}/result` returns `404 ANALYSIS_NOT_READY` for `QUEUED`, `PROCESSING`, `FAILED`. Never a partial body, never a 200 with empty arrays. Clients key off the code, not off emptiness — an empty findings array on a completed analysis is a real, meaningful result (nothing found), and must not be confused with "not ready."

**Idempotency.** `Idempotency-Key` required on upload. Same key + same `file_hash_sha256` → replays the original `202` with the existing IDs. Same key + different hash → `409 IDEMPOTENCY_KEY_CONFLICT`. Missing header → `400`.

**Async contract.** Upload returns before processing starts. Polling is the V1 pattern; webhooks deferred. Suggested interval 2–5 s — analyses run 30–180 s, so faster polling only adds load.

**Presigned URLs.** `image_url` in `GET /prescriptions/{id}` is a 60-second bearer capability. Clients must not cache or persist it; refetch the parent resource instead. The API never logs or stores it.

**Auth.** Access 15 min, refresh 7 days. Refresh checks a PostgreSQL denylist and **fails closed** — `401 BLOCKLIST_UNAVAILABLE` if the DB is unreachable. Access tokens are stateless and unrevocable within their TTL; this is a documented accepted risk, not an oversight.

**Coverage disclaimer.** `coverage_disclaimer` is required and non-empty on every result response. It cannot be omitted, and a client must not hide it. It is the mechanism by which "we found nothing" is prevented from reading as "there is nothing."

## Field naming

`snake_case` throughout — DB, DTOs, API, frontend types. The frontend generates types from `/openapi.json` and does not rename. `medication_name` is never `medicineName`, `drugName`, or `name`.

## Pagination

`GET /prescriptions`: `page` (1-based), `page_size` (default 20, max 100). Response carries `items`, `page`, `page_size`, `total`. Caller-scoped — an OPERATOR sees only their own uploads.

## Versioning

Breaking change → `/api/v2/` with 6-month `/v1` deprecation. Non-breaking (new optional field, new enum value on an existing field) ships in `/v1`.

Clients must tolerate unknown enum values rather than crashing — new `not_evaluated_reason` values are expected as providers are added, and a client that hard-fails on an unrecognized reason will break on a non-breaking change.

## Error handling

Full catalog in [`ERROR-CONTRACT.md`](ERROR-CONTRACT.md). Envelope: `{"error": {"code", "message", "request_id"}}`. Match on `code` only — `message` is human-facing and may change without notice.

## Frontend obligations

These are contract terms, not UI suggestions — the API is built to make each one possible, and a client that violates them breaks the product's safety posture:

1. `NOT_EVALUATED` is rendered with the same visual weight as any other finding — never collapsed, never greyed into invisibility, never omitted.
2. Absence of findings is never rendered as a safe/clear/pass state.
3. Field `state` is always shown alongside its value. A value without its state is a value asserted with false confidence.
4. `not_evaluated[]` is always rendered. It is not a details-on-demand section.
5. No aggregate confidence score is computed client-side. The API deliberately doesn't return one (PRD §17.1); deriving one in the UI reintroduces exactly the flattening the API prevents.