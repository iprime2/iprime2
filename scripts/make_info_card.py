#!/usr/bin/env python3
"""Neofetch-style info card SVGs that fade in line by line (assets/card-dark.svg, assets/card-light.svg).

Facts are edited here by hand; the contribution count comes from data/contributions.json, so the
daily workflow regenerates the card along with the heatmap.
"""
import json
import os
from xml.sax.saxutils import escape

ROOT = os.path.join(os.path.dirname(__file__), "..")
USER = "sushil"
FACTS = [
    ("Name", "Sushil Kumar Gupta"),
    ("Role", "Backend & AI Systems Engineer"),
    ("Now", "Software Engineer @ GoQuant (HFT tech)"),
    ("Before", "Full Stack Developer @ Codeinbound LLP"),
    ("Location", "Pune, India"),
    ("Focus", "MCP servers for AI agents"),
    ("", "Smart order routing, L2 order books"),
    ("Languages", "Python, TypeScript, C++, Rust, Java"),
    ("AI", "LangChain, LangGraph, FastAPI, OpenAI"),
    ("Infra", "AWS, Docker, PostgreSQL, Redis"),
    ("Education", "M.Sc. Computer Science, MIT-WPU"),
    ("Open to", "AI/ML, Backend, Full Stack roles"),
]
WIDTH, HEIGHT, LINE_H = 469, 412, 21
THEMES = {
    "dark": {"bg": "#0d1117", "border": "#30363d", "text": "#c9d1d9", "key": "#58a6ff", "prompt": "#3fb950", "muted": "#8b949e",
             "blocks": ["#f85149", "#d29922", "#3fb950", "#58a6ff", "#bc8cff", "#39c5cf", "#c9d1d9"]},
    "light": {"bg": "#ffffff", "border": "#d0d7de", "text": "#24292f", "key": "#0969da", "prompt": "#1a7f37", "muted": "#57606a",
              "blocks": ["#cf222e", "#9a6700", "#1a7f37", "#0969da", "#8250df", "#1b7c83", "#24292f"]},
}


def contributions():
    try:
        days = json.load(open(os.path.join(ROOT, "data", "contributions.json")))["days"]
        return f"{sum(d['count'] for d in days):,} in the last year"
    except (OSError, KeyError, ValueError):
        return None


def render(t):
    facts = list(FACTS)
    contrib = contributions()
    if contrib:
        facts.append(("Contributions", contrib))
    top = 72
    lines = []
    for i, (k, v) in enumerate(facts):
        y = top + i * LINE_H
        key = f'<tspan class="k">{escape(k + ":") if k else ""}</tspan>'
        lines.append(f'<text x="22" y="{y}" class="l f{i}">{key}<tspan x="138" class="v">{escape(v)}</tspan></text>')
    blocks_y = top + len(facts) * LINE_H + 4
    blocks = "".join(
        f'<rect x="{22 + i * 26}" y="{blocks_y}" width="22" height="12" rx="2" fill="{c}" class="l f{len(facts)}"/>'
        for i, c in enumerate(t["blocks"])
    )
    delays = "".join(f".f{i}{{animation-delay:{0.6 + i * 0.18:.2f}s}}" for i in range(len(facts) + 1))
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}" role="img" aria-labelledby="t">
<title id="t">{escape("; ".join(f"{k} {v}".strip() for k, v in facts))}</title>
<style>
text{{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;font-size:13px}}
.p{{fill:{t["prompt"]};font-weight:600}} .cmd{{fill:{t["text"]}}} .h{{fill:{t["prompt"]};font-weight:700}}
.rule{{fill:{t["muted"]}}} .k{{fill:{t["key"]};font-weight:600}} .v{{fill:{t["text"]}}}
.l{{opacity:0;animation:in .4s ease-out forwards}}
@keyframes in{{from{{opacity:0;transform:translateX(-6px)}}to{{opacity:1;transform:none}}}}
{delays}
@media (prefers-reduced-motion:reduce){{.l{{animation:none;opacity:1}}}}
</style>
<rect x=".5" y=".5" width="{WIDTH - 1}" height="{HEIGHT - 1}" rx="10" fill="{t["bg"]}" stroke="{t["border"]}"/>
<text x="22" y="26"><tspan class="p">{USER}@github</tspan><tspan class="cmd"> ~ $ neofetch</tspan></text>
<text x="22" y="48" class="h">{USER}@github</text><text x="22" y="58" class="rule">{"-" * 13}</text>
{"".join(lines)}
{blocks}
</svg>
'''


def main():
    os.makedirs(os.path.join(ROOT, "assets"), exist_ok=True)
    for name, t in THEMES.items():
        with open(os.path.join(ROOT, "assets", f"card-{name}.svg"), "w") as f:
            f.write(render(t))
    print("wrote assets/card-dark.svg, assets/card-light.svg")


if __name__ == "__main__":
    main()
