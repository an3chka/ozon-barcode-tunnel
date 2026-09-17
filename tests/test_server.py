from __future__ import annotations

import json
import threading
import unittest
from http.server import ThreadingHTTPServer
from urllib.request import Request, urlopen

from barcode_tunnel.aggregator import TunnelAggregator
from barcode_tunnel.server import make_handler


class ServerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        try:
            cls.httpd = ThreadingHTTPServer(
                ("127.0.0.1", 0), make_handler(TunnelAggregator())
            )
        except PermissionError as exc:
            # Некоторые CI-песочницы запрещают создание даже loopback-сокета.
            # В обычной среде этот тест выполняется полностью.
            raise unittest.SkipTest("Среда запрещает локальные TCP-сокеты") from exc
        cls.thread = threading.Thread(target=cls.httpd.serve_forever, daemon=True)
        cls.thread.start()
        cls.base_url = f"http://127.0.0.1:{cls.httpd.server_port}"

    @classmethod
    def tearDownClass(cls) -> None:
        cls.httpd.shutdown()
        cls.httpd.server_close()
        cls.thread.join(timeout=2)

    def test_health_and_event_endpoint(self) -> None:
        with urlopen(f"{self.base_url}/health", timeout=2) as response:  # noqa: S310
            health = json.load(response)
        self.assertEqual(health["status"], "ok")

        payload = json.dumps(
            {
                "type": "box_started",
                "box_id": "http-box",
                "at": "2026-09-17T12:00:00Z",
            }
        ).encode()
        request = Request(
            f"{self.base_url}/v1/events",
            data=payload,
            method="POST",
            headers={"Content-Type": "application/json"},
        )
        with urlopen(request, timeout=2) as response:  # noqa: S310
            result = json.load(response)
        self.assertTrue(result["accepted"])
        self.assertEqual(result["box_id"], "http-box")


if __name__ == "__main__":
    unittest.main()
