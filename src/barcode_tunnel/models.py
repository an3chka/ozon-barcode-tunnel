"""Небольшие модели данных без внешних библиотек.

В production-проекте их можно заменить на pydantic-модели и JSON Schema.
Для тестового задания стандартной библиотеки достаточно, поэтому демо запускается
даже в чистом Python 3.11.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


FACES = ("top", "bottom", "left", "right", "front", "rear")


class EventError(ValueError):
    """Ошибка формата входного события."""


def parse_time(value: str | None) -> datetime:
    """Разбирает ISO-8601 и всегда возвращает время с часовым поясом."""
    if value is None:
        return datetime.now(timezone.utc)
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (TypeError, ValueError) as exc:
        raise EventError(f"Некорректное время: {value!r}") from exc
    if parsed.tzinfo is None:
        raise EventError("Время должно содержать часовой пояс, например +00:00 или Z")
    return parsed.astimezone(timezone.utc)


def iso_time(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def require_text(data: dict[str, Any], key: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise EventError(f"Поле {key!r} должно быть непустой строкой")
    return value.strip()


def validate_face(face: str) -> str:
    normalized = face.lower().strip()
    if normalized not in FACES:
        raise EventError(f"Неизвестная грань {face!r}; допустимо: {', '.join(FACES)}")
    return normalized


@dataclass(frozen=True)
class Point:
    """Центр найденной метки в координатах грани от 0 до 1."""

    x: float
    y: float

    @classmethod
    def from_event(cls, value: Any) -> Point | None:
        if value is None:
            return None
        if not isinstance(value, dict):
            raise EventError("position должна быть объектом с x и y")
        try:
            point = cls(float(value["x"]), float(value["y"]))
        except (KeyError, TypeError, ValueError) as exc:
            raise EventError("position должна содержать числовые x и y") from exc
        if not (0.0 <= point.x <= 1.0 and 0.0 <= point.y <= 1.0):
            raise EventError("Координаты position должны лежать в диапазоне 0..1")
        return point

    def as_dict(self) -> dict[str, float]:
        return {"x": round(self.x, 4), "y": round(self.y, 4)}


@dataclass(frozen=True)
class ReadEvent:
    box_id: str | None
    reader_id: str
    face: str
    code: str
    symbology: str
    at: datetime
    position: Point | None = None
    quality: float | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ReadEvent:
        box_id = data.get("box_id")
        if box_id is not None and (not isinstance(box_id, str) or not box_id.strip()):
            raise EventError("box_id должен быть непустой строкой или null")
        quality = data.get("quality")
        if quality is not None:
            try:
                quality = float(quality)
            except (TypeError, ValueError) as exc:
                raise EventError("quality должна быть числом") from exc
            if not 0.0 <= quality <= 1.0:
                raise EventError("quality должна лежать в диапазоне 0..1")
        return cls(
            box_id=box_id.strip() if isinstance(box_id, str) else None,
            reader_id=require_text(data, "reader_id"),
            face=validate_face(require_text(data, "face")),
            code=require_text(data, "code"),
            symbology=require_text(data, "symbology").upper(),
            at=parse_time(data.get("at")),
            position=Point.from_event(data.get("position")),
            quality=quality,
        )


@dataclass
class Occurrence:
    """Одна физическая наклейка, замеченная на одном или нескольких кадрах."""

    code: str
    symbology: str
    face: str
    first_seen: datetime
    last_seen: datetime
    position: Point | None
    readers: set[str] = field(default_factory=set)
    frame_hits: int = 0
    best_quality: float | None = None

    @classmethod
    def from_read(cls, event: ReadEvent) -> Occurrence:
        occurrence = cls(
            code=event.code,
            symbology=event.symbology,
            face=event.face,
            first_seen=event.at,
            last_seen=event.at,
            position=event.position,
        )
        occurrence.add(event)
        return occurrence

    def is_same_label(self, event: ReadEvent, radius: float) -> bool:
        if (self.code, self.symbology, self.face) != (
            event.code,
            event.symbology,
            event.face,
        ):
            return False
        if self.position is None or event.position is None:
            # Без координат невозможно разделить две одинаковые наклейки на одной
            # грани. Это явно описано как ограничение демо в README и отчёте.
            return True
        distance_sq = (self.position.x - event.position.x) ** 2 + (
            self.position.y - event.position.y
        ) ** 2
        return distance_sq <= radius**2

    def add(self, event: ReadEvent) -> None:
        self.first_seen = min(self.first_seen, event.at)
        self.last_seen = max(self.last_seen, event.at)
        self.readers.add(event.reader_id)
        self.frame_hits += 1
        if event.quality is not None:
            self.best_quality = max(self.best_quality or 0.0, event.quality)
        if self.position is None:
            self.position = event.position
        elif event.position is not None:
            # Простое скользящее среднее стабилизирует координату между кадрами.
            weight = 1.0 / self.frame_hits
            self.position = Point(
                x=self.position.x * (1 - weight) + event.position.x * weight,
                y=self.position.y * (1 - weight) + event.position.y * weight,
            )

    def as_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "code": self.code,
            "symbology": self.symbology,
            "face": self.face,
            "first_seen": iso_time(self.first_seen),
            "last_seen": iso_time(self.last_seen),
            "readers": sorted(self.readers),
            "frame_hits": self.frame_hits,
        }
        if self.position is not None:
            result["position"] = self.position.as_dict()
        if self.best_quality is not None:
            result["best_quality"] = round(self.best_quality, 4)
        return result


@dataclass
class BoxSession:
    box_id: str
    started_at: datetime
    deadline: datetime
    observed_faces: set[str] = field(default_factory=set)
    observed_readers: set[str] = field(default_factory=set)
    occurrences: list[Occurrence] = field(default_factory=list)

