# PRD: Local Multi-Index Retrieval for PageIndex

## 1. Document Purpose

This document defines an implementation-ready plan for extending this `PageIndex` fork into a fully local multi-index retrieval system. It is written to be directly executable by LLM-based coding agents without requiring additional clarification.

This PRD covers:

- local indexing of many Markdown files into PageIndex trees
- durable resume behavior for long-running indexing jobs
- local catalog construction over many index outputs
- local retrieval across many indexed documents using LM Studio
- local context extraction for downstream answer generation
- a path to CLI-first search, then API/MCP integration

This PRD does not cover:

- hosted PageIndex APIs
- hosted MCP servers
- cloud OpenAI inference
- a graphical web UI

## 2. Objective

Build a local-first retrieval workflow over many PageIndex-generated indexes so that a user can search a large Markdown archive, identify relevant documents and nodes, and optionally extract answer-ready context, all using local files and a local OpenAI-compatible inference endpoint such as LM Studio.

## 3. Scope

### In Scope

- Markdown archive indexing at directory scale
- resumable indexing over interrupted jobs
- local catalog metadata over generated `*_structure.json` files
- local candidate selection before tree search
- tree-search-based retrieval over multiple candidate documents
- text extraction from indexed nodes when available
- CLI entry points for search and retrieval
- future-proof interfaces for local API and MCP layers

### Out of Scope

- replacing upstream single-file index generation
- vector database integration as a primary retrieval layer
- remote storage, sync, or SaaS features
- browser UI or dashboard
- user authentication and multi-tenant access control

## 4. Background and Rationale

Upstream PageIndex is optimized for single-document workflows and hosted retrieval paths. That is insufficient for the target environment:

- the main corpus is a large local Markdown archive
- filenames repeat heavily across folders
- retrieval must work across hundreds of files
- all model access must stay local
- results must remain readable and inspectable on disk

This fork already introduced two enabling changes:

1. LM Studio / OpenAI-compatible local inference support in `pageindex/utils.py`
2. Recursive Markdown indexing in `scripts/index_markdown_directory.py`

Those changes solve local index generation, but not local multi-document retrieval. The missing system is a search and retrieval layer over many existing indexes.

## 5. Primary Deliverables

| ID | Deliverable | Description | Success Condition |
|---|---|---|---|
| D1 | Resume-safe indexer | Batch indexer that can skip completed outputs and persist progress | Interrupted jobs can resume without redoing finished work |
| D2 | Local catalog | Searchable metadata registry over many `*_structure.json` files | Catalog can be rebuilt deterministically from disk |
| D3 | Search CLI | Query interface for local candidate selection and tree search | User can retrieve relevant files and node IDs from one command |
| D4 | Context extraction layer | Mapping from search results to titles, summaries, and node text | Retrieved nodes can be converted into answer-ready context |
| D5 | Agent integration contract | Stable result schema suitable for future API/MCP wrapping | Agent can consume results without custom parsing hacks |

## 6. Success Criteria

The initiative is successful only if all of the following are true:

1. A corpus of hundreds of Markdown files can be indexed incrementally and resumed safely.
2. A local user can query across many indexed documents without manually opening individual JSON files.
3. Retrieval returns document paths, relevant node IDs, and reasoning traces.
4. When node text is available, the system can extract answer-ready context locally.
5. The entire workflow runs with local files plus LM Studio only.
6. The architecture leaves a clean path to a local MCP or API service.

## 7. Constraints, Assumptions, and External Dependencies

### Constraints

- All inference must work against a local OpenAI-compatible endpoint.
- Existing upstream single-file behavior must remain functional.
- Outputs must stay as JSON files on disk.
- The repository currently uses Python with a local `.venv`.

### Assumptions

- LM Studio is reachable at a stable local endpoint.
- The user can re-index with `--if-add-node-text yes` when answer generation needs raw text.
- Lexical/metadata narrowing will be required before tree search on large corpora.

### External Dependencies

| Dependency | Purpose | Failure Mode |
|---|---|---|
| LM Studio / compatible server | Local inference backend | Search and summary generation unavailable |
| `openai` Python client | OpenAI-compatible API access | Retrieval calls fail |
| `tiktoken` | Token counting | Fallback encoding required for local model IDs |
| Local filesystem | Source corpus and index storage | Indexing/search unavailable |

## 8. Current State

### Already Implemented

