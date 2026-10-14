#!/usr/bin/env python3
"""Harvest the Daily Intelligence Digest source registry into a windowed, deduplicated set.

The script does the deterministic work that a language model should not be asked to do:
fetching, resolving timestamps, canonicalising URLs, collapsing syndicated coverage into
clusters, and capping volume. It makes no editorial judgement. Ranking, selection and
analysis belong to the skill.

Usage:
    python scripts/harvest_feeds.py                  # harvest the last 24h
    python scripts/harvest_feeds.py --window 48      # widen the window
    python scripts/harvest_feeds.py --health         # re-probe the registry, write nothing
    python scripts/harvest_feeds.py --domains ai,markets
    python scripts/harvest_feeds.py --out -          # write JSON to stdout
    python scripts/harvest_feeds.py --shortlist      # harvest, print ~72 ranked candidates
    python scripts/harvest_feeds.py --expand c012,c034   # full records for selected clusters

Standard library only, apart from PyYAML for the registry.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import gzip
import html
import json
import math
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Any, Iterable, Optional

import yaml

# The registry ships with the skill. Run data (harvests, thread state, rendered briefs)
# lives outside it, in DIGEST_HOME, so updating the skill never touches your history.
SKILL_DIR = Path(__file__).resolve().parent.parent
REGISTRY_FILE = SKILL_DIR / "sources.yaml"
DATA_DIR = Path(os.environ.get("DIGEST_HOME", Path.home() / ".daily-digest")).expanduser()
HARVEST_DIR = DATA_DIR / "harvest"
STATE_FILE = DATA_DIR / "state.json"

SUMMARY_CHARS = 260
MAX_CLUSTERS = 300
CLUSTER_THRESHOLD = 0.36
MIN_SHARED_TOKENS = 2
THREAD_THRESHOLD = 0.55

# Tracking parameters and the syndication junk that makes identical stories look distinct.
TRACKING_PREFIXES = ("utm_", "at_", "cmp", "ito", "ns_", "syn-", "syn_")
TRACKING_PARAMS = {
    "ref", "referrer", "source", "src", "fbclid", "gclid", "mc_cid", "mc_eid",
    "guccounter", "guce_referrer", "guce_referrer_sig", "taid", "smid", "partner",
    "__twitter_impression", "_hsenc", "_hsmi", "sh", "leadSource", "cid", "yptr",
}

STOPWORDS = frozenset("""
a an and are as at be been but by for from has have how in into is it its of on or
that the their they this to was were what when which who will with why after before
new says say said report reports amid over about more than its his her our your you
inc corp corporation ltd limited plc llc holdings group co filer filing form
8-k 10-k 10-q 6-k s-1 13d 13g 424b defa14a
""".split())

# Namespaces seen across RSS 2.0, RDF, Atom and Dublin Core.
NS = {
    "atom": "http://www.w3.org/2005/Atom",
    "dc": "http://purl.org/dc/elements/1.1/",
    "content": "http://purl.org/rss/1.0/modules/content/",
    "rdf": "http://purl.org/rss/1.0/",
}

TAG_RE = re.compile(r"<[^>]+>")
WS_RE = re.compile(r"\s+")
WORD_RE = re.compile(r"[a-z0-9][a-z0-9'’\-]*")

# Section index pages, regulatory filler and standing nav links that reach feeds but
# are never developments. Applied to every source; see also per-source exclude_title.
BOILERPLATE_TITLE_RE = re.compile(
    r"^(ask hn:|show hn:\s*$)"
    r"|\b(scores?|stats|standings|fixtures|odds|box score)\b.*\b(news|stats|today|scores?)\b"
    r"|net asset value|total voting rights|holding\(s\) in company|transaction in own shares"
    r"|director/pdmr shareholding|^daily news\s*\d|^terms of service|^privacy policy"
    r"|^cookie policy|^responsible (scaling|disclosure) policy|^(apod|astronomy picture)"
    r"|^(video|watch|photos|podcast|live updates?|newsletter|subscribe)\s*[:|-]?\s*$"
    r"|^(world|news|markets?) in brief|^this week in |^(morning|evening) briefing"
    r"|, and other [a-z]+ (developments|news|stories)",
    re.I,
)


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------


@dataclass
class Item:
    """One normalised entry from one feed."""

    source_id: str
    source_name: str
    tier: int
    domains: list[str]
    weight: float
    headline_only: bool
    no_cluster: bool
    title: str
    url: str
    summary: str
    published_at: str  # ISO 8601 UTC

    def sort_key(self) -> tuple[int, str]:
        return (self.tier, self.published_at)


@dataclass
class Cluster:
    """One event, with every source that carried it."""

    cluster_id: str
    title: str
    url: str
    summary: str
    published_at: str
    earliest_at: str
    best_tier: int
    domains: list[str]
    source_count: int
    sources: list[str]
    headline_only: bool
    structured: bool = False
    possible_thread: Optional[str] = None
    also: list[str] = field(default_factory=list)


@dataclass
class SourceResult:
    """Outcome of fetching one source, successful or not."""

    source_id: str
    name: str
    status: str
    http_code: str
    raw_items: int
    in_window: int
    latest: Optional[str]
    error: str = ""


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------


def load_registry(path: Path = REGISTRY_FILE) -> dict[str, Any]:
    """Read and lightly validate the source registry."""
    if not path.exists():
        raise FileNotFoundError(f"Source registry not found: {path}")
    with path.open(encoding="utf-8") as handle:
        registry = yaml.safe_load(handle)

    if not isinstance(registry, dict) or "sources" not in registry:
        raise ValueError(f"Registry at {path} has no 'sources' key")

    seen: set[str] = set()
    for source in registry["sources"]:
        for required in ("id", "name", "url", "tier", "domains"):
            if required not in source:
                raise ValueError(f"Source {source.get('id', '?')} is missing '{required}'")
        if source["id"] in seen:
            raise ValueError(f"Duplicate source id: {source['id']}")
        seen.add(source["id"])

    registry.setdefault("config", {})
    return registry


def select_sources(registry: dict[str, Any], domains: Optional[list[str]]) -> list[dict[str, Any]]:
    """Return registry sources, optionally filtered to the given domains."""
    sources = registry["sources"]
    if not domains:
        return sources
    wanted = {d.strip() for d in domains if d.strip()}
    return [s for s in sources if wanted & set(s["domains"])]


# ---------------------------------------------------------------------------
# Fetching
# ---------------------------------------------------------------------------


def fetch(url: str, user_agent: str, timeout: int) -> tuple[str, bytes]:
    """Fetch a URL, returning (http_code, body). Raises only on transport failure."""
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": user_agent,
            "Accept": "application/rss+xml, application/atom+xml, application/xml, text/xml, text/html;q=0.8, */*;q=0.5",
        },
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        body = response.read()
        # Detect by magic bytes: some servers gzip without a matching header.
        if body[:2] == b"\x1f\x8b":
            body = gzip.decompress(body)
        return str(response.status), body


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------


def strip_html(text: str) -> str:
    """Flatten HTML to readable plain text."""
    return WS_RE.sub(" ", TAG_RE.sub(" ", text)).strip()


def parse_datetime(raw: str) -> Optional[datetime]:
    """Parse the date formats that appear across RSS, Atom and RDF feeds."""
    raw = raw.strip()
    if not raw:
        return None
    try:
        parsed = parsedate_to_datetime(raw)
        if parsed is not None:
            return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    except (TypeError, ValueError):
        pass
    candidate = raw.replace("Z", "+00:00")
    for attempt in (candidate, candidate[:19], candidate[:10]):
        try:
            parsed = datetime.fromisoformat(attempt)
            return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    return None


def local_name(tag: str) -> str:
    """Return an element's tag without its namespace."""
    return tag.rsplit("}", 1)[-1]


