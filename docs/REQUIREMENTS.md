# REQUIREMENTS.md — Traceable Requirements Specification

Requirement IDs are canonical. Every test, endpoint, and module references these IDs.
Source: PRD v1 §8–§11 + Arch v1.1 §2. Amendments from PROJECT-SPEC.md §1 applied.

## Legend
`M` MUST HAVE (V1 blocker) · `S` SHOULD HAVE · `N` NICE TO HAVE · `D` DEFERRED

## 1. Document Management

| ID | Requirement | Pri | Verified by |
|---|---|---|---|
| FR-DOC-01 | Accept JPEG, PNG, TIFF, single-page PDF | M | API test, magic-byte unit test |
| FR-DOC-02 | Original immutable after ingestion | M | Integration test |
| FR-DOC-03 | Record uploader, sha256 hash, mime, size, storage key | M | DB test |
| FR-DOC-04 | Optional de-identified `patient_ref`; unlinked is valid | M | DB test |
| FR-DOC-05 | Deletion propagates to storage + derived artifacts + manifest | M | E2E deletion test |
| FR-DOC-06 | Reject >20MB at upload | M | API test |

## 2. Analysis

| ID | Requirement | Pri | Verified by |
|---|---|---|---|
| FR-ANA-01 | Asynchronous; upload returns 202 before processing | M | API test |
| FR-ANA-02 | Status endpoint exposes stage-level progress | M | API test |
| FR-ANA-03 | Record pipeline_version, model_snapshot_id, stage statuses | M | DB test |
| FR-ANA-04 | Unique `analysis_id` per run | M | Schema |
| FR-ANA-05 | Failed analysis resubmittable as a new Analysis | M | Integration test |
| FR-ANA-06 | Stage commits idempotent under duplicate dispatch | M | Fence injection test |
| FR-ANA-07 | Expired lease cannot commit, even if uncontested | M | Fence injection test |

## 3. Extraction

| ID | Requirement | Pri | Verified by |
|---|---|---|---|
| FR-OCR-01 | Text detection precedes recognition | M | Pipeline test |
| FR-OCR-02 | Recognition on line crops only, never full page | M | Pipeline test |
| FR-OCR-03 | Per-region confidence produced | M | Unit test |
| FR-OCR-04 | Low-confidence regions routed to review (VLM verification deferred, see D-04) | M | Threshold test |
| FR-OCR-05 | Four-state field assignment; UNREADABLE never coerced to a guess | M | Unit test |
| FR-OCR-06 | Eight structured fields per line: name, strength, dose, unit, frequency, route, duration, instructions | M | DB test — **blocked by PROJECT-SPEC C-3** |

## 4. Normalization

| ID | Requirement | Pri | Verified by |
|---|---|---|---|
| FR-NORM-01 | Match against internal Medication Master via documented strategy | M | Unit test |
| FR-NORM-02 | Unresolvable → UNRESOLVED → review routing, never forced guess | M | Unit test |
| FR-NORM-03 | Resolved links to canonical Medication with full provenance | M | DB test |
| FR-NORM-04 | Record matching_strategy, candidate_score, source_vocabulary | M | DB test |
| FR-NORM-05 | `rxnorm_cui` nullable for India-only formulations | M | Schema |
| FR-NORM-06 | Every Master entry records source_class, source_version, verification_status | M | DB test |

## 5. Safety Screening

| ID | Requirement | Pri | Verified by |
|---|---|---|---|
| FR-SAFE-01 | Screening operates on resolved Medication entities, never raw OCR text | M | Unit test |
| FR-SAFE-02 | Every finding carries a FindingStatus from the canonical enum | M | Schema CHECK |
| FR-SAFE-03 | Every finding records source_name, source_version, snapshot, timestamp | M | Schema NOT NULL |
| FR-SAFE-04 | NOT_EVALUATED requires an explicit reason | M | Schema CHECK |
| FR-SAFE-05 | NOT_EVALUATED / NO_KNOWN_IN_DB never rendered as NO_INTERACTION_EXISTS | M | UI + API test |
| FR-SAFE-06 | Full structured result produced with LLM disabled (it is, in V1) | M | Integration test |
| FR-SAFE-07 | V1 checks limited to DUPLICATE_MEDICATION, EVIDENCE_LOOKUP, ADVERSE_EFFECT | M | Schema CHECK |
| FR-SAFE-08 | Provider without capability returns NOT_EVALUATED, never a null/empty pass | M | Unit test |

## 6. Review

| ID | Requirement | Pri | Verified by |
|---|---|---|---|
| FR-REV-01 | No finding actionable without qualified/authorized human review | M | Product invariant |
| FR-REV-02 | Per-finding approve / flag / escalate | M | API test |
| FR-REV-03 | Reviewer identity + timestamp + action recorded | M | DB test |
| FR-REV-04 | Review decisions never overwrite system findings | M | DB test |
| FR-REV-05 | Reviewer assignment manual in V1 | M | — |
| FR-REV-06 | Review immutable after submission; corrections create new record | M | DB test |

## 7. Reporting

| ID | Requirement | Pri | Verified by |
|---|---|---|---|
| FR-REP-01 | Structured report for every completed analysis | M | API test |
| FR-REP-04 | Report states sources queried + what was not evaluated | M | Schema + API test |
| FR-REP-05 | No language implying comprehensive safety clearance | M | Copy review + content test |
| FR-REP-02/03 | LLM explanation validation + grounding | D | V1.x — see PROJECT-SPEC C-1 |

## 8. Security & Privacy

| ID | Requirement | Pri |
|---|---|---|
| SEC-01 | Caller-scoped access; explicit grant required | M |
| SEC-02 | No public bucket; presigned GET, 60s TTL | M |
| SEC-03 | OPERATOR / REVIEWER / ADMIN separated | M |
| SEC-04 | JWT RS256, 15min access, 7day refresh, PG denylist | M |
| SEC-05 | Encryption at rest (object storage) | M |
| SEC-06 | TLS in transit, all hops | M |
| SEC-08 | No PHI in operational logs — processor-enforced whitelist | M |
| SEC-12 | Upload validated by magic bytes, not extension or client MIME | M |
| SEC-13 | PDF JavaScript stripped/rejected | M |

## 9. Deferred (explicitly out of V1)

| ID | Item | Pre-condition |
|---|---|---|
| D-01 | LLM explanation layer | DPA signed + injection benchmark passed |
| D-02 | Comprehensive DDI checking | Licensed Indian DDI dataset acquired |
| D-03 | Dosage-range checking | Licensed dosage reference integrated |
| D-04 | VLM verification stage | Experiment 4 shows measurable critical-error reduction |
| D-05 | Dedicated NER stage | Experiment shows gain over direct extraction |
| D-06 | Allergy / contraindication checks | Patient allergy record intake designed |
| D-07 | Redis/Celery, Kafka, K8s, vector DB | Measured triggers in Arch v1.1 §20 |
| D-08 | Multi-page PDF, webhooks, auto-assignment, non-English UI, mobile app | Post-V1 |