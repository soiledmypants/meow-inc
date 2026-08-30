"""Key a baked-in checkerboard background off a sprite.

Usage: python clean_checker.py <src> <dst>

Flood-fills near-neutral light pixels (both checker tones) from the
borders, keeps the largest connected component, despeckles.
"""

import sys
from collections import deque

from PIL import Image

src, dst = sys.argv[1], sys.argv[2]
im = Image.open(src).convert("RGBA")
px = im.load()
w, h = im.size


def is_checker(r, g, b):
    return min(r, g, b) > 222 and max(r, g, b) - min(r, g, b) < 14


stack = deque([(x, 0) for x in range(w)] + [(x, h - 1) for x in range(w)]
              + [(0, y) for y in range(h)] + [(w - 1, y) for y in range(h)])
seen = set()
while stack:
    x, y = stack.pop()
    if (x, y) in seen or not (0 <= x < w and 0 <= y < h):
        continue
    seen.add((x, y))
    r, g, b, a = px[x, y]
    if not (a and is_checker(r, g, b)):
        continue
    px[x, y] = (0, 0, 0, 0)
    stack.extend(((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)))

# largest connected component only
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
