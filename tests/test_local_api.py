from __future__ import annotations

import json
from pathlib import Path
from threading import Thread
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import pytest

from pageindex.local_api import (
    LOCAL_API_ERROR_CODES,
    create_local_api_server,
    dispatch_local_api_request,
    main,
    parse_args,
)


def test_dispatch_local_api_search_reuses_retrieval_result_shape(tmp_path: Path):
    catalog_path = _write_catalog(tmp_path, include_text=True)

    status, payload = dispatch_local_api_request(
        "/search",
        {
            "query": "parse tree",
            "catalog": str(catalog_path),
            "model": "stub-model",
            "include_reasoning": True,
            "answer_ready": True,
        },
        llm_client=lambda *, model, prompt: json.dumps(
            {
                "selected_node_ids": ["0001"],
                "reasoning_by_node": {"0001": "title matches"},
            }
        ),
    )

    assert status == 200
    assert payload["selected_nodes"][0]["node_id"] == "0001"
    assert payload["selected_nodes"][0]["reasoning"] == "title matches"
    assert payload["extracted_context"] == [
        {
            "record_id": "demo:task",
            "node_id": "0001",
            "text": "ParseTree preserves hierarchical parsing semantics.",
            "citation": "TASK_ParseTree.md:3",
        }
    ]


def test_dispatch_local_api_context_serializes_node_contexts(tmp_path: Path):
    output_path = _write_structure(tmp_path, include_text=False)

    status, payload = dispatch_local_api_request(
        "/context",
        {
            "selected_nodes": [
                {
                    "record_id": "demo:task",
                    "node_id": "0001",
                    "title": "ParseTree Overview",
                    "source_path": "/tmp/TASK_ParseTree.md",
                    "output_path": str(output_path),
                    "summary": "Overview",
                    "line_number": 3,
                }
            ],
            "require_text": True,
        },
    )

    assert status == 200
    assert payload["contexts"] == [
        {
            "record_id": "demo:task",
            "node_id": "0001",
            "title": "ParseTree Overview",
            "source_path": "/tmp/TASK_ParseTree.md",
            "output_path": str(output_path),
            "summary": "Overview",
            "line_number": 3,
            "text_available": False,
        }
    ]
    assert [error["code"] for error in payload["errors"]] == ["node_text_missing"]


def test_dispatch_local_api_rejects_invalid_requests(tmp_path: Path):
    catalog_path = _write_catalog(tmp_path)

    status, payload = dispatch_local_api_request(
        "/search",
        {
            "query": "parse tree",
            "catalog": str(catalog_path),
            "model": 123,
        },
    )

    assert status == 400
    assert payload["errors"][0]["code"] == "invalid_request"
    assert LOCAL_API_ERROR_CODES == (
        "invalid_request",
        "unsupported_operation",
        "internal_server_error",
    )


def test_dispatch_local_api_reports_unknown_operation():
    status, payload = dispatch_local_api_request("/unknown", {})

    assert status == 404
    assert payload["errors"][0]["code"] == "unsupported_operation"


def test_dispatch_local_api_accepts_catalog_objects_for_search(tmp_path: Path):
    catalog_path = _write_catalog(tmp_path)
    catalog_payload = json.loads(catalog_path.read_text(encoding="utf-8"))

    status, payload = dispatch_local_api_request(
        "/search",
        {
            "query": "parse tree",
            "catalog": catalog_payload,
            "model": "stub-model",
            "dry_run_candidates": True,
            "document_types": ["task"],
        },
    )

    assert status == 200
    assert [document["record_id"] for document in payload["candidate_documents"]] == ["demo:task"]
    assert payload["selected_nodes"] == []


@pytest.mark.parametrize(
    ("path", "payload", "expected_message"),
    [
        (
            "/search",
            {"query": "parse tree", "catalog": "/tmp/catalog.json", "model": "stub-model", "top_k": True},
            "Field `top_k` must be an integer.",
        ),
        (
            "/search",
            {
                "query": "parse tree",
                "catalog": "/tmp/catalog.json",
                "model": "stub-model",
                "document_types": ["task", 7],
            },
            "Field `document_types[1]` must be a non-empty string.",
        ),
        (
            "/context",
            {"selected_nodes": ["bad-node"]},
            "selected_nodes[0] must be a JSON object.",
        ),
        (
            "/context",
            {
                "selected_nodes": [
                    {
                        "record_id": "demo:task",
                        "node_id": "0001",
                        "title": "ParseTree Overview",
                        "source_path": "/tmp/TASK_ParseTree.md",
                        "output_path": "/tmp/ParseTree_structure.json",
                        "line_number": "3",
                    }
                ]
            },
            "Field `line_number` must be an integer when provided.",
        ),
    ],
)
def test_dispatch_local_api_validation_branches(path: str, payload: dict[str, object], expected_message: str):
    status, response_payload = dispatch_local_api_request(path, payload)

    assert status == 400
    assert response_payload["errors"][0]["message"] == expected_message


