"""The schematic kit of the animation tools (ADR-0036; plan 0070 Phase 11, row 0): drawing primitives and the output
writer shared by the schematic generators (tools/rng_anim.py, tools/seedtree_anim.py) and the rectangle helpers that
tools/maze_anim.py and tools/tc_anim.py use.

Primitives on one palette-indexed canvas (class Kit): filled and outlined rectangles, text in the 5x7 font of
tools/anim_common.py (any integer scale, optional bold), labelled boxes, a cell grid, a proportion bar, a number tape,
a legend, straight lines and arrows, and a caption strip. Colours are names of our own fixed palette, never the
game's: THEMES holds the dark values (anim_common.SCHEM_UI, the palette the maze and drop illustrations use) and the
light values, one RGB per name, in the same order, so a frame's pixels are the same indices in both.

write_illustration() writes the folder the export's builder expects (ADR-0036): frame-NNN.png (marked), <name>.gif,
index.html, steps.json and schematic.json. Illustration helpers only: nothing here models the game, and nothing opens a
game file. Stdlib only.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import anim_common  # noqa: E402
import png  # noqa: E402

DARK = dict(anim_common.SCHEM_UI)
# The light values: same names, same order. Text names are dark on a pale ground; the fills are pale, the lines dark.
LIGHT = dict(
    bg=(248, 248, 250), panel=(228, 230, 238), txt=(24, 24, 32), dim=(98, 98, 112), acc=(128, 84, 0),
    good=(14, 120, 46), bad=(184, 36, 36), blue=(40, 80, 200), cur=(208, 216, 246), grey=(196, 196, 206),
    q_low=(110, 110, 110), q_normal=(40, 40, 40), q_superior=(70, 70, 70), q_magic=(40, 60, 200),
    q_set=(10, 130, 20), q_rare=(150, 120, 0), q_unique=(140, 96, 40), black=(255, 255, 255),
    qd_low=(214, 214, 218), qd_normal=(238, 238, 240), qd_superior=(226, 226, 230), qd_magic=(214, 220, 250),
    qd_set=(208, 240, 210), qd_rare=(244, 238, 190), qd_unique=(238, 224, 200),
    room=(190, 200, 236), roomdone=(170, 184, 232), edge=(60, 70, 150), door=(20, 140, 70), warp=(0, 130, 170))
assert list(LIGHT) == list(DARK)
THEMES = {"dark": DARK, "light": LIGHT}


def palette(theme="dark"):
    """-> (name -> palette index, 768 palette bytes) of a theme."""
    t = THEMES[theme]
    idx = {k: i for i, k in enumerate(t)}
    pal = bytearray()
    for rgb in t.values():
        pal += bytes(rgb)
    return idx, bytes(pal) + bytes(768 - len(pal))


# ---------------------------------------------------------------- rectangle helpers on a bare canvas
# (the helpers maze_anim.py and tc_anim.py draw their boxes with: the same loops as before, moved here)
def fill_rect(cv, W, H, x, y, w, h, col):
    for yy in range(max(0, y), min(H, y + h)):
        a, b = max(0, x), min(W, x + w)
        if a < b:
            cv[yy * W + a:yy * W + b] = bytes([col]) * (b - a)


def outline_rect(cv, W, H, x, y, w, h, col, t=1):
    fill_rect(cv, W, H, x, y, w, t, col)
    fill_rect(cv, W, H, x, y + h - t, w, t, col)
    fill_rect(cv, W, H, x, y, t, h, col)
    fill_rect(cv, W, H, x + w - t, y, t, h, col)


def text_w(s, sc=2):
    """Width in pixels of s at scale sc (6 columns a character, the last one blank)."""
    return 6 * sc * len(s) - sc if s else 0


class Kit:
    """One W x H canvas of palette indices. Colour arguments are palette names (str) or raw indices (int)."""

    def __init__(self, W, H, theme="dark"):
        self.W, self.H, self.theme = W, H, theme
        self.C, self.pal = palette(theme)
        self.cv = None
        self.new()

    def c(self, col):
        return self.C[col] if isinstance(col, str) else col

    def new(self, bg="bg"):
        self.cv = bytearray([self.c(bg)]) * (self.W * self.H)
        return self.cv

    def done(self):
        """The finished frame (bytes) and a fresh canvas."""
        f = bytes(self.cv)
        self.new()
        return f

    # ---- shapes
    def rect(self, x, y, w, h, col):
        fill_rect(self.cv, self.W, self.H, x, y, w, h, self.c(col))

    def outline(self, x, y, w, h, col, t=1):
        outline_rect(self.cv, self.W, self.H, x, y, w, h, self.c(col), t)

    def hline(self, x0, x1, y, col, t=2):
        self.rect(min(x0, x1), y - t // 2, abs(x1 - x0) + 1, t, col)

    def vline(self, x, y0, y1, col, t=2):
        self.rect(x - t // 2, min(y0, y1), t, abs(y1 - y0) + 1, col)

    def arrow(self, x0, y0, x1, y1, col, t=2):
        """Axis-aligned arrow (right, left, down or up) with a triangular head whose tip is (x1, y1)."""
        if y0 == y1:
            d = 1 if x1 > x0 else -1
            self.hline(x0, x1 - d * 6, y0, col, t)
            for k in range(7):                      # the head: k columns back from the tip, half-height k
                self.rect(x1 - d * k, y1 - k, 1, 2 * k + 1, col)
        else:
            d = 1 if y1 > y0 else -1
            self.vline(x0, y0, y1 - d * 6, col, t)
            for k in range(7):
                self.rect(x1 - k, y1 - d * k, 2 * k + 1, 1, col)

    # ---- text
    def text(self, x, y, s, col="txt", sc=2, bold=False):
        anim_common.text(self.cv, self.W, self.H, x, y, s, self.c(col), sc)
        if bold:
            anim_common.text(self.cv, self.W, self.H, x + 1, y, s, self.c(col), sc)

    def text_c(self, cx, y, s, col="txt", sc=2, bold=False):
        """Text centred on x = cx."""
        self.text(cx - text_w(s, sc) // 2, y, s, col, sc, bold)

    # ---- widgets
    def box(self, x, y, w, h, lines=(), fill="panel", edge="dim", col="txt", sc=2, t=1, bold=False, align="c"):
        """A filled rectangle with an outline and one or more text lines, centred (align 'c') or at the left ('l').
        A line may be (text, colour) to colour it alone."""
        self.rect(x, y, w, h, fill)
        self.outline(x, y, w, h, edge, t)
        lines = list(lines)
        lh = 7 * sc + 4
        ty = y + (h - (lh * len(lines) - 4)) // 2
        for ln in lines:
            s, cc = (ln, col) if isinstance(ln, str) else ln
            if align == "c":
                self.text_c(x + w // 2, ty, s, cc, sc, bold)
            else:
                self.text(x + 6, ty, s, cc, sc, bold)
            ty += lh

    def cellgrid(self, x, y, cols, rows, cw, ch, cells=None, fill="panel", edge="grey", sc=1, col="txt"):
        """A cols x rows grid of cw x ch cells. cells: {(c, r): (label, fill name) | label}; a cell outside the dict is
        empty. Returns nothing; cell (c, r) is at x + c * cw, y + r * ch."""
        cells = cells or {}
        for r in range(rows):
            for c_ in range(cols):
                v = cells.get((c_, r))
                lab, fl = (v if isinstance(v, tuple) else (v, fill)) if v is not None else (None, fill)
                self.box(x + c_ * cw, y + r * ch, cw + 1, ch + 1, [lab] if lab else [], fl, edge, col, sc)

    def bar(self, x, y, w, h, num, den, fill="good", back="grey", edge="dim", label=None, sc=2, col="txt"):
        """A proportion bar: num/den of the width w in fill (integer arithmetic, so it is exact and reproducible)."""
        self.rect(x, y, w, h, back)
        if den > 0:
            self.rect(x, y, max(0, min(w, num * w // den)), h, fill)
        self.outline(x, y, w, h, edge)
        if label:
            self.text(x + 6, y + (h - 7 * sc) // 2, label, col, sc)

    def tape(self, x, y, vals, cw, ch, cur=None, sc=2, fill="panel", curfill="cur", edge="grey", col="txt", empty=None):
        """A number tape: len(vals) cells in a row, vals[i] the text of cell i (None: an empty cell, drawn with `empty`
        text if given); cell `cur` is highlighted."""
        for i, v in enumerate(vals):
            lab = v if v is not None else empty
            self.box(x + i * cw, y, cw + 1, ch + 1, [lab] if lab is not None else [], curfill if i == cur else fill,
                     "acc" if i == cur else edge, col if v is not None else "dim", sc)

    def legend(self, x, y, items, sc=1, gap=16):
        """items: [(colour name, label)]: a swatch and its label each, in a row. Returns the x after the last one."""
        for colr, lab in items:
            self.rect(x, y, 8 * sc + 2, 8 * sc + 2, colr)
            self.outline(x, y, 8 * sc + 2, 8 * sc + 2, "dim")
            self.text(x + 8 * sc + 8, y + sc, lab, "dim", sc)
            x += 8 * sc + 8 + text_w(lab, sc) + gap
        return x

    def caption(self, s, y, cols, col="txt", sc=2, x=14, panel_h=None):
        """A caption strip: a panel from y to the bottom, s wrapped to cols characters (the first lines that fit)."""
        self.rect(0, y, self.W, self.H - y, "panel")
        self.hline(0, self.W - 1, y, "grey", 1)
        for i, ln in enumerate(anim_common.wrap(s, cols)[:max(1, (self.H - y - 8) // (7 * sc + 5))]):
            self.text(x, y + 8 + i * (7 * sc + 5), ln, col, sc)


# ---------------------------------------------------------------- output
def write_illustration(out, name, frames, caps, W, H, pal, title, help_html, args, delays=None):
    """Write the schematic folder (ADR-0036) into `out` (a directory under workspace/, made by the caller through
    anim_common.safe_out): frame-NNN.png, <name>.gif, index.html, steps.json, schematic.json. `args`: the run's
    arguments for schematic.json (the data root and --out left out). Every file but schematic.json carries the marker."""
    n = len(frames)
    for i, f in enumerate(frames):
        png.write_indexed(os.path.join(out, "frame-%03d.png" % i), W, H, f, pal, transparent=(),
                          text={anim_common.MARKER_NAME: anim_common.MARKER})
    anim_common.write_html(os.path.join(out, "index.html"), caps, W, H, title, help_html, anim_common.MARKER)
    anim_common.write_steps_json(os.path.join(out, "steps.json"), caps, True)
    if delays is None:
        delays = [120] * n
        delays[-1] = 600
    with open(os.path.join(out, name + ".gif"), "wb") as fh:
        fh.write(anim_common.encode_gif(frames, W, H, pal, delays, anim_common.MARKER))
    anim_common.write_schematic_json(out, args, [name + ".gif", "index.html", "steps.json"] +
                                     ["frame-%03d.png" % i for i in range(n)])
