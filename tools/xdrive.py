#!/usr/bin/env python3
"""Drive an X display for runtime experiments: click, type, screenshot.

The game runs on its own rootful Xwayland display (e.g. :7), so nothing here
touches the user's desktop. Uses ctypes on libX11 / libXtst only; no deps.
Don't move wine's windows with X calls: wine keeps its own idea of where the
window is, and input gets mapped wrongly. Use --window offsets instead.

    python3 -I tools/xdrive.py --display :7 --window "Diablo II" click 400 307   # window-relative
    python3 -I tools/xdrive.py --display :7 shot out.png          # whole root
    python3 -I tools/xdrive.py --display :7 --window "Diablo II" rclick 678 345   # right button
    python3 -I tools/xdrive.py --display :7 key Return
    python3 -I tools/xdrive.py --display :7 type harness
    python3 -I tools/xdrive.py --display :7 run steps.txt   # one command per line, plus 'sleep S'

Without --window, coordinates are root-window pixels.
"""
import argparse
import ctypes as C
import struct
import sys
import time
import zlib

GAME_W, GAME_H = 800, 600  # window-relative screenshots crop to the game's client size

X11 = C.CDLL("libX11.so.6")
XTST = C.CDLL("libXtst.so.6")

X11.XOpenDisplay.restype = C.c_void_p
X11.XOpenDisplay.argtypes = [C.c_char_p]
X11.XDefaultRootWindow.restype = C.c_ulong
X11.XDefaultRootWindow.argtypes = [C.c_void_p]
X11.XDisplayWidth.argtypes = [C.c_void_p, C.c_int]
X11.XDisplayHeight.argtypes = [C.c_void_p, C.c_int]
X11.XFlush.argtypes = [C.c_void_p]
X11.XSync.argtypes = [C.c_void_p, C.c_int]
X11.XStringToKeysym.restype = C.c_ulong
X11.XStringToKeysym.argtypes = [C.c_char_p]
X11.XKeysymToKeycode.restype = C.c_ubyte
X11.XKeysymToKeycode.argtypes = [C.c_void_p, C.c_ulong]
X11.XGetImage.restype = C.c_void_p
X11.XGetImage.argtypes = [C.c_void_p, C.c_ulong, C.c_int, C.c_int, C.c_uint, C.c_uint,
                          C.c_ulong, C.c_int]
X11.XQueryTree.argtypes = [C.c_void_p, C.c_ulong, C.POINTER(C.c_ulong), C.POINTER(C.c_ulong),
                           C.POINTER(C.POINTER(C.c_ulong)), C.POINTER(C.c_uint)]
X11.XFetchName.argtypes = [C.c_void_p, C.c_ulong, C.POINTER(C.c_char_p)]
X11.XTranslateCoordinates.argtypes = [C.c_void_p, C.c_ulong, C.c_ulong, C.c_int, C.c_int,
                                      C.POINTER(C.c_int), C.POINTER(C.c_int), C.POINTER(C.c_ulong)]
XTST.XTestFakeMotionEvent.argtypes = [C.c_void_p, C.c_int, C.c_int, C.c_int, C.c_ulong]
XTST.XTestFakeButtonEvent.argtypes = [C.c_void_p, C.c_uint, C.c_int, C.c_ulong]
XTST.XTestFakeKeyEvent.argtypes = [C.c_void_p, C.c_uint, C.c_int, C.c_ulong]


class XImage(C.Structure):  # only the leading fields we read
    _fields_ = [("width", C.c_int), ("height", C.c_int), ("xoffset", C.c_int),
                ("format", C.c_int), ("data", C.POINTER(C.c_ubyte)),
                ("byte_order", C.c_int), ("bitmap_unit", C.c_int),
                ("bitmap_bit_order", C.c_int), ("bitmap_pad", C.c_int),
                ("depth", C.c_int), ("bytes_per_line", C.c_int),
                ("bits_per_pixel", C.c_int)]


