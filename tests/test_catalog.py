from __future__ import annotations

import json
from pathlib import Path

import pytest

from pageindex.catalog import build_catalog, write_catalog


def test_build_catalog_preserves_unique_paths_and_detects_metadata(tmp_path: Path):
    input_root = tmp_path / "input"
    output_root = tmp_path / "output"
    input_root.mkdir()
    output_root.mkdir()

    alpha_source = input_root / "alpha" / "Summary_of_Work.md"
    beta_source = input_root / "beta" / "Summary_of_Work.md"
    loose_source = input_root / "LooseDoc.markdown"

    _write_text(alpha_source, "# Alpha\n")
    _write_text(beta_source, "# Beta\n")
    _write_text(loose_source, "# Loose\n")

    _write_json(alpha_source.with_name("Summary_of_Work_metrics.json"), {"atoms": 1})
    _write_json(beta_source.with_name("Summary_of_Work_metrics.json"), {"atoms": 2})
    _write_json(loose_source.with_name("LooseDoc_metrics.json"), {"atoms": 3})

    alpha_output = output_root / "alpha" / "Summary_of_Work_structure.json"
    beta_output = output_root / "beta" / "Summary_of_Work_structure.json"
    loose_output = output_root / "LooseDoc_structure.json"

    _write_json(
        alpha_output,
        {
            "doc_name": "Summary_of_Work",
            "structure": [
                {
                    "title": "Alpha",
                    "prefix_summary": "overview",
                    "nodes": [],
                }
            ],
        },
    )
    _write_json(
        beta_output,
        {
            "doc_name": "Summary_of_Work",
            "structure": [
                {
                    "title": "Beta",
                    "text": "raw body",
                    "nodes": [],
                }
            ],
        },
    )
    _write_json(
        loose_output,
        {
            "doc_name": "LooseDoc",
            "structure": [
                {
                    "title": "Loose",
                    "summary": "leaf summary",
                    "nodes": [],
                }
            ],
        },
    )

    _write_json(
        output_root / "manifest.json",
        {
            "input_root": str(input_root),
            "output_root": str(output_root),
            "files": [
                {
                    "source": str(beta_source),
                    "output": str(beta_output),
                    "status": "indexed",
                },
                {
                    "source": str(alpha_source),
                    "output": str(alpha_output),
                    "status": "skipped",
                },
            ],
        },
    )

    catalog = build_catalog(output_root)
    payload = catalog.to_dict()
    records = payload["records"]

    assert payload["project_id"] == output_root.name
    assert [record["output_rel_path"] for record in records] == [
        "LooseDoc_structure.json",
        "alpha/Summary_of_Work_structure.json",
        "beta/Summary_of_Work_structure.json",
    ]
    assert len({record["record_id"] for record in records}) == 3

    loose_record, alpha_record, beta_record = records

    assert loose_record["source_rel_path"] == "LooseDoc.markdown"
    assert loose_record["relative_directory"] == ""
    assert loose_record["provenance"]["source_resolution"] == "inferred"
    assert loose_record["document_type"] == "generic"
    assert loose_record["summary_present"] is True
    assert loose_record["node_text_present"] is False

    assert alpha_record["source_rel_path"] == "alpha/Summary_of_Work.md"
    assert alpha_record["relative_directory"] == "alpha"
    assert alpha_record["provenance"]["manifest_status"] == "skipped"
    assert alpha_record["document_type"] == "summary"
    assert alpha_record["summary_present"] is True
    assert alpha_record["node_text_present"] is False

    assert beta_record["source_rel_path"] == "beta/Summary_of_Work.md"
    assert beta_record["relative_directory"] == "beta"
    assert beta_record["provenance"]["manifest_status"] == "indexed"
    assert beta_record["document_type"] == "summary"
    assert beta_record["summary_present"] is False
    assert beta_record["node_text_present"] is True

    for record in records:
        assert record["freshness"]["source"]["modified_at"] is not None
        assert record["freshness"]["output"]["modified_at"] is not None
        assert record["freshness"]["metrics"]["modified_at"] is not None
        assert record["provenance"]["metrics_exists"] is True
        assert record["ranking_signals"]["freshness_timestamp"] is not None
        assert record["ranking_signals"]["freshness_source"] in {
            "filesystem_created_at",
            "filesystem_modified_at",
        }


