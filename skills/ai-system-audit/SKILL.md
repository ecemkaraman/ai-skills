---
name: ai-system-audit
description: Map and audit your Claude Code setup. Scans instruction files (CLAUDE.md, AGENTS.md), skills, agents, rules, commands, hooks, MCP config and context files, renders a one-page visual map, and lists what is broken, stale or drifting so you can keep the system current. Use for "audit my AI system", "map my setup", "what's stale in my skills", "is my context up to date", or after adding or renaming skills.
---

# AI System Audit

Your AI system is the set of files that tell your assistant who you are and how to work:
instruction files, skills, agents, rules, context docs, hooks and connectors. It drifts.
Skills get renamed, context goes stale, two files start saying different things. This skill
shows you the whole system on one page and tells you what needs attention.

It reads and reports. It never edits, moves or deletes your files unless you ask after
seeing the report.

## Input

- No argument: audit the current project, plus the user-level `~/.claude/` setup.
- `project`: current project only.
- `global`: `~/.claude/` only.
- A path: audit that directory.
- `map-only` or `audit-only`: skip the other half.

## Step 1: Inventory

Discover what exists. Never work from a hardcoded list or memory. Use `ls`, `find` and
`grep`; read frontmatter and headings before reading whole files.

| Layer | Where to look |
|---|---|
| Instruction files | `CLAUDE.md`, `AGENTS.md`, `CLAUDE.local.md` at project root and parents; `~/.claude/CLAUDE.md`; any `@path` imports they contain |
| Skills | `.claude/skills/*/SKILL.md`, `~/.claude/skills/*/SKILL.md`, and symlinked skill folders (note the link target) |
| Agents | `.claude/agents/*.md`, `~/.claude/agents/*.md` |
| Rules | `.claude/rules/*.md` or any rules folder the instruction files point to |
| Commands | `.claude/commands/*.md`, `~/.claude/commands/*.md` |
| Hooks and permissions | `hooks` and `permissions` in `.claude/settings.json`, `.claude/settings.local.json`, `~/.claude/settings.json` |
| Connectors | `.mcp.json`, and `mcpServers` in settings files |
| Context and memory | Folders the instruction files reference (`context/`, `docs/`, `memory/`); `MEMORY.md` indexes |

For each item, record: name, path, one-line purpose (from its description or first
heading), what it references (files, other skills, agents, tools), any "updated" or "last
reviewed" date in the text, file modified date, and line count.

## Step 2: Check

Run these checks. Each finding needs a file path and, where possible, a line number and a
quoted snippet. Say "possible" for anything that needs judgement.

**Broken**
- A referenced path, `@import`, skill, agent or script that does not exist.
- A skill whose frontmatter is missing `name` or `description`, or whose `name` does not
  match its folder.
- A symlink pointing nowhere.
- A hook or MCP server pointing to a command or file that does not exist.

**Stale**
- An "updated" or "last reviewed" date more than 90 days old, or older than the files it
  describes.
- A file that describes the system (a map, an index, a README) listing items that no
  longer exist, or missing items that do.
- References to tools, models or product names the rest of the system has moved away from.

**Drift and conflict**
- Two files giving different instructions for the same thing (e.g. one says "always ask
  before X", another says "do X automatically"). Quote both lines.
- Two skills whose descriptions overlap enough that the assistant could pick either.
- The same content copied into two places instead of referenced (a likely future conflict).

**Unused**
- Skills, agents, rules or context files that nothing references and whose description
  would rarely trigger. Report as "possibly unused", not as wrong: many skills are invoked
  by name.

**Cost and safety**
- Instruction files loaded every session that run long (over about 300 lines combined is
  worth a look), since they cost context on every turn.
- Anything that looks like a secret: API keys, tokens, passwords. Report file and line
  only. **Never print the value.**
- Permission rules broad enough to allow destructive commands without a prompt.

Do not report style preferences as findings.

## Step 3: Render the map

Write one self-contained HTML file, `ai-system-map.html`, in the audited root (or the path
the user gives). Overwrite only a file this skill created; if another file has that name,
ask first.

Layout, top to bottom:

1. **Header:** audited path, date, counts (instruction files, skills, agents, rules,
   commands, hooks, MCP servers, context files), and a health line: `N broken · N stale ·
   N drift · N unused`.
2. **Diagram:** a Mermaid flowchart. One node per instruction file, skill, agent, rule,
   connector and context folder, grouped in subgraphs by layer. Draw an edge only for a
   reference you actually found in a file. Mark nodes with findings in a warning colour.
   Load Mermaid from `https://cdn.jsdelivr.net/npm/mermaid@10.9.1/dist/mermaid.min.js`.
   Over about 40 nodes, collapse each layer into one node with a count and list members
   in the catalog instead.
3. **Findings:** grouped Broken, Stale, Drift and conflict, Unused, Cost and safety. Each
   with path, line, quote and a one-line suggested fix.
4. **Catalog:** one card per item with name, path, purpose, references, dates, line count.

Keep it readable: system font stack, light and dark mode via `prefers-color-scheme`,
works at phone width, no other external assets.

## Step 4: Report

In chat, print:

```
Audited: <path>   Map: <path to ai-system-map.html>
Inventory: N instruction files · N skills · N agents · N rules · N hooks · N MCP · N context files
Health: N broken · N stale · N drift · N unused

Fix first:
1. <most important finding, one line, with path>
2. ...
3. ...
```

Order "Fix first" by impact: broken references the assistant will hit, then conflicts that
change behaviour, then stale context, then tidy-ups. Stop at five.

Then offer to fix specific findings. Make changes only for the ones the user picks, and
show each edit.

## Rules

- Count from the filesystem, not memory. Read a file before describing it.
- Quote evidence for every finding. No finding without a path.
- Never print secrets, and never send file contents anywhere.
- A clean audit is a valid result. Say so in one line and still render the map.
