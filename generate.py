#!/usr/bin/env python3
"""
Build the AI Tech Radar site.

Reads every markdown entry in ./tech-radar (recursively), parses its
frontmatter, and generates a static site in ./docs:

    docs/index.html            interactive radar + entry listings
    docs/entries/<slug>.html   one page per entry
    docs/style.css             shared styles

No third-party dependencies required (Python 3.8+).

Usage:
    python3 generate.py
"""

from __future__ import annotations

import html
import math
import re
import sys
from datetime import datetime
from pathlib import Path

# --------------------------------------------------------------------------
# Configuration
# --------------------------------------------------------------------------

ROOT = Path(__file__).resolve().parent
SRC_DIR = ROOT / "tech-radar"
OUT_DIR = ROOT / "docs"

# Quadrants in display order. Each maps to one corner of the radar.
QUADRANTS = ["Trends", "Techniques", "Tools", "Platforms"]

# Rings from innermost (most adopted) to outermost.
RINGS = ["Adopt", "Trial", "Assess", "Watch"]

RING_COLORS = {
    "Adopt": "#4c9f70",
    "Trial": "#2f7ec2",
    "Assess": "#d99a2b",
    "Watch": "#9a9a9a",
}

QUADRANT_COLORS = {
    "Trends": "#6b4ea0",
    "Techniques": "#2f7ec2",
    "Tools": "#c2542f",
    "Platforms": "#2f9c8f",
}

STATUS_LABELS = {
    "new": "New",
    "moved-in": "Moved in",
    "moved-out": "Moved out",
    "unchanged": "No change",
}

# Radar geometry
SIZE = 720           # svg width/height
CENTER = SIZE / 2
MAX_R = CENTER - 20  # outer radius


# --------------------------------------------------------------------------
# Frontmatter + markdown parsing (minimal, dependency-free)
# --------------------------------------------------------------------------

def parse_frontmatter(text: str):
    """Return (meta_dict, body_str). Supports simple scalars and [a, b] lists."""
    meta = {}
    body = text
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) >= 3:
            raw, body = parts[1], parts[2]
            for line in raw.splitlines():
                line = line.strip()
                if not line or line.startswith("#") or ":" not in line:
                    continue
                key, _, val = line.partition(":")
                key = key.strip()
                val = val.strip()
                # strip inline comments (outside of quotes / brackets)
                if val and not val.startswith("[") and " #" in val:
                    val = val.split(" #", 1)[0].strip()
                if val.startswith("[") and val.endswith("]"):
                    items = [v.strip().strip("'\"") for v in val[1:-1].split(",")]
                    val = [v for v in items if v]
                else:
                    val = val.strip("'\"")
                meta[key] = val
    return meta, body.strip()