- `run_pageindex.py` supports single-file PDF/Markdown indexing
- `pageindex/utils.py` supports LM Studio via `OPENAI_BASE_URL`
- `scripts/index_markdown_directory.py` indexes Markdown recursively
- Flow is installed and configured for this repository

### Current Gaps

- no durable multi-document catalog
- no multi-document search CLI
- no standardized retrieval schema
- no explicit context extraction layer
- no local API or MCP interface

## 9. User Profiles and Primary Workflows

### Primary User

- Repository owner maintaining a local engineering knowledge archive

### Workflow A: Archive Indexing

1. User points the system to a Markdown root.
2. System indexes all files into mirrored `*_structure.json` outputs.
3. If interrupted, user resumes without redoing completed outputs.

### Workflow B: Local Search

1. User submits a query.
2. System narrows candidate documents.
3. System performs tree search over candidate documents.
4. System returns relevant files and nodes.

### Workflow C: Answer Preparation

1. User selects retrieval mode requiring text.
2. System extracts node content and metadata.
3. System returns structured context suitable for answer generation.

### Workflow D: Agent Tooling

1. Agent sends search request to local tool layer.
2. Tool returns structured retrieval results.
3. Agent fetches node context and answers using local evidence.

## 10. Functional Requirements

### FR1. Resume-Safe Batch Indexing

The batch indexer must:

- recursively discover `.md` and `.markdown` files
- mirror source tree structure in output paths
- support `--resume` by skipping outputs that already exist
- write progress to `manifest.json` incrementally
- preserve completed outputs after interrupted runs

### FR2. Index Profiles

The indexing layer must support explicit profiles for:

- structure-only indexing
- summary-enhanced indexing
- retrieval-ready indexing with node text

### FR3. Local Catalog Construction

The system must generate a local catalog artifact containing:

- source path
- output path
- document name
- relative directory
- classification tags
- indexing status
- summary/description presence flags

### FR4. Candidate Selection

The system must support narrowing the corpus before tree search using:

- filename/path filters
- directory/category filters
- lexical matching over catalog metadata
- optional summary/description-based narrowing

### FR5. Multi-Document Tree Search

The system must run tree search through LM Studio over selected candidate documents and return:

- document list considered
- relevant node IDs
- model reasoning trace
- per-node titles and source paths

### FR6. Context Extraction

The system must map tree search results back to:

- node titles
- node summaries
- node text when present
- source file paths
- output JSON paths

### FR7. CLI Query Interface

The system must expose a CLI command that:

- accepts a user query
- supports corpus filters
- supports dry-run candidate inspection
- supports retrieval-only and answer-ready modes

### FR8. Stable Result Schema

The retrieval layer must emit a deterministic schema suitable for CLI, API, and MCP reuse.

Required fields:

- query
- corpus root
- candidate documents
- selected documents
- selected nodes
- reasoning
- extracted context
- errors/warnings

## 11. Non-Functional Requirements

| ID | Requirement | Target |
|---|---|---|
| NFR1 | Fully local operation | No mandatory network dependency beyond local LM Studio |
| NFR2 | Durability | Interrupted indexing jobs can resume without data loss |
| NFR3 | Inspectability | All outputs remain JSON on disk and human-readable |
| NFR4 | Modularity | Catalog, retrieval, extraction, and serving layers are separable |
| NFR5 | Low setup overhead | Works with `.venv`, local endpoint, and local corpus |
| NFR6 | Predictable schemas | CLI/API/MCP can share the same result structure |

## 12. Edge Cases and Failure Scenarios

| Scenario | Expected System Behavior |
|---|---|
| Duplicate basenames in different folders | Outputs remain unique because directory structure is mirrored |
| Interrupted batch indexing | Resume mode skips completed outputs and continues remaining files |
| `manifest.json` missing or stale | Rebuild progress from output file existence and continue |
| Local model ID unknown to `tiktoken` | Fall back to `cl100k_base` and continue |
| Node text absent in index | Report retrieval-only mode or require re-index with node text |
| LM Studio unavailable | Return explicit retrieval failure without corrupting outputs |
| Malformed model JSON response | Record failure and continue processing other documents where possible |

## 13. Proposed Architecture

### A. Indexing Layer

Current files:

- `run_pageindex.py`
- `scripts/index_markdown_directory.py`

Responsibilities:

- single-file indexing
- recursive corpus indexing
- resume-safe manifest persistence

