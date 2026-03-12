# PH5-T1 — Define Local Tool Contract

**Task ID:** PH5-T1
**Phase:** Phase 5: Prepare Agent Integration
**Priority:** P1
**Dependencies:** PH3-T1, PH3-T4, PH4-T1
**Status:** Planned

## Objective Summary

Define the stable local callable contract that future API or MCP wrappers must use for search and context lookups. The contract must stay aligned with the existing CLI and schema surface instead of inventing a second payload format, and it must make machine-readable error behavior explicit for agent callers.

This task should document the contract in code and in the repository README. It should not introduce a service or transport layer yet; that belongs to `PH5-T2`.

## Deliverables

1. A thin contract module under `pageindex/` that:
   - defines the callable search and context request surfaces
   - delegates directly to the existing retrieval and context helpers
   - reuses `RetrievalResult`, `NodeContext`, and `RetrievalError` outputs instead of creating alternate schemas
2. README documentation for:
   - the search operation
   - the context operation
   - machine-readable error codes and when callers should expect them
3. Focused tests showing the contract wrappers call the same underlying search/context logic and preserve output shapes.

## Acceptance Criteria

- Search and context operations have explicit input and output contracts.
- Contracts reuse the CLI schema instead of creating a second format.
- Agent-facing error behavior is documented in machine-readable terms.

## Test-First Plan

Before implementation, add tests for:

1. Search contract wrapper execution with the same result shape as `search_catalog`.
2. Context contract wrapper execution with `NodeContext` output and `node_text_missing` behavior preserved.
3. Contract request defaults mapping cleanly onto the existing CLI/search defaults.

## Execution Plan

### Phase 1: Contract Surface
- Add a small `pageindex/tool_contract.py` module with request models and wrapper functions for search and context operations.
- Keep the wrappers thin and side-effect free beyond delegating to the existing retrieval/context helpers.

### Phase 2: Documentation
- Add a README section that names the two operations, their request fields, their output objects, and the machine-readable error codes they may return.
- Tie the documented search request fields back to the existing CLI arguments.

### Phase 3: Verification
- Add focused unit tests for the wrapper layer.
- Run repository validation commands and task-local coverage.
- Write `SPECS/INPROGRESS/PH5-T1_Validation_Report.md` with verdict and command outcomes.

## Decision Points And Constraints

- Do not add a network service, HTTP API, or MCP server in this task.
- Do not duplicate retrieval or context business logic behind the contract wrappers.
- Keep the contract explicit enough that `PH5-T2` can wrap it directly without reshaping responses.

---
**Archived:** 2026-03-12
**Verdict:** PASS
