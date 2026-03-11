# PH3-T2 — Implement Candidate Selection

**Task ID:** PH3-T2
**Phase:** Phase 3: Build Retrieval CLI
**Priority:** P0
**Dependencies:** PH2-T1, PH2-T2, PH3-T1
**Status:** Planned

## Objective Summary

Add the deterministic first-stage narrowing pass that sits between the catalog artifact and later LM-driven tree search. The selector must take a query plus optional operator filters, score catalog records using cheap lexical and metadata signals, and return a bounded `top-k` document list that future retrieval stages can consume directly through the shared retrieval schema.

The target corpus is `results/isoinspector_task_archive_lmstudio`, where catalog records already carry document type, freshness, and path metadata. The selector must exploit those fields to keep false positives down on archive-heavy corpora without requiring model calls or reopening source Markdown files.

## Deliverables

1. A retrieval candidate-selection module under `pageindex/` that:
   - loads catalog artifacts from disk or accepts in-memory catalog payloads
   - filters by document type and path prefix
   - scores lexical overlap between the query and catalog metadata
   - applies type priority and freshness as first-class ranking signals
2. Deterministic conversion from catalog records into `RetrievalDocument` candidates.
3. Default `top-k` behavior set to `7`, with explicit override support.
4. Automated tests covering filtering, ranking, default exclusion of `next_tasks`, and deterministic bounded output.

## Acceptance Criteria

- Candidate selection supports lexical, path-prefix, and document-type filtering.
- Ranking uses freshness and document type as first-class signals.
- Default `top-k` is `7` and is tuned for low false positives over maximal recall.
- Sample ISOInspector-style queries reduce the corpus to a bounded candidate set before LM calls.
- Selection output is deterministic and serializes cleanly into the retrieval schema.

## Test-First Plan

Before implementation, add tests for:

1. Lexical matching against document names, relative paths, and directories.
2. Path-prefix and document-type filtering, including explicit inclusion of `next_tasks` only when requested.
3. Ranking behavior that prefers `task` over `blocked` over `summary` when lexical relevance is comparable.
4. Freshness tie-breaking using the normalized catalog freshness timestamp.
5. Default bounded output of `7` candidates unless a different `top_k` is provided.

## Execution Plan

### Phase 1: Selector Contract
- Define selector input parameters and document conversion helpers.
- Keep the surface transport-neutral so the future CLI and local API can call the same functions.

### Phase 2: Ranking
- Tokenize queries and candidate metadata with simple deterministic normalization.
- Combine lexical overlap with catalog-provided type priority and freshness into a stable ranking score.
- Exclude or strongly de-prioritize `next_tasks` records by default.

### Phase 3: Verification
- Add focused pytest coverage for candidate ranking and filtering.
- Run repository validation commands plus task-local coverage.
- Write `SPECS/INPROGRESS/PH3-T2_Validation_Report.md` with verdict and command outcomes.

## Decision Points And Constraints

- Do not call any language model in this task.
- Keep scoring explainable enough that the later tree-search stage can surface candidate provenance if needed.
- Avoid tying the selector to one corpus layout beyond the catalog fields already defined in `PH2-T1` and `PH2-T2`.

---
**Archived:** 2026-03-12
**Verdict:** PASS