def _child_text(node: ET.Element, names: Iterable[str]) -> str:
    """First non-empty child text matching any of the given local tag names."""
    wanted = tuple(names)
    for child in node:
        if local_name(child.tag) in wanted and child.text and child.text.strip():
            return child.text.strip()
    return ""


def _entry_link(node: ET.Element) -> str:
    """Extract a usable link from an RSS item, RDF item or Atom entry."""
    fallback = ""
    for child in node:
        if local_name(child.tag) != "link":
            continue
        if child.text and child.text.strip():
            return child.text.strip()
        href = child.get("href")
        if href and child.get("rel") in (None, "alternate"):
            return href.strip()
        fallback = fallback or (href or "")
    if fallback:
        return fallback.strip()
    guid = _child_text(node, ("guid", "id"))
    return guid if guid.startswith("http") else ""


def sanitize_xml(body: bytes) -> bytes:
    """Remove bytes that are illegal in XML 1.0 so a nearly-valid feed still parses."""
    start = body.find(b"<")
    if start > 0:
        body = body[start:]
    return re.sub(rb"[\x00-\x08\x0b\x0c\x0e-\x1f]", b"", body)


def parse_feed(body: bytes) -> list[dict[str, str]]:
    """Parse RSS 2.0, RDF or Atom into raw title/url/summary/date dicts.

    Matching is done on local tag names, because the same logical feed element appears
    under at least four different namespaces across the registry.
    """
    root: Optional[ET.Element] = None
    for candidate in (body, sanitize_xml(body)):
        try:
            root = ET.fromstring(candidate)
            break
        except ET.ParseError:
            continue
    if root is None:
        return []

    entries: list[dict[str, str]] = []
    for node in root.iter():
        if local_name(node.tag) not in ("item", "entry"):
            continue
        title = strip_html(_child_text(node, ("title",)))
        if not title:
            continue
        summary = strip_html(
            _child_text(node, ("description", "summary", "encoded", "content", "abstract"))
        )
        published = _child_text(node, ("pubDate", "published", "updated", "date", "created"))
        entries.append(
            {
                "title": title,
                "url": _entry_link(node),
                "summary": summary[:SUMMARY_CHARS],
                "published": published,
            }
        )
    return entries


LEADING_DATE_RE = re.compile(
    r"^([A-Z][a-z]{2}\s+\d{1,2},\s+\d{4})\s+"
    r"(?:Announcements?|Policy|Product|Research|Societal Impacts|News|Blog|Interpretability|Alignment)?\s*",
)


def split_leading_date(title: str) -> tuple[str, str]:
    """Split a scraped title of the form 'Jul 30, 2026 Announcements Real title'.

    Returns (iso_date, clean_title). The date is empty when none is present, and the
    caller drops those items rather than assuming they are current.
    """
    match = LEADING_DATE_RE.match(title)
    if not match:
        return "", title
    try:
        parsed = datetime.strptime(match.group(1).replace("  ", " "), "%b %d, %Y")
    except ValueError:
        return "", title
    return parsed.replace(tzinfo=timezone.utc).isoformat(), title[match.end():].strip()


