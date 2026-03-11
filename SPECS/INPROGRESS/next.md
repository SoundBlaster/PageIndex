# Next Task: PH3-T1 Define Retrieval Result Schema

**Priority:** P0
**Phase:** Phase 3: Build Retrieval CLI
**Effort:** Medium
**Dependencies:** PH2-T1
**Status:** Selected

## Description

Define the deterministic retrieval result contract that later candidate selection, tree search, and CLI wrappers will emit. The schema should default to a flat `selected_nodes` response while supporting grouped-by-document output and optional reasoning fields without changing the core field names.

## Next Step

Run PLAN for `PH3-T1` and define the retrieval result datatypes, required top-level fields, and serialization rules for grouped output and machine-readable errors.

## Recently Archived

- 2026-03-11 — `PH2-T1` archived to `SPECS/ARCHIVE/PH2-T1_Implement_Catalog_Schema_And_Builder/` with verdict `PASS`.
- 2026-03-11 — `PH2-T2` archived to `SPECS/ARCHIVE/PH2-T2_Add_Classification_And_Freshness_Heuristics/` with verdict `PASS`.
- 2026-03-11 — `PH2-T3` archived to `SPECS/ARCHIVE/PH2-T3_Build_Catalog_CLI/` with verdict `PASS`.
- 2026-03-11 — `TASK_ARCHIVE_Indexing_Summary.md` moved to `SPECS/ARCHIVE/_Historical/` after documenting the completed LM Studio indexing run for `ISOInspector/DOCS/TASK_ARCHIVE`.

## Suggested Next Tasks

- `PH3-T2` — Implement Candidate Selection
- `PH3-T3` — Implement Local Tree Search
- `PH3-T4` — Build Search CLI Wrapper