### B. Catalog Layer

New files:

- `pageindex/catalog.py`
- `scripts/build_index_catalog.py`

Responsibilities:

- scan output tree
- derive metadata and classification tags
- persist catalog JSON

### C. Retrieval Layer

New files:

- `pageindex/retrieval.py`
- `scripts/search_task_archive.py`

Responsibilities:

- query normalization
- candidate selection
- tree search prompt assembly
- result normalization

### D. Context Layer

New files:

- `pageindex/context.py`

Responsibilities:

- node lookup
- summary/text extraction
- citation generation

### E. Serving Layer

Deferred interfaces:

- `scripts/serve_archive_api.py`
- `scripts/pageindex_mcp_server.py`

Responsibilities:

- stable tool/API surface over retrieval results

## 14. Dependency Graph

| Task | Depends On | Parallelizable |
|---|---|---|
| T1. Harden batch indexing | none | no |
| T2. Build catalog layer | T1 output format stable | yes |
| T3. Build retrieval schema | T1 | yes |
| T4. Build candidate selection | T2 | yes |
| T5. Build tree search CLI | T3, T4 | no |
| T6. Build context extraction | T3 | yes |
| T7. Add answer-ready mode | T5, T6 | no |
| T8. Add API/MCP surface | T5, T6 | yes |

## 15. Hierarchical TODO Plan

## Phase 1: Stabilize Indexing Foundations

### T1.1 Define output and manifest contract

| Field | Value |
|---|---|
| Priority | High |
| Effort | 2 |
| Inputs | Existing `scripts/index_markdown_directory.py`, current output directories |
| Process | Define canonical meanings for `indexed`, `skipped`, and `failed`; define when manifest must be flushed |
| Output | Stable manifest schema documented in code and README |
| Verification | Resume run produces deterministic counts and does not overwrite completed outputs |

### T1.2 Harden `--resume`

| Field | Value |
|---|---|
| Priority | High |
| Effort | 3 |
| Inputs | Existing batch script and partially indexed corpus |
| Process | Ensure resume is based on output file existence and manifest updates are incremental |
| Output | Resume-safe batch indexer |
| Verification | Interrupted run can continue and final file count matches expected corpus size |

### T1.3 Define indexing profiles

| Field | Value |
|---|---|
| Priority | Medium |
| Effort | 2 |
| Inputs | Current CLI flags and README notes |
| Process | Document named profiles for structure-only, summary, and retrieval-ready indexing |
| Output | Documented invocation patterns |
| Verification | Commands run successfully against sample corpus |

## Phase 2: Build Catalog Layer

### T2.1 Implement catalog schema

| Field | Value |
|---|---|
| Priority | High |
| Effort | 3 |
| Inputs | Existing `*_structure.json` outputs |
| Process | Define catalog record fields and serialization format |
| Output | `pageindex/catalog.py` with schema and builder |
| Verification | Synthetic and real outputs serialize into a stable catalog JSON |

### T2.2 Add file classification heuristics

| Field | Value |
|---|---|
| Priority | Medium |
| Effort | 2 |
| Inputs | Source paths and repeated archive naming patterns |
| Process | Classify `summary`, `task`, `next_tasks`, `blocked`, and generic docs |
| Output | Tagging logic used by catalog builder |
| Verification | Sample corpus yields expected category tags |

### T2.3 Build catalog CLI

| Field | Value |
|---|---|
| Priority | Medium |
| Effort | 2 |
| Inputs | Catalog module |
| Process | Add script to scan outputs and write `catalog.json` |
| Output | `scripts/build_index_catalog.py` |
| Verification | CLI produces catalog over real corpus without collisions |

## Phase 3: Build Retrieval CLI

### T3.1 Define retrieval result schema

| Field | Value |
|---|---|
| Priority | High |
| Effort | 2 |
| Inputs | Catalog fields and tree search needs |
| Process | Define normalized response shape for CLI/API/MCP reuse |
| Output | Schema implemented in retrieval module |
| Verification | Search command returns deterministic keys and types |

### T3.2 Implement candidate selection

| Field | Value |
|---|---|
| Priority | High |
| Effort | 3 |
| Inputs | Catalog JSON and user query |
| Process | Add lexical/path/category filtering before tree search |
| Output | Candidate selector returning bounded document list |
| Verification | Known queries reduce corpus to relevant subset |

