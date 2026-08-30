"""Logical pixel canvas with transparent layers.

Each trait draws onto its own transparent layer; the generator blits
layers together (with per-animal placement offsets), traces a 1px outline
around the combined silhouette, and scales up with nearest-neighbor.
"""

from PIL import Image


class PixelCanvas:
    def __init__(self, size):
        self.size = size
        self.grid = [[None] * size for _ in range(size)]   # None = transparent
        self.mask = [[False] * size for _ in range(size)]  # character pixels

    # ---------------------------------------------------------- primitives
    def px(self, x, y, color):
        if 0 <= x < self.size and 0 <= y < self.size:
            self.grid[y][x] = color
            self.mask[y][x] = True

    def row(self, y, x0, x1, color):
        for x in range(x0, x1 + 1):
            self.px(x, y, color)

    def col(self, x, y0, y1, color):
        for y in range(y0, y1 + 1):
            self.px(x, y, color)

    def rect(self, x0, y0, x1, y1, color):
        for y in range(y0, y1 + 1):
            self.row(y, x0, x1, color)

    def fill(self, color):
        """Opaque background fill (not part of the character mask)."""
        for y in range(self.size):
            for x in range(self.size):
                self.grid[y][x] = color
                self.mask[y][x] = False

    def blit(self, layer, dx=0, dy=0):
        """Copy a layer's opaque pixels onto this canvas, offset by (dx,dy)."""
        for y in range(layer.size):
            for x in range(layer.size):
                color = layer.grid[y][x]
                if color is not None:
                    self.px(x + dx, y + dy, color)

    def paint_background(self, layer):
        """Copy a layer's pixels without adding them to the character mask."""
        for y in range(layer.size):
            for x in range(layer.size):
                color = layer.grid[y][x]
                if color is not None:
                    self.grid[y][x] = color

    # ---------------------------------------------------------- silhouette
    def outline_ring(self, color):
        """Trace a 1px outline around everything in the mask."""
        ring = []
        for y in range(self.size):
            for x in range(self.size):
                if self.mask[y][x]:
                    continue
                for ddx, ddy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nx, ny = x + ddx, y + ddy
                    if (0 <= nx < self.size and 0 <= ny < self.size
                            and self.mask[ny][nx]):
                        ring.append((x, y))
                        break
        for x, y in ring:
            self.grid[y][x] = color

    # ---------------------------------------------------------- output
    def to_image(self, scale):
        img = Image.new("RGB", (self.size, self.size))
        img.putdata([c or (0, 0, 0) for row in self.grid for c in row])
        if scale != 1:
            img = img.resize(
                (self.size * scale, self.size * scale), Image.NEAREST
            )
        return img
