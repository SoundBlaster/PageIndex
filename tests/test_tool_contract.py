from __future__ import annotations

import json
from pathlib import Path

from pageindex.context import NodeContext
from pageindex.local_tree_search import DEFAULT_MAX_NODES_PER_DOCUMENT
from pageindex.retrieval_schema import RetrievalNode
from pageindex.tool_contract import (
    CONTEXT_OPERATION_ERROR_CODES,
    SEARCH_OPERATION_ERROR_CODES,
    ContextToolRequest,
    SearchToolRequest,
    error_code_catalog,
    run_context_tool,
    run_search_tool,
)


def test_run_search_tool_reuses_retrieval_result_shape(tmp_path: Path):
    catalog_path = _write_catalog(tmp_path)
    request = SearchToolRequest(
        query="parse tree",
        catalog=catalog_path,
        model="stub-model",
        include_reasoning=True,
    )

    result = run_search_tool(
        request,
        llm_client=lambda *, model, prompt: json.dumps(
            {
                "selected_node_ids": ["0001"],
                "reasoning_by_node": {"0001": "title matches"},
            }
        ),
    )

    payload = result.to_dict(include_reasoning=True)

    assert payload["query"] == "parse tree"
    assert payload["selected_nodes"][0]["node_id"] == "0001"
    assert payload["selected_nodes"][0]["reasoning"] == "title matches"


def test_run_context_tool_returns_node_context_and_missing_text_error(tmp_path: Path):
    output_path = tmp_path / "ParseTree_structure.json"
    output_path.write_text(
        json.dumps(
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
            }
        ),
        encoding="utf-8",
    )
    request = ContextToolRequest(
        selected_nodes=(
            RetrievalNode(
                record_id="demo:task",
                node_id="0001",
                title="ParseTree Overview",
                source_path="/tmp/TASK_ParseTree.md",
                output_path=str(output_path),
            ),
        ),
        require_text=True,
    )

    contexts, errors = run_context_tool(request)

    assert contexts == [
        NodeContext(
            record_id="demo:task",
            node_id="0001",
            title="ParseTree Overview",
            source_path="/tmp/TASK_ParseTree.md",
            output_path=str(output_path),
            summary="Overview",
            line_number=3,
            text=None,
            text_available=False,
        )
    ]
    assert [error.code for error in errors] == ["node_text_missing"]


def test_tool_contract_defaults_and_error_catalog_match_existing_surfaces():
    request = SearchToolRequest(query="q", catalog="/tmp/catalog.json", model="stub-model")

    assert request.top_k == 7
    assert request.max_nodes_per_document == DEFAULT_MAX_NODES_PER_DOCUMENT
    assert request.document_types == ()
    assert SEARCH_OPERATION_ERROR_CODES == error_code_catalog()["search"]
    assert CONTEXT_OPERATION_ERROR_CODES == error_code_catalog()["context"]


def _write_catalog(tmp_path: Path) -> Path:
    output_path = tmp_path / "ParseTree_structure.json"
    output_path.write_text(
        json.dumps(
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
            }
        ),
        encoding="utf-8",
    )

    catalog_path = tmp_path / "catalog.json"
    catalog_path.write_text(
        json.dumps(
            {
                "schema_version": "1.0",
                "project_id": "demo",
                "input_root": str((tmp_path / "input").resolve()),
                "output_root": str((tmp_path / "output").resolve()),
                "records": [
                    {
                        "record_id": "demo:task",
                        "document_name": "ParseTree Task",
                        "document_type": "task",
                        "source_path": "/tmp/TASK_ParseTree.md",
                        "output_path": str(output_path),
                        "source_rel_path": "TASK_ARCHIVE/TASK_ParseTree.md",
                        "output_rel_path": output_path.name,
                        "relative_directory": "TASK_ARCHIVE",
                        "ranking_signals": {
                            "type_priority": 0,
                            "default_excluded": False,
                            "default_deprioritized": False,
                            "freshness_timestamp": "2026-03-12",
                            "freshness_source": "explicit_date",
                        },
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    return catalog_path