### T3.3 Implement local tree search

| Field | Value |
|---|---|
| Priority | High |
| Effort | 5 |
| Inputs | Candidate documents, LM Studio endpoint, PageIndex trees |
| Process | Build tree search prompts, call LM Studio, validate result JSON |
| Output | Multi-document tree search engine |
| Verification | Query returns relevant node IDs and reasoning on sample corpus |

### T3.4 Build CLI wrapper

| Field | Value |
|---|---|
| Priority | High |
| Effort | 2 |
| Inputs | Candidate selection and tree search modules |
| Process | Expose command-line interface for local query execution |
| Output | `scripts/search_task_archive.py` |
| Verification | One command can search the corpus and print structured results |

## Phase 4: Build Context Extraction

### T4.1 Implement node lookup helpers

| Field | Value |
|---|---|
| Priority | Medium |
| Effort | 2 |
| Inputs | Retrieval result schema and output JSON structure |
| Process | Resolve node IDs to titles, summaries, and optional text |
| Output | `pageindex/context.py` lookup API |
| Verification | Known node IDs map correctly to source metadata |

### T4.2 Implement answer-ready extraction mode

| Field | Value |
|---|---|
| Priority | Medium |
| Effort | 3 |
| Inputs | Context layer and retrieval results |
| Process | Build a mode that returns condensed context blocks for answering |
| Output | CLI option for extraction mode |
| Verification | Query returns compact evidence package with citations |

## Phase 5: Prepare Agent Integration

### T5.1 Define local tool contract

| Field | Value |
|---|---|
| Priority | Medium |
| Effort | 2 |
| Inputs | Retrieval schema |
| Process | Define callable operations for future API/MCP use |
| Output | Tool contract documented in code and README |
| Verification | Search and context operations map cleanly to stable inputs/outputs |

### T5.2 Add local API or MCP shim

| Field | Value |
|---|---|
| Priority | Low |
| Effort | 4 |
| Inputs | Retrieval CLI and context layer |
| Process | Wrap core search functions in a local service surface |
| Output | API or MCP prototype |
| Verification | Agent can query corpus through the tool layer |

## 16. Test-First Plan

Tests or deterministic checks must be added in this order:

1. Resume behavior over an interrupted sample corpus
2. Manifest correctness after indexed/skipped/failed paths
3. Catalog generation over duplicate basenames
4. Candidate selection over a synthetic catalog fixture
5. Retrieval schema validation for successful and failed LM responses
6. Context extraction for both text-present and text-absent indexes

Recommended verification style:

- unit tests for pure helpers
- fixture-based tests for catalog and context layers
- smoke CLI checks for end-to-end flows
- strict JSON validation for LM responses

## 17. Acceptance Criteria by Deliverable

### D1. Resume-safe indexer

- `--resume` skips completed outputs
- incremental progress survives interruption
- final counts are reproducible

### D2. Local catalog

- catalog rebuilds from disk without manual edits
- duplicate basenames do not collide
- category tagging is present for repeated archive patterns

### D3. Search CLI

- one command accepts a query and returns relevant document paths
- result includes node IDs and reasoning
- candidate selection happens before tree search

### D4. Context extraction

- node IDs can be resolved back to human-usable context
- absence of node text is reported explicitly

### D5. Agent integration contract

- result schema is stable and documented
- core retrieval can be wrapped without changing search logic

## 18. Risks and Mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| Tree search over full corpus is too slow | High | Require candidate narrowing before LM calls |
| Missing node text blocks answer generation | Medium | Support text-retaining indexing profile and explicit fallback messaging |
| LM Studio returns malformed JSON | High | Validate, retry narrowly, and record failures without corrupting outputs |
| Partial resume state becomes ambiguous | High | Treat output file existence as truth and flush manifest incrementally |
| Retrieval schema drifts across tools | Medium | Define shared schema before API/MCP work |

## 19. Implementation Notes for LLM Agents

- Do not replace the upstream single-file CLI.
- Prefer additive modules over invasive rewrites.
- Preserve human-readable JSON outputs.
- Treat local filesystem state as the primary source of truth.
- When introducing new scripts, keep them composable and non-interactive.
- When possible, validate behavior on the existing `ISOInspector` archive layout.

## 20. Immediate Recommended Next Task

Implement **Phase 2: Build Catalog Layer** next.

Reason:

