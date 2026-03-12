# PH4-T2 — Implement Answer-Ready Extraction Mode

**Task ID:** PH4-T2
**Phase:** Phase 4: Build Context Extraction
**Priority:** P1
**Dependencies:** PH3-T4, PH4-T1
**Status:** Planned

## Objective Summary

Add an answer-ready retrieval mode that converts selected nodes into compact evidence blocks when indexed node text is available. The mode must reuse the existing `RetrievalResult` schema by filling `extracted_context`, keep the regular retrieval fields intact, and fail explicitly with machine-readable errors when the current index lacks node text.

This task should extend the current retrieval flow rather than creating a second answer-only output shape. The CLI and local tool contract should expose one opt-in flag for the new mode.

## Deliverables

1. Retrieval/context helpers that:
   - convert resolved node contexts into `ExtractedContext` records with citations
   - preserve `selected_nodes` while populating `extracted_context`
   - return explicit `node_text_missing` errors when answer-ready mode is requested against text-absent indexes
2. A CLI flag and local tool-contract field that enable answer-ready mode without changing the base JSON schema.
3. Focused tests covering:
   - answer-ready success when node text exists
   - explicit failure when node text is absent
   - CLI and tool-contract exposure of the new mode

## Acceptance Criteria

- Retrieval can emit answer-ready evidence blocks with citations when node text is available.
- The command fails explicitly when answer-ready mode requires raw text that is absent from the index.
- The output remains deterministic JSON.

## Test-First Plan

Before implementation, add or update tests for:

1. Context-to-`ExtractedContext` conversion with deterministic citation formatting.
2. `search_catalog(..., answer_ready=True)` success over a text-present structure payload.
3. `search_catalog(..., answer_ready=True)` failure over a text-absent structure payload with explicit `node_text_missing` errors and no partial answer-ready output.
4. CLI and tool-contract exposure of the `answer_ready` option.

## Execution Plan

### Phase 1: Context Extraction
- Add one helper that converts selected retrieval nodes into `ExtractedContext` records through the existing context layer.
- Keep citation formatting deterministic and derived from source path plus line number when available.

### Phase 2: Retrieval And Interface Wiring
- Extend `pageindex/retrieval.py`, `pageindex/search_cli.py`, and `pageindex/tool_contract.py` with an opt-in answer-ready mode.
- Preserve the existing retrieval result shape while populating `extracted_context`.

### Phase 3: Verification
- Add focused tests for the new success and failure paths.
- Run repository validation commands and task-local coverage.
- Write `SPECS/INPROGRESS/PH4-T2_Validation_Report.md` with verdict and command outcomes.

## Decision Points And Constraints

- Do not require node text for the default retrieval mode.
- Do not return partial answer-ready context when required node text is missing; fail explicitly in the `errors` payload instead.
- Keep the answer-ready option compatible with the existing local tool contract so `PH5-T2` can wrap it directly.

---
**Archived:** 2026-03-12
**Verdict:** PASS
