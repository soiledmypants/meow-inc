"""V3 collection generator — composes editions from v3-layers/.

Usage:
    python v3_generate.py --size 24 --seed 28 --out v3-output
    python v3_generate.py --size 3333 --seed 28 --out v3-output-3333

Layers + per-category offsets come from v3-layers/manifest.json and
v3-placements.json (positions tuned in the v3 editor). Weights below
set rarity; "None" rows are the odds an optional slot stays empty.
Writes images/, metadata/, contact-sheet.png, rarity-report.csv,
collection-summary.json; combinations are deduped.
"""

import argparse
import json
import math
import random
import sys
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

COLLECTION_NAME = "Meow Inc"
DESCRIPTION = (
    "Meow Inc is an original collection of hand-drawn doodle cats in "
    "HD-pixel corporate attire. One smooth head, hard-pixel everything "
    "else, and a job to do."
)
BASE_IMAGE_URI = "ipfs://REPLACE_AFTER_UPLOAD/"
LAYERS = Path("v3-layers")
MAX_ATTEMPTS = 5000

# rarity weights; category "None" = odds an optional slot stays empty
WEIGHTS = {
    "Background": {"periwinkle": 90, "sky": 85, "mint": 70,
                   "plasma violet": 65, "rose": 60, "butter": 55,
                   "charcoal": 30},
    "Head": {"sky": 100, "white": 90, "gray": 80, "cream": 80,
             "tabby": 70, "pink": 55, "mint": 45, "lavender": 35},
    "Eyes": {"dots": 100, "bead": 70, "squint": 55, "sleepy": 40,
             "wink": 25},
    "Mouth": {"smile": 100, "line": 70, "grin": 55, "blep": 35},
    "Blush": {"None": 70, "blush": 30},
    "Glasses": {"None": 65, "round-lavender": 25, "shades": 18,
                "round-gold": 15},
    "Accessory": {"None": 60, "earring": 25, "flower": 20},
}


def load_kit():
    manifest = json.loads((LAYERS / "manifest.json").read_text())
    placements = json.loads(Path("v3-placements.json").read_text())
    bgs = {b["name"]: b["color"] for b in manifest["backgrounds"]}
    cats = []
    images = {}
    for cat in manifest["categories"]:
        files = {l["name"]: l["file"] for l in cat["layers"]}
        cats.append({"name": cat["name"], "optional": cat["optional"],
                     "files": files})
        for lname, f in files.items():
            images[(cat["name"], lname)] = Image.open(LAYERS / f).convert("RGBA")
    return manifest, placements, bgs, cats, images


def check_weights(bgs, cats):
    errors = []
    for cat in cats:
        w = WEIGHTS.get(cat["name"], {})
        expected = set(cat["files"]) | ({"None"} if cat["optional"] else set())
        if set(w) != expected:
            errors.append(f"{cat['name']}: weights {sorted(w)} != "
                          f"layers {sorted(expected)}")
    if set(WEIGHTS["Background"]) != set(bgs):
        errors.append("Background weights do not match manifest backgrounds")
    if errors:
        for e in errors:
            print(f"CONFIG ERROR: {e}", file=sys.stderr)
        sys.exit(1)


def sample(rng, cats, seen):
    for _ in range(MAX_ATTEMPTS):
        combo = {}
        names, weights = zip(*WEIGHTS["Background"].items())
        combo["Background"] = rng.choices(names, weights=weights)[0]
        for cat in cats:
            names, weights = zip(*WEIGHTS[cat["name"]].items())
            combo[cat["name"]] = rng.choices(names, weights=weights)[0]
        key = tuple(combo.values())
        if key not in seen:
            seen.add(key)
            return combo
    sys.exit("ERROR: ran out of unique combinations")


def render(combo, bgs, cats, images, placements, size):
    img = Image.new("RGBA", (size, size), bgs[combo["Background"]])
    for cat in cats:
        pick = combo[cat["name"]]
        if pick == "None":
            continue
        layer = images[(cat["name"], pick)]
        dx, dy = placements.get(cat["name"], (0, 0))
        if (dx, dy) == (0, 0):
            img.alpha_composite(layer)
        else:
            shifted = Image.new("RGBA", (size, size), (0, 0, 0, 0))
            shifted.paste(layer, (dx, dy), layer)
            img.alpha_composite(shifted)
    return img.convert("RGB")


def write_metadata(path, edition, combo, seed):
    meta = {
        "name": f"{COLLECTION_NAME} #{edition:04d}",
        "description": DESCRIPTION,
        "image": f"{BASE_IMAGE_URI}{edition:04d}.png",
        "edition": edition,
        "seed": seed,
        "attributes": [{"trait_type": k, "value": v}
                       for k, v in combo.items()],
    }
    path.write_text(json.dumps(meta, indent=2) + "\n")


def contact_sheet(imgs, path, cols=6, thumb=200):
    rows = math.ceil(len(imgs) / cols)
    sheet = Image.new("RGB", (cols * thumb, rows * (thumb + 16)), (30, 30, 40))
    d = ImageDraw.Draw(sheet)
    font = ImageFont.load_default()
    for i, im in enumerate(imgs):
        x, y = (i % cols) * thumb, (i // cols) * (thumb + 16)
        sheet.paste(im.resize((thumb, thumb), Image.LANCZOS), (x, y))
        d.text((x + 4, y + thumb + 2), f"{i + 1:04d}", fill=(210, 210, 220),
               font=font)
    sheet.save(path)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--size", type=int, default=24)
    parser.add_argument("--seed", type=int, default=28)
    parser.add_argument("--out", default="v3-output")
    args = parser.parse_args()

    manifest, placements, bgs, cats, images = load_kit()
    check_weights(bgs, cats)
    canvas = manifest["canvas"]

    out = Path(args.out)
    (out / "images").mkdir(parents=True, exist_ok=True)
    (out / "metadata").mkdir(parents=True, exist_ok=True)

    rng = random.Random(args.seed)
    seen = set()
    editions = [sample(rng, cats, seen) for _ in range(args.size)]

    space = math.prod(len(w) for w in WEIGHTS.values())
    imgs = []
    for i, combo in enumerate(editions):
        n = i + 1
        img = render(combo, bgs, cats, images, placements, canvas)
        img.save(out / "images" / f"{n:04d}.png")
        write_metadata(out / "metadata" / f"{n:04d}.json", n, combo, args.seed)
        imgs.append(img)
        if n % 25 == 0 or n == args.size:
            print(f"rendered {n}/{args.size}")

    contact_sheet(imgs[:60], out / "contact-sheet.png")

    counts = {c: {} for c in WEIGHTS}
    for combo in editions:
        for cat, val in combo.items():
            counts[cat][val] = counts[cat].get(val, 0) + 1
    with open(out / "rarity-report.csv", "w") as f:
        f.write("category,trait,weight,count,percent\n")
        for cat, w in WEIGHTS.items():
            for name, weight in w.items():
                cnt = counts[cat].get(name, 0)
                f.write(f"{cat},{name},{weight},{cnt},"
                        f"{100 * cnt / args.size:.1f}\n")
    summary = {
        "collection": COLLECTION_NAME,
        "size": args.size,
        "seed": args.seed,
        "canvas": canvas,
        "base_image_uri": BASE_IMAGE_URI,
        "possible_combinations": space,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "trait_counts": counts,
    }
    (out / "collection-summary.json").write_text(json.dumps(summary, indent=2))
    print(f"done: {args.size} editions in {out}/ (seed {args.seed}, "
          f"{space:,} weighted trait rows)")


if __name__ == "__main__":
    main()
