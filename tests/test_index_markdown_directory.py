from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys
from types import ModuleType


def test_main_writes_mirrored_outputs_and_indexed_manifest_entries(
    tmp_path: Path,
    monkeypatch,
):
    module = _load_index_markdown_directory_module()
    input_root = tmp_path / "input"
    output_root = tmp_path / "output"

    _write_text(input_root / "alpha.md", "# Alpha\n")
    _write_text(input_root / "nested" / "beta.markdown", "# Beta\n")

    async def fake_index_file(md_path: Path, args) -> dict[str, object]:
        return {
            "doc_name": md_path.stem,
            "structure": [{"title": md_path.stem, "nodes": []}],
        }

    monkeypatch.setattr(module, "index_file", fake_index_file)

    exit_code = module.main(
        [
            "--md_dir",
            str(input_root),
            "--output_dir",
            str(output_root),
            "--if-add-node-summary",
            "no",
            "--if-add-doc-description",
            "no",
            "--if-add-node-text",
            "no",
        ]
    )

    manifest = json.loads((output_root / "manifest.json").read_text(encoding="utf-8"))

    assert exit_code == 0
    assert (output_root / "alpha_structure.json").exists()
    assert (output_root / "nested" / "beta_structure.json").exists()
    assert manifest["indexed_files"] == 2
    assert manifest["skipped_files"] == 0
    assert manifest["failed_files"] == 0
    assert [entry["status"] for entry in manifest["files"]] == ["indexed", "indexed"]


def test_main_records_failed_entries_in_manifest(tmp_path: Path, monkeypatch):
    module = _load_index_markdown_directory_module()
    input_root = tmp_path / "input"
    output_root = tmp_path / "output"

    _write_text(input_root / "good.md", "# Good\n")
    _write_text(input_root / "bad.md", "# Bad\n")

    async def fake_index_file(md_path: Path, args) -> dict[str, object]:
        if md_path.stem == "bad":
            raise RuntimeError("boom")
        return {
            "doc_name": md_path.stem,
            "structure": [{"title": md_path.stem, "nodes": []}],
        }

    monkeypatch.setattr(module, "index_file", fake_index_file)

    exit_code = module.main(
        [
            "--md_dir",
            str(input_root),
            "--output_dir",
            str(output_root),
        ]
    )

    manifest = json.loads((output_root / "manifest.json").read_text(encoding="utf-8"))
    statuses = {Path(entry["source"]).stem: entry for entry in manifest["files"]}

    assert exit_code == 0
    assert manifest["indexed_files"] == 1
    assert manifest["failed_files"] == 1
    assert statuses["good"]["status"] == "indexed"
    assert statuses["bad"]["status"] == "failed"
    assert statuses["bad"]["error"] == "boom"


def test_main_resume_skips_existing_outputs_without_overwrite(tmp_path: Path, monkeypatch):
    module = _load_index_markdown_directory_module()
    input_root = tmp_path / "input"
    output_root = tmp_path / "output"

    _write_text(input_root / "alpha.md", "# Alpha\n")
    _write_text(input_root / "nested" / "beta.md", "# Beta\n")

    async def fake_index_file(md_path: Path, args) -> dict[str, object]:
        return {
            "doc_name": md_path.stem,
            "structure": [{"title": md_path.stem, "nodes": []}],
        }

    monkeypatch.setattr(module, "index_file", fake_index_file)
    first_exit_code = module.main(
        [
            "--md_dir",
            str(input_root),
            "--output_dir",
            str(output_root),
        ]
    )

    alpha_output = output_root / "alpha_structure.json"
    beta_output = output_root / "nested" / "beta_structure.json"
    alpha_before = alpha_output.read_text(encoding="utf-8")
    beta_before = beta_output.read_text(encoding="utf-8")

    async def fail_if_called(md_path: Path, args) -> dict[str, object]:
        raise AssertionError(f"resume should skip {md_path}")

    monkeypatch.setattr(module, "index_file", fail_if_called)
    second_exit_code = module.main(
        [
            "--md_dir",
            str(input_root),
            "--output_dir",
            str(output_root),
            "--resume",
        ]
    )

    manifest = json.loads((output_root / "manifest.json").read_text(encoding="utf-8"))

    assert first_exit_code == 0
    assert second_exit_code == 0
    assert alpha_output.read_text(encoding="utf-8") == alpha_before
    assert beta_output.read_text(encoding="utf-8") == beta_before
    assert manifest["indexed_files"] == 0
    assert manifest["skipped_files"] == 2
    assert manifest["failed_files"] == 0
    assert [entry["status"] for entry in manifest["files"]] == ["skipped", "skipped"]


def test_parse_args_supports_resume_flag(monkeypatch):
    module = _load_index_markdown_directory_module()
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "index_markdown_directory.py",
            "--md_dir",
            "/tmp/input",
            "--output_dir",
            "/tmp/output",
            "--resume",
        ],
    )

    args = module.parse_args()

    assert args.md_dir == "/tmp/input"
    assert args.output_dir == "/tmp/output"
    assert args.resume is True


def _load_index_markdown_directory_module() -> ModuleType:
    script_path = (
        Path(__file__).resolve().parents[1] / "scripts" / "index_markdown_directory.py"
    )
    spec = importlib.util.spec_from_file_location("index_markdown_directory", script_path)
    assert spec is not None
    assert spec.loader is not None

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _write_text(path: Path, contents: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(contents, encoding="utf-8")
