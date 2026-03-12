# PH5-T1 Validation Report

**Task ID:** PH5-T1
**Task Name:** Define Local Tool Contract
**Date:** 2026-03-12
**Verdict:** PASS

## Summary

Defined a stable local tool contract in code and in the README for the existing search and context operations. Validation covered the full repository test suite, task-focused coverage above the 90% threshold, project compile/smoke checks, and a real ISOInspector contract invocation that exercised both the dry-run search path and explicit `node_text_missing` behavior in the context operation.

## Commands

1. `./.venv/bin/python -m pytest`
   - Result: PASS (`34 passed`)
2. `./.venv/bin/python -m py_compile run_pageindex.py pageindex/__init__.py pageindex/page_index.py pageindex/page_index_md.py pageindex/utils.py pageindex/catalog.py pageindex/retrieval_schema.py pageindex/candidate_selection.py pageindex/local_tree_search.py pageindex/retrieval.py pageindex/search_cli.py pageindex/context.py pageindex/tool_contract.py scripts/index_markdown_directory.py scripts/build_index_catalog.py scripts/search_index.py tests/test_catalog.py tests/test_retrieval_schema.py tests/test_candidate_selection.py tests/test_local_tree_search.py tests/test_retrieval.py tests/test_search_cli.py tests/test_context.py tests/test_tool_contract.py`
   - Result: PASS
3. `./.venv/bin/python run_pageindex.py --md_path README.md --if-add-node-summary no --if-add-doc-description no --if-add-node-text no`
   - Result: PASS
4. `./.venv/bin/python -m pytest --cov=pageindex.tool_contract --cov=pageindex.retrieval --cov=pageindex.context --cov-report=term-missing --cov-fail-under=90 tests/test_tool_contract.py tests/test_retrieval.py tests/test_context.py`
   - Result: PASS
   - Coverage note: `pageindex.tool_contract` + `pageindex.retrieval` + `pageindex.context` combined coverage = `98.14%`
5. `./.venv/bin/python - <<'PY' ... run_search_tool(...) + run_context_tool(...) ... PY`
   - Result: PASS
   - Confirmed that `run_search_tool` returned ISOInspector candidate documents from the real catalog artifact and that `run_context_tool` returned a machine-readable `node_text_missing` error for the current text-absent structure outputs.
6. `./.venv/bin/python -m ruff check pageindex tests scripts run_pageindex.py`
   - Result: FAIL (non-blocking baseline)
   - Note: the repository still contains numerous pre-existing Ruff violations in legacy modules such as `pageindex/page_index.py`, `pageindex/page_index_md.py`, `pageindex/utils.py`, and the script entry points. `PH5-T1` did not expand that baseline, and `.flow/params.yaml` continues to use `py_compile` as the active lint gate.

## Acceptance Criteria Check

- Search and context operations have explicit input and output contracts.
- Contracts reuse the CLI schema instead of creating a second format.
- Agent-facing error behavior is documented in machine-readable terms.

## Notes

- `mypy` was not run because this repository does not define a mypy configuration or typed-source validation command in `.flow/params.yaml`.
- `PH5-T1` intentionally stops at the callable contract and README surface; the transport wrapper remains deferred to `PH5-T2`.
