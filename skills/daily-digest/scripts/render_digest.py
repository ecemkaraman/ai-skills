#!/usr/bin/env python3
"""Render the Morning Brief JSON payload into a standalone tabbed HTML file.

The skill writes content. This script owns every pixel: shell, theme, tab behaviour,
Market Pulse strip. That split exists so a morning run never pays output tokens for CSS
that is identical every day.

Usage:
    python scripts/render_digest.py brief.json
    python scripts/render_digest.py brief.json --out path/to/file.html
    python scripts/render_digest.py --schema          # print the payload shape and exit

Standard library only.
"""

from __future__ import annotations

import argparse
import html
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

DATA_DIR = Path(os.environ.get("DIGEST_HOME", Path.home() / ".daily-digest")).expanduser()
OUTPUT_DIR = DATA_DIR / "briefs"

# Tab order is fixed. A quiet tab still renders, so the shape of the day is legible.
TABS: list[tuple[str, str]] = [
    ("brief", "Today's Brief"),
    ("ai_technical", "AI: Technical"),
    ("ai_business", "AI: Business & Startups"),
    ("markets", "Markets"),
    ("economics", "Economics & Policy"),
    ("geopolitics", "Geopolitics"),
    ("culture_science", "Culture & Science"),
    ("for_you", "For You"),
]

STATUS_LABELS = {"new": "NEW", "developing": "DEVELOPING", "follow-up": "FOLLOW-UP"}

SCHEMA = """
{
  "date": "2026-09-14",                  ISO date
  "weekday_title": "Monday 14 September 2026",
  "window": "13 Sep 09:00 to 14 Sep 09:00 ET",
  "meta": "1,400 items | 302 clusters | 12 selected",
  "market_pulse": {
    "main": [{"label": "S&P 500", "value": "7,656.98", "change_pct": 0.86}],
    "secondary": [{"label": "Brent", "value": "109.15", "change_pct": 4.34}],
    "read": "Two or three sentences. What moved, what risk is live, what comes next."
  },
  "tabs": {
    "brief": {
      "items": [
        {"status": "new", "title": "Saudi pipeline stays shut",
         "text": "One sentence on what happened and why it is here.", "url": "https://..."}
      ]
    },
    "ai_technical": {
      "stories": [
        {"status": "developing", "tag": "MODELS", "headline": "...",
         "what_happened": "One or two factual sentences.",
         "what_it_means": "One or two sentences on consequence.",
         "insight_label": "The tell", "insight": "One sharp sentence.",
         "sources": [{"name": "Reuters", "url": "https://..."}],
         "evidence": "reported",
         "note": "previously covered 11 Sep"}
      ],
      "micro": [{"text": "Fact plus what it signals.", "url": "https://..."}],
      "empty": "No major signal today."
    },
    "for_you": {
      "ideas": [
        {"title": "...", "signal": "...", "angle": "...", "hook": "...", "format": "optional"}
      ]
    }
  },
  "extra": {
    "pattern_recognition": [{"label": "...", "text": "..."}],
    "go_deeper": [{"title": "...", "why": "...", "url": "https://..."}],
    "watchlist": ["..."],
    "takeaways": ["..."]
  },
  "footer": "Sources: 111 of 112 healthy. Degraded: llama.cpp (empty)."
}

Every tab key in TABS may be present. Omit a tab and it renders its empty line.
Story keys beyond "headline" are optional; omit rather than pad.
"""

