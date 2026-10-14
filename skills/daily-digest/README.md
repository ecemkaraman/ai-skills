# Daily Digest

A morning brief that tells you what changed in the last 24 hours, and why it matters, in
about five minutes of reading.

It pulls ~120 sources (AI labs, research, tech press, markets, central banks, policy,
geopolitics, science), clusters duplicate coverage, and only keeps stories where something
actually changed. Output is a tabbed HTML page: Today's Brief, AI Technical, AI Business,
Markets, Economics & Policy, Geopolitics, Culture & Science, plus an optional **For You**
tab tied to your own work.

## Why it's cheap to run

Python does the fetching, deduping and HTML. The model only reads a ~70-line shortlist and
writes a small JSON payload. A run stays well under 40k tokens.

## Requirements

- Python 3.9+
- `pip install -r requirements.txt` (just PyYAML)
- Network access

Edit `sources.yaml` and replace `you@example.com` in `gov_user_agent` with your own
email. US government feeds (BLS, SEC) reject requests without a contact.

Briefs and run state are saved to `~/.daily-digest/`. Set `DIGEST_HOME` to change that.

## Install

**Claude Code:** copy the folder into your skills directory.

```bash
cp -r skills/daily-digest ~/.claude/skills/      # all projects
# or: cp -r skills/daily-digest .claude/skills/  # one project
```

**Claude apps:** zip the `daily-digest` folder and upload it under Customize → Skills (+ → Create skill → Upload a skill). Code execution must be on in Settings → Capabilities.

## Try it

- "Morning brief"
- "Daily digest, last 72 hours" (after time away)
- "Morning brief, focus on markets"

For the **For You** tab, add a `my-context.md` (template in the repo root) with your
role and focus.

## Maintain

```bash
python scripts/harvest_feeds.py --health
```

Re-checks every source and flags dead feeds. Add or remove sources in `sources.yaml`.
