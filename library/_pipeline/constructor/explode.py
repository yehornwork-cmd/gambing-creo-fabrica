#!/usr/bin/env python3
"""Explode a constructor variant matrix into CreativeJobs + HyperFrames batch rows."""

from __future__ import annotations

import argparse
import json
import sys
from itertools import product
from pathlib import Path
from typing import Any

CONSTRUCTOR_DIR = Path(__file__).resolve().parent
REPO_ROOT = CONSTRUCTOR_DIR.parents[2]
DEFAULT_MATRIX = CONSTRUCTOR_DIR / "variant_matrix.json"
DEFAULT_SCENARIOS = CONSTRUCTOR_DIR / "scenarios"
DEFAULT_CTAS = CONSTRUCTOR_DIR / "ctas" / "catalog.json"
DEFAULT_JOBS_DIR = CONSTRUCTOR_DIR / "jobs"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def axis_values(matrix: dict[str, Any], name: str, include_stubs: bool) -> list[dict[str, Any]]:
    values = matrix.get("axes", {}).get(name, [])
    selected: list[dict[str, Any]] = []
    for item in values:
        if item.get("enabled"):
            selected.append(item)
            continue
        if include_stubs and item.get("status") == "stub":
            selected.append(item)
    return selected


def load_scenario(scenario_id: str, scenarios_dir: Path) -> dict[str, Any]:
    catalog = load_json(scenarios_dir / "catalog.json")
    entry = next((s for s in catalog["scenarios"] if s["scenario_id"] == scenario_id), None)
    if entry is None:
        raise FileNotFoundError(f"Unknown scenario_id: {scenario_id}")
    return load_json(scenarios_dir / entry["file"])


def load_locale_pack(constructor_dir: Path, pack_rel: str) -> dict[str, Any]:
    return load_json(constructor_dir / pack_rel)


def cta_copy(ctas: dict[str, Any], cta_id: str, locale: str) -> dict[str, str]:
    for item in ctas.get("ctas", []):
        if item["cta_id"] == cta_id:
            locales = item.get("locales", {})
            if locale not in locales:
                raise KeyError(f"CTA {cta_id} has no copy for locale {locale}")
            return dict(locales[locale])
    raise KeyError(f"Unknown cta_id: {cta_id}")


def compliance_disclaimer(compliance: dict[str, Any], geo: str) -> str:
    packs = compliance.get("geo", {})
    pack = packs.get(geo) or packs.get("default") or {}
    return str(pack.get("disclaimer_18_plus", "18+ | Play responsibly"))


def beat_lineage(scenario: dict[str, Any]) -> list[dict[str, Any]]:
    beats: list[dict[str, Any]] = []
    for beat in scenario.get("beats", []):
        beats.append(
            {
                "beat_id": beat["beat_id"],
                "arc_slot_id": beat.get("arc_slot_id", ""),
                "segment_id": beat.get("segment_id"),
                "substitution_group": beat.get("substitution_group"),
                "taxonomy_tags": list(beat.get("taxonomy_tags", [])),
                "duration_sec": beat.get("duration_sec"),
            }
        )
    return beats


def job_id_for(
    game_id: str,
    scenario_id: str,
    locale: str,
    geo: str,
    fmt: str,
    cta_id: str,
) -> str:
    return f"{game_id}_{scenario_id}_{locale}_{geo}_{fmt}_{cta_id}"


def combinations(
    matrix: dict[str, Any],
    include_stubs: bool,
) -> list[tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]]:
    locales = axis_values(matrix, "locale", include_stubs)
    formats = axis_values(matrix, "format", include_stubs)
    ctas = axis_values(matrix, "cta", include_stubs)
    geos = axis_values(matrix, "geo", include_stubs)
    if not all((locales, formats, ctas, geos)):
        return []

    match_locale = matrix.get("constraints", {}).get("geo_must_match_locale", True)
    rows: list[tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]] = []
    for locale, fmt, cta, geo in product(locales, formats, ctas, geos):
        if match_locale and geo.get("locale") not in (None, locale["id"]):
            continue
        rows.append((locale, fmt, cta, geo))
    return rows