STYLE = """
:root{
  --bg:#0e0f12; --panel:#16181d; --panel-2:#1c1f26; --line:#2a2e37;
  --ink:#e8e6e1; --ink-dim:#9aa0ab; --ink-faint:#6b7280;
  --gold:#c9a84c; --gold-dim:#8a7433;
  --up:#4ea87a; --down:#c2605a;
  --serif:"Playfair Display",Georgia,"Times New Roman",serif;
  --sans:"DM Sans",-apple-system,BlinkMacSystemFont,"Segoe UI",Helvetica,Arial,sans-serif;
  --mono:"DM Mono",ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;
}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font-family:var(--sans);
  font-size:15px;line-height:1.6;-webkit-font-smoothing:antialiased}
.wrap{max-width:960px;margin:0 auto;padding:32px 20px 80px}
a{color:var(--gold);text-decoration:none;border-bottom:1px solid var(--gold-dim)}
a:hover{color:#e0bf63}

header{border-bottom:1px solid var(--line);padding-bottom:20px;margin-bottom:24px}
.eyebrow{font-family:var(--mono);font-size:11px;letter-spacing:.16em;text-transform:uppercase;
  color:var(--gold);margin-bottom:10px}
h1{font-family:var(--serif);font-size:40px;line-height:1.12;margin:0 0 10px;font-weight:500}
.sub{font-family:var(--mono);font-size:12px;color:var(--ink-faint)}
.sub span{margin-right:14px}

.pulse{background:var(--panel);border:1px solid var(--line);border-radius:10px;
  padding:18px 20px;margin-bottom:24px}
.pulse h2{font-family:var(--mono);font-size:11px;letter-spacing:.16em;text-transform:uppercase;
  color:var(--gold);margin:0 0 14px;font-weight:500}
.tick-main{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin-bottom:10px}
.tick-sec{display:grid;grid-template-columns:repeat(auto-fit,minmax(108px,1fr));gap:8px}
.tick{background:var(--panel-2);border:1px solid var(--line);border-radius:7px;padding:10px 12px}
.tick .lbl{font-family:var(--mono);font-size:10px;letter-spacing:.08em;text-transform:uppercase;
  color:var(--ink-faint);margin-bottom:5px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.tick .val{font-family:var(--mono);font-size:17px;font-weight:500}
.tick-sec .val{font-size:14px}
.tick .chg{font-family:var(--mono);font-size:11px;margin-top:2px}
.up{color:var(--up)} .down{color:var(--down)} .flat{color:var(--ink-faint)}
.pulse .read{margin:16px 0 0;padding-top:14px;border-top:1px solid var(--line);
  color:var(--ink-dim);font-size:14px}

nav{display:flex;flex-wrap:wrap;gap:6px;margin-bottom:22px;
  border-bottom:1px solid var(--line);padding-bottom:12px}
nav button{background:transparent;border:1px solid transparent;color:var(--ink-dim);
  font-family:var(--sans);font-size:13px;padding:7px 13px;border-radius:999px;cursor:pointer;
  transition:all .14s}
nav button:hover{color:var(--ink);background:var(--panel)}
nav button[aria-selected="true"]{background:var(--gold);color:#15140f;font-weight:500;
  border-color:var(--gold)}
nav button .n{font-family:var(--mono);font-size:10px;opacity:.62;margin-left:5px}

.panel[hidden]{display:none}
.empty{color:var(--ink-faint);font-style:italic;padding:26px 0}

.brief-list{list-style:none;padding:0;margin:0}
.brief-list li{padding:13px 0;border-bottom:1px solid var(--line);display:flex;gap:12px}
.brief-list li:last-child{border-bottom:0}
.dot{color:var(--gold);flex-shrink:0}

.chip{display:inline-block;font-family:var(--mono);font-size:9.5px;letter-spacing:.1em;
  padding:2.5px 7px;border-radius:3px;text-transform:uppercase;vertical-align:2px;
  margin-right:8px;white-space:nowrap}
.chip.new{background:rgba(201,168,76,.16);color:var(--gold);border:1px solid var(--gold-dim)}
.chip.developing{background:rgba(78,168,122,.13);color:var(--up);border:1px solid rgba(78,168,122,.3)}
.chip.followup{background:rgba(154,160,171,.12);color:var(--ink-dim);border:1px solid var(--line)}
.chip.cat{background:transparent;color:var(--ink-faint);border:1px solid var(--line)}

article{background:var(--panel);border:1px solid var(--line);border-radius:10px;
  padding:20px 22px;margin-bottom:16px}
article h3{font-family:var(--serif);font-size:22px;line-height:1.25;margin:9px 0 14px;
  font-weight:500}
article p{margin:0 0 10px}
article .k{font-family:var(--mono);font-size:10.5px;letter-spacing:.09em;text-transform:uppercase;
  color:var(--ink-faint);margin-right:7px}
.insight{background:var(--panel-2);border-left:2px solid var(--gold);border-radius:0 6px 6px 0;
  padding:12px 15px;margin:14px 0 12px}
.insight .k{color:var(--gold)}
.src{font-family:var(--mono);font-size:11.5px;color:var(--ink-faint);
  padding-top:12px;border-top:1px solid var(--line);margin-top:14px}
.src a{border-bottom:0}
.src .sep{opacity:.4;margin:0 7px}

.micro{margin-top:22px;padding-top:18px;border-top:1px solid var(--line)}
.micro h4{font-family:var(--mono);font-size:10.5px;letter-spacing:.14em;text-transform:uppercase;
  color:var(--ink-faint);margin:0 0 12px;font-weight:500}
.micro ul{list-style:none;padding:0;margin:0}
.micro li{padding:8px 0 8px 20px;position:relative;color:var(--ink-dim);font-size:14px}
.micro li:before{content:"\\25C6";position:absolute;left:0;color:var(--gold-dim);font-size:9px;top:12px}

.idea{background:var(--panel);border:1px solid var(--line);border-left:2px solid var(--gold);
  border-radius:0 10px 10px 0;padding:18px 20px;margin-bottom:14px}
.idea h3{font-family:var(--serif);font-size:20px;margin:0 0 12px;font-weight:500}
.idea .hook{font-style:italic;color:var(--ink);background:var(--panel-2);
  padding:11px 14px;border-radius:6px;margin:10px 0}
.fmt{display:inline-block;font-family:var(--mono);font-size:10px;letter-spacing:.1em;
  text-transform:uppercase;color:var(--gold);border:1px solid var(--gold-dim);
  padding:3px 9px;border-radius:999px;margin-top:6px}

.extra{margin-top:38px;padding-top:26px;border-top:1px solid var(--line)}
.extra section{margin-bottom:28px}
.extra h2{font-family:var(--mono);font-size:11px;letter-spacing:.16em;text-transform:uppercase;
  color:var(--gold);margin:0 0 14px;font-weight:500}
.extra ul{list-style:none;padding:0;margin:0}
.extra li{padding:8px 0;border-bottom:1px solid var(--line);color:var(--ink-dim);font-size:14px}
.extra li:last-child{border-bottom:0}
.extra .lbl{color:var(--ink);font-weight:500}
.watch li:before{content:"\\2192";color:var(--gold);margin-right:9px}
.take li{color:var(--ink);border-bottom:0;padding:6px 0 6px 20px;position:relative}
.take li:before{counter-increment:t;content:counter(t);position:absolute;left:0;
  font-family:var(--mono);font-size:11px;color:var(--gold)}
.take ul{counter-reset:t}

footer{margin-top:44px;padding-top:18px;border-top:1px solid var(--line);
  font-family:var(--mono);font-size:11px;color:var(--ink-faint);line-height:1.7}

@media (max-width:640px){
  .wrap{padding:20px 14px 60px}
  h1{font-size:29px}
  .tick-main{grid-template-columns:repeat(2,1fr)}
  article,.idea,.pulse{padding:16px}
  article h3{font-size:19px}
}
@media print{
  body{background:#fff;color:#111}
  nav{display:none}
  .panel[hidden]{display:block!important}
  article,.pulse,.idea{border-color:#ccc;background:#fff}
}
"""

