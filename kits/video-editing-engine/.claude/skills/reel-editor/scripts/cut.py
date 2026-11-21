#!/usr/bin/env python3
"""Cut a video to the segments in a timeline file, in one FFmpeg pass.

Reads the timeline's `source` and `segments` (source times, in seconds),
renders the kept segments with a short audio fade at every cut, and writes:

  work/rough.mp4          the rough cut
  work/cutmap.json        where each segment landed in the output
  work/rough.words.json   transcript words moved to output time (with --words)

Usage:
  python3 cut.py work/timeline.json --plan            # print the plan, render nothing
  python3 cut.py work/timeline.json --words work/take.json
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

FADE_S = 0.03


def load_segments(timeline: dict) -> list[dict]:
    """Return the segments in source order, rejecting overlaps and bad ranges."""
    segments = sorted(timeline["segments"], key=lambda s: s["start"])
    previous_end = 0.0
    for seg in segments:
        if seg["end"] <= seg["start"]:
            raise ValueError(f"Segment {seg.get('id')} ends before it starts.")
        if seg["start"] < previous_end:
            raise ValueError(f"Segment {seg.get('id')} overlaps the one before it.")
        previous_end = seg["end"]
    return segments


def build_cutmap(segments: list[dict]) -> list[dict]:
    """Map each kept segment from source time to output time."""
    cutmap, offset = [], 0.0
    for seg in segments:
        length = seg["end"] - seg["start"]
        cutmap.append({
            "id": seg.get("id"),
            "source_start": seg["start"],
            "source_end": seg["end"],
            "output_start": round(offset, 3),
            "output_end": round(offset + length, 3),
        })
        offset += length
    return cutmap


def filter_graph(segments: list[dict]) -> str:
    """Trim every segment from the one input, fade its audio edges, then concat."""
    parts = []
    for i, seg in enumerate(segments):
        start, end = seg["start"], seg["end"]
        fade_out = max(end - start - FADE_S, 0)
        parts.append(
            f"[0:v]trim=start={start}:end={end},setpts=PTS-STARTPTS[v{i}];"
            f"[0:a]atrim=start={start}:end={end},asetpts=PTS-STARTPTS,"
            f"afade=t=in:st=0:d={FADE_S},afade=t=out:st={fade_out:.3f}:d={FADE_S}[a{i}]"
        )
    joined = "".join(f"[v{i}][a{i}]" for i in range(len(segments)))
    return ";".join(parts) + f";{joined}concat=n={len(segments)}:v=1:a=1[v][a]"


def remap_words(words_file: Path, cutmap: list[dict]) -> list[dict]:
    """Move WhisperX word timings to output time; drop words that were cut."""
    data = json.loads(words_file.read_text())
    words = [w for s in data.get("segments", []) for w in s.get("words", []) if "start" in w]
    kept = []
    for word in words:
        for seg in cutmap:
            if seg["source_start"] <= word["start"] and word["end"] <= seg["source_end"]:
                shift = seg["output_start"] - seg["source_start"]
                kept.append({
                    "word": word["word"].strip(),
                    "start": round(word["start"] + shift, 3),
                    "end": round(word["end"] + shift, 3),
                })
                break
    return kept


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("timeline", type=Path)
    parser.add_argument("--out", type=Path, default=Path("work/rough.mp4"))
    parser.add_argument("--words", type=Path, help="WhisperX JSON of the source")
    parser.add_argument("--plan", action="store_true", help="print the cut plan and stop")
    args = parser.parse_args()

    if not args.timeline.exists():
        print(f"Timeline not found: {args.timeline}", file=sys.stderr)
        return 1
    timeline = json.loads(args.timeline.read_text())
    source = Path(timeline["source"])
    try:
        segments = load_segments(timeline)
    except ValueError as error:
        print(f"Timeline error: {error}", file=sys.stderr)
        return 1
    cutmap = build_cutmap(segments)

    total = cutmap[-1]["output_end"] if cutmap else 0
    for seg in cutmap:
        print(f"{seg['id']}: {seg['source_start']:.2f}-{seg['source_end']:.2f}s "
              f"-> {seg['output_start']:.2f}-{seg['output_end']:.2f}s")
    print(f"{len(cutmap)} segments, {total:.2f}s total")
    if args.plan:
        return 0
    if not source.exists():
        print(f"Source not found: {source}", file=sys.stderr)
        return 1

    args.out.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            "ffmpeg", "-v", "error", "-y", "-i", str(source),
            "-filter_complex", filter_graph(segments), "-map", "[v]", "-map", "[a]",
            "-c:v", "libx264", "-crf", "18", "-preset", "medium", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "192k", str(args.out),
        ],
        check=True,
    )
    cutmap_path = args.out.parent / "cutmap.json"
    cutmap_path.write_text(json.dumps(cutmap, indent=2))
    print(f"Wrote {args.out} and {cutmap_path}")

    if args.words:
        words = remap_words(args.words, cutmap)
        words_path = args.out.with_suffix(".words.json")
        words_path.write_text(json.dumps(words, indent=2))
        print(f"Wrote {words_path} ({len(words)} words)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