def build_job(
    *,
    matrix: dict[str, Any],
    scenario: dict[str, Any],
    locale: dict[str, Any],
    fmt: dict[str, Any],
    cta: dict[str, Any],
    geo: dict[str, Any],
    locale_pack: dict[str, Any],
    cta_vars: dict[str, str],
    disclaimer: str,
) -> dict[str, Any]:
    defaults = matrix.get("defaults", {})
    game_id = matrix["game_id"]
    scenario_id = matrix["scenario_id"]
    jid = job_id_for(game_id, scenario_id, locale["id"], geo["id"], fmt["id"], cta["id"])

    variables: dict[str, str] = {"name": jid}
    variables.update(locale_pack.get("variables", {}))
    variables.update(cta_vars)
    variables["disclaimer"] = disclaimer
    variables["locale"] = locale["id"]
    variables["geo"] = geo["id"]
    variables["format"] = fmt["id"]
    variables["cta_id"] = cta["id"]

    status = "draft"
    blocked_reason = None
    if scenario.get("status") == "stub" or fmt.get("status") == "stub":
        status = "blocked"
        blocked_reason = "stub_axis_or_scenario"
    elif locale_pack.get("status") == "placeholder" or geo.get("copy_status") == "placeholder":
        # Still renderable as a template preview; paid media stays human-gated.
        status = "draft"

    return {
        "job_id": jid,
        "schema_version": "1.0.0",
        "game_id": game_id,
        "scenario_id": scenario_id,
        "locale": locale["id"],
        "geo": geo["id"],
        "format": fmt["id"],
        "cta_id": cta["id"],
        "hook_id": defaults.get("hook_id") or scenario.get("hook_id_default"),
        "parent_creative_id": defaults.get("parent_creative_id"),
        "status": status,
        "blocked_reason": blocked_reason,
        "lineage": {
            "template_id": matrix.get("template_id") or scenario.get("template_id"),
            "arc_id": scenario.get("arc_id", ""),
            "source_scenario_status": scenario.get("status", ""),
            "parent_creative_id": defaults.get("parent_creative_id"),
            "beats": beat_lineage(scenario),
        },
        "render": {
            "project": matrix.get("hyperframes_project") or scenario.get("hyperframes_project"),
            "output_name": jid,
            "variables": variables,
        },
    }


def explode(
    *,
    constructor_dir: Path,
    matrix: dict[str, Any],
    include_stubs: bool,
    repo_root: Path,
) -> list[dict[str, Any]]:
    scenario = load_scenario(matrix["scenario_id"], constructor_dir / "scenarios")
    ctas = load_json(constructor_dir / "ctas" / "catalog.json")
    compliance_rel = matrix.get("compliance_file")
    compliance = load_json(repo_root / compliance_rel) if compliance_rel else {"geo": {}}

    jobs: list[dict[str, Any]] = []
    for locale, fmt, cta, geo in combinations(matrix, include_stubs):
        pack = load_locale_pack(constructor_dir, locale["pack"])
        jobs.append(
            build_job(
                matrix=matrix,
                scenario=scenario,
                locale=locale,
                fmt=fmt,
                cta=cta,
                geo=geo,
                locale_pack=pack,
                cta_vars=cta_copy(ctas, cta["id"], locale["id"]),
                disclaimer=compliance_disclaimer(compliance, geo["id"]),
            )
        )
    return jobs


def batch_payload(jobs: list[dict[str, Any]]) -> dict[str, Any]:
    return {"rows": [job["render"]["variables"] for job in jobs]}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Explode constructor variant matrix into CreativeJobs and HyperFrames batch rows."
    )
    parser.add_argument(
        "--matrix",
        type=Path,
        default=DEFAULT_MATRIX,
        help="Path to variant_matrix.json",
    )
    parser.add_argument(
        "--include-stubs",
        action="store_true",
        help="Include stub formats/scenarios (marked blocked)",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=DEFAULT_JOBS_DIR,
        help="Directory for job JSON files and batch.json",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print count and job_ids without writing files",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    matrix_path: Path = args.matrix
    if not matrix_path.is_file():
        print(f"error: matrix not found: {matrix_path}", file=sys.stderr)
        return 2

    matrix = load_json(matrix_path)
    constructor_dir = matrix_path.parent
    jobs = explode(
        constructor_dir=constructor_dir,
        matrix=matrix,
        include_stubs=args.include_stubs,
        repo_root=REPO_ROOT,
    )

    print(f"jobs: {len(jobs)}")
    for job in jobs:
        flag = f" [{job['status']}]" if job["status"] != "draft" else ""
        print(f"  - {job['job_id']}{flag}")

    if args.dry_run:
        return 0

    out_dir: Path = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    for job in jobs:
        write_json(out_dir / f"{job['job_id']}.json", job)
    write_json(out_dir / "batch.json", batch_payload(jobs))
    write_json(out_dir / "jobs.json", jobs)
    print(f"wrote {len(jobs)} jobs + batch.json → {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
