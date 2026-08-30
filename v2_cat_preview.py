"""V2 art prototype — smooth doodle cats (no pixels, no paws).

Usage: python v2_cat_preview.py [out.png]

Standalone: draws flat vector-style doodle cats with PIL shapes,
supersampled and downscaled for clean smooth edges. Three variants:
pink (happy squint), tabby (bead eyes + beanie), gray (glasses).
"""

import sys

from PIL import Image, ImageChops, ImageDraw

U = 256          # design space units per cat
SS = 6           # supersample: draw at 1536, ship at 768
OUT = 768
BG = (126, 96, 172)
INK = (34, 28, 44)
WHITE = (252, 252, 255)
SHIRT = (246, 244, 250)
PINKIN = (247, 172, 164)
NOSE = (236, 118, 114)
STROKE = 5       # outline thickness in design units


def S(v):
    return v * SS


class Doodle:
    def __init__(self):
        self.img = Image.new("RGB", (S(U), S(U)), BG)
        self.d = ImageDraw.Draw(self.img)

    def ell(self, cx, cy, rx, ry, fill):
        self.d.ellipse([S(cx - rx), S(cy - ry), S(cx + rx), S(cy + ry)], fill=fill)

    def rrect(self, x0, y0, x1, y1, r, fill):
        self.d.rounded_rectangle([S(x0), S(y0), S(x1), S(y1)], radius=S(r), fill=fill)

    def poly(self, pts, fill):
        self.d.polygon([(S(x), S(y)) for x, y in pts], fill=fill)

    def arc(self, x0, y0, x1, y1, a0, a1, width, fill=INK):
        self.d.arc([S(x0), S(y0), S(x1), S(y1)], a0, a1, fill=fill,
                   width=round(S(width)))

    def line(self, pts, width, fill=INK):
        p = [(S(x), S(y)) for x, y in pts]
        self.d.line(p, fill=fill, width=round(S(width)), joint="curve")
        r = width / 2
        for x, y in (pts[0], pts[-1]):               # round caps
            self.ell(x, y, r, r, fill)

    def ring(self, cx, cy, r, width, fill):
        self.d.ellipse([S(cx - r), S(cy - r), S(cx + r), S(cy + r)],
                       outline=fill, width=round(S(width)))

    def crescent(self, draw_fn, dx, dy, color):
        """Cel shadow: shape minus itself shifted (dx, dy)."""
        a = Image.new("L", self.img.size, 0)
        draw_fn(ImageDraw.Draw(a), 0, 0)
        b = Image.new("L", self.img.size, 0)
        draw_fn(ImageDraw.Draw(b), dx, dy)
        self.img.paste(color, (0, 0), ImageChops.subtract(a, b))

    def finish(self):
        return self.img.resize((OUT, OUT), Image.LANCZOS)


def inflate(pts, k=1.16):
    cx = sum(x for x, _ in pts) / len(pts)
    cy = sum(y for _, y in pts) / len(pts)
    return [((x - cx) * k + cx, (y - cy) * k + cy) for x, y in pts]


def mirror(pts):
    return [(U - x, y) for x, y in pts]


HEAD = (128, 110, 80, 68)        # cx, cy, rx, ry
EAR = [(54, 26), (62, 78), (112, 50)]   # tip, outer base, inner base
BODY = (50, 190, 206, 280, 40)   # x0, y0, x1, y1, corner radius
NECK = (88, 156, 168, 204)