def test_build_catalog_requires_manifest_or_input_root(tmp_path: Path):
    output_root = tmp_path / "output"
    output_root.mkdir()
    _write_json(
        output_root / "orphan_structure.json",
        {"doc_name": "orphan", "structure": [{"title": "Orphan", "nodes": []}]},
    )

    with pytest.raises(ValueError):
        build_catalog(output_root)


def test_write_catalog_writes_sorted_json(tmp_path: Path):
    input_root = tmp_path / "input"
    output_root = tmp_path / "output"
    input_root.mkdir()
    output_root.mkdir()

    source = input_root / "Doc.md"
    _write_text(source, "# Doc\n")
    _write_json(source.with_name("Doc_metrics.json"), {"atoms": 1})
    _write_json(
        output_root / "Doc_structure.json",
        {"doc_name": "Doc", "structure": [{"title": "Doc", "summary": "s", "nodes": []}]},
    )

    catalog = build_catalog(output_root, input_root=input_root, project_id="demo")
    destination = tmp_path / "catalog.json"

    written_path = write_catalog(catalog, destination)
    persisted = json.loads(written_path.read_text(encoding="utf-8"))

    assert written_path == destination.resolve()
    assert persisted["project_id"] == "demo"
    assert persisted["records"][0]["record_id"] == "demo:Doc_structure.json"


def test_build_catalog_adds_document_type_and_explicit_freshness_ranking(tmp_path: Path):
    input_root = tmp_path / "input"
    output_root = tmp_path / "output"
    input_root.mkdir()
    output_root.mkdir()

    task_source = input_root / "TASK_ARCHIVE" / "TASK_Parser_Fix.md"
    blocked_source = input_root / "blocked" / "Blocked_Parser.md"
    next_source = input_root / "planning" / "next_tasks.md"
    summary_source = input_root / "reports" / "Sprint_Summary.md"

    _write_text(task_source, "# Task\nUpdated 2026-03-10\nOriginal 2026-01-01\n")
    _write_text(blocked_source, "# Blocked\nReviewed on March 4, 2026\n")
    _write_text(next_source, "# Next Tasks\n2026-03-11\n")
    _write_text(summary_source, "# Summary\nNo explicit date here.\n")

    for source in [task_source, blocked_source, next_source, summary_source]:
        _write_json(source.with_name(f"{source.stem}_metrics.json"), {"atoms": 1})
        _write_json(
            output_root / source.relative_to(input_root).with_name(f"{source.stem}_structure.json"),
            {"doc_name": source.stem, "structure": [{"title": source.stem, "nodes": []}]},
        )

    catalog = build_catalog(output_root, input_root=input_root, project_id="demo")
    records = {record["document_type"]: record for record in catalog.to_dict()["records"]}

    assert records["task"]["ranking_signals"]["type_priority"] == 0
    assert records["task"]["ranking_signals"]["freshness_timestamp"] == "2026-03-10"
    assert records["task"]["ranking_signals"]["freshness_source"] == "explicit_date"
    assert records["task"]["provenance"]["explicit_freshness_date"] == "2026-03-10"

    assert records["blocked"]["ranking_signals"]["type_priority"] == 1
    assert records["blocked"]["ranking_signals"]["freshness_timestamp"] == "2026-03-04"

    assert records["summary"]["ranking_signals"]["type_priority"] == 2
    assert records["summary"]["ranking_signals"]["default_excluded"] is False

    assert records["next_tasks"]["ranking_signals"]["type_priority"] == 99
    assert records["next_tasks"]["ranking_signals"]["default_excluded"] is True
    assert records["next_tasks"]["ranking_signals"]["default_deprioritized"] is True

    summary_freshness_source = records["summary"]["ranking_signals"]["freshness_source"]
    assert summary_freshness_source in {"filesystem_created_at", "filesystem_modified_at"}


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
