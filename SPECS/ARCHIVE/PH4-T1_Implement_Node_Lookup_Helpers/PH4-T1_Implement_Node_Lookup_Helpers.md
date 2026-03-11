# PH4-T1 — Implement Node Lookup Helpers

**Task ID:** PH4-T1
**Phase:** Phase 4: Build Context Extraction
**Priority:** P1
**Dependencies:** PH3-T1
**Status:** Planned

## Objective Summary

Introduce a reusable context lookup layer that resolves retrieved node IDs back to canonical metadata from the indexed structure JSON outputs. The helper must work with the current ISOInspector structure-only artifacts, expose title/summary/path/line metadata without depending on raw node text, and make missing text availability explicit so the later answer-ready extraction mode can fail predictably instead of silently degrading.

The implementation should avoid duplicating node-parsing logic across retrieval and context workflows. `PH4-T1` should establish one canonical structure traversal path that both the tree-search layer and future extraction logic can reuse.

## Deliverables

1. A new `pageindex/context.py` module that:
   - loads indexed structure payloads
   - resolves a node ID to canonical metadata
   - optionally reports node text availability and missing-text errors
2. Lookup helpers that work directly with retrieval results so later phases can enrich `selected_nodes` without re-deriving document metadata elsewhere.
3. Focused tests covering:
   - metadata lookup for known node IDs
   - text-present lookup
   - text-absent lookup with explicit error reporting
   - reuse of the lookup helper from the retrieval path

## Acceptance Criteria

- Node lookup returns title, summary, source path, output path, and line number when present.
- Node lookup works against the current text-absent ISOInspector outputs.
- Missing node text is reported explicitly instead of failing silently.

## Test-First Plan

Before implementation, add or update tests for:

1. Lookup of a nested node from a structure payload with `summary`, `prefix_summary`, and `line_num`.
2. Lookup of a selected retrieval node against a text-present structure payload, producing extracted text metadata without errors.
3. Lookup of a selected retrieval node against a text-absent structure payload, returning metadata plus an explicit `node_text_missing` error when text is required.
4. Retrieval integration continuing to return the same selected node metadata after lookup responsibilities move into the new context layer.

## Execution Plan

### Phase 1: Context API
- Add a small data model for resolved node context and helper functions to load/search structure JSON.
- Normalize summary and line-number fields so retrieval and extraction share the same lookup semantics.

### Phase 2: Retrieval Integration
- Reuse the context lookup helper from `pageindex/local_tree_search.py` when converting LM-selected node IDs into `RetrievalNode` objects.
- Preserve the existing retrieval result schema.

### Phase 3: Verification
- Add targeted context-layer tests plus regression coverage for retrieval.
- Run repository validation commands and task-local coverage.
- Write `SPECS/INPROGRESS/PH4-T1_Validation_Report.md` with verdict and command outcomes.

## Decision Points And Constraints

- Keep answer-ready evidence packaging out of this task; only establish the lookup primitives needed for it.
- Treat missing text as an explicit machine-readable condition, not an exception that aborts metadata lookup.
- Prefer helpers that accept existing retrieval records and output paths rather than introducing a second document-identification contract.

---
**Archived:** 2026-03-12
**Verdict:** PASS
