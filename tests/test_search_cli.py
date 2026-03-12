from __future__ import annotations

from io import StringIO
import json
from pathlib import Path

from pageindex.search_cli import main


def test_search_cli_emits_candidate_json_for_dry_run(tmp_path: Path):
    catalog_path = _write_catalog(tmp_path)
    output = StringIO()

    exit_code = main(
        [
            "--query",
            "parse tree",
            "--catalog",
            str(catalog_path),
            "--dry-run-candidates",
            "--type",
            "task",
        ],
        stdout=output,
    )

    payload = json.loads(output.getvalue())

    assert exit_code == 0
    assert [document["record_id"] for document in payload["candidate_documents"]] == ["demo:task"]
    assert payload["selected_nodes"] == []


def test_search_cli_emits_grouped_json_with_reasoning(tmp_path: Path):
    catalog_path = _write_catalog(tmp_path)
    output = StringIO()

    exit_code = main(
        [
            "--query",
            "parse tree",
            "--catalog",
            str(catalog_path),
            "--with-reasoning",
            "--group-by-document",
        ],
        llm_client=lambda *, model, prompt: json.dumps(
            {
                "selected_node_ids": ["0001"],
                "reasoning_by_node": {"0001": "title matches"},
            }
        ),
        stdout=output,
    )

    payload = json.loads(output.getvalue())

    assert exit_code == 0
    assert payload["selected_nodes"][0]["reasoning"] == "title matches"
    assert payload["grouped_documents"][0]["selected_nodes"][0]["node_id"] == "0001"


def test_search_cli_emits_answer_ready_context_when_requested(tmp_path: Path):
    catalog_path = _write_catalog(tmp_path, include_text=True)
    output = StringIO()

    exit_code = main(
        [
            "--query",
            "parse tree",
            "--catalog",
            str(catalog_path),
            "--answer-ready",
        ],
        llm_client=lambda *, model, prompt: json.dumps({"selected_node_ids": ["0001"]}),
        stdout=output,
    )

    payload = json.loads(output.getvalue())

    assert exit_code == 0
    assert payload["extracted_context"] == [
        {
            "record_id": "demo:task",
            "node_id": "0001",
            "text": "ParseTree preserves hierarchical parsing semantics.",
            "citation": "TASK_ParseTree.md:3",
        }
    ]


def _write_catalog(tmp_path: Path, *, include_text: bool = False) -> Path:
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
                        "text": "ParseTree preserves hierarchical parsing semantics."
                        if include_text
                        else None,
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
