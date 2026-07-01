---
name: documentary-builder
description: >
  Build a narrated documentary video locally and for free from the user's OWN field
  footage + photos, using natural open-source TTS (Kokoro) and ffmpeg. Use when the user
  wants to create/assemble a documentary, promotional, or explainer video from real
  clips and photographs with AI voice-over, burned captions, title/chapter cards, Ken
  Burns photo montages, and a music/ambience bed — no paid APIs, no cloud credits.
  Also use to fix a robotic/mispronounced narration (Kokoro voice + phonetic respelling
  for non-English/Nepali place names) or to add photo motion clips to an existing cut.
---

# Documentary Builder

A **local, free, agent-driven** pipeline for turning real field footage + photographs +
a script into a finished narrated documentary (MP4, burned captions, title/chapter cards,
Ken Burns photo montages, ducked ambience). No paid APIs, no cloud render credits.

It combines two things that were proven in practice:
- **A working ffmpeg + Kokoro core** (natural free voice, real footage, photo montages).
- **An OpenMontage-style agent workflow**: one `project.json` manifest, discrete phases,
  and quality gates you verify by *extracting frames* (you cannot watch video directly).

> Design bias: this is for documentaries built from the **client's authentic media**
> (a real place, real people). It is deliberately *not* a stock-footage/AI-video generator.
> For animated motion-graphics beyond simple cards, see **§8 Infographics**.

---

## 1. When to use / not use
- ✅ Real footage + photos + a narration script → finished film. Government/NGO/field-study
  documentaries, project reports, promos.
- ✅ Replace a bad TTS voice; fix mispronounced non-English names.
- ✅ Add photo motion clips (Ken Burns) to an existing cut.
- ❌ Fully AI-generated / stock-footage video, talking-head avatars, heavy React motion
  graphics → use OpenMontage (github.com/calesthio/OpenMontage) with Remotion instead.

## 2. One-time setup
```
python scripts/setup.py            # downloads static ffmpeg + Kokoro model into ./tools
python -m pip install -r requirements.txt   # kokoro-onnx, soundfile, pillow
```
`setup.py` is idempotent. It fetches a static ffmpeg/ffprobe (BtbN) and the Kokoro v1.0
onnx model + voices. onnxruntime ships with kokoro-onnx.

