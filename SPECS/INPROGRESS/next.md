# Next Task: PH2-T2 Add Classification And Freshness Heuristics

**Priority:** P0
**Phase:** Phase 2: Build Catalog Layer
**Effort:** Medium
**Dependencies:** PH2-T1
**Status:** Selected

## Description

Add catalog-level document classification and freshness heuristics so later retrieval stages can prefer task artifacts, down-rank noisy archive summaries, and avoid selecting stale planning documents by default. This task extends the existing catalog builder without introducing CLI surface yet.

## Next Step

Run PLAN for `PH2-T2` and define the classification labels, ranking defaults, and freshness precedence rules to implement in the catalog builder.

## Recently Archived

- 2026-03-11 — `PH2-T1` archived to `SPECS/ARCHIVE/PH2-T1_Implement_Catalog_Schema_And_Builder/` with verdict `PASS`.
- 2026-03-11 — `TASK_ARCHIVE_Indexing_Summary.md` moved to `SPECS/ARCHIVE/_Historical/` after documenting the completed LM Studio indexing run for `ISOInspector/DOCS/TASK_ARCHIVE`.

## Suggested Next Tasks

- `PH2-T3` — Build Catalog CLI
- `PH3-T1` — Define Retrieval Result Schema
- `PH3-T2` — Implement Candidate Selection
