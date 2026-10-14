# Slack Inbox

Use private Slack channels as your capture tool, and let this skill do the processing.

It reads new messages from the channels you choose (brain dump, ideas, read-later,
reminders), lightly cleans them, sorts them under headings (tasks, things to read, ideas,
plans, lists), appends them to one running `inbox.md`, and reacts 📥 to each message so
nothing is processed twice. Ticked tasks move to a Done section automatically.

## Requirements

A Slack connector (MCP) with permission to read channels and add reactions.

## Install

**Claude Code:** copy the folder into your skills directory.

```bash
cp -r skills/slack-inbox ~/.claude/skills/      # all projects
# or: cp -r skills/slack-inbox .claude/skills/  # one project
```

**Claude apps:** zip the `slack-inbox` folder and upload it under Settings → Capabilities → Skills.

On first run it asks which channels to process and creates `slack-inbox.config.md`. Edit
that file to change channels or headings.

## Try it

- "Process my Slack"
- "Clear my brain dump"
