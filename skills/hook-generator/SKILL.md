---
name: hook-generator
description: Generate, assess and refine opening hooks for short videos, posts, articles and newsletters. Finds distinct angles first, then writes hooks that sound natural, stay true to the content, and ranks them. Use for "give me hooks for this", "check my hook", "make this opening stronger", or "compare these hooks".
---

# Hook Generator

**Different angles first, wording second.** A good hook is the strongest *true* reason to
keep watching. It promises something the content actually delivers.

## Modes

| Mode | When | What it does |
|---|---|---|
| `generate` (default) | An idea, notes, script or article needs an opening | Finds angles, writes 8–12 hooks, ranks, polishes finalists |
| `assess` | "Check this hook" | Diagnoses one hook: keep, repair, or reframe |
| `refine` | "Tighten this hook" | Keeps the angle, improves the wording |
| `compare` | Several hooks supplied | Ranks them and recommends one |
| `from-script` | A full script | Looks for the best buried line before inventing one |

Default format is a spoken short video. Adapt for posts, articles or email subject lines
when asked.

If `my-context.md` exists in the project root or `~/.claude/`, read its audience and Voice
sections. Otherwise ask nothing and write for a smart, curious general audience.

## Step 1: Read the content

Before writing anything, establish:

- **Core idea:** the actual point beneath the topic.
- **Information gain:** what the viewer will understand afterwards that they didn't before.
- **Strongest asset:** a result, mechanism, test, build, trade-off, example or observation.
- **Proof available:** what's supplied, and its limits.

If the idea is generic, say so: "This needs a more specific insight before hook wording
will help," and suggest what's missing (an example, a number, a comparison). Don't fill
the count with hype.

Never invent results, numbers, experiments or experiences.

## Step 2: Angles before wording

Read `references/hook-families.md`. Pick 4–6 families the content can genuinely support.
No Experiment hook without a real test, no Build hook without a real build.

For each candidate, note the viewer's reason to continue and the payoff it promises. Then
write 8–12 hooks grouped by family. Before ranking, strip the family labels and compare:
if two hooks make the same promise the same way, cut one. Rewording is not a new angle.

## Step 3: Ear test (spoken formats)

Every spoken hook must:

- Be one or two complete, natural sentences with normal connecting words ("so", "if you",
  "because"). No telegraphic fragments like "Tools change. Systems don't."
- Name the subject (tool, task or problem) in the first sentence.
- Be sayable in one breath to a friend across a table without sounding read.
- Skip softeners that weaken it ("just", "kind of", "at some point"). Casual qualifiers
  like "honestly" or "I think" are fine when natural.
- Start at the audience's level. Don't open on a question they consider basic.

For written formats, check that the first line makes sense on its own before "see more".

## Step 4: Rank

Score each hook 1–5 on: **Attention, Relevance, Tension, Information gain, Specificity,
Payoff fit, Natural voice.** These are editorial judgements, not predictions.

**Truth is a gate, not a score.** A hook that overpromises or distorts is repaired or cut,
however attention-grabbing. Narrow the claim instead of stacking hedges into it.

Pick: **Best overall**, **Best for reach**, **Best for credibility**, and a **Wildcard**
(omit if none qualifies). One hook can win several.

## Step 5: Polish finalists

Take the 3 distinct finalists. Write a Preferred and a Variant version of each. Keep the
angle and claim; polish for the ear. Re-run the ear test and the truth gate after editing.

## Assess, refine, compare

- **Assess:** score the hook, quote the exact weak phrase, and give a verdict: Keep,
  Targeted repair, Reframe needed, or Blocked by missing proof. If it's strong, say why and
  stop. Otherwise offer 2–3 repairs, each labelled with what it fixes.
- **Refine:** keep the angle, offer a few tighter versions, recommend one. If the original
  is better, say so.
- **Compare:** rank only the supplied hooks with a reason each. Don't generate new ones
  unless asked.

## Output (generate)

```
Core idea: ...
Strongest asset: ...

[Family] (angle: reason to continue)
 1. hook
 2. hook
...

Best overall: #N, why
Best for reach: #N, why
Best for credibility: #N, why
Wildcard: #N, why

Finalists
A. Preferred: ...  Variant: ...
B. ...
C. ...
```

## Never

Empty bait ("you won't believe", "this changes everything", "nobody is talking about
this"), fear of falling behind, fake urgency, or a count that doesn't match the content.
Familiar frames ("Stop doing X", "Here's why X") are fine when the rest is specific and true.
