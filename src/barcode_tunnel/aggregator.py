"""Состояние коробок, дедупликация кадров и финальный результат."""

from __future__ import annotations

from datetime import timedelta
from threading import RLock
from typing import Any
from uuid import uuid4

from .config import TunnelConfig
from .models import (
    BoxSession,
    EventError,
    Occurrence,
    ReadEvent,
    iso_time,
    parse_time,
    require_text,
    validate_face,
)


class TunnelAggregator:
    """Потокобезопасный агрегатор событий от датчиков и smart-reader'ов."""

    def __init__(self, config: TunnelConfig | None = None) -> None:
        self.config = config or TunnelConfig()
        self._active: dict[str, BoxSession] = {}
        self._results: dict[str, dict[str, Any]] = {}
        self._lock = RLock()

    def start_box(self, data: dict[str, Any]) -> dict[str, Any]:
        with self._lock:
            box_id = data.get("box_id") or f"box-{uuid4().hex[:12]}"
            if not isinstance(box_id, str) or not box_id.strip():
                raise EventError("box_id должен быть непустой строкой")
            box_id = box_id.strip()
            if box_id in self._results:
                raise EventError(f"Коробка {box_id!r} уже завершена")
            started_at = parse_time(data.get("at"))
            existing = self._active.get(box_id)
            if existing is not None:
                return {"accepted": True, "box_id": box_id, "duplicate": True}
            self._active[box_id] = BoxSession(
                box_id=box_id,
                started_at=started_at,
                deadline=started_at + timedelta(seconds=self.config.max_box_window_s),
            )
            return {"accepted": True, "box_id": box_id, "duplicate": False}

    def observe_face(self, data: dict[str, Any]) -> dict[str, Any]:
        with self._lock:
            box = self._resolve_box(data.get("box_id"), parse_time(data.get("at")))
            face = validate_face(require_text(data, "face"))
            reader_id = require_text(data, "reader_id")
            box.observed_faces.add(face)
            box.observed_readers.add(reader_id)
            return {"accepted": True, "box_id": box.box_id, "face": face}

    def add_reading(self, data: dict[str, Any]) -> dict[str, Any]:
        with self._lock:
            event = ReadEvent.from_dict(data)
            box = self._resolve_box(event.box_id, event.at)
            box.observed_faces.add(event.face)
            box.observed_readers.add(event.reader_id)
            for occurrence in box.occurrences:
                if occurrence.is_same_label(event, self.config.dedupe_radius):
                    occurrence.add(event)
                    return {
                        "accepted": True,
                        "box_id": box.box_id,
                        "new_occurrence": False,
                    }
            box.occurrences.append(Occurrence.from_read(event))
            return {"accepted": True, "box_id": box.box_id, "new_occurrence": True}

    def finish_box(self, data: dict[str, Any]) -> dict[str, Any]:
        with self._lock:
            box_id = require_text(data, "box_id")
            if box_id in self._results:
                return self._results[box_id]
            box = self._active.get(box_id)
            if box is None:
                raise EventError(f"Нет активной коробки {box_id!r}")
            finished_at = parse_time(data.get("at"))
            missing_faces = sorted(set(self.config.expected_faces) - box.observed_faces)
            missing_readers = sorted(
                set(self.config.required_readers) - box.observed_readers
            )
            if missing_faces or missing_readers:
                status = "INCOMPLETE"
            elif not box.occurrences:
                status = "NO_READ"
            else:
                status = "OK"
            unique_codes = sorted({item.code for item in box.occurrences})
            result: dict[str, Any] = {
                "box_id": box.box_id,
                "status": status,
                "started_at": iso_time(box.started_at),
                "finished_at": iso_time(finished_at),
                "processing_window_ms": max(
                    0, round((finished_at - box.started_at).total_seconds() * 1000)
                ),
                "observed_faces": sorted(box.observed_faces),
                "missing_faces": missing_faces,
                "readers": sorted(box.observed_readers),
                "missing_readers": missing_readers,
                "unique_codes": unique_codes,
                "occurrence_count": len(box.occurrences),
                "occurrences": [item.as_dict() for item in box.occurrences],
            }
            self._results[box_id] = result
            del self._active[box_id]
            return result

    def handle_event(self, data: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(data, dict):
            raise EventError("Событие должно быть JSON-объектом")
        event_type = require_text(data, "type")
        if event_type == "box_started":
            return self.start_box(data)
        if event_type == "face_observed":
            return self.observe_face(data)
        if event_type == "reading":
            return self.add_reading(data)
        if event_type == "box_finished":
            return self.finish_box(data)
        raise EventError(f"Неизвестный type: {event_type!r}")

    def get_result(self, box_id: str) -> dict[str, Any] | None:
        with self._lock:
            return self._results.get(box_id)

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            return {
                "status": "ok",
                "active_boxes": len(self._active),
                "completed_boxes": len(self._results),
            }

    def _resolve_box(self, box_id: Any, event_at: Any) -> BoxSession:
        if box_id is not None:
            if not isinstance(box_id, str) or not box_id.strip():
                raise EventError("box_id должен быть непустой строкой или null")
            box = self._active.get(box_id.strip())
            if box is None:
                raise EventError(f"Нет активной коробки {box_id!r}")
            return box

        candidates = [
            box
            for box in self._active.values()
            if box.started_at <= event_at <= box.deadline
        ]
        if not candidates:
            raise EventError("Не удалось связать событие с активной коробкой")
        # При штатном интервале 2 с здесь всегда один кандидат. Если окна всё же
        # пересеклись, берём коробку, вошедшую в тоннель последней.
        return max(candidates, key=lambda item: item.started_at)
