#!/usr/bin/env python3
"""Local creative enhancer — template prompts with optional Perplexity LLM fallback."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
PROMPTS_DIR = REPO_ROOT / "library" / "_pipeline" / "enhancer" / "prompts"

VALID_FLOWS = {
    "streamer-character",
    "streamer-board",
    "streamer-clip",
    "ugc-character",
    "ugc-board",
    "ugc-clip",
}


def load_prompt_template(flow: str) -> str:
    path = PROMPTS_DIR / f"{flow}.md"
    if not path.is_file():
        raise FileNotFoundError(f"Prompt template not found: {path}")
    return path.read_text(encoding="utf-8")


def render_template(template: str, variables: dict[str, str]) -> str:
    rendered = template
    for key, value in variables.items():
        rendered = rendered.replace(f"{{{{{key}}}}}", value)
    unresolved = re.findall(r"\{\{(\w+)\}\}", rendered)
    if unresolved:
        missing = ", ".join(sorted(set(unresolved)))
        raise ValueError(f"Unresolved template variables: {missing}")
    return rendered.strip()


def perplexity_available() -> bool:
    return bool(os.environ.get("PERPLEXITY_API_KEY", "").strip())


def enhance_with_llm(flow: str, brief: str, template_output: str) -> str:
    from media_http import MediaHttpError
    from perplexity_client import enhance, extract_text

    context = f"Flow: {flow}\n\nTemplate draft:\n{template_output}"
    try:
        result = enhance(brief, context=context)
        return extract_text(result).strip()
    except MediaHttpError as exc:
        print(f"WARN: Perplexity enhance failed, using template fallback: {exc}", file=sys.stderr)
        return template_output


def build_enhancement(
    flow: str,
    brief: str,
    *,
    variables: dict[str, str] | None = None,
    use_llm: bool | None = None,
) -> dict[str, Any]:
    if flow not in VALID_FLOWS:
        raise ValueError(f"Unknown flow {flow!r}. Expected one of: {', '.join(sorted(VALID_FLOWS))}")

    merged_vars = {
        "brief": brief.strip(),
        "game_title": "",
        "game_id": "",
        "aspect": "9:16",
        "duration_sec": "30",
        "locale": "en",
        "competitor_hook": "",
    }
    if variables:
        merged_vars.update({k: str(v) for k, v in variables.items()})

    template = load_prompt_template(flow)
    template_output = render_template(template, merged_vars)

    should_llm = use_llm if use_llm is not None else perplexity_available()
    final_text = template_output
    source = "template"

    if should_llm and perplexity_available():
        final_text = enhance_with_llm(flow, brief, template_output)
        source = "perplexity+template"
    elif should_llm:
        print("WARN: --llm requested but PERPLEXITY_API_KEY is unset; using template only.", file=sys.stderr)

    return {
        "flow": flow,
        "source": source,
        "brief": brief.strip(),
        "variables": merged_vars,
        "enhanced_prompt": final_text,
    }


def cmd_enhance(args: argparse.Namespace) -> int:
    brief_path = Path(args.brief)
    brief = brief_path.read_text(encoding="utf-8") if brief_path.is_file() else args.brief

    variables: dict[str, str] = {}
    if args.vars:
        variables = json.loads(args.vars)

    result = build_enhancement(
        args.flow,
        brief,
        variables=variables,
        use_llm=args.llm,
    )

    if args.output:
        Path(args.output).write_text(result["enhanced_prompt"] + "\n", encoding="utf-8")
    else:
        print(result["enhanced_prompt"])

    if args.json:
        meta = dict(result)
        meta.pop("enhanced_prompt")
        print(json.dumps(meta, indent=2), file=sys.stderr)

    return 0


def cmd_list(_: argparse.Namespace) -> int:
    for flow in sorted(VALID_FLOWS):
        path = PROMPTS_DIR / f"{flow}.md"
        status = "ok" if path.is_file() else "missing"
        print(f"{flow}\t{status}\t{path.relative_to(REPO_ROOT)}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Creative enhancer for factory media flows")
    sub = parser.add_subparsers(dest="command", required=True)

    p_enhance = sub.add_parser("enhance", help="Enhance a brief for a media flow")
    p_enhance.add_argument("flow", choices=sorted(VALID_FLOWS))
    p_enhance.add_argument("brief", help="Brief text or path to markdown file")
    p_enhance.add_argument("--vars", help="JSON object of template variables")
    p_enhance.add_argument("--llm", action="store_true", help="Force Perplexity LLM pass")
    p_enhance.add_argument("--no-llm", action="store_true", help="Disable Perplexity even if key is set")
    p_enhance.add_argument("--output", "-o", help="Write enhanced prompt to file")
    p_enhance.add_argument("--json", action="store_true", help="Print metadata JSON to stderr")
    p_enhance.set_defaults(func=cmd_enhance)

    sub.add_parser("list", help="List supported flows and prompt templates").set_defaults(func=cmd_list)

    args = parser.parse_args()
    if args.command == "enhance":
        if args.no_llm:
            args.llm = False
        elif args.llm:
            args.llm = True
        else:
            args.llm = None

    try:
        return args.func(args)
    except (FileNotFoundError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
