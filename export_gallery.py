"""Bundle an output run's metadata into one compact gallery-data.json.

Usage: python export_gallery.py [--out output-3333]

Writes <out>/gallery-data.json for gallery.html: the category order,
per-trait counts (for rarity percentages), and one row per edition with
its trait values in category order.
"""

import argparse
import json
from pathlib import Path

import config
from traits import CATEGORY_ORDER


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default=config.OUTPUT_DIR)
    args = parser.parse_args()
    out = Path(args.out)

    summary = json.loads((out / "collection-summary.json").read_text())
    size = summary["size"]

    editions = []
    for i in range(1, size + 1):
        meta = json.loads((out / "metadata" / f"{i:04d}.json").read_text())
        attrs = {a["trait_type"]: a["value"] for a in meta["attributes"]}
        editions.append([attrs[cat] for cat in CATEGORY_ORDER])

    data = {
        "collection": summary["collection"],
        "size": size,
        "categories": CATEGORY_ORDER,
        "trait_counts": summary["trait_counts"],
        "editions": editions,
    }
    path = out / "gallery-data.json"
    path.write_text(json.dumps(data, separators=(",", ":")))
    print(f"wrote {path} ({size} editions)")


if __name__ == "__main__":
    main()
