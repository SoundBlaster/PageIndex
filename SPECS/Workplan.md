# Project Workplan — Local Multi-Index Retrieval for PageIndex

This workplan tracks the remaining project work for turning this `PageIndex` fork into a local multi-index retrieval system for agent-facing JSON search over Markdown archives.

Primary validation corpus:

- source archive: `ISOInspector/DOCS/TASK_ARCHIVE`
- current output root: `results/isoinspector_task_archive_lmstudio`

Current baseline already available in the repository:

- single-file PDF/Markdown indexing
- recursive Markdown indexing
- LM Studio / OpenAI-compatible local inference support
- real ISOInspector archive outputs without raw node text

Execution note:

- the existing output root is sufficient to start catalog and retrieval prototyping now
- Phase 1 still must be completed to harden indexing semantics before wider rollout

Release target:

- first usable release stops after Phase 3 if node-level JSON retrieval is stable
- default retrieval optimizes for precision and predictable top-N output, not exhaustive recall
- default `top-k` is `7` unless explicitly overridden

Recommended next task:

- `PH5-T2` Add the local API or MCP shim over the stabilized retrieval contract

---

## Phase 1: Stabilize Indexing Foundations

#### PH1-T1: Define Output And Manifest Contract
- **Status:** Not Started
- **Description:** Define the canonical on-disk contract for indexed, skipped, and failed files so resume logic and downstream tooling share the same assumptions.
- **Priority:** P0
- **Dependencies:** None
- **Parallelizable:** no
- **Acceptance Criteria:**
  - Manifest semantics for `indexed`, `skipped`, and `failed` are documented in code and spec text.
  - Output file existence is explicitly treated as the source of truth for resume behavior.
  - The contract is compatible with the current `results/isoinspector_task_archive_lmstudio` output root.

#### PH1-T2: Harden Resume Behavior
- **Status:** Not Started
- **Description:** Make `--resume` deterministic for interrupted batch indexing runs without overwriting completed output JSON files.
- **Priority:** P0
- **Dependencies:** PH1-T1
- **Parallelizable:** no
- **Acceptance Criteria:**
  - Interrupted runs continue from existing output files without re-indexing completed inputs.
  - Manifest updates are flushed incrementally during long runs.
  - Final indexed/skipped/failed counts are reproducible on a sample corpus.

#### PH1-T3: Define Indexing Profiles
- **Status:** Not Started
- **Description:** Document the supported indexing profiles for lightweight structure retrieval and later answer-ready text extraction.
- **Priority:** P1
- **Dependencies:** PH1-T1
- **Parallelizable:** yes
- **Acceptance Criteria:**
  - Profiles for `structure`, `summary`, and `text` indexing are documented.
  - The `text` profile is defined as enriching existing JSON outputs rather than requiring a separate output root.
  - Operator guidance explains when re-indexing is required to obtain raw node text.

---

## Phase 2: Build Catalog Layer

#### PH2-T1: Implement Catalog Schema And Builder
- **Status:** ✅ Complete
- **Description:** Build the catalog model and scanner that convert many `*_structure.json` files into a deterministic per-project catalog artifact.
- **Priority:** P0
- **Dependencies:** None
- **Parallelizable:** yes
- **Acceptance Criteria:**
  - Each catalog record includes source path, output path, project/output-root identifier, document name, relative directory, and provenance metadata.
  - Each catalog record captures freshness metadata, summary presence, and node-text presence.
  - Duplicate basenames in different folders remain uniquely addressable in the catalog.

#### PH2-T2: Add Classification And Freshness Heuristics
- **Status:** ✅ Complete
- **Description:** Classify archive files by document type and derive document freshness so candidate selection can stay precise on noisy corpora.
- **Priority:** P0
- **Dependencies:** PH2-T1
- **Parallelizable:** yes
- **Acceptance Criteria:**
  - Catalog records are classified into at least `task`, `blocked`, `summary`, `next_tasks`, and `generic`.
  - Default ranking priority is `task > blocked > summary`.
  - `next_tasks` records are excluded or strongly de-prioritized by default.
  - Explicit in-document dates are preferred for freshness; filesystem creation metadata is the fallback.

#### PH2-T3: Build Catalog CLI
- **Status:** ✅ Complete
- **Description:** Expose a CLI command that scans an output root and writes a separate per-project `catalog.json` artifact.
- **Priority:** P0
- **Dependencies:** PH2-T1, PH2-T2
- **Parallelizable:** yes
- **Acceptance Criteria:**
  - One CLI command rebuilds the catalog from disk without manual edits.
  - The catalog artifact is stored separately from the index JSON files.
  - The command works against the real `isoinspector_task_archive_lmstudio` output root.

---

## Phase 3: Build Retrieval CLI

