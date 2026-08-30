"""V4 layer kit — image-based: pixel head + suit bases, recolored.

Usage: python v4_layers.py

Reads art-refs/v4-head-base.png (orange pixel tabby) and
art-refs/v4-body-base.png (black pixel suit), builds colorways via
palette hue-rotation (head) and dark-tone colorization (body), plus
pre-rendered detailed backdrops from v4_generate's motif functions.
Writes v4-layers/ + manifest.json for the v4 editor.
"""

import colorsys
import json
import random
from pathlib import Path

from PIL import Image

import v4_generate as v4

CANVAS = 1024
OUT = Path("v4-layers")


# ------------------------------------------------------------ head

def load_head():
    im = Image.open("art-refs/v4-head-base.png").convert("RGBA")
    bbox = im.getbbox()
    im = im.crop(bbox)
    scale = min(620 / im.width, 620 / im.height)
    im = im.resize((round(im.width * scale), round(im.height * scale)),
                   Image.NEAREST)
    canvas = Image.new("RGBA", (CANVAS, CANVAS), (0, 0, 0, 0))
    canvas.paste(im, ((CANVAS - im.width) // 2, 44), im)
    return canvas


def hue_shift(base, dh, sat, val):
    """Recolor only the green fur (hue 0.20-0.55); pink ears, nose,
    cream muzzle, whites and blacks stay as they are."""
    out = base.copy()
    px = out.load()
    for y in range(out.height):
        for x in range(out.width):
            r, g, b, a = px[x, y]
            if not a:
                continue
            h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
            if not (0.20 <= h <= 0.55 and s > 0.15):
                continue
            h = (h + dh) % 1.0
            s = min(1.0, s * sat)
            v = min(1.0, v * val)
            r2, g2, b2 = colorsys.hsv_to_rgb(h, s, v)
            px[x, y] = (round(r2 * 255), round(g2 * 255), round(b2 * 255), a)
    return out


# shifts are relative to the GREEN base (fur hue ~0.36)
HEADS = [
    ("tabby", 0.72, 1.70, 1.02),     # back to the original rich orange
    ("green", 0.0, 1.0, 1.0),        # the base itself
    ("blue", 0.22, 1.15, 1.0),
    ("pink", 0.57, 1.10, 1.05),
    ("mint", 0.04, 0.70, 1.02),
    ("lilac", 0.42, 1.05, 1.0),
    ("gold", 0.76, 1.50, 1.06),
    ("smoke", 0.0, 0.12, 0.95),
    ("midnight", 0.22, 0.25, 0.62),
]


# ------------------------------------------------------------ body

def load_body():
    im = Image.open("art-refs/v4-body-base.png").convert("RGBA")
    bbox = im.getbbox()
    im = im.crop(bbox)
    scale = CANVAS / im.width
    im = im.resize((CANVAS, round(im.height * scale)), Image.NEAREST)
    canvas = Image.new("RGBA", (CANVAS, CANVAS), (0, 0, 0, 0))
    canvas.paste(im, (0, CANVAS - im.height), im)
    return canvas


def suit_recolor(base, target):
    """Colorize the dark suit (and tie) tones; the white shirt stays."""
    out = base.copy()
    px = out.load()
    r2, g2, b2 = target
    for y in range(out.height):
        for x in range(out.width):
            r, g, b, a = px[x, y]
            if not a:
                continue
            v = max(r, g, b)
            if v < 160:
                f = v / 60
                px[x, y] = (min(255, round(r2 * f)), min(255, round(g2 * f)),
                            min(255, round(b2 * f)), a)
    return out


BODIES = [
    ("black", None),                 # the original
    ("navy", (52, 72, 132)),
    ("burgundy", (128, 46, 60)),
    ("forest", (46, 104, 70)),
    ("royal", (92, 62, 148)),
    ("sand", (168, 136, 92)),
]


# ------------------------------------------------------------ backdrops

FLAT_BGS = [
    ("navy", "#182056"), ("charcoal", "#201e28"), ("violet", "#42306e"),
    ("deep green", "#104632"), ("plum", "#3a2250"), ("crimson", "#6e1a24"),
]


def render_backdrops():
    layers = []
    rng = random.Random(28)
    for name, base, draw in v4.BACKDROPS:
        c = v4.C(base)
        draw(c, rng)
        slug = name.replace(" ", "-")
        c.img().convert("RGBA").save(OUT / f"backdrop-{slug}.png")
        layers.append({"name": name, "file": f"backdrop-{slug}.png"})
        print(f"backdrop-{slug}.png")
    return layers


# ------------------------------------------------------------ main

def main():
    OUT.mkdir(exist_ok=True)

    backdrops = render_backdrops()

    body_base = load_body()
    bodies = []
    for name, color in BODIES:
        img = body_base if color is None else suit_recolor(body_base, color)
        img.save(OUT / f"body-{name}.png")
        bodies.append({"name": name, "file": f"body-{name}.png"})
        print(f"body-{name}.png")

    head_base = load_head()
    heads = []
    for name, dh, sat, val in HEADS:
        img = head_base if name == "green" else hue_shift(head_base, dh, sat, val)
        img.save(OUT / f"head-{name}.png")
        heads.append({"name": name, "file": f"head-{name}.png"})
        print(f"head-{name}.png")

    manifest = {
        "canvas": CANVAS,
        "backgrounds": [{"name": n, "color": c} for n, c in FLAT_BGS],
        "categories": [
            {"name": "Backdrop", "optional": True, "layers": backdrops},
            {"name": "Body", "optional": False, "layers": bodies},
            {"name": "Head", "optional": False, "layers": heads},
        ],
    }
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2))
    n = len(backdrops) + len(bodies) + len(heads)
    print(f"manifest.json — {n} layers across 3 categories")


if __name__ == "__main__":
    main()
