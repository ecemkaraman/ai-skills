#!/usr/bin/env python3
"""Export the final MP4 with the settings in brand.json.

Scales and pads to the brand frame, fixes the frame rate, normalizes loudness
and writes H.264 + AAC with the index at the front for fast playback.

Usage: python3 export.py out/reel.mp4 [--out out/final.mp4] [--brand brand.json]
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

DEFAULTS = {
    "format": {"width": 1080, "height": 1920, "fps": 30},
    "audio": {"loudness_lufs": -14, "true_peak_db": -1.5},
}


def load_brand(path: Path) -> dict:
    """Read brand.json, falling back to Reel defaults for missing keys."""
    brand = json.loads(path.read_text()) if path.exists() else {}
    return {key: {**DEFAULTS[key], **brand.get(key, {})} for key in DEFAULTS}


def export_command(source: Path, out: Path, brand: dict) -> list[str]:
    """Build the FFmpeg command for the final file."""
    fmt, audio = brand["format"], brand["audio"]
    w, h = fmt["width"], fmt["height"]
    video_filter = (
        f"scale={w}:{h}:force_original_aspect_ratio=decrease,"
        f"pad={w}:{h}:(ow-iw)/2:(oh-ih)/2,fps={fmt['fps']},format=yuv420p"
    )
    audio_filter = f"loudnorm=I={audio['loudness_lufs']}:TP={audio['true_peak_db']}:LRA=11"
    return [
        "ffmpeg", "-v", "error", "-y", "-i", str(source),
        "-vf", video_filter, "-af", audio_filter,
        "-c:v", "libx264", "-crf", "18", "-preset", "slow",
        "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
        "-movflags", "+faststart", str(out),
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("video", type=Path)
    parser.add_argument("--out", type=Path, default=Path("out/final.mp4"))
    parser.add_argument("--brand", type=Path, default=Path("brand.json"))
    args = parser.parse_args()

    if not args.video.exists():
        print(f"Not found: {args.video}", file=sys.stderr)
        return 1
    args.out.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(export_command(args.video, args.out, load_brand(args.brand)), check=True)
    print(f"Wrote {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
