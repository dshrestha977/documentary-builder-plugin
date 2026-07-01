---
description: Build a narrated animated data/infographics segment (charts, stats, checklists)
argument-hint: [path to a data_segment config JSON]
---

Use the **documentary-builder** skill's data-segment tool to build a narrated, animated
**data/infographics segment** — fully local and free (ffmpeg + Kokoro voice, no Node, no
paid APIs). This is the layer that turns report figures into motion.

Steps (run from a SHORT working dir; `tools/paths.json` must exist — run `setup.py` if not):

1. Author or edit a config with a `data_segment.cards` list. Start from
   `skills/documentary-builder/config/datasegment.example.json`. Card types:
   - `section` (title/subtitle), `stats` (value+label grid), `compare` (animated bars),
     `number` (one hero figure), `checklist` (green-tick pass list).
   - Each card takes a `narration` line (drives its timing) and optional `pad`.
2. Run: `python scripts/datasegment.py <config.json>` → produces the segment MP4 + captions.
3. Verify by extracting a frame (`ffmpeg -ss <t> -i out.mp4 -frames:v 1 f.png`) and a
   `volumedetect` audio check, per SKILL.md §5.

The segment can stand alone for a presentation, or be concatenated into a main film built
with `build.py`. See SKILL.md §8 for the full card schema and gotchas (percent signs need
`expansion=none` — already handled; the checkmark needs the symbol font `setup.py` fetches).

Config / target: $ARGUMENTS
