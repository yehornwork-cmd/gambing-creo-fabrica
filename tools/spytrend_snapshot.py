#!/usr/bin/env python3
"""SpyTrend MCP snapshot writer for factory intelligence runs."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
TOKEN_SCRIPT = REPO_ROOT / "bin" / "spytrend-token.sh"
MCP_URL = "https://mcp.spytrend.com/mcp"


def mint_bearer() -> str:
    proc = subprocess.run(
        ["bash", str(TOKEN_SCRIPT)],
        capture_output=True,
        text=True,
        check=True,
        cwd=REPO_ROOT,
    )
    payload = json.loads(proc.stdout)
    auth = payload.get("Authorization", "")
    if not auth.startswith("Bearer "):
        raise RuntimeError(f"Unexpected token payload: {proc.stdout}")
    return auth.split(" ", 1)[1]


def mcp_call(tool: str, arguments: dict[str, Any]) -> Any:
    import urllib.error
    import urllib.request

    body = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {"name": tool, "arguments": arguments},
    }
    token = mint_bearer()
    req = urllib.request.Request(
        MCP_URL,
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        raw = resp.read().decode("utf-8", errors="replace")

    for line in raw.splitlines():
        if line.startswith("data: "):
            event = json.loads(line[6:])
            content = event.get("result", {}).get("content", [])
            if content and content[0].get("type") == "text":
                text = content[0].get("text", "")
                try:
                    return json.loads(text)
                except json.JSONDecodeError:
                    return {"raw": text}
    raise RuntimeError(f"No MCP data line in response: {raw[:500]}")


def summarize_ads(data: dict[str, Any]) -> list[str]:
    rows: list[str] = []
    for ad in data.get("data", [])[:10]:
        rows.append(
            f"| {ad.get('title', '—')[:40]} | {','.join(ad.get('countries') or [])} | "
            f"{ad.get('call_to_action', '—')} | {ad.get('landing_domain', '—')} | "
            f"{ad.get('status_today', '—')} | {ad.get('days_active', '—')}d |"
        )
    return rows


def write_snapshot(out_path: Path, query: str, ads: dict[str, Any], creatives: dict[str, Any]) -> None:
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    ad_rows = summarize_ads(ads)
    creative_notes: list[str] = []
    for item in creatives.get("data", [])[:8]:
        sub = item.get("ai_subcategory", "—")
        geo = ",".join(item.get("countries") or [])
        creative_notes.append(
            f"- **{sub}** · {geo} · active_today={item.get('active_ads_today')} · "
            f"media={item.get('media_type')}"
        )

    md = f"""# SpyTrend snapshot — {query}

- **generated:** {now}
- **source:** SpyTrend MCP (Pro linked account)
- **query_ads:** `{query}`
- **total_ads_matching:** {ads.get('pagination', {}).get('total', '—')}

## Ad listing patterns (sample)

| Title | Geo | CTA | Landing | Status | Run |
|-------|-----|-----|---------|--------|-----|
{chr(10).join(ad_rows) if ad_rows else '| — | — | — | — | — | — |'}

## Creative clusters (sample)

{chr(10).join(creative_notes) if creative_notes else '- (none)'}

## Hooks for factory briefs

1. **Star-rating social proof** — Meta ads use fake 5★ titles (`⭐️⭐️⭐️⭐️⭐️ 5.0`) with `Play game` CTA to affiliate landers (`*.pics`, `*.site`).
2. **Direct title match** — Some creatives name the slot (`Gates Of Olympus`) with geo-specific landers (CZ `onlyczgame.site`).
3. **UGC differentiation** — Competitors rarely show verified in-game screencast; our pilot uses real capture + VO beats — lean into authenticity.
4. **Scatter tease without false FS** — Competitors often over-promise bonus; our AD_B scenario explicitly avoids false bonus claims (see `gameplay/pilot_ad_scenario.md`).
5. **End-card compliance** — Pair excitement hooks with 18+ / responsible play on B06; most affiliate ads omit disclaimers.

## Factory actions

- Use `streamer_character_hook` / `ugc_streamer_template` presets with scatter-tease VO from scenario doc.
- SpyTrend refresh: `python3 tools/spytrend_snapshot.py --game-id vs20olympgate --query "gates of olympus slot"`
"""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(md, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Write SpyTrend competitor snapshot markdown")
    parser.add_argument("--game-id", default="vs20olympgate")
    parser.add_argument("--query", default="gates of olympus slot")
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Output markdown path (default: library/games/<game_id>/intelligence/spytrend_snapshot.md)",
    )
    args = parser.parse_args()

    out = args.out or (
        REPO_ROOT / "library" / "games" / args.game_id / "intelligence" / "spytrend_snapshot.md"
    )

    try:
        ads = mcp_call("search_ads", {"query": args.query, "limit": 10})
        creatives = mcp_call("search_creatives", {"query": "olympus slot", "limit": 8})
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    write_snapshot(out, args.query, ads, creatives)
    print(json.dumps({"ok": True, "path": str(out)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