SCRIPT = """
(function(){
  var tabs=[].slice.call(document.querySelectorAll('nav button'));
  var panels=[].slice.call(document.querySelectorAll('.panel'));
  function show(id){
    tabs.forEach(function(t){t.setAttribute('aria-selected', String(t.dataset.tab===id));});
    panels.forEach(function(p){p.hidden = p.id!=='panel-'+id;});
    try{ history.replaceState(null,'','#'+id); }catch(e){}
  }
  tabs.forEach(function(t){ t.addEventListener('click',function(){ show(t.dataset.tab); }); });
  document.addEventListener('keydown',function(e){
    if(e.metaKey||e.ctrlKey||e.altKey) return;
    var i=tabs.findIndex(function(t){return t.getAttribute('aria-selected')==='true';});
    if(e.key==='ArrowRight'){ show(tabs[(i+1)%tabs.length].dataset.tab); }
    if(e.key==='ArrowLeft'){ show(tabs[(i-1+tabs.length)%tabs.length].dataset.tab); }
    if(/^[1-8]$/.test(e.key) && tabs[+e.key-1]){ show(tabs[+e.key-1].dataset.tab); }
  });
  var start=(location.hash||'').replace('#','');
  show(tabs.some(function(t){return t.dataset.tab===start;}) ? start : tabs[0].dataset.tab);
})();
"""


