"""Render the simple 1500x500 MEOW INC X banner: flat background, the
featured editions in a row, gold logo on top.

Usage: python banner_simple.py [--out banner]

Reuses banner.py's character renderer (real editions, minus their
Background layer). Writes <out>/meow-inc-banner-simple-1500x500.png.
"""

import argparse
import json
from pathlib import Path

import config
from banner import CAST, Scene, render_character
from palette import GOLD

W, H = 375, 125
SCALE = 4
CHAR_SCALE = 2          # each character pixel covers 2x2 logical pixels

BG_DARK = (20, 19, 31)  # site background #14131f


def hex_color(s):
    s = s.lstrip("#")
    return tuple(int(s[i:i + 2], 16) for i in (0, 2, 4))


def blit_scaled(scene, layer, dx, dy, k):
    for y in range(layer.size):
        for x in range(layer.size):
            color = layer.grid[y][x]
            if color is not None:
                scene.rect(dx + x * k, dy + y * k,
                           dx + x * k + k - 1, dy + y * k + k - 1, color)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="banner")
    parser.add_argument("--src", default="output-3333")
    parser.add_argument("--bg", type=hex_color, default=BG_DARK,
                        help="background color, e.g. #232142")
    parser.add_argument("--text", type=hex_color, default=GOLD,
                        help="logo color, e.g. #f4c64a")
    parser.add_argument("--name", default="simple",
                        help="variant name used in the output filename")
    args = parser.parse_args()

    placements_path = Path(__file__).parent / config.PLACEMENTS_FILE
    placements = (json.loads(placements_path.read_text())
                  if placements_path.exists() else {})

    s = Scene(W, H)
    s.rect(0, 0, W - 1, H - 1, args.bg)

    label = "MEOW INC"
    tw = s.text_width(label, 4)
    s.text(label, (W - tw) // 2, 10, args.text, 4)

    box = config.LOGICAL_SIZE * CHAR_SCALE          # 64 logical px per character
    top = H - box                                   # bottom-anchored, like the NFTs
    for i, edition in enumerate(CAST):
        meta = json.loads((Path(args.src) / "metadata"
                           / f"{edition:04d}.json").read_text())
        assignment = {a["trait_type"]: a["value"] for a in meta["attributes"]}
        layer = render_character(assignment, placements)
        center = W * (2 * i + 1) // (2 * len(CAST))
        blit_scaled(s, layer, center - box // 2, top, CHAR_SCALE)

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    path = out / f"meow-inc-banner-{args.name}-1500x500.png"
    s.to_image(SCALE).save(path)
    print(f"wrote {path} ({W * SCALE}x{H * SCALE}), "
          f"editions {', '.join(f'#{e:04d}' for e in CAST)}")


if __name__ == "__main__":
    main()
