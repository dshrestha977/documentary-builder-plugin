---
description: Build a local, free narrated documentary from your own footage + photos
argument-hint: [working dir or path to project.json]
---

Use the **documentary-builder** skill (bundled in this plugin at
`skills/documentary-builder/`) to build a documentary video from the user's OWN field
footage and photographs — natural free voice (Kokoro), Ken Burns photo montages, title
and chapter cards, and burned captions. Fully local; no paid APIs or cloud credits.

Read the skill's `SKILL.md` and follow its phases in order:

1. **setup** — `python scripts/setup.py` (fetch ffmpeg + Kokoro) if `tools/paths.json` is missing.
2. **probe** — `python scripts/probe.py project.json` → footage.json.
3. **contact** — `python scripts/contact.py project.json`, then VIEW `contact/contact_*.png`
   and curate the best photo ids into `project.json` (`photos` + segment `feature`/`interlude`).
4. **narrate** — `python scripts/narrate.py project.json` (Kokoro voice + phonetics).
5. **build** — `python scripts/build.py project.json all` (norm → assemble → final).
6. **verify** — extract frames + run `volumedetect` per SKILL.md §5 (you cannot watch video).

Honor every gotcha in SKILL.md §7: run from a SHORT working dir (Windows MAX_PATH), zoompan
single-still Ken Burns, never mix audio + subtitle-burn in one filtergraph, normalize the
ambience with dynaudnorm, blurred-fill for portrait clips.

Working target: $ARGUMENTS
