# SOP Writer

Turn "here's roughly how I do it" into a procedure someone else, or your AI, can follow.

Paste a voice-note transcript, a bullet dump or a rambling description. It pulls out the
trigger, owner, tools, steps and "done" criteria, asks only for what's missing (always
including edge cases), never invents steps, and ends with a handoff test. It also flags
which steps an AI agent could take over.

## Install

**Claude Code:** copy the folder into your skills directory.

```bash
cp -r skills/sop-writer ~/.claude/skills/      # all projects
# or: cp -r skills/sop-writer .claude/skills/  # one project
```

**Claude apps:** zip the `sop-writer` folder and upload it under Settings → Capabilities → Skills.

## Try it

- "Write an SOP for how I publish a newsletter: <notes>"
- "I want to delegate client onboarding, here's what I do"
- "Turn this into a checklist an assistant could follow"

Inspired by *SOP Writer* from [AI Skill of the Week](https://github.com/aiskilloftheweek/claude-ai-skill-of-the-week). This is a rewritten version.