def slugify(name: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return s or "entry"


def md_inline(text: str) -> str:
    """Inline markdown: escape, then apply links, bold, italic, code."""
    text = html.escape(text)
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<em>\1</em>", text)
    return text


def md_to_html(text: str) -> str:
    """Very small markdown renderer: headings, lists, paragraphs, inline."""
    lines = text.splitlines()
    out = []
    i = 0
    in_list = False

    def close_list():
        nonlocal in_list
        if in_list:
            out.append("</ul>")
            in_list = False

    while i < len(lines):
        line = lines[i].rstrip()
        if not line.strip():
            close_list()
            i += 1
            continue
        m = re.match(r"^(#{1,6})\s+(.*)$", line)
        if m:
            close_list()
            level = len(m.group(1))
            out.append(f"<h{level}>{md_inline(m.group(2))}</h{level}>")
            i += 1
            continue
        if re.match(r"^[-*]\s+", line):
            if not in_list:
                out.append("<ul>")
                in_list = True
            item = re.sub(r"^[-*]\s+", "", line)
            out.append(f"<li>{md_inline(item)}</li>")
            i += 1
            continue
        # paragraph: gather consecutive non-blank, non-special lines
        close_list()
        para = [line]
        i += 1
        while i < len(lines) and lines[i].strip() and not re.match(
            r"^(#{1,6}\s|[-*]\s)", lines[i]
        ):
            para.append(lines[i].rstrip())
            i += 1
        out.append("<p>" + md_inline(" ".join(para)) + "</p>")
    close_list()
    return "\n".join(out)


# --------------------------------------------------------------------------
# Load entries
# --------------------------------------------------------------------------

def load_entries():
    entries = []
    if not SRC_DIR.exists():
        sys.exit(f"Source directory not found: {SRC_DIR}")
    for path in sorted(SRC_DIR.rglob("*.md")):
        if path.name.startswith("_") or path.name.lower() == "readme.md":
            continue
        meta, body = parse_frontmatter(path.read_text(encoding="utf-8"))
        name = meta.get("name") or path.stem.replace("-", " ").title()
        quadrant = meta.get("quadrant", "").strip()
        ring = meta.get("ring", "").strip()
        problems = []
        if quadrant not in QUADRANTS:
            problems.append(f"quadrant '{quadrant}'")
        if ring not in RINGS:
            problems.append(f"ring '{ring}'")
        if problems:
            print(f"  ! skipping {path.relative_to(ROOT)}: invalid {', '.join(problems)}")
            continue
        tags = meta.get("tags", [])
        if isinstance(tags, str):
            tags = [tags] if tags else []
        entries.append({
            "name": name,
            "quadrant": quadrant,
            "ring": ring,
            "status": meta.get("status", "unchanged"),
            "tags": tags,
            "date": meta.get("date", ""),
            "slug": slugify(name),
            "body_html": md_to_html(body),
            "source": str(path.relative_to(ROOT)),
        })
    return entries


# --------------------------------------------------------------------------
# Radar geometry
# --------------------------------------------------------------------------

def ring_bounds():
    """Return list of (inner, outer) radius for each ring."""
    step = MAX_R / len(RINGS)
    return [(i * step, (i + 1) * step) for i in range(len(RINGS))]


def quadrant_angles(q_index: int):
    """Return (start_deg, end_deg) for a quadrant, measured math-style (ccw, +x=0)."""
    start = q_index * 90
    return start, start + 90


def place_blips(entries):
    """Assign x, y and a display number to each entry. Mutates entries."""
    bounds = ring_bounds()
    # group by (quadrant, ring)
    cells = {}
    for e in entries:
        cells.setdefault((e["quadrant"], e["ring"]), []).append(e)

    number = 0
    for q_index, quadrant in enumerate(QUADRANTS):
        a0, a1 = quadrant_angles(q_index)
        for r_index, ring in enumerate(RINGS):
            group = cells.get((quadrant, ring), [])
            inner, outer = bounds[r_index]
            n = len(group)
            for j, e in enumerate(group):
                number += 1
                e["number"] = number
                # spread angularly across the wedge (with margin)
                frac = (j + 1) / (n + 1)
                ang = math.radians(a0 + 8 + frac * (90 - 16))
                # alternate radius within the band to reduce overlap
                rad = inner + (outer - inner) * (0.30 + 0.5 * ((j % 3) / 2.0))
                e["x"] = CENTER + rad * math.cos(ang)
                e["y"] = CENTER - rad * math.sin(ang)
    return entries


# --------------------------------------------------------------------------
# SVG radar
# --------------------------------------------------------------------------

def build_svg(entries):
    bounds = ring_bounds()
    parts = [f'<svg viewBox="0 0 {SIZE} {SIZE}" class="radar" xmlns="http://www.w3.org/2000/svg">']

    # ring circles (outer to inner so inner draws on top)
    for r_index in range(len(RINGS) - 1, -1, -1):
        _, outer = bounds[r_index]
        shade = "#ffffff" if r_index % 2 == 0 else "#f4f6f8"
        parts.append(
            f'<circle cx="{CENTER}" cy="{CENTER}" r="{outer:.1f}" '
            f'fill="{shade}" stroke="#dfe3e8" stroke-width="1"/>'
        )

    # quadrant divider lines
    parts.append(
        f'<line x1="{CENTER}" y1="20" x2="{CENTER}" y2="{SIZE - 20}" stroke="#dfe3e8"/>'
    )
    parts.append(
        f'<line x1="20" y1="{CENTER}" x2="{SIZE - 20}" y2="{CENTER}" stroke="#dfe3e8"/>'
    )

    # ring labels along the top vertical axis
    for r_index, ring in enumerate(RINGS):
        inner, outer = bounds[r_index]
        y = CENTER - (inner + outer) / 2
        parts.append(
            f'<text x="{CENTER + 4}" y="{y:.1f}" class="ring-label">{ring}</text>'
        )

    # quadrant labels (corners)
    corners = {
        0: (SIZE - 28, 34, "end"),        # top-right   -> Trends
        1: (28, 34, "start"),             # top-left    -> Techniques
        2: (28, SIZE - 20, "start"),      # bottom-left -> Tools
        3: (SIZE - 28, SIZE - 20, "end"), # bottom-right-> Platforms
    }
    for q_index, quadrant in enumerate(QUADRANTS):
        x, y, anchor = corners[q_index]
        color = QUADRANT_COLORS[quadrant]
        parts.append(
            f'<text x="{x}" y="{y}" class="quad-label" '
            f'text-anchor="{anchor}" fill="{color}">{html.escape(quadrant)}</text>'
        )

    # blips
    for e in entries:
        color = RING_COLORS[e["ring"]]
        parts.append(
            f'<a href="entries/{e["slug"]}.html" class="blip" '
            f'data-slug="{e["slug"]}">'
            f'<circle cx="{e["x"]:.1f}" cy="{e["y"]:.1f}" r="11" fill="{color}"/>'
            f'<text x="{e["x"]:.1f}" y="{e["y"] + 4:.1f}" '
            f'text-anchor="middle" class="blip-num">{e["number"]}</text>'
            f'<title>{html.escape(e["name"])} — {e["ring"]}</title>'
            f'</a>'
        )

    parts.append("</svg>")
    return "\n".join(parts)


# --------------------------------------------------------------------------
# HTML pages
# --------------------------------------------------------------------------

PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<link rel="stylesheet" href="{css}">
</head>
<body>
<header class="site-header">
  <h1><a href="{home}">AI Tech Radar</a></h1>
  <p class="subtitle">Trends, techniques, tools &amp; platforms · built {built}</p>
</header>
<main>
{content}
</main>
<footer class="site-footer">Generated by generate.py · {count} entries</footer>
{script}
</body>
</html>
"""


def legend_html(entries):
    """Grouped listing by quadrant then ring."""
    out = ['<section class="legend">']
    for quadrant in QUADRANTS:
        q_entries = [e for e in entries if e["quadrant"] == quadrant]
        color = QUADRANT_COLORS[quadrant]
        out.append(f'<div class="quad-block">')
        out.append(f'<h2 style="color:{color}">{html.escape(quadrant)}'
                    f' <span class="q-count">{len(q_entries)}</span></h2>')
        for ring in RINGS:
            r_entries = [e for e in q_entries if e["ring"] == ring]
            if not r_entries:
                continue
            out.append(f'<h3 class="ring-heading">'
                       f'<span class="ring-dot" style="background:{RING_COLORS[ring]}"></span>'
                       f'{ring}</h3>')
            out.append("<ul class='entry-list'>")
            for e in r_entries:
                status = STATUS_LABELS.get(e["status"], "")
                badge = (f'<span class="status status-{e["status"]}">{status}</span>'
                         if status else "")
                out.append(
                    f'<li data-slug="{e["slug"]}">'
                    f'<span class="num">{e["number"]}</span>'
                    f'<a href="entries/{e["slug"]}.html">{html.escape(e["name"])}</a>'
                    f'{badge}</li>'
                )
            out.append("</ul>")
        out.append("</div>")
    out.append("</section>")
    return "\n".join(out)


INDEX_SCRIPT = """<script>
(function () {
  function setActive(slug, on) {
    document.querySelectorAll('[data-slug="' + slug + '"]').forEach(function (el) {
      el.classList.toggle('hl', on);
    });
  }
  document.querySelectorAll('[data-slug]').forEach(function (el) {
    var slug = el.getAttribute('data-slug');
    el.addEventListener('mouseenter', function () { setActive(slug, true); });
    el.addEventListener('mouseleave', function () { setActive(slug, false); });
  });
})();
</script>"""


def build_index(entries):
    content = ('<section class="radar-wrap">'
               + build_svg(entries)
               + "</section>\n"
               + legend_html(entries))
    return PAGE.format(
        title="AI Tech Radar",
        css="style.css",
        home="index.html",
        built=datetime.now().strftime("%Y-%m-%d"),
        content=content,
        count=len(entries),
        script=INDEX_SCRIPT,
    )


def build_entry_page(e):
    tags = "".join(
        f'<span class="tag">{html.escape(t)}</span>' for t in e["tags"]
    )
    meta = (
        f'<p class="entry-meta">'
        f'<span class="pill" style="background:{QUADRANT_COLORS[e["quadrant"]]}">'
        f'{html.escape(e["quadrant"])}</span> '
        f'<span class="pill" style="background:{RING_COLORS[e["ring"]]}">'
        f'{html.escape(e["ring"])}</span>'
        + (f' <span class="pill status-pill">{STATUS_LABELS.get(e["status"], "")}</span>'
           if STATUS_LABELS.get(e["status"]) else "")
        + (f' <span class="reviewed">Reviewed {html.escape(e["date"])}</span>'
           if e["date"] else "")
        + "</p>"
    )
    content = (
        f'<article class="entry">'
        f'<p class="crumb"><a href="../index.html">&larr; Radar</a></p>'
        f'<h1>{html.escape(e["name"])}</h1>'
        f'{meta}'
        f'{e["body_html"]}'
        + (f'<p class="tags">{tags}</p>' if tags else "")
        + "</article>"
    )
    return PAGE.format(
        title=f'{e["name"]} · AI Tech Radar',
        css="../style.css",
        home="../index.html",
        built=datetime.now().strftime("%Y-%m-%d"),
        content=content,
        count="",
        script="",
    )


CSS = """
:root { color-scheme: light; }
* { box-sizing: border-box; }
body {
  margin: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI",
  Roboto, Helvetica, Arial, sans-serif; color: #1f2933; background: #fbfcfd;
  line-height: 1.55;
}
a { color: #2f7ec2; text-decoration: none; }
a:hover { text-decoration: underline; }
.site-header {
  padding: 28px 24px 16px; border-bottom: 1px solid #e4e8ec; background: #fff;
}
.site-header h1 { margin: 0; font-size: 26px; letter-spacing: -0.01em; }
.site-header h1 a { color: #1f2933; }
.subtitle { margin: 4px 0 0; color: #6b7684; font-size: 14px; }
main { max-width: 1120px; margin: 0 auto; padding: 24px;
  display: grid; grid-template-columns: minmax(0, 1fr) 380px; gap: 32px; }
.radar-wrap { min-width: 0; }
.radar { width: 100%; height: auto; }
.ring-label { font-size: 12px; fill: #9aa5b1; font-weight: 600; }
.quad-label { font-size: 17px; font-weight: 700; letter-spacing: -0.01em; }
.blip { cursor: pointer; }
.blip circle { transition: r 0.1s ease; }
.blip.hl circle { stroke: #1f2933; stroke-width: 3; }
.blip-num { fill: #fff; font-size: 11px; font-weight: 700; pointer-events: none; }
.legend { min-width: 0; }
.quad-block { margin-bottom: 22px; }
.quad-block h2 { font-size: 16px; margin: 0 0 6px; border-bottom: 2px solid #eef1f4;
  padding-bottom: 4px; }
.q-count { color: #9aa5b1; font-size: 13px; font-weight: 500; }
.ring-heading { font-size: 13px; text-transform: uppercase; letter-spacing: 0.04em;
  color: #52606d; margin: 12px 0 4px; display: flex; align-items: center; gap: 6px; }
.ring-dot { width: 10px; height: 10px; border-radius: 50%; display: inline-block; }
.entry-list { list-style: none; margin: 0; padding: 0; }
.entry-list li { display: flex; align-items: center; gap: 8px; padding: 3px 4px;
  border-radius: 6px; }
.entry-list li.hl { background: #eef4fb; }
.num { font-size: 12px; color: #9aa5b1; width: 22px; text-align: right; flex: none; }
.status { font-size: 11px; padding: 1px 7px; border-radius: 10px; margin-left: auto;
  background: #eef1f4; color: #52606d; }
.status-new { background: #e4f3ea; color: #2f7d4f; }
.status-moved-in { background: #e5eefb; color: #2f6bc2; }
.status-moved-out { background: #fdecec; color: #c23f3f; }
.entry { grid-column: 1 / -1; max-width: 720px; }
.crumb { font-size: 14px; margin: 0 0 8px; }
.entry h1 { font-size: 28px; margin: 0 0 10px; letter-spacing: -0.01em; }
.entry h2 { font-size: 18px; margin: 22px 0 6px; }
.entry-meta { margin: 0 0 18px; display: flex; align-items: center; gap: 8px;
  flex-wrap: wrap; }
.pill { color: #fff; font-size: 12px; font-weight: 600; padding: 3px 10px;
  border-radius: 12px; }
.status-pill { background: #52606d; }
.reviewed { color: #9aa5b1; font-size: 13px; }
.entry code, .entry-list code { background: #eef1f4; padding: 1px 5px;
  border-radius: 4px; font-size: 0.9em; }
.tags { margin-top: 22px; }
.tag { display: inline-block; background: #eef1f4; color: #52606d; font-size: 12px;
  padding: 2px 9px; border-radius: 10px; margin: 0 6px 6px 0; }
.site-footer { text-align: center; color: #9aa5b1; font-size: 13px;
  padding: 24px; border-top: 1px solid #e4e8ec; margin-top: 24px; }
@media (max-width: 860px) {
  main { grid-template-columns: 1fr; }
}
"""


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------

def main():
    print(f"Reading entries from {SRC_DIR.relative_to(ROOT)}/ ...")
    entries = load_entries()
    if not entries:
        sys.exit("No valid entries found. Add markdown files under tech-radar/.")
    place_blips(entries)
    print(f"  {len(entries)} entries loaded.")

    (OUT_DIR / "entries").mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "style.css").write_text(CSS, encoding="utf-8")
    (OUT_DIR / "index.html").write_text(build_index(entries), encoding="utf-8")
    for e in entries:
        (OUT_DIR / "entries" / f'{e["slug"]}.html').write_text(
            build_entry_page(e), encoding="utf-8"
        )

    print(f"Wrote site to {OUT_DIR.relative_to(ROOT)}/ (open docs/index.html).")


if __name__ == "__main__":
    main()