def esc(value: Any) -> str:
    return html.escape(str(value if value is not None else ""), quote=True)


def change_span(change: Any) -> str:
    """Render a percent move. Absent data prints nothing rather than a fabricated zero."""
    if change is None or change == "":
        return ""
    try:
        value = float(change)
    except (TypeError, ValueError):
        return f'<div class="chg flat">{esc(change)}</div>'
    css = "up" if value > 0 else "down" if value < 0 else "flat"
    return f'<div class="chg {css}">{value:+.2f}%</div>'


def render_tick(tick: dict[str, Any]) -> str:
    return (
        '<div class="tick">'
        f'<div class="lbl">{esc(tick.get("label"))}</div>'
        f'<div class="val">{esc(tick.get("value"))}</div>'
        f'{change_span(tick.get("change_pct"))}'
        "</div>"
    )


def render_pulse(pulse: dict[str, Any]) -> str:
    if not pulse:
        return ""
    main = "".join(render_tick(t) for t in pulse.get("main", []))
    secondary = "".join(render_tick(t) for t in pulse.get("secondary", []))
    parts = ['<div class="pulse"><h2>Market Pulse</h2>']
    if main:
        parts.append(f'<div class="tick-main">{main}</div>')
    if secondary:
        parts.append(f'<div class="tick-sec">{secondary}</div>')
    if pulse.get("read"):
        parts.append(f'<p class="read">{esc(pulse["read"])}</p>')
    if pulse.get("unavailable"):
        parts.append(
            f'<p class="read">Quotes unavailable: {esc(pulse["unavailable"])}</p>'
        )
    parts.append("</div>")
    return "".join(parts)


def status_chip(status: Optional[str]) -> str:
    if not status:
        return ""
    key = str(status).lower().strip()
    label = STATUS_LABELS.get(key, status.upper())
    css = "followup" if key == "follow-up" else key if key in STATUS_LABELS else "cat"
    return f'<span class="chip {css}">{esc(label)}</span>'


def render_brief_items(items: list[dict[str, Any]]) -> str:
    if not items:
        return ""
    rows = []
    for item in items:
        link = ""
        if item.get("url"):
            link = f' <a href="{esc(item["url"])}" target="_blank" rel="noopener">&#8594;</a>'
        title = f"<strong>{esc(item['title'])}</strong> " if item.get("title") else ""
        rows.append(
            '<li><span class="dot">&#9679;</span><div>'
            f'{status_chip(item.get("status"))}{title}{esc(item.get("text"))}{link}'
            "</div></li>"
        )
    return f'<ul class="brief-list">{"".join(rows)}</ul>'


def render_sources(story: dict[str, Any]) -> str:
    bits = []
    for source in story.get("sources", []):
        name = esc(source.get("name", "source"))
        bits.append(
            f'<a href="{esc(source["url"])}" target="_blank" rel="noopener">{name}</a>'
            if source.get("url")
            else name
        )
    line = '<span class="sep">&middot;</span>'.join(bits)
    if story.get("evidence"):
        line += f'<span class="sep">&middot;</span><em>{esc(story["evidence"])}</em>'
    if story.get("note"):
        line += f'<span class="sep">&middot;</span>[{esc(story["note"])}]'
    return f'<div class="src">{line}</div>' if line else ""


