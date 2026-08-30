"""Extract a clean suit bust from a white-background JPG.

Usage: python clean_v4_body.py [src] [dst]

Flood-fills the white background from the borders, trims JPEG halo
fringe, refills horizontally-enclosed gaps as clean shirt white, keeps
the largest component. Defaults: art-refs/v4-body-source.jpg ->
art-refs/v4-body-base.png (the path v4_layers.py reads).
"""

import sys
from collections import deque

from PIL import Image

src = sys.argv[1] if len(sys.argv) > 1 else "art-refs/v4-body-source.jpg"
dst = sys.argv[2] if len(sys.argv) > 2 else "art-refs/v4-body-base.png"

im = Image.open(src).convert("RGBA")
px = im.load()
w, h = im.size

# flood the near-white background from the borders
stack = deque([(x, 0) for x in range(w)] + [(x, h - 1) for x in range(w)]
              + [(0, y) for y in range(h)] + [(w - 1, y) for y in range(h)])
seen = set()
while stack:
    x, y = stack.pop()
    if (x, y) in seen or not (0 <= x < w and 0 <= y < h):
        continue
    seen.add((x, y))
    r, g, b, a = px[x, y]
    if not (a and r > 235 and g > 235 and b > 235):
        continue
    px[x, y] = (0, 0, 0, 0)
    stack.extend(((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)))

# trim bright JPEG halo pixels that touch the transparency
for _ in range(2):
    trim = []
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            if a and max(r, g, b) > 190:
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < w and 0 <= ny < h and px[nx, ny][3] == 0:
                        trim.append((x, y))
                        break
    for x, y in trim:
        px[x, y] = (0, 0, 0, 0)

# keep the largest connected component
comp_seen = [[False] * w for _ in range(h)]
best = []
for sy in range(h):
    for sx in range(w):
        if comp_seen[sy][sx] or px[sx, sy][3] < 16:
            continue
        comp = []
        q = deque([(sx, sy)])
        comp_seen[sy][sx] = True
        while q:
            x, y = q.popleft()
            comp.append((x, y))
            for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1),
                           (x + 1, y + 1), (x - 1, y - 1),
                           (x + 1, y - 1), (x - 1, y + 1)):
                if 0 <= nx < w and 0 <= ny < h and not comp_seen[ny][nx] \
                        and px[nx, ny][3] >= 16:
                    comp_seen[ny][nx] = True
                    q.append((nx, ny))
        if len(comp) > len(best):
            best = comp
keep = set(best)
for y in range(h):
    for x in range(w):
        if px[x, y][3] >= 16 and (x, y) not in keep:
            px[x, y] = (0, 0, 0, 0)

# refill horizontally-enclosed gaps (the shirt / collar V) in clean white
for y in range(h):
    xs = [x for x in range(w) if px[x, y][3] >= 16]
    if len(xs) < 2:
        continue
    left, right = xs[0], xs[-1]
    run = 0
    for x in range(left, right + 1):
        if px[x, y][3] < 16:
            run += 1
        else:
            if 0 < run <= 420:
                for fx in range(x - run, x):
                    px[fx, y] = (250, 250, 252, 255)
            run = 0

# palette snap: quantize to the suit's few tones, killing JPEG noise
PALETTE = [(14, 14, 17), (42, 41, 48), (88, 86, 94), (150, 148, 156),
           (205, 205, 210), (250, 250, 252)]
for y in range(h):
    for x in range(w):
        r, g, b, a = px[x, y]
        if a < 128:
            px[x, y] = (0, 0, 0, 0)
            continue
        pr, pg, pb = min(PALETTE, key=lambda p: (p[0] - r) ** 2
                         + (p[1] - g) ** 2 + (p[2] - b) ** 2)
        px[x, y] = (pr, pg, pb, 255)

# final despeckle after the alpha hardening
for _ in range(1):
    clear = []
    for y in range(h):
        for x in range(w):
            if px[x, y][3] == 0:
                continue
            n = sum(1 for dx in (-1, 0, 1) for dy in (-1, 0, 1)
                    if (dx or dy) and 0 <= x + dx < w and 0 <= y + dy < h
                    and px[x + dx, y + dy][3] > 0)
            if n <= 2:
                clear.append((x, y))
    for x, y in clear:
        px[x, y] = (0, 0, 0, 0)

im.save(dst)
print(f"cleaned {src} -> {dst}, kept {len(best)} px")
