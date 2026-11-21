---
name: reel-editor
description: Edit a raw talking-head recording into a vertical Reel with this project's brand rules. Plans the cut from the transcript, waits for approval, cuts, captions, checks its own render and exports.
argument-hint: "[path to raw recording]"
disable-model-invocation: true
---

# Reel editor

Edit `$ARGUMENTS` into a 1080x1920 Reel. Read `brand.json` for every size, font,
color, safe zone and loudness value. Read [rules.md](rules.md) before planning and
[qa.md](qa.md) before showing any render.

## Steps

1. **Inspect.** `python3 ${CLAUDE_SKILL_DIR}/scripts/probe.py $ARGUMENTS`. Report any warnings.
2. **Transcribe**, unless `work/<name>.json` already exists for this file:
   `whisperx $ARGUMENTS --model small --device cpu --compute_type int8 --output_format json --output_dir work`
   (inside the project's `.venv`). Fix names and terms I've listed in `CLAUDE.md`.
3. **Plan.** Write `work/timeline.json` (format: [timeline.example.json](timeline.example.json)):
   the segments to keep in source time, captions, zooms, graphics and audio. Then
   explain the plan in plain English: what's cut and why, the order, the length.
   **Stop and wait for my approval.**
4. **Cut.** `python3 ${CLAUDE_SKILL_DIR}/scripts/cut.py work/timeline.json --words work/<name>.json`.
   Captions use `work/rough.words.json`, which is already in output time.
5. **Frame, caption, add graphics** with the project's animation engine, following
   `brand.json` and any template in `templates/`. Render a draft to `out/reel.mp4`.
6. **Check.** `python3 ${CLAUDE_SKILL_DIR}/scripts/qa.py out/reel.mp4 --cutmap work/cutmap.json`.
   Open the contact sheet and every cut strip and go through [qa.md](qa.md). Fix
   what fails and check again, **at most three passes**, then show me the draft with
   what you checked and changed.
7. **Export** only after I approve the draft:
   `python3 ${CLAUDE_SKILL_DIR}/scripts/export.py out/reel.mp4`.

## Always

- Never modify `raw/`. Everything generated goes in `work/` or `out/`.
- Ask before installing anything or calling a paid API.
- When I give a note, fix it and add it to [rules.md](rules.md) as a rule.

## Leave to me

What the video is about, which take is better when it's a matter of taste, and the
final yes.
