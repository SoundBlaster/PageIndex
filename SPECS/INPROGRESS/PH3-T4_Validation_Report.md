# PH3-T4 Validation Report

**Task ID:** PH3-T4
**Task Name:** Build Search CLI Wrapper
**Date:** 2026-03-12
**Verdict:** PASS

## Summary

Added a retrieval orchestration layer plus a JSON-first local CLI that composes catalog loading, candidate selection, and optional local tree search without duplicating business logic. Validation covered orchestration and CLI tests, repository compile/runtime checks, task-local coverage, a real dry-run search against the ISOInspector catalog artifact, and a full CLI execution path with a stub model response.

## Commands

1. `./.venv/bin/python -m pytest tests/test_catalog.py tests/test_retrieval_schema.py tests/test_candidate_selection.py tests/test_local_tree_search.py tests/test_retrieval.py tests/test_search_cli.py`
   - Result: PASS (`23 passed`)
2. `./.venv/bin/python -m py_compile run_pageindex.py pageindex/__init__.py pageindex/page_index.py pageindex/page_index_md.py pageindex/utils.py pageindex/catalog.py pageindex/retrieval_schema.py pageindex/candidate_selection.py pageindex/local_tree_search.py pageindex/retrieval.py pageindex/search_cli.py scripts/index_markdown_directory.py scripts/build_index_catalog.py scripts/search_index.py tests/test_catalog.py tests/test_retrieval_schema.py tests/test_candidate_selection.py tests/test_local_tree_search.py tests/test_retrieval.py tests/test_search_cli.py`
   - Result: PASS
3. `./.venv/bin/python run_pageindex.py --md_path README.md --if-add-node-summary no --if-add-doc-description no --if-add-node-text no`
   - Result: PASS
4. `./.venv/bin/python -m pytest --cov=pageindex.retrieval --cov=pageindex.search_cli --cov-report=term-missing --cov-fail-under=90 tests/test_retrieval.py tests/test_search_cli.py`
   - Result: PASS
   - Coverage note: `pageindex/retrieval.py` + `pageindex/search_cli.py` combined coverage = `97.83%`
5. `./.venv/bin/python scripts/search_index.py --query "What is BoxHeader and how is it related to BoxParserRegistry" --catalog results/isoinspector_task_archive_lmstudio_catalog.json --dry-run-candidates --top-k 5`
   - Result: PASS
   - Returned deterministic JSON candidate output from the real ISOInspector catalog artifact.
6. `./.venv/bin/python - <<'PY' ... from pageindex.search_cli import main ... llm_client=stub ... PY`
   - Result: PASS
   - The production CLI entry point emitted grouped JSON with reasoning over real ISOInspector structure files using a deterministic stub model response.

## Acceptance Criteria Check

- CLI emits JSON by default.
- CLI supports `--query`, `--catalog`, `--top-k`, `--type`, `--path-prefix`, `--dry-run-candidates`, and `--with-reasoning`.
- CLI can optionally group results by document while keeping flat node results as the default mode.
- The wrapper reuses the candidate-selection and local tree-search cores instead of duplicating retrieval logic.

## Notes

- `OPENAI_BASE_URL` / `CHATGPT_BASE_URL` were not set in this shell, so validation did not include a live LM Studio request from the CLI.
- Candidate `ranking_score` values were adjusted during this task so the CLI’s exposed scores align with the actual candidate ordering.