def parse_page_links(body: bytes, base_url: str, link_pattern: str = "") -> list[dict[str, str]]:
    """Extract dated article links from an HTML page, for sources with no feed.

    Used for Anthropic, which publishes no RSS. Deliberately conservative: it returns
    links only, with no date, so every item is treated as undated and must have its
    timing confirmed before use.
    """
    html = body.decode("utf-8", "ignore")
    entries: list[dict[str, str]] = []
    seen: set[str] = set()
    wanted = re.compile(link_pattern) if link_pattern else None
    pattern = re.compile(r'<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>', re.I | re.S)
    for href, inner in pattern.findall(html):
        text = strip_html(inner)
        if len(text) < 25 or len(text) > 200:
            continue
        url = urllib.parse.urljoin(base_url, href)
        if url in seen or urllib.parse.urlparse(url).netloc != urllib.parse.urlparse(base_url).netloc:
            continue
        if wanted and not wanted.search(url):
            continue
        seen.add(url)
        published, clean = split_leading_date(text)
        if not published:
            # No date on the page means no way to honour the window. Dropping is correct:
            # Techmeme is the backstop for anything genuinely new from these sources.
            continue
        entries.append({"title": clean, "url": url, "summary": "", "published": published})
    return entries[:40]


# ---------------------------------------------------------------------------
# Normalising and deduplicating
# ---------------------------------------------------------------------------


def canonicalize_url(url: str) -> str:
    """Strip tracking noise and syndication variants so identical stories collide."""
    if not url:
        return ""
    url = url.strip()
    try:
        parts = urllib.parse.urlsplit(url)
    except ValueError:
        return url

    netloc = parts.netloc.lower()
    if netloc.startswith("www."):
        netloc = netloc[4:]
    if netloc.endswith(":80") or netloc.endswith(":443"):
        netloc = netloc.rsplit(":", 1)[0]

    path = parts.path
    if path.endswith("/amp") or path.endswith("/amp/"):
        path = path[: path.rfind("/amp")]
    if len(path) > 1 and path.endswith("/"):
        path = path[:-1]

    kept = [
        (key, value)
        for key, value in urllib.parse.parse_qsl(parts.query, keep_blank_values=False)
        if key.lower() not in TRACKING_PARAMS
        and not any(key.lower().startswith(prefix) for prefix in TRACKING_PREFIXES)
    ]
    query = urllib.parse.urlencode(sorted(kept))
    return urllib.parse.urlunsplit(("https", netloc, path, query, ""))


def title_tokens(title: str) -> frozenset[str]:
    """Reduce a headline to the significant tokens that identify the underlying event."""
    lowered = title.lower()
    # Drop a trailing outlet attribution, e.g. "... - Reuters" or "... | The Verge".
    lowered = re.split(r"\s[\|–—]\s|\s-\s(?=[a-z0-9 .']{2,30}$)", lowered)[0]
    tokens = {
        token
        for token in WORD_RE.findall(lowered)
        if token not in STOPWORDS and len(token) > 2
    }
    return frozenset(tokens)


def jaccard(left: frozenset[str], right: frozenset[str]) -> float:
    """Unweighted overlap between two token sets, 0.0 to 1.0."""
    if not left or not right:
        return 0.0
    union = len(left | right)
    return len(left & right) / union if union else 0.0


def inverse_document_frequency(token_sets: list[frozenset[str]]) -> dict[str, float]:
    """Score each token by how rare it is across the day's headlines.

    Rare tokens identify an event ("capsizes", "indonesia"); common ones do not
    ("news", "says", "scores"). Weighting by rarity is what lets the threshold sit low
    enough to merge differently-worded coverage of one event without merging two
    unrelated stories that happen to share filler words.

    Note the small-corpus property: with only a handful of documents every shared token
    looks common and similarity is compressed. A real run carries several hundred
    headlines, where the separation is wide. Tests must reflect that scale.
    """
    total = len(token_sets) or 1
    counts: dict[str, int] = {}
    for tokens in token_sets:
        for token in tokens:
            counts[token] = counts.get(token, 0) + 1
    return {token: math.log(total / count) + 1.0 for token, count in counts.items()}


def weighted_similarity(
    left: frozenset[str], right: frozenset[str], idf: dict[str, float]
) -> float:
    """IDF-weighted overlap coefficient between two headline token sets.

    Overlap (shared / smaller side) rather than Jaccard, because two outlets covering one
    event write headlines of very different lengths and Jaccard punishes that difference
    as though it were disagreement. Measured against hand-labelled duplicate pairs from a
    live harvest, true duplicates scored 0.34-0.50 and unrelated pairs almost all below
    0.45. At least two shared tokens are required, so a single coincidental proper noun
    ("Japan") cannot merge two unrelated stories.
    """
    shared_tokens = left & right
    if len(shared_tokens) < MIN_SHARED_TOKENS:
        return 0.0
    shared = sum(idf.get(token, 1.0) for token in shared_tokens)
    left_mass = sum(idf.get(token, 1.0) for token in left)
    right_mass = sum(idf.get(token, 1.0) for token in right)
    smaller = min(left_mass, right_mass)
    return shared / smaller if smaller else 0.0


