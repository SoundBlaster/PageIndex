# PH3-T4 — Build Search CLI Wrapper

**Task ID:** PH3-T4
**Phase:** Phase 3: Build Retrieval CLI
**Priority:** P0
**Dependencies:** PH3-T2, PH3-T3
**Status:** Planned

## Objective Summary

Wrap the candidate-selection and local tree-search cores behind a stable local CLI that agents can call directly. The CLI should be JSON-first, deterministic, and narrow in scope: accept a catalog artifact, apply the requested retrieval filters, optionally stop after candidate selection, and otherwise execute the full bounded retrieval flow into the shared `RetrievalResult` schema.

The wrapper must not duplicate selection or tree-search logic. Instead it should introduce a thin orchestration layer that combines the existing modules and exposes the stable command-line surface promised by the workplan.

## Deliverables

1. A retrieval orchestration module under `pageindex/` that:
   - loads a catalog artifact
   - runs candidate selection
   - optionally stops at dry-run candidate output
   - otherwise runs local tree search and returns a `RetrievalResult`
2. A CLI entry point that supports:
   - `--query`
   - `--catalog`
   - `--top-k`
   - `--type`
   - `--path-prefix`
   - `--dry-run-candidates`
   - `--with-reasoning`
3. Optional grouped-by-document output while keeping flat node results as the default mode.
4. Tests covering dry-run candidate output, full retrieval output, and grouped/reasoning serialization through the CLI surface.

## Acceptance Criteria

- CLI emits JSON by default.
- CLI supports `--query`, `--catalog`, `--top-k`, `--type`, `--path-prefix`, `--dry-run-candidates`, and `--with-reasoning`.
- CLI can optionally group results by document while keeping flat node results as the default mode.
- The wrapper reuses the retrieval cores from `PH3-T2` and `PH3-T3` instead of duplicating business logic.

## Test-First Plan

Before implementation, add tests for:

1. Dry-run candidate output that returns candidate documents without selected nodes.
2. Full retrieval output through the orchestration layer with an injected model stub.
3. CLI JSON emission with grouped-by-document output and optional reasoning.
4. Repeated `--type` filters and path-prefix filtering reaching the underlying candidate selector.

## Execution Plan

### Phase 1: Orchestration
- Build one retrieval function that composes catalog loading, candidate selection, and optional local tree search.
- Preserve the shared retrieval schema as the only output shape.

### Phase 2: CLI
- Add an argument parser and JSON output writer.
- Keep the script thin by delegating all retrieval behavior to the orchestration module.

### Phase 3: Verification
- Add focused tests for the orchestration layer and CLI entry point.
- Run repository validation commands plus task-local coverage.
- Write `SPECS/INPROGRESS/PH3-T4_Validation_Report.md` with verdict and command outcomes.

## Decision Points And Constraints

- Keep the default mode flat and machine-readable; grouped output must be opt-in.
- The CLI should remain local-only and file-based for now; API and MCP wrappers are deferred to later phases.
- Avoid adding flags that change the underlying retrieval schema contract.

---
**Archived:** 2026-03-12
**Verdict:** PASS
