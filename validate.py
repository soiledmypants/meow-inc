"""Automated post-generation checks.

Usage: python validate.py [--out output]

Verifies: file counts, image dimensions, hard-pixel integrity (perfect
32x32 grid, no antialiasing), limited palette, metadata schema, and
unique combinations.
"""

import argparse
import json
import sys
from pathlib import Path

from PIL import Image, ImageChops

import config
from traits import TRAITS, CATEGORY_ORDER

MAX_COLORS_PER_IMAGE = 40  # limited-palette sanity bound


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default=config.OUTPUT_DIR)
    args = parser.parse_args()
    out = Path(args.out)

    problems = []

    def check(ok, msg):
        if not ok:
            problems.append(msg)

    summary_path = out / "collection-summary.json"
    check(summary_path.exists(), "missing collection-summary.json")
    check((out / "contact-sheet.png").exists(), "missing contact-sheet.png")
    check((out / "rarity-report.csv").exists(), "missing rarity-report.csv")
    if problems:
        report(problems)

    summary = json.loads(summary_path.read_text())
    size = summary["size"]

    images = sorted((out / "images").glob("*.png"))
    metas = sorted((out / "metadata").glob("*.json"))
    check(len(images) == size, f"expected {size} images, found {len(images)}")
    check(len(metas) == size, f"expected {size} metadata files, found {len(metas)}")

    registry = {cat: {t.name for t in TRAITS[cat]} for cat in CATEGORY_ORDER}
    seen_combos = {}

    for i in range(1, size + 1):
        stem = f"{i:04d}"
        img_path = out / "images" / f"{stem}.png"
        meta_path = out / "metadata" / f"{stem}.json"
        if not img_path.exists():
            check(False, f"missing image {stem}.png")
            continue
        if not meta_path.exists():
            check(False, f"missing metadata {stem}.json")
            continue

        img = Image.open(img_path)
        check(img.size == (config.OUTPUT_SIZE, config.OUTPUT_SIZE),
              f"{stem}.png has size {img.size}")
        check(img.mode == "RGB", f"{stem}.png mode is {img.mode}, expected RGB")

        # Hard-pixel integrity: downscale to the logical grid and back —
        # a perfect nearest-neighbor upscale must round-trip losslessly.
        small = img.resize((config.LOGICAL_SIZE,) * 2, Image.NEAREST)
        back = small.resize(img.size, Image.NEAREST)
        check(ImageChops.difference(img, back).getbbox() is None,
              f"{stem}.png is not a clean {config.LOGICAL_SIZE}px pixel grid")

        colors = small.getcolors(maxcolors=4096)
        check(colors is not None and len(colors) <= MAX_COLORS_PER_IMAGE,
              f"{stem}.png uses {len(colors or [])} colors "
              f"(limit {MAX_COLORS_PER_IMAGE})")

        meta = json.loads(meta_path.read_text())
        for field in ("name", "description", "image", "edition", "seed",
                      "attributes"):
            check(field in meta, f"{stem}.json missing field {field!r}")
        check(meta.get("edition") == i, f"{stem}.json edition mismatch")
        check(meta.get("image") == f"{config.BASE_IMAGE_URI}{stem}.png",
              f"{stem}.json image URI mismatch")

        attrs = {a["trait_type"]: a["value"] for a in meta.get("attributes", [])}
        check(set(attrs) == set(CATEGORY_ORDER),
              f"{stem}.json attribute categories mismatch")
        for cat, val in attrs.items():
            check(val in registry.get(cat, ()),
                  f"{stem}.json has unknown trait {cat}/{val}")

        combo = tuple(attrs.get(cat) for cat in CATEGORY_ORDER)
        if combo in seen_combos:
            check(False, f"{stem}.json duplicates combination of "
                         f"{seen_combos[combo]}.json")
        seen_combos[combo] = stem

    report(problems, size)


def report(problems, size=None):
    if problems:
        print(f"FAILED: {len(problems)} problem(s)")
        for p in problems:
            print(f"  - {p}")
        sys.exit(1)
    if size is not None:
        print(f"OK: all checks passed for {size} editions")
        sys.exit(0)


if __name__ == "__main__":
    main()
