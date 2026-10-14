# Video Transcriber

Paste video links and get complete, unedited transcripts saved to a swipe file you can
search, study and reference.

Works with Instagram Reels, TikTok, YouTube Shorts, YouTube and X. Transcription runs
locally with Whisper, so there's no API key and no per-minute cost. It dedupes by video ID,
keeps the source and your notes with each entry, and can read links from a Slack channel
if you have the Slack connector.

## Requirements

- Python 3.9+ and [ffmpeg](https://ffmpeg.org/) (`brew install ffmpeg` on macOS)
- `pip install -r requirements.txt` (yt-dlp, openai-whisper)
- For login-gated videos: `export YTDLP_COOKIES_BROWSER=chrome`

## Install

**Claude Code:** copy the folder into your skills directory.

```bash
cp -r skills/video-transcriber ~/.claude/skills/      # all projects
# or: cp -r skills/video-transcriber .claude/skills/  # one project
```

**Claude apps:** zip the `video-transcriber` folder and upload it under Customize → Skills (+ → Create skill → Upload a skill). Code execution must be on in Settings → Capabilities.

## Try it

- "Transcribe these: <link> <link>"
- "Add these reels to my swipe file" (with a text file of links)
- "Transcribe the links in #inspo"

Only transcribe content you have the right to use. Transcripts are saved for study, not
for republishing someone else's words.
