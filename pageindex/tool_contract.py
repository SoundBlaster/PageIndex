from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from pathlib import Path

from .candidate_selection import DEFAULT_TOP_K
from .context import NodeContext, resolve_selected_node_contexts
from .local_tree_search import DEFAULT_MAX_NODES_PER_DOCUMENT
from .retrieval import search_catalog
from .retrieval_schema import RetrievalError, RetrievalNode, RetrievalResult

SEARCH_OPERATION_ERROR_CODES = (
    "document_load_failed",
    "lm_unavailable",
    "invalid_lm_response",
    "node_lookup_failed",
    "node_text_missing",
)
CONTEXT_OPERATION_ERROR_CODES = (
    "node_lookup_failed",
    "node_text_missing",
)


@dataclass(frozen=True, slots=True)
class SearchToolRequest:
    query: str
    catalog: str | Path | dict[str, object]
    model: str
    top_k: int = DEFAULT_TOP_K
    document_types: tuple[str, ...] = field(default_factory=tuple)
    path_prefix: str | None = None
    dry_run_candidates: bool = False
    include_reasoning: bool = False
    answer_ready: bool = False
    max_nodes_per_document: int = DEFAULT_MAX_NODES_PER_DOCUMENT


@dataclass(frozen=True, slots=True)
class ContextToolRequest:
    selected_nodes: tuple[RetrievalNode, ...] = field(default_factory=tuple)
    require_text: bool = False


def run_search_tool(
    request: SearchToolRequest,
    *,
    llm_client: Callable[..., str] | None = None,
) -> RetrievalResult:
    return search_catalog(
        request.query,
        request.catalog,
        model=request.model,
        top_k=request.top_k,
        document_types=request.document_types,
        path_prefix=request.path_prefix,
        dry_run_candidates=request.dry_run_candidates,
        include_reasoning=request.include_reasoning,
        answer_ready=request.answer_ready,
        max_nodes_per_document=request.max_nodes_per_document,
        llm_client=llm_client,
    )


def run_context_tool(
    request: ContextToolRequest,
) -> tuple[list[NodeContext], list[RetrievalError]]:
    return resolve_selected_node_contexts(
        request.selected_nodes,
        require_text=request.require_text,
    )


def error_code_catalog() -> dict[str, Sequence[str]]:
    return {
        "search": SEARCH_OPERATION_ERROR_CODES,
        "context": CONTEXT_OPERATION_ERROR_CODES,
    }
