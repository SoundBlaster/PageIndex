# Next Task: PH3-T2 — Implement Candidate Selection

**Task ID:** PH3-T2
**Phase:** Phase 3: Build Retrieval CLI
**Effort:** Medium
**Dependencies:** PH2-T1, PH2-T2, PH3-T1
**Status:** Selected

## Description

Implement the first-stage retrieval narrowing pass over `catalog.json`. Candidate selection must use cheap deterministic signals only: lexical matching, optional path-prefix filtering, optional document-type filtering, and ranking based on document type plus freshness so the later LM-driven tree search operates on a bounded and relevant candidate set.

## Next Step

Run PLAN and EXECUTE for `PH3-T2`, then archive the task and review the changes before proceeding to `PH3-T3`.

## Recently Archived

- 2026-03-11 — `PH2-T1` archived to `SPECS/ARCHIVE/PH2-T1_Implement_Catalog_Schema_And_Builder/` with verdict `PASS`.
- 2026-03-11 — `PH2-T2` archived to `SPECS/ARCHIVE/PH2-T2_Add_Classification_And_Freshness_Heuristics/` with verdict `PASS`.
- 2026-03-11 — `PH2-T3` archived to `SPECS/ARCHIVE/PH2-T3_Build_Catalog_CLI/` with verdict `PASS`.
- 2026-03-11 — `PH3-T1` archived to `SPECS/ARCHIVE/PH3-T1_Define_Retrieval_Result_Schema/` with verdict `PASS`.
- 2026-03-11 — `TASK_ARCHIVE_Indexing_Summary.md` moved to `SPECS/ARCHIVE/_Historical/` after documenting the completed LM Studio indexing run for `ISOInspector/DOCS/TASK_ARCHIVE`.

## Suggested Next Tasks

- `PH3-T3` — Implement Local Tree Search
- `PH3-T4` — Build Search CLI Wrapper
- `PH4-T1` — Implement Node Lookup Helpers
