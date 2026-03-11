# Next Task: PH2-T3 Build Catalog CLI

**Priority:** P0
**Phase:** Phase 2: Build Catalog Layer
**Effort:** Medium
**Dependencies:** PH2-T1, PH2-T2
**Status:** Selected

## Description

Expose the catalog builder through a stable command-line interface that scans an output root and writes a separate `catalog.json` artifact. The CLI should reuse the existing builder logic, support explicit output destinations, and work against the real ISOInspector output root without manual edits.

## Next Step

Run PLAN for `PH2-T3` and define the CLI contract, default output path, and verification steps for synthetic and real output roots.

## Recently Archived

- 2026-03-11 — `PH2-T1` archived to `SPECS/ARCHIVE/PH2-T1_Implement_Catalog_Schema_And_Builder/` with verdict `PASS`.
- 2026-03-11 — `PH2-T2` archived to `SPECS/ARCHIVE/PH2-T2_Add_Classification_And_Freshness_Heuristics/` with verdict `PASS`.
- 2026-03-11 — `TASK_ARCHIVE_Indexing_Summary.md` moved to `SPECS/ARCHIVE/_Historical/` after documenting the completed LM Studio indexing run for `ISOInspector/DOCS/TASK_ARCHIVE`.

## Suggested Next Tasks

- `PH3-T1` — Define Retrieval Result Schema
- `PH3-T2` — Implement Candidate Selection
- `PH3-T3` — Implement Local Tree Search
