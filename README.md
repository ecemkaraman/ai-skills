# AI Skills

Free, practical skills for Claude that I've built and use in my own AI system, packaged so
they work for anyone.

From [AI with Ecem](https://aiwithecem.com): researching, building, testing and explaining AI.

## The skills

| Skill | What it does |
|---|---|
| [ai-system-audit](skills/ai-system-audit) | Maps your Claude setup on one page and flags what's broken, stale or conflicting |
| [daily-digest](skills/daily-digest) | A tabbed morning brief on what changed in AI, markets, policy and the world in the last 24 hours |
| [video-transcriber](skills/video-transcriber) | Turns Reels, TikToks and Shorts into a searchable swipe file of full transcripts, locally |
| [slack-inbox](skills/slack-inbox) | Clears Slack capture channels into one grouped markdown inbox |
| [ai-writing-check](skills/ai-writing-check) | Finds AI-sounding lines in a draft and fixes only those |
| [hook-generator](skills/hook-generator) | Generates, ranks and repairs opening hooks across different angles |
| [reel-script](skills/reel-script) | Brain dump → outline → 45–60s spoken script in your voice |
| [repurpose](skills/repurpose) | Adapts one piece into a genuinely different format and channel |
| [thinking-partner](skills/thinking-partner) | Stress-tests a plan and ends with the cheapest test to run this week |
| [sop-writer](skills/sop-writer) | Turns how you do something into a procedure someone (or an AI) can follow |
| [self-review](skills/self-review) | Makes the AI grade its own output before you use it |

## Install a skill

**Claude Code:** copy a skill folder into your skills directory.

```bash
git clone https://github.com/ecemkaraman/ai-skills.git
cp -r ai-skills/skills/ai-system-audit ~/.claude/skills/
```

Use `~/.claude/skills/` for all projects, or `.claude/skills/` inside a project for one.
Claude picks a skill automatically when your request matches its description, or you can
call it by name.

**Claude apps:** zip a skill folder and upload it under Settings → Capabilities → Skills.

Some skills need Python or a connector. Each skill's README lists what it needs.

## Make them yours: `my-context.md`

Several skills write or judge in *your* voice. Copy [`my-context.md`](my-context.md) to
your project root or `~/.claude/my-context.md` and fill it in. Skills that use it:
ai-writing-check, hook-generator, reel-script, repurpose, daily-digest (For You tab).
Without it they fall back to clear, neutral defaults.

## Credits

`thinking-partner`, `sop-writer` and `self-review` are rewritten versions of ideas from
[AI Skill of the Week](https://github.com/aiskilloftheweek/claude-ai-skill-of-the-week).

## License

MIT. Use them, change them, share them.
