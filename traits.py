"""Trait registry — 5 animals in suits, 8 simple categories.

Every trait is Trait(name, weight, draw). Bigger weight = more common.
Draw functions paint onto their own transparent layer at a canonical
position; per-animal placement offsets live in placements.json and are
applied when the layers are composited (tune them visually with the
local site — see README).

Base geometry (32x32 grid, origin top-left):
  head    x 9..22,  y 8..23      ears above/beside, per animal
  eyes    2x2 boxes at (12,13) and (18,13)
  muzzle  around x 12..19, y 15..21, nose baked into the animal
  mouth   y 19..22, x 13..18
  torso   y 26..31, widening to x 6..25 (runs off canvas bottom)
"""

from dataclasses import dataclass
from palette import (
    INK, GOLD, WHITE, RED, TEAL, MOUTH, TONGUE, LID, WOOD,
    BG, BGFX, FUR, EAR_PINK, DOG_EAR, FOX_TIP, NOSE_ROSE, NOSE_COCOA,
    HAT, SUIT, TIE_PURPLE,
)


@dataclass
class Trait:
    name: str
    weight: int
    draw: callable = None     # paints the layer; None = empty trait
    color: tuple = None       # backgrounds only: flat fill color


CATEGORY_ORDER = [
    "Background", "Animal", "Eyes", "Mouth", "Suit", "Tie", "Hat",
    "Eyewear", "Accessory",
]
CHARACTER_ORDER = CATEGORY_ORDER[1:]   # draw order after the background

# =====================================================================
# Background — flat base color + optional motif drawn behind the
# character (motifs stay near the edges so they never fight the face)
# =====================================================================

def bg_stars(c):
    for x, y in ((2, 4), (28, 2), (30, 19), (1, 23), (29, 28), (3, 14)):
        c.px(x, y, BGFX["star"])

def bg_haze(c):
    c.row(3, 0, 31, BGFX["haze"])
    c.row(4, 0, 31, BGFX["haze"])
    c.row(21, 0, 31, BGFX["haze"])
    c.px(3, 9, WHITE); c.px(29, 12, WHITE)

def bg_dashes(c):
    for x0, y0 in ((1, 3), (3, 1), (28, 3), (29, 27), (27, 29), (1, 27)):
        c.px(x0, y0, BGFX["dash"])
        c.px(x0 + 1, y0 + 1, BGFX["dash"])

def bg_panels(c):
    c.col(3, 0, 31, BGFX["seam"])
    c.col(28, 0, 31, BGFX["seam"])
    c.row(8, 0, 31, BGFX["seam"])
    c.row(22, 0, 31, BGFX["seam"])
    for i, x in enumerate(range(0, 5)):          # hazard stripe, lower left
        c.px(x, 29, GOLD if i % 2 == 0 else INK)
        c.px(x, 30, INK if i % 2 == 0 else GOLD)

def bg_aurora(c):
    wave = (2, 2, 3, 3, 4, 4, 3, 3)
    for x in range(32):
        c.px(x, wave[x % 8], BGFX["aurora"])
        c.px(x, wave[(x + 3) % 8] + 3, BGFX["aurora2"])
    c.px(2, 12, BGFX["star"]); c.px(29, 15, BGFX["star"])

def bg_sunrise(c):
    for y in range(0, 16):
        c.row(y, 0, 31, BGFX["sunrise_top"])
    c.row(16, 0, 31, BGFX["sunrise_band"])
    c.row(17, 0, 31, BGFX["sunrise_band"])

BACKGROUNDS = [
    Trait("Deep Space", 100, bg_stars, color=BG["deep_space"]),
    Trait("Rose Nebula", 90, bg_haze, color=BG["rose_nebula"]),
    Trait("Hyperlane Teal", 90, bg_dashes, color=BG["hyperlane_teal"]),
    Trait("Signal Mint", 90, color=BG["signal_mint"]),
    Trait("Docking Bay", 80, bg_panels, color=BG["slate_bay"]),
    Trait("Plasma Violet", 60, color=BG["plasma_violet"]),
    Trait("Aurora Night", 60, bg_aurora, color=BG["aurora_night"]),
    Trait("Sunrise Orbit", 40, bg_sunrise, color=BG["sunrise_bottom"]),
]

