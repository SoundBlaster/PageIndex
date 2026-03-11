from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
import re
from typing import Any, Iterable

CATALOG_SCHEMA_VERSION = "1.0"
_MONTH_NAME_PATTERN = (
    r"January|February|March|April|May|June|July|August|September|October|November|December"
)
_TYPE_PRIORITIES = {
    "task": 0,
    "blocked": 1,
    "summary": 2,
    "generic": 3,
    "next_tasks": 99,
}


@dataclass(frozen=True, slots=True)
class FileFreshness:
    created_at: str | None
    modified_at: str | None

    def to_dict(self) -> dict[str, str | None]:
        return {
            "created_at": self.created_at,
            "modified_at": self.modified_at,
        }


@dataclass(frozen=True, slots=True)
class CatalogRecord:
    record_id: str
    project_id: str
    document_name: str
    document_type: str
    relative_directory: str
    source_path: str
    output_path: str
    source_rel_path: str
    output_rel_path: str
    summary_present: bool
    node_text_present: bool
    freshness: dict[str, dict[str, str | None]]
    ranking_signals: dict[str, Any]
    provenance: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "record_id": self.record_id,
            "project_id": self.project_id,
            "document_name": self.document_name,
            "document_type": self.document_type,
            "relative_directory": self.relative_directory,
            "source_path": self.source_path,
            "output_path": self.output_path,
            "source_rel_path": self.source_rel_path,
            "output_rel_path": self.output_rel_path,
            "summary_present": self.summary_present,
            "node_text_present": self.node_text_present,
            "freshness": self.freshness,
            "ranking_signals": self.ranking_signals,
            "provenance": self.provenance,
        }


@dataclass(frozen=True, slots=True)
class CatalogArtifact:
    schema_version: str
    project_id: str
    input_root: str
    output_root: str
    manifest_path: str | None
    records: list[CatalogRecord]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "project_id": self.project_id,
            "input_root": self.input_root,
            "output_root": self.output_root,
            "manifest_path": self.manifest_path,
            "records": [record.to_dict() for record in self.records],
        }


def build_catalog(
    output_root: str | Path,
    *,
    input_root: str | Path | None = None,
    project_id: str | None = None,
    manifest_path: str | Path | None = None,
) -> CatalogArtifact:
    resolved_output_root = Path(output_root).expanduser().resolve()
    resolved_manifest_path = _resolve_manifest_path(resolved_output_root, manifest_path)
    manifest = _load_manifest(resolved_manifest_path) if resolved_manifest_path else None

    resolved_input_root = _resolve_input_root(input_root, manifest, resolved_manifest_path)
    if resolved_input_root is None:
        raise ValueError("Catalog building requires either manifest.json or an explicit input_root.")

    resolved_project_id = project_id or resolved_output_root.name
    manifest_entries = _index_manifest_entries(manifest, resolved_manifest_path)

    records: list[CatalogRecord] = []
    for structure_path in sorted(resolved_output_root.rglob("*_structure.json")):
        output_rel_path = structure_path.relative_to(resolved_output_root).as_posix()
        manifest_entry = manifest_entries.get(str(structure_path.resolve()))

        source_path, source_resolution = _resolve_source_path(
            input_root=resolved_input_root,
            output_root=resolved_output_root,
            structure_path=structure_path,
            manifest_entry=manifest_entry,
            manifest_path=resolved_manifest_path,
        )
        source_rel_path = _relative_path_or_name(source_path, resolved_input_root)
        relative_directory = _relative_directory(source_rel_path)

        structure_payload = json.loads(structure_path.read_text(encoding="utf-8"))
        document_name = _resolve_document_name(structure_payload, structure_path)
        document_type = _classify_document_type(source_rel_path, document_name)
        metrics_path = _metrics_path_for_source(source_path)
        source_freshness = _file_freshness(source_path).to_dict()
        output_freshness = _file_freshness(structure_path).to_dict()
        metrics_freshness = _file_freshness(metrics_path).to_dict()
        freshness_signal = _resolve_freshness_signal(source_path, source_freshness)

        record = CatalogRecord(
            record_id=f"{resolved_project_id}:{output_rel_path}",
            project_id=resolved_project_id,
            document_name=document_name,
            document_type=document_type,
            relative_directory=relative_directory,
            source_path=str(source_path),
            output_path=str(structure_path),
            source_rel_path=source_rel_path,
            output_rel_path=output_rel_path,
            summary_present=_structure_contains_any_key(
                structure_payload.get("structure"), {"summary", "prefix_summary"}
            ),
            node_text_present=_structure_contains_any_key(structure_payload.get("structure"), {"text"}),
            freshness={
                "source": source_freshness,
                "output": output_freshness,
                "metrics": metrics_freshness,
            },
            ranking_signals=_ranking_signals_for_document_type(document_type, freshness_signal),
            provenance={
                "manifest_path": str(resolved_manifest_path) if resolved_manifest_path else None,
                "manifest_status": manifest_entry["status"] if manifest_entry else None,
                "manifest_index": manifest_entry["index"] if manifest_entry else None,
                "source_resolution": source_resolution,
                "metrics_path": str(metrics_path),
                "metrics_exists": metrics_path.exists(),
                "structure_doc_name": structure_payload.get("doc_name"),
                "explicit_freshness_date": freshness_signal["explicit_date"],
            },
        )
        records.append(record)

    return CatalogArtifact(
        schema_version=CATALOG_SCHEMA_VERSION,
        project_id=resolved_project_id,
        input_root=str(resolved_input_root),
        output_root=str(resolved_output_root),
        manifest_path=str(resolved_manifest_path) if resolved_manifest_path else None,
        records=records,
    )


