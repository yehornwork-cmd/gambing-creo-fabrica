#!/usr/bin/env python3
"""Clone a winner CreativeJob via substitution_group footage swaps (F5.1).

Buyer uploads keep the same master; this path is for library/VOD clips that
share a substitution_group. One tagged winner → N draft jobs with
parent_creative_id set.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

CONSTRUCTOR_DIR = Path(__file__).resolve().parent

import explode  # noqa: E402


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def load_catalog(constructor_dir: Path | None = None) -> dict[str, list[dict[str, Any]]]:
    constructor_dir = constructor_dir or CONSTRUCTOR_DIR
    payload = load_json(constructor_dir / "substitution_catalog.json")
    groups = payload.get("groups") or {}
    return {str(k): list(v) for k, v in groups.items()}


def alternatives_for(group: str, catalog: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    rows = catalog.get(group) or []
    return [row for row in rows if row.get("segment_id")]


def clone_winner(
    job: dict[str, Any],
    *,
    catalog: dict[str, list[dict[str, Any]]] | None = None,
    groups: list[str] | None = None,
    constructor_dir: Path | None = None,
) -> list[dict[str, Any]]:
    """Return clones including the original (index 0 is the parent row)."""
    catalog = catalog if catalog is not None else load_catalog(constructor_dir)
    parent_id = job.get("parent_creative_id") or job.get("job_id")
    beats = list((job.get("lineage") or {}).get("beats") or [])
    target_groups = groups or sorted(
        {
            str(b.get("substitution_group"))
            for b in beats
            if b.get("substitution_group") and len(alternatives_for(str(b["substitution_group"]), catalog)) > 1
        }
    )
    clones = [json.loads(json.dumps(job))]
    clones[0]["parent_creative_id"] = parent_id
    clones[0]["lineage"]["parent_creative_id"] = parent_id

    for group in target_groups:
        alts = alternatives_for(group, catalog)
        if len(alts) < 2:
            continue
        current = list(clones)
        clones = []
        for base in current:
            for alt in alts:
                row = json.loads(json.dumps(base))
                new_beats = []
                swapped = False
                for beat in row.get("lineage", {}).get("beats") or []:
                    item = dict(beat)
                    if item.get("substitution_group") == group:
                        if item.get("segment_id") != alt["segment_id"]:
                            swapped = True
                        item["segment_id"] = alt["segment_id"]
                    new_beats.append(item)
                row["lineage"]["beats"] = new_beats
                row["parent_creative_id"] = parent_id
                row["lineage"]["parent_creative_id"] = parent_id
                suffix = str(alt["segment_id"]).replace("seg_", "")[:16]
                if swapped:
                    row["job_id"] = f"{base['job_id']}_{suffix}"
                    row["render"]["output_name"] = row["job_id"]
                    row["render"]["variables"]["name"] = row["job_id"]
                    row["render"]["variables"]["parent_creative_id"] = parent_id
                    row["render"]["variables"][f"sub_{group}"] = alt["segment_id"]
                    row["status"] = "draft"
                clones.append(row)
    # De-dupe identical job_ids (unswapped parent copies)
    seen: set[str] = set()
    unique: list[dict[str, Any]] = []
    for row in clones:
        jid = row["job_id"]
        if jid in seen:
            continue
        seen.add(jid)
        unique.append(row)
    return unique


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Clone a CreativeJob across substitution_group alternatives.")
    parser.add_argument("--job", type=Path, required=True)
    parser.add_argument("--group", action="append", dest="groups")
    parser.add_argument("--out-dir", type=Path, default=None)
    parser.add_argument("--dry-run", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if not args.job.is_file():
        print(f"error: job not found: {args.job}", file=sys.stderr)
        return 2
    job = load_json(args.job)
    clones = clone_winner(job, groups=args.groups)
    print(json.dumps({"parent": job.get("job_id"), "clones": len(clones), "job_ids": [c["job_id"] for c in clones]}, indent=2))
    if args.dry_run:
        return 0
    out_dir = args.out_dir or (CONSTRUCTOR_DIR / "jobs" / "clones" / str(job.get("job_id")))
    for row in clones:
        write_json(out_dir / f"{row['job_id']}.json", row)
    write_json(out_dir / "batch.json", explode.batch_payload(clones))
    print(f"wrote {len(clones)} clones → {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