def is_boilerplate(title: str, extra_pattern: Optional[re.Pattern[str]]) -> bool:
    """True if a title is a section page, standing link or regulatory filler."""
    if len(title) < 12 or BOILERPLATE_TITLE_RE.search(title):
        return True
    if len(title_tokens(title)) < 3:
        # "East Asia - Nikkei Asia", "Tennis Scores - AP": a section, not a story.
        return True
    return bool(extra_pattern and extra_pattern.search(title))


def build_items(source: dict[str, Any], entries: list[dict[str, str]]) -> list[Item]:
    """Turn raw feed entries into normalised items, discarding those without a URL."""
    raw_exclude = source.get("exclude_title")
    extra = re.compile(str(raw_exclude), re.I) if raw_exclude else None
    items: list[Item] = []
    for entry in entries:
        url = canonicalize_url(entry["url"])
        if not url or is_boilerplate(entry["title"], extra):
            continue
        published = parse_datetime(entry["published"])
        items.append(
            Item(
                source_id=source["id"],
                source_name=source["name"],
                tier=int(source["tier"]),
                domains=list(source["domains"]),
                weight=float(source.get("weight", 1.0)),
                headline_only=bool(source.get("headline_only", False)),
                no_cluster=bool(source.get("no_cluster", False)),
                title=entry["title"],
                url=url,
                summary=entry["summary"],
                published_at=(published or datetime.now(timezone.utc)).astimezone(timezone.utc).isoformat(),
            )
        )
    return items


def within_window(item: Item, cutoff: datetime, now: datetime) -> bool:
    """True if the item was published inside the window.

    Future timestamps are tolerated by up to two hours. Feeds routinely carry small clock
    skew, and arXiv stamps items at the start of the announcement day.
    """
    published = datetime.fromisoformat(item.published_at)
    return cutoff <= published <= now + timedelta(hours=2)


def cap_per_source(items: list[Item], registry_caps: dict[str, int], default_cap: int) -> list[Item]:
    """Keep the newest N items per source so one busy feed cannot swamp the set."""
    by_source: dict[str, list[Item]] = {}
    for item in items:
        by_source.setdefault(item.source_id, []).append(item)
    kept: list[Item] = []
    for source_id, group in by_source.items():
        group.sort(key=lambda i: i.published_at, reverse=True)
        kept.extend(group[: registry_caps.get(source_id, default_cap)])
    return kept


def cap_clusters(clusters: list[Cluster], limit: int = MAX_CLUSTERS) -> tuple[list[Cluster], int]:
    """Trim the tail so the analysis pass stays affordable.

    This is a volume cap, not an editorial judgement. Everything corroborated by more than
    one source, everything from a primary or high-quality source, and everything matching a
    previously covered thread is kept unconditionally. Only the remaining single-source,
    lower-tier tail is trimmed, newest first, and the number dropped is reported.
    """
    if len(clusters) <= limit:
        return clusters, 0
    kept = [c for c in clusters if c.source_count > 1 or c.best_tier <= 2 or c.possible_thread]
    tail = [c for c in clusters if c not in kept]
    tail.sort(key=lambda c: c.published_at, reverse=True)
    room = max(0, limit - len(kept))
    return kept + tail[:room], max(0, len(tail) - room)


def cluster_items(items: list[Item], threshold: float = CLUSTER_THRESHOLD) -> list[Cluster]:
    """Collapse the same event reported by many outlets into one cluster.

    Exact canonical-URL matches merge first. Remaining items join a cluster when their
    headline tokens overlap enough. Lower tiers are processed first so a primary or
    high-quality source becomes the cluster lead rather than an aggregator.
    """
    by_url: dict[str, list[Item]] = {}
    for item in items:
        by_url.setdefault(item.url, []).append(item)

    groups = sorted(by_url.values(), key=lambda g: min(i.sort_key() for i in g))
    idf = inverse_document_frequency([title_tokens(g[0].title) for g in groups])

    clusters: list[tuple[frozenset[str], list[Item]]] = []
    for group in groups:
        tokens = title_tokens(group[0].title)
        if group[0].no_cluster:
            clusters.append((tokens, list(group)))
            continue
        best_index, best_score = -1, threshold
        for index, (existing_tokens, existing_items) in enumerate(clusters):
            if existing_items[0].no_cluster:
                continue
            score = weighted_similarity(tokens, existing_tokens, idf)
            if score >= best_score:
                best_index, best_score = index, score
        if best_index >= 0:
            # Anchor on the lead item's tokens and never mutate them, so a cluster cannot
            # drift topic by topic through chained partial matches.
            clusters[best_index][1].extend(group)
        else:
            clusters.append((tokens, list(group)))

    built: list[Cluster] = []
    for index, (_, members) in enumerate(clusters, start=1):
        members.sort(key=lambda i: i.sort_key())
        lead = members[0]
        timestamps = sorted(m.published_at for m in members)
        domains: list[str] = []
        for member in members:
            for domain in member.domains:
                if domain not in domains:
                    domains.append(domain)
        seen_sources: dict[str, str] = {}
        for member in members:
            seen_sources.setdefault(member.source_id, member.source_name)
        built.append(
            Cluster(
                cluster_id=f"c{index:03d}",
                title=lead.title,
                url=lead.url,
                summary=lead.summary,
                published_at=timestamps[-1],
                earliest_at=timestamps[0],
                best_tier=min(m.tier for m in members),
                domains=domains,
                source_count=len(seen_sources),
                sources=list(seen_sources.values()),
                headline_only=all(m.headline_only for m in members),
                structured=lead.no_cluster,
                also=[m.title for m in members[1:4] if m.title != lead.title],
            )
        )
    built.sort(key=lambda c: (c.best_tier, -c.source_count, c.published_at))
    return built