class Display:
    def __init__(self, name):
        self.d = X11.XOpenDisplay(name.encode())
        if not self.d:
            sys.exit(f"cannot open display {name}")
        self.root = X11.XDefaultRootWindow(self.d)

    def find(self, title, win=None):
        """Depth-first search for a window whose WM_NAME equals title."""
        win = win or self.root
        name = C.c_char_p()
        if X11.XFetchName(self.d, win, C.byref(name)) and name.value == title.encode():
            return win
        r, p, kids, n = C.c_ulong(), C.c_ulong(), C.POINTER(C.c_ulong)(), C.c_uint()
        if not X11.XQueryTree(self.d, win, C.byref(r), C.byref(p), C.byref(kids), C.byref(n)):
            return None
        for i in range(n.value):
            hit = self.find(title, kids[i])
            if hit:
                return hit
        return None

    def origin(self, title):
        """Root coordinates of the named window's top-left corner."""
        win = self.find(title)
        if not win:
            sys.exit(f"no window named {title!r}")
        x, y, child = C.c_int(), C.c_int(), C.c_ulong()
        X11.XTranslateCoordinates(self.d, win, self.root, 0, 0, C.byref(x), C.byref(y), C.byref(child))
        return x.value, y.value

    def flush(self):
        X11.XSync(self.d, 0)

    def move(self, x, y):
        XTST.XTestFakeMotionEvent(self.d, -1, x, y, 0)
        self.flush()

    def click(self, x, y, button=1, hold=0.25):
        self.move(x, y)
        time.sleep(0.2)  # the game samples the pointer once per frame
        XTST.XTestFakeButtonEvent(self.d, button, 1, 0)
        self.flush()
        time.sleep(hold)
        XTST.XTestFakeButtonEvent(self.d, button, 0, 0)
        self.flush()

    def key(self, name, hold=0.05):
        ks = X11.XStringToKeysym(name.encode())
        kc = X11.XKeysymToKeycode(self.d, ks)
        if not kc:
            sys.exit(f"no keycode for {name!r}")
        XTST.XTestFakeKeyEvent(self.d, kc, 1, 0)
        self.flush()
        time.sleep(hold)
        XTST.XTestFakeKeyEvent(self.d, kc, 0, 0)
        self.flush()

    def type(self, text):
        for ch in text:
            self.key(ch)
            time.sleep(0.03)

    def shot(self, path, x=0, y=0, w=None, h=None):
        rw, rh = X11.XDisplayWidth(self.d, 0), X11.XDisplayHeight(self.d, 0)
        w = min(w or rw, rw - x)  # XGetImage fails with BadMatch past the root's edge
        h = min(h or rh, rh - y)
        img = X11.XGetImage(self.d, self.root, x, y, w, h, 0xFFFFFFFF, 2)  # ZPixmap
        if not img:
            sys.exit("XGetImage failed")
        im = XImage.from_address(img)
        if im.bits_per_pixel != 32:
            sys.exit(f"unsupported bpp {im.bits_per_pixel}")
        raw = C.string_at(im.data, im.bytes_per_line * h)
        rows = []
        for r in range(h):
            line = raw[r * im.bytes_per_line: r * im.bytes_per_line + 4 * w]
            # BGRX little-endian -> RGB
            rgb = bytearray(3 * w)
            rgb[0::3] = line[2::4]
            rgb[1::3] = line[1::4]
            rgb[2::3] = line[0::4]
            rows.append(b"\0" + bytes(rgb))
        write_png(path, w, h, b"".join(rows))


def write_png(path, w, h, filtered):
    def chunk(tag, data):
        c = struct.pack(">I", len(data)) + tag + data
        return c + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
    png = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
    png += chunk(b"IDAT", zlib.compress(filtered, 6)) + chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(png)


def do(dpy, argv, off=None):
    cmd, *a = argv
    if cmd in ("click", "rclick", "dclick", "move"):
        ox, oy = off or (0, 0)
        a = [int(a[0]) + ox, int(a[1]) + oy]
    if cmd == "shot":
        if off:
            dpy.shot(a[0], off[0], off[1], GAME_W, GAME_H)
        else:
            dpy.shot(a[0])
    elif cmd == "click":
        dpy.click(a[0], a[1])
    elif cmd == "rclick":
        dpy.click(a[0], a[1], button=3)
    elif cmd == "move":
        dpy.move(a[0], a[1])
    elif cmd == "dclick":
        dpy.click(a[0], a[1])
        time.sleep(0.1)
        dpy.click(a[0], a[1])
    elif cmd == "key":
        dpy.key(a[0])
    elif cmd == "type":
        dpy.type(a[0])
    elif cmd == "sleep":
        time.sleep(float(a[0]))
    else:
        sys.exit(f"unknown command {cmd!r}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--display", default=":7")
    ap.add_argument("--window", help="window title; click/move coordinates become relative to it")
    ap.add_argument("cmd", nargs="+")
    ns = ap.parse_args()
    dpy = Display(ns.display)
    off = dpy.origin(ns.window) if ns.window else None
    if ns.cmd[0] == "run":
        for line in open(ns.cmd[1]):
            line = line.split("#", 1)[0].strip()
            if line:
                do(dpy, line.split(None, 2) if not line.startswith("type ") else ["type", line[5:]], off)
    else:
        do(dpy, ns.cmd, off)


if __name__ == "__main__":
    main()
