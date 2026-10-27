#!/usr/bin/env python3
"""Render data/contributions.json as a terminal-style glyph graph (assets/glyphs-*.svg).

The year is drawn as text, one character per day: . : + # @ from the fewest to the most contributions, using
GitHub's own levels. The command line types itself, then each column of days flickers through two decoy
characters and settles on the real one. Decoys come from a seeded generator, so the output is identical for
identical data and the daily commit only changes when the data does. Standard library only.
"""
import datetime as dt
import json
import os
import random
from xml.sax.saxutils import escape

ROOT = os.path.join(os.path.dirname(__file__), "..")
PROMPT_USER = "sushil"
COMMAND = "contributions --glyphs --last-year"
GLYPHS = ".:+#@"          # indexed by GitHub's contribution level, 0 to 4
DECOYS = ".:+#@=*%~"
LEFT, COLW, ROWH, ADV = 44, 14, 17, 7.8   # left margin, column pitch, row pitch, assumed monospace advance
THEMES = {
    "dark": {"bg": "#0d1117", "border": "#30363d", "text": "#c9d1d9", "muted": "#8b949e", "prompt": "#3fb950",
             "ramp": ["#3a424a", "#2d7a3d", "#2ea043", "#3fb950", "#56d364"]},
    "light": {"bg": "#ffffff", "border": "#d0d7de", "text": "#24292f", "muted": "#57606a", "prompt": "#1a7f37",
              "ramp": ["#c8cfd6", "#6fc383", "#40a35a", "#2a7f43", "#216e39"]},
}
TYPE_START, TYPE_STEP = 200, 30           # ms
GRID_START, COL_STEP, FLICKER = 1400, 25, 110