# ---------------------------------------------------------------------------
# Prior coverage
# ---------------------------------------------------------------------------


def load_state(path: Path = STATE_FILE) -> dict[str, Any]:
    """Read the thread state written by previous digests."""
    if not path.exists():
        return {"threads": []}
    try:
        with path.open(encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, json.JSONDecodeError):
        return {"threads": []}


def containment(left: frozenset[str], right: frozenset[str]) -> float:
    """Share of the smaller token set that appears in the larger one."""
    if not left or not right:
        return 0.0
    return len(left & right) / min(len(left), len(right))


def tag_prior_coverage(clusters: list[Cluster], state: dict[str, Any]) -> None:
    """Flag clusters that look like continuations of a previously covered thread.

    This only raises the question. Whether the thread has actually moved is the delta
    test, and that is the skill's job, not the script's.
    """
    threads = [
        (
            thread["thread_id"],
            title_tokens(" ".join(thread.get("entities", [])) + " " + thread.get("last_claim", "")),
            title_tokens(" ".join(thread.get("entities", []))),
        )
        for thread in state.get("threads", [])
        if thread.get("status", "open") == "open"
    ]
    if not threads:
        return
    for cluster in clusters:
        tokens = title_tokens(cluster.title)
        best_id, best_score = None, THREAD_THRESHOLD
        for thread_id, thread_tokens, entity_tokens in threads:
            # A continuation must name one of the thread's entities. Without this a short
            # headline sharing only prose words ("the case against X") scores highly
            # against the claim text and is tagged as a continuation of an unrelated story.
            if not (tokens & entity_tokens):
                continue
            score = containment(tokens, thread_tokens)
            if score >= best_score:
                best_id, best_score = thread_id, score
        cluster.possible_thread = best_id


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------


def harvest_source(
    source: dict[str, Any], config: dict[str, Any], cutoff: datetime, now: datetime
) -> tuple[SourceResult, list[Item]]:
    """Fetch and normalise a single source. Never raises; failures become a status."""
    agent = config.get("gov_user_agent") if source.get("gov") else config.get("user_agent")
    timeout = int(config.get("timeout_seconds", 20))
    name = source["name"]

    try:
        code, body = fetch(source["url"], str(agent), timeout)
    except urllib.error.HTTPError as error:
        return SourceResult(source["id"], name, "failed", str(error.code), 0, 0, None, "http"), []
    except (urllib.error.URLError, TimeoutError, ConnectionError, OSError) as error:
        return SourceResult(source["id"], name, "failed", "ERR", 0, 0, None, type(error).__name__), []

    if source.get("fetch") == "page":
        entries = parse_page_links(body, source["url"], str(source.get("link_pattern", "")))
    else:
        entries = parse_feed(body)

    items = build_items(source, entries)
    latest = max((i.published_at for i in items), default=None)
    windowed = [i for i in items if within_window(i, cutoff, now)]

    if items:
        status = "ok"
    elif source.get("fetch") != "page" and body.lstrip()[:9].lower().startswith(b"<!doctype"):
        # A feed endpoint answering with HTML is a bot challenge or an interstitial, not an
        # empty feed. Worth distinguishing: one is rate limiting, the other is quiet news.
        status = "blocked"
    else:
        status = "empty"
    return SourceResult(source["id"], name, status, code, len(items), len(windowed), latest), windowed


def run_harvest(
    registry: dict[str, Any],
    window_hours: int,
    domains: Optional[list[str]],
    with_quotes: bool = True,
) -> dict[str, Any]:
    """Fetch every selected source and assemble the harvest payload."""
    config = registry["config"]
    sources = select_sources(registry, domains)
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(hours=window_hours)

    results: list[SourceResult] = []
    items: list[Item] = []
    workers = int(config.get("max_workers", 24))
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(harvest_source, s, config, cutoff, now) for s in sources]
        for future in concurrent.futures.as_completed(futures):
            result, source_items = future.result()
            results.append(result)
            items.extend(source_items)

    caps = {s["id"]: int(s.get("cap", config.get("default_cap", 20))) for s in sources}
    capped = cap_per_source(items, caps, int(config.get("default_cap", 20)))
    clusters = cluster_items(capped)
    tag_prior_coverage(clusters, load_state())
    clusters, dropped = cap_clusters(clusters)

    results.sort(key=lambda r: (r.status != "ok", r.name))
    degraded = [asdict(r) for r in results if r.status != "ok"]
    quotes = fetch_quotes(config) if with_quotes else []

    return {
        "generated_at": now.isoformat(),
        "window": {
            "hours": window_hours,
            "from": cutoff.isoformat(),
            "to": now.isoformat(),
            "timezone": config.get("timezone", "America/New_York"),
        },
        "counts": {
            "sources_attempted": len(sources),
            "sources_ok": sum(1 for r in results if r.status == "ok"),
            "sources_degraded": len(degraded),
            "items_in_window": len(items),
            "items_after_cap": len(capped),
            "clusters": len(clusters),
            "clusters_trimmed": dropped,
        },
        "degraded_sources": degraded,
        "quotes": quotes,
        "clusters": [asdict(c) for c in clusters],
    }


