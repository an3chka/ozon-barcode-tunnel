"""Отправка результата в систему управления конвейером."""

from __future__ import annotations

import json
import time
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class CallbackError(RuntimeError):
    pass


def post_result(
    url: str,
    result: dict[str, Any],
    *,
    timeout_s: float = 1.0,
    retries: int = 3,
) -> None:
    """POST с простым retry и идемпотентным ключом box_id."""
    payload = json.dumps(result, ensure_ascii=False).encode("utf-8")
    last_error: Exception | None = None
    for attempt in range(retries):
        request = Request(
            url,
            data=payload,
            method="POST",
            headers={
                "Content-Type": "application/json; charset=utf-8",
                "Idempotency-Key": str(result["box_id"]),
            },
        )
        try:
            with urlopen(request, timeout=timeout_s) as response:  # noqa: S310
                if 200 <= response.status < 300:
                    return
                last_error = CallbackError(f"HTTP {response.status}")
        except (HTTPError, URLError, TimeoutError) as exc:
            last_error = exc
        if attempt + 1 < retries:
            time.sleep(0.05 * 2**attempt)
    raise CallbackError(f"Не удалось отправить результат за {retries} попытки") from last_error