def render_story(story: dict[str, Any]) -> str:
    parts = ["<article>"]
    chips = status_chip(story.get("status"))
    if story.get("tag"):
        chips += f'<span class="chip cat">{esc(story["tag"])}</span>'
    if chips:
        parts.append(f"<div>{chips}</div>")
    parts.append(f'<h3>{esc(story.get("headline"))}</h3>')
    if story.get("what_happened"):
        parts.append(
            f'<p><span class="k">What happened</span>{esc(story["what_happened"])}</p>'
        )
    if story.get("what_it_means"):
        parts.append(
            f'<p><span class="k">What it means</span>{esc(story["what_it_means"])}</p>'
        )
    if story.get("insight"):
        label = esc(story.get("insight_label", "The read")).rstrip(":")
        parts.append(
            f'<div class="insight"><span class="k">{label}</span>{esc(story["insight"])}</div>'
        )
    parts.append(render_sources(story))
    parts.append("</article>")
    return "".join(parts)


def render_micro(micro: list[dict[str, Any]]) -> str:
    if not micro:
        return ""
    rows = []
    for item in micro:
        link = ""
        if item.get("url"):
            link = f' <a href="{esc(item["url"])}" target="_blank" rel="noopener">&#8594;</a>'
        rows.append(f"<li>{esc(item.get('text'))}{link}</li>")
    return f'<div class="micro"><h4>Also worth knowing</h4><ul>{"".join(rows)}</ul></div>'


def render_ideas(ideas: list[dict[str, Any]]) -> str:
    blocks = []
    for idea in ideas:
        parts = [f'<div class="idea"><h3>{esc(idea.get("title"))}</h3>']
        if idea.get("signal"):
            parts.append(f'<p><span class="k">Signal</span>{esc(idea["signal"])}</p>')
        if idea.get("angle"):
            parts.append(f'<p><span class="k">Angle</span>{esc(idea["angle"])}</p>')
        if idea.get("hook"):
            parts.append(f'<p class="hook">{esc(idea["hook"])}</p>')
        if idea.get("format"):
            parts.append(f'<span class="fmt">{esc(idea["format"])}</span>')
        parts.append("</div>")
        blocks.append("".join(parts))
    return "".join(blocks)


def tab_count(key: str, tab: dict[str, Any]) -> int:
    if key == "brief":
        return len(tab.get("items", []))
    if key == "for_you":
        return len(tab.get("ideas", []))
    return len(tab.get("stories", []))


def render_tab_body(key: str, tab: dict[str, Any]) -> str:
    if key == "brief":
        body = render_brief_items(tab.get("items", []))
    elif key == "for_you":
        body = render_ideas(tab.get("ideas", []))
    else:
        body = "".join(render_story(s) for s in tab.get("stories", []))
        body += render_micro(tab.get("micro", []))
    if not body.strip():
        return f'<p class="empty">{esc(tab.get("empty", "No major signal today."))}</p>'
    return body


def render_extra(extra: dict[str, Any]) -> str:
    if not extra:
        return ""
    sections = []

    patterns = extra.get("pattern_recognition", [])
    if patterns:
        rows = "".join(
            f'<li><span class="lbl">{esc(p.get("label"))}.</span> {esc(p.get("text"))}</li>'
            for p in patterns
        )
        sections.append(f"<section><h2>Pattern Recognition</h2><ul>{rows}</ul></section>")

    deeper = extra.get("go_deeper", [])
    if deeper:
        rows = []
        for item in deeper:
            title = esc(item.get("title"))
            if item.get("url"):
                title = f'<a href="{esc(item["url"])}" target="_blank" rel="noopener">{title}</a>'
            rows.append(f'<li><span class="lbl">{title}</span> &mdash; {esc(item.get("why"))}</li>')
        sections.append(f'<section><h2>Go Deeper</h2><ul>{"".join(rows)}</ul></section>')

    watch = extra.get("watchlist", [])
    if watch:
        rows = "".join(f"<li>{esc(w)}</li>" for w in watch)
        sections.append(f'<section><h2>Watchlist</h2><ul class="watch">{rows}</ul></section>')

    takeaways = extra.get("takeaways", [])
    if takeaways:
        rows = "".join(f"<li>{esc(t)}</li>" for t in takeaways)
        sections.append(
            f'<section class="take"><h2>Today&#39;s Takeaways</h2><ul>{rows}</ul></section>'
        )

    return f'<div class="extra">{"".join(sections)}</div>' if sections else ""


