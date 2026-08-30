# Meow Inc — animals in suits

A clean generative pixel-art collection: **5 animals, always in a suit and
tie**, with hats, eyewear, and accessories. Everything is drawn
programmatically on a 32×32 grid and scaled to 1024×1024 with hard pixels
only — no image layers to prepare.

**Categories (9):** Background (8, with edge motifs) · Animal (Tabby Cat,
Ash Dog, Honey Bear, Snow Rabbit, Red Fox) · Eyes (6) · Mouth (6) ·
Suit (8 designs) · Tie (8 colors & styles, incl. bow ties) · Hat (8) ·
Eyewear (5) · Accessory (5) — **18,432,000 possible unique combinations.**

## Setup

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

## Generate the collection

```bash
.venv/bin/python generate.py          # renders the collection from config.py
.venv/bin/python validate.py          # runs all automated output checks
```

Optional: `generate.py --size 500 --seed 7`. Same seed = identical
collection. Duplicates are impossible. Output lands in `output/`
(images/, metadata/, contact-sheet.png, rarity-report.csv,
collection-summary.json).

## Trait placement editor (local site)

Adjust where each trait sits **per animal** (hat height, earring position,
etc.) visually in the browser:

```bash
.venv/bin/python export_site.py
```

```bash
python3 -m http.server 8017 --directory site
```

Then open <http://localhost:8017>.

- Pick an animal, cycle traits with ◀ ▶, click a trait row, nudge with the
  arrow buttons or keyboard arrows.
- **📋 Copy settings JSON** copies the offsets for all animals.
- Paste that JSON into `placements.json` (replacing its contents) — or send
  it to Claude — then re-run `generate.py`. The generator applies the same
  offsets when rendering.
- The site can also re-load settings: paste JSON into the box and hit
  **⬆ Load JSON from box**.

Re-run `export_site.py` whenever you edit trait art in `traits.py` so the
site picks up the new pixels.

## Where to change things

| What | Where |
|---|---|
| Collection name, size, seed, output size, base URI | `config.py` |
| Colors / theme | `palette.py` |
| Trait art + rarity weights (bigger weight = more common) | `traits.py` |
| Per-animal trait position offsets | `placements.json` (edit via the site) |

### Adding a trait

1. In `traits.py`, write a draw function `(c)` using `c.px / c.row / c.col
   / c.rect` (canonical coordinates are documented at the top of the file).
2. Append `Trait("My Trait", 40, my_draw_fn)` to its category list.
3. Run `export_site.py` to see it in the editor, nudge per animal if
   needed, and regenerate.

### Quick previews

```bash
.venv/bin/python preview.py Hat       # one image per hat on a neutral bear
```

## Automated checks (`validate.py`)

File counts and matching zero-padded names, exact dimensions, hard-pixel
integrity (each PNG must round-trip losslessly through a 32×32
nearest-neighbor downscale), limited palette, metadata schema, and
duplicate-combination detection.
