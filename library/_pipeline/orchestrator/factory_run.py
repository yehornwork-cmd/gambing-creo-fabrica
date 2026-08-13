#!/usr/bin/env python3
"""Creative Factory orchestrator — status and tick for MVP (P*) and scale (F*) chunks."""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]
PIPELINE = REPO_ROOT / "library" / "_pipeline"
ROADMAPS = {
    "mvp": PIPELINE / "phases" / "MVP_ROADMAP.md",
    "scale": PIPELINE / "phases" / "FACTORY_SCALE.md",
}
STATE_FILE = PIPELINE / "state.json"
RUNS_DIR = PIPELINE / "runs"

CHUNK_RE = re.compile(
    r"^\|\s*((?:P|F)\d+\.\d+)\s*\|\s*([^|]+)\|\s*([^|]+)(?:\|\s*([^|]+))?\s*\|$"
)


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def load_state() -> dict[str, Any]:
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    return {
        "version": 1,
        "updated_at": utc_now(),
        "completed": [],
        "in_progress": None,
        "blocked": {},
        "runs": [],
    }


def save_state(state: dict[str, Any]) -> None:
    state["updated_at"] = utc_now()
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")


def parse_roadmap(roadmap: str = "mvp") -> list[dict[str, str]]:
    path = ROADMAPS[roadmap]
    if not path.exists():
        return []
    chunks: list[dict[str, str]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        match = CHUNK_RE.match(line.strip())
        if not match:
            continue
        chunk_id, title, acceptance, blocker = match.groups()
        chunks.append(
            {
                "id": chunk_id.strip(),
                "title": title.strip(),
                "acceptance": acceptance.strip(),
                "blocker": (blocker or "").strip(),
            }
        )
    return chunks


def all_known_chunk_ids() -> set[str]:
    ids: set[str] = set()
    for name in ROADMAPS:
        ids.update(c["id"] for c in parse_roadmap(name))
    return ids


def next_chunk(state: dict[str, Any], chunks: list[dict[str, str]]) -> dict[str, str] | None:
    completed = set(state.get("completed", []))
    blocked = set(state.get("blocked", {}).keys())
    for chunk in chunks:
        cid = chunk["id"]
        if cid in completed or cid in blocked:
            continue
        if chunk.get("blocker"):
            state.setdefault("blocked", {})[cid] = chunk["blocker"]
            continue
        return chunk
    return None


def run_id_for(chunk_id: str) -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"{stamp}_{chunk_id}"


def _print_lane(name: str, chunks: list[dict[str, str]], state: dict[str, Any]) -> None:
    completed = set(state.get("completed", []))
    blocked = state.get("blocked", {})
    pending = [c["id"] for c in chunks if c["id"] not in completed and c["id"] not in blocked]
    done = [c["id"] for c in chunks if c["id"] in completed]
    print(f"  {name}: {len(done)}/{len(chunks)} complete")
    if done:
        print(f"           {', '.join(done)}")
    lane_blocked = {cid: blocked[cid] for cid in blocked if any(c["id"] == cid for c in chunks)}
    if lane_blocked:
        for cid, reason in lane_blocked.items():
            print(f"           blocked {cid}: {reason}")
    if pending:
        print(f"           next: {pending[0]}")
    elif not lane_blocked:
        print("           next: (all chunks complete)")
    else:
        print("           next: (blocked)")


def cmd_status(_: argparse.Namespace) -> int:
    state = load_state()
    print("Creative Factory — status")
    print(f"  repo:      {REPO_ROOT}")
    print(f"  updated:   {state.get('updated_at', '—')}")
    _print_lane("mvp", parse_roadmap("mvp"), state)
    _print_lane("scale", parse_roadmap("scale"), state)
    if state.get("in_progress"):
        print(f"  in flight: {state['in_progress']}")
    return 0


def cmd_tick(args: argparse.Namespace) -> int:
    state = load_state()
    roadmap = getattr(args, "roadmap", "mvp")
    chunks = parse_roadmap(roadmap)
    if not chunks:
        print(f"ERROR: {roadmap} roadmap not found or empty.", file=sys.stderr)
        return 1

    chunk = next_chunk(state, chunks)
    if chunk is None:
        save_state(state)
        print("No actionable chunk — all complete or blocked.")
        cmd_status(args)
        return 0

    rid = run_id_for(chunk["id"])
    run_dir = RUNS_DIR / rid
    run_dir.mkdir(parents=True, exist_ok=True)

    state["in_progress"] = chunk["id"]
    state.setdefault("runs", []).append(
        {"run_id": rid, "chunk_id": chunk["id"], "started_at": utc_now()}
    )
    save_state(state)

    run_md = f"""# Run {rid}

- **chunk:** {chunk['id']} — {chunk['title']}
- **started:** {utc_now()}
- **acceptance:** {chunk['acceptance']}

## Agent instructions

Implement this chunk only. Log actions and assumptions below. Commit + push when done, then mark complete:

```bash
python3 library/_pipeline/orchestrator/factory_run.py complete {chunk['id']}
```

## Actions

- [ ] (agent fills in)

## Blockers

- (none yet)

## Notes

"""
    (run_dir / "RUN.md").write_text(run_md, encoding="utf-8")

    payload = {
        "run_id": rid,
        "chunk_id": chunk["id"],
        "title": chunk["title"],
        "acceptance": chunk["acceptance"],
        "run_log": str(run_dir / "RUN.md"),
    }
    print(json.dumps(payload, indent=2))
    return 0


def cmd_complete(args: argparse.Namespace) -> int:
    state = load_state()
    chunk_id = args.chunk_id
    if chunk_id not in all_known_chunk_ids():
        print(f"ERROR: unknown chunk {chunk_id}", file=sys.stderr)
        return 1
    completed = set(state.get("completed", []))
    completed.add(chunk_id)
    state["completed"] = sorted(completed)
    if state.get("in_progress") == chunk_id:
        state["in_progress"] = None
    state.get("blocked", {}).pop(chunk_id, None)
    save_state(state)
    print(f"Marked {chunk_id} complete.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Creative Factory orchestrator")
    sub = parser.add_subparsers(dest="command", required=True)

    p_status = sub.add_parser("status", help="Show pipeline status")
    p_status.set_defaults(func=cmd_status)

    p_tick = sub.add_parser("tick", help="Start next bounded chunk")
    p_tick.add_argument(
        "--roadmap",
        choices=sorted(ROADMAPS),
        default="mvp",
        help="Which roadmap to advance (default: mvp). Use 'scale' for F0–F6.",
    )
    p_tick.set_defaults(func=cmd_tick)

    p_done = sub.add_parser("complete", help="Mark a chunk complete")
    p_done.add_argument("chunk_id", help="Chunk ID e.g. P1.2 or F0.1")
    p_done.set_defaults(func=cmd_complete)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
