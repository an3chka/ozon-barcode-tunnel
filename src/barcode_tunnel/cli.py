"""Команды запуска демо."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from .aggregator import TunnelAggregator
from .config import TunnelConfig, load_config
from .models import EventError
from .server import serve
from .vision import VisionDependencyError, decode_image


def _read_events(path: Path) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, 1):
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            try:
                item = json.loads(line)
            except json.JSONDecodeError as exc:
                raise EventError(f"{path}:{line_number}: {exc.msg}") from exc
            if not isinstance(item, dict):
                raise EventError(f"{path}:{line_number}: ожидался JSON-объект")
            events.append(item)
    return events


def run_simulation(args: argparse.Namespace) -> int:
    config = load_config(args.config) if args.config else TunnelConfig()
    aggregator = TunnelAggregator(config)
    results: list[dict[str, Any]] = []
    for event in _read_events(Path(args.events)):
        response = aggregator.handle_event(event)
        if event["type"] == "box_finished":
            results.append(response)
    rendered = json.dumps(results, ensure_ascii=False, indent=2)
    if args.output:
        Path(args.output).write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
    return 0


def run_server(args: argparse.Namespace) -> int:
    config = load_config(args.config) if args.config else TunnelConfig()
    serve(TunnelAggregator(config), args.host, args.port)
    return 0


def run_decode(args: argparse.Namespace) -> int:
    events = decode_image(
        args.image,
        box_id=args.box_id,
        reader_id=args.reader_id,
        face=args.face,
    )
    for event in events:
        print(json.dumps(event, ensure_ascii=False))
    if not events:
        print("Коды не найдены", file=sys.stderr)
        return 2
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Демо шестистороннего barcode-тоннеля")
    sub = parser.add_subparsers(dest="command", required=True)

    simulate = sub.add_parser("simulate", help="проиграть JSONL-события")
    simulate.add_argument("events")
    simulate.add_argument("--config")
    simulate.add_argument("--output")
    simulate.set_defaults(func=run_simulation)

    server = sub.add_parser("serve", help="запустить HTTP API")
    server.add_argument("--config")
    server.add_argument("--host", default="127.0.0.1")
    server.add_argument("--port", type=int, default=8080)
    server.set_defaults(func=run_server)

    decode = sub.add_parser("decode-image", help="декодировать тестовое изображение")
    decode.add_argument("image")
    decode.add_argument("--box-id", default="demo-box")
    decode.add_argument("--reader-id", default="demo-reader")
    decode.add_argument("--face", default="front")
    decode.set_defaults(func=run_decode)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return int(args.func(args))
    except (EventError, VisionDependencyError, OSError) as exc:
        print(f"Ошибка: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

