# PH1-T4 — Formalize Indexing Contract Docs And Tests

## Objective

Turn the already-implemented indexing foundation into an explicit, verifiable contract. The repository already ships recursive Markdown indexing, mirrored output paths, `manifest.json`, and `--resume`, but the operator-facing docs and automated tests do not fully describe or enforce those semantics. This task documents the contract and adds focused coverage without changing the broader retrieval architecture.

## Scope And Deliverables

Deliverables for this task:

- README updates that describe the indexing contract used by downstream catalog/retrieval code.
- Code-level contract notes in `scripts/index_markdown_directory.py` where resume and manifest behavior are defined.
- Focused automated tests for the batch indexer covering mirrored outputs, manifest statuses, failure entries, and `--resume` overwrite protection.
- A validation report capturing the quality gates and task-local coverage results.

Out of scope:

- Redesigning the manifest format.
- Changing retrieval, catalog, or local API behavior.
- Completing the broader Phase 1 tasks beyond the contract/docs/test gap targeted here.

## Success Criteria

The task is complete when all of the following are true:

- README documents `indexed`, `skipped`, and `failed` manifest statuses.
- README states that output JSON existence is the source of truth for `--resume` and that `manifest.json` is a per-run progress artifact.
- README defines named `structure`, `summary`, and `text` indexing profiles and maps them to the existing CLI flags, including guidance for enriching an existing output root with node text.
- Tests directly exercise `scripts/index_markdown_directory.py` and verify mirrored output paths, per-run manifest semantics, failure recording, and resume skip/no-overwrite behavior.

## Test-First Plan

1. Add failing tests for the batch indexer contract before changing implementation or docs.
2. Refactor the script only as needed to make it directly testable without changing CLI behavior.
3. Update README and in-code comments once the tests describe the intended behavior.
4. Run project quality gates plus task-local coverage for the modified script/tests.

## Execution Plan

### Phase 1 — Define Observable Contract

- Inspect the current script, README, PRD, and real ISOInspector manifest.
- Translate the implicit rules into explicit user-facing and code-facing contract statements.
- Keep the rules aligned with `SPECS/PRD.md`, especially the filesystem source-of-truth decision.

### Phase 2 — Add Outside-In Tests

- Write tests that drive the script through its public CLI entry behavior with a tiny temporary Markdown corpus.
- Cover:
  - mirrored `*_structure.json` paths
  - `indexed` / `skipped` / `failed` manifest entries
  - `--resume` skipping existing outputs without overwriting them
- Use minimal stubs or monkeypatching only where needed to avoid LM dependencies.

### Phase 3 — Implement And Validate

- Make the script testable with the smallest production changes required.
- Update README and inline contract notes.
- Run:
  - repository tests
  - configured compile/lint smoke checks
  - task-local coverage with threshold `>= 90%`

## Notes

- Preserve the current contract that the manifest is a progress artifact, not a database.
- Do not introduce a new indexing profile format or wrapper CLI in this task.
- If the tests reveal ambiguous resume behavior, document the current intended behavior rather than silently redefining it.

---
**Archived:** 2026-03-12
**Verdict:** PASS