# =====================================================================
# Animals — head, ears, muzzle, nose, neck, torso
# =====================================================================

def draw_base(c, fur, shade):
    c.row(8, 11, 20, fur)
    c.row(9, 10, 21, fur)
    for y in range(10, 22):
        c.row(y, 9, 22, fur)
    c.row(22, 10, 21, fur)
    c.row(23, 12, 19, fur)
    for y in range(10, 24):          # right-side shading for depth
        x1 = 21 if y == 22 else (19 if y == 23 else 22)
        c.px(x1, y, shade)
    c.row(24, 14, 17, shade)         # chin shadow
    c.row(25, 14, 17, fur)           # neck
    c.row(26, 9, 22, fur)            # torso base (suits overdraw)
    c.row(27, 7, 24, fur)
    c.rect(6, 28, 25, 31, fur)

def muzzle_small(c, color):
    c.rect(13, 16, 18, 20, color)
    c.row(21, 14, 17, color)

def muzzle_big(c, color):
    c.row(15, 13, 18, color)
    c.rect(12, 16, 19, 20, color)
    c.row(21, 13, 18, color)

def animal_cat(c):
    fur, shade, muzzle = FUR["cat"]
    draw_base(c, fur, shade)
    c.px(9, 4, fur); c.row(5, 8, 10, fur)          # tapered ears
    c.rect(8, 6, 11, 7, fur)
    c.px(22, 4, fur); c.row(5, 21, 23, fur)
    c.rect(20, 6, 23, 7, fur)
    c.px(9, 6, EAR_PINK); c.px(9, 7, EAR_PINK)
    c.px(22, 6, EAR_PINK); c.px(22, 7, EAR_PINK)
    muzzle_small(c, muzzle)
    c.rect(15, 16, 16, 17, NOSE_ROSE)

def animal_dog(c):
    fur, shade, muzzle = FUR["dog"]
    draw_base(c, fur, shade)
    muzzle_big(c, muzzle)
    c.rect(7, 8, 9, 13, DOG_EAR)                    # floppy ears
    c.row(14, 8, 9, DOG_EAR)
    c.rect(22, 8, 24, 13, DOG_EAR)
    c.row(14, 22, 23, DOG_EAR)
    c.row(16, 14, 17, INK)                          # big nose
    c.row(17, 15, 16, INK)

def animal_bear(c):
    fur, shade, muzzle = FUR["bear"]
    draw_base(c, fur, shade)
    c.row(6, 9, 12, fur); c.row(7, 8, 12, fur)      # wide round ears
    c.px(10, 7, shade); c.px(11, 7, shade)
    c.row(6, 19, 22, fur); c.row(7, 19, 23, fur)
    c.px(20, 7, shade); c.px(21, 7, shade)
    muzzle_big(c, muzzle)
    c.row(16, 14, 17, NOSE_COCOA)
    c.row(17, 15, 16, NOSE_COCOA)

def animal_rabbit(c):
    fur, shade, muzzle = FUR["rabbit"]
    draw_base(c, fur, shade)
    c.px(10, 1, fur); c.rect(9, 2, 11, 7, fur)      # tall ears
    c.px(21, 1, fur); c.rect(20, 2, 22, 7, fur)
    c.col(10, 3, 6, EAR_PINK); c.col(21, 3, 6, EAR_PINK)
    muzzle_small(c, muzzle)
    c.row(16, 15, 16, NOSE_ROSE)

def animal_fox(c):
    fur, shade, muzzle = FUR["fox"]
    draw_base(c, fur, shade)
    c.row(4, 8, 9, FOX_TIP); c.row(5, 8, 10, fur)   # dark-tipped ears
    c.rect(7, 6, 10, 7, fur)
    c.row(4, 22, 23, FOX_TIP); c.row(5, 21, 23, fur)
    c.rect(21, 6, 24, 7, fur)
    muzzle_big(c, muzzle)
    c.rect(10, 16, 11, 18, muzzle)                  # white cheek wedges
    c.rect(20, 16, 21, 18, muzzle)
    c.rect(15, 16, 16, 17, INK)

