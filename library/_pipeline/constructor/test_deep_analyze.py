#!/usr/bin/env python3
"""Unit tests for Gemini beat merge (no live API)."""

from __future__ import annotations

import unittest

import deep_analyze  # noqa: E402


class ClampBeatsTests(unittest.TestCase):
    def test_fills_duration_and_closes_gaps(self) -> None:
        template = [
            {"beat_id": "B01", "name": "motion_hook", "arc_slot_id": "ARC_TEASE", "substitution_group": "motion_hook"},
            {"beat_id": "B06", "name": "end_card", "arc_slot_id": "ARC_CTA", "substitution_group": "end_card"},
        ]
        raw = [
            {"beat_id": "B01", "t_start": 0.4, "t_end": 3.0, "name": "motion_hook", "substitution_group": "motion_hook"},
            {"beat_id": "B06", "t_start": 5.0, "t_end": 5.5, "name": "end_card", "substitution_group": "end_card"},
        ]
        beats = deep_analyze._clamp_beats(raw, 6.0, template)
        self.assertEqual(beats[0]["t_start"], 0.0)
        self.assertEqual(beats[-1]["t_end"], 6.0)
        self.assertEqual(beats[0]["source"], "vlm")
        self.assertAlmostEqual(sum(b["duration_sec"] for b in beats), 6.0, delta=0.05)

    def test_apply_gemini_sets_ready(self) -> None:
        analysis = {
            "analysis_id": "abc1234567",
            "status": "heuristic",
            "probe": {"duration_sec": 6.0},
            "beats": [],
        }
        parsed = {
            "language": "en",
            "spoken_cta": "Play now",
            "has_bonus_footage": False,
            "beats": [
                {"beat_id": "B01", "t_start": 0, "t_end": 4.5, "substitution_group": "motion_hook"},
                {"beat_id": "B06", "t_start": 4.5, "t_end": 6.0, "substitution_group": "end_card"},
            ],
        }
        out = deep_analyze.apply_gemini(analysis, parsed, [])
        self.assertEqual(out["status"], "ready")
        self.assertEqual(out["vlm"]["language"], "en")
        self.assertEqual(len(out["beats"]), 2)


if __name__ == "__main__":
    unittest.main()