# ---------------------------------------------------------------------------
# Market quotes
# ---------------------------------------------------------------------------

# Yahoo's chart endpoint is keyless and returns last price plus session change.
# Stooq's CSV endpoint was the first choice and now sits behind a JS challenge.
QUOTE_SYMBOLS: list[tuple[str, str, str]] = [
    # (yahoo symbol, display label, group: "main" or "secondary")
    ("^GSPC", "S&P 500", "main"),
    ("^IXIC", "Nasdaq", "main"),
    ("VOO", "VOO", "main"),
    ("VGT", "VGT", "main"),
    ("BZ=F", "Brent", "secondary"),
    ("CL=F", "WTI", "secondary"),
    ("GC=F", "Gold", "secondary"),
    ("^TNX", "10Y Yield", "secondary"),
    ("^VIX", "VIX", "secondary"),
    ("DX-Y.NYB", "Dollar Index", "secondary"),
    ("BTC-USD", "Bitcoin", "secondary"),
]

QUOTE_URL = "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?range=1d&interval=1d"

# Yahoo 429s a request that claims a full Chrome user agent without the rest of a browser
# fingerprint, so the quote strip does not reuse the registry's feed-fetching identity.
QUOTE_USER_AGENT = "daily-digest/1.0"


QUOTE_ATTEMPTS = 3
QUOTE_BACKOFF = 1.5


def fetch_quote(symbol: str, label: str, group: str, user_agent: str, timeout: int) -> dict[str, Any]:
    """Fetch one quote. Never raises: a failure is reported, never guessed at."""
    url = QUOTE_URL.format(symbol=urllib.parse.quote(symbol, safe=""))
    record: dict[str, Any] = {"symbol": symbol, "label": label, "group": group}
    last_error = "no attempt"
    for attempt in range(QUOTE_ATTEMPTS):
        try:
            request = urllib.request.Request(
                url, headers={"User-Agent": user_agent, "Accept": "application/json"}
            )
            with urllib.request.urlopen(request, timeout=timeout) as response:
                body = response.read()
            meta = json.loads(body.decode("utf-8"))["chart"]["result"][0]["meta"]
            price = meta.get("regularMarketPrice")
            if price is None:
                raise ValueError("no regularMarketPrice")
            record["price"] = round(float(price), 2)
            change = meta.get("regularMarketChangePercent")
            record["change_pct"] = round(float(change), 2) if change is not None else None
            previous = meta.get("previousClose") or meta.get("chartPreviousClose")
            record["previous_close"] = round(float(previous), 2) if previous is not None else None
            record["as_of"] = meta.get("regularMarketTime")
            record["status"] = "ok"
            return record
        except (urllib.error.URLError, OSError, ValueError, KeyError, IndexError, TypeError) as error:
            last_error = f"{type(error).__name__}: {error}"[:120]
            if attempt < QUOTE_ATTEMPTS - 1:
                time.sleep(QUOTE_BACKOFF * (attempt + 1))
    record["status"] = "failed"
    record["error"] = last_error
    return record


def fetch_quotes(config: dict[str, Any]) -> list[dict[str, Any]]:
    """Fetch the Market Pulse strip. Yahoo 429s on a parallel burst, so keep it narrow."""
    timeout = int(config.get("timeout", 12))
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        futures = [
            pool.submit(fetch_quote, symbol, label, group, QUOTE_USER_AGENT, timeout)
            for symbol, label, group in QUOTE_SYMBOLS
        ]
        records = [f.result() for f in futures]
    order = {symbol: index for index, (symbol, _, _) in enumerate(QUOTE_SYMBOLS)}
    records.sort(key=lambda r: order[r["symbol"]])
    return records


# ---------------------------------------------------------------------------
# Shortlist
# ---------------------------------------------------------------------------

# A cheap prominence prior so the model reads roughly 70 candidates instead of 300.
# It ranks how visible and well-corroborated a story is, which is not the same as how
# much it matters. Editorial selection stays with the skill.
#
# Corroboration dominates and tier is a light tiebreak. Tier measures how much a source
# can establish, not how prominent the story is: an individual 8-K from a micro-cap is
# tier 1 and almost never news, while a wire story carried by four outlets is tier 2 and
# usually is. Scoring on tier alone buries every real story under routine filings.
TIER_SCORE = {1: 1.2, 2: 1.0, 3: 0.7, 4: 0.3, 5: 0.0}
DOMAIN_ORDER = ["ai", "business", "markets", "econ", "geo", "culture", "science"]
SHORTLIST_SUMMARY_CHARS = 110

# Above this many solo clusters in one window, a source is a firehose (SEC filings, arXiv,
# USGS) rather than a news source, and its uncorroborated items get damped.
FIREHOSE_FLOOR = 3


def solo_source_volume(clusters: list[dict[str, Any]]) -> dict[str, int]:
    """Count how many single-source clusters each source produced in this window."""
    volume: dict[str, int] = {}
    for cluster in clusters:
        sources = cluster.get("sources", [])
        if len(sources) == 1:
            volume[sources[0]] = volume.get(sources[0], 0) + 1
    return volume


