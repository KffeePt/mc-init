# 2026-05-23 — Approved dedup + rebuildable venv cleanup

## When this applies

Use this pattern after a prior dry-run has already identified exact-hash duplicate archives and rebuildable Python virtual environments, and Xan has explicitly approved cleanup.

## Durable lessons

- Treat deletion as a manifest-driven execution, not an ad-hoc `rm` pass.
- Re-hash duplicate archives immediately before deletion. The old scan is evidence, not a warrant.
- Retain the survivor copy in the semantically preferred/organized project location, then verify each survivor exists after deletion.
- Python venv deletion is acceptable only when dependency manifests exist nearby (`requirements*.txt`, `pyproject.toml`, lock files, environment files, etc.) and the venv is not the only record of the environment.
- Keep dataset/archive deletion and venv deletion as separate manifest sections so reclaimed space and risk can be reported separately.
- Write both execution results and verification output as artifacts: CSV/JSON for machine audit, Markdown for the human summary.
- Final report should state: targets deleted, errors, skipped, reclaimed GiB by class, survivor verification count, deleted-target absence count, and remaining work.

## Execution pattern

1. Load the approved deletion manifest.
2. For duplicate archives:
   - Recompute cryptographic hashes for delete target and survivor.
   - Delete only if hashes still match and survivor exists.
   - Log mismatch/source-missing/survivor-missing as skip, not failure-to-hide.
3. For venvs:
   - Confirm path is a venv-like directory, not a source/project root.
   - Confirm rebuild manifests exist.
   - Delete the venv folder only, not adjacent project files.
4. Verify:
   - Deleted targets absent.
   - Survivor archives present.
   - Approved venv paths absent.
   - No errors/skips unless explicitly reported.
5. Report compactly in chat and put full detail in `Documents/Hermes/Artifacts/...`.

## Pitfalls

- Do not delete based solely on filename similarity or old duplicate reports.
- Do not treat `.venv`/`venv` as disposable if there is no reproducible dependency manifest.
- Do not collapse all reclaimed space into one number; Xan needs to know which class produced the savings.
- Do not say “none remaining” unless the approved cleanup scope is actually complete; carry unrelated remaining work separately if present.
