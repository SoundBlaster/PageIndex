from __future__ import annotations

import json
from pathlib import Path

import pytest

from pageindex.context import (
    build_extracted_context,
    flatten_structure_nodes,
    lookup_document_node,
    resolve_selected_node_contexts,
)
from pageindex.retrieval_schema import RetrievalDocument, RetrievalNode


def test_lookup_document_node_returns_metadata_for_nested_node(tmp_path: Path):
    output_path = _write_structure(
        tmp_path / "ParseTree_structure.json",
        {
            "doc_name": "ParseTree",
            "structure": [
                {
                    "title": "ParseTree Overview",
                    "node_id": "0001",
                    "prefix_summary": "Overview of ParseTree",
                    "line_num": 1,
                    "nodes": [
                        {
                            "title": "ValidationIssue Types",
                            "node_id": "0002",
                            "summary": "Explains the ValidationIssue types",
                            "line_num": 8,
                            "nodes": [],
                        }
                    ],
                }
            ],
        },
    )
    document = _document(output_path)

    context = lookup_document_node(document, "0002")

    assert context.record_id == document.record_id
    assert context.node_id == "0002"
    assert context.title == "ValidationIssue Types"
    assert context.source_path == document.source_path
    assert context.output_path == document.output_path
    assert context.summary == "Explains the ValidationIssue types"
    assert context.line_number == 8
    assert context.text is None
    assert context.text_available is False


def test_resolve_selected_node_contexts_returns_text_when_present(tmp_path: Path):
    output_path = _write_structure(
        tmp_path / "BoxHeader_structure.json",
        {
            "doc_name": "BoxHeader",
            "structure": [
                {
                    "title": "BoxHeader",
                    "node_id": "0001",
                    "summary": "Defines BoxHeader",
                    "text": "BoxHeader is the protocol entry point.",
                    "line_num": 12,
                    "nodes": [],
                }
            ],
        },
    )
    selected_node = _selected_node(output_path, node_id="0001", title="BoxHeader")

    contexts, errors = resolve_selected_node_contexts([selected_node], require_text=True)

    assert errors == []
    assert len(contexts) == 1
    assert contexts[0].text == "BoxHeader is the protocol entry point."
    assert contexts[0].text_available is True
    assert contexts[0].line_number == 12


def test_resolve_selected_node_contexts_reports_missing_text_when_required(tmp_path: Path):
    output_path = _write_structure(
        tmp_path / "ParseTree_structure.json",
        {
            "doc_name": "ParseTree",
            "structure": [
                {
                    "title": "ParseTree Overview",
                    "node_id": "0001",
                    "summary": "Overview",
                    "line_num": 3,
                    "nodes": [],
                }
            ],
        },
    )
    selected_node = _selected_node(output_path, node_id="0001", title="ParseTree Overview")

    contexts, errors = resolve_selected_node_contexts([selected_node], require_text=True)

    assert len(contexts) == 1
    assert contexts[0].summary == "Overview"
    assert contexts[0].text is None
    assert contexts[0].text_available is False
    assert [error.code for error in errors] == ["node_text_missing"]
    assert errors[0].details == {
        "record_id": selected_node.record_id,
        "node_id": "0001",
        "output_path": selected_node.output_path,
    }


def test_flatten_structure_nodes_normalizes_fallback_fields():
    flattened = flatten_structure_nodes(
        [
            "skip me",
            {
                "title": "",
                "node_id": "0001",
                "prefix_summary": "  Prefix summary  ",
                "line_num": 12.0,
                "nodes": [
                    None,
                    {
                        "title": "Child",
                        "node_id": "0002",
                        "summary": "Child summary",
                        "line_num": True,
                        "nodes": [],
                    },
                ],
            },
        ]
    )

    assert flattened == [
        {
            "node_id": "0001",
            "title": "0001",
            "summary": "Prefix summary",
            "line_number": 12,
        },
        {
            "node_id": "0002",
            "title": "Child",
            "summary": "Child summary",
            "line_number": None,
        },
    ]


def test_lookup_document_node_raises_key_error_for_missing_node(tmp_path: Path):
    output_path = _write_structure(
        tmp_path / "Missing_structure.json",
        {
            "doc_name": "Missing",
            "structure": [
                "skip me",
                {
                    "title": "Known Node",
                    "node_id": "0001",
                    "summary": "Known summary",
                    "line_num": 1,
                    "nodes": [],
                },
            ],
        },
    )
    document = _document(output_path)

    with pytest.raises(KeyError):
        lookup_document_node(document, "9999")


def test_resolve_selected_node_contexts_reports_lookup_failure_when_node_is_missing(tmp_path: Path):
    output_path = _write_structure(
        tmp_path / "Missing_structure.json",
        {
            "doc_name": "Missing",
            "structure": [
                {
                    "title": "Known Node",
                    "node_id": "0001",
                    "summary": "Known summary",
                    "line_num": 1,
                    "nodes": [],
                }
            ],
        },
    )
    selected_node = _selected_node(output_path, node_id="9999", title="Unknown")

    contexts, errors = resolve_selected_node_contexts([selected_node], require_text=True)

    assert contexts == []
    assert [error.code for error in errors] == ["node_lookup_failed"]


def test_build_extracted_context_returns_citation_when_text_exists(tmp_path: Path):
    output_path = _write_structure(
        tmp_path / "BoxHeader_structure.json",
        {
            "doc_name": "BoxHeader",
            "structure": [
                {
                    "title": "BoxHeader",
                    "node_id": "0001",
                    "summary": "Defines BoxHeader",
                    "text": "BoxHeader is the protocol entry point.",
                    "line_num": 12,
                    "nodes": [],
                }
            ],
        },
    )
    selected_node = _selected_node(output_path, node_id="0001", title="BoxHeader")

    extracted_context, errors = build_extracted_context([selected_node], require_text=True)

    assert errors == []
    assert [context.to_dict() for context in extracted_context] == [
        {
            "record_id": selected_node.record_id,
            "node_id": "0001",
            "text": "BoxHeader is the protocol entry point.",
            "citation": "BoxHeader.md:12",
        }
    ]


def _document(output_path: Path) -> RetrievalDocument:
    stem = output_path.name[: -len("_structure.json")]
    return RetrievalDocument(
        record_id=f"demo:{stem}",
        document_name=stem,
        document_type="task",
        source_path=f"/tmp/{stem}.md",
        output_path=str(output_path),
        source_rel_path=f"{stem}.md",
        output_rel_path=output_path.name,
        freshness_timestamp="2026-03-12",
    )


def _selected_node(output_path: Path, *, node_id: str, title: str) -> RetrievalNode:
    stem = output_path.name[: -len("_structure.json")]
    return RetrievalNode(
        record_id=f"demo:{stem}",
        node_id=node_id,
        title=title,
        source_path=f"/tmp/{stem}.md",
        output_path=str(output_path),
    )


def _write_structure(path: Path, payload: dict[str, object]) -> Path:
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path
