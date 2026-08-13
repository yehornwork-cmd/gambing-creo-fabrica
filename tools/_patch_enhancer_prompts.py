#!/usr/bin/env python3
"""Apply shared context block to all enhancer prompt templates."""

from pathlib import Path

BLOCK = """- Competitor insight: {{competitor_hook}}
- Scenario: {{scenario_summary}}
- Capture status: {{capture_note}}
"""

PROMPTS = Path(__file__).resolve().parents[1] / "library" / "_pipeline" / "enhancer" / "prompts"
MARKER = "competitor_hook"


def main() -> None:
    for path in sorted(PROMPTS.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        if MARKER in text:
            continue
        needle = "- Locale: **{{locale}}**"
        if needle not in text:
            print(f"skip {path.name}")
            continue
        updated = text.replace(needle, needle + "\n" + BLOCK.rstrip())
        path.write_text(updated, encoding="utf-8")
        print(f"updated {path.name}")


if __name__ == "__main__":
    main()
