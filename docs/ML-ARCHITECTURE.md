# ML-ARCHITECTURE.md

ML system design and the boundary between learned and deterministic components. Stage I/O in ML-PIPELINES.md; per-model specs in MODEL-SPECIFICATIONS.md; metrics in EVALUATION-PLAN.md.

## What is learned and what is not

| Stage | Learned? | Why |
|---|---|---|
| Quality check | No | Laplacian variance, histogram spread — deterministic, debuggable |
| Text detection | **Yes** | PP-OCRv6 detector |
| Recognition | **Yes** | The one genuinely hard perception problem |
| Structured extraction | No | Regex + abbreviation lexicon |
| Normalization | No | Fuzzy/phonetic string matching against the Master |
| Safety screening | No | Deterministic rules over canonical entities |
| Report assembly | No | Rule-based routing |

Two learned stages out of eight. That ratio is deliberate.

**Why extraction is rules, not a model:** a regex that mis-parses `500mg` is inspectable, fixable in minutes, and fails the same way every time. A model that mis-parses it fails unpredictably, needs retraining to fix, and needs labeled data to even diagnose. For dosage parsing — where the error classes are `mg→mcg` and `OD→QID` — deterministic and auditable beats marginally more accurate. This is also why the dedicated NER stage is deferred rather than assumed: it must *prove* it beats rules (E5), not merely sound more sophisticated.

**Why safety is rules, not a model:** a finding must be traceable to a source and a version. A model-generated finding cannot carry provenance in the sense SR-06 requires. The safety engine is a pure domain component with zero ML dependency — which is also what makes it testable without any model loaded.

## Confidence architecture

The critical design point, and the place where this system most differs from a naive pipeline.

```
raw_score (model-native, incomparable across architectures)
   → calibration snapshot (per model_version)
   → calibrated_confidence ∈ [0,1], interpretable as P(field correct)
   → FieldState, bucketed against that version's review_threshold
   → routing decision
```

Raw scores are not probabilities. A TrOCR beam-search score and a PP-OCR CTC confidence of "0.85" mean different things, and neither means "85% likely correct." Thresholding raw scores directly produces a system whose review routing is arbitrary — and arbitrary routing silently breaks the human-in-the-loop guarantee that the entire safety argument rests on.

So: **no model runs without a calibration snapshot.** Enforced at worker startup, not by convention.

### What is never done

- No averaging of confidences across layers. OCR confidence and evidence strength are different quantities; combining them produces a number that means nothing.
- No single overall analysis confidence (PRD §17.1). Five CLEAR fields and one AMBIGUOUS field is not "96% confident" — it's five of one thing and one of another, reported as such.
- No confidence propagation by arithmetic. Propagation is by **state**: AMBIGUOUS in → AMBIGUOUS out, enforced by `ExtractedField.propagate()` raising rather than degrading silently.

## Uncertainty as a type

```python
@dataclass(frozen=True)
class ExtractedField(Generic[T]):
    value: Optional[T]
    state: FieldState
    confidence: float
    raw_text: str

    def propagate(self) -> "ExtractedField[T]":
        if self.state is FieldState.UNREADABLE:
            raise UncertaintyPropagationError(...)
        if self.state is not FieldState.CLEAR:
            return ExtractedField(self.value, FieldState.AMBIGUOUS, self.confidence, self.raw_text)
        return self
```

Frozen, generic, and it **raises** rather than returning a degraded value. A bug that would have let UNREADABLE text reach the safety engine becomes a crash in a test, not a silently wrong finding in production.

`mypy --strict` on `domain/` is load-bearing here. Without it these annotations are documentation, and the invariant reduces to developer discipline.

## Model runtime abstraction

`ModelRuntime` (Arch §11) isolates model choice behind `detect_regions` / `recognize_line` / `model_version_id`. Swapping a model is a config change plus a worker restart — which is exactly what E1 needs, since model selection is unresolved until Tier B exists.

Startup validation refuses to boot on: unregistered model version, missing calibration snapshot, checkpoint hash mismatch, or load failure. Four gates, all safety-relevant, none skippable.

## VLM verification — deferred, and why

The architecture reserves the shape (low-confidence branch → VLM verifier) but does not build it in V1.

PP-OCRv6's own hallucination benchmark indicates specialized OCR stays better grounded to image content than large VLMs. In this domain a hallucinated drug name is a safety incident, not a cosmetic defect. So the VLM must earn the stage by measurably reducing **critical error rate** — not CER — in E4. If it improves transcription while missing unit errors, it has added latency and no safety value, and it gets cut regardless of build cost already spent.

## LLM — off

`LLM_ENABLED = false` (ADR-09). The structured report is the complete V1 product.

When it returns (D-01), its authority is bounded by construction: frozen `ExplanationContext` in, schema-validated JSON out, finding UUIDs cross-checked against pre-existing findings, clearance-phrase rejection, and discard-on-failure. It explains findings; it cannot create, alter, or clear them.

Worth stating plainly: the V1 pipeline has **no stochastic stage**. Same inputs, same pins, same output. That reproducibility disappears the day the LLM is enabled — a known and accepted future tradeoff, flagged now rather than discovered later.

## Resource profile

| Stage | Cost | Note |
|---|---|---|
| Detection | Moderate | Once per document |
| Recognition | **Dominant** | 200–800 ms × 5–20 lines, CPU |
| Everything else | Negligible | Rules and string matching |

Optimization effort belongs in recognition or nowhere. Free-tier constraint means TrOCR-large feasibility is genuinely uncertain — the week-1 Colab pilot decides whether fine-tuning is in the plan at all, or whether the plan is zero-shot checkpoints plus rule-based post-correction.

## Critical path

Nothing here resolves without Tier B. Model selection, thresholds, calibration, and every reported metric depend on a dataset that does not yet exist. Collection and expert annotation are the schedule's real constraint — not model training.