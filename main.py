#!/usr/bin/env python3
"""THE WORLD TODAY - front page summing up world news of 18 November 2026.

Pure standard library: draws a 1024x1024 PNG with a hand-built rasterizer
and a hand-designed 5x7 bitmap font. Deterministic: fixed zlib level, no
timestamps, no randomness, no dict-order dependence.
"""
import os
import struct
import zlib

W, H = 1024, 1024

# ---------------------------------------------------------------- palette
PAPER = (246, 241, 227)
INK = (20, 33, 61)
RED = (180, 35, 24)
TEAL = (14, 107, 107)
GOLD = (176, 124, 0)
WHITE = (255, 255, 255)
PANEL = (255, 253, 245)
LINE = (20, 33, 61)
SOFT = (90, 96, 110)
SEA = (38, 84, 124)
SKY = (214, 232, 240)
SAND = (232, 214, 170)
TINTS = [(214, 232, 240), (248, 220, 216), (220, 238, 226),
         (250, 232, 196), (228, 222, 244), (220, 236, 236)]

# ---------------------------------------------------------------- 5x7 font
# Each glyph: 7 rows of 5 bits, "1" = ink. Designed from scratch here.
F = {}
def _g(ch, rows):
    F[ch] = rows
_g("A", ["01110", "10001", "10001", "11111", "10001", "10001", "10001"])
_g("B", ["11110", "10001", "10001", "11110", "10001", "10001", "11110"])
_g("C", ["01110", "10001", "10000", "10000", "10000", "10001", "01110"])
_g("D", ["11110", "10001", "10001", "10001", "10001", "10001", "11110"])
_g("E", ["11111", "10000", "10000", "11110", "10000", "10000", "11111"])
_g("F", ["11111", "10000", "10000", "11110", "10000", "10000", "10000"])
_g("G", ["01110", "10001", "10000", "10111", "10001", "10001", "01111"])
_g("H", ["10001", "10001", "10001", "11111", "10001", "10001", "10001"])
_g("I", ["01110", "00100", "00100", "00100", "00100", "00100", "01110"])
_g("J", ["00111", "00010", "00010", "00010", "00010", "10010", "01100"])
_g("K", ["10001", "10010", "10100", "11000", "10100", "10010", "10001"])
_g("L", ["10000", "10000", "10000", "10000", "10000", "10000", "11111"])
_g("M", ["10001", "11011", "10101", "10101", "10001", "10001", "10001"])
_g("N", ["10001", "11001", "10101", "10011", "10001", "10001", "10001"])
_g("O", ["01110", "10001", "10001", "10001", "10001", "10001", "01110"])
_g("P", ["11110", "10001", "10001", "11110", "10000", "10000", "10000"])
_g("Q", ["01110", "10001", "10001", "10001", "10101", "10010", "01101"])
_g("R", ["11110", "10001", "10001", "11110", "10100", "10010", "10001"])
_g("S", ["01111", "10000", "10000", "01110", "00001", "00001", "11110"])
_g("T", ["11111", "00100", "00100", "00100", "00100", "00100", "00100"])
_g("U", ["10001", "10001", "10001", "10001", "10001", "10001", "01110"])
_g("V", ["10001", "10001", "10001", "10001", "10001", "01010", "00100"])
_g("W", ["10001", "10001", "10001", "10101", "10101", "11011", "10001"])
_g("X", ["10001", "10001", "01010", "00100", "01010", "10001", "10001"])
_g("Y", ["10001", "10001", "01010", "00100", "00100", "00100", "00100"])
_g("Z", ["11111", "00001", "00010", "00100", "01000", "10000", "11111"])
_g("0", ["01110", "10001", "10011", "10101", "11001", "10001", "01110"])
_g("1", ["00100", "01100", "00100", "00100", "00100", "00100", "01110"])
_g("2", ["01110", "10001", "00001", "00010", "00100", "01000", "11111"])
_g("3", ["11111", "00010", "00100", "00010", "00001", "10001", "01110"])
_g("4", ["00010", "00110", "01010", "10010", "11111", "00010", "00010"])
_g("5", ["11111", "10000", "11110", "00001", "00001", "10001", "01110"])
_g("6", ["01110", "10000", "10000", "11110", "10001", "10001", "01110"])
_g("7", ["11111", "00001", "00010", "00100", "01000", "01000", "01000"])
_g("8", ["01110", "10001", "10001", "01110", "10001", "10001", "01110"])
_g("9", ["01110", "10001", "10001", "01111", "00001", "00001", "01110"])
_g(" ", ["00000", "00000", "00000", "00000", "00000", "00000", "00000"])
_g(".", ["00000", "00000", "00000", "00000", "00000", "01100", "01100"])
_g(",", ["00000", "00000", "00000", "00000", "01100", "00100", "01000"])
_g(":", ["00000", "01100", "01100", "00000", "01100", "01100", "00000"])
_g(";", ["00000", "01100", "01100", "00000", "01100", "00100", "01000"])
_g("'", ["00100", "00100", "01000", "00000", "00000", "00000", "00000"])
_g("-", ["00000", "00000", "00000", "01110", "00000", "00000", "00000"])
_g("(", ["00010", "00100", "01000", "01000", "01000", "00100", "00010"])
_g(")", ["01000", "00100", "00010", "00010", "00010", "00100", "01000"])
_g("/", ["00001", "00010", "00010", "00100", "01000", "01000", "10000"])
_g("&", ["01100", "10010", "10100", "01000", "10101", "10010", "01101"])
_g("%", ["11001", "11010", "00010", "00100", "01000", "01011", "10011"])
_g("+", ["00000", "00100", "00100", "01110", "00100", "00100", "00000"])
_g("=", ["00000", "00000", "11111", "00000", "11111", "00000", "00000"])
_g("!", ["00100", "00100", "00100", "00100", "00100", "00000", "00100"])
_g("?", ["01110", "10001", "00001", "00010", "00100", "00000", "00100"])
_g("$", ["00100", "01111", "10100", "01110", "00101", "11110", "00100"])

