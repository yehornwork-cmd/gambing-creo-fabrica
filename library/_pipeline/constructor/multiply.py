#!/usr/bin/env python3
"""Multiply a buyer-analyzed master into CreativeJobs (locale × CTA).

This is the Forge buyer loop: one uploaded winner → N draft jobs with
`parent_creative_id` set, so later F5 substitution-group clones have lineage.
Footage stays the master; copy/CTA/disclaimer change per market.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

CONSTRUCTOR_DIR = Path(__file__).resolve().parent
REPO_ROOT = CONSTRUCTOR_DIR.parents[2]

import explode  # noqa: E402  (sibling module)
import lint  # noqa: E402

GEO_ID_RE = re.compile(r"[^a-z0-9]+")


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def sanitize_geo_id(geo: str) -> str:
    return GEO_ID_RE.sub("", geo.strip().lower()) or "geo"


def load_compliance(constructor_dir: Path, repo_root: Path, rel: str | None) -> dict[str, Any]:
    fallback = {"geo": {"default": {"disclaimer_18_plus": "18+ | Play responsibly"}}}
    if not rel:
        return fallback
    stripped = rel[8:] if rel.startswith("library/") else rel
    candidates = [
        repo_root / rel,
        repo_root / stripped,
        constructor_dir.parents[2] / rel,
        constructor_dir.parents[1] / stripped,
        constructor_dir.parent.parent / stripped,
    ]
    for path in candidates:
        if path.is_file():
            return explode.load_json(path)
    return fallback


def load_geo_map(constructor_dir: Path) -> dict[str, dict[str, str]]:
    payload = load_json(constructor_dir / "geo_locale_map.json")
    return {code.upper(): row for code, row in payload.get("geos", {}).items()}


def resolve_geo(geo: str, geo_map: dict[str, dict[str, str]]) -> dict[str, str]:
    key = geo.strip().upper()
    row = geo_map.get(key)
    if row:
        return {
            "id": key,
            "locale": row["locale"],
            "language": row.get("language") or row["locale"],
            "pack": row.get("pack") or "locale_packs/en.json",
            "gate": row.get("gate") or "open",
            "gate_reason": row.get("gate_reason") or "",
        }
    return {
        "id": key,
        "locale": key.lower(),
        "language": key.lower(),
        "pack": "locale_packs/en.json",
        "gate": "open",
        "gate_reason": "",
    }


def cta_copy_with_fallback(ctas: dict[str, Any], cta_id: str, locale: str) -> dict[str, str]:
    for item in ctas.get("ctas", []):
        if item["cta_id"] != cta_id:
            continue
        locales = item.get("locales") or {}
        if locale in locales:
            return dict(locales[locale])
        if "en" in locales:
            return dict(locales["en"])
        if "ru" in locales:
            return dict(locales["ru"])
        raise KeyError(f"CTA {cta_id} has no copy for locale {locale} (and no en/ru fallback)")
    raise KeyError(f"Unknown cta_id: {cta_id}")


def enabled_ctas(matrix: dict[str, Any]) -> list[dict[str, Any]]:
    return explode.axis_values(matrix, "cta", include_stubs=False)


def format_axis(matrix: dict[str, Any], format_id: str) -> dict[str, Any]:
    for item in matrix.get("axes", {}).get("format", []):
        if item.get("id") == format_id:
            return item
    return {"id": format_id, "enabled": True}


def analysis_beats_as_lineage(analysis: dict[str, Any]) -> list[dict[str, Any]]:
    beats: list[dict[str, Any]] = []
    for beat in analysis.get("beats") or []:
        beats.append(
            {
                "beat_id": beat["beat_id"],
                "arc_slot_id": beat.get("arc_slot_id", ""),
                "segment_id": beat.get("segment_id"),
                "substitution_group": beat.get("substitution_group"),
                "taxonomy_tags": list(beat.get("taxonomy_tags") or []),
                "duration_sec": beat.get("duration_sec"),
                "t_start": beat.get("t_start"),
                "t_end": beat.get("t_end"),
            }
        )
    return beats


def multiply(
    *,
    analysis: dict[str, Any],
    geos: list[str],
    constructor_dir: Path | None = None,
    repo_root: Path | None = None,
    cta_ids: list[str] | None = None,
    compliance_allow: bool = False,
) -> list[dict[str, Any]]:
    constructor_dir = constructor_dir or CONSTRUCTOR_DIR
    repo_root = repo_root or REPO_ROOT
    if not geos:
        raise ValueError("geos must not be empty")

    matrix = explode.load_json(constructor_dir / "variant_matrix.json")
    scenario = explode.load_scenario(analysis.get("scenario_id") or matrix["scenario_id"], constructor_dir / "scenarios")
    ctas = explode.load_json(constructor_dir / "ctas" / "catalog.json")
    geo_map = load_geo_map(constructor_dir)
    compliance = load_compliance(constructor_dir, repo_root, matrix.get("compliance_file"))

    parent_id = analysis.get("parent_creative_id") or analysis.get("analysis_id")
    format_id = analysis.get("format") or "9x16"
    fmt = format_axis(matrix, format_id)
    selected_ctas = enabled_ctas(matrix)
    if cta_ids:
        wanted = set(cta_ids)
        selected_ctas = [c for c in selected_ctas if c["id"] in wanted]
    if not selected_ctas:
        raise ValueError("no enabled CTAs to multiply")

    game_id = analysis.get("game_id") or matrix["game_id"]
    jobs: list[dict[str, Any]] = []
    for geo_code in geos:
        geo_row = resolve_geo(geo_code, geo_map)
        pack_path = constructor_dir / geo_row["pack"]
        if not pack_path.is_file():
            pack_path = constructor_dir / "locale_packs" / "en.json"
        locale_pack = explode.load_json(pack_path)
        locale = {"id": geo_row["locale"]}
        geo = {"id": sanitize_geo_id(geo_row["id"]), "locale": geo_row["locale"]}
        disclaimer = explode.compliance_disclaimer(compliance, geo["id"])
        if disclaimer == "18+ | Play responsibly":
            disclaimer = explode.compliance_disclaimer(compliance, "default")

        for cta in selected_ctas:
            job = explode.build_job(
                matrix={
                    **matrix,
                    "game_id": game_id,
                    "scenario_id": analysis.get("scenario_id") or matrix["scenario_id"],
                    "defaults": {
                        **matrix.get("defaults", {}),
                        "parent_creative_id": parent_id,
                    },
                },
                scenario=scenario,
                locale=locale,
                fmt=fmt,
                cta=cta,
                geo=geo,
                locale_pack=locale_pack,
                cta_vars=cta_copy_with_fallback(ctas, cta["id"], locale["id"]),
                disclaimer=disclaimer,
            )
            job["parent_creative_id"] = parent_id
            job["lineage"]["parent_creative_id"] = parent_id
            job["lineage"]["beats"] = analysis_beats_as_lineage(analysis) or job["lineage"]["beats"]
            job["job_id"] = f"{job['job_id']}_{str(parent_id)[:8]}"
            job["render"]["output_name"] = job["job_id"]
            job["render"]["variables"]["name"] = job["job_id"]
            job["render"]["variables"]["parent_creative_id"] = parent_id
            job["render"]["variables"]["forge_geo"] = geo_row["id"]
            if geo_row.get("gate") == "restricted" and not compliance_allow:
                job["status"] = "blocked"
                job["blocked_reason"] = geo_row.get("gate_reason") or "geo_restricted"
            jobs.append(job)
    bonus_in_source = bool((analysis.get("vlm") or {}).get("has_bonus_footage"))
    return lint.lint_jobs(jobs, bonus_in_source=bonus_in_source)


def summary_payload(analysis: dict[str, Any], jobs: list[dict[str, Any]]) -> dict[str, Any]:
    ready = [job for job in jobs if job.get("status") != "blocked"]
    blocked = [job for job in jobs if job.get("status") == "blocked"]
    geo_of = lambda job: job["render"]["variables"].get("forge_geo") or job["geo"]
    return {
        "analysis_id": analysis.get("analysis_id"),
        "parent_creative_id": analysis.get("parent_creative_id") or analysis.get("analysis_id"),
        "format": analysis.get("format"),
        "duration_sec": (analysis.get("probe") or {}).get("duration_sec"),
        "beats": len(analysis.get("beats") or []),
        "jobs": len(jobs),
        "ready_jobs": len(ready),
        "blocked_jobs": len(blocked),
        "job_ids": [job["job_id"] for job in jobs],
        "geos": sorted({geo_of(job) for job in jobs}),
        "ready_geos": sorted({geo_of(job) for job in ready}),
        "blocked_geos": sorted({geo_of(job) for job in blocked}),
        "ctas": sorted({job["cta_id"] for job in jobs}),
        "n8n_geos": sorted({geo_of(job) for job in ready})
        or sorted({geo_of(job) for job in jobs}),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Explode a CreativeAnalysis into locale × CTA CreativeJobs.")
    parser.add_argument("--analysis", type=Path, required=True, help="Path to CreativeAnalysis JSON")
    parser.add_argument("--geos", required=True, help="Comma-separated Forge geo codes (PL,NL,...)")
    parser.add_argument("--allow", action="store_true", help="Set compliance.allow for restricted geos (NL/PL)")
    parser.add_argument("--out-dir", type=Path, default=None)
    parser.add_argument("--dry-run", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if not args.analysis.is_file():
        print(f"error: analysis not found: {args.analysis}", file=sys.stderr)
        return 2
    analysis = load_json(args.analysis)
    geos = [g.strip() for g in args.geos.split(",") if g.strip()]
    jobs = multiply(analysis=analysis, geos=geos, compliance_allow=args.allow)
    payload = summary_payload(analysis, jobs)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    if args.dry_run:
        return 0
    out_dir = args.out_dir or (CONSTRUCTOR_DIR / "jobs" / "buyer" / str(analysis.get("analysis_id")))
    out_dir.mkdir(parents=True, exist_ok=True)
    for job in jobs:
        write_json(out_dir / f"{job['job_id']}.json", job)
    write_json(out_dir / "batch.json", explode.batch_payload(jobs))
    write_json(out_dir / "jobs.json", jobs)
    write_json(out_dir / "analysis.json", analysis)
    print(f"wrote {len(jobs)} jobs → {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