def render(days, user, theme):
    t = THEMES[theme]
    first = dt.date.fromisoformat(days[0]["date"])
    start = first - dt.timedelta(days=(first.weekday() + 1) % 7)  # Sunday on or before the first day
    cols = (dt.date.fromisoformat(days[-1]["date"]) - start).days // 7 + 1
    width = max(860, LEFT + cols * COLW + 30)
    top = 80                                   # baseline of the first row
    height = top + 6 * ROWH + 62
    total = sum(d["count"] for d in days)
    active = sum(1 for d in days if d["count"] > 0)
    best = max(days, key=lambda d: d["count"])
    best_day = dt.date.fromisoformat(best["date"])
    stats = f"{total:,} contributions · {active} active days · best day {best['count']} ({best_day.strftime('%b')} {best_day.day})"

    column = {c: {} for c in range(cols)}      # column -> row -> (level, date)
    labels, last_month = [], None
    for d in days:
        day = dt.date.fromisoformat(d["date"])
        col, row = (day - start).days // 7, (day.weekday() + 1) % 7
        column[col][row] = (min(4, max(0, d["level"])), d["date"])
        if row == 0 and day.month != last_month and col < cols - 1:
            labels.append((col, day.strftime("%b")))
            last_month = day.month
    # The window starts mid-month, so the first two labels can land a column apart: keep only the later one.
    months = "".join(
        f'<text x="{LEFT + col * COLW}" y="{top - 20}" class="lbl">{name}</text>'
        for i, (col, name) in enumerate(labels)
        if i == len(labels) - 1 or labels[i + 1][0] - col >= 3
    )

    # Prompt and command, one character at a time at fixed positions, so alignment does not depend on the font.
    line = f"{PROMPT_USER}@github ~ $ "
    chars = []
    for i, ch in enumerate(line):
        chars.append(f'<tspan x="{20 + i * ADV:.1f}" class="p">{escape(ch)}</tspan>')
    for j, ch in enumerate(COMMAND):
        x = 20 + (len(line) + j) * ADV
        chars.append(f'<tspan x="{x:.1f}" class="k" style="animation-delay:{TYPE_START + j * TYPE_STEP}ms">{escape(ch)}</tspan>')
    typed_end = TYPE_START + len(COMMAND) * TYPE_STEP

    def layer(col, glyph_for, klass, delay):
        cx = LEFT + col * COLW + COLW // 2
        spans = "".join(
            f'<tspan x="{cx}" y="{top + row * ROWH}" class="l{lvl}">{escape(glyph_for(row, lvl, date))}</tspan>'
            for row, (lvl, date) in sorted(column[col].items())
        )
        return f'<text text-anchor="middle" class="{klass}" style="animation-delay:{delay}ms">{spans}</text>'

    grid = []
    for col in range(cols):
        s = GRID_START + col * COL_STEP
        def decoy(k):
            def pick(row, lvl, date):
                return random.Random(f"{date}/{k}").choice(DECOYS)
            return pick
        grid.append(layer(col, decoy(0), "da", s))
        grid.append(layer(col, decoy(1), "db", s + FLICKER))
        grid.append(layer(col, lambda row, lvl, date: GLYPHS[lvl], "fin", s + 2 * FLICKER))
    grid_end = GRID_START + cols * COL_STEP + 2 * FLICKER

    ramp = "".join(f".l{i}{{fill:{c}}}" for i, c in enumerate(t["ramp"]))
    legend_x = width - 20 - 200
    legend = "".join(
        f'<tspan x="{legend_x + 40 + i * 24}" class="l{i}">{g}</tspan>' for i, g in enumerate(GLYPHS)
    )
    foot_y = top + 6 * ROWH + 38
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="t">
<title id="t">{escape(user)}: the last year of contributions drawn as text characters, from . for none to @ for the most. {escape(stats)}</title>
<style>
text{{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;font-size:13px}}
.p{{fill:{t["prompt"]};font-weight:600}} .k{{fill:{t["text"]}}}
.lbl{{fill:{t["muted"]};font-size:10px}} .st{{fill:{t["text"]};font-size:12px}} .lg{{fill:{t["muted"]};font-size:10px}}
{ramp}
.k{{opacity:0;animation:show 0s steps(1) both}}
.da,.db,.fin{{opacity:0}}
.da,.db{{animation:blink {FLICKER}ms steps(1)}} .fin{{animation:show 0s steps(1) forwards}}
.foot{{opacity:0;animation:show .6s ease-out {grid_end}ms forwards}}
@keyframes show{{to{{opacity:1}}}}
@keyframes blink{{from{{opacity:1}}to{{opacity:1}}}}
@media (prefers-reduced-motion:reduce){{.k,.fin,.foot{{animation:none;opacity:1}}.da,.db{{display:none}}}}
</style>
<rect x=".5" y=".5" width="{width - 1}" height="{height - 1}" rx="10" fill="{t["bg"]}" stroke="{t["border"]}"/>
<text y="28">{"".join(chars)}</text>
<text x="{legend_x}" y="28" class="lg">less</text><text y="28" text-anchor="middle">{legend}</text><text x="{legend_x + 40 + 5 * 24}" y="28" class="lg">more</text>
{months}
<text x="6" y="{top + 1 * ROWH}" class="lbl">Mon</text><text x="6" y="{top + 3 * ROWH}" class="lbl">Wed</text><text x="6" y="{top + 5 * ROWH}" class="lbl">Fri</text>
{"".join(grid)}
<text x="{LEFT}" y="{foot_y}" class="st foot">{escape(stats)}</text>
</svg>
'''


def main():
    data = json.load(open(os.path.join(ROOT, "data", "contributions.json")))
    os.makedirs(os.path.join(ROOT, "assets"), exist_ok=True)
    for theme in THEMES:
        with open(os.path.join(ROOT, "assets", f"glyphs-{theme}.svg"), "w") as f:
            f.write(render(data["days"], data["user"], theme))
    print("wrote assets/glyphs-dark.svg, assets/glyphs-light.svg")


if __name__ == "__main__":
    main()