CHAR_W = 6  # 5 glyph columns + 1 spacing, times scale


def text_w(s, scale):
    return len(s) * CHAR_W * scale - scale


# ---------------------------------------------------------------- canvas
class Canvas:
    def __init__(self, w, h, bg):
        self.w, self.h = w, h
        self.px = bytearray(w * h * 3)
        self.fill_rect(0, 0, w, h, bg)

    def set(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i], self.px[i + 1], self.px[i + 2] = c

    def fill_rect(self, x, y, w, h, c):
        x0, y0 = max(0, x), max(0, y)
        x1, y1 = min(self.w, x + w), min(self.h, y + h)
        for yy in range(y0, y1):
            base = (yy * self.w + x0) * 3
            for xx in range(x0, x1):
                i = base + (xx - x0) * 3
                self.px[i], self.px[i + 1], self.px[i + 2] = c

    def rect(self, x, y, w, h, c, t=1):
        self.fill_rect(x, y, w, t, c)
        self.fill_rect(x, y + h - t, w, t, c)
        self.fill_rect(x, y, t, h, c)
        self.fill_rect(x + w - t, y, t, h, c)

    def hline(self, x, y, w, c, t=1):
        self.fill_rect(x, y, w, t, c)

    def vline(self, x, y, h, c, t=1):
        self.fill_rect(x, y, t, h, c)

    def line(self, x0, y0, x1, y1, c, t=1):
        dx, dy = abs(x1 - x0), abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy
        while True:
            self.fill_rect(x0 - t // 2, y0 - t // 2, t, t, c)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x0 += sx
            if e2 < dx:
                err += dx
                y0 += sy

    def disc(self, cx, cy, r, c):
        for yy in range(cy - r, cy + r + 1):
            for xx in range(cx - r, cx + r + 1):
                if (xx - cx) ** 2 + (yy - cy) ** 2 <= r * r:
                    self.set(xx, yy, c)

    def circle(self, cx, cy, r, c, t=2):
        for a in range(0, 360, 2):
            import math as _m
            self.fill_rect(int(cx + r * _m.cos(_m.radians(a))) - t // 2,
                           int(cy + r * _m.sin(_m.radians(a))) - t // 2,
                           t, t, c)

    def text(self, x, y, s, scale, c):
        cx = x
        for ch in s.upper():
            rows = F.get(ch, F["?"])
            for ry in range(7):
                row = rows[ry]
                for rx in range(5):
                    if row[rx] == "1":
                        self.fill_rect(cx + rx * scale, y + ry * scale,
                                       scale, scale, c)
            cx += CHAR_W * scale
        return cx

    def text_c(self, cx, y, s, scale, c):
        self.text(cx - text_w(s, scale) // 2, y, s, scale, c)


def wrap(s, max_chars):
    words, lines, cur = s.split(" "), [], ""
    for wd in words:
        nxt = wd if not cur else cur + " " + wd
        if len(nxt) <= max_chars:
            cur = nxt
        else:
            if cur:
                lines.append(cur)
            cur = wd
    if cur:
        lines.append(cur)
    return lines


# ---------------------------------------------------------------- pictograms
def icon(cv, kind, x, y, tint, ink):
    cv.fill_rect(x, y, 34, 34, tint)
    cv.rect(x, y, 34, 34, ink, 1)
    cx, cy = x + 17, y + 17
    if kind == "plane":  # Trump / Manila flight
        cv.fill_rect(x + 6, cy - 2, 22, 4, ink)
        cv.fill_rect(x + 12, cy - 9, 4, 18, ink)
        cv.fill_rect(x + 24, cy - 5, 6, 3, ink)
        cv.fill_rect(x + 24, cy + 3, 6, 3, ink)
    elif kind == "bridge":
        cv.line(x + 5, y + 26, x + 29, y + 26, ink, 2)
        cv.line(x + 5, y + 26, cx, y + 10, ink, 2)
        cv.line(x + 29, y + 26, cx, y + 10, ink, 2)
        cv.vline(cx, y + 10, 16, ink, 2)
        cv.vline(x + 11, y + 18, 8, ink, 2)
        cv.vline(x + 23, y + 18, 8, ink, 2)
    elif kind == "ship":  # Hormuz tanker
        cv.fill_rect(x + 6, y + 20, 22, 7, ink)
        cv.fill_rect(x + 9, y + 13, 6, 7, RED)
        cv.fill_rect(x + 16, y + 13, 6, 7, GOLD)
        cv.fill_rect(x + 23, y + 13, 4, 7, TEAL)
        cv.fill_rect(x + 24, y + 8, 2, 5, ink)
        cv.hline(x + 4, y + 29, 26, ink, 2)
    elif kind == "chip":  # Nvidia
        cv.fill_rect(x + 11, y + 11, 12, 12, ink)
        cv.fill_rect(x + 14, y + 14, 6, 6, tint)
        for px in (12, 17, 22):
            cv.vline(x + px, y + 6, 5, ink, 2)
            cv.vline(x + px, y + 23, 5, ink, 2)
            cv.hline(x + 6, y + px, 5, ink, 2)
            cv.hline(x + 23, y + px, 5, ink, 2)
    elif kind == "storm":  # cyclone
        cv.circle(cx, cy, 11, ink, 2)
        cv.circle(cx, cy, 6, ink, 2)
        cv.disc(cx, cy, 2, RED)
        cv.line(x + 5, y + 6, x + 12, y + 12, ink, 2)
        cv.line(x + 29, y + 28, x + 22, y + 22, ink, 2)
    elif kind == "trade":  # Canada-China
        cv.line(x + 6, y + 12, x + 28, y + 12, ink, 3)
        cv.line(x + 28, y + 12, x + 23, y + 8, ink, 2)
        cv.line(x + 28, y + 12, x + 23, y + 16, ink, 2)
        cv.line(x + 28, y + 22, x + 6, y + 22, ink, 3)
        cv.line(x + 6, y + 22, x + 11, y + 18, ink, 2)
        cv.line(x + 6, y + 22, x + 11, y + 26, ink, 2)
    elif kind == "ban":  # sanctions
        cv.circle(cx, cy, 11, ink, 2)
        cv.line(x + 9, y + 25, x + 25, y + 9, RED, 3)
    elif kind == "globe":  # Taiwan / UN
        cv.circle(cx, cy, 11, ink, 2)
        cv.vline(cx, y + 6, 22, ink, 1)
        cv.hline(x + 6, cy, 22, ink, 1)
        cv.line(x + 8, y + 10, x + 26, y + 10, ink, 1)
        cv.line(x + 8, y + 24, x + 26, y + 24, ink, 1)
    elif kind == "bars":  # UN toll
        for i, bh in enumerate((8, 14, 20)):
            cv.fill_rect(x + 8 + i * 7, y + 26 - bh, 5, bh, ink)
        cv.hline(x + 6, y + 27, 24, RED, 2)
    elif kind == "bowl":  # Gaza food
        cv.fill_rect(x + 8, y + 18, 18, 8, ink)
        cv.fill_rect(x + 6, y + 16, 22, 3, ink)
        cv.line(x + 13, y + 15, x + 13, y + 9, ink, 2)
        cv.line(x + 20, y + 15, x + 20, y + 9, ink, 2)
    elif kind == "pin":  # Sudan
        cv.disc(cx, y + 13, 8, RED)
        cv.disc(cx, y + 13, 3, WHITE)
        cv.line(cx - 6, y + 19, cx, y + 29, RED, 3)
        cv.line(cx + 6, y + 19, cx, y + 29, RED, 3)
    elif kind == "cup":  # SAFF trophy
        cv.fill_rect(x + 12, y + 8, 10, 9, GOLD)
        cv.fill_rect(x + 10, y + 8, 3, 6, GOLD)
        cv.fill_rect(x + 21, y + 8, 3, 6, GOLD)
        cv.fill_rect(cx - 1, y + 17, 2, 6, GOLD)
        cv.fill_rect(x + 11, y + 23, 12, 3, GOLD)


# ---------------------------------------------------------------- lead scene
def lead_scene(cv, x, y, w, h):
    # Flat scene, drawn entirely inside its own box: sky, sea, shore,
    # a radar dish on the Bahrain shore, drones above, a tanker at sea.
    cv.fill_rect(x, y, w, h, SKY)
    cv.fill_rect(x, y + h - 20, w, 20, SEA)
    cv.fill_rect(x, y + h - 24, w, 4, SAND)
    # radar dish on a mast at left, fully inside the box
    bx, by = x + 70, y + h - 24
    cv.fill_rect(bx - 3, by - 18, 6, 18, INK)
    cv.line(bx, by - 18, bx - 18, by - 34, INK, 3)
    cv.line(bx, by - 18, bx + 16, by - 32, INK, 3)
    cv.line(bx - 18, by - 34, bx + 16, by - 32, INK, 3)
    cv.circle(bx, by - 18, 22, TEAL, 2)
    cv.text(x + 8, y + h - 18, "BAHRAIN", 1, WHITE)
    # three drones with dotted trails, upper half of the sky
    for dx, dy in ((300, 8), (440, 4), (580, 10)):
        for t in range(0, 40, 10):
            cv.fill_rect(x + dx - t, y + dy + 2, 4, 3, SOFT)
        cv.fill_rect(x + dx, y + dy, 18, 5, INK)
        cv.fill_rect(x + dx + 6, y + dy - 4, 6, 4, INK)
        cv.fill_rect(x + dx - 3, y + dy + 1, 3, 3, RED)
    # small tanker on the sea at right
    sx = x + w - 200
    cv.fill_rect(sx, y + h - 14, 76, 8, INK)
    cv.fill_rect(sx + 12, y + h - 22, 20, 8, RED)
    cv.fill_rect(sx + 36, y + h - 22, 20, 8, WHITE)
    cv.rect(sx + 36, y + h - 22, 20, 8, INK, 1)
    cv.text(x + w - 252, y + 4, "STRAIT OF HORMUZ", 1, SOFT)


# ---------------------------------------------------------------- page
def build():
    cv = Canvas(W, H, PAPER)
    # ---- masthead
    cv.fill_rect(0, 0, W, 10, RED)
    cv.text_c(512, 22, "THE WORLD TODAY", 7, INK)
    cv.hline(24, 84, 976, INK, 3)
    cv.text_c(512, 96, "WEDNESDAY 18 NOVEMBER 2026", 4, RED)
    cv.text_c(512, 130, "ONE DAY. ONE PAGE. THE WORLD.", 2, SOFT)
    cv.hline(24, 152, 976, INK, 2)

    # ---- lead story
    lx, ly, lw, lh = 24, 164, 976, 196
    cv.fill_rect(lx, ly, lw, lh, PANEL)
    cv.rect(lx, ly, lw, lh, INK, 2)
    cv.fill_rect(lx, ly, lw, 26, RED)
    cv.text(lx + 12, ly + 6, "LEAD STORY  -  THE GULF", 2, WHITE)
    cv.text(lx + lw - 12 - text_w("18 NOV 2026", 2), ly + 6,
            "18 NOV 2026", 2, WHITE)
    cv.text_c(512, ly + 34, "DRONES OVER THE GULF", 6, INK)
    cv.text_c(512, ly + 84, "IRAN HITS US RADAR IN BAHRAIN", 3, RED)
    cv.text_c(512, ly + 112,
              "BAHRAIN SOUNDS ALL-CLEAR; KUWAIT SHOT DOWN DRONES", 2, INK)
    lead_scene(cv, lx + 12, ly + 132, lw - 24, 56)

    # ---- story grid: 12 panels, 3 columns x 4 rows
    stories = [
        ("ASIA", "plane", "TRUMP LANDS IN MANILA",
         "ASEAN TALKS, THEN CHINA"),
        ("EUROPE", "bridge", "UKRAINE HITS CRIMEA BRIDGE",
         "SECOND DAY IN A ROW"),
        ("GULF", "ship", "TANKER ATTACKED IN HORMUZ",
         "21 INDIANS EVACUATED"),
        ("TECH", "chip", "NVIDIA SALES DOUBLE",
         "$115.8BN IN A QUARTER"),
        ("ASIA", "storm", "CYCLONE AKVAN STRENGTHENS",
         "FLIGHTS CANCELLED"),
        ("AMERICAS", "trade", "CANADA, CHINA EXTEND DEALS",
         "XI MEETS CARNEY"),
        ("EUROPE", "ban", "BRITAIN SANCTIONS SETTLERS",
         "TWO-STATE PUSH"),
        ("ASIA", "globe", "US PRESSES UN OVER TAIWAN",
         "CHINA HITS BACK"),
        ("EUROPE", "bars", "UN: 372 CIVILIANS KILLED",
         "IN UKRAINE IN OCTOBER"),
        ("GULF", "bowl", "GAZA FAMILIES GET ONE MEAL",
         "EVERY TWO DAYS: WFP"),
        ("AFRICA", "pin", "SUDAN DEATH TOLL TOPS 2,230",
         "UN CONFIRMS FIGURE"),
        ("SPORT", "cup", "INDIA WIN 10TH SAFF TITLE",
         "BEAT PAKISTAN 2-1"),
    ]
    gx, gy = 24, 372
    pw, ph, gap = 318, 116, 11
    for i, (tag, kind, head, cap) in enumerate(stories):
        px = gx + (i % 3) * (pw + gap)
        py = gy + (i // 3) * (ph + gap)
        tint = TINTS[i % len(TINTS)]
        cv.fill_rect(px, py, pw, ph, PANEL)
        cv.rect(px, py, pw, ph, INK, 1)
        cv.fill_rect(px, py, pw, 5, RED if i % 3 == 0 else
                     (TEAL if i % 3 == 1 else GOLD))
        icon(cv, kind, px + 10, py + 12, tint, INK)
        cv.text(px + 52, py + 20, tag, 2, RED)
        lines = wrap(head, 16)
        for li, ln in enumerate(lines[:2]):
            cv.text(px + 10, py + 50 + li * 23, ln, 3, INK)
        cv.text(px + 10, py + 98, cap, 2, SOFT)

    # ---- region band (clean labelled strip, not a garbled map)
    by = 372 + 4 * ph + 3 * gap + 10  # 880
    cv.fill_rect(24, by, 976, 74, INK)
    cv.text(36, by + 8, "WHERE THE NEWS HAPPENED", 2, WHITE)
    regions = [("MIDDLE EAST", "3"), ("ASIA-PACIFIC", "4"),
               ("EUROPE", "3"), ("N. AMERICA", "2"), ("AFRICA", "1")]
    rx = 36
    for name, n in regions:
        cv.text(rx, by + 34, name, 2, (200, 210, 225))
        cv.text(rx, by + 52, n + " STORIES", 2, GOLD)
        rx += 196

    # ---- footer: date again, faithfulness line
    fy = by + 74 + 10  # 964
    cv.hline(24, fy, 976, INK, 2)
    cv.text_c(512, fy + 10,
              "WEDNESDAY 18 NOVEMBER 2026", 3, RED)
    cv.text_c(512, fy + 36,
              "ALL 13 STORIES ABOVE WERE REPORTED ON 18 NOVEMBER 2026",
              2, INK)
    return cv


def write_png(cv, path):
    raw = bytearray()
    for y in range(cv.h):
        raw.append(0)  # filter none
        raw += cv.px[y * cv.w * 3:(y + 1) * cv.w * 3]
    comp = zlib.compress(bytes(raw), 9)

    def chunk(tag, data):
        c = struct.pack(">I", len(data)) + tag + data
        return c + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", struct.pack(">IIBBBBB", cv.w, cv.h, 8, 2, 0, 0, 0))
    png += chunk(b"IDAT", comp)
    png += chunk(b"IEND", b"")
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "wb") as fh:
        fh.write(png)


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    write_png(build(), os.path.join(out_dir, "entry.png"))


if __name__ == "__main__":
    main()
