from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

from .retrieval_schema import ExtractedContext, RetrievalDocument, RetrievalError, RetrievalNode


@dataclass(frozen=True, slots=True)
class NodeContext:
    record_id: str
    node_id: str
    title: str
    source_path: str
    output_path: str
    summary: str | None = None
    line_number: int | None = None
    text: str | None = None
    text_available: bool = False

    def to_retrieval_node(self, *, reasoning: str | None = None) -> RetrievalNode:
        return RetrievalNode(
            record_id=self.record_id,
            node_id=self.node_id,
            title=self.title,
            source_path=self.source_path,
            output_path=self.output_path,
            summary=self.summary,
            line_number=self.line_number,
            reasoning=reasoning,
        )

    def to_dict(self) -> dict[str, Any]:
        payload = {
            "record_id": self.record_id,
            "node_id": self.node_id,
            "title": self.title,
            "source_path": self.source_path,
            "output_path": self.output_path,
            "summary": self.summary,
            "line_number": self.line_number,
            "text": self.text,
            "text_available": self.text_available,
        }
        return {key: value for key, value in payload.items() if value is not None}

    def to_extracted_context(self) -> ExtractedContext | None:
        if self.text is None:
            return None
        return ExtractedContext(
            record_id=self.record_id,
            node_id=self.node_id,
            text=self.text,
            citation=_citation_for_context(self),
        )


def load_structure_payload(output_path: str | Path) -> dict[str, Any]:
    return json.loads(Path(output_path).expanduser().resolve().read_text(encoding="utf-8"))


def flatten_structure_nodes(structure: Any) -> list[dict[str, Any]]:
    flattened: list[dict[str, Any]] = []
    if isinstance(structure, list):
        for node in structure:
            flattened.extend(flatten_structure_nodes(node))
        return flattened

    if not isinstance(structure, dict):
        return flattened

    node_id = structure.get("node_id")
    if isinstance(node_id, str):
        flattened.append(
            {
                "node_id": node_id,
                "title": _normalized_title(structure, node_id),
                "summary": _normalized_summary(structure),
                "line_number": _normalized_line_number(structure.get("line_num")),
            }
        )

    children = structure.get("nodes")
    if isinstance(children, list):
        for child in children:
            flattened.extend(flatten_structure_nodes(child))
    return flattened


def lookup_document_node(
    document: RetrievalDocument,
    node_id: str,
    *,
    structure_payload: dict[str, Any] | None = None,
) -> NodeContext:
    payload = structure_payload or load_structure_payload(document.output_path)
    return _lookup_node_context(
        record_id=document.record_id,
        node_id=node_id,
        source_path=document.source_path,
        output_path=document.output_path,
        structure_payload=payload,
    )


def lookup_selected_node(
    node: RetrievalNode,
    *,
    structure_payload: dict[str, Any] | None = None,
) -> NodeContext:
    payload = structure_payload or load_structure_payload(node.output_path)
    return _lookup_node_context(
        record_id=node.record_id,
        node_id=node.node_id,
        source_path=node.source_path,
        output_path=node.output_path,
        structure_payload=payload,
    )


def resolve_selected_node_contexts(
    selected_nodes: Iterable[RetrievalNode],
    *,
    require_text: bool = False,
) -> tuple[list[NodeContext], list[RetrievalError]]:
    payload_cache: dict[str, dict[str, Any]] = {}
    resolved_contexts: list[NodeContext] = []
    errors: list[RetrievalError] = []

    for node in selected_nodes:
        try:
            cache_key = str(Path(node.output_path).expanduser().resolve())
            structure_payload = payload_cache.get(cache_key)
            if structure_payload is None:
                structure_payload = load_structure_payload(node.output_path)
                payload_cache[cache_key] = structure_payload
            context = lookup_selected_node(node, structure_payload=structure_payload)
        except Exception as exc:
            errors.append(
                RetrievalError(
                    code="node_lookup_failed",
                    message=f"Failed to resolve node metadata for {node.record_id}:{node.node_id}",
                    details={
                        "record_id": node.record_id,
                        "node_id": node.node_id,
                        "output_path": node.output_path,
                        "error": str(exc),
                    },
                )
            )
            continue

        resolved_contexts.append(context)
        if require_text and not context.text_available:
            errors.append(
                RetrievalError(
                    code="node_text_missing",
                    message=f"Node text is unavailable for {node.record_id}:{node.node_id}",
                    details={
                        "record_id": node.record_id,
                        "node_id": node.node_id,
                        "output_path": node.output_path,
                    },
                )
            )

    return resolved_contexts, errors


def build_extracted_context(
    selected_nodes: Iterable[RetrievalNode],
    *,
    require_text: bool = True,
) -> tuple[list[ExtractedContext], list[RetrievalError]]:
    resolved_contexts, errors = resolve_selected_node_contexts(
        selected_nodes,
        require_text=require_text,
    )
    if require_text and errors:
        return [], errors

    extracted_context = [
        context.to_extracted_context()
        for context in resolved_contexts
        if context.to_extracted_context() is not None
    ]
    return extracted_context, errors


def _lookup_node_context(
    *,
    record_id: str,
    node_id: str,
    source_path: str,
    output_path: str,
    structure_payload: dict[str, Any],
) -> NodeContext:
    node_payload = _find_node_payload(structure_payload.get("structure"), node_id)
    if node_payload is None:
        raise KeyError(f"Node {node_id} not found in {output_path}")

    text = _normalized_text(node_payload.get("text"))
    return NodeContext(
        record_id=record_id,
        node_id=node_id,
        title=_normalized_title(node_payload, node_id),
        source_path=source_path,
        output_path=output_path,
        summary=_normalized_summary(node_payload),
        line_number=_normalized_line_number(node_payload.get("line_num")),
        text=text,
        text_available=text is not None,
    )


def _find_node_payload(structure: Any, node_id: str) -> dict[str, Any] | None:
    if isinstance(structure, list):
        for node in structure:
            match = _find_node_payload(node, node_id)
            if match is not None:
                return match
        return None

    if not isinstance(structure, dict):
        return None

    if structure.get("node_id") == node_id:
        return structure

    children = structure.get("nodes")
    if isinstance(children, list):
        for child in children:
            match = _find_node_payload(child, node_id)
            if match is not None:
                return match
    return None


def _normalized_title(node_payload: dict[str, Any], fallback_node_id: str) -> str:
    title = node_payload.get("title")
    return title if isinstance(title, str) and title else fallback_node_id


def _normalized_summary(node_payload: dict[str, Any]) -> str | None:
    for key in ("summary", "prefix_summary"):
        value = node_payload.get(key)
        if isinstance(value, str):
            summary = value.strip()
            if summary:
                return summary
    return None


def _normalized_line_number(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float) and value.is_integer():
        return int(value)
    return None


def _normalized_text(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    text = value.strip()
    return text or None


def _citation_for_context(context: NodeContext) -> str:
    source_name = Path(context.source_path).name if context.source_path else Path(context.output_path).name
    if context.line_number is not None:
        return f"{source_name}:{context.line_number}"
    return source_name
