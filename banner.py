"""Render the 1500x500 MEOW INC X banner from real collection editions.

Usage: python banner.py [--out banner]

Draws a night office with a space window on a 300x100 logical grid
(scaled x5, same hard-pixel rules as the collection) and seats real
editions — rendered from their exact trait combos, minus the Background
layer — at their desks. Writes <out>/meow-inc-banner-1500x500.png.
"""

import argparse
import json
from pathlib import Path

from PIL import Image

import config
from canvas import PixelCanvas
from palette import GOLD, TEAL, INK
from traits import TRAITS, CHARACTER_ORDER

# featured editions (edition number -> desk order, one per species;
# re-picked after the office-wing background regen)
CAST = [1, 6, 13, 93, 57]

W, H = 300, 100
SCALE = 5

# scene palette — site theme colors plus collection accents
CEIL = (38, 37, 56)
WALL = (30, 29, 46)
LINE = (53, 51, 77)
SPACE = (20, 19, 31)
FLOOR = (26, 25, 40)
SEAM = (36, 35, 54)
STAR = (205, 208, 228)
STAR_DIM = (120, 122, 150)
NEB = (206, 140, 162)
NEB_DEEP = (150, 96, 122)
PLANET = TEAL
PLANET_SHADE = (44, 148, 140)
GOLD_DIM = (170, 132, 48)
OFFWHITE = (232, 230, 240)
DESK = (48, 46, 72)
DESK_TOP = (66, 63, 96)
CRT = (34, 33, 52)
CRT_EDGE = (53, 51, 77)
MUG = (222, 70, 66)
PAPER = (232, 230, 240)
PLANT = (84, 160, 110)
PLANT_DARK = (58, 118, 80)
POT = (128, 88, 50)

FONT = {
    "M": ["X...X", "XX.XX", "X.X.X", "X.X.X", "X...X", "X...X", "X...X"],
    "E": ["XXXX", "X...", "X...", "XXX.", "X...", "X...", "XXXX"],
    "O": [".XX.", "X..X", "X..X", "X..X", "X..X", "X..X", ".XX."],
    "W": ["X...X", "X...X", "X...X", "X.X.X", "X.X.X", "XX.XX", "X...X"],
    "I": ["XXX", ".X.", ".X.", ".X.", ".X.", ".X.", "XXX"],
    "N": ["X...X", "XX..X", "XX..X", "X.X.X", "X..XX", "X..XX", "X...X"],
    "C": [".XXX", "X...", "X...", "X...", "X...", "X...", ".XXX"],
    " ": ["...", "...", "...", "...", "...", "...", "..."],
}


class Scene:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.grid = [[SPACE] * w for _ in range(h)]

    def px(self, x, y, color):
        if 0 <= x < self.w and 0 <= y < self.h:
            self.grid[y][x] = color

    def row(self, y, x0, x1, color):
        for x in range(x0, x1 + 1):
            self.px(x, y, color)

    def col(self, x, y0, y1, color):
        for y in range(y0, y1 + 1):
            self.px(x, y, color)

    def rect(self, x0, y0, x1, y1, color):
        for y in range(y0, y1 + 1):
            self.row(y, x0, x1, color)

    def blit_layer(self, layer, dx, dy):
        for y in range(layer.size):
            for x in range(layer.size):
                color = layer.grid[y][x]
                if color is not None:
                    self.px(x + dx, y + dy, color)

    def text(self, s, x, y, color, scale=2):
        cx = x
        for ch in s:
            glyph = FONT[ch]
            for gy, rowstr in enumerate(glyph):
                for gx, cell in enumerate(rowstr):
                    if cell == "X":
                        self.rect(cx + gx * scale, y + gy * scale,
                                  cx + gx * scale + scale - 1,
                                  y + gy * scale + scale - 1, color)
            cx += (len(glyph[0]) + 1) * scale
        return cx - scale  # right edge

    def text_width(self, s, scale=2):
        return sum((len(FONT[ch][0]) + 1) * scale for ch in s) - scale

    def to_image(self, scale):
        img = Image.new("RGB", (self.w, self.h))
        img.putdata([c for row in self.grid for c in row])
        return img.resize((self.w * scale, self.h * scale), Image.NEAREST)