def test_local_api_server_exposes_healthcheck():
    server = create_local_api_server("127.0.0.1", 0)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()

    try:
        with urlopen(f"http://127.0.0.1:{server.server_port}/health", timeout=5) as response:
            payload = json.loads(response.read().decode("utf-8"))

        assert payload == {
            "status": "ok",
            "service": "pageindex-local-api",
        }
    finally:
        server.shutdown()
        thread.join(timeout=5)
        server.server_close()


def test_local_api_server_rejects_invalid_json_and_non_object_payload():
    server = create_local_api_server("127.0.0.1", 0)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()

    try:
        status, payload = _post_raw(
            f"http://127.0.0.1:{server.server_port}/search",
            b"{not-json",
        )

        assert status == 400
        assert payload["errors"][0]["code"] == "invalid_request"

        status, payload = _post_raw(
            f"http://127.0.0.1:{server.server_port}/search",
            json.dumps([]).encode("utf-8"),
        )

        assert status == 400
        assert payload["errors"][0]["message"] == "Request body must be a JSON object."
    finally:
        server.shutdown()
        thread.join(timeout=5)
        server.server_close()


def test_local_api_server_handles_search_request_end_to_end(tmp_path: Path):
    catalog_path = _write_catalog(tmp_path, include_text=True)
    server = create_local_api_server(
        "127.0.0.1",
        0,
        llm_client=lambda *, model, prompt: json.dumps({"selected_node_ids": ["0001"]}),
    )
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()

    try:
        request = Request(
            f"http://127.0.0.1:{server.server_port}/search",
            data=json.dumps(
                {
                    "query": "parse tree",
                    "catalog": str(catalog_path),
                    "model": "stub-model",
                    "answer_ready": True,
                }
            ).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urlopen(request, timeout=5) as response:
            payload = json.loads(response.read().decode("utf-8"))

        assert payload["selected_nodes"][0]["node_id"] == "0001"
        assert payload["extracted_context"][0]["citation"] == "TASK_ParseTree.md:3"
    finally:
        server.shutdown()
        thread.join(timeout=5)
        server.server_close()


def test_local_api_main_parses_args_and_closes_server(monkeypatch: pytest.MonkeyPatch):
    class FakeServer:
        def __init__(self) -> None:
            self.started = False
            self.closed = False

        def serve_forever(self) -> None:
            self.started = True
            raise KeyboardInterrupt

        def server_close(self) -> None:
            self.closed = True

    fake_server = FakeServer()

    monkeypatch.setattr(
        "pageindex.local_api.create_local_api_server",
        lambda host, port, llm_client=None: fake_server,
    )

    args = parse_args(["--host", "0.0.0.0", "--port", "8100"])

    assert args.host == "0.0.0.0"
    assert args.port == 8100
    assert main(["--host", "0.0.0.0", "--port", "8100"]) == 0
    assert fake_server.started is True
    assert fake_server.closed is True


def _write_catalog(tmp_path: Path, *, include_text: bool = False) -> Path:
    output_path = _write_structure(tmp_path, include_text=include_text)
    catalog_path = tmp_path / "catalog.json"
    catalog_path.write_text(
        json.dumps(
            {
                "schema_version": "1.0",
                "project_id": "demo",
                "input_root": str((tmp_path / "input").resolve()),
                "output_root": str((tmp_path / "output").resolve()),
                "records": [
                    {
                        "record_id": "demo:task",
                        "document_name": "ParseTree Task",
                        "document_type": "task",
                        "source_path": "/tmp/TASK_ParseTree.md",
                        "output_path": str(output_path),
                        "source_rel_path": "TASK_ARCHIVE/TASK_ParseTree.md",
                        "output_rel_path": output_path.name,
                        "relative_directory": "TASK_ARCHIVE",
                        "ranking_signals": {
                            "type_priority": 0,
                            "default_excluded": False,
                            "default_deprioritized": False,
                            "freshness_timestamp": "2026-03-12",
                            "freshness_source": "explicit_date",
                        },
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    return catalog_path


def _write_structure(tmp_path: Path, *, include_text: bool) -> Path:
    output_path = tmp_path / "ParseTree_structure.json"
    output_path.write_text(
        json.dumps(
            {
                "doc_name": "ParseTree",
                "structure": [
                    {
                        "title": "ParseTree Overview",
                        "node_id": "0001",
                        "summary": "Overview",
                        "text": "ParseTree preserves hierarchical parsing semantics."
                        if include_text
                        else None,
                        "line_num": 3,
                        "nodes": [],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    return output_path


def _post_raw(url: str, data: bytes) -> tuple[int, dict[str, object]]:
    request = Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=5) as response:
            return response.status, json.loads(response.read().decode("utf-8"))
    except HTTPError as error:
        return error.code, json.loads(error.read().decode("utf-8"))