def draw_cat(F, suit, tie, face="bead", beanie=None, glasses=None, flower=False):
    c = Doodle()
    fur, fsh = F["base"], F["shade"]
    s = STROKE

    # ---- ink silhouette underlay -> one clean uniform outline
    cx, cy, rx, ry = HEAD
    c.ell(cx, cy, rx + s, ry + s, INK)
    for pts in (EAR, mirror(EAR)):
        c.poly(inflate(pts), INK)
    c.rrect(NECK[0] - s, NECK[1], NECK[2] + s, NECK[3], 14, INK)
    x0, y0, x1, y1, r = BODY
    c.rrect(x0 - s, y0 - s, x1 + s, y1, r + s, INK)

    # ---- fur + body fills
    for pts in (EAR, mirror(EAR)):
        c.poly(pts, fur)
    c.rrect(*NECK, 14, fur)
    c.ell(128, 182, 42, 12, fsh)                     # chin shadow, neck only —
    c.ell(cx, cy, rx, ry, fur)                       # the head paints over it
    # head cel shadow: thin sliver along the lower-right edge
    c.crescent(lambda d, ox, oy: d.ellipse(
        [S(cx - rx + ox), S(cy - ry + oy), S(cx + rx + ox), S(cy + ry + oy)],
        fill=255), S(-4), S(-4), fsh)
    c.rrect(x0, y0, x1, y1, r, suit["base"])
    # body cel shadow along its lower-right shoulder
    c.crescent(lambda d, ox, oy: d.rounded_rectangle(
        [S(x0 + ox), S(y0 + oy), S(x1 + ox), S(y1 + oy)],
        radius=S(r), fill=255), S(-5), S(-5), suit["shade"])

    # inner ears: shaded base + lighter top
    for pts in (EAR, mirror(EAR)):
        inner = inflate(pts, 0.55)
        c.poly([(x, y + 10) for x, y in inner], F["earshade"])
        c.poly([(x, y + 7) for x, y in inflate(pts, 0.48)], PINKIN)

    # ---- coat markings
    if F.get("stripe"):
        for bx in (100, 148):
            c.rrect(bx, 88, bx + 10, 116, 5, F["stripe"])
        c.rrect(48, 128, 66, 137, 4.5, F["stripe"])
        c.rrect(190, 128, 208, 137, 4.5, F["stripe"])

    # ---- beanie: smooth dome + band, its own outline
    if beanie:
        c.rrect(70, 88, 186, 98, 5, fsh)             # brim shadow on the brow
        c.d.chord([S(66 - s), S(14 - s), S(190 + s), S(100 + s)], 180, 360, fill=INK)
        c.rrect(62 - s, 66 - s, 194 + s, 88 + s, 12, INK)
        c.d.chord([S(66), S(14), S(190), S(94)], 180, 360, fill=beanie["base"])
        c.crescent(lambda d, ox, oy: d.chord(
            [S(66 + ox), S(14 + oy), S(190 + ox), S(94 + oy)], 180, 360,
            fill=255), S(-5), S(-4), beanie["shade"])
        c.rrect(62, 66, 194, 88, 12, beanie["band"])
        c.ell(128, 15, 8, 8, beanie["band"])

    # ---- suit details
    c.poly([(112, 208), (144, 208), (128, 242)], SHIRT)          # shirt V
    c.poly([(112, 208), (96, 214), (120, 236)], suit["deep"])    # lapels
    c.poly([(144, 208), (160, 214), (136, 236)], suit["deep"])
    c.poly([(120, 210), (136, 210), (132, 222), (124, 222)], tie["base"])  # knot
    c.poly([(124, 222), (132, 222), (140, 262), (128, 276), (116, 262)], tie["base"])

    # ---- face, set low on the head for the cute read
    ex = (100, 156)
    if face == "squint":                             # happy closed eyes ∩∩
        for x in ex:
            c.arc(x - 16, 114, x + 16, 138, 195, 345, 7)
            c.ell(x - 14.5, 122.5, 3.5, 3.5, INK)
            c.ell(x + 14.5, 122.5, 3.5, 3.5, INK)
    else:                                            # soft bead eyes
        for x in ex:
            c.ell(x, 126, 9, 12, INK)
            c.ell(x - 3, 120.5, 3.6, 3.6, WHITE)
            c.ell(x + 3.5, 131, 1.8, 1.8, (216, 210, 228))

    if glasses:
        for x in ex:
            c.ring(x, 126, 21, 5, glasses)
        c.line([(121, 122), (135, 122)], 5, glasses)
        c.line([(52, 118), (79, 122)], 5, glasses)
        c.line([(177, 122), (204, 118)], 5, glasses)

    # nose: soft rounded triangle with a highlight
    c.poly([(120, 146), (136, 146), (128, 156)], NOSE)
    c.ell(128, 154, 4, 4, NOSE)
    c.d.ellipse([S(122), S(147), S(127), S(150)], fill=(250, 162, 156))

    # omega mouth
    c.arc(112, 152, 129, 168, 30, 165, 5)
    c.arc(127, 152, 144, 168, 15, 150, 5)

    # blush
    c.ell(70, 147, 12, 7, F["blush"])
    c.ell(186, 147, 12, 7, F["blush"])

    # whiskers
    for sx in (1, -1):
        mid = 128
        c.line([(mid - sx * 98, 123), (mid - sx * 72, 128)], 3.5)
        c.line([(mid - sx * 102, 139), (mid - sx * 72, 139)], 3.5)
        c.line([(mid - sx * 98, 154), (mid - sx * 72, 149)], 3.5)

    # ---- flower tucked behind one ear
    if flower:
        fx, fy = 148, 52
        for a in range(5):
            import math
            px_ = fx + 9.5 * math.cos(a * 1.2566 - 1.5708)
            py_ = fy + 9.5 * math.sin(a * 1.2566 - 1.5708)
            c.ell(px_, py_, 7.5 + 2, 7.5 + 2, INK)
        for a in range(5):
            import math
            px_ = fx + 9.5 * math.cos(a * 1.2566 - 1.5708)
            py_ = fy + 9.5 * math.sin(a * 1.2566 - 1.5708)
            c.ell(px_, py_, 7.5, 7.5, (250, 214, 226))
        c.ell(fx, fy, 5.5, 5.5, (246, 200, 78))

    return c.finish()


