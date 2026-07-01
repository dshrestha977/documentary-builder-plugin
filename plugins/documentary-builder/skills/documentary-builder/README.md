# documentary-builder

Build a narrated documentary **locally and for free** from your **own field footage +
photographs** + a script. Natural open-source voice (Kokoro), Ken Burns photo montages,
title/chapter cards, burned captions, and a ducked ambience bed — **no paid APIs, no cloud
render credits**.

Works as a **Claude Code skill** (drop in `~/.claude/skills/`) *and* as a standalone repo
(the `scripts/` are plain Python + ffmpeg).

## Why this exists
It combines two things:
- A **proven ffmpeg + Kokoro pipeline** (real footage, natural free voice, photo motion).
- An **OpenMontage-style agent workflow**: one `project.json` manifest, discrete
  re-runnable phases, and quality gates you verify by extracting frames.

It is deliberately built for documentaries made from *authentic* media (a real place, real
people) — not a stock-footage/AI-video generator. For heavy animated motion-graphics, pair
it with [OpenMontage](https://github.com/calesthio/OpenMontage) (Remotion) and concat the
rendered segments with `build.py`.

## Install
```bash
pip install -r requirements.txt          # kokoro-onnx, soundfile, pillow
python scripts/setup.py                   # fetch static ffmpeg + Kokoro model -> tools/
```
> **Windows MAX_PATH**: run from a SHORT working dir (e.g. `C:\Users\you\docbuild`).
> ffmpeg.exe under a long path (>260 chars) fails with `WinError 206`. Inputs may be long.

## Use
```bash
# 1) edit config/project.example.json -> project.json (title, media_dir, script, photos)
python scripts/probe.py    project.json            # -> footage.json
python scripts/contact.py  project.json            # contact sheets -> curate photo ids
python scripts/narrate.py  project.json            # Kokoro TTS + phonetics -> seg_*.wav, timing.json
python scripts/build.py    project.json norm       # normalize clips (720p, blurred-fill portrait)
python scripts/build.py    project.json assemble   # cards + montages + footage -> video_only + captions
python scripts/build.py    project.json final      # ambience + duck + burn captions -> OUTPUT.mp4
# optional infographics piece:
python scripts/datacard.py project.json "54,330" "litres/day - Scheme A design demand" pieces/dc.mp4 4
```

## Verify (you cannot watch video)
```bash
ffmpeg -ss 8 -i OUTPUT.mp4 -frames:v 1 f.png     # Read the PNG: title/caption/montage look right?
ffmpeg -ss <t> -i OUTPUT.mp4 -af volumedetect -f null -   # narration ~-26dB; interlude present; end not silent
```

## Manifest & voice
See `SKILL.md` §3 (schema) and §6 (voices + phonetic respelling for non-English names).
- Male voices: `am_michael` (default), `am_fenrir`, `bm_george`, `bm_lewis`. Swap `voice`,
  re-run `narrate`+`assemble`+`final`.
- Non-English names: add `phonetics` entries (e.g. `"Jhangaji":"Jhangahjee"`). Captions keep
  the correct spelling; only the *spoken* audio is respelled.

## Gotchas (baked into scripts — see SKILL.md §7)
Short working dir · zoompan single-still Ken Burns · never mix audio + subtitle-burn in one
filtergraph · normalize quiet field audio with `dynaudnorm` · portrait blurred-fill · re-encode
pieces to identical params for fast concat-copy · JSON read as utf-8-sig (BOM tolerant).

## Files
```
SKILL.md            agent playbook (the brain)
requirements.txt
scripts/  setup.py  dvlib.py  probe.py  contact.py  narrate.py  build.py  datacard.py
config/   project.example.json   (a real, runnable Myagdi example: 16 clips, 54 photos, 8 segments)
```

## License / credits
Your own code + media. Third-party components keep their own licenses: **Kokoro** (Apache-2.0),
**ffmpeg** (GPL build), **Piper** (MIT). Attribute any external music you add.
