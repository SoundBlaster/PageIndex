# PH3-T3 — Implement Local Tree Search

**Task ID:** PH3-T3
**Phase:** Phase 3: Build Retrieval CLI
**Priority:** P0
**Dependencies:** PH3-T1, PH3-T2
**Status:** Planned

## Objective Summary

Implement the LM-driven node-selection step that runs after candidate documents have already been narrowed by `PH3-T2`. The current ISOInspector corpus mostly contains structure JSON with titles, summaries, and line numbers but no raw node text, so the tree-search stage must operate over those structural fields first and normalize its output into the shared retrieval schema without inventing a second result format.

This task should produce a retrieval core that accepts bounded candidate documents, loads their structure JSON files, asks a local OpenAI-compatible model to choose relevant node IDs, and returns aggregated node-level results plus machine-readable errors when any document cannot be searched cleanly.

## Deliverables

1. A local tree-search module under `pageindex/` that:
   - loads candidate structure JSON files from disk
   - flattens nodes into prompt-ready search entries with node ID, title, summary, and line number
   - queries a local OpenAI-compatible model for relevant nodes per document
   - normalizes selected nodes into `RetrievalNode` results
2. Explicit machine-readable errors for:
   - structure payload load failures
   - invalid LM responses
   - LM request failures
3. Tests covering successful node selection, optional reasoning, and failure paths.

## Acceptance Criteria

- Retrieval returns source path, output path, node ID, title, summary when available, and line number when available.
- Reasoning output is optional and off by default.
- LM failures return explicit JSON errors rather than partial unstructured output.
- The tree-search core can operate directly on the bounded candidate set returned by `PH3-T2`.

## Test-First Plan

Before implementation, add tests for:

1. Successful node selection from a flattened structure payload with summaries and line numbers.
2. Optional reasoning propagation into `RetrievalNode` only when explicitly requested.
3. Invalid LM JSON responses producing `invalid_lm_response` errors.
4. Structure payload load failures producing explicit machine-readable errors without crashing the whole retrieval result.

## Execution Plan

### Phase 1: Search Contract
- Define the search entry points and node-flattening helpers.
- Keep the model call injectable so unit tests do not depend on LM Studio availability.

### Phase 2: Normalization
- Build prompt payloads from candidate structures using only stable structural fields.
- Parse LM output into normalized selected nodes and selected documents.
- Surface per-document errors through `RetrievalError` instead of partial raw responses.

### Phase 3: Verification
- Add focused pytest coverage for success and error cases.
- Run repository validation commands plus task-local coverage.
- Write `SPECS/INPROGRESS/PH3-T3_Validation_Report.md` with verdict and command outcomes.

## Decision Points And Constraints

- Do not add the public CLI surface yet; `PH3-T4` will wrap the retrieval core.
- Keep prompts deterministic and compact because candidate selection already bounds the document set.
- Prefer structural evidence already present in the indexed JSON over assumptions about raw text availability.

---
**Archived:** 2026-03-12
**Verdict:** PASS
