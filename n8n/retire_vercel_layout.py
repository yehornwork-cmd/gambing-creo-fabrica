#!/usr/bin/env python3
"""Point Factory v3 layout analysis at forge-renderer. Run on the n8n host.

Replaces creative-localizer.vercel.app with the local renderer:
  POST http://forge-forge-renderer-1:8890/api/layout
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

WORKFLOW_ID = "bzPWFbzTKkGHW1hW"
VERCEL_HOST = "creative-localizer.vercel.app"
LOCAL_LAYOUT = "http://forge-forge-renderer-1:8890/api/layout"
BACKUP = Path("/opt/forge") / f"backup-v3-before-local-layout-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json"


def psql(sql: str, *args: str) -> str:
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
        *args,
    ]
    return subprocess.check_output(cmd, text=True)


def patch_nodes(nodes: list[dict]) -> int:
    changed = 0
    for node in nodes:
        name = node.get("name") or ""
        params = node.get("parameters") or {}
        blob = json.dumps(params, ensure_ascii=False)
        if VERCEL_HOST not in blob and VERCEL_HOST not in json.dumps(node, ensure_ascii=False):
            continue
        if name == "Анализ эталона":
            params["url"] = LOCAL_LAYOUT
            params["authentication"] = "none"
            params.pop("nodeCredentialType", None)
            node["parameters"] = params
            creds = node.get("credentials")
            if creds:
                node.pop("credentials", None)
            changed += 1
        if name == "Настройки" and isinstance(params.get("jsCode"), str):
            params["jsCode"] = params["jsCode"].replace(
                f"https://{VERCEL_HOST}/source.mp4",
                "",
            )
            node["parameters"] = params
            changed += 1
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
        print("already local (no vercel host in nodes)")
        return 0

    payload = json.dumps(nodes, ensure_ascii=False)
    # Dollar-quoting avoids shell/JSON escaping issues inside psql.
    sql = (
        "UPDATE workflow_entity SET nodes = $wf$%s$wf$::json, \"updatedAt\" = NOW() "
        "WHERE id = '%s';"
        % (payload, WORKFLOW_ID)
    )
    psql(sql)
    version = psql(
        f"SELECT \"versionId\" FROM workflow_entity WHERE id='{WORKFLOW_ID}';"
    ).strip()
    if version:
        hist_sql = (
            "UPDATE workflow_history SET nodes = $wf$%s$wf$::json, \"updatedAt\" = NOW() "
            "WHERE \"versionId\" = '%s';"
            % (payload, version)
        )
        psql(hist_sql)
    leftover = psql(
        f"SELECT nodes::text ILIKE '%{VERCEL_HOST}%' FROM workflow_entity WHERE id='{WORKFLOW_ID}';"
    ).strip()
    print(f"patched {changed} node(s); vercel_left={leftover}")
    return 0 if leftover in {"f", "false", "0"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
