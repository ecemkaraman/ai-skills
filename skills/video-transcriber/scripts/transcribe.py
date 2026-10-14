#!/usr/bin/env python3
"""Download the audio of one or more short videos and transcribe it locally with Whisper.

Works with anything yt-dlp supports: Instagram Reels, TikTok, YouTube Shorts, YouTube,
X/Twitter video and many more. Transcription runs on your machine; no API key needed.

Usage:
    python scripts/transcribe.py URL [URL ...]
    python scripts/transcribe.py --file links.txt
    python scripts/transcribe.py URL --model small --language en

Prints one JSON object per line: {"url", "id", "status", "transcript", "speech_seconds",
"language", "error"}. Status is "ok", "no_speech" or "failed".

Requires: ffmpeg, yt-dlp and openai-whisper (pip install -r requirements.txt).
Private or login-gated videos need browser cookies: set YTDLP_COOKIES_BROWSER=chrome
(or firefox, safari) to let yt-dlp read them.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Optional

MIN_SPEECH_WORDS = 3
DEFAULT_MODEL = "base"


def video_id(url: str) -> str:
    """Return a stable short id for a video URL, used to name files and dedupe."""
    patterns = [
        r"instagram\.com/(?:[^/]+/)?(?:reel|reels|p)/([A-Za-z0-9_-]+)",
        r"tiktok\.com/.*/video/(\d+)",
        r"(?:youtube\.com/(?:shorts/|watch\?v=)|youtu\.be/)([A-Za-z0-9_-]{6,})",
        r"(?:x|twitter)\.com/[^/]+/status/(\d+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return re.sub(r"[^A-Za-z0-9]", "_", url)[-40:]


def cookies_args() -> list[str]:
    """Pass browser cookies to yt-dlp only when the user opts in."""
    browser = os.environ.get("YTDLP_COOKIES_BROWSER")
    return ["--cookies-from-browser", browser] if browser else []


def download_audio(url: str, out_path: Path) -> Optional[str]:
    """Download audio as mp3. Return None on success, or the error message."""
    cmd = [
        "yt-dlp", *cookies_args(),
        "-x", "--audio-format", "mp3", "--audio-quality", "5",
        "-o", str(out_path), "--no-playlist", "--quiet", "--no-warnings", url,
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    except FileNotFoundError:
        return "yt-dlp is not installed"
    except subprocess.TimeoutExpired:
        return "download timed out"
    if result.returncode != 0 or not out_path.exists():
        lines = result.stderr.strip().splitlines()
        return lines[-1][:200] if lines else "download failed"
    return None


def transcribe_file(model: Any, audio_path: Path, language: Optional[str]) -> dict[str, Any]:
    """Run Whisper and return the full transcript, spoken length and detected language."""
    result = model.transcribe(str(audio_path), language=language, fp16=False, verbose=False)
    segments = result.get("segments", [])
    text = " ".join(segment["text"].strip() for segment in segments).strip()
    return {
        "transcript": text,
        "speech_seconds": round(segments[-1]["end"]) if segments else 0,
        "language": result.get("language"),
    }


def process(url: str, model: Any, language: Optional[str], workdir: Path) -> dict[str, Any]:
    """Download and transcribe one URL. Never raises; failures are reported in the record."""
    record: dict[str, Any] = {"url": url, "id": video_id(url), "status": "failed",
                              "transcript": "", "speech_seconds": 0, "language": None,
                              "error": None}
    audio_path = workdir / f"{record['id']}.mp3"
    error = download_audio(url, audio_path)
    if error:
        record["error"] = error
        return record
    try:
        record.update(transcribe_file(model, audio_path, language))
    except (RuntimeError, ValueError, OSError) as exc:
        record["error"] = f"transcription failed: {exc}"
        return record
    words = len(record["transcript"].split())
    record["status"] = "ok" if words >= MIN_SPEECH_WORDS else "no_speech"
    return record


def read_urls(args: argparse.Namespace) -> list[str]:
    """Collect URLs from arguments and an optional file, deduped, order preserved."""
    urls = list(args.urls)
    if args.file:
        urls += [line.strip() for line in Path(args.file).read_text().splitlines()
                 if line.strip().startswith("http")]
    seen: set[str] = set()
    unique = []
    for url in urls:
        key = video_id(url)
        if key not in seen:
            seen.add(key)
            unique.append(url.replace("\\_", "_"))
    return unique


def main() -> int:
    parser = argparse.ArgumentParser(description="Transcribe short videos locally.")
    parser.add_argument("urls", nargs="*", help="Video URLs")
    parser.add_argument("--file", help="Text file with one URL per line")
    parser.add_argument("--model", default=DEFAULT_MODEL,
                        help="Whisper model: tiny, base, small, medium, large")
    parser.add_argument("--language", default=None,
                        help="Force a language code such as en; default auto-detects")
    args = parser.parse_args()

    urls = read_urls(args)
    if not urls:
        parser.error("no URLs supplied")

    try:
        import whisper  # imported late so --help works without it installed
    except ImportError:
        print("openai-whisper is not installed: pip install -r requirements.txt",
              file=sys.stderr)
        return 1

    model = whisper.load_model(args.model)
    with tempfile.TemporaryDirectory() as tmp:
        for url in urls:
            print(json.dumps(process(url, model, args.language, Path(tmp))), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
