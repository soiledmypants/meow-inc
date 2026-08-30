"""Export trait layers + placements for the local trait editor site.

Renders every trait onto its own transparent layer and writes the pixel
data (plus current placements.json) into site/traits-data.js, which the
editor page loads. Run this again after editing trait art in traits.py.

Usage: python export_site.py
"""

import json
from pathlib import Path

import config
from canvas import PixelCanvas
from palette import INK
from traits import TRAITS, CATEGORY_ORDER, CHARACTER_ORDER


def layer_pixels(trait):
    if not trait.draw:
        return []
    layer = PixelCanvas(config.LOGICAL_SIZE)
    trait.draw(layer)
    pixels = []
    for y in range(layer.size):
        for x in range(layer.size):
            color = layer.grid[y][x]
            if color is not None:
                pixels.append([x, y, list(color)])
    return pixels


def main():
    root = Path(__file__).parent
    placements_path = root / config.PLACEMENTS_FILE
    placements = (json.loads(placements_path.read_text())
                  if placements_path.exists() else {})

    data = {
        "collection": config.COLLECTION_NAME,
        "size": config.LOGICAL_SIZE,
        "ink": list(INK),
        "categories": CATEGORY_ORDER,
        "characterOrder": CHARACTER_ORDER,
        "backgrounds": [
            {"name": t.name, "color": list(t.color),
             "pixels": layer_pixels(t)}
            for t in TRAITS["Background"]
        ],
        "layers": {
            cat: {t.name: layer_pixels(t) for t in TRAITS[cat]}
            for cat in CHARACTER_ORDER
        },
        "placements": placements,
    }

    site = root / "site"
    site.mkdir(exist_ok=True)
    (site / "traits-data.js").write_text(
        "window.TRAITS_DATA = " + json.dumps(data) + ";\n"
    )
    n_layers = sum(len(v) for v in data["layers"].values())
    print(f"exported {n_layers} trait layers to site/traits-data.js")


if __name__ == "__main__":
    main()
