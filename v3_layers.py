"""V3 layer kit — smooth doodle base head + HD-pixel traits.

Usage: python v3_layers.py

Reads art-refs/base-head-cat.png (hand-drawn head, blue fill, dot eyes),
heals the dots out, whitens the fill, and tints it into coat heads.
All other layers (suits, eyes, mouths, hats, glasses, accessories) are
drawn as hard-edged pixel art on a 64-cell grid — the mixed style.
Writes v3-layers/ + manifest.json for the v3 editor.
"""

import json
from pathlib import Path

from PIL import Image, ImageDraw

CANVAS = 1024
GRID = 64
CELL = CANVAS // GRID
CH = (45, 43, 52)            # charcoal ink, matches the head outline
WHITE = (252, 252, 255)
SHIRT = (244, 242, 248)
NOSE = (238, 122, 118)
TONGUE = (247, 143, 152)

OUT = Path("v3-layers")

# face anchors in grid cells — set in main() from the detected dot eyes
EL, ER, EY = 25, 39, 35
MX = 32                      # face center column, from the anchors


# ------------------------------------------------------------ base head

FILL_V = 232          # value of the base's blue fill, for whitening


def load_base():
    """Heal out the baked-in dot eyes, whiten the blue fill for tinting,
    fit to canvas. Returns (canvas, (eyeL_px, eyeR_px, eyeY_px))."""
    im = Image.open("art-refs/base-head-cat.png").convert("RGBA")
    px = im.load()

    # tight interior window that holds only the two dot eyes
    clusters = {"L": [], "R": []}
    for y in range(470, 660):
        for x in range(340, 690):
            r, g, b, a = px[x, y]
            if a > 200 and max(r, g, b) < 90:
                clusters["L" if x < 512 else "R"].append((x, y))
    anchors = {}
    fill = (137, 196, 232, 255)
    d = ImageDraw.Draw(im)
    for side, pts in clusters.items():
        cx = sum(p[0] for p in pts) / len(pts)
        cy = sum(p[1] for p in pts) / len(pts)
        # drop outliers (stray outline pixels), recompute, cap the radius
        pts = [p for p in pts
               if ((p[0] - cx) ** 2 + (p[1] - cy) ** 2) ** 0.5 < 50]
        cx = sum(p[0] for p in pts) / len(pts)
        cy = sum(p[1] for p in pts) / len(pts)
        rad = min(45, max(((p[0] - cx) ** 2 + (p[1] - cy) ** 2) ** 0.5
                          for p in pts))
        anchors[side] = (cx, cy)
        d.ellipse([cx - rad - 6, cy - rad - 6, cx + rad + 6, cy + rad + 6],
                  fill=fill)

    for y in range(im.height):
        for x in range(im.width):
            r, g, b, a = px[x, y]
            if a:
                v = min(255, round(max(r, g, b) * 255 / FILL_V))
                px[x, y] = (v, v, v, a)

    bbox = im.getbbox()
    im = im.crop(bbox)
    scale = min(780 / im.width, 720 / im.height)
    im = im.resize((round(im.width * scale), round(im.height * scale)),
                   Image.LANCZOS)
    ox = (CANVAS - im.width) // 2
    oy = (CANVAS - im.height) // 2 + 20   # centered, sitting slightly low
    canvas = Image.new("RGBA", (CANVAS, CANVAS), (0, 0, 0, 0))
    canvas.paste(im, (ox, oy), im)

    def map_pt(p):
        return (round((p[0] - bbox[0]) * scale) + ox,
                round((p[1] - bbox[1]) * scale) + oy)

    (lx, ly), (rx, ry) = map_pt(anchors["L"]), map_pt(anchors["R"])
    return canvas, (lx, rx, round((ly + ry) / 2))


