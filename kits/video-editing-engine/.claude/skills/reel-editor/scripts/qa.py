#!/usr/bin/env python3
"""Check a rendered video and collect what Claude needs to look at.

Writes to work/qa/: a contact sheet, a frame strip around every cut (when a
cutmap is given) and report.json with black or frozen frames, loudness, and
the audio and video stream lengths.

Usage: python3 qa.py out/reel.mp4 [--cutmap work/cutmap.json] [--brand brand.json]
"""

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path


def ffmpeg_log(args: list[str]) -> str:
    """Run FFmpeg with a null output and return what it printed to stderr."""
    result = subprocess.run(
        ["ffmpeg", "-hide_banner", "-nostats", *args, "-f", "null", "-"],
        capture_output=True, text=True, check=True,
    )
    return result.stderr


def stream_durations(video: Path) -> dict:
    """Return the duration of each stream type, in seconds."""
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "stream=codec_type,duration",
         "-of", "json", str(video)],
        capture_output=True, text=True, check=True,
    )
    streams = json.loads(result.stdout)["streams"]
    return {s["codec_type"]: float(s.get("duration", 0)) for s in streams}


def contact_sheet(video: Path, out: Path, duration: float) -> None:
    """Save 18 evenly spaced frames as one 6x3 image."""
    fps = 18 / max(duration, 1)
    subprocess.run(
        ["ffmpeg", "-v", "error", "-y", "-i", str(video),
         "-vf", f"fps={fps:.4f},scale=216:-1,tile=6x3", "-frames:v", "1", str(out)],
        check=True,
    )


def cut_strips(video: Path, cutmap: list[dict], fps: float, folder: Path) -> list[str]:
    """Save 10 frames either side of every cut as one strip per cut."""
    paths = []
    for seg in cutmap[:-1]:
        at = seg["output_end"]
        out = folder / f"cut-{at:06.2f}s.png"
        subprocess.run(
            ["ffmpeg", "-v", "error", "-y", "-ss", f"{max(at - 10 / fps, 0):.3f}", "-i", str(video),
             "-vf", "scale=108:-1,tile=10x2", "-frames:v", "1", str(out)],
            check=True,
        )
        paths.append(str(out))
    return paths


def find_events(log: str, key: str) -> list[str]:
    """Pull the start times of black or frozen stretches from FFmpeg's log."""
    return re.findall(rf"{key}:\s*([\d.]+)", log)


def loudness(video: Path) -> dict:
    """Measure integrated loudness and true peak."""
    log = ffmpeg_log(["-i", str(video), "-vn", "-af", "loudnorm=print_format=json"])
    data = json.loads(log[log.rindex("{"):log.rindex("}") + 1])
    return {"lufs": float(data["input_i"]), "true_peak_db": float(data["input_tp"])}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("video", type=Path)
    parser.add_argument("--cutmap", type=Path)
    parser.add_argument("--brand", type=Path, default=Path("brand.json"))
    parser.add_argument("--folder", type=Path, default=Path("work/qa"))
    args = parser.parse_args()

    if not args.video.exists():
        print(f"Not found: {args.video}", file=sys.stderr)
        return 1
    args.folder.mkdir(parents=True, exist_ok=True)
    brand = json.loads(args.brand.read_text()) if args.brand.exists() else {}
    target = brand.get("audio", {})

    durations = stream_durations(args.video)
    length = max(durations.values())
    fps = brand.get("format", {}).get("fps", 30)
    issues: list[str] = []

    contact_sheet(args.video, args.folder / "sheet.png", length)
    strips = []
    if args.cutmap and args.cutmap.exists():
        strips = cut_strips(args.video, json.loads(args.cutmap.read_text()), fps, args.folder)

    log = ffmpeg_log(["-i", str(args.video), "-an", "-vf", "blackdetect=d=0.5,freezedetect=d=1"])
    black, frozen = find_events(log, "black_start"), find_events(log, "freeze_start")
    if black:
        issues.append(f"Black frames starting at {', '.join(black)} s")
    if frozen:
        issues.append(f"Frozen frames starting at {', '.join(frozen)} s")

    if "audio" in durations and "video" in durations:
        gap = abs(durations["audio"] - durations["video"])
        if gap > 0.1:
            issues.append(f"Audio and video lengths differ by {gap:.2f} s")

    level = loudness(args.video) if "audio" in durations else {}
    if level:
        goal = target.get("loudness_lufs", -14)
        if abs(level["lufs"] - goal) > 2:
            issues.append(f"Loudness {level['lufs']} LUFS, target {goal}")
        if level["true_peak_db"] > target.get("true_peak_db", -1.5) + 0.1:
            issues.append(f"True peak {level['true_peak_db']} dBTP is too high")

    report = {
        "video": str(args.video), "durations": durations, "loudness": level,
        "contact_sheet": str(args.folder / "sheet.png"), "cut_strips": strips,
        "issues": issues,
        "look_at": "Open the contact sheet and every cut strip. Check text against the safe zone, "
                   "captions over faces, one-frame flashes and framing.",
    }
    (args.folder / "report.json").write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
