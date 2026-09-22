# REFERENCES.md

Verification status is recorded per entry. "Verified" means read at the primary source on the stated date, not inferred.

## Knowledge sources

| Source | URL | Verified | Concept used | Adopted? |
|---|---|---|---|---|
| NLM RxNorm docs | https://www.nlm.nih.gov/research/umls/rxnorm/docs/ | 2026-09 | NLM states RxNorm is US-centric with few if any non-US drugs | ✅ Adopted as optional CUI enrichment only. **Rejected as sole ontology** — this statement is the direct basis for ADR-07 |
| openFDA disclaimer | https://open.fda.gov/apis/disclaimer/ | 2026-09 | Not for clinical decision-making; results unvalidated | ✅ Adopted as labeling/AE evidence, explicitly not clinical truth |
| SIDER 4.1 | http://sideeffects.embl.de/ | 2026-09 | CC BY-NC-SA 4.0 | ⚠️ `RESEARCH_ONLY`; excluded from commercial builds (ADR-14) |
| DrugBank terms | https://go.drugbank.com | 2026-09 | Free academic tier scoped to non-clinical research/education | ❌ Not used at runtime — our use case isn't clearly covered |
| PhysioNet / MIMIC-IV | https://physionet.org/content/mimiciv/ | 2026-09 | Credentialed access, CITI training, per-person DUA; EHR tables not prescription images | ❌ Rejected — wrong data type, high access overhead, zero pipeline benefit |
| CDSCO | Indian regulatory listings | ⚠️ Pending | Approved formulations, FDCs | Medication Master seed — **reuse terms need legal review** |

## Models

| Model | Source | License verified | Adopted? |
|---|---|---|---|
| PP-OCRv6 | arXiv 2606.13108; PaddleOCR docs | Apache 2.0 ✅ | ✅ Detection locked; recognition as baseline floor |
| TrOCR handwritten | Microsoft / HF model cards | MIT ✅ (base) | Candidate, pending E1 |
| TrOCR prescription fine-tune | HF model card | ⚠️ Unverified | Candidate; sub-2% CER is the author's own test set, not ours |
| PaddleOCR-VL-1.6 | PaddleOCR | ⚠️ Verify | Deferred (D-04) |
| Qwen2.5-VL | Qwen / HF | ⚠️ **Varies by checkpoint** — some Apache 2.0, some Qwen Research License | Deferred. Never assume family-wide licensing |
| BioBERT / Bio_ClinicalBERT | Lee et al. 2020; Alsentzer et al. 2019 | Apache 2.0 / open weights ✅ | Deferred (D-05) |

**Verification note:** PP-OCRv6 medium-tier aggregate figures (83.2% weighted-avg recognition, 86.2% detection Hmean) are confirmed from the technical report. The handwritten-English / printed-English split figures circulated in earlier drafts are **unverified at medium tier** — only the tiny-tier row was confirmable, which showed the same large handwritten-vs-printed gap. Do not cite those two specific numbers until pulled directly from Table 6.

## Datasets

| Dataset | Source | Verified | Tier |
|---|---|---|---|
| MedOCR-Vision | HF `naazimsnh02/medocr-vision` | MIT ✅; 2,462 docs | A |
| RxHandBD | Mendeley Data | ⚠️ Pending | A (candidate) |
| Bangladesh curated prescriptions | Mendeley Data | ⚠️ Pending | A (candidate) |
| HF Indian medicine names (~69K) | HuggingFace | ⚠️ Pending | A — fuzzy dictionary only |

## Papers

- Lee et al. (2020). *BioBERT: a pre-trained biomedical language representation model.* Bioinformatics 36(4). https://doi.org/10.1093/bioinformatics/btz682 — cited in the project abstract; informs the deferred NER stage
- Alsentzer et al. (2019). *Publicly Available Clinical BERT Embeddings.* — weights published openly despite MIMIC-III training; weights ≠ data access

## Engineering references

| Reference | URL | Concept | Applied? |
|---|---|---|---|
| System Design Primer | https://github.com/donnemartin/system-design-primer | Sync/async boundaries, failure-first design | ✅ Async pipeline, degradation matrix |
| PostgreSQL explicit locking | https://www.postgresql.org/docs/current/explicit-locking.html | `FOR UPDATE SKIP LOCKED` | ✅ ADR-04, job queue |
| Fencing tokens (Kleppmann, *DDIA*) | — | Lease + monotonic token prevents stale-worker writes | ✅ Arch §7. Renders "exactly-once" honest as effectively-once |
| FastAPI docs | https://fastapi.tiangolo.com/ | OpenAPI generation from Pydantic | ✅ ADR-05 |
| MinIO docs | https://min.io/docs/ | S3-compatible dev storage | ✅ ADR-03 |
| Full Stack Deep Learning | https://fullstackdeeplearning.com | Model versioning; don't build infra you can't justify | ✅ Reinforces deferral discipline |
| Standard README | https://github.com/RichardLitt/standard-readme | README structure | ✅ |
| DPDPA 2023 + Rules 2025 | MeitY | Erasure, minimization, purpose limitation | ✅ Arch §2, §17 |

**Rejected without adoption:** Kafka, Kubernetes, vector databases, Redis/Celery, service mesh, microservices. Each has a measured reversal trigger in Arch §20; none has fired. Listed here so it's clear they were considered and declined, not overlooked.

## Outstanding verification

1. RxHandBD, Bangladesh dataset, HF 69K — licenses and de-identification audits
2. CDSCO reuse terms for a derived Medication Master — legal review, not an engineering call
3. TrOCR prescription fine-tune — license and CER claim at the primary source
4. PP-OCRv6 Table 6 medium-tier handwritten/printed English split
5. Qwen2.5-VL — exact checkpoint license, if D-04 ever proceeds