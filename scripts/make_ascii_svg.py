#!/usr/bin/env python3
"""Photo -> self-typing ASCII portrait SVGs (assets/portrait-dark.svg, assets/portrait-light.svg).

One-off, run locally: pip install pillow numpy "rembg[cpu]"
    python scripts/make_ascii_svg.py source/photo.jpg --crop 175,225,355,460
Characters are drawn only inside the person (rembg mask); brightness picks the character.
"""
import argparse
import os
from xml.sax.saxutils import escape

import numpy as np
from PIL import Image, ImageEnhance, ImageOps

ROOT = os.path.join(os.path.dirname(__file__), "..")
RAMP = " .,:;i1tfLCG08@"  # sparse -> dense
COLS, CHAR_W, LINE_H, PAD, HEIGHT = 84, 4.4, 7.6, 12, 412  # HEIGHT matches the info card
THEMES = {
    "dark": {"bg": "#0d1117", "border": "#30363d", "ink": "#c9d1d9", "prompt": "#3fb950", "dense_is_bright": True},
    "light": {"bg": "#ffffff", "border": "#d0d7de", "ink": "#24292f", "prompt": "#1a7f37", "dense_is_bright": False},
}


def ascii_rows(photo, crop):
    from rembg import remove  # heavy import, only for this one-off script

    cut = remove(Image.open(photo).convert("RGB").crop(crop))  # RGBA, background transparent
    rows = round(COLS * cut.height / cut.width * CHAR_W / LINE_H)
    small = cut.resize((COLS, rows), Image.LANCZOS)
    alpha = np.asarray(small.getchannel("A"), dtype=float) / 255
    lum = ImageOps.autocontrast(small.convert("L"), cutoff=2)
    lum = np.asarray(ImageEnhance.Contrast(lum).enhance(1.3), dtype=float) / 255
    return lum, alpha


def to_text(lum, alpha, dense_is_bright):
    out = []
    for y in range(lum.shape[0]):
        line = ""
        for x in range(lum.shape[1]):
            if alpha[y, x] < 0.5:
                line += " "
                continue
            v = lum[y, x] if dense_is_bright else 1 - lum[y, x]
            line += RAMP[1 + min(len(RAMP) - 2, int(v * (len(RAMP) - 1)))]
        out.append(line.rstrip())
    while out and not out[0].strip():
        out.pop(0)
    while out and not out[-1].strip():
        out.pop()
    return out


def svg(lines, t, user):
    width = round(PAD * 2 + COLS * CHAR_W)
    height = HEIGHT
    top = 40 + max(0, (HEIGHT - 40 - PAD - len(lines) * LINE_H) / 2)
    per_row = 3.6 / max(1, len(lines))
    style_rows = "".join(f".r{i}{{animation-delay:{0.3 + i * per_row:.2f}s}}" for i in range(len(lines)))
    text = "".join(
        f'<text x="{PAD}" y="{top + (i + 1) * LINE_H - 2:.1f}" class="a r{i}" xml:space="preserve">{escape(line)}</text>'
        for i, line in enumerate(lines)
    )
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="t">
<title id="t">ASCII portrait of {escape(user)}</title>
<style>
text{{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace}}
.p{{fill:{t["prompt"]};font-size:13px;font-weight:600}} .cmd{{fill:{t["ink"]};font-size:13px}}
.a{{fill:{t["ink"]};font-size:{CHAR_W / 0.6:.2f}px;clip-path:inset(0 100% 0 0);animation:type .35s steps({COLS}) forwards}}
@keyframes type{{to{{clip-path:inset(0 0 0 0)}}}}
{style_rows}
@media (prefers-reduced-motion:reduce){{.a{{animation:none;clip-path:none}}}}
</style>
<rect x=".5" y=".5" width="{width - 1}" height="{height - 1}" rx="10" fill="{t["bg"]}" stroke="{t["border"]}"/>
<text x="{PAD + 4}" y="26"><tspan class="p">{escape(user)}@github</tspan><tspan class="cmd"> ~ $ cat portrait.txt</tspan></text>
{text}
</svg>
'''


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("photo")
    ap.add_argument("--crop", default=None, help="left,top,right,bottom in source pixels")
    ap.add_argument("--user", default="sushil")
    args = ap.parse_args()
    img = Image.open(args.photo)
    crop = tuple(int(v) for v in args.crop.split(",")) if args.crop else (0, 0, img.width, img.height)
    lum, alpha = ascii_rows(args.photo, crop)
    os.makedirs(os.path.join(ROOT, "assets"), exist_ok=True)
    for name, t in THEMES.items():
        lines = to_text(lum, alpha, t["dense_is_bright"])
        with open(os.path.join(ROOT, "assets", f"portrait-{name}.svg"), "w") as f:
            f.write(svg(lines, t, args.user))
        print(f"portrait-{name}.svg: {len(lines)} rows x {COLS} cols")


if __name__ == "__main__":
    main()
