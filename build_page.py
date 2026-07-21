#!/usr/bin/env python3
"""Build index.html from papers.json.

Re-runnable: fetch_papers.py refreshes the data, this rebuilds the page.
"""

import html
import json
import re
from datetime import date

NAME = "Georgia Tsambos"
TAGLINE = "Population geneticist, Harris lab, University of Washington"
ORCID = "0000-0001-7001-2275"

# OpenAlex reports "Open MIND" for records it hasn't placed properly.
VENUE_OVERRIDES = {
    "https://doi.org/10.48550/arxiv.2602.09649": "arXiv (preprint)",
}

SOFTWARE = [
    ("tskit", "The tree sequence toolkit", "https://github.com/tskit-dev/tskit"),
    ("msprime", "Coalescent simulator for population genetics",
     "https://github.com/tskit-dev/msprime"),
    ("stdpopsim", "Standard library of population genetic models",
     "https://github.com/popsim-consortium/stdpopsim"),
    ("tspop", "Population ancestry from tree sequences",
     "https://github.com/gtsambos/tspop"),
    ("link-ancestors", "Fast local-ancestry simulation",
     "https://github.com/tskit-dev/tskit"),
]

# --- palette (reference instance; see dataviz references/palette.md) ----------
LIGHT = {
    "surface": "#fcfcfb", "plane": "#f9f9f7", "ink": "#0b0b0b",
    "secondary": "#52514e", "muted": "#898781", "grid": "#e1e0d9",
    "axis": "#c3c2b7", "accent": "#eb6834",
}
DARK = {
    "surface": "#1a1a19", "plane": "#0d0d0d", "ink": "#ffffff",
    "secondary": "#c3c2b7", "muted": "#898781", "grid": "#2c2c2a",
    "axis": "#383835", "accent": "#d95926",
}


def clean(s):
    """Strip stray markup OpenAlex leaves in titles, then escape."""
    return html.escape(re.sub(r"<[^>]+>", "", s or "").strip())


def cumulative(papers):
    per = {}
    for p in papers:
        for y, c in p["counts_by_year"].items():
            per[int(y)] = per.get(int(y), 0) + c
    years = range(min(per), max(per) + 1)
    out, run = [], 0
    for y in years:
        run += per.get(y, 0)
        out.append((y, run))
    return out


