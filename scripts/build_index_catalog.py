from __future__ import annotations

import argparse
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from pageindex.catalog import build_catalog, write_catalog


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a deterministic catalog.json artifact from PageIndex structure outputs."
    )
    parser.add_argument(
        "--output-root",
        required=True,
        help="Root directory containing PageIndex *_structure.json files.",
    )
    parser.add_argument(
        "--input-root",
        help="Optional source Markdown root. Required when manifest.json is absent or stale.",
    )
    parser.add_argument(
        "--manifest-path",
        help="Optional explicit manifest.json path when it does not live under the output root.",
    )
    parser.add_argument(
        "--project-id",
        help="Optional stable project identifier to store in the catalog artifact.",
    )
    parser.add_argument(
        "--catalog-path",
        help="Optional explicit destination for the generated catalog JSON artifact.",
    )
    return parser.parse_args()


def default_catalog_path(output_root: str | Path) -> Path:
    resolved_output_root = Path(output_root).expanduser().resolve()
    return resolved_output_root.parent / f"{resolved_output_root.name}_catalog.json"


def main() -> int:
    args = parse_args()
    catalog = build_catalog(
        args.output_root,
        input_root=args.input_root,
        project_id=args.project_id,
        manifest_path=args.manifest_path,
    )
    catalog_path = write_catalog(
        catalog,
        args.catalog_path or default_catalog_path(args.output_root),
    )
    print(catalog_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
