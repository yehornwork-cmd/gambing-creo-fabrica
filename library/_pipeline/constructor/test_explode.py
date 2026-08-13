#!/usr/bin/env python3
"""Unit tests for constructor variant explosion."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

CONSTRUCTOR = Path(__file__).resolve().parent

import explode  # noqa: E402  (sibling module)


class ExplodeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.matrix = explode.load_json(CONSTRUCTOR / "variant_matrix.json")
        cls.jobs = explode.explode(
            constructor_dir=CONSTRUCTOR,
            matrix=cls.matrix,
            include_stubs=False,
            repo_root=explode.REPO_ROOT,
        )

    def test_default_matrix_is_four_jobs(self) -> None:
        # ru+pl × 9x16 × 2 CTAs, geo locked to locale
        self.assertEqual(len(self.jobs), 4)
        ids = {job["job_id"] for job in self.jobs}
        self.assertEqual(
            ids,
            {
                "vs20olympgate_AD_B_ru_ru_9x16_play_now",
                "vs20olympgate_AD_B_ru_ru_9x16_bonus_first_deposit",
                "vs20olympgate_AD_B_pl_pl_9x16_play_now",
                "vs20olympgate_AD_B_pl_pl_9x16_bonus_first_deposit",
            },
        )

    def test_geo_matches_locale(self) -> None:
        for job in self.jobs:
            self.assertEqual(job["locale"], job["geo"])

    def test_lineage_has_six_ad_b_beats(self) -> None:
        job = self.jobs[0]
        beats = job["lineage"]["beats"]
        self.assertEqual(len(beats), 6)
        self.assertEqual(job["lineage"]["arc_id"], "ARC_TEASE_NEAR_MISS_PAYOFF")
        self.assertEqual(beats[0]["segment_id"], "seg_v2_motion_hook")
        self.assertEqual(beats[2]["substitution_group"], "scatter_bonus_4")
        self.assertIsNone(job["parent_creative_id"])

    def test_variables_include_locale_cta_and_disclaimer(self) -> None:
        ru_play = next(j for j in self.jobs if j["cta_id"] == "play_now" and j["locale"] == "ru")
        vars_ = ru_play["render"]["variables"]
        self.assertEqual(vars_["vo_b01"], "Gates of Olympus. Ставка €2. Поехали.")
        self.assertEqual(vars_["cta_main"], "ИГРАТЬ")
        self.assertIn("18+", vars_["disclaimer"])
        self.assertEqual(vars_["name"], ru_play["job_id"])

        pl_bonus = next(
            j for j in self.jobs if j["cta_id"] == "bonus_first_deposit" and j["locale"] == "pl"
        )
        self.assertEqual(pl_bonus["render"]["variables"]["cta_main"], "ODBIERZ BONUS")
        self.assertIn("Graj odpowiedzialnie", pl_bonus["render"]["variables"]["disclaimer"])

    def test_batch_rows_are_flat(self) -> None:
        payload = explode.batch_payload(self.jobs)
        self.assertEqual(len(payload["rows"]), 4)
        for row in payload["rows"]:
            self.assertIn("name", row)
            for value in row.values():
                self.assertIsInstance(value, (str, int, float, bool))

    def test_include_stubs_adds_square_and_landscape(self) -> None:
        stub_jobs = explode.explode(
            constructor_dir=CONSTRUCTOR,
            matrix=self.matrix,
            include_stubs=True,
            repo_root=explode.REPO_ROOT,
        )
        formats = {job["format"] for job in stub_jobs}
        self.assertEqual(formats, {"9x16", "1x1", "16x9"})
        self.assertEqual(len(stub_jobs), 12)
        blocked = [job for job in stub_jobs if job["format"] != "9x16"]
        self.assertTrue(blocked)
        self.assertTrue(all(job["status"] == "blocked" for job in blocked))

    def test_html_declares_every_batch_variable(self) -> None:
        html = (explode.REPO_ROOT / "output" / "gates-pilot-ad-v3" / "index.html").read_text(
            encoding="utf-8"
        )
        marker = "data-composition-variables='"
        start = html.index(marker) + len(marker)
        end = html.index("'", start)
        declared = {item["id"] for item in json.loads(html[start:end])}
        payload = explode.batch_payload(self.jobs)
        for row in payload["rows"]:
            missing = set(row) - declared
            self.assertFalse(missing, msg=f"undeclared batch keys: {sorted(missing)}")


class CatalogTests(unittest.TestCase):
    def test_catalog_lists_live_arcs_and_remaining_stubs(self) -> None:
        catalog = json.loads((CONSTRUCTOR / "scenarios" / "catalog.json").read_text(encoding="utf-8"))
        by_id = {s["scenario_id"]: s for s in catalog["scenarios"]}
        self.assertEqual(by_id["AD_B"]["status"], "partial")
        self.assertEqual(by_id["AD_HOOK_ONLY"]["status"], "partial")
        self.assertEqual(by_id["AD_MECHANIC_SHOWCASE"]["status"], "partial")
        stubs = [s for s in catalog["scenarios"] if s["status"] == "stub"]
        self.assertEqual(len(stubs), 3)
        for entry in catalog["scenarios"]:
            path = CONSTRUCTOR / "scenarios" / entry["file"]
            self.assertTrue(path.is_file(), msg=entry["file"])
        hook = json.loads((CONSTRUCTOR / "scenarios" / "AD_HOOK_ONLY.json").read_text(encoding="utf-8"))
        self.assertGreaterEqual(len(hook["beats"]), 2)


if __name__ == "__main__":
    unittest.main()
