"""V4 prototype — chunky trading-desk pixel cats, HD grid.

Usage: python v4_generate.py [--count 16] [--seed 7] [--out v4-output]

64x64 grid (16px cells at 1024): round-skulled cats with huge glossy
eyes, suit and tie, ticker-digit backgrounds and a chart line that goes
up or down. Flat color boundaries, no outline ring.
Writes images/ and contact-sheet.png.
"""

import argparse
import math
import random
from pathlib import Path

from PIL import Image

G = 64
SCALE = 16          # 1024px output
M = 63              # mirror
INKEYE = (18, 16, 22)
WHITE = (250, 250, 252)
SHIRT = (245, 244, 248)
NOSE = (216, 120, 110)
NOSE_DK = (188, 96, 90)
EARPINK = (214, 128, 106)
EARPINK_DK = (182, 100, 84)


class C:
    def __init__(self, fill):
        self.g = [[fill] * G for _ in range(G)]

    def px(self, x, y, c):
        if 0 <= x < G and 0 <= y < G:
            self.g[y][x] = c

    def row(self, y, x0, x1, c):
        for x in range(x0, x1 + 1):
            self.px(x, y, c)

    def rect(self, x0, y0, x1, y1, c):
        for y in range(y0, y1 + 1):
            self.row(y, x0, x1, c)

    def ell(self, cx, cy, rx, ry, c):
        for y in range(cy - ry, cy + ry + 1):
            hw = rx * math.sqrt(max(0.0, 1 - ((y - cy) / (ry + 0.5)) ** 2))
            self.row(y, round(cx - hw), round(cx + hw), c)

    def img(self):
        im = Image.new("RGB", (G, G))
        im.putdata([c for row in self.g for c in row])
        return im.resize((G * SCALE,) * 2, Image.NEAREST)


# ------------------------------------------------------------ backdrops

GREEN_C = (74, 214, 128)
RED_C = (226, 64, 58)


def bg_candles(grid, green=GREEN_C, red=RED_C):
    def draw(c, rng):
        for y in (6, 14, 22, 30):                    # gridlines
            c.row(y, 0, G - 1, grid)
        x = rng.randint(0, 2)
        while x < G - 3:
            top = rng.randint(3, 16)
            bot = top + rng.randint(4, 12)
            up = rng.random() < 0.5
            col = green if up else red
            c.rect(x, top, x + 2, min(bot, 31), col)
            c.px(x + 1, max(0, top - rng.randint(1, 3)), col)   # wick
            c.px(x + 1, top - 1, col)
            c.px(x + 1, min(33, bot + rng.randint(1, 2)), col)
            x += rng.randint(4, 6)
    return draw


def bg_area(grid, line, fill):
    def draw(c, rng):
        for y in range(4, 34, 6):                    # dotted gridlines
            for x in range(0, G, 3):
                c.px(x, y, grid)
        y = rng.randint(12, 22)
        for x in range(G):                           # meandering area chart
            y = max(3, min(28, y + rng.choice((-2, -1, -1, 0, 0, 1, 1, 2))))
            c.rect(x, y, x, y + 1, line)
            for fy in range(y + 2, 32):
                c.px(x, fy, fill)
    return draw


def bg_board(cell, digits, green=GREEN_C, red=RED_C):
    def draw(c, rng):
        for gy in range(2, 34, 7):                   # board rows of cells
            for gx in range(1, G - 9, 11):
                c.rect(gx, gy, gx + 8, gy + 4, cell)
                for _ in range(rng.randint(2, 3)):   # digit fragments
                    sx = gx + 1 + rng.randint(0, 4)
                    c.rect(sx, gy + 1 + rng.randint(0, 2),
                           sx + rng.randint(0, 1), gy + 1 + rng.randint(0, 2),
                           digits)
                up = rng.random() < 0.5              # up/down arrow
                ax = gx + 7
                col = green if up else red
                if up:
                    c.px(ax, gy + 1, col); c.row(gy + 2, ax - 1, ax + 1, col)
                else:
                    c.row(gy + 2, ax - 1, ax + 1, col); c.px(ax, gy + 3, col)
    return draw


def bg_skyline(tower, window, star):
    def draw(c, rng):
        for _ in range(14):                          # stars
            c.px(rng.randint(0, G - 1), rng.randint(0, 20), star)
        mx = rng.randint(38, 56)                     # moon
        c.rect(mx, 3, mx + 3, 6, star)
        for x0, w in ((0, 6), (5, 5), (52, 5), (58, 6)):   # edge towers
            h = rng.randint(24, 40)
            c.rect(x0, G - h, x0 + w - 1, G - 1, tower)
            for wy in range(G - h + 2, G - 2, 3):    # lit windows
                for wx in range(x0 + 1, x0 + w - 1, 2):
                    if rng.random() < 0.5:
                        c.px(wx, wy, window)
    return draw


