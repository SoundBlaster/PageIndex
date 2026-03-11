from __future__ import annotations

import json
from pathlib import Path

from pageindex.candidate_selection import DEFAULT_TOP_K, select_candidate_documents


def test_candidate_selection_ranks_task_before_blocked_and_summary():
    catalog = _catalog_payload(
        _record(
            record_id="demo:task",
            document_name="ParseTree Task",
            document_type="task",
            source_rel_path="TASK_ARCHIVE/TASK_ParseTree.md",
            freshness_timestamp="2026-03-10",
            type_priority=0,
        ),
        _record(
            record_id="demo:blocked",
            document_name="ParseTree Blocked",
            document_type="blocked",
            source_rel_path="blocked/Blocked_ParseTree.md",
            freshness_timestamp="2026-03-11",
            type_priority=1,
        ),
        _record(
            record_id="demo:summary",
            document_name="ParseTree Summary",
            document_type="summary",
            source_rel_path="reports/ParseTree_Summary.md",
            freshness_timestamp="2026-03-12",
            type_priority=2,
        ),
    )

    selected = select_candidate_documents("parse tree", catalog)

    assert [document.record_id for document in selected] == [
        "demo:task",
        "demo:blocked",
        "demo:summary",
    ]


def test_candidate_selection_filters_by_path_prefix_and_document_type():
    catalog = _catalog_payload(
        _record(
            record_id="demo:task",
            document_name="BoxHeader Task",
            document_type="task",
            source_rel_path="TASK_ARCHIVE/specs/TASK_BoxHeader.md",
        ),
        _record(
            record_id="demo:generic",
            document_name="BoxHeader Notes",
            document_type="generic",
            source_rel_path="notes/BoxHeader.md",
            type_priority=3,
        ),
    )

    selected = select_candidate_documents(
        "box header",
        catalog,
        document_types=["task"],
        path_prefix="TASK_ARCHIVE/specs",
    )

    assert [document.record_id for document in selected] == ["demo:task"]


def test_candidate_selection_excludes_next_tasks_by_default():
    catalog = _catalog_payload(
        _record(
            record_id="demo:next",
            document_name="next tasks",
            document_type="next_tasks",
            source_rel_path="planning/next_tasks.md",
            type_priority=99,
            default_excluded=True,
        ),
        _record(
            record_id="demo:task",
            document_name="actual task",
            document_type="task",
            source_rel_path="TASK_ARCHIVE/TASK_Actual.md",
        ),
    )

    selected = select_candidate_documents("task", catalog)

    assert [document.record_id for document in selected] == ["demo:task"]

    included = select_candidate_documents(
        "task",
        catalog,
        document_types=["next_tasks"],
    )
    assert [document.record_id for document in included] == ["demo:next"]


def test_candidate_selection_uses_freshness_to_break_ties():
    catalog = _catalog_payload(
        _record(
            record_id="demo:older",
            document_name="ValidationIssue Task",
            document_type="task",
            source_rel_path="TASK_ARCHIVE/TASK_ValidationIssue_Older.md",
            freshness_timestamp="2026-03-09",
        ),
        _record(
            record_id="demo:newer",
            document_name="ValidationIssue Task",
            document_type="task",
            source_rel_path="TASK_ARCHIVE/TASK_ValidationIssue_Newer.md",
            freshness_timestamp="2026-03-11",
        ),
    )

    selected = select_candidate_documents("validation issue", catalog)

    assert [document.record_id for document in selected] == ["demo:newer", "demo:older"]


def test_candidate_selection_defaults_to_top_seven_and_accepts_catalog_path(tmp_path: Path):
    records = [
        _record(
            record_id=f"demo:task-{index}",
            document_name=f"Query Match {index}",
            document_type="task",
            source_rel_path=f"TASK_ARCHIVE/TASK_Query_Match_{index}.md",
            freshness_timestamp=f"2026-03-{index + 1:02d}",
        )
        for index in range(10)
    ]
    catalog_path = tmp_path / "catalog.json"
    catalog_path.write_text(json.dumps(_catalog_payload(*records)), encoding="utf-8")

    selected = select_candidate_documents("query match", catalog_path)

    assert len(selected) == DEFAULT_TOP_K
    assert selected[0].record_id == "demo:task-9"
    assert selected[-1].record_id == "demo:task-3"


def _catalog_payload(*records: dict[str, object]) -> dict[str, object]:
    return {
        "schema_version": "1.0",
        "project_id": "demo",
        "input_root": "/tmp/input",
        "output_root": "/tmp/output",
        "records": list(records),
    }


def _record(
    *,
    record_id: str,
    document_name: str,
    document_type: str,
    source_rel_path: str,
    freshness_timestamp: str = "2026-03-10",
    type_priority: int = 0,
    default_excluded: bool = False,
) -> dict[str, object]:
    filename = Path(source_rel_path).stem
    return {
        "record_id": record_id,
        "document_name": document_name,
        "document_type": document_type,
        "source_path": f"/tmp/input/{source_rel_path}",
        "output_path": f"/tmp/output/{filename}_structure.json",
        "source_rel_path": source_rel_path,
        "output_rel_path": f"{filename}_structure.json",
        "relative_directory": str(Path(source_rel_path).parent).replace("\\", "/").strip("."),
        "ranking_signals": {
            "type_priority": type_priority,
            "default_excluded": default_excluded,
            "default_deprioritized": document_type in {"next_tasks", "generic"},
            "freshness_timestamp": freshness_timestamp,
            "freshness_source": "explicit_date",
        },
    }
