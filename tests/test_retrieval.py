from __future__ import annotations

import json
from pathlib import Path

from pageindex.retrieval import search_catalog


def test_search_catalog_supports_dry_run_candidates(tmp_path: Path):
    catalog_path = _write_catalog(
        tmp_path,
        [
            _record(
                record_id="demo:task",
                document_name="ParseTree Task",
                document_type="task",
                source_rel_path="TASK_ARCHIVE/TASK_ParseTree.md",
                output_path=tmp_path / "ParseTree_structure.json",
            ),
            _record(
                record_id="demo:summary",
                document_name="ParseTree Summary",
                document_type="summary",
                source_rel_path="reports/ParseTree_Summary.md",
                output_path=tmp_path / "ParseTree_Summary_structure.json",
                type_priority=2,
            ),
        ],
    )

    result = search_catalog(
        "parse tree",
        catalog_path,
        model="stub-model",
        dry_run_candidates=True,
    )

    assert [document.record_id for document in result.candidate_documents] == [
        "demo:task",
        "demo:summary",
    ]
    assert result.selected_documents == []
    assert result.selected_nodes == []


def test_search_catalog_runs_full_retrieval_with_stub_model(tmp_path: Path):
    structure_path = tmp_path / "ParseTree_structure.json"
    structure_path.write_text(
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
    catalog_path = _write_catalog(
        tmp_path,
        [
            _record(
                record_id="demo:task",
                document_name="ParseTree Task",
                document_type="task",
                source_rel_path="TASK_ARCHIVE/TASK_ParseTree.md",
                output_path=structure_path,
            )
        ],
    )

    result = search_catalog(
        "parse tree",
        catalog_path,
        model="stub-model",
        llm_client=lambda *, model, prompt: json.dumps({"selected_node_ids": ["0001"]}),
    )

    assert result.corpus_root == str((tmp_path / "input").resolve())
    assert result.catalog_path == str(catalog_path.resolve())
    assert [document.record_id for document in result.selected_documents] == ["demo:task"]
    assert result.selected_nodes[0].node_id == "0001"


def _write_catalog(tmp_path: Path, records: list[dict[str, object]]) -> Path:
    input_root = (tmp_path / "input").resolve()
    output_root = (tmp_path / "output").resolve()
    input_root.mkdir(exist_ok=True)
    output_root.mkdir(exist_ok=True)

    for record in records:
        output_path = Path(str(record["output_path"]))
        output_path.parent.mkdir(parents=True, exist_ok=True)
        if not output_path.exists():
            output_path.write_text(
                json.dumps(
                    {
                        "doc_name": record["document_name"],
                        "structure": [
                            {
                                "title": record["document_name"],
                                "node_id": "0001",
                                "summary": "Summary",
                                "line_num": 1,
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
                "input_root": str(input_root),
                "output_root": str(output_root),
                "records": records,
            }
        ),
        encoding="utf-8",
    )
    return catalog_path


def _record(
    *,
    record_id: str,
    document_name: str,
    document_type: str,
    source_rel_path: str,
    output_path: Path,
    type_priority: int = 0,
) -> dict[str, object]:
    return {
        "record_id": record_id,
        "document_name": document_name,
        "document_type": document_type,
        "source_path": f"/tmp/{Path(source_rel_path).name}",
        "output_path": str(output_path),
        "source_rel_path": source_rel_path,
        "output_rel_path": output_path.name,
        "relative_directory": str(Path(source_rel_path).parent).replace("\\", "/").strip("."),
        "ranking_signals": {
            "type_priority": type_priority,
            "default_excluded": False,
            "default_deprioritized": document_type in {"next_tasks", "generic"},
            "freshness_timestamp": "2026-03-12",
            "freshness_source": "explicit_date",
        },
    }