### ⚠️ Windows MAX_PATH gotcha (critical)
Windows `CreateProcess` rejects an **executable path > 260 chars**. Deeply-nested temp
/OneDrive working dirs will make ffmpeg.exe unreachable with `WinError 206`. **Run this
skill from a SHORT working dir** (e.g. `C:\Users\<you>\docbuild`). The media *inputs* may
live under long paths (arguments aren't subject to the 260 limit) — only the tool exe path
and the working dir must be short.

## 3. The manifest — `project.json`
Everything is config. Copy `config/project.example.json` and edit. Schema:
```jsonc
{
  "title": "Water for the High Herds",
  "subtitle": "Water Management for Livestock in the High Hills and Mountains",
  "location_line": "Annapurna Rural Municipality | Myagdi District | Gandaki Province",
  "outro": ["Study title line 1","line 2","Consultancy","Ministry | 2083 BS"],
  "width": 1280, "height": 720, "fps": 30,          // 720p matches phone/WhatsApp source
  "voice": "am_michael", "speed": 0.95,             // Kokoro voice (see §6)
  "media_dir": "C:/abs/path/to/photos_and_clips",   // inputs; may be a long path
  "ambient_clips": ["02","03","05"],                // clips used for the ambience bed
  "clips":  { "01_overview": "Overview.mp4", "02": "clipA.mp4" },   // id -> filename
  "clip_pool": ["01_overview","02","04","03"],      // rotation order of footage under narration
  "photos": { "0":"a.jpg", "93":"peak.jpg", "spring_01":"spring.jpg" }, // curated id -> filename
  "phonetics": { "Myagdi":"Myahgdee", "Naribang":"Nareebahng" },       // spoken respell; captions keep proper spelling
  "segments": [
    { "id":"opening", "chapter": null,
      "feature": ["93"],                            // stills shown (Ken Burns) at segment start
      "interlude": ["120","104","94"],              // photo montage AFTER the segment
      "interlude_dur": 18,
      "sentences": ["Sentence one.", "Sentence two."] },
    { "id":"s1", "chapter": ["I","The Landscape"],
      "feature": ["7","144"], "interlude": ["39","32","37"], "interlude_dur": 22,
      "sentences": ["..."] }
  ]
}
```
Rules: photo/clip paths are relative to `media_dir`. Every id in `feature`/`interlude`
must exist in `photos`. Captions use the **proper** sentence text; the spoken audio is the
sentence with `phonetics` substitutions applied (longest key first).

## 4. Workflow (run in order; each is re-runnable)
```
python scripts/probe.py     project.json     # ffprobe clips -> footage.json (res/orient/audio)
python scripts/contact.py   project.json     # contact sheets of ALL photos in media_dir -> curate
python scripts/narrate.py   project.json     # Kokoro TTS + phonetics -> seg_*.wav + timing.json
python scripts/build.py     project.json norm     # normalize clips -> 720p/30 (blurred-fill for portrait)
python scripts/build.py     project.json assemble # cards + montages + features + footage -> video_only + narr + srt
python scripts/build.py     project.json final    # ambience bed + duck + burn captions -> OUTPUT.mp4
```
Curation loop: run `contact.py`, **view `contact/contact_*.png`** (each cell is labelled
with its id), pick the good ids, and place them into `photos` + segment `feature`/`interlude`.

## 5. Quality gates — you cannot watch video, so VERIFY BY FRAMES
After `final`, always:
1. `ffprobe` the output: video+audio streams present, duration in target range.
2. Extract frames at key timestamps and **Read the PNGs**: title card, a captioned
   narration moment (spelling correct?), a photo montage (Ken Burns?), a chapter card, the outro.
   `ffmpeg -ss <t> -i OUT.mp4 -frames:v 1 f.png`
3. Audio sanity via `volumedetect` at (a) a narration moment — expect mean ≈ −24..−28 dB;
   (b) an interlude — ambience present, not silence (mean ≳ −34 dB); (c) near the END —
   narration must not have cut off. `n_samples: 0` = silent/absent → investigate.
Do NOT declare done until frames + all three audio checks pass.

## 6. Voice & pronunciation
- Kokoro male voices: `am_michael` (warm, default), `am_fenrir` (deeper), `bm_george`
  (British, documentary gravitas), `bm_lewis`. Female: `af_heart`/`af_bella` (highest rated).
  Swapping voice = change `voice`, re-run `narrate`+`assemble`+`final`.
- **Non-English names**: never trust the TTS. Add a `phonetics` entry that respells the word
  the way English phonics reads it (e.g. `"Jhangaji":"Jhangahjee"`, `"Kharka":"Kar-kah"`).
  Captions keep the correct spelling automatically. Tune one name at a time.

## 7. Hard-won gotchas (baked into the scripts — do not "fix" them away)
- **Short working dir** (see §2) or ffmpeg is unreachable.
- **Kokoro/espeak**: kokoro-onnx handles phonemization; if you ever call Piper directly it
  needs `cwd` = its own dir + `ESPEAK_DATA_PATH` set.
- **zoompan Ken Burns**: feed a SINGLE still (`-i img`, no `-loop 1 -t`), set
  `zoompan d=<total_frames>`, then `-t <dur>` on output — otherwise it multiplies to minutes.
- **Audio/caption entanglement**: never mix audio *and* burn subtitles in the same
  `filter_complex`; it silently truncates audio. Render the mixed WAV first, then a second
  pass burns subtitles (`-vf subtitles=...`) and maps audio **directly from the WAV**.
- **Ambience bed**: raw field audio is often ~−49 dB (inaudible). Normalize with
  `dynaudnorm` then set level; duck under narration via `sidechaincompress`.
- **Import/query limits** (if using a cloud tool like Descript): batch ≤ 3 media/call.
- **Portrait clips**: blurred-fill background (no black bars) — handled in `build.py norm`.
- Re-encode all pieces to identical codec params so the final concat is a fast stream-copy.

## 8. Infographics layer (optional — the OpenMontage strength, done locally)
`scripts/datacard.py` renders a lightweight **animated data card** (big-number reveal or a
bar) to an MP4 piece you can drop into the timeline — e.g. "54,330 L/day", the two schemes,
or the water-quality pass. It uses ffmpeg only (no Node). For richer motion-graphics
(animated maps, charts, transitions) install **OpenMontage** and use its Remotion pipeline
to render segments, then concat them with this skill's `build.py`.

## 9. Outputs
`OUTPUT.mp4` (from manifest `output` or default), `captions.srt`, and intermediate
`video_only.mp4` / `narr.wav` / `footage.json` / `timing.json` in the working dir. Deliver
the MP4 + SRT; keep the working dir for cheap re-renders (voice swap, photo changes).