def write_catalog(catalog: CatalogArtifact, destination: str | Path) -> Path:
    output_path = Path(destination).expanduser().resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(catalog.to_dict(), indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return output_path


def _resolve_manifest_path(output_root: Path, manifest_path: str | Path | None) -> Path | None:
    if manifest_path is not None:
        return Path(manifest_path).expanduser().resolve()

    default_manifest_path = output_root / "manifest.json"
    if default_manifest_path.exists():
        return default_manifest_path
    return None


def _load_manifest(manifest_path: Path) -> dict[str, Any]:
    return json.loads(manifest_path.read_text(encoding="utf-8"))


def _resolve_input_root(
    input_root: str | Path | None,
    manifest: dict[str, Any] | None,
    manifest_path: Path | None,
) -> Path | None:
    if input_root is not None:
        return Path(input_root).expanduser().resolve()

    if not manifest:
        return None

    manifest_input_root = manifest.get("input_root")
    if not manifest_input_root:
        return None
    return _normalize_path(manifest_input_root, manifest_path.parent if manifest_path else None)


def _index_manifest_entries(
    manifest: dict[str, Any] | None,
    manifest_path: Path | None,
) -> dict[str, dict[str, Any]]:
    if not manifest:
        return {}

    manifest_root = manifest_path.parent if manifest_path else None
    entries: dict[str, dict[str, Any]] = {}
    for index, entry in enumerate(manifest.get("files", [])):
        output_path = entry.get("output")
        if not output_path:
            continue

        resolved_output_path = _normalize_path(output_path, manifest_root)
        entries[str(resolved_output_path)] = {
            "index": index,
            "status": entry.get("status"),
            "source_path": _normalize_path(entry["source"], manifest_root)
            if entry.get("source")
            else None,
        }
    return entries


def _resolve_source_path(
    *,
    input_root: Path,
    output_root: Path,
    structure_path: Path,
    manifest_entry: dict[str, Any] | None,
    manifest_path: Path | None,
) -> tuple[Path, str]:
    if manifest_entry and manifest_entry.get("source_path") is not None:
        return manifest_entry["source_path"], "manifest"

    structure_rel_path = structure_path.relative_to(output_root)
    stem = structure_rel_path.name[: -len("_structure.json")]
    candidate_md = input_root / structure_rel_path.parent / f"{stem}.md"
    candidate_markdown = input_root / structure_rel_path.parent / f"{stem}.markdown"

    if candidate_md.exists():
        return candidate_md.resolve(), "inferred"
    if candidate_markdown.exists():
        return candidate_markdown.resolve(), "inferred"

    if manifest_path:
        return candidate_md.resolve(), "inferred"
    return candidate_md.resolve(), "inferred"


def _normalize_path(path_value: str | Path, base_dir: Path | None = None) -> Path:
    candidate = Path(path_value).expanduser()
    if candidate.is_absolute():
        return candidate.resolve()
    if base_dir is not None:
        return (base_dir / candidate).resolve()
    return candidate.resolve()


def _resolve_document_name(structure_payload: dict[str, Any], structure_path: Path) -> str:
    doc_name = structure_payload.get("doc_name")
    if isinstance(doc_name, str) and doc_name:
        return doc_name
    return structure_path.name[: -len("_structure.json")]


def _metrics_path_for_source(source_path: Path) -> Path:
    return source_path.with_name(f"{source_path.stem}_metrics.json")


def _relative_path_or_name(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.name


def _relative_directory(relative_path: str) -> str:
    parent = Path(relative_path).parent.as_posix()
    return "" if parent == "." else parent


def _structure_contains_any_key(structure: Any, keys: set[str]) -> bool:
    for node in _iter_mapping_nodes(structure):
        if any(key in node for key in keys):
            return True
    return False


def _iter_mapping_nodes(value: Any) -> Iterable[dict[str, Any]]:
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from _iter_mapping_nodes(child)
    elif isinstance(value, list):
        for item in value:
            yield from _iter_mapping_nodes(item)


def _file_freshness(path: Path) -> FileFreshness:
    if not path.exists():
        return FileFreshness(created_at=None, modified_at=None)

    stat_result = path.stat()
    created_timestamp = getattr(stat_result, "st_birthtime", None)
    return FileFreshness(
        created_at=_format_timestamp(created_timestamp),
        modified_at=_format_timestamp(stat_result.st_mtime),
    )


def _format_timestamp(timestamp: float | None) -> str | None:
    if timestamp is None:
        return None
    return (
        datetime.fromtimestamp(timestamp, tz=timezone.utc)
        .isoformat(timespec="seconds")
        .replace("+00:00", "Z")
    )


def _classify_document_type(source_rel_path: str, document_name: str) -> str:
    fingerprint = f"{source_rel_path} {document_name}".lower()
    if "next task" in fingerprint or "next_tasks" in fingerprint or "next.md" in fingerprint:
        return "next_tasks"
    if "blocked" in fingerprint:
        return "blocked"
    if "summary" in fingerprint:
        return "summary"
    if "task_archive" in fingerprint or Path(source_rel_path).name.lower().startswith("task_"):
        return "task"
    return "generic"


def _ranking_signals_for_document_type(
    document_type: str, freshness_signal: dict[str, str | int | bool | None]
) -> dict[str, Any]:
    type_priority = _TYPE_PRIORITIES[document_type]
    return {
        "type_priority": type_priority,
        "default_excluded": document_type == "next_tasks",
        "default_deprioritized": document_type in {"next_tasks", "generic"},
        "freshness_timestamp": freshness_signal["timestamp"],
        "freshness_source": freshness_signal["source"],
    }


def _resolve_freshness_signal(
    source_path: Path, source_freshness: dict[str, str | None]
) -> dict[str, str | None]:
    explicit_date = _extract_latest_explicit_date(source_path)
    if explicit_date is not None:
        return {
            "timestamp": explicit_date,
            "source": "explicit_date",
            "explicit_date": explicit_date,
        }

    created_at = source_freshness.get("created_at")
    if created_at is not None:
        return {
            "timestamp": created_at,
            "source": "filesystem_created_at",
            "explicit_date": None,
        }

    return {
        "timestamp": source_freshness.get("modified_at"),
        "source": "filesystem_modified_at",
        "explicit_date": None,
    }


def _extract_latest_explicit_date(source_path: Path) -> str | None:
    if not source_path.exists():
        return None

    text = source_path.read_text(encoding="utf-8")
    matches: list[datetime] = []
    matches.extend(_extract_iso_dates(text))
    matches.extend(_extract_month_name_dates(text))
    if not matches:
        return None

    latest = max(matches)
    return latest.date().isoformat()


def _extract_iso_dates(text: str) -> list[datetime]:
    results: list[datetime] = []
    for match in re.finditer(r"\b(\d{4})-(\d{2})-(\d{2})\b", text):
        try:
            results.append(datetime.strptime(match.group(0), "%Y-%m-%d"))
        except ValueError:
            continue
    return results


def _extract_month_name_dates(text: str) -> list[datetime]:
    results: list[datetime] = []
    pattern = rf"\b({_MONTH_NAME_PATTERN})\s+(\d{{1,2}}),\s+(\d{{4}})\b"
    for match in re.finditer(pattern, text):
        try:
            results.append(datetime.strptime(match.group(0), "%B %d, %Y"))
        except ValueError:
            continue
    return results