def chart(points, partial_year):
    """Inline SVG: cumulative citations. 2px line, 10% area wash,
    dashed final segment for the incomplete year, hover crosshair."""
    W, H = 720, 300
    ml, mr, mt, mb = 44, 18, 18, 34
    pw, ph = W - ml - mr, H - mt - mb

    xs = [p[0] for p in points]
    ymax = max(p[1] for p in points)
    # round the axis top to a clean number
    step = 250 if ymax > 500 else 100
    top = ((ymax // step) + 1) * step

    def px(y): return ml + (y - xs[0]) / max(1, (xs[-1] - xs[0])) * pw
    def py(v): return mt + ph - (v / top) * ph

    pts = [(px(y), py(v)) for y, v in points]
    # solid path up to the last complete year; dashed for the partial tail
    solid = " ".join(f"{'M' if i == 0 else 'L'}{x:.1f},{y:.1f}"
                     for i, (x, y) in enumerate(pts[:-1]))
    tail = f"M{pts[-2][0]:.1f},{pts[-2][1]:.1f} L{pts[-1][0]:.1f},{pts[-1][1]:.1f}"
    area = (solid + f" L{pts[-1][0]:.1f},{pts[-1][1]:.1f}"
            + f" L{pts[-1][0]:.1f},{py(0):.1f} L{pts[0][0]:.1f},{py(0):.1f} Z")

    grid, ticks = [], []
    v = 0
    while v <= top:
        y = py(v)
        grid.append(f'<line x1="{ml}" y1="{y:.1f}" x2="{W-mr}" y2="{y:.1f}" '
                    f'class="grid"/>')
        ticks.append(f'<text x="{ml-10}" y="{y+4:.1f}" class="tick ytick">'
                     f'{v:,}</text>')
        v += step

    xlab = "".join(
        f'<text x="{px(y):.1f}" y="{H-mb+20}" class="tick xtick">{y}</text>'
        for y in xs if y % 2 == 0 or y == xs[-1])

    hot = "".join(
        f'<rect class="hot" x="{px(y)-pw/(len(xs)-1)/2:.1f}" y="{mt}" '
        f'width="{pw/(len(xs)-1):.1f}" height="{ph}" '
        f'data-year="{y}" data-value="{v}" data-x="{px(y):.1f}" '
        f'data-y="{py(v):.1f}"/>'
        for y, v in points)

    last_y, last_v = points[-1]
    return f'''<figure class="chart">
  <figcaption>
    <h2>Citations over time</h2>
    <p class="sub">Cumulative citations to all {len(xs) and ""}papers, {xs[0]}&ndash;{xs[-1]}.
       {partial_year} is a partial year.</p>
  </figcaption>
  <svg viewBox="0 0 {W} {H}" role="img" preserveAspectRatio="xMidYMid meet"
       aria-label="Cumulative citations rising from 0 in {xs[0]} to {last_v} in {last_y}">
    <g class="grid-g">{"".join(grid)}</g>
    <path d="{area}" class="area"/>
    <path d="{solid}" class="line"/>
    <path d="{tail}" class="line dashed"/>
    <g class="ticks">{"".join(ticks)}{xlab}</g>
    <line class="crosshair" x1="0" y1="{mt}" x2="0" y2="{mt+ph}" opacity="0"/>
    <circle class="dot" cx="{pts[-1][0]:.1f}" cy="{pts[-1][1]:.1f}" r="5"/>
    <text class="endlabel" x="{pts[-1][0]-8:.1f}" y="{pts[-1][1]-14:.1f}">
      {last_v:,}</text>
    <circle class="hoverdot" r="5" opacity="0"/>
    <g class="hotspots">{hot}</g>
  </svg>
  <div class="tooltip" hidden></div>
</figure>'''


def main():
    papers = json.load(open("papers.json", encoding="utf-8"))
    points = cumulative(papers)
    total = sum(p["cited_by_count"] for p in papers)
    first = min(p["year"] for p in papers if p["year"])
    partial = points[-1][0]

    rows = []
    for p in papers:
        venue = VENUE_OVERRIDES.get(p["doi"]) or p["venue"] or "—"
        cites = p["cited_by_count"]
        cite_txt = (f'<span class="cites">{cites:,} citation'
                    f'{"" if cites == 1 else "s"}</span>' if cites else "")
        title = clean(p["title"])
        link = html.escape(p["url"] or "#")
        rows.append(f'''    <li>
      <a class="title" href="{link}">{title}</a>
      <p class="meta"><span class="venue">{html.escape(venue)}</span>
         <span class="year">{p["year"]}</span>{cite_txt}</p>
    </li>''')

    soft = "".join(
        f'    <li><a href="{u}">{n}</a> <span class="what">{d}</span></li>\n'
        for n, d, u in SOFTWARE)

    css_vars = lambda d: "\n".join(f"      --{k}: {v};" for k, v in d.items())

    page = f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{NAME} — publications</title>
<style>
  :root {{
    color-scheme: light;
{css_vars(LIGHT)}
  }}
  @media (prefers-color-scheme: dark) {{
    :root {{
      color-scheme: dark;
{css_vars(DARK)}
    }}
  }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0; padding: 0;
    background: var(--plane); color: var(--ink);
    font: 16px/1.6 system-ui, -apple-system, "Segoe UI", sans-serif;
    -webkit-font-smoothing: antialiased;
  }}
  .wrap {{ max-width: 46rem; margin: 0 auto; padding: 5rem 1.5rem 4rem; }}
  header h1 {{
    margin: 0 0 .3rem; font-size: 2.1rem; font-weight: 600;
    letter-spacing: -0.02em;
  }}
  .tagline {{ margin: 0; color: var(--secondary); }}
  .orcid {{
    display: inline-block; margin-top: .9rem; font-size: .85rem;
    color: var(--muted); text-decoration: none;
    border-bottom: 1px solid var(--axis); padding-bottom: 1px;
  }}
  .orcid:hover {{ color: var(--accent); border-color: var(--accent); }}
  .intro {{
    margin: 2.6rem 0 0; font-size: 1.25rem; line-height: 1.5;
    color: var(--ink);
  }}
  .intro b {{ font-weight: 600; color: var(--accent); }}

  /* chart */
  .chart {{
    margin: 3.5rem 0 0; padding: 1.5rem 1.25rem 1rem;
    background: var(--surface); border-radius: 10px;
    border: 1px solid var(--grid); position: relative;
  }}
  .chart figcaption {{ margin-bottom: .5rem; }}
  .chart h2 {{ margin: 0; font-size: 1rem; font-weight: 600; }}
  .chart .sub {{ margin: .2rem 0 0; font-size: .85rem; color: var(--muted); }}
  .chart svg {{ width: 100%; height: auto; display: block; overflow: visible; }}
  .grid line {{ stroke: var(--grid); stroke-width: 1; }}
  .line {{ fill: none; stroke: var(--accent); stroke-width: 2;
           stroke-linejoin: round; stroke-linecap: round; }}
  .line.dashed {{ stroke-dasharray: 5 4; }}
  .area {{ fill: var(--accent); opacity: .10; stroke: none; }}
  .dot, .hoverdot {{ fill: var(--accent); stroke: var(--surface);
                     stroke-width: 2; }}
  .endlabel {{ fill: var(--secondary); font-size: 12px; font-weight: 600;
               text-anchor: end; }}
  .tick {{ fill: var(--muted); font-size: 11px;
           font-variant-numeric: tabular-nums; }}
  .ytick {{ text-anchor: end; }}
  .xtick {{ text-anchor: middle; }}
  .crosshair {{ stroke: var(--axis); stroke-width: 1; }}
  .hot {{ fill: transparent; cursor: crosshair; }}
  .tooltip {{
    position: absolute; pointer-events: none; z-index: 5;
    background: var(--surface); color: var(--ink);
    border: 1px solid var(--grid); border-radius: 6px;
    padding: .45rem .6rem; font-size: .8rem; line-height: 1.35;
    box-shadow: 0 2px 10px rgba(0,0,0,.08); white-space: nowrap;
  }}
  .tooltip b {{ font-variant-numeric: tabular-nums; }}

  /* papers */
  h2.section {{
    margin: 3.5rem 0 0; font-size: .78rem; font-weight: 600;
    text-transform: uppercase; letter-spacing: .09em; color: var(--muted);
  }}
  ul.papers {{ list-style: none; margin: .5rem 0 0; padding: 0; }}
  ul.papers li {{ padding: 1.35rem 0; border-bottom: 1px solid var(--grid); }}
  ul.papers li:last-child {{ border-bottom: none; }}
  a.title {{
    color: var(--ink); text-decoration: none; font-size: 1.05rem;
    font-weight: 500; line-height: 1.4; display: inline-block;
  }}
  a.title:hover {{ color: var(--accent); }}
  .meta {{ margin: .35rem 0 0; font-size: .85rem; color: var(--muted); }}
  .meta .venue {{ color: var(--secondary); }}
  .meta .year::before, .meta .cites::before {{ content: "·"; margin: 0 .45rem; }}
  .cites {{ font-variant-numeric: tabular-nums; }}

  ul.software {{ list-style: none; margin: .5rem 0 0; padding: 0; }}
  ul.software li {{ padding: .55rem 0; font-size: .95rem; }}
  ul.software a {{ color: var(--accent); text-decoration: none;
                   font-weight: 500; }}
  ul.software a:hover {{ text-decoration: underline; }}
  ul.software .what {{ color: var(--muted); font-size: .85rem; }}

  footer {{
    margin: 4rem 0 0; padding-top: 1.5rem; border-top: 1px solid var(--grid);
    font-size: .8rem; color: var(--muted);
  }}
  @media (max-width: 34rem) {{
    .wrap {{ padding: 3rem 1.1rem; }}
    header h1 {{ font-size: 1.7rem; }}
    .intro {{ font-size: 1.1rem; }}
  }}
</style>
</head>
<body>
<div class="wrap">
  <header>
    <h1>{NAME}</h1>
    <p class="tagline">{TAGLINE}</p>
    <a class="orcid" href="https://orcid.org/{ORCID}">ORCID {ORCID}</a>
  </header>

  <p class="intro"><b>{len(papers)} papers</b>, cited <b>{total:,} times</b>
     since {first}.</p>

{chart(points, partial)}

  <h2 class="section">Publications</h2>
  <ul class="papers">
{chr(10).join(rows)}
  </ul>

  <h2 class="section">Software</h2>
  <ul class="software">
{soft}  </ul>

  <footer>Data from OpenAlex, last updated {date.today():%-d %B %Y}.</footer>
</div>

<script>
(function () {{
  var fig = document.querySelector('.chart');
  if (!fig) return;
  var svg = fig.querySelector('svg'),
      tip = fig.querySelector('.tooltip'),
      cross = fig.querySelector('.crosshair'),
      dot = fig.querySelector('.hoverdot');

  function show(e) {{
    var r = e.target, x = +r.dataset.x, y = +r.dataset.y;
    cross.setAttribute('x1', x); cross.setAttribute('x2', x);
    cross.setAttribute('opacity', 1);
    dot.setAttribute('cx', x); dot.setAttribute('cy', y);
    dot.setAttribute('opacity', 1);
    tip.innerHTML = r.dataset.year + '<br><b>' +
      (+r.dataset.value).toLocaleString() + '</b> citations';
    tip.hidden = false;
    var box = svg.getBoundingClientRect(),
        fb = fig.getBoundingClientRect(),
        vb = svg.viewBox.baseVal,
        sx = box.width / vb.width, sy = box.height / vb.height;
    var left = box.left - fb.left + x * sx,
        top = box.top - fb.top + y * sy;
    tip.style.left = Math.min(Math.max(left - tip.offsetWidth / 2, 4),
                              fb.width - tip.offsetWidth - 4) + 'px';
    tip.style.top = (top - tip.offsetHeight - 12) + 'px';
  }}
  function hide() {{
    tip.hidden = true;
    cross.setAttribute('opacity', 0);
    dot.setAttribute('opacity', 0);
  }}
  svg.querySelectorAll('.hot').forEach(function (r) {{
    r.addEventListener('mouseenter', show);
    r.addEventListener('mousemove', show);
  }});
  svg.addEventListener('mouseleave', hide);
}})();
</script>
</body>
</html>
'''
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(page)
    print(f"index.html written — {len(papers)} papers, {total:,} citations, "
          f"chart {points[0][0]}-{points[-1][0]}")


if __name__ == "__main__":
    main()
