# Game Library

Canonical storage for Game DNA, gameplay analysis, and creative briefs.

## Layout

```
library/games/<game_id>/
├── game.json              # Identity, specs, meta
├── gameplay/
│   ├── game_analysis_v3.json
│   ├── mechanics.json
│   └── symbols.json
├── briefs/
│   └── <brief_slug>/
│       ├── BRIEF.md
│       └── STORYBOARD.md
├── assets/                # Relative paths to production assets (may live off-repo)
└── compliance.json        # GEO-specific copy (user-validated)
```

## Conventions

- `game_id` matches provider slug (e.g. `vs20olympgate` for Gates of Olympus).
- All paths inside JSON are **relative to the game root** (`library/games/<game_id>/`).
- Staging content in `context/` should be migrated here, then deprecated.
- Run `python3 tools/path_normalizer.py` after importing JSON with absolute paths.

## Constructor

Variant explosion (locale × format × CTA × geo) lives in `library/_pipeline/constructor/`. See that README. 500 creatives/day is a product of those axes, not 500 unique storyboards.

```bash
python3 library/_pipeline/constructor/explode.py --dry-run
```

## Pipeline

```bash
python3 library/_pipeline/orchestrator/factory_run.py status
python3 library/_pipeline/orchestrator/factory_run.py tick --roadmap scale
```
