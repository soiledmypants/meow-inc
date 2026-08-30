"""Collection configuration — edit this file to control a run."""

COLLECTION_NAME = "Meow Inc"
COLLECTION_DESCRIPTION = (
    "Meow Inc is an original generative pixel-art collection of animals in "
    "tailored suits. Every character is drawn programmatically on a 32x32 "
    "grid and scaled with hard pixels only."
)

# Placeholder base URI, prepended to image filenames in metadata.
BASE_IMAGE_URI = "ipfs://REPLACE_AFTER_UPLOAD/"

COLLECTION_SIZE = 25          # how many editions to generate
SEED = 28                     # fixed seed -> identical collection every run
OUTPUT_DIR = "output"

LOGICAL_SIZE = 32             # art is authored on this pixel grid
OUTPUT_SIZE = 1024            # final PNG size; must be a multiple of LOGICAL_SIZE

PLACEMENTS_FILE = "placements.json"   # per-animal trait offsets (see README)

CONTACT_SHEET_COLUMNS = 5
CONTACT_SHEET_THUMB = 128
CONTACT_SHEET_MAX = 100       # only the first N editions go on the sheet
