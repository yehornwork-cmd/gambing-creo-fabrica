#!/usr/bin/env python3
"""Tests for buyer upload analysis + multiply."""

from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

CONSTRUCTOR = Path(__file__).resolve().parent

import analyze_upload  # noqa: E402
import multiply  # noqa: E402


def make_silent_mp4(path: Path, *, width: int, height: int, duration: float = 6.0) -> None:
    proc = subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-f",
            "lavfi",
            "-i",
            f"color=c=black:s={width}x{height}:d={duration}",
            "-pix_fmt",
            "yuv420p",
            str(path),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr[-500:] or "ffmpeg failed")


class ClassifyFormatTests(unittest.TestCase):
    def test_portrait_square_landscape(self) -> None:
        self.assertEqual(analyze_upload.classify_format(1080, 1920)[0], "9x16")
        self.assertEqual(analyze_upload.classify_format(1080, 1080)[0], "1x1")
        self.assertEqual(analyze_upload.classify_format(1920, 1080)[0], "16x9")


class AnalyzeAndMultiplyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.tmp = tempfile.TemporaryDirectory()
        cls.video = Path(cls.tmp.name) / "master.mp4"
        make_silent_mp4(cls.video, width=1080, height=1920, duration=24.0)
        cls.analysis = analyze_upload.analyze(
            video=cls.video,
            product="Gates of Olympus",
            analysis_id="buyer12abcd",
        )
        cls.jobs = multiply.multiply(
            analysis=cls.analysis,
            geos=["PL", "NL"],
        )

    @classmethod
    def tearDownClass(cls) -> None:
        cls.tmp.cleanup()

    def test_probe_and_game(self) -> None:
        self.assertEqual(self.analysis["format"], "9x16")
        self.assertEqual(self.analysis["game_id"], "vs20olympgate")
        self.assertGreaterEqual(self.analysis["probe"]["duration_sec"], 23.5)
        self.assertEqual(self.analysis["scenario_id"], "AD_B")
        self.assertEqual(len(self.analysis["beats"]), 6)
        span = self.analysis["beats"][-1]["t_end"] - self.analysis["beats"][0]["t_start"]
        self.assertAlmostEqual(span, self.analysis["probe"]["duration_sec"], delta=0.15)

    def test_two_geos_times_two_ctas(self) -> None:
        self.assertEqual(len(self.jobs), 4)
        geos = {job["render"]["variables"]["forge_geo"] for job in self.jobs}
        self.assertEqual(geos, {"PL", "NL"})
        for job in self.jobs:
            self.assertEqual(job["parent_creative_id"], "buyer12abcd")
            self.assertTrue(job["job_id"].endswith("buyer12a"))
            self.assertEqual(job["format"], "9x16")
            self.assertEqual(job["status"], "blocked")
            self.assertIn(job["blocked_reason"], {"nl_untargeted_gambling_ads", "pl_private_casino_ads"})

    def test_allow_unlocks_restricted_geos(self) -> None:
        jobs = multiply.multiply(
            analysis=self.analysis,
            geos=["PL", "NL"],
            compliance_allow=True,
        )
        self.assertEqual(len(jobs), 4)
        self.assertTrue(all(j["status"] != "blocked" or "geo" not in (j.get("blocked_reason") or "") for j in jobs))
        self.assertTrue(all(j["status"] != "blocked" for j in jobs))

    def test_open_geos_are_ready(self) -> None:
        jobs = multiply.multiply(analysis=self.analysis, geos=["CA-EN", "AU"], cta_ids=["play_now"])
        self.assertEqual(len(jobs), 2)
        self.assertTrue(all(j["status"] != "blocked" for j in jobs))
        payload = multiply.summary_payload(self.analysis, jobs)
        self.assertEqual(payload["ready_jobs"], 2)
        self.assertEqual(payload["n8n_geos"], ["AU", "CA-EN"])

    def test_pl_uses_polish_cta_nl_falls_back_to_en(self) -> None:
        pl_play = next(
            j for j in self.jobs if j["cta_id"] == "play_now" and j["render"]["variables"]["forge_geo"] == "PL"
        )
        nl_play = next(
            j for j in self.jobs if j["cta_id"] == "play_now" and j["render"]["variables"]["forge_geo"] == "NL"
        )
        self.assertEqual(pl_play["render"]["variables"]["cta_main"], "GRAJ TERAZ")
        self.assertEqual(nl_play["render"]["variables"]["cta_main"], "SPEEL NU")
        self.assertEqual(nl_play["locale"], "nl")

    def test_hyphenated_geo_is_safe_in_job_id(self) -> None:
        jobs = multiply.multiply(analysis=self.analysis, geos=["CH-DE"], cta_ids=["play_now"])
        self.assertEqual(len(jobs), 1)
        self.assertEqual(jobs[0]["geo"], "chde")
        self.assertRegex(jobs[0]["job_id"], r"^[A-Za-z0-9_]+$")
        self.assertIn("chde", jobs[0]["job_id"])

    def test_summary_counts(self) -> None:
        payload = multiply.summary_payload(self.analysis, self.jobs)
        self.assertEqual(payload["jobs"], 4)
        self.assertEqual(payload["ready_jobs"], 0)
        self.assertEqual(payload["blocked_jobs"], 4)
        self.assertEqual(payload["beats"], 6)
        self.assertEqual(set(payload["geos"]), {"PL", "NL"})
        self.assertEqual(set(payload["blocked_geos"]), {"PL", "NL"})
        self.assertEqual(payload["n8n_geos"], ["NL", "PL"])


class ShortAdScenarioTests(unittest.TestCase):
    def test_six_second_uses_hook_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            video = Path(tmp) / "short.mp4"
            make_silent_mp4(video, width=1080, height=1920, duration=6.0)
            analysis = analyze_upload.analyze(video=video, analysis_id="shorthook01")
            self.assertEqual(analysis["scenario_id"], "AD_HOOK_ONLY")
            self.assertEqual(len(analysis["beats"]), 2)
            self.assertEqual(analysis["beats"][0]["beat_id"], "B01")
            self.assertEqual(analysis["beats"][-1]["beat_id"], "B06")

    def test_twelve_second_uses_mechanic(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            video = Path(tmp) / "mid.mp4"
            make_silent_mp4(video, width=1080, height=1920, duration=12.0)
            analysis = analyze_upload.analyze(video=video, analysis_id="mechanic12xx")
            self.assertEqual(analysis["scenario_id"], "AD_MECHANIC_SHOWCASE")
            self.assertEqual(len(analysis["beats"]), 3)
        self.assertEqual(analyze_upload.pick_scenario_id(5.0), "AD_HOOK_ONLY")
        self.assertEqual(analyze_upload.pick_scenario_id(12.0), "AD_MECHANIC_SHOWCASE")
        self.assertEqual(analyze_upload.pick_scenario_id(30.0), "AD_B")


class GuessGameTests(unittest.TestCase):
    def test_aliases(self) -> None:
        self.assertEqual(analyze_upload.guess_game_id("Sweet Bonanza"), "vs10bbbonanza")
        self.assertEqual(analyze_upload.guess_game_id(""), "vs20olympgate")


if __name__ == "__main__":
    unittest.main()
