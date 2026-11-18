#!/usr/bin/env python3
"""THE WORLD TODAY - one image summing up Wednesday 18 November 2026.

Pure-stdlib front-page renderer: a hand-designed 5x7 bitmap font, a small
rasterizer, and a hand-rolled PNG encoder. No network, no randomness, no
timestamps in the output, so two runs write byte-identical files.

Design goal for this version: legibility at the same breadth as a 13-story
front page. No glyph is rendered smaller than ~17 px tall at 1024 px wide:
big headlines, one short deck line per story, generous white space.
"""

import os
import struct
import zlib

W, H = 1024, 1024
WHITE = (255, 255, 255)
BLACK = (10, 10, 10)
INK = (32, 32, 32)
RED = (178, 0, 0)
GREY = (205, 205, 205)

# ---------------------------------------------------------------- font
# 5x7 bitmap glyphs, written out by hand for this entry. "#" is a set pixel.
FONT = {
    "A": (".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "B": ("####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."),
    "C": (".####", "#....", "#....", "#....", "#....", "#....", ".####"),
    "D": ("####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."),
    "E": ("#####", "#....", "#....", "####.", "#....", "#....", "#####"),
    "F": ("#####", "#....", "#....", "####.", "#....", "#....", "#...."),
    "G": (".####", "#....", "#....", "#.###", "#...#", "#...#", ".###."),
    "H": ("#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "I": ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "#####"),
    "J": ("..###", "...#.", "...#.", "...#.", "...#.", "#..#.", ".##.."),
    "K": ("#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"),
    "L": ("#....", "#....", "#....", "#....", "#....", "#....", "#####"),
    "M": ("#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"),
    "N": ("#...#", "##..#", "#.#.#", "#..##", "#...#", "#...#", "#...#"),
    "O": (".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "P": ("####.", "#...#", "#...#", "####.", "#....", "#....", "#...."),
    "Q": (".###.", "#...#", "#...#", "#...#", "#.#.#", "#..#.", ".##.#"),
    "R": ("####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"),
    "S": (".####", "#....", "#....", ".###.", "....#", "....#", "####."),
    "T": ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."),
    "U": ("#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "V": ("#...#", "#...#", "#...#", "#...#", "#...#", ".#.#.", "..#.."),
    "W": ("#...#", "#...#", "#...#", "#.#.#", "#.#.#", "##.##", "#...#"),
    "X": ("#...#", "#...#", ".#.#.", "..#..", ".#.#.", "#...#", "#...#"),
    "Y": ("#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."),
    "Z": ("#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"),
    "0": (".###.", "#...#", "#..##", "#.#.#", "##..#", "#...#", ".###."),
    "1": ("..#..", ".##..", "..#..", "..#..", "..#..", "..#..", ".###."),
    "2": (".###.", "#...#", "....#", "...#.", "..#..", ".#...", "#####"),
    "3": ("####.", "....#", "....#", ".###.", "....#", "....#", "####."),
    "4": ("...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#."),
    "5": ("#####", "#....", "####.", "....#", "....#", "#...#", ".###."),
    "6": (".###.", "#....", "#....", "####.", "#...#", "#...#", ".###."),
    "7": ("#####", "....#", "...#.", "..#..", ".#...", ".#...", ".#..."),
    "8": (".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."),
    "9": (".###.", "#...#", "#...#", ".####", "....#", "....#", ".###."),
    " ": (".....", ".....", ".....", ".....", ".....", ".....", "....."),
    ".": (".....", ".....", ".....", ".....", ".....", ".##..", ".##.."),
    ",": (".....", ".....", ".....", ".....", ".....", ".##..", "..#.."),
    "-": (".....", ".....", ".....", "#####", ".....", ".....", "....."),
    ":": (".....", ".##..", ".##..", ".....", ".##..", ".##..", "....."),
    ";": (".....", ".##..", ".##..", ".....", ".##..", ".##..", "..#.."),
    "'": ("..#..", "..#..", ".#...", ".....", ".....", ".....", "....."),
    "(": ("...##", "..#..", ".#...", ".#...", ".#...", "..#..", "...##"),
    ")": ("##...", "..#..", "...#.", "...#.", "...#.", "..#..", "##..."),
    "/": ("....#", "....#", "...#.", "..#..", ".#...", "#....", "#...."),
    "&": (".##..", "#..#.", "#..#.", ".#...", "#.#.#", "#..#.", ".##.#"),
    "%": ("##..#", "##.#.", "...#.", "..#..", ".#...", "#.#.#", "#..##"),
    "$": ("..#..", ".####", "#.#.#", ".###.", "..#.#", "####.", "..#.."),
    "!": ("..#..", "..#..", "..#..", "..#..", "..#..", ".....", "..#.."),
    "?": (".###.", "#...#", "....#", "...#.", "..#..", ".....", "..#.."),
    "+": (".....", "..#..", "..#..", ".###.", "..#..", "..#..", "....."),
    "=": (".....", ".....", "#####", ".....", "#####", ".....", "....."),
    '"': (".#.#.", ".#.#.", ".....", ".....", ".....", ".....", "....."),
}

# ---------------------------------------------------------------- canvas
class Canvas:
    def __init__(self, w, h, bg):
        self.w = w
        self.h = h
        self.px = bytearray(bg * w * h)

    def rect(self, x, y, rw, rh, color):
        x0, y0 = max(0, x), max(0, y)
        x1, y1 = min(self.w, x + rw), min(self.h, y + rh)
        if x1 <= x0 or y1 <= y0:
            return
        r, g, b = color
        for yy in range(y0, y1):
            base = (yy * self.w + x0) * 3
            for xx in range(x0, x1):
                i = base + (xx - x0) * 3
                self.px[i] = r
                self.px[i + 1] = g
                self.px[i + 2] = b

    def text_width(self, text, scale):
        return int(round(len(text) * 6 * scale))

    def draw_text(self, x, y, text, scale, color, align="left", bold=False):
        if align == "center":
            x -= self.text_width(text, scale) // 2
        cx = float(x)
        for ch in text:
            glyph = FONT.get(ch)
            if glyph is None:
                raise ValueError("no glyph for %r" % ch)
            for gy, row in enumerate(glyph):
                for gx, bit in enumerate(row):
                    if bit == "#":
                        px = int(round(cx + gx * scale))
                        py = int(round(y + gy * scale))
                        pw = max(1, int(round(scale))) + (1 if bold else 0)
                        ph = max(1, int(round(scale)))
                        self.rect(px, py, pw, ph, color)
            cx += 6 * scale

# ---------------------------------------------------------------- content
# 13 stories of Wednesday 18 November 2026, picked fresh from that day's
# reporting. Headlines are pre-split into two short lines so every line
# fits its column at a large size; each deck is a single short line.
LEAD_KICKER = "LEAD STORY - U.S.-IRAN WAR ESCALATES"
LEAD_HEAD = ("US SINKS FIVE IRANIAN", "TANKERS AS IRAN HITS BACK")
LEAD_DECK = "IRAN HITS SHIPS NEAR HORMUZ, A US BASE IN JORDAN"

STORIES = [
    (("KERCH BRIDGE HIT", "FOR SECOND NIGHT"), "RUSSIA HITS KYIV BRIDGES"),
    (("GAZA FACES COLD", "AS AID STALLS"), "UN WARNS OF WINTER DEATHS"),
    (("TRUMP IN MANILA", "FOR QUAD SUMMIT"), "CHINA VISIT AND APEC NEXT"),
    (("EISENKOT TAPPED TO", "FORM GOVERNMENT"), "HERZOG BYPASSES NETANYAHU"),
    (("NORTH KOREA FIRES", "MISSILE TO SEA"), "SEOUL CONFIRMS LAUNCH"),
    (("DOW SINKS 876 AS", "FED HIKES LOOM"), "OIL NEAR $93 ON GULF RISK"),
    (("COP31 TALKS ENTER", "DECISIVE PHASE"), "144 ITEMS STILL DISPUTED"),
    (("CYCLONE AKVAN", "BEARS DOWN ON INDIA"), "COAST STATES ON HIGH ALERT"),
    (("RUSSIAN PLANE", "CRASH KILLS 19"), "AN-12 DOWN IN KEMEROVO"),
    (("US MEASLES CASES", "HIT 40-YEAR HIGH"), "VACCINATION RATES FALLING"),
    (("WHITE HOUSE DROPS", "FDA NOMINEE"), "OVERTON PULLED BEFORE VOTE"),
    (("VOYAGER 1 REACHES", "ONE LIGHT-DAY OUT"), "FARTHEST HUMAN OBJECT EVER"),
]

FOOTER = "13 STORIES - WEDNESDAY 18 NOVEMBER 2026"

# ---------------------------------------------------------------- layout
def render():
    c = Canvas(W, H, WHITE)
    cx = W // 2

    c.rect(0, 0, W, 10, RED)

    # Masthead.
    c.draw_text(cx, 26, "THE WORLD TODAY", 9, BLACK, align="center")
    # Date, in red.
    c.draw_text(cx, 102, "WEDNESDAY 18 NOVEMBER 2026", 4, RED, align="center")
    c.rect(36, 140, 952, 4, BLACK)

    # Lead story: big two-line headline, one-line deck.
    c.draw_text(cx, 158, LEAD_KICKER, 3, RED, align="center")
    c.draw_text(cx, 192, LEAD_HEAD[0], 6, BLACK, align="center")
    c.draw_text(cx, 240, LEAD_HEAD[1], 6, BLACK, align="center")
    c.draw_text(cx, 294, LEAD_DECK, 3, INK, align="center")
    c.rect(36, 328, 952, 4, BLACK)

    # Grid: 2 columns x 6 rows of the remaining 12 stories.
    head_scale, deck_scale = 3.5, 2.5
    col_x = (36, 532)
    col_w = 456
    top, row_h = 346, 106
    for i, (lines, deck) in enumerate(STORIES):
        row, col = divmod(i, 2)
        x = col_x[col]
        y = top + row * row_h
        # Red tick marks the story.
        c.rect(x, y + 8, 10, 10, RED)
        for j, line in enumerate(lines):
            if c.text_width(line, head_scale) > col_w - 20:
                raise ValueError("headline too wide: %r" % line)
            c.draw_text(x + 20, y + j * 29, line, head_scale, BLACK)
        if c.text_width(deck, deck_scale) > col_w - 20:
            raise ValueError("deck too wide: %r" % deck)
        c.draw_text(x + 20, y + 66, deck, deck_scale, INK, bold=True)
        if row < 5:
            c.rect(36, y + row_h - 8, 952, 2, GREY)
    c.rect(510, top, 2, 6 * row_h - 8, GREY)

    # Footer.
    c.draw_text(cx, 992, FOOTER, 2.5, INK, align="center", bold=True)
    return c

# ---------------------------------------------------------------- png
def chunk(kind, data):
    out = struct.pack(">I", len(data)) + kind + data
    out += struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
    return out

def encode_png(c):
    raw = bytearray()
    for yy in range(c.h):
        raw.append(0)  # filter: none
        raw += c.px[yy * c.w * 3:(yy + 1) * c.w * 3]
    ihdr = struct.pack(">IIBBBBB", c.w, c.h, 8, 2, 0, 0, 0)
    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", ihdr)
    png += chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    png += chunk(b"IEND", b"")
    return png

def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    png = encode_png(render())
    with open(os.path.join(out_dir, "entry.png"), "wb") as f:
        f.write(png)

if __name__ == "__main__":
    main()
