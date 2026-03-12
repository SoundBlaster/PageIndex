## REVIEW REPORT — PH4-T2 Answer-Ready Extraction Mode

**Scope:** `feature/PH5-T1-define-local-tool-contract..HEAD`
**Files:** 15

### Summary Verdict
- [x] Approve
- [ ] Approve with comments
- [ ] Request changes
- [ ] Block

### Critical Issues

- None.

### Secondary Issues

- None.

### Architectural Notes

- `pageindex.retrieval.search_catalog()` adds answer-ready behavior as an opt-in layer over the existing retrieval result instead of introducing a parallel execution path, which keeps the shared contract centralized.
- `pageindex.context.build_extracted_context()` reuses the node lookup helpers from `PH4-T1`, so the explicit `node_text_missing` error stays aligned across direct context lookups and answer-ready search output.
- The CLI and tool-contract surfaces expose the same `answer_ready` flag and resulting `extracted_context` shape, keeping local callers on one machine-readable contract.
- Ruff still reports pre-existing legacy violations outside this task scope; no new lint-specific debt was identified in the answer-ready changes.

### Tests

- `./.venv/bin/python -m pytest`
- `./.venv/bin/python -m py_compile run_pageindex.py pageindex/__init__.py pageindex/page_index.py pageindex/page_index_md.py pageindex/utils.py pageindex/catalog.py pageindex/retrieval_schema.py pageindex/candidate_selection.py pageindex/local_tree_search.py pageindex/retrieval.py pageindex/search_cli.py pageindex/context.py pageindex/tool_contract.py scripts/index_markdown_directory.py scripts/build_index_catalog.py scripts/search_index.py tests/test_catalog.py tests/test_retrieval_schema.py tests/test_candidate_selection.py tests/test_local_tree_search.py tests/test_retrieval.py tests/test_search_cli.py tests/test_context.py tests/test_tool_contract.py`
- `./.venv/bin/python run_pageindex.py --md_path README.md --if-add-node-summary no --if-add-doc-description no --if-add-node-text no`
- `./.venv/bin/python -m pytest --cov=pageindex.context --cov=pageindex.retrieval --cov=pageindex.search_cli --cov=pageindex.tool_contract --cov-report=term-missing --cov-fail-under=90 tests/test_context.py tests/test_retrieval.py tests/test_search_cli.py tests/test_tool_contract.py`
- `./.venv/bin/python - <<'PY' ... search_catalog(answer_ready=True) against ISOInspector catalog ... PY`

### Next Steps

- FOLLOW-UP skipped: no actionable review findings.