PINKY = {"base": (244, 146, 172), "shade": (222, 116, 148),
         "earshade": (224, 128, 128), "blush": (252, 196, 130)}
TABBY = {"base": (246, 178, 100), "shade": (222, 146, 70),
         "earshade": (226, 132, 122), "stripe": (216, 138, 62),
         "blush": (244, 136, 120)}
GRAY = {"base": (190, 192, 208), "shade": (162, 164, 184),
        "earshade": (222, 134, 130), "blush": (240, 150, 154)}

NAVY = {"base": (56, 78, 128), "shade": (46, 64, 106), "deep": (36, 52, 92)}
BURGUNDY = {"base": (140, 54, 68), "shade": (118, 44, 58), "deep": (100, 36, 50)}
FOREST = {"base": (60, 110, 78), "shade": (48, 92, 64), "deep": (38, 76, 52)}

GOLD_TIE = {"base": (246, 200, 78)}
RED_TIE = {"base": (224, 86, 78)}
TEAL_TIE = {"base": (68, 200, 190)}

BEANIE = {"base": (96, 136, 206), "shade": (80, 118, 184), "band": (62, 96, 162)}
GLASSES = (152, 130, 218)


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else "v2-cat-preview.png"
    variants = [
        (PINKY, NAVY, TEAL_TIE, "squint", None, None, True),
        (TABBY, BURGUNDY, GOLD_TIE, "bead", BEANIE, None, False),
        (GRAY, FOREST, RED_TIE, "bead", None, GLASSES, False),
    ]
    sheet = Image.new("RGB", (OUT * 3, OUT), BG)
    for i, (F, suit, tie, face, beanie, glasses, flower) in enumerate(variants):
        sheet.paste(draw_cat(F, suit, tie, face, beanie, glasses, flower),
                    (i * OUT, 0))
    sheet.save(out)
    print(f"saved {out}")


if __name__ == "__main__":
    main()
