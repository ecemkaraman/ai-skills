---
name: repurpose
description: Adapt one piece of content into a genuinely different format (script to LinkedIn post, article to carousel, thread to newsletter section, video to caption) by making a real creative decision for the new channel, not by reformatting. Ends with a map of what else the piece could become. Use for "turn this into a LinkedIn post", "repurpose this", "make a carousel from this article".
---

# Repurpose

One good piece of work can feed several channels. A repurpose that only reshuffles the same
words is a failure, even if every word changed. Each version needs its own entry point and
structure for the place it will live.

## Input

```
SOURCE: the original content (script, article, post, notes, transcript)
FORMAT: target format(s): linkedin post, x thread, carousel, caption, newsletter, short video, email
NOTES:  anything specific (optional)
```

If the target format isn't given, ask one question. If `my-context.md` exists in the
project root or `~/.claude/`, read its Voice and channels sections.

## Step 1: Find what travels

Identify the core idea, the strongest asset (example, result, mechanism, opinion), and the
evidence. These must survive intact. Everything else can change.

## Step 2: Decide what the format needs

| Format | What changes |
|---|---|
| **LinkedIn post** | Written register. Point in the first two lines (before "see more"). Short paragraphs. Grounded in a real build, finding or opinion, for a professional reader |
| **X / Threads** | First post stands alone. One idea per post. Cut setup ruthlessly |
| **Carousel** | Slide 1 is the hook. One idea per slide, under ~25 words each. Last slide pays off the promise |
| **Caption** | The first line works on its own. Adds context the video didn't, doesn't repeat it |
| **Newsletter section** | Room for nuance, links and caveats. Conversational, but complete |
| **Short video** | Spoken. See the `reel-script` skill for the full approach |

Make a real creative choice: a new entry point, a different example forward, a different
structure. Keep the voice and the evidence.

If the source has no genuine angle for a format, or forcing it would mean inventing
something, say so instead of producing a weak version.

## Step 3: Quality check

Before returning, check each version: no empty engagement bait ("save this", "follow for
more", "this changes everything"), no tacked-on motivational ending, no claims beyond the
source, no AI filler. Fix anything that fails. Don't flag it and leave it broken.

## Output

```
[FORMAT]
<copy-paste ready content>

---
What else this could become:
- <format + specific angle, e.g. "the 3-step check in the middle could be a 3-slide carousel">
- <up to 4, only if genuinely worth it>

Note: <anything that didn't translate cleanly; omit if nothing>
```

Never repurpose something that was itself produced by this skill. Go back to the original.
