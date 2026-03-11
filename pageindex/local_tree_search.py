from __future__ import annotations

from collections.abc import Callable
import json
from typing import Any

from .context import flatten_structure_nodes, load_structure_payload, lookup_document_node
from .retrieval_schema import RetrievalDocument, RetrievalError, RetrievalNode, RetrievalResult
from .utils import ChatGPT_API, extract_json

DEFAULT_MAX_NODES_PER_DOCUMENT = 3


def search_selected_documents(
    query: str,
    candidate_documents: list[RetrievalDocument],
    *,
    model: str,
    llm_client: Callable[..., str] | None = None,
    max_nodes_per_document: int = DEFAULT_MAX_NODES_PER_DOCUMENT,
    include_reasoning: bool = False,
    corpus_root: str | None = None,
    catalog_path: str | None = None,
) -> RetrievalResult:
    client = llm_client or ChatGPT_API
    selected_documents: list[RetrievalDocument] = []
    selected_nodes: list[RetrievalNode] = []
    errors: list[RetrievalError] = []

    for document in candidate_documents:
        try:
            structure_payload = load_structure_payload(document.output_path)
        except Exception as exc:
            errors.append(
                RetrievalError(
                    code="document_load_failed",
                    message=f"Failed to load structure payload for {document.record_id}",
                    details={
                        "record_id": document.record_id,
                        "output_path": document.output_path,
                        "error": str(exc),
                    },
                )
            )
            continue

        flattened_nodes = flatten_structure_nodes(structure_payload.get("structure"))
        if not flattened_nodes:
            continue

        prompt = _build_tree_search_prompt(
            query=query,
            document=document,
            flattened_nodes=flattened_nodes,
            max_nodes_per_document=max_nodes_per_document,
        )

        try:
            raw_response = client(model=model, prompt=prompt)
        except Exception as exc:
            errors.append(
                RetrievalError(
                    code="lm_unavailable",
                    message=f"Local tree search failed for {document.record_id}",
                    details={
                        "record_id": document.record_id,
                        "output_path": document.output_path,
                        "error": str(exc),
                    },
                )
            )
            continue

        parsed_response = _parse_lm_response(raw_response)
        if parsed_response is None:
            errors.append(
                RetrievalError(
                    code="invalid_lm_response",
                    message=f"Tree search returned invalid JSON for {document.record_id}",
                    details={
                        "record_id": document.record_id,
                        "output_path": document.output_path,
                        "raw_response": raw_response,
                    },
                )
            )
            continue

        document_nodes: list[RetrievalNode] = []
        for node_id in parsed_response["selected_node_ids"][:max_nodes_per_document]:
            try:
                resolved_node = lookup_document_node(
                    document,
                    node_id,
                    structure_payload=structure_payload,
                )
            except KeyError as exc:
                errors.append(
                    RetrievalError(
                        code="node_lookup_failed",
                        message=f"Selected node {node_id} could not be resolved for {document.record_id}",
                        details={
                            "record_id": document.record_id,
                            "node_id": node_id,
                            "output_path": document.output_path,
                            "error": str(exc),
                        },
                    )
                )
                continue
            document_nodes.append(
                resolved_node.to_retrieval_node(
                    reasoning=parsed_response["reasoning_by_node"].get(node_id)
                    if include_reasoning
                    else None,
                )
            )

        if document_nodes:
            selected_documents.append(document)
            selected_nodes.extend(document_nodes)

    return RetrievalResult(
        query=query,
        corpus_root=corpus_root or "",
        catalog_path=catalog_path or "",
        candidate_documents=candidate_documents,
        selected_documents=selected_documents,
        selected_nodes=selected_nodes,
        errors=errors,
    )


def _build_tree_search_prompt(
    *,
    query: str,
    document: RetrievalDocument,
    flattened_nodes: list[dict[str, Any]],
    max_nodes_per_document: int,
) -> str:
    node_listing = json.dumps(flattened_nodes, ensure_ascii=False, indent=2)
    return (
        "You are selecting the most relevant document nodes for a retrieval query.\n"
        f"Query: {query}\n"
        f"Document: {document.document_name}\n"
        f"Document type: {document.document_type}\n"
        f"Select up to {max_nodes_per_document} node IDs from the provided nodes.\n"
        "Prefer nodes whose titles or summaries directly answer the query.\n"
        "Return JSON only in this exact shape:\n"
        '{\n'
        '  "selected_node_ids": ["0001"],\n'
        '  "reasoning_by_node": {"0001": "short reason"}\n'
        '}\n'
        "If nothing is relevant, return an empty selected_node_ids list.\n"
        f"Nodes:\n{node_listing}\n"
    )


def _parse_lm_response(raw_response: str) -> dict[str, Any] | None:
    payload = extract_json(raw_response)
    if not isinstance(payload, dict):
        return None

    selected_node_ids = payload.get("selected_node_ids")
    if not isinstance(selected_node_ids, list) or not all(
        isinstance(node_id, str) for node_id in selected_node_ids
    ):
        return None

    reasoning_by_node = payload.get("reasoning_by_node", {})
    if not isinstance(reasoning_by_node, dict):
        reasoning_by_node = {}

    return {
        "selected_node_ids": selected_node_ids,
        "reasoning_by_node": {
            str(node_id): str(reason)
            for node_id, reason in reasoning_by_node.items()
            if isinstance(node_id, str)
        },
    }
