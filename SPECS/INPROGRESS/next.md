# Next Task: PH2-T1 — Implement Catalog Schema And Builder

**Priority:** P0
**Phase:** Phase 2: Build Catalog Layer
**Effort:** 3
**Dependencies:** None
**Status:** Ready

## Description

Build the catalog model and scanner that convert many `*_structure.json` files into a deterministic per-project catalog artifact. The catalog must include source path, output path, project/output-root identifier, document name, relative directory, and provenance metadata. It must also preserve uniqueness for duplicate basenames across different folders.

## Next Step

Run the PLAN command to create the implementation-ready PRD for `PH2-T1`.

## Recently Archived

- 2026-03-11 — `TASK_ARCHIVE_Indexing_Summary.md` moved to `SPECS/ARCHIVE/_Historical/` after documenting the completed LM Studio indexing run for `ISOInspector/DOCS/TASK_ARCHIVE`.

## Suggested Next Tasks

- `PH2-T2` — Add Classification And Freshness Heuristics
- `PH2-T3` — Build Catalog CLI
