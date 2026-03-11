# PH2-T2 — Add Classification And Freshness Heuristics

**Task ID:** PH2-T2
**Phase:** Phase 2: Build Catalog Layer
**Priority:** P0
**Dependencies:** PH2-T1
**Status:** Planned

## Objective Summary

Extend the catalog builder so each record carries retrieval-oriented heuristics for document type and freshness. The target corpus is a task archive with mixed planning notes, blocked work items, task summaries, and generic design documents. Candidate selection in later phases needs these heuristics available in the catalog artifact so it can rank precisely without reopening every source file during every query.

## Deliverables

1. Catalog schema updates for:
   - `document_type`
   - `ranking_signals` containing type priority, freshness timestamp, freshness source, and default exclusion/de-prioritization flags
2. Classification heuristics that map catalog records into at least:
   - `task`
   - `blocked`
   - `summary`
   - `next_tasks`
   - `generic`
3. Freshness heuristics that:
   - prefer explicit in-document dates extracted from source Markdown when available
   - fall back to filesystem metadata when no explicit date is present
4. Automated tests covering classification, date extraction precedence, and default ranking behavior for noisy planning documents.

## Acceptance Criteria

- Catalog records are classified into at least `task`, `blocked`, `summary`, `next_tasks`, and `generic`.
- Default ranking priority is `task > blocked > summary`.
- `next_tasks` records are excluded or strongly de-prioritized by default.
- Explicit in-document dates are preferred for freshness; filesystem creation metadata is the fallback.
- Heuristics are deterministic and serializable into the catalog artifact for later CLI consumers.

## Test-First Plan

Before implementation, extend pytest coverage for:

1. Filename and path patterns that distinguish archived task documents, blocked notes, summary documents, and next-task planning files.
2. Source Markdown files containing ISO-style dates and month-name dates to verify explicit-date extraction.
3. Freshness fallback behavior when no explicit date exists and only filesystem metadata is available.
4. Ranking defaults that make `task` highest priority and mark `next_tasks` as excluded or severely de-prioritized.

## Execution Plan

### Phase 1: Schema
- Add document classification and ranking fields to `CatalogRecord`.
- Keep fields deterministic and JSON-serializable for direct reuse by later retrieval commands.

### Phase 2: Heuristics
- Infer document type from source-relative path, document name, and archive conventions.
- Parse explicit dates from source Markdown text using conservative patterns.
- Normalize freshness into a single ranking timestamp plus a source marker describing whether it came from document content or filesystem metadata.

### Phase 3: Verification
- Extend `tests/test_catalog.py` with focused heuristics coverage.
- Run pytest plus the repository-configured verification commands.
- Write `SPECS/INPROGRESS/PH2-T2_Validation_Report.md` with verdict and command outcomes.

## Decision Points And Constraints

- Favor precise, transparent heuristics over broad fuzzy matching so ranking remains predictable.
- Do not introduce candidate selection or CLI behaviors yet; this task only prepares catalog metadata.
- Keep fallback logic stable when files lack explicit dates or use unfamiliar naming.

---
**Archived:** 2026-03-11
**Verdict:** PASS
