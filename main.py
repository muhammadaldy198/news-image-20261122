#!/usr/bin/env python3
"""News Image 22 - one front page for Sunday 22 November 2026.

The artwork committed beside this program, art.png, is a flat editorial
front page drawn for the day the contest names:

  - hero panel: an oil tanker burning in the Strait of Hormuz, the
    narrow channel where two tankers were struck by projectiles and a
    third caught fire after hitting a mine, as reported that weekend
    by UKMTO and carried by Reuters and AP;
  - the COP31 climate summit in Antalya running into a second day of
    overtime past midnight, deadlocked over fossil fuels;
  - Mexican special forces capturing cartel boss Fausto Isidro Meza
    Flores, "El Chapo Isidro", in Guasave, Sinaloa, in a raid that
    left eleven people dead;
  - a Ukrainian city under air-defence searchlights as Russia struck
    Kryvyi Rih with a ballistic missile.

The artwork deliberately leaves its masthead band empty. This program
finishes the page: it decodes art.png with a small pure-Python PNG
reader, locates the navy band at the top, and prints the date the page
sums up - "22 NOVEMBER 2026" - into the band with a hand-drawn 5x7
bitmap typeface, then writes the finished page to /output/entry.png.

Standard library only. No network, no randomness, no clock reads: the
output is a pure function of art.png, so two runs write identical
bytes.
"""

import os
import struct
import sys
import zlib

DATE_LINE = "22 NOVEMBER 2026"
INK = (248, 200, 96)        # masthead gold
MAX_BYTES = 1048576         # the gate's 1 MiB cap
MAX_SIDE = 1024             # the gate's 1024x1024 cap

