# habile-media — Claude Code plugin marketplace

A small marketplace that distributes **documentary-builder**: a Claude Code plugin for
building narrated documentary videos **locally and for free** from your own field footage
and photographs.

## Install (for people you share this with)

In Claude Code:

```
/plugin marketplace add dshrestha977/documentary-builder-plugin
/plugin install documentary-builder@habile-media
```

- The first command registers this marketplace (point it at the GitHub repo where you host
  this folder, e.g. `deependra/documentary-builder-plugin`). A local path also works:
  `/plugin marketplace add ./documentary-builder-plugin`.
- The second installs the plugin. It adds the **`documentary-builder` skill** and the
  **`/documentary` command**.

Then, one-time on the user's machine (fetches ffmpeg + the Kokoro voice model):

```
pip install -r <plugin>/skills/documentary-builder/requirements.txt
python <plugin>/skills/documentary-builder/scripts/setup.py
```

## What it does

`/documentary` (or just asking Claude to "build a documentary from my footage and photos")
runs a config-driven, fully local pipeline:

- **Kokoro** natural free voice-over (Apache-2.0) with **phonetic respelling** so non-English
  place names are pronounced correctly while captions keep the proper spelling.
- Real **field footage** normalized to 720p (blurred-fill for portrait clips).
- **Ken Burns motion clips** from your photographs (montage interludes + featured stills),
  curated via auto-generated contact sheets.
- Title / chapter / outro cards, burned captions, and a ducked field-ambience bed.
- Verify-by-frames quality gates (the agent can't watch video, so it checks extracted frames).

No paid APIs, no cloud render credits. See `plugins/documentary-builder/skills/documentary-builder/SKILL.md`
for the full playbook and `config/project.example.json` for a complete runnable example.

## Repo layout

```
.claude-plugin/marketplace.json          # this marketplace
plugins/
  documentary-builder/
    .claude-plugin/plugin.json           # the plugin manifest
    commands/documentary.md              # /documentary slash command
    skills/documentary-builder/          # the bundled skill (SKILL.md + scripts + example)
```

## Hosting

Push this folder to GitHub (or any git host). Users then
`/plugin marketplace add <owner>/<repo>` and `/plugin install documentary-builder@habile-media`.
Update by pushing changes; users run `/plugin marketplace update`.

## License

MIT (this plugin's own code). Third-party tools fetched by `setup.py` keep their licenses:
Kokoro (Apache-2.0), ffmpeg (GPL build), Piper (MIT). Attribute any external music you add.
