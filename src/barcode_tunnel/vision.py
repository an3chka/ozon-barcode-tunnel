"""Опциональный декодер картинок через ZXing-C++.

Production DataMan 3816X выполняет распознавание внутри reader'а. Этот модуль
нужен только для локальной демонстрации на файлах.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class VisionDependencyError(RuntimeError):
    pass


def decode_image(
    path: str | Path,
    *,
    box_id: str,
    reader_id: str,
    face: str,
) -> list[dict[str, Any]]:
    try:
        from PIL import Image
        import zxingcpp
    except ImportError as exc:
        raise VisionDependencyError(
            "Установите опциональные зависимости: pip install -e '.[vision]'"
        ) from exc

    image = Image.open(path).convert("RGB")
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    events: list[dict[str, Any]] = []
    for result in zxingcpp.read_barcodes(image):
        event: dict[str, Any] = {
            "type": "reading",
            "box_id": box_id,
            "reader_id": reader_id,
            "face": face,
            "code": result.text,
            "symbology": str(result.format),
            "at": now,
        }
        try:
            points = [
                result.position.top_left,
                result.position.top_right,
                result.position.bottom_right,
                result.position.bottom_left,
            ]
            event["position"] = {
                "x": sum(point.x for point in points) / (4 * image.width),
                "y": sum(point.y for point in points) / (4 * image.height),
            }
        except (AttributeError, TypeError, ZeroDivisionError):
            pass
        events.append(event)
    return events