ANIMALS = [
    Trait("Tabby Cat", 100, animal_cat),
    Trait("Ash Dog", 100, animal_dog),
    Trait("Honey Bear", 100, animal_bear),
    Trait("Snow Rabbit", 100, animal_rabbit),
    Trait("Red Fox", 70, animal_fox),
]

# =====================================================================
# Eyes — two 2x2 boxes anchored at (12,13) and (18,13)
# =====================================================================

LX, RX, EY = 12, 18, 13

def eyes_steady(c):
    for x in (LX, RX):
        c.col(x, EY, EY + 1, WHITE)
        c.col(x + 1, EY, EY + 1, INK)

def eyes_sideeye(c):
    for x in (LX, RX):
        c.col(x, EY, EY + 1, INK)
        c.col(x + 1, EY, EY + 1, WHITE)

def eyes_sleepy(c):
    for x in (LX, RX):
        c.row(EY, x, x + 1, LID)
        c.px(x, EY + 1, WHITE)
        c.px(x + 1, EY + 1, INK)

def eyes_wide(c):
    for x in (LX, RX):
        c.rect(x, EY, x + 1, EY + 1, WHITE)
        c.px(x + 1, EY + 1, INK)

def eyes_serene(c):
    c.row(EY + 1, LX, LX + 1, INK)
    c.row(EY + 1, RX, RX + 1, INK)

def eyes_starry(c):
    for x in (LX, RX):
        c.rect(x, EY, x + 1, EY + 1, WHITE)
        c.px(x + 1, EY, GOLD)
        c.px(x, EY + 1, GOLD)

EYES = [
    Trait("Steady", 100, eyes_steady),
    Trait("Sideeye", 100, eyes_sideeye),
    Trait("Sleepy", 70, eyes_sleepy),
    Trait("Wide", 70, eyes_wide),
    Trait("Serene", 30, eyes_serene),
    Trait("Starry", 15, eyes_starry),
]

# =====================================================================
# Mouth — rows 19..22
# =====================================================================

def mouth_smile(c):
    c.row(20, 14, 17, MOUTH)
    c.px(13, 19, MOUTH); c.px(18, 19, MOUTH)

def mouth_line(c):
    c.row(20, 14, 17, MOUTH)

def mouth_grin(c):
    c.row(19, 13, 18, MOUTH)
    c.row(20, 14, 17, WHITE)

def mouth_blep(c):
    c.row(20, 14, 17, MOUTH)
    c.rect(16, 21, 17, 22, TONGUE)

def mouth_frown(c):
    c.row(20, 14, 17, MOUTH)
    c.px(13, 21, MOUTH); c.px(18, 21, MOUTH)

def mouth_toothpick(c):
    c.row(20, 14, 17, MOUTH)
    c.row(20, 18, 23, WOOD)

MOUTHS = [
    Trait("Smile", 100, mouth_smile),
    Trait("Line", 100, mouth_line),
    Trait("Grin", 60, mouth_grin),
    Trait("Blep", 50, mouth_blep),
    Trait("Frown", 50, mouth_frown),
    Trait("Toothpick", 20, mouth_toothpick),
]

# =====================================================================
# Suits — every courier wears one; ties are their own category and are
# drawn on top of the suit's shirt V
# =====================================================================

def torso(c, color):
    c.row(26, 9, 22, color)
    c.row(27, 7, 24, color)
    c.rect(6, 28, 25, 31, color)

def make_suit(jacket, lapel, square=None, extra=None):
    def draw(c):
        torso(c, jacket)
        c.row(26, 13, 18, SUIT["shirt"])          # shirt collar V
        c.row(27, 14, 17, SUIT["shirt"])
        c.row(28, 15, 16, SUIT["shirt"])
        # wide angled lapels converging on the tie
        c.row(26, 11, 12, lapel); c.row(26, 19, 20, lapel)
        c.row(27, 12, 13, lapel); c.row(27, 18, 19, lapel)
        c.row(28, 13, 14, lapel); c.row(28, 17, 18, lapel)
        c.row(29, 14, 15, lapel); c.row(29, 16, 17, lapel)
        if square:
            c.px(9, 28, square); c.px(10, 28, square)    # pocket square
        if extra:
            extra(c)
    return draw

