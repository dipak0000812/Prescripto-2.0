# ERROR-CONTRACT.md

Two distinct error surfaces. Conflating them is the mistake this document exists to prevent.

1. **API errors** — a request failed. Returned as HTTP 4xx/5xx with the envelope below.
2. **Pipeline stage errors** — an analysis stage failed. Returned as **HTTP 200** on the status endpoint, carried in `analysis_stages.error_code`. A failed analysis is a successful status query.

## API error envelope

```json
{"error": {"code": "ANALYSIS_NOT_READY", "message": "human readable", "request_id": "uuid"}}
```

`code` is stable and machine-matched. `message` is for humans and may change — never parse it. `request_id` correlates to structured logs. No stack traces, no SQL, no file paths in production responses.

## API error codes

| Code | HTTP | Meaning |
|---|---|---|
| `INVALID_CREDENTIALS` | 401 | Auth failed |
| `TOKEN_EXPIRED` | 401 | Access token past TTL |
| `TOKEN_REVOKED` | 401 | Refresh token on denylist |
| `BLOCKLIST_UNAVAILABLE` | 401 | Denylist unreachable — fails closed, deliberately |
| `INSUFFICIENT_ROLE` | 403 | Role lacks the operation |
| `FORBIDDEN_RESOURCE_ACCESS` | 403 | Authenticated but not the owner/assignee |
| `RESOURCE_NOT_FOUND` | 404 | Unknown ID, or ID not visible to caller |
| `ANALYSIS_NOT_READY` | 404 | Result requested while QUEUED/PROCESSING/FAILED |
| `UNSUPPORTED_MEDIA_TYPE` | 415 | Magic bytes not in the accepted set |
| `FILE_TOO_LARGE` | 413 | >20 MB |
| `MALFORMED_REQUEST` | 400 | Schema validation failure |
| `MISSING_IDEMPOTENCY_KEY` | 400 | Header absent on upload |
| `IDEMPOTENCY_KEY_CONFLICT` | 409 | Same key, different `file_hash_sha256` |
| `ANALYSIS_NOT_REVIEWABLE` | 409 | Review submitted against a non-reviewable state |
| `DELETION_IN_PROGRESS` | 409 | Operation on a document being deleted |
| `PDF_ACTIVE_CONTENT_REJECTED` | 422 | Embedded JavaScript detected |
| `INTERNAL_ERROR` | 500 | Unhandled — logged with request_id, no detail leaked |
| `STORAGE_UNAVAILABLE` | 503 | Object storage down at upload |

**404-over-403 rule:** a resource the caller may not see returns `RESOURCE_NOT_FOUND`, not `FORBIDDEN_RESOURCE_ACCESS`. `FORBIDDEN_RESOURCE_ACCESS` is only used where the caller already legitimately knows the resource exists (e.g. an assigned reviewer hitting an operator-only action). Otherwise 403 confirms existence to an attacker enumerating UUIDs.

## Pipeline stage error codes

Stored in `analysis_stages.error_code`. Surfaced via `GET /analyses/{id}` at HTTP 200.

| Code | Stage | Analysis outcome |
|---|---|---|
| `FORMAT_UNSUPPORTED` | INGESTION | FAILED |
| `FILE_CORRUPTED` | INGESTION | FAILED |
| `QUALITY_TOO_LOW` | QUALITY_CHECK | REQUIRES_REVIEW |
| `DETECTION_FAILED` | TEXT_DETECTION | REQUIRES_REVIEW |
| `OCR_FAILED` | OCR_RECOGNITION | Fields marked UNREADABLE; continues |
| `EXTRACTION_FAILED` | STRUCTURED_EXTRACTION | FAILED |
| `MODEL_LOAD_FAILED` | any ML stage | FAILED + operator alert |
| `DB_CONSTRAINT_VIOLATION` | REPORT_ASSEMBLY | FAILED |

Note the asymmetry: `QUALITY_TOO_LOW` and `DETECTION_FAILED` route to review rather than failing, because a human can still read a bad scan. `EXTRACTION_FAILED` cannot — there is nothing structured to review.

## `not_evaluated_reason` values

Not errors. A finding that *correctly* reports it couldn't evaluate.

| Value | Meaning |
|---|---|
| `SOURCE_UNAVAILABLE` | Provider timeout or outage |
| `PROVIDER_LACKS_CAPABILITY` | No registered provider supports this check type |
| `UNRESOLVED_IDENTITY` | Medication never resolved to a canonical entity |
| `AMBIGUOUS_IDENTITY` | Multiple candidates scored comparably |
| `SOURCE_NOT_COVERING` | Provider available, has no record for this medication |
| `CHECK_TYPE_DEFERRED` | Check not implemented in V1 (DDI, dosage range) |
| `LICENSE_MODE_EXCLUDED` | Source excluded in this deployment (e.g. SIDER in commercial build) |

> `SOURCE_NOT_COVERING` is the one most likely to be mis-rendered as "safe" in a UI. It means the source was asked and had nothing — which is not evidence of absence. Frontend must render it with the same visual weight as the other NOT_EVALUATED reasons.

## Worker fencing errors

Internal, never reach the API. `WorkerFencedError` (lease expired or superseded) → job released, not failed, and `retry_count` is **not** incremented — a fenced worker is a coordination event, not an execution failure. Incrementing here would exhaust retries on a healthy job.