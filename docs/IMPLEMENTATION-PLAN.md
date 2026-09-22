# IMPLEMENTATION-PLAN.md

**Team:** Dipak (architecture) · Bhushan (backend) · Aakanksha (frontend) · Prachi (AI/ML)
**Window:** ~2–2.5 months · **Compute:** free tier only

## Two things gate everything

1. **Tier B does not exist.** No model can be selected, no threshold set, no metric reported until it does. Collection and annotation are slow, human, and not parallelizable by adding code.
2. **Free-tier feasibility for TrOCR fine-tuning is unverified.** If a fine-tune doesn't fit inside a Colab session, the ML plan changes shape entirely.

Both are started in week 1, in parallel with slice work, because both are long-lead and neither is under our control.

## Vertical slices

Each slice is end-to-end and ships with tests. No slice builds a whole layer.

| # | Slice | Delivers | Owner |
|---|---|---|---|
| 0 | Skeleton | Compose up, migrations, health check, auth, CI green | Bhushan + Dipak |
| 1 | Upload | POST → storage → DB row → 202 + IDs; idempotency; deletion stub | Bhushan |
| 2 | Job + fence | Queue, lease, heartbeat, backoff, DEAD; **fence tests pass** | Bhushan + Dipak |
| 3 | Ingest + quality | INGESTION, QUALITY_CHECK stages; status endpoint real | Prachi |
| 4 | Detect + OCR | TEXT_DETECTION, OCR_RECOGNITION; crops stored; raw confidence | Prachi |
| 5 | Extraction | STRUCTURED_EXTRACTION; 8 fields; `FieldState` assigned | Prachi |
| 6 | Normalization | Medication Master seeded; candidate generation; RESOLVED/AMBIGUOUS/UNRESOLVED | Prachi + Bhushan |
| 7 | Safety | DUPLICATE_MEDICATION + capability-gated providers; NOT_EVALUATED paths | Bhushan |
| 8 | Report + routing | REPORT_ASSEMBLY, review routing, coverage disclaimer, result endpoint | Bhushan |
| 9 | Review UI | Image + fields + states + findings + not-evaluated; submit decisions | Aakanksha |
| 10 | Deletion | Full workflow + manifest vault + verification | Bhushan |
| 11 | Calibration | Snapshots, thresholds, startup validation | Prachi + Dipak |
| 12 | Hardening | Failure injection suite, security tests, observability | All |

Frontend starts at slice 1 (upload + status views) against generated types, not at slice 9 — Aakanksha shouldn't be idle for six slices, and early UI contact surfaces API problems while they're cheap to fix.

## Sequencing

| Weeks | Focus |
|---|---|
| 1 | Slice 0. **Tier B collection begins. Colab fine-tune pilot runs.** License audits on RxHandBD / Bangladesh set / HF 69K |
| 2 | Slices 1–2. Fence tests are the gate — do not proceed until they pass. Annotation continues |
| 3–4 | Slices 3–5. First real OCR output. Annotation continues |
| 5 | Slice 6. Medication Master seeded from CDSCO. Tier B first batch annotated |
| 6 | Slices 7–8. First end-to-end structured report |
| 7 | Slice 9 complete. **E1 benchmark on Tier B** |
| 8 | Slices 10–11. Model selected, thresholds set from measurement |
| 9–10 | Slice 12. Full failure injection. Report writing |

Weeks 9–10 have deliberate slack. Tier B annotation will overrun — expert review time is the least compressible thing here.

## Dependencies

```
0 → 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 → 9
                              ↓
Tier B ─────────────────────→ E1 → 11
1 ───────────────────────────→ 10
```

Slice 11 (calibration) cannot start before E1, and E1 cannot start before Tier B. That chain is the schedule's real critical path — not the code.

## Definition of done, per slice

- Tests at every applicable layer
- OpenAPI updated; contract tests pass
- Migration with tested downgrade
- Failure paths tested, not just the happy path
- Docs updated if a contract changed
- CI green, review approved (two for safety/auth/retention/migrations)

## Scope cuts, pre-agreed

If the schedule slips, cut in this order — **breadth first, never engineering quality**:

1. Slice 9 richness → minimal functional review UI
2. `EVIDENCE_LOOKUP` / `ADVERSE_EFFECT` → ship `DUPLICATE_MEDICATION` only (it's local, always available, and demonstrates the full pipeline)
3. Multi-strategy normalization → exact + fuzzy only
4. TIFF/PDF support → images only
5. Slice 10 → tombstone + storage delete, manifest vault deferred

**Never cut:** fence tests, uncertainty propagation, NOT_EVALUATED semantics, provenance, calibration-before-promotion, the no-PHI-in-logs whitelist. These are what make the project defensible; a demo without them is the "connected some APIs and called it AI" outcome.

## Risks

| Risk | Impact | Response |
|---|---|---|
| Tier B annotation overruns | Blocks E1, 11, all metrics | Start week 1; 200 is the floor, not the target |
| Colab limits block fine-tuning | ML plan changes | Week-1 pilot; fallback is zero-shot + rule-based post-correction |
| Handwriting accuracy too low to demo | Weak demo | Report honestly with CIs; the engineering is the deliverable, not the accuracy number |
| CDSCO parsing harder than expected | Delays slice 6 | Timebox; fall back to a smaller expert-curated seed set |
| Four people, one integration point | Merge pain | Short branches, contract-first, CI gates |

The third risk deserves a direct word: if handwriting recognition lands at a mediocre number, that is a legitimate result reported with confidence intervals — not a failure to hide. A project that honestly measures a hard problem is stronger than one that quietly reports a number from a favorable test set.