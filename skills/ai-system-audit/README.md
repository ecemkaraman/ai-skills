# AI System Audit

See your whole Claude setup on one page and find out what's broken, stale or drifting.

Your AI system is a pile of files: CLAUDE.md, skills, agents, rules, context docs, hooks,
MCP servers. Over time skills get renamed, context goes out of date, and two files start
giving opposite instructions. This skill scans all of it, renders a visual map, and gives
you a short "fix first" list.

## What you get

- `ai-system-map.html`: a diagram of how your instruction files, skills, agents, rules,
  connectors and context connect, plus a card per item.
- A findings list: broken references, stale dates and indexes, conflicting instructions,
  overlapping skills, possibly unused files, oversized always-loaded context, and anything
  that looks like a secret (file and line only, never the value).
- A ranked "fix first" list in chat. It never edits anything unless you ask.

## Install

**Claude Code:** copy the folder into your skills directory.

```bash
cp -r skills/ai-system-audit ~/.claude/skills/      # all projects
# or: cp -r skills/ai-system-audit .claude/skills/  # one project
```

**Claude apps:** zip the `ai-system-audit` folder and upload it under Customize → Skills (+ → Create skill → Upload a skill). Code execution must be on in Settings → Capabilities.

## Try it

- "Audit my AI system"
- "Map my Claude setup, project only"
- "What's stale in my skills?"

Run it after you add or rename skills, or once a month.
