# Next Task: PH4-T2 — Implement Answer-Ready Extraction Mode

**Task ID:** PH4-T2
**Phase:** Phase 4: Build Context Extraction
**Effort:** Medium
**Dependencies:** PH3-T4, PH4-T1
**Status:** Selected

## Description

Implement an answer-ready extraction mode that enriches retrieval results with compact evidence blocks and citations when node text exists. The mode must keep the existing deterministic JSON schema, populate `extracted_context` on success, and return explicit machine-readable errors when raw node text is unavailable in the current index outputs.

## Next Step

Run PLAN and EXECUTE for `PH4-T2`, then archive the task and review the answer-ready retrieval flow.

## Recently Archived

- 2026-03-11 — `PH2-T1` archived to `SPECS/ARCHIVE/PH2-T1_Implement_Catalog_Schema_And_Builder/` with verdict `PASS`.
- 2026-03-11 — `PH2-T2` archived to `SPECS/ARCHIVE/PH2-T2_Add_Classification_And_Freshness_Heuristics/` with verdict `PASS`.
- 2026-03-11 — `PH2-T3` archived to `SPECS/ARCHIVE/PH2-T3_Build_Catalog_CLI/` with verdict `PASS`.
- 2026-03-11 — `PH3-T1` archived to `SPECS/ARCHIVE/PH3-T1_Define_Retrieval_Result_Schema/` with verdict `PASS`.
- 2026-03-12 — `PH3-T2` archived to `SPECS/ARCHIVE/PH3-T2_Implement_Candidate_Selection/` with verdict `PASS`.
- 2026-03-12 — `PH3-T3` archived to `SPECS/ARCHIVE/PH3-T3_Implement_Local_Tree_Search/` with verdict `PASS`.
- 2026-03-12 — `PH3-T4` archived to `SPECS/ARCHIVE/PH3-T4_Build_Search_CLI_Wrapper/` with verdict `PASS`.
- 2026-03-12 — `PH4-T1` archived to `SPECS/ARCHIVE/PH4-T1_Implement_Node_Lookup_Helpers/` with verdict `PASS`.
- 2026-03-12 — `PH5-T1` archived to `SPECS/ARCHIVE/PH5-T1_Define_Local_Tool_Contract/` with verdict `PASS`.
- 2026-03-11 — `TASK_ARCHIVE_Indexing_Summary.md` moved to `SPECS/ARCHIVE/_Historical/` after documenting the completed LM Studio indexing run for `ISOInspector/DOCS/TASK_ARCHIVE`.

## Suggested Next Tasks

- `PH5-T2` — Add Local API Or MCP Shim
- `PH1-T1` — Define Output And Manifest Contract
- `PH1-T2` — Harden Resume Behavior