def bg_coins(coin, rim, shine):
    def draw(c, rng):
        for _ in range(11):
            x = rng.randint(1, G - 6)
            y = rng.randint(1, 34)
            c.rect(x + 1, y, x + 3, y + 4, coin)
            c.rect(x, y + 1, x + 4, y + 3, coin)
            c.px(x + 3, y + 3, rim); c.px(x + 4, y + 3, rim)
            c.px(x + 3, y + 4, rim)
            c.px(x + 1, y + 1, shine)
        for _ in range(6):                           # tiny far coins
            x, y = rng.randint(1, G - 3), rng.randint(1, 30)
            c.rect(x, y, x + 1, y + 1, coin)
    return draw


BACKDROPS = [
    ("candles navy", (24, 32, 86), bg_candles((44, 54, 120))),
    ("candles charcoal", (32, 30, 40), bg_candles((56, 52, 70))),
    ("area violet", (66, 48, 112),
     bg_area((92, 72, 150), (64, 198, 188), (84, 64, 136))),
    ("area green", (16, 72, 50),
     bg_area((36, 100, 72), (240, 210, 90), (26, 90, 64))),
    ("board blue", (20, 28, 70),
     bg_board((36, 48, 104), (96, 116, 196))),
    ("skyline midnight", (18, 20, 44),
     bg_skyline((38, 42, 78), (244, 198, 74), (200, 205, 235))),
    ("coins plum", (58, 34, 80),
     bg_coins((238, 190, 70), (190, 140, 44), (252, 232, 160))),
]

COATS = [
    ("orange tabby", (242, 166, 66), (198, 118, 40), (250, 233, 202), True),
    ("gray tabby", (178, 180, 192), (130, 132, 148), (240, 240, 245), True),
    ("black", (62, 60, 68), (44, 42, 50), (156, 154, 164), True),
    ("cream", (244, 232, 205), (215, 197, 162), (252, 247, 234), True),
    ("white", (240, 240, 243), (218, 218, 224), (250, 250, 252), False),
    ("sky", (137, 196, 232), (100, 160, 206), (226, 241, 250), False),
]

SUITS = [
    ("black", (28, 27, 33), (48, 46, 56)),
    ("navy", (44, 62, 110), (60, 82, 138)),
    ("burgundy", (108, 38, 50), (134, 54, 68)),
]

TIES = [("black", (16, 15, 20)), ("red", (198, 48, 44)),
        ("gold", (238, 190, 70))]

EYESTYLES = ["wide", "lidded"]
MOUTHS = ["frown", "line", "smile"]


# ------------------------------------------------------------ drawing

