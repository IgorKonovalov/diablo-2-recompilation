"""Minimal PNG writer for 8-bit indexed images (stdlib only: zlib + struct).

Used by the render subcommands in tools/ (dt1.py, ds1.py, ...). Not a command-line tool.

  write_indexed(path, width, height, pixels, palette_rgb, transparent=(0,))
    pixels: bytes/bytearray of width*height palette indices, row-major, top row first.
    palette_rgb: 768 bytes, R,G,B per entry (see tools/palette.py for the pal.dat order).
    transparent: indices written with alpha 0 (tRNS chunk). Index 0 by default.
"""
import os
import struct
import zlib


def _chunk(kind, data):
    return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)


def encode_indexed(width, height, pixels, palette_rgb, transparent=(0,)):
    if width <= 0 or height <= 0:
        width, height, pixels = 1, 1, b"\0"
    if len(pixels) != width * height or len(palette_rgb) != 768:
        raise ValueError("pixel or palette size mismatch")
    raw = bytearray()
    for y in range(height):
        raw.append(0)  # filter type 0 (none)
        raw += pixels[y * width:(y + 1) * width]
    out = b"\x89PNG\r\n\x1a\n"
    out += _chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 3, 0, 0, 0))
    out += _chunk(b"PLTE", bytes(palette_rgb))
    if transparent:
        alpha = bytearray(b"\xff" * (max(transparent) + 1))
        for i in transparent:
            alpha[i] = 0
        out += _chunk(b"tRNS", bytes(alpha))
    out += _chunk(b"IDAT", zlib.compress(bytes(raw), 6))
    out += _chunk(b"IEND", b"")
    return out


def write_indexed(path, width, height, pixels, palette_rgb, transparent=(0,)):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "wb") as f:
        f.write(encode_indexed(width, height, pixels, palette_rgb, transparent))
