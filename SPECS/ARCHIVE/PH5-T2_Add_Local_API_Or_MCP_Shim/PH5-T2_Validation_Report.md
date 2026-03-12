# PH5-T2 Validation Report

**Task ID:** PH5-T2
**Task Name:** Add Local API Or MCP Shim
**Date:** 2026-03-12
**Verdict:** PASS

## Summary

Added a thin local HTTP API shim over the stabilized search and context contract without duplicating retrieval or node lookup logic. Validation covered the full repository test suite, task-focused coverage above the 90% threshold, compile and smoke checks, a launcher-script verification, a touched-file lint pass, and a real ISOInspector `/search` request through the HTTP wrapper using the rebuilt catalog artifact.

## Commands

1. `./.venv/bin/python -m pytest`
   - Result: PASS (`52 passed`)
2. `./.venv/bin/python -m py_compile run_pageindex.py pageindex/__init__.py pageindex/page_index.py pageindex/page_index_md.py pageindex/utils.py pageindex/catalog.py pageindex/retrieval_schema.py pageindex/candidate_selection.py pageindex/local_tree_search.py pageindex/retrieval.py pageindex/search_cli.py pageindex/context.py pageindex/tool_contract.py pageindex/local_api.py scripts/index_markdown_directory.py scripts/build_index_catalog.py scripts/search_index.py scripts/run_local_api.py tests/test_catalog.py tests/test_retrieval_schema.py tests/test_candidate_selection.py tests/test_local_tree_search.py tests/test_retrieval.py tests/test_search_cli.py tests/test_context.py tests/test_tool_contract.py tests/test_local_api.py`
   - Result: PASS
3. `./.venv/bin/python run_pageindex.py --md_path README.md --if-add-node-summary no --if-add-doc-description no --if-add-node-text no`
   - Result: PASS
4. `./.venv/bin/python -m pytest --cov=pageindex.local_api --cov=pageindex.context --cov=pageindex.tool_contract --cov-report=term-missing --cov-fail-under=90 tests/test_local_api.py tests/test_context.py tests/test_tool_contract.py`
   - Result: PASS
   - Coverage note: `pageindex.local_api` + `pageindex.context` + `pageindex.tool_contract` combined coverage = `94.86%`
5. `./.venv/bin/python scripts/run_local_api.py --help`
   - Result: PASS
   - Confirmed that the launcher script resolves the repository package correctly and prints the HTTP shim usage text.
6. `./.venv/bin/ruff check pageindex/local_api.py pageindex/context.py pageindex/tool_contract.py tests/test_local_api.py scripts/run_local_api.py README.md`
   - Result: PASS
7. `./.venv/bin/python - <<'PY' ... create_local_api_server(...) + POST /search against results/isoinspector_task_archive_lmstudio_catalog.json ... PY`
   - Result: PASS
   - Confirmed that the local HTTP shim returned `5` candidate documents from the real ISOInspector catalog artifact with no errors.
8. `./.venv/bin/ruff check .`
   - Result: FAIL (non-blocking baseline)
   - Note: the repository still contains `114` pre-existing Ruff violations in legacy modules and notebooks, including `pageindex/page_index.py`, `pageindex/page_index_md.py`, `pageindex/utils.py`, `run_pageindex.py`, and `cookbook/*.ipynb`. `PH5-T2` did not add to that baseline, and `.flow/params.yaml` continues to use `py_compile` as the active lint gate.

## Acceptance Criteria Check

- The wrapper calls the same underlying retrieval and context functions as the CLI.
- No business logic is duplicated into the wrapper layer.
- An agent can query the local corpus through the wrapper without custom response parsing hacks.

## Notes

- `mypy` was not run because this repository does not define a mypy configuration or typed-source validation command in `.flow/params.yaml`.
- `PH5-T2` chooses the local HTTP API path, not an MCP server, to keep the transport thin and dependency-free at this stage.
