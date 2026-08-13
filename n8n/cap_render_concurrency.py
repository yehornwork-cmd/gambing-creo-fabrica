#!/usr/bin/env python3
"""Cap Factory v3 render fan-out to the local renderer capacity.

forge-renderer runs with CONCURRENCY=2. The Code node used CONC=12, so a
buyer localization of 3+ geos raced the renderer and one geo came back
`рендер не отработал: Request failed with status code 500`. AU-only
retries succeeded — this is overload, not an AU copy bug.

Also retries a failed geo once after 2s.
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

WORKFLOW_ID = "bzPWFbzTKkGHW1hW"
BACKUP = Path("/opt/forge") / (
    f"backup-v3-before-render-conc-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json"
)

OLD_CONC = "const CONC = 12;"
NEW_CONC = "const CONC = 2; // match forge-renderer CONCURRENCY=2"

OLD_SHOT = """const shot = async (item) => {
  const j = item.json;
  const res = await this.helpers.httpRequest({
    method: 'POST', url: URL,
    headers: { 'x-api-key': KEY, 'content-type': 'application/json' },
    body: {
      geo: j.geo, headline: j.headline, disclaimer: j.disclaimer,
      vo_base64: j.vo_base64, video_url: cfg.master_url, layout,
      qc: true, expect_duration: master, output: 'url', run_id: runId,
    },
    json: true, timeout: 300000,
  });
"""

NEW_SHOT = """const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

const shot = async (item) => {
  const j = item.json;
  let res;
  let lastErr;
  for (let attempt = 0; attempt < 2; attempt++) {
    try {
      res = await this.helpers.httpRequest({
        method: 'POST', url: URL,
        headers: { 'x-api-key': KEY, 'content-type': 'application/json' },
        body: {
          geo: j.geo, headline: j.headline, disclaimer: j.disclaimer,
          vo_base64: j.vo_base64, video_url: cfg.master_url, layout,
          qc: true, expect_duration: master, output: 'url', run_id: runId,
        },
        json: true, timeout: 300000,
      });
      lastErr = null;
      break;
    } catch (e) {
      lastErr = e;
      if (attempt === 0) await sleep(2000);
    }
  }
  if (!res) throw lastErr;
"""


def psql(sql: str) -> str:
    cmd = [
        "docker",
        "exec",
        "video-factory-postgres-1",
        "psql",
        "-U",
        "n8n",
        "-d",
        "n8n",
        "-t",
        "-A",
        "-c",
        sql,
    ]
    return subprocess.check_output(cmd, text=True)


def patch_nodes(nodes: list[dict]) -> int:
    changed = 0
    for node in nodes:
        if node.get("name") != "Рендер + автопроверка":
            continue
        params = node.get("parameters") or {}
        code = params.get("jsCode")
        if not isinstance(code, str):
            continue
        if "const CONC = 2;" in code and "attempt < 2" in code:
            continue
        if OLD_CONC in code:
            code = code.replace(OLD_CONC, NEW_CONC, 1)
            changed += 1
        if OLD_SHOT in code:
            code = code.replace(OLD_SHOT, NEW_SHOT, 1)
            changed += 1
        elif "attempt < 2" not in code:
            raise SystemExit("render shot() marker missing — live node drifted")
        params["jsCode"] = code
        node["parameters"] = params
    return changed


def main() -> int:
    raw = psql(f"SELECT nodes::text FROM workflow_entity WHERE id='{WORKFLOW_ID}';").strip()
    if not raw:
        print(f"error: workflow {WORKFLOW_ID} not found", file=sys.stderr)
        return 2
    nodes = json.loads(raw)
    BACKUP.parent.mkdir(parents=True, exist_ok=True)
    BACKUP.write_text(json.dumps(nodes, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"backup {BACKUP}")

    changed = patch_nodes(nodes)
    if changed == 0:
        print("already capped (CONC=2 + retry)")
        return 0

    payload = json.dumps(nodes, ensure_ascii=False)
    sql = (
        "UPDATE workflow_entity SET nodes = $wf$%s$wf$::json, \"updatedAt\" = NOW() "
        "WHERE id = '%s';" % (payload, WORKFLOW_ID)
    )
    psql(sql)
    version = psql(f"SELECT \"versionId\" FROM workflow_entity WHERE id='{WORKFLOW_ID}';").strip()
    if version:
        hist_sql = (
            "UPDATE workflow_history SET nodes = $wf$%s$wf$::json, \"updatedAt\" = NOW() "
            "WHERE \"versionId\" = '%s';" % (payload, version)
        )
        psql(hist_sql)
    check = psql(
        f"SELECT nodes::text FROM workflow_entity WHERE id='{WORKFLOW_ID}';"
    )
    ok_conc = "const CONC = 2;" in check
    ok_retry = "attempt < 2" in check
    print(f"patched {changed} replacement(s); conc2={ok_conc} retry={ok_retry}")
    return 0 if ok_conc and ok_retry else 1


if __name__ == "__main__":
    raise SystemExit(main())
