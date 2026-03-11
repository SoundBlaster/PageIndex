## REVIEW REPORT — PH3-T2 Candidate Selection

**Scope:** `origin/main..HEAD`
**Files:** 8

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

- The selector stays transport-neutral and returns shared `RetrievalDocument` values, which keeps `PH3-T3` and `PH3-T4` from duplicating ranking or serialization logic.
- Default exclusion of `next_tasks` records gives the retrieval flow a practical precision bias on noisy planning corpora while still allowing explicit opt-in through filters.

### Tests

- `./.venv/bin/python -m pytest tests/test_candidate_selection.py tests/test_retrieval_schema.py tests/test_catalog.py`
- `./.venv/bin/python -m py_compile run_pageindex.py pageindex/__init__.py pageindex/page_index.py pageindex/page_index_md.py pageindex/utils.py pageindex/catalog.py pageindex/retrieval_schema.py pageindex/candidate_selection.py scripts/index_markdown_directory.py scripts/build_index_catalog.py tests/test_catalog.py tests/test_retrieval_schema.py tests/test_candidate_selection.py`
- `./.venv/bin/python run_pageindex.py --md_path README.md --if-add-node-summary no --if-add-doc-description no --if-add-node-text no`
- `./.venv/bin/python -m pytest --cov=pageindex.candidate_selection --cov-report=term-missing --cov-fail-under=90 tests/test_candidate_selection.py`
- `./.venv/bin/python scripts/build_index_catalog.py --output-root results/isoinspector_task_archive_lmstudio --catalog-path results/isoinspector_task_archive_lmstudio_catalog.json`

### Next Steps

- FOLLOW-UP skipped: no actionable review findings.
