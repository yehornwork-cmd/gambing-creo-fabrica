#!/usr/bin/env python3
"""Tests for buyer URL allowlist (no network)."""

from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path

DEPLOY = Path(__file__).resolve().parent
sys.path.insert(0, str(DEPLOY))
os.environ.setdefault("PIPELINE_ROOT", str(DEPLOY.parent))

import buyer_jobs  # noqa: E402


class AllowlistTests(unittest.TestCase):
    def test_forge_hosts(self) -> None:
        self.assertTrue(buyer_jobs._is_allowed_url("https://forge.vizioner.xyz/media/a.mp4"))
        self.assertTrue(buyer_jobs._is_allowed_url("http://forge-forge-1/media/a.mp4"))
        self.assertTrue(buyer_jobs._is_allowed_url("https://n8n.vizioner.xyz/x"))

    def test_rejects_external(self) -> None:
        self.assertFalse(buyer_jobs._is_allowed_url("https://evil.example/x.mp4"))
        self.assertFalse(buyer_jobs._is_allowed_url("file:///etc/passwd"))
        self.assertFalse(buyer_jobs._is_allowed_url("https://127.0.0.1/x"))


if __name__ == "__main__":
    unittest.main()
