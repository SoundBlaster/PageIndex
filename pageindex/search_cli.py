from __future__ import annotations

import argparse
import json
import sys
from typing import TextIO

from .retrieval import search_catalog

DEFAULT_MODEL = "gpt-4o-2024-11-20"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Search a PageIndex catalog and emit deterministic JSON retrieval results."
    )
    parser.add_argument("--query", required=True, help="Search query to run.")
    parser.add_argument("--catalog", required=True, help="Path to the catalog JSON artifact.")
    parser.add_argument("--top-k", type=int, default=7, help="Maximum number of candidate documents.")
    parser.add_argument(
        "--type",
        dest="document_types",
        action="append",
        default=[],
        help="Optional document type filter. Repeat the flag to include multiple types.",
    )
    parser.add_argument(
        "--path-prefix",
        help="Optional source-relative path prefix filter applied before local tree search.",
    )
    parser.add_argument(
        "--dry-run-candidates",
        action="store_true",
        help="Return bounded candidate documents without running the local model.",
    )
    parser.add_argument(
        "--with-reasoning",
        action="store_true",
        help="Include model reasoning in the selected node payload.",
    )
    parser.add_argument(
        "--group-by-document",
        action="store_true",
        help="Add grouped document output while preserving the flat selected_nodes list.",
    )
    parser.add_argument("--model", default=DEFAULT_MODEL, help="Local model name for tree search.")
    parser.add_argument(
        "--max-nodes-per-document",
        type=int,
        default=3,
        help="Maximum number of nodes to keep per selected document.",
    )
    return parser.parse_args(argv)


def main(
    argv: list[str] | None = None,
    *,
    llm_client=None,
    stdout: TextIO | None = None,
) -> int:
    args = parse_args(argv)
    result = search_catalog(
        args.query,
        args.catalog,
        model=args.model,
        top_k=args.top_k,
        document_types=args.document_types,
        path_prefix=args.path_prefix,
        dry_run_candidates=args.dry_run_candidates,
        include_reasoning=args.with_reasoning,
        max_nodes_per_document=args.max_nodes_per_document,
        llm_client=llm_client,
    )
    output = json.dumps(
        result.to_dict(
            group_by_document=args.group_by_document,
            include_reasoning=args.with_reasoning,
        ),
        indent=2,
        ensure_ascii=False,
        sort_keys=False,
    )
    destination = stdout or sys.stdout
    destination.write(output)
    destination.write("\n")
    return 0