def prominence(
    cluster: dict[str, Any],
    window_from: datetime,
    window_to: datetime,
    solo_volume: dict[str, int],
) -> float:
    """Rank clusters by corroboration, recency and tier. Not a judgement of importance."""
    sources = cluster.get("sources", [])
    score = TIER_SCORE.get(int(cluster.get("best_tier", 5)), 0.0)
    score += min(2.0 * math.log2(1 + int(cluster.get("source_count", 1))), 5.0)
    try:
        published = datetime.fromisoformat(cluster["published_at"])
        span = max((window_to - window_from).total_seconds(), 1.0)
        elapsed = (published - window_from).total_seconds()
        score += 1.5 * max(0.0, min(1.0, elapsed / span))
    except (KeyError, ValueError, TypeError):
        pass
    if len(sources) == 1:
        solo = solo_volume.get(sources[0], 0)
        if solo > FIREHOSE_FLOOR:
            score -= min(0.7 * math.log2(solo / FIREHOSE_FLOOR), 2.2)
    if cluster.get("structured"):
        score += 0.4
    if cluster.get("headline_only"):
        score -= 1.2
    if cluster.get("possible_thread"):
        score += 0.3  # surfaced so the delta test can be applied, not because it wins
    return score


def build_shortlist(
    payload: dict[str, Any], limit: int = 72, per_domain: int = 10
) -> list[dict[str, Any]]:
    """Take the top clusters overall, with a guaranteed floor for every domain.

    Without the per-domain floor a loud day in one domain buries every quiet one, and the
    skill never gets the chance to decide that a domain is genuinely empty.
    """
    window_from = datetime.fromisoformat(payload["window"]["from"])
    window_to = datetime.fromisoformat(payload["window"]["to"])
    solo_volume = solo_source_volume(payload["clusters"])
    ranked = sorted(
        payload["clusters"],
        key=lambda c: prominence(c, window_from, window_to, solo_volume),
        reverse=True,
    )

    chosen: dict[str, dict[str, Any]] = {}
    for domain in DOMAIN_ORDER:
        taken = 0
        for cluster in ranked:
            if taken >= per_domain:
                break
            if domain in cluster.get("domains", []):
                chosen.setdefault(cluster["cluster_id"], cluster)
                taken += 1
    for cluster in ranked:
        if len(chosen) >= limit:
            break
        chosen.setdefault(cluster["cluster_id"], cluster)

    return [c for c in ranked if c["cluster_id"] in chosen][:limit]


