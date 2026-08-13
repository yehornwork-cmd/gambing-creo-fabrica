#!/usr/bin/env python3
"""Set Factory v3 render fan-out.

Renderer jobs used to share one HyperFrames project dir, so live sat at
CONCURRENCY=2 and this node was capped to match. Projects are now per-job;
fan-out can be higher. Renderer still queues above its slot count.

Keeps a single retry after 2s for a transient 500.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

WORKFLOW_ID = "bzPWFbzTKkGHW1hW"
TARGET_CONC = 8
BACKUP = Path("/opt/forge") / (
    f"backup-v3-before-render-conc-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json"
)

CONC_RE = re.compile(r"const CONC = \d+;(?:[^\n]*)")
NEW_CONC = f"const CONC = {TARGET_CONC}; // renderer queues above CONCURRENCY"

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
        next_code = CONC_RE.sub(NEW_CONC, code, count=1)
        if next_code != code:
            code = next_code
            changed += 1
        if "attempt < 2" not in code:
            if OLD_SHOT not in code:
                raise SystemExit("render shot() marker missing — live node drifted")
            code = code.replace(OLD_SHOT, NEW_SHOT, 1)
            changed += 1
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
    check = psql(f"SELECT nodes::text FROM workflow_entity WHERE id='{WORKFLOW_ID}';")
    ok_conc = f"const CONC = {TARGET_CONC};" in check
    ok_retry = "attempt < 2" in check
    print(f"patched {changed} replacement(s); conc{TARGET_CONC}={ok_conc} retry={ok_retry}")
    return 0 if ok_conc and ok_retry else 1


if __name__ == "__main__":
    raise SystemExit(main())
