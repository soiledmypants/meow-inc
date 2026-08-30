"""Extract a clean head from the full v4 scene image.

Usage: python clean_v4_head.py [src] [dst]

Removes the blue ticker background and red chart, cuts everything below
the collar line, keeps only the largest connected component, and trims
blue-fringed edge pixels. Defaults: art-refs/v4-head-source.png ->
art-refs/v4-head-base.png (the path v4_layers.py reads).
"""

import sys
from collections import deque

from PIL import Image

src = sys.argv[1] if len(sys.argv) > 1 else "art-refs/v4-head-source.png"
dst = sys.argv[2] if len(sys.argv) > 2 else "art-refs/v4-head-base.png"

im = Image.open(src).convert("RGBA")
px = im.load()
w, h = im.size
cutoff = round(h * 0.705)          # collar line — suit starts below


def is_bg(r, g, b):
    if b > g and b > r * 0.82 and b > 70:      # blues, incl. digit tint
        return True
    if r > 150 and g < 90 and b < 90:          # red chart line
        return True
    return False


for y in range(h):
    for x in range(w):
        r, g, b, a = px[x, y]
        if y >= cutoff or (a and is_bg(r, g, b)):
            px[x, y] = (0, 0, 0, 0)

# keep only the largest connected component
seen = [[False] * w for _ in range(h)]
best = []
for sy in range(h):
    for sx in range(w):
        if seen[sy][sx] or px[sx, sy][3] < 16:
            continue
        comp = []
        q = deque([(sx, sy)])
        seen[sy][sx] = True
        while q:
            x, y = q.popleft()
            comp.append((x, y))
            for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1),
                           (x + 1, y + 1), (x - 1, y - 1),
                           (x + 1, y - 1), (x - 1, y + 1)):
                if 0 <= nx < w and 0 <= ny < h and not seen[ny][nx] \
                        and px[nx, ny][3] >= 16:
                    seen[ny][nx] = True
                    q.append((nx, ny))
        if len(comp) > len(best):
            best = comp

keep = set(best)
for y in range(h):
    for x in range(w):
        if px[x, y][3] >= 16 and (x, y) not in keep:
            px[x, y] = (0, 0, 0, 0)

# suit-shoulder remnants: near-black pixels low on the head are not fur
for y in range(round(h * 0.66), h):
    for x in range(w):
        r, g, b, a = px[x, y]
        if a and max(r, g, b) < 90:
            px[x, y] = (0, 0, 0, 0)

# despeckle: clear pixels with almost no opaque neighbors (thin tails)
for _ in range(2):
    clear = []
    for y in range(h):
        for x in range(w):
            if px[x, y][3] < 16:
                continue
            n = sum(1 for dx in (-1, 0, 1) for dy in (-1, 0, 1)
                    if (dx or dy) and 0 <= x + dx < w and 0 <= y + dy < h
                    and px[x + dx, y + dy][3] >= 16)
            if n <= 2:
                clear.append((x, y))
    for x, y in clear:
        px[x, y] = (0, 0, 0, 0)

im.save(dst)
print(f"cleaned {src} -> {dst}, kept {len(best)} px")
