#!/usr/bin/env python3
"""Tests for F5.1 substitution-group clones and F4.1 lint."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

CONSTRUCTOR = Path(__file__).resolve().parent

import clone  # noqa: E402
import explode  # noqa: E402
import lint  # noqa: E402


class CloneTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        jobs = explode.explode(
            constructor_dir=CONSTRUCTOR,
            matrix=explode.load_json(CONSTRUCTOR / "variant_matrix.json"),
            include_stubs=False,
            repo_root=explode.REPO_ROOT,
        )
        cls.parent = next(j for j in jobs if j["cta_id"] == "play_now" and j["locale"] == "ru")

    def test_motion_hook_swap_creates_sibling(self) -> None:
        clones = clone.clone_winner(self.parent, groups=["motion_hook"])
        ids = [c["job_id"] for c in clones]
        self.assertGreaterEqual(len(clones), 2)
        self.assertEqual(clones[0]["parent_creative_id"], self.parent["job_id"])
        segments = {
            next(b["segment_id"] for b in c["lineage"]["beats"] if b["substitution_group"] == "motion_hook")
            for c in clones
        }
        self.assertIn("seg_v2_motion_hook", segments)
        self.assertIn("seg_vod_hook_spin_press", segments)
        self.assertTrue(any("hook_spin" in i or "vod_hook" in i for i in ids))

    def test_single_alt_group_does_not_explode(self) -> None:
        clones = clone.clone_winner(self.parent, groups=["scatter_bonus_4"])
        self.assertEqual(len(clones), 1)
        self.assertEqual(clones[0]["job_id"], self.parent["job_id"])


class LintTests(unittest.TestCase):
    def test_guaranteed_win_blocks(self) -> None:
        job = {
            "job_id": "x_y_ru_ru_9x16_play_now",
            "status": "draft",
            "blocked_reason": None,
            "render": {"variables": {"vo_b01": "Guaranteed win every spin", "cta_main": "PLAY"}},
        }
        out = lint.lint_job(job)
        self.assertEqual(out["status"], "blocked")
        self.assertIn("guaranteed_win", out["blocked_reason"])

    def test_clean_copy_passes(self) -> None:
        job = {
            "job_id": "x_y_ru_ru_9x16_play_now",
            "status": "draft",
            "blocked_reason": None,
            "render": {"variables": {"vo_b01": "Gates of Olympus. Stake €2.", "cta_main": "PLAY NOW"}},
        }
        self.assertEqual(lint.lint_job(job)["status"], "draft")


if __name__ == "__main__":
    unittest.main()