# ------------------------------------------------------------ characters

def trait_by_name(category, name):
    for t in TRAITS[category]:
        if t.name == name:
            return t
    raise KeyError(f"{category}/{name}")


def render_character(assignment, placements):
    """The collection's render() minus the Background layer: transparent."""
    animal = assignment["Animal"]
    c = PixelCanvas(config.LOGICAL_SIZE)
    for cat in CHARACTER_ORDER:
        t = trait_by_name(cat, assignment[cat])
        if not t.draw:
            continue
        layer = PixelCanvas(config.LOGICAL_SIZE)
        t.draw(layer)
        dx, dy = placements.get(animal, {}).get(cat, {}).get(t.name, (0, 0))
        c.blit(layer, dx, dy)
    c.outline_ring(INK)
    return c


def load_cast(out_dir):
    placements_path = Path(__file__).parent / config.PLACEMENTS_FILE
    placements = (json.loads(placements_path.read_text())
                  if placements_path.exists() else {})
    cast = []
    for edition in CAST:
        meta = json.loads(
            (out_dir / "metadata" / f"{edition:04d}.json").read_text())
        assignment = {a["trait_type"]: a["value"] for a in meta["attributes"]}
        cast.append(render_character(assignment, placements))
    return cast


# ------------------------------------------------------------ scene parts

def draw_window(s):
    s.rect(0, 0, W - 1, 2, CEIL)                    # ceiling strip
    s.row(3, 0, W - 1, LINE)
    s.rect(0, 4, W - 1, 44, SPACE)                  # space behind glass

    # nebula band sweeping lower-left to upper-right
    for x in range(0, W):
        y = 38 - x // 6
        for dy, color in ((0, NEB_DEEP), (1, NEB), (2, NEB), (3, NEB_DEEP)):
            yy = y + dy
            if 5 <= yy <= 43 and (x + yy) % 7 != 0:   # ragged edge
                s.px(x, yy, color)

    stars = [(9, 8), (21, 30), (34, 12), (52, 39), (63, 7), (77, 22),
             (93, 33), (104, 10), (118, 40), (131, 6), (146, 27), (158, 12),
             (172, 38), (185, 8), (198, 30), (214, 14), (228, 41), (240, 9),
             (256, 24), (269, 37), (281, 11), (292, 31), (46, 18), (137, 35),
             (205, 6), (274, 20)]
    for i, (x, y) in enumerate(stars):
        s.px(x, y, STAR if i % 3 else STAR_DIM)
        if i % 4 == 0:                              # sparkle cross
            s.px(x - 1, y, STAR_DIM); s.px(x + 1, y, STAR_DIM)
            s.px(x, y - 1, STAR_DIM); s.px(x, y + 1, STAR_DIM)

    # teal planet, right side
    px_, py = 262, 16
    s.rect(px_ - 2, py - 4, px_ + 2, py + 4, PLANET)
    s.rect(px_ - 4, py - 2, px_ + 4, py + 2, PLANET)
    s.rect(px_ - 3, py - 3, px_ + 3, py + 3, PLANET)
    s.rect(px_ + 1, py - 2, px_ + 3, py + 2, PLANET_SHADE)
    s.px(px_ - 2, py - 2, OFFWHITE)

    # mullions and frame
    for x in (0, 74, 149, 224, W - 1):
        s.col(x, 4, 44, LINE)
        if x not in (0, W - 1):
            s.col(x + 1, 4, 44, LINE)
    s.row(44, 0, W - 1, LINE)
    s.row(45, 0, W - 1, CEIL)


