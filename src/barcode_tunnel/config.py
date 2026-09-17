"""Загрузка конфигурации тоннеля из JSON."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .models import FACES, EventError, validate_face


@dataclass(frozen=True)
class TunnelConfig:
    expected_faces: tuple[str, ...] = FACES
    required_readers: tuple[str, ...] = ()
    dedupe_radius: float = 0.08
    max_box_window_s: float = 1.8
    callback_url: str | None = None
    callback_timeout_s: float = 1.0
    callback_retries: int = 3

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TunnelConfig:
        faces_raw = data.get("expected_faces", list(FACES))
        if not isinstance(faces_raw, list) or not faces_raw:
            raise EventError("expected_faces должен быть непустым списком")
        faces = tuple(dict.fromkeys(validate_face(str(face)) for face in faces_raw))
        readers_raw = data.get("required_readers", [])
        if not isinstance(readers_raw, list):
            raise EventError("required_readers должен быть списком")
        readers = tuple(
            dict.fromkeys(
                str(reader).strip() for reader in readers_raw if str(reader).strip()
            )
        )
        radius = float(data.get("dedupe_radius", 0.08))
        window = float(data.get("max_box_window_s", 1.8))
        timeout = float(data.get("callback_timeout_s", 1.0))
        retries = int(data.get("callback_retries", 3))
        if not 0.0 < radius <= 1.0:
            raise EventError("dedupe_radius должен быть в диапазоне (0, 1]")
        if window <= 0 or timeout <= 0 or retries < 1:
            raise EventError("Временные параметры должны быть положительными")
        callback = data.get("callback_url")
        if callback is not None and not isinstance(callback, str):
            raise EventError("callback_url должен быть строкой или null")
        return cls(
            expected_faces=faces,
            required_readers=readers,
            dedupe_radius=radius,
            max_box_window_s=window,
            callback_url=callback,
            callback_timeout_s=timeout,
            callback_retries=retries,
        )


def load_config(path: str | Path) -> TunnelConfig:
    with Path(path).open("r", encoding="utf-8") as stream:
        data = json.load(stream)
    if not isinstance(data, dict):
        raise EventError("Корень конфигурации должен быть JSON-объектом")
    return TunnelConfig.from_dict(data)