def extra_pinstripe(c):
    for x in (8, 11, 20, 23):
        c.col(x, 28, 31, SUIT["pinstripe"])

def extra_trench(c):
    c.row(30, 6, 25, SUIT["belt"])
    c.px(15, 30, GOLD); c.px(16, 30, GOLD)

def extra_tux(c):
    c.px(13, 29, GOLD); c.px(18, 29, GOLD)        # shirt studs

SUITS = [
    Trait("Navy Suit", 100,
          make_suit(SUIT["navy"], SUIT["navy_lapel"], square=SUIT["shirt"])),
    Trait("Charcoal Pinstripe", 80,
          make_suit(SUIT["charcoal"], SUIT["charcoal_lapel"], square=RED,
                    extra=extra_pinstripe)),
    Trait("Burgundy Suit", 80,
          make_suit(SUIT["burgundy"], SUIT["burgundy_lapel"],
                    square=SUIT["shirt"])),
    Trait("Forest Suit", 70,
          make_suit(SUIT["forest"], SUIT["forest_lapel"], square=GOLD)),
    Trait("Sky Suit", 70,
          make_suit(SUIT["sky"], SUIT["sky_lapel"], square=SUIT["shirt"])),
    Trait("Lavender Suit", 50,
          make_suit(SUIT["lavender"], SUIT["lavender_lapel"], square=GOLD)),
    Trait("Trench Coat", 40,
          make_suit(SUIT["trench"], SUIT["trench_lapel"], extra=extra_trench)),
    Trait("Midnight Tuxedo", 25,
          make_suit(SUIT["tux"], SUIT["tux_lapel"], square=WHITE,
                    extra=extra_tux)),
]

# =====================================================================
# Ties — knot at the collar (15..16, 26), body widens, tapers to a point
# =====================================================================

def make_tie(color, stripe=None, dots=None):
    def draw(c):
        c.px(15, 26, color); c.px(16, 26, color)   # knot in the collar
        c.row(27, 15, 16, color)
        c.rect(14, 28, 17, 29, color)              # wide body
        c.row(30, 15, 16, color)                   # tapered point
        if stripe:
            c.row(29, 14, 17, stripe)
        if dots:
            c.px(14, 28, dots); c.px(16, 29, dots); c.px(15, 30, dots)
    return draw

def make_bow(color, knot):
    def draw(c):
        c.rect(13, 26, 14, 27, color)              # wings
        c.rect(17, 26, 18, 27, color)
        c.rect(15, 26, 16, 27, knot)               # center knot
    return draw

TIES = [
    Trait("Red Tie", 100, make_tie(RED)),
    Trait("Gold Tie", 80, make_tie(GOLD)),
    Trait("Teal Tie", 80, make_tie(TEAL)),
    Trait("Magenta Tie", 60, make_tie((214, 74, 130))),
    Trait("Candy Stripe Tie", 40, make_tie(RED, stripe=WHITE)),
    Trait("Royal Dot Tie", 30, make_tie(TIE_PURPLE, dots=GOLD)),
    Trait("Red Bow Tie", 25, make_bow(RED, INK)),
    Trait("Ink Bow Tie", 15, make_bow(INK, RED)),
]

# =====================================================================
# Hats — sit at x12..19 so animal ears stay visible beside them
# =====================================================================

def hat_beanie(c):
    c.row(5, 12, 19, HAT["beanie"])
    c.rect(10, 6, 21, 8, HAT["beanie"])
    c.row(9, 10, 21, HAT["beanie_fold"])
    c.row(4, 15, 16, WHITE)

def hat_flat_cap(c):
    c.row(6, 12, 19, HAT["flat_cap"])
    c.row(7, 11, 20, HAT["flat_cap"])
    c.row(8, 10, 21, HAT["flat_cap"])
    c.row(9, 12, 19, HAT["flat_shade"])

def hat_bowler(c):
    c.rect(13, 4, 18, 5, HAT["bowler"])
    c.rect(12, 6, 19, 7, HAT["bowler"])
    c.row(6, 12, 19, INK)
    c.row(8, 10, 21, HAT["bowler"])

