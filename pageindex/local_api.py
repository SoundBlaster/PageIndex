from __future__ import annotations

import argparse
import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

from .retrieval_schema import RetrievalError, RetrievalNode
from .tool_contract import ContextToolRequest, SearchToolRequest, run_context_tool, run_search_tool

LOCAL_API_ERROR_CODES = (
    "invalid_request",
    "unsupported_operation",
    "internal_server_error",
)


class LocalAPIRequestError(Exception):
    def __init__(
        self,
        *,
        status: HTTPStatus,
        code: str,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.status = status
        self.code = code
        self.message = message
        self.details = details


def dispatch_local_api_request(
    path: str,
    payload: dict[str, Any],
    *,
    llm_client=None,
) -> tuple[HTTPStatus, dict[str, Any]]:
    try:
        normalized_path = path.rstrip("/") or "/"
        if normalized_path == "/search":
            request = SearchToolRequest(
                query=_required_string(payload, "query"),
                catalog=_catalog_value(payload),
                model=_required_string(payload, "model"),
                top_k=_integer_value(payload, "top_k", default=7),
                document_types=_string_tuple(payload, "document_types"),
                path_prefix=_optional_string(payload, "path_prefix"),
                dry_run_candidates=_boolean_value(payload, "dry_run_candidates", default=False),
                include_reasoning=_boolean_value(payload, "include_reasoning", default=False),
                answer_ready=_boolean_value(payload, "answer_ready", default=False),
                max_nodes_per_document=_integer_value(payload, "max_nodes_per_document", default=3),
            )
            result = run_search_tool(request, llm_client=llm_client)
            return HTTPStatus.OK, result.to_dict(include_reasoning=request.include_reasoning)

        if normalized_path == "/context":
            request = ContextToolRequest(
                selected_nodes=_selected_nodes(payload),
                require_text=_boolean_value(payload, "require_text", default=False),
            )
            contexts, errors = run_context_tool(request)
            return HTTPStatus.OK, {
                "contexts": [context.to_dict() for context in contexts],
                "errors": [error.to_dict() for error in errors],
            }

        raise LocalAPIRequestError(
            status=HTTPStatus.NOT_FOUND,
            code="unsupported_operation",
            message=f"Unsupported local API operation: {normalized_path}",
        )
    except LocalAPIRequestError as error:
        return error.status, _error_payload(
            code=error.code,
            message=error.message,
            details=error.details,
        )


def create_local_api_server(
    host: str = "127.0.0.1",
    port: int = 8000,
    *,
    llm_client=None,
) -> ThreadingHTTPServer:
    server = ThreadingHTTPServer((host, port), _request_handler(llm_client=llm_client))
    server.daemon_threads = True
    return server


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Serve the PageIndex local API shim over HTTP."
    )
    parser.add_argument("--host", default="127.0.0.1", help="Bind address for the local API.")
    parser.add_argument("--port", type=int, default=8000, help="Bind port for the local API.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None, *, llm_client=None) -> int:
    args = parse_args(argv)
    server = create_local_api_server(args.host, args.port, llm_client=llm_client)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


def _request_handler(*, llm_client=None) -> type[BaseHTTPRequestHandler]:
    class LocalAPIHandler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802
            normalized_path = self.path.rstrip("/") or "/"
            if normalized_path == "/health":
                self._write_json(
                    HTTPStatus.OK,
                    {
                        "status": "ok",
                        "service": "pageindex-local-api",
                    },
                )
                return

            self._write_json(
                HTTPStatus.NOT_FOUND,
                _error_payload(
                    code="unsupported_operation",
                    message=f"Unsupported local API operation: {normalized_path}",
                ),
            )

        def do_POST(self) -> None:  # noqa: N802
            try:
                payload = self._read_payload()
                status, response_payload = dispatch_local_api_request(
                    self.path,
                    payload,
                    llm_client=llm_client,
                )
            except json.JSONDecodeError:
                status = HTTPStatus.BAD_REQUEST
                response_payload = _error_payload(
                    code="invalid_request",
                    message="Request body must be valid JSON.",
                )
            except LocalAPIRequestError as error:
                status = error.status
                response_payload = _error_payload(
                    code=error.code,
                    message=error.message,
                    details=error.details,
                )
            except Exception as error:  # pragma: no cover - defensive transport wrapper
                status = HTTPStatus.INTERNAL_SERVER_ERROR
                response_payload = _error_payload(
                    code="internal_server_error",
                    message="Local API request failed.",
                    details={"error": str(error), "path": self.path},
                )

            self._write_json(status, response_payload)

        def log_message(self, format: str, *args: object) -> None:
            return None

        def _read_payload(self) -> dict[str, Any]:
            try:
                content_length = int(self.headers.get("Content-Length", "0"))
            except ValueError as error:
                raise LocalAPIRequestError(
                    status=HTTPStatus.BAD_REQUEST,
                    code="invalid_request",
                    message="Content-Length must be an integer.",
                ) from error

            if content_length <= 0:
                raise LocalAPIRequestError(
                    status=HTTPStatus.BAD_REQUEST,
                    code="invalid_request",
                    message="Request body must be a non-empty JSON object.",
                )

            payload = json.loads(self.rfile.read(content_length))
            if not isinstance(payload, dict):
                raise LocalAPIRequestError(
                    status=HTTPStatus.BAD_REQUEST,
                    code="invalid_request",
                    message="Request body must be a JSON object.",
                )
            return payload

        def _write_json(self, status: HTTPStatus, payload: dict[str, Any]) -> None:
            body = json.dumps(
                payload,
                indent=2,
                ensure_ascii=False,
                sort_keys=False,
            ).encode("utf-8")
            self.send_response(int(status))
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    return LocalAPIHandler


def _catalog_value(payload: dict[str, Any]) -> str | dict[str, object]:
    value = payload.get("catalog")
    if isinstance(value, str) and value.strip():
        return value
    if isinstance(value, dict):
        return value
    raise LocalAPIRequestError(
        status=HTTPStatus.BAD_REQUEST,
        code="invalid_request",
        message="Field `catalog` must be a non-empty string path or a catalog object.",
    )


def _selected_nodes(payload: dict[str, Any]) -> tuple[RetrievalNode, ...]:
    raw_nodes = payload.get("selected_nodes")
    if not isinstance(raw_nodes, list):
        raise LocalAPIRequestError(
            status=HTTPStatus.BAD_REQUEST,
            code="invalid_request",
            message="Field `selected_nodes` must be a JSON array.",
        )

    selected_nodes: list[RetrievalNode] = []
    for index, raw_node in enumerate(raw_nodes):
        if not isinstance(raw_node, dict):
            raise LocalAPIRequestError(
                status=HTTPStatus.BAD_REQUEST,
                code="invalid_request",
                message=f"selected_nodes[{index}] must be a JSON object.",
            )
        selected_nodes.append(
            RetrievalNode(
                record_id=_required_string(raw_node, "record_id", prefix=f"selected_nodes[{index}]"),
                node_id=_required_string(raw_node, "node_id", prefix=f"selected_nodes[{index}]"),
                title=_required_string(raw_node, "title", prefix=f"selected_nodes[{index}]"),
                source_path=_required_string(
                    raw_node,
                    "source_path",
                    prefix=f"selected_nodes[{index}]",
                ),
                output_path=_required_string(
                    raw_node,
                    "output_path",
                    prefix=f"selected_nodes[{index}]",
                ),
                summary=_optional_string(raw_node, "summary"),
                line_number=_optional_integer(raw_node, "line_number"),
                reasoning=_optional_string(raw_node, "reasoning"),
            )
        )

    return tuple(selected_nodes)


def _required_string(
    payload: dict[str, Any],
    field_name: str,
    *,
    prefix: str | None = None,
) -> str:
    value = payload.get(field_name)
    if isinstance(value, str) and value.strip():
        return value
    label = f"{prefix}.{field_name}" if prefix else field_name
    raise LocalAPIRequestError(
        status=HTTPStatus.BAD_REQUEST,
        code="invalid_request",
        message=f"Field `{label}` must be a non-empty string.",
    )


def _optional_string(payload: dict[str, Any], field_name: str) -> str | None:
    value = payload.get(field_name)
    if value is None:
        return None
    if isinstance(value, str):
        return value or None
    raise LocalAPIRequestError(
        status=HTTPStatus.BAD_REQUEST,
        code="invalid_request",
        message=f"Field `{field_name}` must be a string when provided.",
    )


def _boolean_value(payload: dict[str, Any], field_name: str, *, default: bool) -> bool:
    value = payload.get(field_name, default)
    if isinstance(value, bool):
        return value
    raise LocalAPIRequestError(
        status=HTTPStatus.BAD_REQUEST,
        code="invalid_request",
        message=f"Field `{field_name}` must be a boolean.",
    )


def _integer_value(payload: dict[str, Any], field_name: str, *, default: int) -> int:
    value = payload.get(field_name, default)
    if isinstance(value, bool) or not isinstance(value, int):
        raise LocalAPIRequestError(
            status=HTTPStatus.BAD_REQUEST,
            code="invalid_request",
            message=f"Field `{field_name}` must be an integer.",
        )
    return value


def _optional_integer(payload: dict[str, Any], field_name: str) -> int | None:
    value = payload.get(field_name)
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int):
        raise LocalAPIRequestError(
            status=HTTPStatus.BAD_REQUEST,
            code="invalid_request",
            message=f"Field `{field_name}` must be an integer when provided.",
        )
    return value


def _string_tuple(payload: dict[str, Any], field_name: str) -> tuple[str, ...]:
    value = payload.get(field_name, [])
    if not isinstance(value, list):
        raise LocalAPIRequestError(
            status=HTTPStatus.BAD_REQUEST,
            code="invalid_request",
            message=f"Field `{field_name}` must be a JSON array of strings.",
        )

    string_values: list[str] = []
    for index, item in enumerate(value):
        if not isinstance(item, str) or not item.strip():
            raise LocalAPIRequestError(
                status=HTTPStatus.BAD_REQUEST,
                code="invalid_request",
                message=f"Field `{field_name}[{index}]` must be a non-empty string.",
            )
        string_values.append(item)
    return tuple(string_values)


def _error_payload(
    *,
    code: str,
    message: str,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "errors": [
            RetrievalError(
                code=code,
                message=message,
                details=details,
            ).to_dict()
        ]
    }


if __name__ == "__main__":
    raise SystemExit(main())