def hours_ago(published_at: str, reference: datetime) -> str:
    try:
        delta = reference - datetime.fromisoformat(published_at)
    except (ValueError, TypeError):
        return "  ?"
    hours = int(delta.total_seconds() // 3600)
    return f"{max(hours, 0):3d}h"


def print_shortlist(payload: dict[str, Any], shortlist: list[dict[str, Any]], out_path: Path) -> None:
    """Print the compact candidate list. No URLs: --expand fetches those for the few selected."""
    counts = payload["counts"]
    window = payload["window"]
    reference = datetime.fromisoformat(window["to"])

    print(f"WINDOW  {window['from'][:16]} to {window['to'][:16]} UTC ({window['hours']}h)")
    print(
        f"HARVEST {counts['items_in_window']} items -> {counts['clusters']} clusters -> "
        f"{len(shortlist)} shortlisted | sources {counts['sources_ok']}/{counts['sources_attempted']} ok"
    )
    degraded = payload.get("degraded_sources", [])
    if degraded:
        names = ", ".join(f"{d['name']} ({d['status']})" for d in degraded[:8])
        print(f"DEGRADED {len(degraded)}: {names}")

    quotes = payload.get("quotes") or []
    if quotes:
        print("\nQUOTES")
        for quote in quotes:
            if quote.get("status") != "ok":
                print(f"  {quote['label']:<13} unavailable ({quote.get('error', 'error')})")
                continue
            change = quote.get("change_pct")
            move = f"{change:+.2f}%" if change is not None else "n/a"
            print(f"  {quote['label']:<13} {quote['price']:>12,.2f}  {move:>8}  [{quote['group']}]")

    tally: dict[str, int] = {d: 0 for d in DOMAIN_ORDER}
    for cluster in shortlist:
        for domain in cluster.get("domains", []):
            if domain in tally:
                tally[domain] += 1
    spread = "  ".join(f"{d}:{n}" for d, n in tally.items())
    print(f"\nTAGS    {spread}")
    print("        Source-level tags, not story routing. A cluster carries every domain its")
    print("        outlet covers. Route each story yourself against the tab definitions.")

    print(f"\nFULL HARVEST {out_path}")
    print("EXPAND       python scripts/harvest_feeds.py --expand c012,c034,c101\n")
    print("Ranked by prominence: corroboration, recency, tier. Not by importance.\n")
    print("ID    TIER SRC  AGE  TAGS                 TITLE :: SUMMARY")
    print("-" * 100)
    for cluster in shortlist:
        print(format_shortlist_row(cluster, reference))


def format_shortlist_row(cluster: dict[str, Any], reference: datetime) -> str:
    title = html.unescape(cluster.get("title", "")).strip()
    summary = html.unescape(strip_html(cluster.get("summary", ""))).strip()
    summary = re.sub(r"\s+", " ", summary)
    # Google News summaries repeat the headline and append the outlet. Drop the echo.
    if summary[:40].lower() == title[:40].lower():
        summary = ""
    if len(summary) > SHORTLIST_SUMMARY_CHARS:
        summary = summary[:SHORTLIST_SUMMARY_CHARS].rsplit(" ", 1)[0] + "..."
    flags = ""
    if cluster.get("headline_only"):
        flags += " [hdln]"
    if cluster.get("possible_thread"):
        flags += f" [thread:{cluster['possible_thread']}]"
    domains = ",".join(cluster.get("domains", []))
    body = title
    if summary:
        body += f" :: {summary}"
    return (
        f"{cluster['cluster_id']:<5} t{cluster.get('best_tier', '?')}   "
        f"x{cluster.get('source_count', 1):<3} {hours_ago(cluster.get('published_at', ''), reference)}  "
        f"{domains:<20} {body}{flags}"
    )


def run_expand(ids: str, path: Optional[str]) -> int:
    """Print full records for the handful of clusters the skill actually selected."""
    if path:
        harvest_path = Path(path)
    else:
        harvest_path = HARVEST_DIR / f"{datetime.now().date().isoformat()}.json"
    if not harvest_path.exists():
        print(f"ERROR: no harvest at {harvest_path}. Run the harvest first.", file=sys.stderr)
        return 2

    with harvest_path.open(encoding="utf-8") as handle:
        payload = json.load(handle)

    wanted = [i.strip() for i in ids.split(",") if i.strip()]
    index = {c["cluster_id"]: c for c in payload["clusters"]}
    found = [index[i] for i in wanted if i in index]
    missing = [i for i in wanted if i not in index]

    json.dump({"clusters": found, "missing": missing}, sys.stdout, indent=2, ensure_ascii=False)
    print()
    if missing:
        print(f"WARNING: not in harvest: {', '.join(missing)}", file=sys.stderr)
    return 0


def run_health(registry: dict[str, Any]) -> int:
    """Re-probe every source and print a status table. Returns a shell exit code."""
    config = registry["config"]
    sources = registry["sources"]
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=3650)

    rows: list[SourceResult] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=int(config.get("max_workers", 24))) as pool:
        futures = [pool.submit(harvest_source, s, config, cutoff, now) for s in sources]
        for future in concurrent.futures.as_completed(futures):
            rows.append(future.result()[0])

    rows.sort(key=lambda r: (r.status == "ok", r.name))
    print(f"{'SOURCE':<34} {'STATUS':<8} {'CODE':<5} {'ITEMS':<6} LATEST")
    print("-" * 78)
    stale: list[str] = []
    for row in rows:
        age = ""
        if row.latest:
            latest = datetime.fromisoformat(row.latest)
            days = (now - latest).days
            age = f"{row.latest[:10]}  ({days}d)"
            if days > 45:
                stale.append(f"{row.name}: {days} days")
        print(f"{row.name:<34} {row.status:<8} {row.http_code:<5} {row.raw_items:<6} {age}")

    healthy = sum(1 for r in rows if r.status == "ok")
    print("-" * 78)
    print(f"{healthy}/{len(rows)} healthy")
    if stale:
        print("\nStale (no item in 45 days), review or retire:")
        for entry in stale:
            print(f"  {entry}")
    return 0 if healthy >= len(rows) * 0.8 else 1


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Harvest sources for the Daily Intelligence Digest.")
    parser.add_argument("--window", type=int, default=None, help="Window in hours (default: registry config)")
    parser.add_argument("--domains", type=str, default=None, help="Comma-separated domains to restrict to")
    parser.add_argument("--health", action="store_true", help="Probe the registry and print status")
    parser.add_argument("--out", type=str, default=None, help="Output path, or - for stdout")
    parser.add_argument(
        "--shortlist",
        nargs="?",
        type=int,
        const=72,
        default=None,
        help="Harvest, then print a compact ranked candidate list instead of the full JSON",
    )
    parser.add_argument(
        "--per-domain", type=int, default=10, help="Shortlist floor per domain (default 10)"
    )
    parser.add_argument(
        "--expand",
        type=str,
        default=None,
        help="Comma-separated cluster ids: print their full records from today's harvest",
    )
    parser.add_argument("--no-quotes", action="store_true", help="Skip the Market Pulse quote fetch")
    args = parser.parse_args(argv)

    if args.expand:
        return run_expand(args.expand, args.out)

    try:
        registry = load_registry()
    except (FileNotFoundError, ValueError, yaml.YAMLError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2

    if args.health:
        return run_health(registry)

    window = args.window or int(registry["config"].get("window_hours", 24))
    domains = args.domains.split(",") if args.domains else None
    payload = run_harvest(registry, window, domains, with_quotes=not args.no_quotes)

    if args.out == "-":
        json.dump(payload, sys.stdout, indent=2, ensure_ascii=False)
        return 0

    HARVEST_DIR.mkdir(parents=True, exist_ok=True)
    out_path = Path(args.out) if args.out else HARVEST_DIR / f"{datetime.now().date().isoformat()}.json"
    with out_path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)

    if args.shortlist:
        shortlist = build_shortlist(payload, limit=args.shortlist, per_domain=args.per_domain)
        print_shortlist(payload, shortlist, out_path)
        return 0

    counts = payload["counts"]
    print(
        f"{out_path}\n"
        f"  sources   {counts['sources_ok']}/{counts['sources_attempted']} ok, "
        f"{counts['sources_degraded']} degraded\n"
        f"  items     {counts['items_in_window']} in window -> {counts['items_after_cap']} after cap\n"
        f"  clusters  {counts['clusters']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