def render(payload: dict[str, Any]) -> str:
    tabs = payload.get("tabs", {})

    nav, panels = [], []
    for key, label in TABS:
        tab = tabs.get(key) or {}
        count = tab_count(key, tab)
        badge = f'<span class="n">{count}</span>' if count else ""
        nav.append(
            f'<button role="tab" data-tab="{key}" aria-selected="false" '
            f'aria-controls="panel-{key}">{esc(label)}{badge}</button>'
        )
        panels.append(
            f'<div class="panel" id="panel-{key}" role="tabpanel" hidden>'
            f"{render_tab_body(key, tab)}</div>"
        )

    sub = []
    if payload.get("window"):
        sub.append(f'<span>{esc(payload["window"])}</span>')
    if payload.get("meta"):
        sub.append(f'<span>{esc(payload["meta"])}</span>')

    title = payload.get("weekday_title") or payload.get("date", "Morning Brief")
    footer = (
        f'<footer>{esc(payload["footer"])}</footer>' if payload.get("footer") else ""
    )

    return f"""<!doctype html>
<html lang="en"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Morning Brief &middot; {esc(payload.get("date", ""))}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;700&family=DM+Mono:wght@400;500&family=Playfair+Display:wght@400;500;600&display=swap" rel="stylesheet">
<style>{STYLE}</style>
</head><body>
<div class="wrap">
<header>
  <div class="eyebrow">Morning Brief</div>
  <h1>{esc(title)}</h1>
  <div class="sub">{"".join(sub)}</div>
</header>
{render_pulse(payload.get("market_pulse", {}))}
<nav role="tablist">{"".join(nav)}</nav>
{"".join(panels)}
{render_extra(payload.get("extra", {}))}
{footer}
</div>
<script>{SCRIPT}</script>
</body></html>
"""


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Render the Morning Brief payload to HTML.")
    parser.add_argument("payload", nargs="?", help="Path to the brief JSON, or - for stdin")
    parser.add_argument("--out", type=str, default=None, help="Output path")
    parser.add_argument("--schema", action="store_true", help="Print the payload shape and exit")
    args = parser.parse_args(argv)

    if args.schema:
        print(SCHEMA)
        return 0
    if not args.payload:
        parser.error("a payload path is required unless --schema is given")

    try:
        raw = sys.stdin.read() if args.payload == "-" else Path(args.payload).read_text("utf-8")
        payload = json.loads(raw)
    except FileNotFoundError:
        print(f"ERROR: no payload at {args.payload}", file=sys.stderr)
        return 2
    except json.JSONDecodeError as error:
        print(f"ERROR: payload is not valid JSON: {error}", file=sys.stderr)
        return 2

    unknown = [k for k in payload.get("tabs", {}) if k not in dict(TABS)]
    if unknown:
        print(f"WARNING: ignoring unknown tab keys: {', '.join(unknown)}", file=sys.stderr)

    date_slug = payload.get("date") or datetime.now().date().isoformat()
    out_path = Path(args.out) if args.out else OUTPUT_DIR / f"{date_slug}_digest.html"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(render(payload), encoding="utf-8")

    filled = sum(1 for key, _ in TABS if tab_count(key, payload.get("tabs", {}).get(key) or {}))
    print(f"{out_path}\n  {filled}/{len(TABS)} tabs with content")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
