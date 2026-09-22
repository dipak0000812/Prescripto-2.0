# CI-CD.md

## Repository

Single repo, no submodules.

```
prescripto/          backend + ML (see Arch §6)
web/                 React/Vite client, OpenAPI-generated types
docs/                all engineering documentation
scripts/             seeds, benchmarks, manifest re-application
tests/               unit · integration · contract · failure · security
migrations/          Alembic
docker/              Dockerfile, compose files
.github/workflows/   CI
```

Frontend and backend in one repo because the OpenAPI contract couples them — split repos make contract drift possible between merges, which is exactly the failure this architecture is built to prevent.

## Branching

`main` always deployable. Feature branches `feat/`, `fix/`, `docs/`, `chore/`. Squash merge. No direct pushes to `main`.

Short-lived branches only — a vertical slice (IMPLEMENTATION-PLAN.md) should merge within days, not weeks.

## Commits

Conventional Commits: `type(scope): subject`. Scopes: `api`, `domain`, `pipeline`, `ml`, `db`, `auth`, `web`, `docs`, `ci`.

## PR gates

Every PR, blocking:

| Check | Tool | Fails on |
|---|---|---|
| Format | `ruff format --check` | Any diff |
| Lint | `ruff check` | Any error |
| Types | `mypy --strict` on `domain/`, standard elsewhere | Any error |
| Unit tests | pytest | Any failure |
| Integration | pytest + testcontainers | Any failure |
| Contract | Response ↔ `/openapi.json` | Any divergence |
| Failure injection | pytest | Any failure |
| Security tests | pytest | Any failure |
| Coverage | `domain/` ≥90%, overall ≥70% | Below threshold |
| **Enum drift** | custom script | Python enum ≠ DB CHECK ≠ OpenAPI enum |
| **Banned patterns** | custom script | `"latest"` in model config; `localStorage` in artifacts; hardcoded secrets |
| Migration downgrade | `alembic upgrade head && downgrade -1 && upgrade head` | Any failure |
| Dependency audit | `pip-audit`, `npm audit` | High/critical |
| Secret scan | `gitleaks` | Any hit |
| Frontend | `tsc --noEmit`, `eslint`, `vitest` | Any failure |

`mypy --strict` on `domain/` is load-bearing, not hygiene: the uncertainty-propagation invariants are encoded as types, and without strict mode Python annotations are decoration.

**Enum drift** gets a dedicated check because the same enum lives in three places (Python, DB CHECK, OpenAPI). Review catches this inconsistently; a script catches it every time.

## ML-specific gates

| Change touches | Additional required |
|---|---|
| `ml/`, `pipeline/` | Golden-set benchmark (~20 prescriptions), must not regress |
| Model version bump | Full Tier B benchmark + calibration snapshot + reviewer sign-off |
| Extraction rules | Golden set + per-field accuracy report |

Golden set runs in CI (fast). Full Tier B is manual and gates promotion, not merge.

## Review requirements

One approving review minimum. Two for anything touching: `domain/safety/`, `domain/uncertainty/`, `retention/`, `auth/`, or any migration.

The double-review set is exactly the code where a subtle error is silent: a broken safety invariant produces plausible output, a broken deletion produces a success message, a broken auth check produces a working app.

### Reviewer checklist
- Does this let uncertainty round up? (`AMBIGUOUS`→`CLEAR`, `NOT_EVALUATED`→absent)
- Can a finding be surfaced without full provenance?
- New endpoint: in `openapi.yaml` and the contract matrix?
- New enum value: in all three places?
- New log field: on the whitelist?
- Migration: tested `downgrade()`?
- New dependency: license verified at primary source?
- Model reference: pinned version, never `"latest"`?

## Pipelines

**PR** — all gates above, ~5 min target.
**Merge to main** — gates + build image + tag `main-{sha}` + push.
**Release tag `v*`** — build + tag semver + generate changelog + publish `openapi.yaml` artifact.

Deployment stays manual in V1. Automated deploy to a demo environment is post-V1 and not worth the setup cost at this stage.

## Automated model deployment

**Not implemented.** Requires regression gates, which require measured baseline variance on Tier B, which doesn't exist yet (PRD §12.6). Model promotion is: benchmark → human review → config change → worker restart.

## Secrets in CI

GitHub Actions secrets. Never echoed. Integration tests use ephemeral testcontainer credentials, never staging ones.