def hat_top(c):
    c.rect(12, 1, 19, 6, HAT["top_hat"])
    c.row(5, 12, 19, GOLD)
    c.row(7, 10, 21, HAT["top_hat"])

def hat_cap(c):
    c.rect(11, 5, 20, 8, HAT["cap_red"])
    c.rect(13, 6, 18, 8, HAT["cap_cream"])
    c.px(15, 7, GOLD); c.px(16, 7, GOLD)
    c.row(9, 9, 22, HAT["cap_dark"])

def hat_halo(c):
    c.row(7, 10, 21, HAT["headset_band"])
    c.rect(7, 13, 8, 16, HAT["headset_cup"])
    c.rect(23, 13, 24, 16, HAT["headset_cup"])
    c.col(25, 5, 12, HAT["headset_band"])
    c.px(25, 4, RED)

def hat_crown(c):
    for x in (12, 14, 16, 18):
        c.px(x, 5, GOLD)
    c.rect(12, 6, 19, 7, GOLD)
    c.px(15, 7, RED)

HATS = [
    Trait("None", 100),
    Trait("Dock Beanie", 60, hat_beanie),
    Trait("Flat Cap", 60, hat_flat_cap),
    Trait("Bowler Hat", 45, hat_bowler),
    Trait("Courier Cap", 45, hat_cap),
    Trait("Top Hat", 25, hat_top),
    Trait("Comms Halo", 20, hat_halo),
    Trait("Gold Crown", 6, hat_crown),
]

# =====================================================================
# Eyewear
# =====================================================================

def wear_glasses(c):
    for x0 in (11, 17):
        c.row(12, x0, x0 + 3, INK)
        c.row(15, x0, x0 + 3, INK)
        c.col(x0, 13, 14, INK)
        c.col(x0 + 3, 13, 14, INK)
    c.px(15, 13, INK); c.px(16, 13, INK)      # bridge
    c.px(9, 13, INK); c.px(10, 13, INK)       # temples
    c.px(21, 13, INK); c.px(22, 13, INK)

def wear_visor(c):
    c.rect(10, 13, 21, 14, TEAL)
    c.px(11, 13, WHITE); c.px(12, 13, WHITE)
    c.px(9, 13, INK); c.px(22, 13, INK)

def wear_monocle(c):
    c.row(12, 17, 20, GOLD)
    c.row(15, 17, 20, GOLD)
    c.col(17, 13, 14, GOLD); c.col(20, 13, 14, GOLD)
    c.px(21, 16, GOLD); c.px(22, 17, GOLD)    # chain

def wear_patch(c):
    c.rect(17, 12, 20, 15, INK)
    c.row(12, 9, 16, INK)
    c.row(12, 21, 22, INK)

EYEWEAR = [
    Trait("None", 100),
    Trait("Round Glasses", 45, wear_glasses),
    Trait("Visor Shades", 30, wear_visor),
    Trait("Scanner Monocle", 15, wear_monocle),
    Trait("Eye Patch", 10, wear_patch),
]

# =====================================================================
# Accessories — earrings draw at the cat's ear; placements.json moves
# them to each other animal's ear
# =====================================================================

def acc_chain(c):
    c.row(25, 12, 19, GOLD)
    c.px(15, 26, GOLD); c.px(16, 26, GOLD)    # pendant

def acc_stud(c):
    c.px(9, 6, GOLD)

def acc_hoop(c):
    c.px(9, 6, GOLD); c.px(9, 7, GOLD); c.px(8, 7, GOLD)

def acc_star(c):
    c.px(19, 17, GOLD); c.px(20, 16, WHITE)

ACCESSORIES = [
    Trait("None", 100),
    Trait("Neck Chain", 45, acc_chain),
    Trait("Stud Earring", 40, acc_stud),
    Trait("Hoop Earring", 30, acc_hoop),
    Trait("Cheek Star", 25, acc_star),
]

# =====================================================================
# Registry
# =====================================================================

TRAITS = {
    "Background": BACKGROUNDS,
    "Animal": ANIMALS,
    "Eyes": EYES,
    "Mouth": MOUTHS,
    "Suit": SUITS,
    "Tie": TIES,
    "Hat": HATS,
    "Eyewear": EYEWEAR,
    "Accessory": ACCESSORIES,
}
