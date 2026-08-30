# Meow Inc — generative pixel-art NFT collection

Original collection of 5 pixel animals (cat, dog, bear, rabbit, fox) in
tailored suits and ties. All art is drawn in code on a 32×32 grid — there
are no source image files — and scaled to 1024×1024 with nearest-neighbor
so pixels stay hard.

## Layout

- `config.py` — collection name/size/seed/output sizes/base URI
- `palette.py` — every color in the project
- `traits.py` — all trait art (draw functions) + rarity weights; 9
  categories: Background, Animal, Eyes, Mouth, Suit, Tie, Hat, Eyewear,
  Accessory
- `placements.json` — per-animal per-trait (dx, dy) pixel offsets, edited
  visually via the site
- `generate.py` — renders the collection (`--size N --seed N --out DIR`),
  writes images/, metadata/, contact-sheet.png, rarity-report.csv,
  collection-summary.json; dedupes combinations
- `validate.py` — post-run checks (dims, hard-pixel grid round-trip,
  palette size, metadata schema, uniqueness)
- `export_site.py` — dumps trait pixel layers to `site/traits-data.js`
- `site/` — static local editor: pick animal/traits, nudge per-animal
  offsets, copy/paste the placements JSON
- `output/` — 25-edition sample; `output-3333/` — the full 3,333 run

## Workflow

Setup: `python3 -m venv .venv && .venv/bin/pip install -r requirements.txt`
(on Windows: `.venv\Scripts\pip install -r requirements.txt`).

After editing trait art: run `export_site.py`, then `generate.py`, then
`validate.py`. The editor site is served with
`python3 -m http.server 8017 --directory site`.

Conventions: every trait draws on its own transparent layer at canonical
coordinates (documented at the top of `traits.py`); the generator composites
layers, applies placement offsets, and traces the 1px ink outline around the
whole silhouette. Keep art hard-edged — no gradients or antialiasing.
