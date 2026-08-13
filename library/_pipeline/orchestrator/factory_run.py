#!/usr/bin/env python3
"""Creative Factory orchestrator — status and tick for bounded MVP chunks."""

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
ROADMAP = PIPELINE / "phases" / "MVP_ROADMAP.md"
ROADMAP_PHASE2 = PIPELINE / "phases" / "PHASE2_ROADMAP.md"
STATE_FILE = PIPELINE / "state.json"
RUNS_DIR = PIPELINE / "runs"

ROADMAP_FILES = {
    "mvp": ROADMAP,
    "phase2": ROADMAP_PHASE2,
}

CHUNK_RE = re.compile(
    r"^\|\s*(P\d+\.\d+)\s*\|\s*([^|]+)\|\s*([^|]+)(?:\|\s*([^|]+))?\s*\|$"
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


def parse_roadmap(path: Path | None = None) -> list[dict[str, str]]:
    roadmap_path = path or ROADMAP
    if not roadmap_path.exists():
        return []
    chunks: list[dict[str, str]] = []
    for line in roadmap_path.read_text(encoding="utf-8").splitlines():
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


def cmd_status(args: argparse.Namespace) -> int:
    state = load_state()
    phase = getattr(args, "phase", "mvp")
    roadmap_path = ROADMAP_FILES.get(phase, ROADMAP)
    chunks = parse_roadmap(roadmap_path)
    completed = state.get("completed", [])
    blocked = state.get("blocked", {})
    chunk_ids = {c["id"] for c in chunks}
    phase_completed = [c for c in completed if c in chunk_ids]
    pending = [c["id"] for c in chunks if c["id"] not in completed and c["id"] not in blocked]

    print("Creative Factory — status")
    print(f"  phase:     {phase}")
    print(f"  repo:      {REPO_ROOT}")
    print(f"  updated:   {state.get('updated_at', '—')}")
    print(f"  completed: {len(phase_completed)}/{len(chunks)} chunks")
    if phase_completed:
        print(f"             {', '.join(phase_completed)}")
    if blocked:
        print("  blocked:")
        for cid, reason in blocked.items():
            print(f"    {cid}: {reason}")
    if pending:
        print(f"  next up:   {pending[0]}")
    elif not blocked:
        print("  next up:   (all chunks complete)")
    else:
        print("  next up:   (blocked — resolve blockers or mark complete manually)")
    if state.get("in_progress"):
        print(f"  in flight: {state['in_progress']}")
    return 0


def cmd_tick(args: argparse.Namespace) -> int:
    state = load_state()
    phase = getattr(args, "phase", "mvp")
    roadmap_path = ROADMAP_FILES.get(phase, ROADMAP)
    chunks = parse_roadmap(roadmap_path)
    if not chunks:
        print("ERROR: MVP roadmap not found or empty.", file=sys.stderr)
        return 1

    chunk = next_chunk(state, chunks)
    if chunk is None:
        save_state(state)
        print(f"No actionable chunk in phase {phase} — all complete or blocked.")
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
    phase = getattr(args, "phase", "mvp")
    roadmap_path = ROADMAP_FILES.get(phase, ROADMAP)
    if chunk_id not in {c["id"] for c in parse_roadmap(roadmap_path)}:
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
    p_status.add_argument("--phase", choices=list(ROADMAP_FILES.keys()), default="mvp")
    p_status.set_defaults(func=cmd_status)

    p_tick = sub.add_parser("tick", help="Start next bounded MVP chunk")
    p_tick.add_argument("--phase", choices=list(ROADMAP_FILES.keys()), default="mvp")
    p_tick.set_defaults(func=cmd_tick)

    p_done = sub.add_parser("complete", help="Mark a chunk complete")
    p_done.add_argument("chunk_id", help="Chunk ID e.g. P1.2")
    p_done.add_argument("--phase", choices=list(ROADMAP_FILES.keys()), default="mvp")
    p_done.set_defaults(func=cmd_complete)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
