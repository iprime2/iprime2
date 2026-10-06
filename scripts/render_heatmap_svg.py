#!/usr/bin/env python3
"""Render data/contributions.json as animated dark/light contribution heatmaps (assets/heatmap-*.svg)."""
import datetime as dt
import json
import os
from xml.sax.saxutils import escape

ROOT = os.path.join(os.path.dirname(__file__), "..")
PROMPT_USER = "sushil"
CELL, GAP, LEFT, TOP = 12, 3, 34, 58
THEMES = {
    "dark": {"bg": "#0d1117", "border": "#30363d", "text": "#c9d1d9", "muted": "#8b949e", "prompt": "#3fb950",
             "levels": ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"]},
    "light": {"bg": "#ffffff", "border": "#d0d7de", "text": "#24292f", "muted": "#57606a", "prompt": "#1a7f37",
              "levels": ["#ebedf0", "#9be9a8", "#40c463", "#30a14e", "#216e39"]},
}


def streaks(days):
    longest = run = 0
    for d in days:
        run = run + 1 if d["count"] > 0 else 0
        longest = max(longest, run)
    current = 0
    for d in reversed(days):
        if d["count"] > 0:
            current += 1
        elif current == 0 and d is days[-1]:
            continue  # today may still be empty
        else:
            break
    return current, longest


def render(days, user, theme):
    t = THEMES[theme]
    first = dt.date.fromisoformat(days[0]["date"])
    start = first - dt.timedelta(days=(first.weekday() + 1) % 7)  # Sunday on or before the first day
    cols = (dt.date.fromisoformat(days[-1]["date"]) - start).days // 7 + 1
    width = max(860, LEFT + cols * (CELL + GAP) + 20)
    height = TOP + 7 * (CELL + GAP) + 52
    total = sum(d["count"] for d in days)
    best = max(days, key=lambda d: d["count"])
    current, longest = streaks(days)

    cells, months, last_month = [], [], None
    for d in days:
        day = dt.date.fromisoformat(d["date"])
        col, row = (day - start).days // 7, (day.weekday() + 1) % 7
        x, y = LEFT + col * (CELL + GAP), TOP + row * (CELL + GAP)
        if row == 0 and day.month != last_month and col < cols - 1:
            months.append(f'<text x="{x}" y="{TOP - 8}" class="lbl">{day.strftime("%b")}</text>')
            last_month = day.month
        cells.append(
            f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="2" fill="{t["levels"][d["level"]]}" '
            f'class="c d{col + row}"><title>{d["count"]} on {d["date"]}</title></rect>'
        )
    delays = "".join(f".d{i}{{animation-delay:{i * 22}ms}}" for i in range(cols + 7))
    legend_x = width - 20 - 5 * (CELL + GAP) - 70
    legend = "".join(
        f'<rect x="{legend_x + 34 + i * (CELL + GAP)}" y="18" width="{CELL}" height="{CELL}" rx="2" fill="{c}"/>'
        for i, c in enumerate(t["levels"])
    )
    stats = (f"{total:,} contributions in the last year · current streak {current} d · "
             f"longest streak {longest} d · best day {best['count']} ({best['date']})")
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="t">
<title id="t">{escape(user)}: {escape(stats)}</title>
<style>
text{{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace}}
.p{{fill:{t["prompt"]};font-size:13px;font-weight:600}} .cmd{{fill:{t["text"]};font-size:13px}}
.lbl{{fill:{t["muted"]};font-size:10px}} .st{{fill:{t["text"]};font-size:12px}}
.c{{opacity:0;animation:in .45s ease-out forwards;transform-box:fill-box}}
@keyframes in{{from{{opacity:0;transform:translate(-8px,-8px) scale(.4)}}to{{opacity:1;transform:none}}}}
{delays}
@media (prefers-reduced-motion:reduce){{.c{{animation:none;opacity:1}}}}
</style>
<rect x=".5" y=".5" width="{width - 1}" height="{height - 1}" rx="10" fill="{t["bg"]}" stroke="{t["border"]}"/>
<text x="20" y="28"><tspan class="p">{PROMPT_USER}@github</tspan><tspan class="cmd"> ~ $ contributions --last-year</tspan></text>
{"".join(months)}
<text x="6" y="{TOP + 1 * (CELL + GAP) + 10}" class="lbl">Mon</text><text x="6" y="{TOP + 3 * (CELL + GAP) + 10}" class="lbl">Wed</text><text x="6" y="{TOP + 5 * (CELL + GAP) + 10}" class="lbl">Fri</text>
{"".join(cells)}
<text x="{LEFT}" y="{height - 20}" class="st">{escape(stats)}</text>
<text x="{legend_x}" y="28" class="lbl">Less</text>{legend}<text x="{legend_x + 34 + 5 * (CELL + GAP) + 4}" y="28" class="lbl">More</text>
</svg>
'''


def main():
    data = json.load(open(os.path.join(ROOT, "data", "contributions.json")))
    os.makedirs(os.path.join(ROOT, "assets"), exist_ok=True)
    for theme in THEMES:
        with open(os.path.join(ROOT, "assets", f"heatmap-{theme}.svg"), "w") as f:
            f.write(render(data["days"], data["user"], theme))
    print("wrote assets/heatmap-dark.svg, assets/heatmap-light.svg")


if __name__ == "__main__":
    main()
