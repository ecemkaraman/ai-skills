# Self-Review

Make the AI grade its own work before you rely on it.

Run it right after an answer you're about to send, publish or act on. It re-reads the
output against five fixed questions: did it answer the ask, what's uncertain, what's vague,
what's inconsistent, and what would go wrong in use. It returns only a list of what to fix,
pointing at exact lines and naming every fact it isn't sure of. It fixes them only if you
ask.

## Install

**Claude Code:** copy the folder into your skills directory.

```bash
cp -r skills/self-review ~/.claude/skills/      # all projects
# or: cp -r skills/self-review .claude/skills/  # one project
```

**Claude apps:** zip the `self-review` folder and upload it under Settings → Capabilities → Skills.

## Try it

- "Review that"
- "Grade your last answer"
- "Is this ready to send?"

Inspired by *Make AI Grade Its Own Work* from [AI Skill of the Week](https://github.com/aiskilloftheweek/claude-ai-skill-of-the-week). This is a
rewritten version.
