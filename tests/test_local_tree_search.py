from __future__ import annotations

import json
from pathlib import Path

from pageindex.local_tree_search import search_selected_documents
from pageindex.retrieval_schema import RetrievalDocument


def test_local_tree_search_returns_selected_nodes_without_reasoning_by_default(tmp_path: Path):
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
    candidate = _candidate_document(output_path)

    result = search_selected_documents(
        "validation issue",
        [candidate],
        model="local-model",
        llm_client=lambda *, model, prompt: json.dumps(
            {
                "selected_node_ids": ["0002"],
                "reasoning_by_node": {"0002": "summary matches the query"},
            }
        ),
    )

    payload = result.to_dict()

    assert [document.record_id for document in result.selected_documents] == [candidate.record_id]
    assert payload["selected_nodes"] == [
        {
            "record_id": candidate.record_id,
            "node_id": "0002",
            "title": "ValidationIssue Types",
            "source_path": candidate.source_path,
            "output_path": candidate.output_path,
            "summary": "Explains the ValidationIssue types",
            "line_number": 8,
        }
    ]


def test_local_tree_search_includes_reasoning_when_requested(tmp_path: Path):
    output_path = _write_structure(
        tmp_path / "BoxHeader_structure.json",
        {
            "doc_name": "BoxHeader",
            "structure": [
                {
                    "title": "BoxHeader",
                    "node_id": "0001",
                    "summary": "Defines BoxHeader",
                    "line_num": 12,
                    "nodes": [],
                }
            ],
        },
    )
    candidate = _candidate_document(output_path)

    result = search_selected_documents(
        "box header",
        [candidate],
        model="local-model",
        llm_client=lambda *, model, prompt: json.dumps(
            {
                "selected_node_ids": ["0001"],
                "reasoning_by_node": {"0001": "title directly matches the query"},
            }
        ),
        include_reasoning=True,
    )

    payload = result.to_dict(include_reasoning=True)

    assert payload["selected_nodes"][0]["reasoning"] == "title directly matches the query"


def test_local_tree_search_returns_invalid_response_error(tmp_path: Path):
    output_path = _write_structure(
        tmp_path / "Broken_structure.json",
        {
            "doc_name": "Broken",
            "structure": [
                {"title": "Broken", "node_id": "0001", "summary": "Broken", "line_num": 1, "nodes": []}
            ],
        },
    )
    candidate = _candidate_document(output_path)

    result = search_selected_documents(
        "broken",
        [candidate],
        model="local-model",
        llm_client=lambda *, model, prompt: "not json",
    )

    assert result.selected_nodes == []
    assert result.errors[0].code == "invalid_lm_response"


def test_local_tree_search_returns_document_load_error_for_missing_payload(tmp_path: Path):
    missing_output = tmp_path / "missing_structure.json"
    candidate = _candidate_document(missing_output)

    result = search_selected_documents(
        "missing",
        [candidate],
        model="local-model",
        llm_client=lambda *, model, prompt: json.dumps({"selected_node_ids": []}),
    )

    assert result.selected_nodes == []
    assert result.errors[0].code == "document_load_failed"


def test_local_tree_search_returns_lm_unavailable_error(tmp_path: Path):
    output_path = _write_structure(
        tmp_path / "Unavailable_structure.json",
        {
            "doc_name": "Unavailable",
            "structure": [
                {"title": "Unavailable", "node_id": "0001", "summary": "Unavailable", "line_num": 1, "nodes": []}
            ],
        },
    )
    candidate = _candidate_document(output_path)

    def _failing_client(*, model: str, prompt: str) -> str:
        raise RuntimeError("LM Studio offline")

    result = search_selected_documents(
        "unavailable",
        [candidate],
        model="local-model",
        llm_client=_failing_client,
    )

    assert result.selected_nodes == []
    assert result.errors[0].code == "lm_unavailable"


def _candidate_document(output_path: Path) -> RetrievalDocument:
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


def _write_structure(path: Path, payload: dict[str, object]) -> Path:
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path
