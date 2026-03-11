# PH2-T3 — Build Catalog CLI

**Task ID:** PH2-T3
**Phase:** Phase 2: Build Catalog Layer
**Priority:** P0
**Dependencies:** PH2-T1, PH2-T2
**Status:** Planned

## Objective Summary

Add a dedicated CLI command that rebuilds a per-project catalog from an output root on disk and writes the resulting `catalog.json` as a separate artifact. This task should wrap the existing builder logic rather than duplicating schema or scanning behavior. The real target is `results/isoinspector_task_archive_lmstudio`, but the CLI must also be easy to validate against synthetic fixtures.

## Deliverables

1. A CLI script at `scripts/build_index_catalog.py`.
2. Command-line options for:
   - `--output-root` (required)
   - `--input-root` (optional)
   - `--manifest-path` (optional)
   - `--project-id` (optional)
   - `--catalog-path` (optional explicit destination)
3. Default output behavior that writes `catalog.json` beside, not inside, the structure output set unless explicitly overridden.
4. Automated tests covering CLI execution, output file generation, and default destination behavior.

## Acceptance Criteria

- One CLI command rebuilds the catalog from disk without manual edits.
- The catalog artifact is stored separately from the index JSON files.
- The command works against the real `isoinspector_task_archive_lmstudio` output root.
- The CLI reuses `pageindex.catalog` instead of reimplementing scan or serialization logic.

## Test-First Plan

Before implementation, add tests for:

1. Running the CLI over a synthetic output root with an explicit destination.
2. Running the CLI without `--catalog-path` to verify the default artifact path.
3. CLI payload correctness for `project_id`, `output_root`, and record count.

## Execution Plan

### Phase 1: Interface
- Define the CLI arguments and help text.
- Choose a default destination that keeps `catalog.json` outside the mirrored index tree.

### Phase 2: Implementation
- Build the catalog via `pageindex.catalog.build_catalog`.
- Persist via `pageindex.catalog.write_catalog`.
- Print the written artifact path for operator visibility.

### Phase 3: Verification
- Add focused CLI pytest coverage.
- Run repo verification commands plus a real-corpus catalog build.
- Write `SPECS/INPROGRESS/PH2-T3_Validation_Report.md` with command outputs and verdict.

## Decision Points And Constraints

- Keep the CLI as a standalone script for now; do not overload `run_pageindex.py`.
- Avoid any behavior that mutates existing structure JSON files or manifests.
- Default artifact placement must stay deterministic and easy to reference from later retrieval commands.