def draw_cat(c, coat, suit, tiecol, eyestyle, mouth):
    name, fur, stripe, muzzle, striped = coat
    _, scol, lapel = suit

    # ears: wide and chunky, near-vertical outer edge, big inner patch
    ear = [(4, 14, 16), (5, 13, 18), (6, 13, 20), (7, 12, 21), (8, 12, 23),
           (9, 12, 24), (10, 12, 25), (11, 12, 26), (12, 12, 26),
           (13, 12, 27), (14, 12, 27), (15, 12, 28)]
    for y, x0, x1 in ear:
        c.row(y, x0, x1, fur)
        c.row(y, M - x1, M - x0, fur)
    inner = [(6, 15, 18), (7, 14, 19), (8, 14, 21), (9, 14, 22),
             (10, 14, 23), (11, 14, 24), (12, 14, 24), (13, 14, 25)]
    for y, x0, x1 in inner:
        c.row(y, x0, x1, EARPINK)
        c.row(y, M - x1, M - x0, EARPINK)
        c.px(x1, y, EARPINK_DK)                 # shaded inner edge
        c.px(M - x1, y, EARPINK_DK)
    for y, x0, x1 in ear[2:]:                   # dark rim toward the center
        c.px(x1, y, stripe if striped else fur)
        c.px(M - x1, y, stripe if striped else fur)

    # head: flat top, stepped corners, straight sides — angular skull
    c.row(16, 20, 43, fur)
    c.row(17, 18, 45, fur)
    c.row(18, 17, 46, fur)
    c.rect(16, 19, 47, 38, fur)
    for y, inset in ((39, 1), (40, 1), (41, 2), (42, 3), (43, 5), (44, 8)):
        c.row(y, 16 + inset, 47 - inset, fur)

    if striped:
        c.rect(29, 16, 34, 24, stripe)          # broad center stripe
        c.rect(24, 16, 25, 22, stripe)          # flanking bars
        c.rect(38, 16, 39, 22, stripe)
        c.rect(16, 26, 18, 27, stripe)          # temple dashes
        c.rect(45, 26, 47, 27, stripe)
        c.px(16, 33, stripe); c.px(47, 33, stripe)
        c.px(17, 21, stripe); c.px(46, 21, stripe)

    # eyes: huge, rounded corners, double shine
    for ex in (21, 36):
        c.rect(ex, 25, ex + 6, 33, INKEYE)
        for dx, dy in ((0, 0), (6, 0), (0, 8), (6, 8)):
            c.px(ex + dx, 25 + dy, fur)         # rounded corner nick
        c.rect(ex + 1, 26, ex + 2, 27, WHITE)
        c.px(ex + 5, 31, (168, 166, 178))
    if eyestyle == "lidded":
        c.rect(21, 25, 27, 27, fur)
        c.rect(36, 25, 42, 27, fur)
        c.row(28, 21, 27, stripe if striped else fur)
        c.row(28, 36, 42, stripe if striped else fur)

    # muzzle, nose, mouth
    c.ell(31, 39, 8, 5, muzzle)
    c.rect(29, 35, 33, 36, NOSE)
    c.row(37, 30, 32, NOSE_DK)
    if mouth == "frown":
        c.row(41, 28, 35, INKEYE)
        c.px(27, 42, INKEYE); c.px(36, 42, INKEYE)
    elif mouth == "line":
        c.row(41, 28, 35, INKEYE)
    else:
        c.row(41, 28, 35, INKEYE)
        c.px(27, 40, INKEYE); c.px(36, 40, INKEYE)

    # collar band + suit
    c.row(45, 22, 41, SHIRT)
    c.row(46, 21, 42, SHIRT)
    rows = [(47, 18, 45), (48, 14, 49), (49, 11, 52), (50, 8, 55),
            (51, 6, 57), (52, 5, 58)]
    for y, x0, x1 in rows:
        c.row(y, x0, x1, scol)
    c.rect(4, 53, 59, 63, scol)
    # lapels
    for i in range(6):
        c.rect(24 - i, 47 + i, 25 - i, 47 + i, lapel)
        c.rect(38 + i, 47 + i, 39 + i, 47 + i, lapel)
    # shirt V + collar wings
    c.rect(27, 47, 36, 47, SHIRT)
    c.rect(28, 48, 35, 49, SHIRT)
    c.rect(29, 50, 34, 51, SHIRT)
    c.rect(30, 52, 33, 53, SHIRT)
    c.px(26, 47, SHIRT); c.px(37, 47, SHIRT)
    # tie: knot + blade + taper
    c.rect(29, 47, 34, 49, tiecol)
    c.rect(30, 50, 33, 60, tiecol)
    c.rect(31, 61, 32, 62, tiecol)


def make(rng):
    bname, base, draw_bg = rng.choice(BACKDROPS)
    coat = rng.choice(COATS)
    suit = rng.choice(SUITS)
    tie = rng.choice(TIES)
    eyestyle = rng.choice(EYESTYLES)
    mouth = rng.choice(MOUTHS)
    c = C(base)
    draw_bg(c, rng)
    draw_cat(c, coat, suit, tie[1], eyestyle, mouth)
    label = f"{coat[0]} / {suit[0]} suit / {tie[0]} tie / {bname}"
    return c.img(), label


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, default=16)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--out", default="v4-output")
    args = parser.parse_args()

    out = Path(args.out)
    (out / "images").mkdir(parents=True, exist_ok=True)
    rng = random.Random(args.seed)

    imgs = []
    for i in range(args.count):
        img, label = make(rng)
        img.save(out / "images" / f"{i + 1:04d}.png")
        imgs.append(img)
        print(f"{i + 1:04d}  {label}")

    cols = 4
    thumb = 300
    rows = math.ceil(len(imgs) / cols)
    sheet = Image.new("RGB", (cols * thumb, rows * thumb), (20, 19, 31))
    for i, im in enumerate(imgs):
        sheet.paste(im.resize((thumb, thumb), Image.NEAREST),
                    ((i % cols) * thumb, (i // cols) * thumb))
    sheet.save(out / "contact-sheet.png")
    print(f"done: {args.count} cats in {out}/")


if __name__ == "__main__":
    main()
