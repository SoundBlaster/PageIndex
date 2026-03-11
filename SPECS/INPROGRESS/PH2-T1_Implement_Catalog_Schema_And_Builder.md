# PH2-T1 — Implement Catalog Schema And Builder

**Task ID:** PH2-T1
**Phase:** Phase 2: Build Catalog Layer
**Priority:** P0
**Dependencies:** None
**Status:** Planned

## Objective Summary

Add a deterministic catalog builder for mirrored `*_structure.json` outputs produced by the recursive Markdown indexing workflow. The builder must scan one output root, recover the matching source Markdown path for each indexed structure file, and emit stable per-record metadata that later retrieval steps can use without reopening every JSON file on every query. The initial scope is schema definition plus in-process builder functions; the CLI wrapper that writes `catalog.json` is deferred to `PH2-T3`.

The real target corpus is `results/isoinspector_task_archive_lmstudio`, which includes a `manifest.json`, mirrored output directories, repeated basenames such as `Summary_of_Work`, and source-side `*_metrics.json` provenance sidecars. The catalog must preserve those distinctions while staying deterministic across repeated runs over unchanged filesystem state.

## Deliverables

1. A catalog module under `pageindex/` that defines the catalog artifact schema and record shape.
2. A builder that scans an output root, reads `manifest.json` when present, inspects each structure JSON, and produces a deterministically ordered catalog object.
3. Record metadata covering:
   - `project_id` / output-root identifier
   - source path and output path
   - source-relative and output-relative paths
   - document name and relative directory
   - freshness metadata from filesystem timestamps
   - summary-presence and node-text-presence booleans
   - provenance metadata linking manifest status/index and optional metrics sidecar discovery
4. Automated tests covering deterministic ordering, duplicate basenames in different folders, manifest/source path reconstruction, and summary/text detection.

## Acceptance Criteria

- Each catalog record includes source path, output path, project identifier, document name, relative directory, freshness metadata, and provenance metadata.
- Duplicate basenames remain uniquely addressable through stable record IDs and relative paths.
- Summary presence is true when any node contains `summary` or `prefix_summary`; node-text presence is true when any node contains `text`.
- Catalog output order is deterministic and independent of filesystem traversal order.
- Tests cover both manifest-backed source reconstruction and fallback behavior for root-level/root-relative files.

## Test-First Plan

Before implementation, add pytest coverage for:

1. Two documents with the same basename in different directories to prove unique `record_id` and stable ordering.
2. A structure file with summaries but no text and another with raw node text to verify boolean detection.
3. Manifest-backed reconstruction of `source_path`, `relative_directory`, and `manifest_status`.
4. Metrics sidecar discovery and timestamp capture for freshness/provenance fields.

## Execution Plan

### Phase 1: Schema
- Define typed record/artifact helpers that serialize cleanly to JSON-ready dicts.
- Decide and document the stable `record_id` format as `{project_id}:{output_rel_path}`.

### Phase 2: Builder
- Load manifest metadata and build output-to-source lookup tables.
- Walk `*_structure.json` files, inspect document payloads, derive source/metrics paths, and collect timestamps.
- Sort records by relative output path to guarantee deterministic artifacts.

### Phase 3: Verification
- Add focused pytest coverage for fixture-based output roots.
- Run repository validation commands plus targeted coverage for the new catalog module.
- Write `SPECS/INPROGRESS/PH2-T1_Validation_Report.md` with recorded commands and verdicts.

## Decision Points And Constraints

- Do not add CLI surface yet; keep the builder importable so `PH2-T3` can wrap it without refactoring.
- Avoid non-deterministic fields such as “generated at” timestamps inside the catalog artifact.
- Require either `manifest.json` or an explicit `input_root` so `source_path` remains authoritative.

## Notes

- Update `README.md` after implementation if the new builder becomes a user-facing capability worth documenting before `PH2-T3`.
- Keep the schema extensible for `PH2-T2`, which will add classification and freshness heuristics on top of these raw fields.