def tint(base, color):
    out = base.copy()
    px = out.load()
    r2, g2, b2 = color
    for y in range(out.height):
        for x in range(out.width):
            r, g, b, a = px[x, y]
            if a:
                px[x, y] = (r * r2 // 255, g * g2 // 255, b * b2 // 255, a)
    return out


COATS = [
    ("sky", (137, 196, 232)),      # the original design's blue
    ("white", (255, 255, 255)),
    ("pink", (246, 158, 182)),
    ("tabby", (247, 184, 110)),
    ("gray", (196, 198, 212)),
    ("cream", (249, 240, 224)),
    ("mint", (166, 220, 186)),
    ("lavender", (196, 172, 232)),
]


# ------------------------------------------------------------ suit

SUIT_TOP = 47                # collar top row (cells), set after normalizing


def load_suit():
    """base-suit.png: key out the baked-in checkerboard background by
    flood-fill from the borders, then normalize to the canvas bottom."""
    im = Image.open("art-refs/base-suit.png").convert("RGBA")
    px = im.load()
    w, h = im.size

    def is_bg(p):
        r, g, b, a = p
        return a > 200 and r > 215 and g > 215 and b > 215

    stack = ([(x, 0) for x in range(w)] + [(x, h - 1) for x in range(w)]
             + [(0, y) for y in range(h)] + [(w - 1, y) for y in range(h)])
    seen = set()
    while stack:
        x, y = stack.pop()
        if (x, y) in seen or not (0 <= x < w and 0 <= y < h):
            continue
        seen.add((x, y))
        if not is_bg(px[x, y]):
            continue
        px[x, y] = (0, 0, 0, 0)
        stack.extend(((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)))

    bbox = im.getbbox()
    im = im.crop(bbox)
    scale = 720 / im.width
    im = im.resize((720, round(im.height * scale)), Image.LANCZOS)
    canvas = Image.new("RGBA", (CANVAS, CANVAS), (0, 0, 0, 0))
    canvas.paste(im, ((CANVAS - 720) // 2, CANVAS - im.height), im)
    return canvas, (CANVAS - im.height) // CELL


def suit_variant(base, color):
    """Recolor the key-green jacket; the white shirt and outline stay."""
    out = base.copy()
    px = out.load()
    r2, g2, b2 = color
    for y in range(out.height):
        for x in range(out.width):
            r, g, b, a = px[x, y]
            if a and g > r + 20 and g > b + 20:
                v = g / 200
                px[x, y] = (min(255, round(r2 * v)), min(255, round(g2 * v)),
                            min(255, round(b2 * v)), a)
    return out


SUIT_COLORS = [
    ("green", None),               # the original key color, kept as-is
    ("navy", (66, 90, 142)),
    ("burgundy", (150, 60, 76)),
    ("mustard", (234, 178, 76)),
    ("lavender", (172, 148, 216)),
    ("black", (70, 68, 80)),
]


def shirt_variant(suit_base, color):
    """The keying removed the shirt (it connects to the background through
    the neck opening), so rebuild it: fill every transparent gap that is
    horizontally enclosed by suit pixels. Rendered UNDER the suit, this
    fills the collar V and neck opening exactly."""
    out = Image.new("RGBA", suit_base.size, (0, 0, 0, 0))
    src = suit_base.load()
    dst = out.load()
    w, h = suit_base.size
    for y in range(h):
        xs = [x for x in range(w) if src[x, y][3] > 40]
        if len(xs) < 2:
            continue
        left, right = xs[0], xs[-1]
        run = 0
        for x in range(left, right + 1):
            if src[x, y][3] <= 40:
                run += 1
            else:
                if 0 < run <= 460:
                    for fx in range(x - run, x):
                        dst[fx, y] = color + (255,)
                run = 0
    return out


SHIRT_COLORS = [
    ("white", (252, 252, 255)),
    ("sky", (170, 206, 240)),
    ("butter", (248, 222, 140)),
    ("pink", (248, 184, 200)),
    ("mint", (180, 226, 196)),
]


# ------------------------------------------------------- pixel layers

class Pix:
    def __init__(self):
        self.g = {}

    def px(self, x, y, c):
        if 0 <= x < GRID and 0 <= y < GRID:
            self.g[(x, y)] = c

    def row(self, y, x0, x1, c):
        for x in range(x0, x1 + 1):
            self.px(x, y, c)

    def col(self, x, y0, y1, c):
        for y in range(y0, y1 + 1):
            self.px(x, y, c)

    def rect(self, x0, y0, x1, y1, c):
        for y in range(y0, y1 + 1):
            self.row(y, x0, x1, c)

    def outline(self):
        ring = []
        for (x, y) in list(self.g):
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                if (x + dx, y + dy) not in self.g:
                    ring.append((x + dx, y + dy))
        for p in ring:
            if 0 <= p[0] < GRID and 0 <= p[1] < GRID:
                self.g[p] = CH

    def save(self, name):
        im = Image.new("RGBA", (GRID, GRID), (0, 0, 0, 0))
        for (x, y), c in self.g.items():
            im.putpixel((x, y), c + (255,))
        im.resize((CANVAS, CANVAS), Image.NEAREST).save(OUT / name)
        return name


def tie(name, color, dark):
    c = Pix()
    k = SUIT_TOP + 6                 # knot sits in the collar dip
    c.rect(MX - 2, k, MX + 2, k + 2, color)
    c.px(MX - 2, k, dark); c.px(MX + 2, k + 2, dark)
    for i, y in enumerate(range(k + 3, GRID)):
        half = 2 if 1 <= i <= 6 else 1
        c.row(y, MX - half, MX + half, color)
        c.px(MX + half, y, dark)
    c.outline()
    return c.save(f"tie-{name}.png")


TIES = [
    ("gold", (246, 200, 78), (206, 158, 52)),
    ("red", (224, 86, 78), (182, 62, 56)),
    ("teal", (68, 200, 190), (48, 158, 150)),
    ("magenta", (216, 92, 168), (174, 66, 132)),
]


def eyes_dots():
    c = Pix()
    for x in (EL, ER):
        c.rect(x, EY, x + 1, EY + 1, CH)
    return c.save("eyes-dots.png")


def eyes_bead():
    c = Pix()
    for x in (EL, ER):
        c.rect(x - 1, EY - 2, x + 2, EY + 3, CH)
        c.rect(x - 1, EY - 1, x, EY, WHITE)
        c.px(x + 2, EY + 2, (214, 210, 226))
    return c.save("eyes-bead.png")


def eyes_squint():
    c = Pix()
    for x in (EL, ER):
        for dx, dy in ((-3, 1), (-2, 0), (-1, -1), (0, -1), (1, -1), (2, 0), (3, 1)):
            c.px(x + dx, EY + dy, CH)
            c.px(x + dx, EY + dy + 1, CH)
    return c.save("eyes-squint.png")


def eyes_wink():
    c = Pix()
    c.rect(EL - 1, EY - 2, EL + 2, EY + 3, CH)
    c.rect(EL - 1, EY - 1, EL, EY, WHITE)
    for dx, dy in ((-3, 1), (-2, 0), (-1, -1), (0, -1), (1, -1), (2, 0), (3, 1)):
        c.px(ER + dx, EY + dy, CH)
        c.px(ER + dx, EY + dy + 1, CH)
    return c.save("eyes-wink.png")


def eyes_sleepy():
    c = Pix()
    for x in (EL, ER):
        c.row(EY, x - 3, x + 3, CH)
        c.row(EY + 1, x - 3, x + 3, CH)
        c.px(x - 3, EY + 2, CH)
        c.px(x + 3, EY + 2, CH)
    return c.save("eyes-sleepy.png")


def _nose(c, ny):
    c.row(ny, MX - 1, MX + 1, NOSE)
    c.px(MX, ny + 1, (208, 96, 92))


def mouth_smile():
    c = Pix()
    _nose(c, EY + 4)
    y = EY + 7
    for dx, dy in ((-4, 0), (-3, 1), (-2, 1), (-1, 0), (0, 0), (1, 1), (2, 1), (3, 0)):
        c.px(MX + dx, y + dy, CH)
    return c.save("mouth-smile.png")


def mouth_grin():
    c = Pix()
    _nose(c, EY + 4)
    y = EY + 7
    c.row(y, MX - 4, MX + 4, CH)
    c.row(y + 1, MX - 3, MX + 3, CH)
    c.row(y + 2, MX - 2, MX + 2, CH)
    c.row(y + 2, MX - 1, MX + 1, TONGUE)
    c.row(y + 3, MX - 1, MX + 1, TONGUE)
    return c.save("mouth-grin.png")


def mouth_blep():
    c = Pix()
    _nose(c, EY + 4)
    y = EY + 7
    for dx, dy in ((-4, 0), (-3, 1), (-2, 1), (-1, 0), (0, 0), (1, 1), (2, 1), (3, 0)):
        c.px(MX + dx, y + dy, CH)
    c.rect(MX - 2, y + 2, MX + 1, y + 5, TONGUE)
    c.px(MX - 2, y + 5, (222, 110, 116)); c.px(MX + 1, y + 5, (222, 110, 116))
    c.outline()
    return c.save("mouth-blep.png")


def mouth_line():
    c = Pix()
    _nose(c, EY + 4)
    c.row(EY + 8, MX - 3, MX + 3, CH)
    return c.save("mouth-line.png")


def blush():
    c = Pix()
    c.rect(EL - 7, EY + 4, EL - 5, EY + 5, (246, 158, 150))
    c.rect(ER + 5, EY + 4, ER + 7, EY + 5, (246, 158, 150))
    return c.save("blush.png")


def glasses_round(name, color):
    c = Pix()
    ring = ((-3, -2), (-2, -3), (-1, -4), (0, -4), (1, -4), (2, -3), (3, -2),
            (4, -1), (4, 0), (4, 1), (3, 2), (2, 3), (1, 4), (0, 4), (-1, 4),
            (-2, 3), (-3, 2), (-4, 1), (-4, 0), (-4, -1))
    for ex in (EL, ER):
        for dx, dy in ring:
            c.px(ex + dx, EY + dy, color)
    c.row(EY - 1, EL + 5, ER - 5, color)
    c.row(EY - 1, EL - 8, EL - 5, color)
    c.row(EY - 1, ER + 5, ER + 8, color)
    return c.save(f"glasses-{name}.png")


def glasses_shades():
    c = Pix()
    c.row(EY - 3, EL - 6, ER + 6, CH)
    for ex in (EL, ER):
        c.rect(ex - 4, EY - 2, ex + 4, EY, CH)
        c.rect(ex - 3, EY + 1, ex + 3, EY + 1, CH)
        c.rect(ex - 2, EY + 2, ex + 2, EY + 2, CH)
        c.px(ex - 2, EY - 1, (120, 118, 132))
    c.row(EY - 2, EL - 8, EL - 6, CH)
    c.row(EY - 2, ER + 6, ER + 8, CH)
    return c.save("glasses-shades.png")


BACKGROUNDS = [
    ("periwinkle", "#9aa4ea"), ("plasma violet", "#7e60ac"),
    ("mint", "#a8dcc0"), ("rose", "#e8a0b4"), ("butter", "#f2d488"),
    ("sky", "#a9c8ee"), ("charcoal", "#3a3846"),
    ("volt", "#ccff00"), ("tangerine", "#ff8c42"),
    ("hot pink", "#ff5c9e"), ("royal", "#4657d8"),
]


def main():
    global EL, ER, EY, MX, SUIT_TOP
    OUT.mkdir(exist_ok=True)
    base, (lx, rx, ey) = load_base()
    EL, ER, EY = round(lx / CELL), round(rx / CELL), round(ey / CELL)
    MX = round((EL + ER) / 2)
    suit_base, SUIT_TOP = load_suit()
    print(f"anchors (cells): L={EL} R={ER} Y={EY} center={MX} "
          f"suit_top={SUIT_TOP}")

    heads = []
    for name, color in COATS:
        img = tint(base, color) if name != "white" else base
        img.save(OUT / f"head-{name}.png")
        heads.append({"name": name, "file": f"head-{name}.png"})
        print(f"head-{name}.png")

    suits = []
    for name, color in SUIT_COLORS:
        img = suit_base if color is None else suit_variant(suit_base, color)
        img.save(OUT / f"suit-{name}.png")
        suits.append({"name": name, "file": f"suit-{name}.png"})
        print(f"suit-{name}.png")

    shirts = []
    for name, color in SHIRT_COLORS:
        shirt_variant(suit_base, color).save(OUT / f"shirt-{name}.png")
        shirts.append({"name": name, "file": f"shirt-{name}.png"})
        print(f"shirt-{name}.png")

    cats = [
        {"name": "Shirt", "optional": False, "layers": shirts},
        {"name": "Suit", "optional": False, "layers": suits},
        {"name": "Tie", "optional": True,
         "layers": [{"name": n, "file": tie(n, c_, d)} for n, c_, d in TIES]},
        {"name": "Head", "optional": False, "layers": heads},
        {"name": "Eyes", "optional": False, "layers": [
            {"name": "dots", "file": eyes_dots()},
            {"name": "bead", "file": eyes_bead()},
            {"name": "squint", "file": eyes_squint()},
            {"name": "wink", "file": eyes_wink()},
            {"name": "sleepy", "file": eyes_sleepy()}]},
        {"name": "Mouth", "optional": False, "layers": [
            {"name": "smile", "file": mouth_smile()},
            {"name": "grin", "file": mouth_grin()},
            {"name": "blep", "file": mouth_blep()},
            {"name": "line", "file": mouth_line()}]},
        {"name": "Blush", "optional": True,
         "layers": [{"name": "blush", "file": blush()}]},
        {"name": "Glasses", "optional": True, "layers": [
            {"name": "round-lavender", "file": glasses_round("round-lavender", (168, 146, 224))},
            {"name": "round-gold", "file": glasses_round("round-gold", (226, 178, 76))},
            {"name": "shades", "file": glasses_shades()}]},
    ]

    manifest = {
        "canvas": CANVAS,
        "backgrounds": [{"name": n, "color": c} for n, c in BACKGROUNDS],
        "categories": cats,
    }
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2))
    n_layers = sum(len(c["layers"]) for c in cats)
    print(f"manifest.json — {n_layers} layers across {len(cats)} categories")


if __name__ == "__main__":
    main()
