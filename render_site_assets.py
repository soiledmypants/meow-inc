"""Render marketing-site assets from the collection's own trait code.

Usage: python render_site_assets.py --dest ../meow-inc-site/assets

Writes transparent character PNGs for the featured cast and clean
background tiles (no character) for every background trait.
"""

import argparse
import json
from pathlib import Path

from PIL import Image

import config
from banner import CAST, render_character
from canvas import PixelCanvas
from traits import TRAITS

CHAR_SCALE = 10   # 320px characters
BG_SCALE = 8      # 256px background tiles


def to_rgba(layer, scale):
    img = Image.new("RGBA", (layer.size, layer.size), (0, 0, 0, 0))
    data = [(c[0], c[1], c[2], 255) if c is not None else (0, 0, 0, 0)
            for row in layer.grid for c in row]
    img.putdata(data)
    return img.resize((layer.size * scale,) * 2, Image.NEAREST)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dest", default="../meow-inc-site/assets")
    parser.add_argument("--src", default="output-3333")
    args = parser.parse_args()
    dest = Path(args.dest)
    dest.mkdir(parents=True, exist_ok=True)

    placements_path = Path(__file__).parent / config.PLACEMENTS_FILE
    placements = (json.loads(placements_path.read_text())
                  if placements_path.exists() else {})

    for edition in CAST:
        meta = json.loads((Path(args.src) / "metadata"
                           / f"{edition:04d}.json").read_text())
        assignment = {a["trait_type"]: a["value"] for a in meta["attributes"]}
        layer = render_character(assignment, placements)
        to_rgba(layer, CHAR_SCALE).save(dest / f"char-{edition:04d}.png")
        print(f"char-{edition:04d}.png")

    for t in TRAITS["Background"]:
        c = PixelCanvas(config.LOGICAL_SIZE)
        c.fill(t.color)
        if t.draw:
            layer = PixelCanvas(config.LOGICAL_SIZE)
            t.draw(layer)
            c.paint_background(layer)
        slug = t.name.lower().replace(" ", "-")
        c.to_image(BG_SCALE).save(dest / f"bg-{slug}.png")
        print(f"bg-{slug}.png")


if __name__ == "__main__":
    main()