#### PH3-T1: Define Retrieval Result Schema
- **Status:** ✅ Complete
- **Description:** Define the deterministic JSON contract used by CLI output first and future API/MCP wrappers later.
- **Priority:** P0
- **Dependencies:** PH2-T1
- **Parallelizable:** yes
- **Acceptance Criteria:**
  - Default output is a flat `selected_nodes` list.
  - Optional grouped-by-document output is supported without changing core field names.
  - Schema includes `query`, `corpus_root`, `catalog_path`, candidate documents, selected documents, selected nodes, extracted context, and machine-readable errors.

#### PH3-T2: Implement Candidate Selection
- **Status:** ✅ Complete
- **Description:** Add cheap first-stage narrowing over the catalog before any LM-driven tree search runs.
- **Priority:** P0
- **Dependencies:** PH2-T1, PH2-T2, PH3-T1
- **Parallelizable:** yes
- **Acceptance Criteria:**
  - Candidate selection supports lexical, path-prefix, and document-type filtering.
  - Ranking uses freshness and document type as first-class signals.
  - Default `top-k` is `7` and is tuned for low false positives over maximal recall.
  - Sample ISOInspector queries reduce the corpus to a bounded candidate set before LM calls.

#### PH3-T3: Implement Local Tree Search
- **Status:** ✅ Complete
- **Description:** Run PageIndex tree search over selected candidates through LM Studio and normalize node-level results.
- **Priority:** P0
- **Dependencies:** PH3-T1, PH3-T2
- **Parallelizable:** no
- **Acceptance Criteria:**
  - Retrieval returns source path, output path, node ID, title, summary when available, and line number when available.
  - Reasoning output is optional and off by default.
  - LM failures return explicit JSON errors rather than partial unstructured output.

#### PH3-T4: Build Search CLI Wrapper
- **Status:** ✅ Complete
- **Description:** Expose the retrieval flow as a stable local CLI for agent consumption.
- **Priority:** P0
- **Dependencies:** PH3-T2, PH3-T3
- **Parallelizable:** no
- **Acceptance Criteria:**
  - CLI emits JSON by default.
  - CLI supports `--query`, `--catalog`, `--top-k`, `--type`, `--path-prefix`, `--dry-run-candidates`, and `--with-reasoning`.
  - CLI can optionally group results by document while keeping flat node results as the default mode.

---

## Phase 4: Build Context Extraction

#### PH4-T1: Implement Node Lookup Helpers
- **Status:** ✅ Complete
- **Description:** Resolve retrieved node IDs back to human-usable metadata from the indexed JSON outputs.
- **Priority:** P1
- **Dependencies:** PH3-T1
- **Parallelizable:** yes
- **Acceptance Criteria:**
  - Node lookup returns title, summary, source path, output path, and line number when present.
  - Node lookup works against the current text-absent ISOInspector outputs.
  - Missing node text is reported explicitly instead of failing silently.

#### PH4-T2: Implement Answer-Ready Extraction Mode
- **Status:** ✅ Complete
- **Description:** Add a higher-level retrieval mode that returns compact evidence packages when node text exists.
- **Priority:** P1
- **Dependencies:** PH3-T4, PH4-T1
- **Parallelizable:** no
- **Acceptance Criteria:**
  - Retrieval can emit answer-ready evidence blocks with citations when node text is available.
  - The command fails explicitly when answer-ready mode requires raw text that is absent from the index.
  - The output remains deterministic JSON.

---

## Phase 5: Prepare Agent Integration

#### PH5-T1: Define Local Tool Contract
- **Status:** ✅ Complete
- **Description:** Document the stable search and context operations that future agent wrappers must call.
- **Priority:** P1
- **Dependencies:** PH3-T1, PH3-T4, PH4-T1
- **Parallelizable:** yes
- **Acceptance Criteria:**
  - Search and context operations have explicit input and output contracts.
  - Contracts reuse the CLI schema instead of creating a second format.
  - Agent-facing error behavior is documented in machine-readable terms.

#### PH5-T2: Add Local API Or MCP Shim
- **Status:** Not Started
- **Description:** Wrap the retrieval core in a local service surface only after the CLI and schema have stabilized.
- **Priority:** P2
- **Dependencies:** PH5-T1, PH3-T4, PH4-T1
- **Parallelizable:** yes
- **Acceptance Criteria:**
  - The wrapper calls the same underlying retrieval and context functions as the CLI.
  - No business logic is duplicated into the wrapper layer.
  - An agent can query the local corpus through the wrapper without custom response parsing hacks.

---

## Acceptance Queries For MVP Validation

Use queries like these when validating Phase 3:

- `What is BoxHeader and how is it related to BoxParserRegistry`
- `Why was ParseTree added in ISOInspectorKit`
- `What ValidationIssue types are used in ParseTreeStore and what are they for`

MVP is ready when an agent working against the ISOInspector codebase can use one CLI command to find the specification files and nodes where the relevant concepts are defined.

---

## Task Status Legend

- **Not Started** — Task is defined but has not begun
- **INPROGRESS** — Task is currently active
- **✅ Complete** — Task is finished
