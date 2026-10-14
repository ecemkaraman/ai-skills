# AI Writing Check

Find out whether your draft sounds like AI, and fix only the lines that do.

**Check** quotes every line with empty hype, AI filler ("unlock", "dive into", "it's not X,
it's Y"), a tacked-on moral, or an unsupported claim, scores the draft on a 7-point bar, and
ranks what to fix first. **Fix** rewrites only the failing lines and shows you each change.
Casual phrasing and contractions stay. That's what makes writing sound human.

Add a `my-context.md` (template in the repo root) with a few sample lines of your writing
and it checks against *your* voice, not a generic one.

## Install

**Claude Code:** copy the folder into your skills directory.

```bash
cp -r skills/ai-writing-check ~/.claude/skills/      # all projects
# or: cp -r skills/ai-writing-check .claude/skills/  # one project
```

**Claude apps:** zip the `ai-writing-check` folder and upload it under Customize → Skills (+ → Create skill → Upload a skill). Code execution must be on in Settings → Capabilities.

## Try it

- "Does this sound like AI? <draft>"
- "Check this LinkedIn post"
- "Humanize this and show me what you changed"
