from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

RETRIEVAL_SCHEMA_VERSION = "1.0"


@dataclass(frozen=True, slots=True)
class RetrievalDocument:
    record_id: str
    document_name: str
    document_type: str
    source_path: str
    output_path: str
    source_rel_path: str
    output_rel_path: str
    freshness_timestamp: str | None = None
    ranking_score: float | None = None

    def to_dict(self) -> dict[str, Any]:
        payload = {
            "record_id": self.record_id,
            "document_name": self.document_name,
            "document_type": self.document_type,
            "source_path": self.source_path,
            "output_path": self.output_path,
            "source_rel_path": self.source_rel_path,
            "output_rel_path": self.output_rel_path,
            "freshness_timestamp": self.freshness_timestamp,
            "ranking_score": self.ranking_score,
        }
        return {key: value for key, value in payload.items() if value is not None}


@dataclass(frozen=True, slots=True)
class RetrievalNode:
    record_id: str
    node_id: str
    title: str
    source_path: str
    output_path: str
    summary: str | None = None
    line_number: int | None = None
    reasoning: str | None = None

    def to_dict(self, *, include_reasoning: bool = False) -> dict[str, Any]:
        payload = {
            "record_id": self.record_id,
            "node_id": self.node_id,
            "title": self.title,
            "source_path": self.source_path,
            "output_path": self.output_path,
            "summary": self.summary,
            "line_number": self.line_number,
        }
        if include_reasoning and self.reasoning is not None:
            payload["reasoning"] = self.reasoning
        return {key: value for key, value in payload.items() if value is not None}


@dataclass(frozen=True, slots=True)
class ExtractedContext:
    record_id: str
    node_id: str
    text: str
    citation: str | None = None

    def to_dict(self) -> dict[str, Any]:
        payload = {
            "record_id": self.record_id,
            "node_id": self.node_id,
            "text": self.text,
            "citation": self.citation,
        }
        return {key: value for key, value in payload.items() if value is not None}


@dataclass(frozen=True, slots=True)
class RetrievalError:
    code: str
    message: str
    details: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        payload = {
            "code": self.code,
            "message": self.message,
            "details": self.details,
        }
        return {key: value for key, value in payload.items() if value is not None}


@dataclass(frozen=True, slots=True)
class RetrievalResult:
    query: str
    corpus_root: str
    catalog_path: str
    candidate_documents: list[RetrievalDocument] = field(default_factory=list)
    selected_documents: list[RetrievalDocument] = field(default_factory=list)
    selected_nodes: list[RetrievalNode] = field(default_factory=list)
    extracted_context: list[ExtractedContext] = field(default_factory=list)
    errors: list[RetrievalError] = field(default_factory=list)
    schema_version: str = RETRIEVAL_SCHEMA_VERSION

    def to_dict(
        self,
        *,
        group_by_document: bool = False,
        include_reasoning: bool = False,
    ) -> dict[str, Any]:
        payload = {
            "schema_version": self.schema_version,
            "query": self.query,
            "corpus_root": self.corpus_root,
            "catalog_path": self.catalog_path,
            "candidate_documents": [doc.to_dict() for doc in self.candidate_documents],
            "selected_documents": [doc.to_dict() for doc in self.selected_documents],
            "selected_nodes": [
                node.to_dict(include_reasoning=include_reasoning) for node in self.selected_nodes
            ],
            "extracted_context": [context.to_dict() for context in self.extracted_context],
            "errors": [error.to_dict() for error in self.errors],
        }
        if group_by_document:
            payload["grouped_documents"] = self._grouped_documents(
                include_reasoning=include_reasoning
            )
        return payload

    def _grouped_documents(self, *, include_reasoning: bool) -> list[dict[str, Any]]:
        nodes_by_record_id: dict[str, list[dict[str, Any]]] = {}
        for node in self.selected_nodes:
            nodes_by_record_id.setdefault(node.record_id, []).append(
                node.to_dict(include_reasoning=include_reasoning)
            )

        grouped_documents: list[dict[str, Any]] = []
        for document in self.selected_documents:
            grouped_documents.append(
                {
                    "document": document.to_dict(),
                    "selected_nodes": nodes_by_record_id.get(document.record_id, []),
                }
            )
        return grouped_documents