def draw_sign(s):
    label = "MEOW INC"
    tw = s.text_width(label, 2)
    x0 = (W - tw) // 2 - 6
    x1 = (W + tw) // 2 + 6
    s.col(x0 + 8, 4, 9, GOLD_DIM)                   # hanging chains
    s.col(x1 - 8, 4, 9, GOLD_DIM)
    s.rect(x0, 10, x1, 31, GOLD)                    # gold border
    s.rect(x0 + 1, 11, x1 - 1, 30, SPACE)           # dark face
    s.text(label, (W - tw) // 2, 14, GOLD, 2)


def draw_wall_and_floor(s):
    s.rect(0, 46, W - 1, 73, WALL)
    s.row(74, 0, W - 1, LINE)                       # baseboard
    s.row(75, 0, W - 1, CEIL)
    s.rect(0, 76, W - 1, H - 1, FLOOR)
    for y in (82, 90, 98):                          # carpet tile seams
        s.row(y, 0, W - 1, SEAM)
    for x in range(10, W, 20):
        off = 10 if (x // 20) % 2 else 0
        s.col(x, 76 + (6 if off else 0), 81, SEAM)
    # wall accent lights
    for x in (12, 104, 194, 286):
        s.rect(x, 50, x + 1, 55, GOLD_DIM)
        s.px(x, 50, GOLD); s.px(x + 1, 50, GOLD)


def draw_desk(s, cx):
    """A desk in front of a character centered at logical x = cx."""
    x0, x1 = cx - 19, cx + 19
    s.rect(x0, 70, x1, 71, DESK_TOP)                # desktop
    s.rect(x0, 72, x1, 82, DESK)                    # front panel
    s.row(72, x0, x1, LINE)
    s.col(x0, 70, 82, INK); s.col(x1, 70, 82, INK)
    # CRT seen from behind, offset so the face stays clear
    mx = cx - 13
    s.rect(mx, 60, mx + 9, 69, CRT)
    s.col(mx, 60, 69, CRT_EDGE); s.col(mx + 9, 60, 69, CRT_EDGE)
    s.row(60, mx, mx + 9, CRT_EDGE)
    for y in (63, 65, 67):                          # vents
        s.row(y, mx + 2, mx + 7, CRT_EDGE)
    # papers and mug on the desk
    s.rect(cx + 8, 68, cx + 13, 69, PAPER)
    s.rect(cx + 15, 66, cx + 17, 69, MUG)
    s.px(cx + 18, 67, MUG)


def draw_side_props(s):
    # filing cabinet, far left
    s.rect(2, 50, 18, 73, CEIL)
    s.col(2, 50, 73, LINE); s.col(18, 50, 73, LINE); s.row(50, 2, 18, LINE)
    for y in (56, 62, 68):
        s.row(y, 3, 17, LINE)
        s.rect(8, y - 3, 12, y - 2, GOLD_DIM)       # drawer handles
    s.rect(6, 44, 14, 46, PLANT)                    # plant on top
    s.rect(7, 42, 9, 43, PLANT_DARK); s.rect(11, 41, 13, 43, PLANT)
    s.rect(8, 47, 12, 49, POT)
    # bookshelf, far right
    s.rect(281, 48, 297, 73, CEIL)
    s.col(281, 48, 73, LINE); s.col(297, 48, 73, LINE)
    s.row(48, 281, 297, LINE)
    for shelf_y in (56, 64, 72):
        s.row(shelf_y, 282, 296, LINE)
        bx = 283
        for w_, color in ((3, MUG), (2, TEAL), (3, GOLD_DIM), (2, OFFWHITE)):
            s.rect(bx, shelf_y - 6, bx + w_ - 1, shelf_y - 1, color)
            bx += w_ + 1


# ------------------------------------------------------------------ main

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="banner")
    parser.add_argument("--src", default="output-3333")
    args = parser.parse_args()

    cast = load_cast(Path(args.src))

    s = Scene(W, H)
    draw_window(s)
    draw_sign(s)
    draw_wall_and_floor(s)
    draw_side_props(s)

    desk_centers = [46, 96, 150, 204, 254]
    for layer, cx in zip(cast, desk_centers):
        s.blit_layer(layer, cx - 16, 46)            # character first...
    for cx in desk_centers:
        draw_desk(s, cx)                            # ...desk in front

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    path = out / "meow-inc-banner-1500x500.png"
    s.to_image(SCALE).save(path)
    print(f"wrote {path} ({W * SCALE}x{H * SCALE}), "
          f"editions {', '.join(f'#{e:04d}' for e in CAST)}")


if __name__ == "__main__":
    main()
