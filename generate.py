"""Collection generator.

Usage:
    python generate.py                # uses config.py
    python generate.py --size 100 --seed 7 --out output
"""

import argparse
import csv
import json
import math
import random
import sys
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

import config
from canvas import PixelCanvas
from palette import INK
from traits import TRAITS, CATEGORY_ORDER, CHARACTER_ORDER

MAX_SAMPLE_ATTEMPTS_PER_EDITION = 5000


# ---------------------------------------------------------------- setup

def load_placements():
    path = Path(__file__).parent / config.PLACEMENTS_FILE
    if path.exists():
        return json.loads(path.read_text())
    return {}


def validate_setup(size):
    errors = []
    if config.OUTPUT_SIZE % config.LOGICAL_SIZE != 0:
        errors.append("OUTPUT_SIZE must be a multiple of LOGICAL_SIZE")
    for cat in CATEGORY_ORDER:
        names = [t.name for t in TRAITS[cat]]
        if len(names) != len(set(names)):
            errors.append(f"duplicate trait names in category {cat}")

    space = math.prod(len(TRAITS[cat]) for cat in CATEGORY_ORDER)
    if size > space:
        errors.append(f"collection size {size} exceeds the {space} possible "
                      "trait combinations")

    if errors:
        for e in errors:
            print(f"CONFIG ERROR: {e}", file=sys.stderr)
        sys.exit(1)
    return space


# ---------------------------------------------------------------- sampling

def sample_edition(rng, seen):
    for _ in range(MAX_SAMPLE_ATTEMPTS_PER_EDITION):
        combo = {}
        for cat in CATEGORY_ORDER:
            traits = TRAITS[cat]
            pick = rng.choices(traits, weights=[t.weight for t in traits])[0]
            combo[cat] = pick.name
        key = tuple(combo[cat] for cat in CATEGORY_ORDER)
        if key not in seen:
            seen.add(key)
            return combo
    print("ERROR: could not find a new unique combination — the collection "
          "size is too large for the available trait space.", file=sys.stderr)
    sys.exit(1)


# ---------------------------------------------------------------- rendering

def trait_by_name(category, name):
    for t in TRAITS[category]:
        if t.name == name:
            return t
    raise KeyError(f"{category}/{name}")


def render(assignment, placements=None):
    placements = placements or {}
    animal = assignment["Animal"]
    c = PixelCanvas(config.LOGICAL_SIZE)
    bg = trait_by_name("Background", assignment["Background"])
    c.fill(bg.color)
    if bg.draw:
        layer = PixelCanvas(config.LOGICAL_SIZE)
        bg.draw(layer)
        c.paint_background(layer)

    for cat in CHARACTER_ORDER:
        t = trait_by_name(cat, assignment[cat])
        if not t.draw:
            continue
        layer = PixelCanvas(config.LOGICAL_SIZE)
        t.draw(layer)
        dx, dy = placements.get(animal, {}).get(cat, {}).get(t.name, (0, 0))
        c.blit(layer, dx, dy)

    c.outline_ring(INK)
    return c.to_image(config.OUTPUT_SIZE // config.LOGICAL_SIZE)


# ---------------------------------------------------------------- metadata

def write_metadata(path, edition, assignment):
    meta = {
        "name": f"{config.COLLECTION_NAME} #{edition:04d}",
        "description": config.COLLECTION_DESCRIPTION,
        "image": f"{config.BASE_IMAGE_URI}{edition:04d}.png",
        "edition": edition,
        "seed": config.SEED,
        "attributes": [
            {"trait_type": cat, "value": assignment[cat]}
            for cat in CATEGORY_ORDER
        ],
    }
    path.write_text(json.dumps(meta, indent=2) + "\n")


# ---------------------------------------------------------------- reports

def write_contact_sheet(images, path):
    cols = config.CONTACT_SHEET_COLUMNS
    thumb = config.CONTACT_SHEET_THUMB
    label_h = 14
    rows = math.ceil(len(images) / cols)
    sheet = Image.new("RGB", (cols * thumb, rows * (thumb + label_h)), (30, 30, 40))
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.load_default()
    for i, img in enumerate(images):
        x = (i % cols) * thumb
        y = (i // cols) * (thumb + label_h)
        sheet.paste(img.resize((thumb, thumb), Image.NEAREST), (x, y))
        draw.text((x + 4, y + thumb + 2), f"{i + 1:04d}",
                  fill=(200, 200, 210), font=font)
    sheet.save(path)


def write_rarity_report(editions, path):
    counts = {cat: {t.name: 0 for t in TRAITS[cat]} for cat in CATEGORY_ORDER}
    for assignment in editions:
        for cat in CATEGORY_ORDER:
            counts[cat][assignment[cat]] += 1
    n = len(editions)
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["category", "trait", "weight", "count", "percent"])
        for cat in CATEGORY_ORDER:
            for t in TRAITS[cat]:
                cnt = counts[cat][t.name]
                w.writerow([cat, t.name, t.weight, cnt, f"{100 * cnt / n:.1f}"])
    return counts


def write_summary(editions, counts, space, path):
    summary = {
        "collection": config.COLLECTION_NAME,
        "size": len(editions),
        "seed": config.SEED,
        "logical_size": config.LOGICAL_SIZE,
        "output_size": config.OUTPUT_SIZE,
        "base_image_uri": config.BASE_IMAGE_URI,
        "possible_combinations": space,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "trait_counts": counts,
    }
    path.write_text(json.dumps(summary, indent=2) + "\n")


# ---------------------------------------------------------------- main

def main():
    parser = argparse.ArgumentParser(description="Generate the collection")
    parser.add_argument("--size", type=int, default=config.COLLECTION_SIZE)
    parser.add_argument("--seed", type=int, default=config.SEED)
    parser.add_argument("--out", default=config.OUTPUT_DIR)
    args = parser.parse_args()

    config.COLLECTION_SIZE = args.size
    config.SEED = args.seed

    space = validate_setup(args.size)
    rng = random.Random(args.seed)
    placements = load_placements()

    out = Path(args.out)
    img_dir = out / "images"
    meta_dir = out / "metadata"
    img_dir.mkdir(parents=True, exist_ok=True)
    meta_dir.mkdir(parents=True, exist_ok=True)

    seen = set()
    editions = [sample_edition(rng, seen) for _ in range(args.size)]

    images = []
    for i, assignment in enumerate(editions):
        edition = i + 1
        img = render(assignment, placements)
        img.save(img_dir / f"{edition:04d}.png")
        write_metadata(meta_dir / f"{edition:04d}.json", edition, assignment)
        images.append(img)
        if edition % 25 == 0 or edition == len(editions):
            print(f"rendered {edition}/{len(editions)}")

    write_contact_sheet(images[:config.CONTACT_SHEET_MAX], out / "contact-sheet.png")
    counts = write_rarity_report(editions, out / "rarity-report.csv")
    write_summary(editions, counts, space, out / "collection-summary.json")

    print(f"done: {len(editions)} editions in {out}/ "
          f"(seed {args.seed}, {space:,} possible combinations)")


if __name__ == "__main__":
    main()
