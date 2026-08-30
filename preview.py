"""Render a lineup of every trait in one category for quick art review.

Usage:
    python preview.py                 # one of each Animal (default)
    python preview.py Hat             # one of each hat
    python preview.py Suit out.png    # choose the output file
"""

import sys

from PIL import Image

import generate
from traits import TRAITS

BASE = {
    "Background": "Deep Space", "Animal": "Honey Bear", "Eyes": "Steady",
    "Mouth": "Smile", "Suit": "Navy Suit", "Tie": "Red Tie", "Hat": "None",
    "Eyewear": "None", "Accessory": "None",
}
THUMB = 128
COLS = 5


def main():
    category = sys.argv[1] if len(sys.argv) > 1 else "Animal"
    out_path = sys.argv[2] if len(sys.argv) > 2 else f"preview-{category.lower()}.png"
    if category not in TRAITS:
        sys.exit(f"unknown category {category!r}; pick from {list(TRAITS)}")

    placements = generate.load_placements()
    variants = [t.name for t in TRAITS[category]]
    rows = (len(variants) + COLS - 1) // COLS
    sheet = Image.new("RGB", (COLS * THUMB, rows * THUMB), (30, 30, 40))
    for i, name in enumerate(variants):
        assignment = dict(BASE)
        assignment[category] = name
        img = generate.render(assignment, placements).resize(
            (THUMB, THUMB), Image.NEAREST)
        sheet.paste(img, ((i % COLS) * THUMB, (i // COLS) * THUMB))
    sheet.save(out_path)
    print(f"saved {out_path}: {variants}")


if __name__ == "__main__":
    main()
