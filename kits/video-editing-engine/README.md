# Video Editing Engine

A starter kit for editing talking-head Reels with Claude Code. One folder, one skill,
one format, one set of brand rules and four small scripts. You record; Claude plans
the cut, waits for your approval, cuts, captions, checks its own render and exports.

Built for the guide [Build Your Own AI Video Editing Engine with Claude Code](https://www.aiwithecem.com/guides/build-ai-video-editing-engine),
part 4 of the [Video Editing with Claude Code](https://www.aiwithecem.com/guides/video-editing-claude-code-tools) series.

## How it works

```text
raw/take.mp4
  → probe.py           inspect the source
  → WhisperX           word-level transcript (cached)
  → work/timeline.json the edit as data          ◆ you approve the plan
  → cut.py             one-pass cut, words moved to output time
  → your engine        captions, title, graphics (HyperFrames or Remotion)
  → qa.py + qa.md      frames at every cut, black/frozen frames, loudness
                                                ◆ you approve the draft
  → export.py          out/final.mp4, 1080x1920 H.264
```

## What's inside

```text
brand.json                      sizes, safe zone, fonts, colors, captions, loudness
CLAUDE.md                       project rules and the terms your transcript gets wrong
raw/  work/  assets/  out/      footage in, intermediate files, your assets, renders
templates/                      caption and title templates, once you have them
.claude/skills/reel-editor/
  SKILL.md                      the workflow, with two approval gates
  rules.md                      editing rules; grows with every note
  qa.md                         what to check before a draft is shown
  timeline.example.json         the edit as data
  scripts/probe.py              inspect the source and flag risky inputs
  scripts/cut.py                cut to the timeline in one pass, remap transcript words
  scripts/qa.py                 contact sheet, cut strips, black/frozen frames, loudness
  scripts/export.py             final export from brand.json
```

The scripts use only Python's standard library and call FFmpeg.

## Requirements

- [Claude Code](https://code.claude.com/docs)
- [FFmpeg](https://ffmpeg.org/) (`brew install ffmpeg` on a Mac)
- Python 3.10+
- [WhisperX](https://github.com/m-bain/whisperX) for word-level transcripts
- One animation engine for captions and graphics: [HyperFrames](https://hyperframes.heygen.com/) or [Remotion](https://www.remotion.dev/)

## Set up

Copy the kit into a new project folder (the copy includes the hidden `.claude/` folder):

```bash
git clone https://github.com/ecemkaraman/ai-skills.git
cp -R ai-skills/kits/video-editing-engine my-reels
cd my-reels
```

Install WhisperX in a virtual environment, not your system or Anaconda Python:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install whisperx
```

Then:

1. Set your fonts, colors, safe zone and loudness target in `brand.json`.
2. Name your animation engine in `CLAUDE.md`, and list names or terms your transcript gets wrong.
3. Install your animation engine as its docs describe.

## Use

Put a recording in `raw/`, open Claude Code in the folder and run:

```text
/reel-editor raw/take.mp4
```

Claude inspects and transcribes the take, writes `work/timeline.json`, explains the plan
and waits. After your yes it cuts, captions, checks its own render (at most three fix
passes) and waits again before exporting `out/final.mp4`.

The scripts also run on their own:

```bash
python3 .claude/skills/reel-editor/scripts/cut.py work/timeline.json --plan
python3 .claude/skills/reel-editor/scripts/qa.py out/reel.mp4 --cutmap work/cutmap.json
```

## Make it yours

- **Every note becomes a rule.** When you give feedback, Claude fixes it and adds a line to `rules.md`, so you never give the same note twice.
- **Save what works.** After your first good video, keep its captions and title in `templates/`.
- **Grow only when needed.** A second format is a second skill. Batch editing is a loop over `raw/` with one approval per video.

## License

MIT, like the rest of this repository.
