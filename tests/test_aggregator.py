from __future__ import annotations

import unittest

from barcode_tunnel.aggregator import TunnelAggregator
from barcode_tunnel.config import TunnelConfig
from barcode_tunnel.models import EventError, FACES


BASE = "2026-09-17T12:00:00"


def event(event_type: str, suffix: str, **extra: object) -> dict[str, object]:
    return {"type": event_type, "at": f"{BASE}.{suffix}Z", **extra}


class AggregatorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.aggregator = TunnelAggregator(TunnelConfig(dedupe_radius=0.08))
        self.aggregator.handle_event(
            event("box_started", "000", box_id="box-1")
        )

    def observe_all_faces(self) -> None:
        for index, face in enumerate(FACES, 1):
            self.aggregator.handle_event(
                event(
                    "face_observed",
                    f"{index:03d}",
                    box_id="box-1",
                    reader_id=f"{face}-01",
                    face=face,
                )
            )

    def test_repeated_frames_are_deduplicated_but_two_labels_remain(self) -> None:
        self.observe_all_faces()
        common = {
            "box_id": "box-1",
            "reader_id": "left-01",
            "face": "left",
            "code": "12345",
            "symbology": "CODE128",
        }
        self.aggregator.handle_event(
            event("reading", "100", **common, position={"x": 0.2, "y": 0.4})
        )
        self.aggregator.handle_event(
            event("reading", "120", **common, position={"x": 0.21, "y": 0.41})
        )
        self.aggregator.handle_event(
            event("reading", "140", **common, position={"x": 0.8, "y": 0.7})
        )
        result = self.aggregator.handle_event(
            event("box_finished", "800", box_id="box-1")
        )
        self.assertEqual(result["status"], "OK")
        self.assertEqual(result["unique_codes"], ["12345"])
        self.assertEqual(result["occurrence_count"], 2)
        self.assertEqual(result["occurrences"][0]["frame_hits"], 2)

    def test_missing_face_is_incomplete(self) -> None:
        self.aggregator.handle_event(
            event(
                "reading",
                "100",
                box_id="box-1",
                reader_id="top-01",
                face="top",
                code="123",
                symbology="QR_CODE",
            )
        )
        result = self.aggregator.handle_event(
            event("box_finished", "500", box_id="box-1")
        )
        self.assertEqual(result["status"], "INCOMPLETE")
        self.assertIn("bottom", result["missing_faces"])

    def test_all_faces_without_code_is_no_read(self) -> None:
        self.observe_all_faces()
        result = self.aggregator.handle_event(
            event("box_finished", "600", box_id="box-1")
        )
        self.assertEqual(result["status"], "NO_READ")

    def test_event_without_box_id_is_assigned_by_time_window(self) -> None:
        response = self.aggregator.handle_event(
            event(
                "reading",
                "100",
                reader_id="front-01",
                face="front",
                code="AUTO",
                symbology="CODE128",
            )
        )
        self.assertEqual(response["box_id"], "box-1")

    def test_invalid_face_is_rejected(self) -> None:
        with self.assertRaises(EventError):
            self.aggregator.handle_event(
                event(
                    "reading",
                    "100",
                    box_id="box-1",
                    reader_id="reader",
                    face="inside",
                    code="123",
                    symbology="CODE128",
                )
            )

    def test_missing_required_reader_is_incomplete(self) -> None:
        aggregator = TunnelAggregator(
            TunnelConfig(required_readers=("top-01", "bottom-front-01"))
        )
        aggregator.handle_event(event("box_started", "000", box_id="box-2"))
        for index, face in enumerate(FACES, 1):
            aggregator.handle_event(
                event(
                    "face_observed",
                    f"{index:03d}",
                    box_id="box-2",
                    reader_id="top-01",
                    face=face,
                )
            )
        result = aggregator.handle_event(
            event("box_finished", "700", box_id="box-2")
        )
        self.assertEqual(result["status"], "INCOMPLETE")
        self.assertEqual(result["missing_readers"], ["bottom-front-01"])


if __name__ == "__main__":
    unittest.main()
