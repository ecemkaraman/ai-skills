---
name: self-review
description: Make the AI grade its own work before you use it. Reviews the last output (a draft, research answer, plan, code explanation or email) against a fixed checklist (did it answer the ask, is anything uncertain, vague or inconsistent) and returns only what needs fixing. Use for "review this", "grade your answer", "double check that", "is this ready to send?", or right after any output you're about to rely on.
---

# Self-Review

AI output often looks finished before it is. This skill makes the assistant re-read its own
work as a skeptical editor and list exactly what to fix. It does not rewrite unless asked.

## Target

Review the most recent substantial output in this conversation. If it's unclear which one
the user means, ask in one line. Skip throwaway answers.

## Checklist

Apply the same five questions every time, whatever the task was.

1. **Did it answer the ask?** Re-read the original request. Anything missing, skipped, or
   answered to a different question?
2. **What am I not sure about?** Every fact, number, date, name, quote, link, version or
   capability claim you can't fully stand behind. Name each one. "Probably right" counts as
   uncertain.
3. **Where is it vague?** Generic lines that a specific detail, example or number would
   improve. Quote them.
4. **Is it consistent?** Contradictions between sections, tone that shifts, terms used two
   ways, numbers that don't add up.
5. **Would it hold up in use?** If they send, publish or act on this as is, what's the most
   likely thing to go wrong?

Be as strict with your own output as you would be with someone else's. Don't defend it.

## Output

A short list, one line per issue, pointing at the exact sentence, claim or section:

```
- [Missing] The request asked for pricing; the answer covers features only.
- [Unsure] "Released in March 2025": not verified.
- [Vague] "This can significantly improve results": improve what, by how much?
- [Inconsistent] Section 2 says 3 steps, the list has 4.
- [Risk] The email names the wrong deadline if the meeting moved.
```

- No preamble, praise, recap of the checklist, or rewritten version.
- Leave out any question that found nothing.
- If nothing needs fixing: "Ready. Nothing to fix." and stop.

After the list, stop. Apply fixes only if the user asks. When they do, fix exactly the
listed issues, and verify uncertain facts (with a search, if available) rather than just
rewording them.
