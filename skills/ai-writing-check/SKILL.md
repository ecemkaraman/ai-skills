---
name: ai-writing-check
description: Check a draft (post, script, article, email, caption) for AI-sounding patterns, empty hype, unsupported claims and off-voice lines, then optionally repair only what fails. Use for "does this sound like AI?", "check this draft", "make this sound like me", "humanize this", or a final pass before publishing.
---

# AI Writing Check

Two modes, run in order unless the user asks for one:

1. **Check** diagnoses. It quotes every failing line and ranks the fixes.
2. **Fix** repairs only the lines that failed and leaves everything else alone.

Default: run Check, show the result, then ask whether to Fix. Run both straight through if
the user says "fix it", "humanize this" or similar.

## Calibrate to the writer

Look for `my-context.md` in the current project root, then `~/.claude/my-context.md`. Use
its Voice section (tone, words they use, words they avoid, sample lines). Without it, judge
against plain, direct, conversational writing, and say that's the baseline.

Ask for the format if it isn't obvious: spoken script, social post, article, email. Spoken
lines are judged by how they sound aloud, not by their punctuation.

## Check

### 1. Hard fails

Automatic failures. Quote the exact line for each.

- **Fabrication:** an experience, result, number, client, study or resource the input does
  not support.
- **Empty bait:** "you won't believe", "this will blow your mind", "this changes
  everything", "no one is talking about this", "this is your sign", "save this if you
  agree", "follow for more", fake urgency, fear of falling behind.
- **Tacked-on moral:** a motivational closing line that adds nothing. A clear conclusion or
  answer is fine.
- Anything on the writer's own avoid list.

Familiar frames ("Stop doing X", "Here's why X", "Unpopular opinion: X") are fine when the
rest of the line is specific and true. Test: swap the specific part for a generic noun. If
the line would still open any post, it's bait.

### 2. AI-pattern signals

Signals, not bans. Flag one only when it stands in for a specific thought, or repeats.

- Buzzwords and filler: "game-changer", "unlock", "dive into", "in today's fast-paced
  world", "it's worth noting", "leverage", "seamless", "robust".
- "It's not X, it's Y" reversals, especially more than one.
- Forced lists of three, where the third item exists for rhythm.
- Dramatic one-line verdicts set off for effect.
- The same sentence shape several times in a row.
- Robotic transitions: "Here's the thing", "Let's break it down", "Furthermore", "That said".
- Runs of punchy fragments that read well but sound scripted aloud.
- Hedge stacks: "it's important to note that this can potentially help".
- Em dashes used as a tic (several per paragraph).
- Lines that are clever on paper but that nobody would say out loud.

For each flag: quote the line and name the specific thing it's standing in for.

### 3. Substance bar

Pass or fail each, quoting the line for every fail:

1. **Voice:** sounds like the writer, not generic content.
2. **Concrete:** contains a real mechanism, example, observation, method or decision.
3. **Supported:** claims have the evidence they need; opinion and inference are labelled.
4. **Right depth:** fits the reader without talking down or assuming a demographic.
5. **Calibrated:** no hype, unsupported certainty or needless complexity.
6. **Useful:** the reader leaves understanding something or able to do something.
7. **Delivers:** the opening's promise is kept.

### Check output

```
Hard fails: [quoted lines, or "None"]
AI-pattern flags: [quoted line: what it stands in for, or "None worth fixing"]
Score: X/7
Failed: [point: quoted line: why]
Fix first:
1. ...
2. ...
Verdict: Ready / Needs fixes
```

If there are no hard fails, 7/7, and no flags worth fixing: say "Ready." and stop.

## Fix

Repair only what failed. For each fix, go back to what the line is trying to say and say
that plainly. Don't just swap a word.

| Problem | Repair |
|---|---|
| Bait or buzzword | Find the real point underneath and state it |
| Formula ("not X, it's Y", forced three) | Replace with the specific claim it was standing in for |
| Tacked-on moral | Cut it. End on the actual answer or decision |
| Unsupported claim | Narrow it to what the evidence supports, or remove it. Never invent support |
| Off-voice line | Rewrite in the writer's register using their own sample lines |
| Fragment runs | Join into complete, natural sentences |

Rewrite the whole draft only if more than half of it fails or the voice is wrong
throughout. Keep the topic and angle; don't add new information.

Do not "fix" casual phrasing, contractions, short sentences or a little mess. That's what
makes writing sound human.

Before returning, re-run the Check silently on the result. Don't return a draft that still
fails.

### Fix output

```
[the revised draft, copy-paste ready]

What changed:
- "original line" → "new line": why
```
