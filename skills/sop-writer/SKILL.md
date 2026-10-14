---
name: sop-writer
description: Turn a messy description of how you do something (voice note, bullet dump, screen-recording transcript) into a clear standard operating procedure someone else, or your AI, could follow. Asks only for what's missing, never invents steps, and ends with a handoff test. Use for "write an SOP", "document this process", "I want to delegate this", "turn this into a checklist", or "make this repeatable".
---

# SOP Writer

A process that only lives in your head can't be delegated, automated or improved. This
skill turns however you describe it into a procedure someone with zero context could run.

## Step 1: Get the six essentials

Pull these from the input. Ask only for what's missing, at most three questions at a time,
conversationally.

1. **Name:** what is this process called?
2. **Who runs it:** a role, not a person. You, a teammate, a contractor, or an AI agent.
3. **Trigger:** what starts it? A date, an event, a request.
4. **Done looks like:** what's objectively true when it's finished correctly?
5. **Tools:** every app or file touched, including obvious ones like email.
6. **Frequency:** how often does it run?

Always ask about edge cases if none were mentioned: "Has this ever gone wrong? Is there a
step where the person has to make a judgement call?" This is where most SOPs fail.

**Never invent** steps, tools or criteria. Infer what's clearly implied, and mark real gaps
`[TO CONFIRM]`.

## Step 2: Pick the detail level

- **Someone else runs it:** expanded. Where to click, what to type, what "good" looks like.
- **The user runs it:** compact. One line per step.
- **An AI agent runs it:** explicit inputs, outputs, decision rules and stop conditions.
  This can become a skill.

Match the destination if given (Notion, Google Docs, a task tool, an email). Default:
clean Markdown.

## Step 3: Write it

```markdown
# <Process name>
Version 1.0 · Written <date> · Review by <date + 6 months>

## Overview
- Run by: <role>
- Trigger: <what starts it>
- Frequency: <how often> · Time: <estimate>
- Done when: <objective output>

## Tools
- <Tool>: <what it's used for>

## Steps
1. **<Verb> <what>** in <tool>
2. ...

## Edge cases
- If <situation> → <do this>
- If unsure → <decision rule or who to ask>

## Done checklist
- [ ] <verifiable output>

## Handoff test
- [ ] Someone with no context could finish this using only this page
- [ ] They have access to every tool listed
- [ ] Edge cases cover things that have actually happened
- [ ] "Done" is checkable, not a matter of opinion
```

Add sections only when the process needs them:
- **Delegated:** an FAQ of 3–5 questions a first-timer would ask, and an escalation path.
- **Content or quality work:** objective quality criteria and common mistakes.
- **Onboarding:** steps grouped by Day 1 / Week 1 / Month 1.
- **Recurring ops:** time per step and early warning signs.
- **Incidents:** a decision table at the top and severity labels on steps.

## Step 4: Check

Every step starts with an active verb. Every tool named is one the user mentioned. At least
one edge case. No invented steps. The handoff test is present.

If the user says "just the steps", give a clean numbered list and keep the handoff test.

After the SOP, if the process is repetitive and rule-based, add one line noting which steps
an AI could do. Don't build it unless asked.
