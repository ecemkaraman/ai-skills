#!/usr/bin/env python3
"""Summarize a video with ffprobe and flag inputs that cause trouble later.

Usage: python3 probe.py raw/take.mp4 [--out work/probe.json]
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path


def run_ffprobe(path: Path) -> dict:
    """Return ffprobe's JSON description of the file's format and streams."""
    result = subprocess.run(
        [
            "ffprobe", "-v", "error", "-print_format", "json",
            "-show_format", "-show_streams", str(path),
        ],
        capture_output=True, text=True, check=True,
    )
    return json.loads(result.stdout)


def frame_rate(value: str) -> float:
    """Convert an ffprobe rate such as '30000/1001' to frames per second."""
    num, _, den = value.partition("/")
    return float(num) / float(den or 1) if float(den or 1) else 0.0


def summarize(info: dict) -> dict:
    """Pick out the facts an edit depends on and list any warnings."""
    video = next((s for s in info["streams"] if s["codec_type"] == "video"), None)
    audio = next((s for s in info["streams"] if s["codec_type"] == "audio"), None)
    warnings: list[str] = []
    summary: dict = {"duration_s": round(float(info["format"]["duration"]), 3)}

    if video is None:
        warnings.append("No video stream.")
    else:
        nominal = frame_rate(video.get("r_frame_rate", "0/1"))
        average = frame_rate(video.get("avg_frame_rate", "0/1"))
        summary["video"] = {
            "codec": video.get("codec_name"),
            "width": video.get("width"),
            "height": video.get("height"),
            "fps": round(average or nominal, 3),
        }
        if nominal and average and abs(nominal - average) > 0.01:
            warnings.append("Variable frame rate: re-encode to a fixed rate before cutting.")
        if video.get("codec_name") == "hevc":
            warnings.append("HEVC source: export the final as H.264 for compatibility.")

    if audio is None:
        warnings.append("No audio stream.")
    else:
        summary["audio"] = {
            "codec": audio.get("codec_name"),
            "sample_rate": int(audio.get("sample_rate", 0)),
            "channels": audio.get("channels"),
        }

    summary["warnings"] = warnings
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("video", type=Path)
    parser.add_argument("--out", type=Path, default=Path("work/probe.json"))
    args = parser.parse_args()

    if not args.video.exists():
        print(f"Not found: {args.video}", file=sys.stderr)
        return 1

    summary = summarize(run_ffprobe(args.video))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
