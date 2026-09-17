"""Минимальный HTTP API на стандартной библиотеке Python."""

from __future__ import annotations

import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
from urllib.parse import unquote

from .aggregator import TunnelAggregator
from .models import EventError
from .transport import CallbackError, post_result


def make_handler(aggregator: TunnelAggregator) -> type[BaseHTTPRequestHandler]:
    class Handler(BaseHTTPRequestHandler):
        server_version = "BarcodeTunnel/0.1"

        def do_GET(self) -> None:  # noqa: N802
            if self.path == "/health":
                self._send(HTTPStatus.OK, aggregator.snapshot())
                return
            prefix = "/v1/results/"
            if self.path.startswith(prefix):
                box_id = unquote(self.path[len(prefix) :])
                result = aggregator.get_result(box_id)
                if result is None:
                    self._send(HTTPStatus.NOT_FOUND, {"error": "result_not_found"})
                else:
                    self._send(HTTPStatus.OK, result)
                return
            self._send(HTTPStatus.NOT_FOUND, {"error": "not_found"})

        def do_POST(self) -> None:  # noqa: N802
            if self.path != "/v1/events":
                self._send(HTTPStatus.NOT_FOUND, {"error": "not_found"})
                return
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if length <= 0 or length > 1_000_000:
                    raise EventError("Некорректный Content-Length")
                raw = self.rfile.read(length)
                data = json.loads(raw.decode("utf-8"))
                result = aggregator.handle_event(data)
                callback_warning = None
                if data.get("type") == "box_finished" and aggregator.config.callback_url:
                    try:
                        post_result(
                            aggregator.config.callback_url,
                            result,
                            timeout_s=aggregator.config.callback_timeout_s,
                            retries=aggregator.config.callback_retries,
                        )
                    except CallbackError as exc:
                        callback_warning = str(exc)
                response: dict[str, Any] = result
                if callback_warning:
                    response = {**result, "callback_warning": callback_warning}
                self._send(HTTPStatus.OK, response)
            except (EventError, json.JSONDecodeError, UnicodeDecodeError) as exc:
                self._send(HTTPStatus.BAD_REQUEST, {"error": str(exc)})
            except Exception as exc:  # pragma: no cover - последний защитный барьер API
                self._send(
                    HTTPStatus.INTERNAL_SERVER_ERROR,
                    {"error": "internal_error", "detail": type(exc).__name__},
                )

        def log_message(self, fmt: str, *args: Any) -> None:
            # Оставляем стандартный доступ-лог, но в одном предсказуемом формате.
            print(f"http {self.address_string()} {fmt % args}")

        def _send(self, status: HTTPStatus, payload: dict[str, Any]) -> None:
            body = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    return Handler


def serve(aggregator: TunnelAggregator, host: str, port: int) -> None:
    server = ThreadingHTTPServer((host, port), make_handler(aggregator))
    print(f"Barcode tunnel API: http://{host}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()

