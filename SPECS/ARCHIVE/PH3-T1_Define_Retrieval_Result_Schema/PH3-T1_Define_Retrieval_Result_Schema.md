# PH3-T1 — Define Retrieval Result Schema

**Task ID:** PH3-T1
**Phase:** Phase 3: Build Retrieval CLI
**Priority:** P0
**Dependencies:** PH2-T1
**Status:** Planned

## Objective Summary

Define the normalized retrieval result contract that the future candidate selector, local tree search, CLI wrapper, and agent-facing surfaces will all reuse. The schema must prioritize deterministic JSON output and predictable keys over implementation convenience. Flat node results are the default shape, but callers must be able to request grouped-by-document output without losing the core top-level fields.

## Deliverables

1. A retrieval schema module under `pageindex/` with typed result helpers.
2. Top-level result fields covering:
   - `query`
   - `corpus_root`
   - `catalog_path`
   - `candidate_documents`
   - `selected_documents`
   - `selected_nodes`
   - `extracted_context`
   - `errors`
3. Optional grouped output that adds grouped document structure without changing the core field names.
4. Optional reasoning support that is omitted by default but serializes deterministically when enabled.
5. Automated tests for serialization, grouped output, and machine-readable error payloads.

## Acceptance Criteria

- Default output is a flat `selected_nodes` list.
- Optional grouped-by-document output is supported without changing core field names.
- Schema includes `query`, `corpus_root`, `catalog_path`, candidate documents, selected documents, selected nodes, extracted context, and machine-readable errors.
- Serialization is deterministic and suitable for CLI/API/MCP reuse.

## Test-First Plan

Before implementation, add tests for:

1. Default flat serialization with deterministic top-level keys.
2. Grouped serialization that preserves flat lists while adding grouped document structure.
3. Error serialization with stable `code`, `message`, and optional details fields.
4. Optional reasoning behavior that is excluded by default and included only when requested.

## Execution Plan

### Phase 1: Schema
- Define typed document, node, context, and error payload helpers.
- Keep field names explicit so later modules can adopt the schema without wrappers.

### Phase 2: Serialization
- Implement deterministic `to_dict()` behavior for flat output.
- Add an opt-in grouped serialization mode and opt-in reasoning inclusion.

### Phase 3: Verification
- Add focused pytest coverage for the schema module.
- Run repository verification commands plus task-local coverage.
- Write `SPECS/INPROGRESS/PH3-T1_Validation_Report.md` with verdict and command outcomes.

## Decision Points And Constraints

- Do not implement candidate selection or LM search behavior in this task.
- Keep the schema independent from transport layers so it can back CLI output, local APIs, and MCP wrappers.
- Avoid leaking optional reasoning fields into default output.

---
**Archived:** 2026-03-11
**Verdict:** PASS