# A 5x7 bitmap typeface, one string per row, '#' for a lit pixel.
# Only the shapes the date line needs are load-bearing, but the full
# alphabet is here so the masthead can be reworded by hand.
GLYPHS = {
    "0": (".###.", "#...#", "#..##", "#.#.#", "##..#", "#...#", ".###."),
    "1": ("..#..", ".##..", "..#..", "..#..", "..#..", "..#..", ".###."),
    "2": (".###.", "#...#", "....#", "...#.", "..#..", ".#...", "#####"),
    "3": (".###.", "#...#", "....#", "..##.", "....#", "#...#", ".###."),
    "4": ("...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#."),
    "5": ("#####", "#....", "####.", "....#", "....#", "#...#", ".###."),
    "6": (".###.", "#....", "#....", "####.", "#...#", "#...#", ".###."),
    "7": ("#####", "....#", "...#.", "..#..", "..#..", "..#..", "..#.."),
    "8": (".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."),
    "9": (".###.", "#...#", "#...#", ".####", "....#", "....#", ".###."),
    "A": (".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "B": ("####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."),
    "C": (".###.", "#...#", "#....", "#....", "#....", "#...#", ".###."),
    "D": ("####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."),
    "E": ("#####", "#....", "#....", "####.", "#....", "#....", "#####"),
    "F": ("#####", "#....", "#....", "####.", "#....", "#....", "#...."),
    "G": (".###.", "#...#", "#....", "#.###", "#...#", "#...#", ".###."),
    "H": ("#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "I": (".###.", "..#..", "..#..", "..#..", "..#..", "..#..", ".###."),
    "J": ("..###", "...#.", "...#.", "...#.", "...#.", "#..#.", ".##.."),
    "K": ("#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"),
    "L": ("#....", "#....", "#....", "#....", "#....", "#....", "#####"),
    "M": ("#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"),
    "N": ("#...#", "##..#", "##..#", "#.#.#", "#..##", "#..##", "#...#"),
    "O": (".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "P": ("####.", "#...#", "#...#", "####.", "#....", "#....", "#...."),
    "Q": (".###.", "#...#", "#...#", "#...#", "#.#.#", "#..#.", ".##.#"),
    "R": ("####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"),
    "S": (".####", "#....", "#....", ".###.", "....#", "....#", "####."),
    "T": ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."),
    "U": ("#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "V": ("#...#", "#...#", "#...#", "#...#", "#...#", ".#.#.", "..#.."),
    "W": ("#...#", "#...#", "#...#", "#.#.#", "#.#.#", "#.#.#", ".#.#."),
    "X": ("#...#", ".#.#.", "..#..", "..#..", "..#..", ".#.#.", "#...#"),
    "Y": ("#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."),
    "Z": ("#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"),
    " ": (".....", ".....", ".....", ".....", ".....", ".....", "....."),
    "-": (".....", ".....", ".....", "#####", ".....", ".....", "....."),
}


# ---------------------------------------------------------------- PNG in

def _paeth(a, b, c):
    """PNG's Paeth predictor: whichever of a, b, c sits closest to a+b-c."""
    guess = a + b - c
    da, db, dc = abs(guess - a), abs(guess - b), abs(guess - c)
    if da <= db and da <= dc:
        return a
    return b if db <= dc else c


def decode_png(path):
    """Read an 8-bit RGB or RGBA PNG (no interlace) as (w, h, bytearray).

    The returned buffer is packed RGB, three bytes per pixel, row-major.
    Anything outside that small family raises ValueError: the committed
    artwork is produced to fit it, and a loud failure beats a wrong page.
    """
    with open(path, "rb") as fh:
        blob = fh.read()
    if blob[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("artwork is not a PNG")
    width = height = depth = colour = interlace = None
    idat = bytearray()
    pos = 8
    while pos + 12 <= len(blob):
        (size,) = struct.unpack_from(">I", blob, pos)
        kind = blob[pos + 4:pos + 8]
        body = blob[pos + 8:pos + 8 + size]
        if kind == b"IHDR":
            width, height, depth, colour, _c, _f, interlace = \
                struct.unpack(">IIBBBBB", body)
        elif kind == b"IDAT":
            idat += body
        elif kind == b"IEND":
            break
        pos += 12 + size
    if depth != 8 or colour not in (2, 6) or interlace != 0:
        raise ValueError("unsupported PNG variant")
    channels = 3 if colour == 2 else 4
    stride = width * channels
    raw = zlib.decompress(bytes(idat))
    pixels = bytearray(width * height * 3)
    prior = bytearray(stride)
    src = 0
    for y in range(height):
        filt = raw[src]
        src += 1
        row = bytearray(raw[src:src + stride])
        src += stride
        if filt == 1:                        # Sub
            for i in range(channels, stride):
                row[i] = (row[i] + row[i - channels]) & 0xFF
        elif filt == 2:                      # Up
            for i in range(stride):
                row[i] = (row[i] + prior[i]) & 0xFF
        elif filt == 3:                      # Average
            for i in range(stride):
                left = row[i - channels] if i >= channels else 0
                row[i] = (row[i] + ((left + prior[i]) >> 1)) & 0xFF
        elif filt == 4:                      # Paeth
            for i in range(stride):
                a = row[i - channels] if i >= channels else 0
                b = prior[i]
                c = prior[i - channels] if i >= channels else 0
                row[i] = (row[i] + _paeth(a, b, c)) & 0xFF
        elif filt != 0:
            raise ValueError("bad PNG filter %d" % filt)
        if channels == 3:
            pixels[y * width * 3:(y + 1) * width * 3] = row
        else:                                # drop the alpha channel
            flat = pixels[y * width * 3:(y + 1) * width * 3]
            for x in range(width):
                flat[x * 3:x * 3 + 3] = row[x * 4:x * 4 + 3]
            pixels[y * width * 3:(y + 1) * width * 3] = flat
        prior = row
    return width, height, pixels


# --------------------------------------------------------------- PNG out

def _apply_filter(kind, row, prior, bpp):
    """One scanline, filtered with PNG filter `kind`, as bytes."""
    if kind == 0:
        return bytes(row)
    out = bytearray(len(row))
    for i, value in enumerate(row):
        left = row[i - bpp] if i >= bpp else 0
        if kind == 1:
            out[i] = (value - left) & 0xFF
        elif kind == 2:
            out[i] = (value - prior[i]) & 0xFF
        elif kind == 3:
            out[i] = (value - ((left + prior[i]) >> 1)) & 0xFF
        else:
            up_left = prior[i - bpp] if i >= bpp else 0
            out[i] = (value - _paeth(left, prior[i], up_left)) & 0xFF
    return bytes(out)


def _filter_cost(filtered):
    """Rough entropy proxy: bytes near 0 (either side) cost little."""
    return sum(v if v < 128 else 256 - v for v in filtered)


def encode_png(width, height, pixels):
    """Encode packed RGB pixels as deterministic PNG bytes.

    Every row independently picks the cheapest of the five PNG filters
    under _filter_cost, ties going to the lower filter number, so the
    same pixels always produce the same file.
    """
    stride = width * 3
    stream = bytearray()
    prior = bytearray(stride)
    for y in range(height):
        row = pixels[y * stride:(y + 1) * stride]
        chosen_kind, chosen = 0, None
        chosen_cost = None
        for kind in range(5):
            trial = _apply_filter(kind, row, prior, 3)
            cost = _filter_cost(trial)
            if chosen_cost is None or cost < chosen_cost:
                chosen_kind, chosen, chosen_cost = kind, trial, cost
        stream.append(chosen_kind)
        stream += chosen
        prior = bytearray(row)

    def chunk(kind, body):
        return (struct.pack(">I", len(body)) + kind + body
                + struct.pack(">I", zlib.crc32(kind + body) & 0xFFFFFFFF))

    header = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", header)
            + chunk(b"IDAT", zlib.compress(bytes(stream), 9))
            + chunk(b"IEND", b""))


# -------------------------------------------------------------- masthead

def _looks_navy(r, g, b):
    """The masthead's deep blue: blue clearly dominant, nothing bright."""
    return b - r >= 25 and b - g >= 12 and r <= 90 and b <= 170


def _row_is_navy(pixels, width, y):
    """True when a row reads as masthead navy on a 16-pixel sample grid."""
    base = y * width * 3
    hits = total = 0
    for x in range(0, width, 16):
        i = base + x * 3
        total += 1
        if _looks_navy(pixels[i], pixels[i + 1], pixels[i + 2]):
            hits += 1
    return hits * 10 >= total * 9


def masthead_span(pixels, width, height):
    """(top, bottom) of the masthead band, bottom exclusive.

    The artwork frames its front page with a pale margin, so the band
    does not start at row 0: skip leading rows until the first navy
    one, then run while rows stay navy. The run ends at the pale
    gutter the artwork keeps under the band, above the hero panel.
    Returns (0, 0) when no navy row shows up in the top half.
    """
    top = None
    bottom = 0
    for y in range(height // 2):
        if _row_is_navy(pixels, width, y):
            if top is None:
                top = y
            bottom = y + 1
        elif top is not None:
            break
    if top is None:
        return 0, 0
    return top, bottom


def stamp_date(pixels, width, top, band):
    """Print DATE_LINE, centred, inside the masthead band.

    The glyph grid is used exactly as drawn: widening the strokes was
    tried on the sister entry and merged the counters of 0 and 6 at
    thumbnail size, so the plain 5x7 shapes are what ships.
    """
    scale = max(1, int(band * 0.62) // 7)
    text_w = (len(DATE_LINE) * 6 - 1) * scale
    left = (width - text_w) // 2
    top = top + (band - 7 * scale) // 2
    red, green, blue = INK
    for n, ch in enumerate(DATE_LINE):
        glyph = GLYPHS[ch]
        gx = left + n * 6 * scale
        for row_i, row in enumerate(glyph):
            for col_i, mark in enumerate(row):
                if mark != "#":
                    continue
                for dy in range(scale):
                    base = ((top + row_i * scale + dy) * width
                            + gx + col_i * scale) * 3
                    for dx in range(scale):
                        i = base + dx * 3
                        pixels[i] = red
                        pixels[i + 1] = green
                        pixels[i + 2] = blue


# --------------------------------------------------------------- scaling

def shrink_pixels(pixels, width, height, num, den):
    """Area-average downscale by the exact fraction num/den (< 1).

    Each output pixel averages the source rectangle it maps to, with
    integer boundaries throughout, so the result depends only on the
    input pixels - never on platform float behaviour.
    """
    new_w = max(1, width * num // den)
    new_h = max(1, height * num // den)
    out = bytearray(new_w * new_h * 3)
    for y in range(new_h):
        y0 = y * den // num
        y1 = max(y0 + 1, (y + 1) * den // num)
        for x in range(new_w):
            x0 = x * den // num
            x1 = max(x0 + 1, (x + 1) * den // num)
            count = (x1 - x0) * (y1 - y0)
            for ch in range(3):
                total = 0
                for sy in range(y0, y1):
                    base = (sy * width + x0) * 3 + ch
                    for sx in range(x0, x1):
                        total += pixels[base + (sx - x0) * 3]
                out[(y * new_w + x) * 3 + ch] = total // count
    return new_w, new_h, out


# ------------------------------------------------------------------ main

def build(art_path):
    """Artwork path in, finished entry.png bytes out.

    The page is stamped at the artwork's own size first; only if the
    encoded page would break a gate cap does the shrink ladder step
    in, walking the finished page down by fifteenths until it fits.
    Every step is deterministic, so the ladder cannot make two runs
    disagree.
    """
    width, height, pixels = decode_png(art_path)
    while width > MAX_SIDE or height > MAX_SIDE:
        width, height, pixels = shrink_pixels(pixels, width, height, 15, 16)
    top, bottom = masthead_span(pixels, width, height)
    if bottom - top < 21:
        raise ValueError("no masthead band found in the artwork")
    stamp_date(pixels, width, top, bottom - top)
    data = encode_png(width, height, pixels)
    while len(data) > MAX_BYTES and width > 640:
        width, height, pixels = shrink_pixels(pixels, width, height, 15, 16)
        data = encode_png(width, height, pixels)
    return data


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    data = build(os.path.join(here, "art.png"))
    if len(data) > MAX_BYTES:
        raise ValueError("finished page exceeds the 1 MiB gate cap")
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "entry.png"), "wb") as fh:
        fh.write(data)
    return 0


if __name__ == "__main__":
    sys.exit(main())
