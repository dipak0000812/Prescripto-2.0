You are fixing an EXISTING codebase (Prescripto AI 2.0). You are NOT adding features.

1. SCOPE. Change only what the task names. No refactors, renames, formatting-only
   edits, new abstractions, or new dependencies unless the task lists them.
2. EVIDENCE FIRST. Before editing, open each named file and quote the exact lines
   (file:line) you will change. If a named function/line does not exist as described,
   STOP and report. Do not guess or "find something similar".
3. NO INVENTED APIs. For any third-party call you are not 100% sure of (PaddleOCR,
   boto3, SQLAlchemy, Alembic, FastAPI), read the installed package source or its
   docs first. If you cannot verify it, say so and leave a marked question instead of code.
4. TESTS. Never weaken, delete, skip, xfail, or loosen existing assertions to get
   green. Only modify tests the task names. Every fix gets a regression test that
   FAILS before the fix and PASSES after; show both runs.
5. RUN, DON'T CLAIM. Run the task's verification commands and paste the real output.
   If you could not run something, write "NOT RUN" and why.
6. NO PLACEHOLDERS. No TODO, pass-bodies, fake data, or mocks in production code.
   No `except Exception: pass`. No silencing errors.
7. PRESERVE BEHAVIOR outside the task. Change a public response shape or DB schema
   only if the task says so; then update OPENAPI.yaml (parity test must pass) and
   add an Alembic migration (upgrade AND downgrade).
8. PHI SAFETY. Never log request bodies, filenames, patient references, extracted
   text, or raw exception messages that may contain them.
9. ONE TASK = ONE COMMIT (Conventional Commits). Do not bundle tasks.
10. OUTPUT FORMAT per task: (a) findings with file:line, (b) plan, (c) diff,
    (d) test output before/after, (e) risks and anything NOT verified.
11. If code and docs disagree, code wins unless the task says otherwise.
    Report the disagreement.