- indexing already exists
- retrieval across hundreds of files is impractical without a catalog
- catalog schema is the clean dependency boundary for CLI, API, and MCP

## 21. Architectural Decisions

These decisions are mandatory unless this PRD is explicitly revised.

### AD1. Filesystem Is the Source of Truth

The system must treat on-disk outputs as canonical state.

Implications:

- output JSON existence is authoritative for resume logic
- `manifest.json` is a progress artifact, not a primary database
- catalog rebuild must work even if `manifest.json` is missing or stale

### AD2. Candidate Selection Must Be Cheap

The system must not run LM-driven tree search over the full corpus by default.

Implications:

- candidate narrowing happens before any LM call
- first-stage narrowing must rely on catalog metadata, lexical search, and path/category filters
- tree search only runs on a bounded candidate set

### AD3. Retrieval and Answer Generation Are Separate Modes

The system must distinguish:

- retrieval mode: find documents and node IDs
- answer mode: extract text and build answer-ready context

Implications:

- a query may succeed in retrieval mode even when node text is absent
- answer mode must fail explicitly if required node text is unavailable

### AD4. Maintain Two Valid Index Profiles

The system should support two persistent operational profiles:

1. `summary` profile for lighter storage and navigation
2. `text` profile for answer-ready context extraction

Implications:

- do not force every corpus to retain node text
- allow re-indexing or parallel output roots for text-heavy corpora

### AD5. MCP Is a Wrapper, Not the Core

MCP must be implemented only after CLI and retrieval schema stabilize.

Implications:

- the core system is a Python retrieval library plus CLI
- API and MCP layers must call the same underlying retrieval functions
- do not encode business logic directly into the MCP layer

## 22. MVP Execution Strategy

This section defines the preferred implementation order and the point at which the first usable version is considered complete.

### MVP Goal

Deliver a local CLI that can:

1. build or rebuild a catalog over many PageIndex outputs
2. accept a user query
3. narrow the corpus to candidate documents
4. run tree search over those candidates through LM Studio
5. return file paths, node IDs, section titles, and reasoning

### Explicit MVP Exclusions

The following are not required for MVP completion:

- MCP server
- HTTP API
- final answer synthesis
- automatic re-index orchestration
- UI

### MVP Milestones

| Milestone | Required Tasks | Done When |
|---|---|---|
| M1. Stable index artifacts | T1.1, T1.2, T1.3 | Resume is reliable and manifest semantics are clear |
| M2. Searchable catalog | T2.1, T2.2, T2.3 | Catalog can be rebuilt from real corpus and queried deterministically |
| M3. Retrieval CLI | T3.1, T3.2, T3.3, T3.4 | One command returns relevant files, nodes, and reasoning |
| M4. Context-ready expansion | T4.1, T4.2 | Retrieval can optionally emit answer-ready evidence |
| M5. Agent integration | T5.1, T5.2 | CLI/core can be wrapped for agents via API or MCP |

### Stop Condition for First Release

Stop after **M3** and validate real usage before building MCP.

Rationale:

- M3 already solves the core user problem: local smart search over many indexes
- M4 and M5 are valuable but should be driven by real retrieval usage
- deferring MCP reduces architectural churn

## 23. Priority Corrections

To avoid overbuilding, apply the following priority order across the whole initiative:

| Priority Band | Items |
|---|---|
| Highest | T1.2, T2.1, T2.3, T3.1, T3.2, T3.3, T3.4 |
| Medium | T1.3, T2.2, T4.1, T4.2, T5.1 |
| Lowest | T5.2 |

Interpretation:

- if time is limited, finish catalog plus retrieval CLI first
- do not start MCP before the retrieval schema and CLI prove stable on the real archive

## 24. Recommended Next Three Tasks

If execution starts immediately, do the following in order:

### Next Task 1

Implement `pageindex/catalog.py` with a stable record schema and filesystem scan.

Why first:

- it converts raw output JSON files into a queryable substrate
- every later search interface depends on it

### Next Task 2

Implement `scripts/build_index_catalog.py` and generate a real catalog over the current `isoinspector_task_archive_lmstudio` output root.

Why second:

- it validates the catalog design against the real corpus, including duplicate basenames

### Next Task 3

Implement `scripts/search_task_archive.py` with candidate selection over catalog metadata before any LM call.

Why third:

- this is the first user-visible “smart search” milestone
- it solves the core problem without waiting for MCP or API work
