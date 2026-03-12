# PH5-T2 — Add Local API Or MCP Shim

**Task ID:** PH5-T2
**Phase:** Phase 5: Prepare Agent Integration
**Priority:** P2
**Dependencies:** PH5-T1, PH3-T4, PH4-T1
**Status:** Planned

## Objective Summary

Add a thin local API shim that exposes the stabilized search and context contract over simple JSON HTTP requests. The shim must call the same `pageindex.tool_contract` functions that future agent integrations are expected to use, preserve the existing retrieval and context payloads, and avoid copying any retrieval or node lookup logic into the transport layer.

This task should choose the local API path rather than introducing a full MCP server. The transport only needs to be local, deterministic, and easy for an agent to call.

## Deliverables

1. A local API module under `pageindex/` that:
   - exposes POST handlers for search and context operations
   - deserializes JSON request payloads into `SearchToolRequest`, `ContextToolRequest`, and `RetrievalNode` objects
   - delegates directly to `run_search_tool(...)` and `run_context_tool(...)`
2. A runnable local wrapper entry point that starts the HTTP server without adding a new framework dependency.
3. README documentation that covers:
   - how to start the local API shim
   - the `/search` and `/context` request payloads
   - the response shapes and their relationship to the shared contract layer
4. Focused tests showing:
   - the wrapper reuses the existing contract surface
   - the JSON responses are deterministic and agent-friendly
   - invalid requests fail in a machine-readable way

## Acceptance Criteria

- The wrapper calls the same underlying retrieval and context functions as the CLI.
- No business logic is duplicated into the wrapper layer.
- An agent can query the local corpus through the wrapper without custom response parsing hacks.

## Test-First Plan

Before implementation, add tests for:

1. Search requests reaching the contract layer and returning the existing `RetrievalResult` JSON shape.
2. Context requests accepting `selected_nodes` in retrieval-node JSON form and returning serialized `NodeContext` plus shared error payloads.
3. Request validation failures returning deterministic JSON error payloads instead of HTML or tracebacks.
4. A server-level smoke test proving the shim can service a local request end-to-end.

## Execution Plan

### Phase 1: Transport Surface
- Add a small `pageindex/local_api.py` module built on the Python standard library HTTP server.
- Keep transport concerns limited to routing, JSON decoding/encoding, and request validation.

### Phase 2: Contract Delegation
- Convert request payloads into the existing tool-contract dataclasses and retrieval-node objects.
- Reuse `RetrievalResult.to_dict(...)`, `NodeContext` serialization, and `RetrievalError.to_dict()` for responses.

### Phase 3: Verification
- Add focused unit and integration-style tests for request handling.
- Run repository validation commands and task-local coverage.
- Write `SPECS/INPROGRESS/PH5-T2_Validation_Report.md` with verdict and command outcomes.

## Decision Points And Constraints

- Do not add FastAPI, Flask, or any other new web framework dependency.
- Do not duplicate retrieval, answer-ready extraction, or node lookup logic in the API layer.
- Keep the API local-only and lightweight; transport complexity belongs after MVP if still needed.
- Preserve the shared search result schema so agent callers can reuse the same response parsing across CLI, contract, and local API layers.
