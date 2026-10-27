#!/usr/bin/env python3
"""Render data/contributions.json as an animated 3D skyline (assets/skyline-*.svg).

Every day is a building as tall as its contributions. Heights use the square root of the count, so one
huge day does not flatten the rest of the year. Colours are GitHub's own level shades. Standard library only.

The buildings are boxes in an oblique projection: a front face, a lit top and a shaded side, offset up and
to the right, drawn back to front so nearer buildings cover farther ones. No 3D library involved.
"""
import datetime as dt
import json
import math
import os
from xml.sax.saxutils import escape

ROOT = os.path.join(os.path.dirname(__file__), "..")
PROMPT_USER = "sushil"
S, D = 11, 5            # footprint width of a building, depth offset of the top and side faces
PX, PY = 15, 14         # column and row pitch
LEFT, HMAX = 34, 64     # left margin, height of the tallest building
THEMES = {
    "dark": {"bg": "#0d1117", "border": "#30363d", "text": "#c9d1d9", "muted": "#8b949e", "prompt": "#3fb950",
             "levels": ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"], "lit": 0.28, "shade": 0.35},
    "light": {"bg": "#ffffff", "border": "#d0d7de", "text": "#24292f", "muted": "#57606a", "prompt": "#1a7f37",
              "levels": ["#ebedf0", "#9be9a8", "#40c463", "#30a14e", "#216e39"], "lit": 0.4, "shade": 0.22},
}


def mix(hex_color, target, amount):
    """Blend a #rrggbb colour toward white or black."""
    c = [int(hex_color[i:i + 2], 16) for i in (1, 3, 5)]
    c = [round(v + (target - v) * amount) for v in c]
    return "#%02x%02x%02x" % tuple(c)


def render(days, user, theme):
    t = THEMES[theme]
    first = dt.date.fromisoformat(days[0]["date"])
    start = first - dt.timedelta(days=(first.weekday() + 1) % 7)  # Sunday on or before the first day
    cols = (dt.date.fromisoformat(days[-1]["date"]) - start).days // 7 + 1
    width = max(860, LEFT + cols * PX + D + 26)
    base = 48 + HMAX + D                      # baseline of the back row (Sunday)
    height = base + 6 * PY + 52
    total = sum(d["count"] for d in days)
    biggest = max(1, max(d["count"] for d in days))
    best = max(days, key=lambda d: d["count"])
    stats = f"{total:,} contributions in the last year · tallest day {best['count']} ({best['date']})"

    cells, labels, last_month = {}, [], None
    for d in days:
        day = dt.date.fromisoformat(d["date"])
        col, row = (day - start).days // 7, (day.weekday() + 1) % 7
        cells[(row, col)] = d
        if row == 0 and day.month != last_month and col < cols - 1:
            labels.append((col, day.strftime("%b")))
            last_month = day.month
    # The window starts mid-month, so the first two labels can land a column apart: keep only the later one.
    months = [
        f'<text x="{LEFT + col * PX}" y="{base + 6 * PY + 22}" class="lbl">{name}</text>'
        for i, (col, name) in enumerate(labels)
        if i == len(labels) - 1 or labels[i + 1][0] - col >= 3
    ]

    ground, boxes, lead = [], [], ""
    for row in range(7):                       # back (Sunday) to front (Saturday)
        for col in range(cols):
            d = cells.get((row, col))
            if d is None:
                continue
            x, y = LEFT + col * PX, base + row * PY
            if d["count"] <= 0:                # an empty day is a flat tile on the ground
                ground.append(f"M{x} {y}h{S}l{D} -{D}h-{S}z")
                continue
            h = max(3, round(HMAX * math.sqrt(d["count"] / biggest)))
            lvl = min(4, max(1, d["level"]))
            delay = (6 - row) * 45 + col * 10  # the wave starts at the front left and sweeps back and right
            boxes.append(
                f'<g class="b" style="animation-delay:{delay}ms;transform-origin:{x}px {y}px">'
                f'<path class="f{lvl}" d="M{x} {y}h{S}v-{h}h-{S}z"/>'
                f'<path class="t{lvl}" d="M{x} {y - h}h{S}l{D} -{D}h-{S}z"/>'
                f'<path class="s{lvl}" d="M{x + S} {y}l{D} -{D}v-{h}l-{D} {D}z"/></g>'
            )
            if d is best:                      # a leader line from the tallest building to its label
                tx, ty = x + (S + D) // 2 + 2, y - h - D
                ly = max(46, ty - 16)
                end = tx > width - 190
                anchor = ' text-anchor="end"' if end else ""
                when = dt.date.fromisoformat(d["date"])
                label = f'{d["count"]} contributions · {when.strftime("%b")} {when.day}'
                lead = (f'<g class="lead"><path d="M{tx} {ty}V{ly}" stroke="{t["muted"]}" fill="none"/>'
                        f'<circle cx="{tx}" cy="{ly}" r="2" fill="{t["prompt"]}"/>'
                        f'<text x="{tx + (-6 if end else 6)}" y="{ly + 4}" class="st"{anchor}>{escape(label)}</text></g>')

    shades = "".join(
        f'.f{i}{{fill:{c}}}.t{i}{{fill:{mix(c, 255, t["lit"])}}}.s{i}{{fill:{mix(c, 0, t["shade"])}}}'
        for i, c in enumerate(t["levels"]) if i
    )
    legend_x = width - 20 - 5 * 15 - 70
    legend = "".join(
        f'<rect x="{legend_x + 34 + i * 15}" y="18" width="11" height="11" rx="2" fill="{c}"/>' for i, c in enumerate(t["levels"])
    )
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="t">
<title id="t">{escape(user)}: skyline of contributions. {escape(stats)}</title>
<style>
text{{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace}}
.p{{fill:{t["prompt"]};font-size:13px;font-weight:600}} .cmd{{fill:{t["text"]};font-size:13px}}
.lbl{{fill:{t["muted"]};font-size:10px}} .st{{fill:{t["text"]};font-size:11px}} .z{{fill:{t["levels"][0]}}}
{shades}
.b{{animation:rise .65s cubic-bezier(.3,1.35,.5,1) both}}
@keyframes rise{{from{{transform:scaleY(0)}}to{{transform:none}}}}
.lead{{animation:fade .5s ease-out 1.5s both}}
@keyframes fade{{from{{opacity:0}}to{{opacity:1}}}}
@media (prefers-reduced-motion:reduce){{.b,.lead{{animation:none}}}}
</style>
<rect x=".5" y=".5" width="{width - 1}" height="{height - 1}" rx="10" fill="{t["bg"]}" stroke="{t["border"]}"/>
<text x="20" y="28"><tspan class="p">{PROMPT_USER}@github</tspan><tspan class="cmd"> ~ $ skyline --last-year</tspan></text>
<text x="{legend_x}" y="28" class="lbl">Less</text>{legend}<text x="{legend_x + 34 + 5 * 15 + 4}" y="28" class="lbl">More</text>
<path class="z" d="{"".join(ground)}"/>
{"".join(boxes)}
{lead}
{"".join(months)}
<text x="{LEFT}" y="{height - 14}" class="st">{escape(stats)}</text>
</svg>
'''


def main():
    data = json.load(open(os.path.join(ROOT, "data", "contributions.json")))
    os.makedirs(os.path.join(ROOT, "assets"), exist_ok=True)
    for theme in THEMES:
        with open(os.path.join(ROOT, "assets", f"skyline-{theme}.svg"), "w") as f:
            f.write(render(data["days"], data["user"], theme))
    print("wrote assets/skyline-dark.svg, assets/skyline-light.svg")


if __name__ == "__main__":
    main()
