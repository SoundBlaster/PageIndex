import argparse
import asyncio
import json
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from pageindex.page_index_md import md_to_tree


def parse_args():
    parser = argparse.ArgumentParser(
        description="Recursively index Markdown files with PageIndex and mirror outputs into a target directory."
    )
    parser.add_argument(
        "--md_dir",
        required=True,
        help="Root directory containing Markdown files to index recursively.",
    )
    parser.add_argument(
        "--output_dir",
        required=True,
        help="Directory where JSON outputs and manifest.json will be written.",
    )
    parser.add_argument(
        "--model",
        default="gpt-4o-2024-11-20",
        help="Model to use when summary generation is enabled.",
    )
    parser.add_argument(
        "--if-add-node-id",
        default="yes",
        help="Whether to add node IDs to nodes.",
    )
    parser.add_argument(
        "--if-add-node-summary",
        default="no",
        help="Whether to add node summaries.",
    )
    parser.add_argument(
        "--if-add-doc-description",
        default="no",
        help="Whether to add a document description.",
    )
    parser.add_argument(
        "--if-add-node-text",
        default="no",
        help="Whether to keep node text in the output.",
    )
    parser.add_argument(
        "--if-thinning",
        default="no",
        help="Whether to apply tree thinning.",
    )
    parser.add_argument(
        "--thinning-threshold",
        type=int,
        default=5000,
        help="Minimum token threshold for thinning.",
    )
    parser.add_argument(
        "--summary-token-threshold",
        type=int,
        default=200,
        help="Token threshold for generating summaries.",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Skip files whose output JSON already exists and keep writing manifest progress during the run.",
    )
    return parser.parse_args()


def find_markdown_files(root: Path):
    files = list(root.rglob("*.md"))
    files.extend(root.rglob("*.markdown"))
    return sorted({path.resolve() for path in files})


def build_output_path(output_root: Path, md_root: Path, md_path: Path):
    rel_path = md_path.relative_to(md_root)
    rel_without_suffix = rel_path.with_suffix("")
    return output_root / rel_without_suffix.parent / f"{rel_without_suffix.name}_structure.json"


async def index_file(md_path: Path, args):
    return await md_to_tree(
        md_path=str(md_path),
        if_thinning=args.if_thinning.lower() == "yes",
        min_token_threshold=args.thinning_threshold,
        if_add_node_summary=args.if_add_node_summary,
        summary_token_threshold=args.summary_token_threshold,
        model=args.model,
        if_add_doc_description=args.if_add_doc_description,
        if_add_node_text=args.if_add_node_text,
        if_add_node_id=args.if_add_node_id,
    )


def write_manifest(manifest_path: Path, manifest: dict):
    with manifest_path.open("w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)


async def main():
    args = parse_args()
    md_root = Path(args.md_dir).expanduser().resolve()
    output_root = Path(args.output_dir).expanduser().resolve()

    if not md_root.is_dir():
        raise ValueError(f"Markdown directory not found: {md_root}")

    markdown_files = find_markdown_files(md_root)
    output_root.mkdir(parents=True, exist_ok=True)

    manifest = {
        "input_root": str(md_root),
        "output_root": str(output_root),
        "total_files": len(markdown_files),
        "indexed_files": 0,
        "skipped_files": 0,
        "failed_files": 0,
        "files": [],
    }
    manifest_path = output_root / "manifest.json"
    write_manifest(manifest_path, manifest)

    for index, md_path in enumerate(markdown_files, start=1):
        output_path = build_output_path(output_root, md_root, md_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if args.resume and output_path.exists():
            print(f"[{index}/{len(markdown_files)}] Skipping existing {md_path}")
            manifest["skipped_files"] += 1
            manifest["files"].append(
                {
                    "source": str(md_path),
                    "output": str(output_path),
                    "status": "skipped",
                }
            )
            write_manifest(manifest_path, manifest)
            continue

        print(f"[{index}/{len(markdown_files)}] Indexing {md_path}")
        try:
            result = await index_file(md_path, args)
            with output_path.open("w", encoding="utf-8") as f:
                json.dump(result, f, indent=2, ensure_ascii=False)

            manifest["indexed_files"] += 1
            manifest["files"].append(
                {
                    "source": str(md_path),
                    "output": str(output_path),
                    "status": "indexed",
                }
            )
        except Exception as exc:
            manifest["failed_files"] += 1
            manifest["files"].append(
                {
                    "source": str(md_path),
                    "output": str(output_path),
                    "status": "failed",
                    "error": str(exc),
                }
            )
            print(f"Failed: {md_path} -> {exc}")
        write_manifest(manifest_path, manifest)

    print(
        f"Done. Indexed {manifest['indexed_files']} files, skipped {manifest['skipped_files']}, "
        f"failed {manifest['failed_files']}. "
        f"Manifest: {manifest_path}"
    )


if __name__ == "__main__":
    asyncio.run(main())
