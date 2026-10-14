---
name: reel-script
description: Turn a brain dump, rough idea, article or reference into a 45–60 second spoken short-video script, in two stages. First an outline (the strongest angle and a narrative backbone), then a natural script in your voice once you approve it. Also does surgical revisions from your feedback. Use for "I have an idea for a reel/TikTok/short", "find the angle", "outline this", "turn this into a script".
---

# Reel Script

Turn an idea into a tight spoken script for a short video (Reels, TikTok, Shorts) that
keeps **what you actually want to say** and sounds like you talking, not like AI copy.

## Two stages

**Outline** runs first whenever the input is a brain dump, idea, topic, article or link and
no outline has been approved. Stop after the outline and wait.

**Script** runs when the user approves an outline, gives their own outline or rough draft,
asks for the script directly, or gives feedback on an existing script.

If `my-context.md` exists in the project root or `~/.claude/`, read its audience and Voice
sections, including any sample lines. Those samples are the best guide to how the user
sounds.

## Stage 1: Outline

**1. Read the input.**
- *Their own idea:* their message is the source of truth.
- *An article or link:* a short video carries one idea. Pick the single idea that stands
  alone and say which one. Take ideas, not wording.
- *A bare topic:* there's no opinion yet. Ask.

**2. Check you have enough.** You need what they actually think, and why a viewer should
care. If either is missing, ask up to three questions and wait: "What's your actual take?",
"What did you see or do that made you think this?", "What do most people get wrong here?",
"Who is this for, and what should they do differently afterwards?" Never invent an opinion
for them.

**3. Look things up, in proportion.** If the idea names a product, feature, number or
recent event, do a quick web check and open the pages you rely on. Keep three things
separate: a **fact** (checked at a primary source), an **opinion** (who said it, with the
link), and a **lead** (a headline you didn't open). Only facts go into a script as facts.

**4. Find the angle.** Name the two or three predictable takes most creators would post on
this. Then choose the angle that's different because it's true and specific to the user,
not because it's contrarian. If their view is the common one and it's right, keep it and
find the detail that makes it theirs.

**5. Return the outline**, about 120–180 words:

```
THESIS   What they're actually saying, in one sentence.
ANGLE    What makes this take different. Predictable takes this avoids: ...
PAYOFF   Why a viewer finds this useful or interesting.
HOOK     The direction of the opening, plus one rough line as they might say it.
BEATS    1. ... 2. ... 3. ... (each a step in the reasoning)
ENDING   The strongest takeaway or last thought.
FOUND    Only if you looked things up: 2–4 items tagged [fact] [opinion] [lead], with links.
OPEN     Anything to verify, or proof only they can supply.
```

Then stop. When they edit the outline, change only what they flagged.

## Stage 2: Script

The approved outline is the source of truth. Keep its thesis, angle, beat order and
ending. Target 45–60 seconds, roughly 100–130 spoken words.

### Voice

The script should sound like something the user would actually say aloud. Optimise for
cadence, personality, clarity and natural speech.

Keep the emotion that's in their input (frustration, excitement, disbelief, humour,
conviction) and express it through word choice and rhythm, not stage directions. Don't
sanitise strong, natural phrasing into professional language.

Flat: "Maintaining separate systems can create unnecessary complexity."
Better: "If you built your whole setup in one tool and now you're rebuilding it in another,
that's the problem right there."

### Structure

A loose flow, not a template: **hook → tension → the idea → how it works → one tangible
detail → what it means for you.** Use only the beats the idea needs.

- **Hook:** short. A strong claim or observation, not a topic introduction.
- Give the mental model before the details. Explain unfamiliar terms at first use.
- Show one concrete task or example so the viewer can picture what happens.
- For comparisons, say when each option is the right choice.
- Mostly "you". Use "I" when it adds experience, credibility or a real reaction.
- End on the actual point or decision. No motivational tagline.

### Write for the ear

Prefer contractions, natural transitions, varied sentence length and concrete words.
Avoid documentation language, noun stacks, corporate phrasing, "it's not X, it's Y"
formulas, forced lists of three, dramatic one-liners, and runs of punchy fragments. If a
line is correct but sounds unnatural aloud, rewrite it.

### Compress without killing it

Cut in this order: repeated meaning, setup before value, explanations the viewer can infer,
duplicate examples. Protect the emotion, the strong phrasing, the one example a newcomer
needs, and the connecting words that make speech flow. The shortest version isn't
automatically the best.

Return one script. It's a draft to react to, not a finished artifact.

## Revision mode

When the user gives feedback, revise surgically. Protect the lines that work.

| Feedback | Do |
|---|---|
| "too mechanical" | Same meaning, said the way they'd naturally say it |
| "too long before the value" | Compress the setup, keep its purpose |
| "lost my personality" | Restore emotion and point of view without adding length |
| "would a beginner get this?" | Add a concrete task and explain terms; keep the main point |
| "this line sounds like me" | Keep it and learn from it for the rest |

## Final check

Did I keep the idea they actually want to say? Does the hook sound like a person with an
opinion? Does value arrive fast? Does it sound natural aloud? Is anything explained twice?
Is every factual claim checked or clearly labelled as opinion?
