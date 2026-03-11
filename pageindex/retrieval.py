from __future__ import annotations

from collections.abc import Callable, Iterable
from pathlib import Path

from .candidate_selection import DEFAULT_TOP_K, load_catalog_payload, select_candidate_documents
from .local_tree_search import DEFAULT_MAX_NODES_PER_DOCUMENT, search_selected_documents
from .retrieval_schema import RetrievalResult


def search_catalog(
    query: str,
    catalog: str | Path | dict[str, object],
    *,
    model: str,
    top_k: int = DEFAULT_TOP_K,
    document_types: Iterable[str] | None = None,
    path_prefix: str | None = None,
    dry_run_candidates: bool = False,
    include_reasoning: bool = False,
    max_nodes_per_document: int = DEFAULT_MAX_NODES_PER_DOCUMENT,
    llm_client: Callable[..., str] | None = None,
) -> RetrievalResult:
    payload = load_catalog_payload(catalog)
    candidate_documents = select_candidate_documents(
        query,
        payload,
        top_k=top_k,
        document_types=document_types,
        path_prefix=path_prefix,
    )

    corpus_root = str(payload.get("input_root", ""))
    catalog_path = _resolved_catalog_path(catalog)
    if dry_run_candidates:
        return RetrievalResult(
            query=query,
            corpus_root=corpus_root,
            catalog_path=catalog_path,
            candidate_documents=candidate_documents,
        )

    return search_selected_documents(
        query,
        candidate_documents,
        model=model,
        llm_client=llm_client,
        max_nodes_per_document=max_nodes_per_document,
        include_reasoning=include_reasoning,
        corpus_root=corpus_root,
        catalog_path=catalog_path,
    )


def _resolved_catalog_path(catalog: str | Path | dict[str, object]) -> str:
    if isinstance(catalog, dict):
        return str(catalog.get("catalog_path", ""))
    return str(Path(catalog).expanduser().resolve())
