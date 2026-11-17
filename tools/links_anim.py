"""Animate an act's link builder (docs/specs/drlg/warps.md B and C): each table entry placing its level's rectangle
against its anchor, the side it draws, and the check that accepts or rejects it. With --warps, a short second output:
two levels' warp points and how their warp slots pair (warps E and F). Schematic only (ADR-0036): boxes, text and
lines in our own palette; level rectangles are boxes labelled with the level number.

Usage:
  python3 -I tools/links_anim.py <root> <seed> [--act N] [--diff D] [--theme dark|light] [--out DIR] [--schematic]
  python3 -I tools/links_anim.py <root> [<seed>] --warps [--theme dark|light] [--out DIR] [--schematic]

<root> is the data tree every illustration tool takes first (workspace/merged); the tool reads the Levels table there
and the link tables of the game image beside it (the model's own loader), never a map, tile or picture. <seed> is the
map seed, decimal or 0x hex (an illustrative input, never a seed a game derives). --act: the act, 0 to 4 (0 = Act I,
default 0); acts I, II, IV and V have a link builder (act III's jungle layout is part of the outdoor generator).
--diff: 0 normal, 1 nightmare, 2 hell (default 0; the level sizes depend on it). --warps: the second output (the two
levels it shows are fixed: Cold Plains and Cave Level 1; it takes no seed, and one given changes nothing). --theme: dark or
light (default dark). --schematic is accepted for the export builder and changes nothing. DIR defaults to
workspace/render/anim/links-<seed hex>-schematic/ (or links-warps-schematic/) and must stay under workspace/. Outputs:
  frame-NNN.png one frame per step; links.gif the animated GIF; index.html the step-through page; steps.json the
  captions and calculations; schematic.json the marker's file list.

Link builder: one frame per placement attempt of every table of the act with two or more levels (the pick, the draws
on the copy of the act seed, the side, the rectangle, the check's answer and its reason), a frame when a table is
done, and Act I's second table ends with the level 27 index step. Every value is read from the DRLG model's act link
builder (tools/drlg.py: Act, act_links, link_build and the pick and check functions), traced by wrapping the picks and
checks, so the frames are the model's own calls. A level the table fixes far from the others (Moo Moo Farm) is
named and left out of the picture. Stdlib only.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import anim_common  # noqa: E402
import drlg  # noqa: E402
import schematic_kit as K  # noqa: E402

W, H = 960, 520
CAP_Y = 436
ACTN = ["ACT I", "ACT II", "ACT III", "ACT IV", "ACT V"]
ACTR = ["I", "II", "III", "IV", "V"]
DIFFN = ["normal", "nightmare", "hell"]
NAMES = {1: "ROGUE ENCAMPMENT", 2: "BLOOD MOOR", 3: "COLD PLAINS", 4: "STONY FIELD", 5: "DARK WOOD", 6: "BLACK MARSH",
         7: "TAMOE HIGHLAND", 9: "CAVE LEVEL 1", 17: "BURIAL GROUNDS", 26: "MONASTERY GATE", 39: "MOO MOO FARM",
         40: "LUT GHOLEIN", 41: "ROCKY WASTE", 42: "DRY HILLS", 43: "FAR OASIS", 44: "LOST CITY", 45: "VALLEY OF SNAKES",
         46: "CANYON OF THE MAGI", 103: "PANDEMONIUM FORTRESS", 104: "OUTER STEPPES", 105: "PLAINS OF DESPAIR",
         106: "CITY OF THE DAMNED", 108: "CHAOS SANCTUM", 109: "HARROGATH", 110: "BLOODY FOOTHILLS",
         111: "RIGID HIGHLANDS", 112: "ARREAT PLATEAU", 117: "TUNDRA WASTELANDS", 134: "PANDEMONIUM RUN 2",
         136: "TRISTRAM"}
# the pick kinds: (words for the frame, the spec's rule for the step page)
PICKS = {
    0x6760F0: ("AT ITS TABLE POSITION", "anchor pick: no draw, the position is the Levels OffsetX, OffsetY"),
    0x676150: ("4 SIDES, ONE DRAW", "cycle 4: first call d = Step(copy) & 3, then d = (d + 1) mod 4 until back at the first"),
    0x676280: ("8 SIDES, ONE DRAW", "cycle 8: first call d = Step(copy) & 7, then d = (d + 1) mod 8 until back at the first"),
    0x676450: ("SIDE AND FLIP, 2 DRAWS", "first call d = Step & 3 then f = Step & 1; next (d, f) = ((d + f) mod 4, (f + 1) mod 2)"),
    0x676650: ("SIDE AND FLIP, 2 DRAWS", "as the Rogue Encampment's pick; the size is 96 * 56 for odd d, 56 * 96 for even d"),
    0x6768C0: ("ONE FIXED SIDE", "fixed pick: d = 0, no draw"),
    0x6769A0: ("2 SIDES, ONE DRAW", "first call d = (Step & 1) + 1, then the other of 1 and 2"),
    0x676AE0: ("8 SIDES, ONE DRAW", "cycle 8: first call d = Step(copy) & 7, then d = (d + 1) mod 8 until back at the first"),
    0x676C00: ("A DRAW EACH CALL", "d = 3; a draw on every call decides the position"),
    0x67D830: ("A DRAW EACH CALL", "b = Step & 1 on every call decides the size"),
    0x67D8E0: ("A DRAW EACH CALL", "b = Step & 1 on every call decides the size"),
    0x67D980: ("2 SIZES, ONE DRAW", "first call b = Step & 1, then the other value"),
}


SHAPE = (0x67D830, 0x67D8E0, 0x67D980)       # picks whose stored choice is a shape (size), not a side
REDRAW = (0x676C00, 0x67D830, 0x67D8E0)      # the picks that draw again on every call (warps B1)
AGAIN = {False: "The same entry tries its next choice with no new draw.",
         True: "The same entry picks again and draws again."}


def nm(lid):
    return NAMES.get(lid, "LEVEL %d" % lid)


def nice(lid):
    """A level's name in running text: each word capitalised, 'of' and 'the' not."""
    return " ".join(w.lower() if w in ("OF", "THE") else w.capitalize() for w in nm(lid).split())


def fx(v):
    return "%08X" % v


def fs(lo, hi):
    return "{%08x:%08x}" % (lo, hi)


# ---------------------------------------------------------------- the model's own calls, traced
def trace(root, act, seed, diff):
    """Run drlg.act_links on Act(act, seed, diff) with the picks and checks wrapped. -> (Act, [table dict])."""
    exe = os.path.join(os.path.dirname(os.path.abspath(root)), "install", "app", "game.exe")
    drlg.load_outdoor(root, exe)
    A = drlg.Act(act, seed, diff)
    events = []                      # one dict per pick call, in call order
    state = {"depth": 0}
    saved_pick, saved_chk = dict(drlg.PICK), {n: getattr(drlg, n) for n in ("_chk1a", "_chk1b", "_chk_plain")}

    def wrap_pick(va, fn):
        def f(B):
            if B.seed.log is None:
                B.seed.log = []
            n0 = len(B.seed.log)
            r = fn(B)
            i = B.i
            events.append(dict(B=B, va=B.t[i][0], i=i, pick=bool(r), draws=list(B.seed.log[n0:]),
                               dir=B.dir[i], flip=B.flip[i], dir0=B.dir0[i], rect=list(B.rect[i]),
                               rects=[list(x) for x in B.rect], chk=None, chkname=None, ok=bool(r)))
            return r
        return f

    def wrap_chk(name):
        orig = getattr(drlg, name)

        def f(B):
            if state["depth"]:
                return orig(B)
            state["depth"] = 1
            try:
                r = orig(B)
            finally:
                state["depth"] = 0
            e = events[-1]
            assert e["B"] is B and e["i"] == B.i
            e["chk"], e["chkname"], e["ok"] = bool(r), name, bool(r)
            return r
        return f
    try:
        for va, fn in saved_pick.items():
            drlg.PICK[va] = wrap_pick(va, fn)
        for n, fn in saved_chk.items():
            setattr(drlg, n, wrap_chk(n))
        drlg.act_links(A)
    finally:
        drlg.PICK.clear()
        drlg.PICK.update(saved_pick)
        for n, fn in saved_chk.items():
            setattr(drlg, n, fn)
    tables = []
    for va, B, seed_in, seed_out in A.builds:
        ev = [e for e in events if e["B"] is B]
        tables.append(dict(va=va, B=B, t=B.t, seed_in=seed_in, seed_out=seed_out, events=ev))
    return A, tables


def reject_reason(e):
    """The check's reason for a reject, as the spec's B3 lists them: -> (words for the frame, text for the step page,
    index of the rectangle in the way or -1). Uses the model's own gap test."""
    B, i = e["B"], e["i"]
    lv, a = B.t[i][1], B.t[i][2]
    cur = e["rect"]
    for j in range(i):
        if j != a and drlg.gap_overlap(cur, e["rects"][j]):
            return "OVERLAPS %d" % B.t[j][1], "it overlaps level %d (%s)" % (B.t[j][1], nice(B.t[j][1])), j
    if e["chkname"] == "_chk1a" and lv == 1:
        return "SIDE NOT ALLOWED", "its side is not in the table of allowed sides", -1
    if e["chkname"] == "_chk1a" and lv == 17:
        return "SIDE ALREADY HELD", "another level placed against the Cold Plains holds that side", -1
    if e["chkname"] == "_chk1b":
        return "OVERLAPS MOO MOO", "it overlaps Moo Moo Farm's rectangle widened 200 tiles toward lower y", 0
    return "CHECK REJECTS", "the check rejects", -1


# ---------------------------------------------------------------- drawing
class MapView:
    """A fixed window onto a table's rectangles: integer scale k/1000 from the bounds of every rectangle the table
    tries (the entries shown)."""

    def __init__(self, tbl, shown, x0, y0, w, h):
        xs, ys = [], []
        for e in tbl["events"]:
            if e["pick"] and e["i"] in shown:
                r = e["rect"]
                xs += [r[0], r[0] + r[2]]
                ys += [r[1], r[1] + r[3]]
        for i in shown:
            r = tbl["B"].rect[i]
            xs += [r[0], r[0] + r[2]]
            ys += [r[1], r[1] + r[3]]
        self.minx, self.miny = min(xs), min(ys)
        sx, sy = max(xs) - self.minx, max(ys) - self.miny
        pad = 16
        self.k = min((w - 2 * pad) * 1000 // max(sx, 1), (h - 2 * pad) * 1000 // max(sy, 1))
        self.x0 = x0 + (w - sx * self.k // 1000) // 2
        self.y0 = y0 + (h - sy * self.k // 1000) // 2
        self.panel = (x0, y0, w, h)

    def rect(self, r):
        x = self.x0 + (r[0] - self.minx) * self.k // 1000
        y = self.y0 + (r[1] - self.miny) * self.k // 1000
        w = max(3, (r[0] + r[2] - self.minx) * self.k // 1000 + self.x0 - x)
        h = max(3, (r[1] + r[3] - self.miny) * self.k // 1000 + self.y0 - y)
        return x, y, w, h


def draw_rect(k, view, r, lid, fill, edge, t=1):
    x, y, w, h = view.rect(r)
    k.rect(x, y, w, h, fill)
    k.outline(x, y, w, h, edge, t)
    s = str(lid)
    sc = 2 if w >= K.text_w(s, 2) + 6 and h >= 18 else 1
    if w >= K.text_w(s, sc) + 2 and h >= 7 * sc + 2:
        k.text(x + (w - K.text_w(s, sc)) // 2, y + (h - 7 * sc) // 2, s, "txt", sc)


def entry_state(tbl, ev_index):
    """The entries placed (kept) after the first `ev_index` events: -> {entry: rect}; an accepted pick keeps its rect,
    a backed-up entry loses it."""
    kept = {}
    for e in tbl["events"][:ev_index]:
        i = e["i"]
        for j in [x for x in kept if x >= i]:
            del kept[j]
        if e["pick"] and e["ok"]:
            kept[i] = e["rect"]
    return kept


def build_links(root, act, seed, diff, theme):
    A, tables = trace(root, act, seed, diff)
    frames, caps = [], []
    k = K.Kit(W, H, theme)
    shown_tables = []
    for tbl in tables:
        t = tbl["t"]
        # an entry no later entry anchors to and that anchors to nothing is fixed far from the others: left out
        anch = {a for (_p, _l, a, _b) in t if a != -1}
        shown = [i for i in range(len(t)) if not (t[i][0] == 0x6760F0 and i not in anch and t[i][2] == -1)]
        if len(shown) >= 2:
            shown_tables.append((tbl, shown))
    nT = len(shown_tables)
    MX, MY, MW, MH = 20, 52, 580, 372
    IX, IW = 616, 324
    for ti, (tbl, shown) in enumerate(shown_tables):
        t, B, evs = tbl["t"], tbl["B"], tbl["events"]
        view = MapView(tbl, shown, MX, MY, MW, MH)
        hidden = [t[i][1] for i in range(len(t)) if i not in shown]
        tname = "TABLE %d OF %d" % (ti + 1, nT)

        def header():
            k.text(20, 12, "%s LINK BUILDER: %s" % (ACTN[act], tname), "acc", 2, True)
            k.rect(MX, MY, MW, MH, "bg")
            k.outline(MX, MY, MW, MH, "grey", 1)

        def entries_list(kept, cur_i):
            y = 262
            k.text(IX, y - 14, "ENTRIES (LEVEL, ANCHOR)", "dim", 1)
            for i in range(len(t)):
                a = t[i][2]
                lab = "%d %s" % (t[i][1], nm(t[i][1]))
                lab += " (ANCHOR %d)" % t[a][1] if a != -1 else ""
                col = "txt" if i in kept or i == cur_i else "dim"
                if i == cur_i:
                    k.rect(IX - 4, y - 2, IW + 4, 12, "cur")
                k.text(IX, y, lab[:50], "txt" if i == cur_i else col, 1)
                y += 13
            if hidden:
                k.text(IX, y + 4, "NOT SHOWN: %s, FIXED FAR AWAY" % ", ".join(nm(x) for x in hidden), "dim", 1)

        # ---- one frame per pick call
        for n, e in enumerate(evs):
            i = e["i"]
            lv, a = t[i][1], t[i][2]
            kept = entry_state(tbl, n)
            header()
            for j, r in kept.items():
                if j in shown:
                    draw_rect(k, view, r, t[j][1], "roomdone", "edge")
            if not e["pick"]:
                info = [("ENTRY %d: %d" % (i + 1, lv), "txt"), (nm(lv)[:26], "txt"), ("NO CHOICES LEFT", "bad"),
                        ("BACK UP ONE ENTRY", "bad")]
                cap = ("%s: every side has been tried, so the builder backs up to the entry before it and that entry "
                       "tries its next side." % nice(lv))
                text = "%s has no side left to try: the builder backs up one entry." % nice(lv)
                calc = ["Entry %d (level %d): the pick returns 0 (its next choice equals the first one)." % (i + 1, lv),
                        "dir, dir0, flip and flip0 of the entry are reset to -1; the loop goes to entry %d." % i]
            else:
                x, y, w, h = view.rect(e["rect"]) if i in shown else (0, 0, 0, 0)
                ok = e["ok"]
                col = "good" if ok else "bad"
                if i in shown:
                    if not ok:
                        why = reject_reason(e)
                        if why[2] >= 0 and why[2] in shown:
                            xx, yy, ww, hh = view.rect(e["rects"][why[2]])
                            k.outline(xx - 1, yy - 1, ww + 2, hh + 2, "bad", 2)
                    draw_rect(k, view, e["rect"], lv, "cur" if ok else "panel", col, 3)
                kind = PICKS[e["va"]][0]
                dstr = ", ".join(fx(d) for d in e["draws"]) if e["draws"] else "NO DRAW"
                sw = "shape" if e["va"] in SHAPE else "side"
                side = "%s %d" % (sw.upper(), e["dir"]) if e["dir"] != -1 else "NO SIDE"
                if e["flip"] != -1:
                    side += " FLIP %d" % e["flip"]
                r = e["rect"]
                info = [("ENTRY %d: %d" % (i + 1, lv), "txt"), (nm(lv)[:26], "txt"), (kind, "dim"),
                        ("DRAW " + dstr if e["draws"] else "NO NEW DRAW", "dim"), (side, "txt"),
                        ("AT %d, %d  %d * %d" % tuple(r), "txt")]
                if e["chk"] is None:
                    info.append(("NO CHECK: KEPT", "good"))
                elif ok:
                    info.append(("CHECK: ACCEPT", "good"))
                else:
                    info.append(("REJECT: " + reject_reason(e)[0], "bad"))
                info = [(s[:26], c_) for s, c_ in info]
                anchor = "anchored to %s" % nice(t[a][1]) if a != -1 else "a table position, not an anchor"
                if ok:
                    if e["va"] in (0x6760F0, 0x6768C0):
                        how = "is placed at its table position" if e["va"] == 0x6760F0 else "is placed on its one fixed side"
                    elif e["draws"]:
                        how = "takes %s %d (it drew %s on the copy of the act seed)" % (
                            sw, e["dir"], ", ".join(fx(d) for d in e["draws"]))
                    else:
                        how = "takes its next %s, %d, with no new draw" % (sw, e["dir"])
                    cap = "%s %s; the rectangle is %d * %d at (%d, %d)%s." % (
                        nice(lv), how, r[2], r[3], r[0], r[1],
                        "" if e["chk"] is None else ", and the check accepts it")
                else:
                    cap = ("%s on %s %d%s is rejected: %s. %s" % (
                        nice(lv), sw, e["dir"], "" if e["flip"] == -1 else ", flip %d," % e["flip"],
                        reject_reason(e)[1], AGAIN[e["va"] in REDRAW]))
                text = ("%s: %s, %s." % (nice(lv), kind.lower() if e["dir"] == -1 or e["va"] in (0x6768C0,) else
                                         "%s, %s %s" % (kind.lower(), sw, e["dir"]),
                                         "accepted" if ok else "rejected, " + reject_reason(e)[1]))
                calc = ["Entry %d: level %d, %s; pick: %s." % (i + 1, lv, anchor, PICKS[e["va"]][1])]
                if e["draws"]:
                    calc.append("Draws on the copy of the act seed (low words): %s." % ", ".join(str(d) for d in e["draws"]))
                elif e["va"] in (0x6760F0, 0x6768C0):
                    calc.append("No draw: this pick never draws.")
                else:
                    calc.append("No draw on this call: the next choice follows from the current one, and the stored "
                                "first choice only ends the cycle.")
                calc.append("%s; rectangle (x, y, w, h) = (%d, %d, %d, %d)." % (
                    "No side (the position is the table's)" if e["dir"] == -1 else "%s %d%s" % (
                        sw.capitalize(), e["dir"], "" if e["flip"] == -1 else ", flip %d" % e["flip"]),
                    r[0], r[1], r[2], r[3]))
                if e["chk"] is None:
                    calc.append("This table has no check: the entry is kept.")
                elif ok:
                    calc.append("Check: accepts.")
                else:
                    calc.append("Check: rejects, %s; %s" % (
                        reject_reason(e)[1], "the next call draws again." if e["va"] in REDRAW else "the next call tries the next %s." % sw))
            k.box(IX, 52, IW, 188, info, "panel", "dim", sc=2, align="l")
            entries_list(entry_state(tbl, n + 1), i)
            k.legend(MX, 412 - 2, [("roomdone", "KEPT"), ("cur", "ACCEPTED NOW"), ("panel", "REJECTED NOW")], 1)
            k.caption(cap, CAP_Y, 76)
            frames.append(k.done())
            caps.append(dict(text=text, calc=calc))
        # ---- the table done
        header()
        kept = entry_state(tbl, len(evs))
        for j, r in kept.items():
            if j in shown:
                draw_rect(k, view, r, t[j][1], "roomdone", "edge")
        seam = A.idx != 4 and any(t[j][2] != -1 for j in range(len(t)))
        info = [("TABLE DONE", "good"), ("%d LEVELS PLACED" % len(t), "txt"),
                ("COPY OF SEED DROPPED", "dim"), ("RECTANGLES WRITTEN", "txt")]
        if seam:
            info.append(("SEAMS TO ANCHORS", "txt"))
        k.box(IX, 52, IW, 188, info, "panel", "dim", sc=2, align="l")
        entries_list(kept, -1)
        cap = ("The table is done: every level has its rectangle%s. The copy of the act seed is thrown away, so the next "
               "table starts from the same act seed." % (", and each level placed against an anchor is linked both ways "
                                                         "to it as a walkable seam" if seam else ""))
        for i in range(len(t)):
            assert list(A.rect[t[i][1]]) == list(B.rect[i])
        k.caption(cap, CAP_Y, 76)
        frames.append(k.done())
        caps.append(dict(
            text="The table is done: each level has its rectangle%s." % (
                ", and each level with an anchor a seam both ways to it" if seam else ""),
            calc=["Rectangles: %s." % "; ".join("%d: (%d, %d, %d, %d)" % ((t[i][1],) + tuple(B.rect[i])) for i in range(len(t))),
                  "The copy of the act seed ends at %s and is discarded; the layout did not step the act seed, still %s." % (
                      fs(B.seed.lo, B.seed.hi), fs(tbl["seed_in"].lo, tbl["seed_in"].hi))]))
        # ---- level 27's index: the builder's one draw on the act seed (Black Marsh, level 6)
        lv6 = [i for i in range(len(t)) if t[i][1] == 6]
        if lv6:
            i = lv6[0]
            d = B.dir[i]
            header()
            for j, r in kept.items():
                if j in shown:
                    draw_rect(k, view, r, t[j][1], "roomdone", "edge", 1)
            xx, yy, ww, hh = view.rect(kept[i])
            k.outline(xx - 1, yy - 1, ww + 2, hh + 2, "acc", 2)
            s_in = tbl["seed_in"].copy()
            if d in (1, 3):
                r_ = s_in.step()
                assert A.idx27 == ((2 - (r_ & 1)) if d == 1 else ((~r_) & 1)), (A.idx27, r_)
                info = [("BLACK MARSH: SIDE %d" % d, "txt"), ("ONE DRAW ON THE ACT SEED", "txt"), ("DRAW %s" % fx(r_), "dim"),
                        ("LEVEL 27 INDEX %d" % A.idx27, "good")]
                cap = ("The Black Marsh ended on side %d, so the builder draws once on the act seed itself: %s, and level "
                       "27 gets file index %d." % (d, fx(r_), A.idx27))
                calc = ["Level 6 is on side %d: one step of the act seed (the builder's only draw on it)." % d,
                        "Draw (low word) = %d, so level 27's index = %s = %d." % (
                            r_, "2 - (r & 1)" if d == 1 else "(not r) & 1", A.idx27),
                        "The act seed after: %s." % fs(tbl["seed_out"].lo, tbl["seed_out"].hi)]
                text = "Level 27's file index %d, from the one draw the builder makes on the act seed." % A.idx27
            else:
                info = [("BLACK MARSH: SIDE %d" % d, "txt"), ("NO DRAW, NO WRITE", "txt"), ("LEVEL 27 KEEPS ITS", "dim"),
                        ("CREATE-TIME INDEX", "dim")]
                cap = ("The Black Marsh ended on side %d: nothing is drawn or written, and level 27 keeps the index its own "
                       "creation draws." % d)
                calc = ["Level 6 is on side %d: neither side 1 nor side 3, so the act seed is not stepped." % d]
                text = "Level 27 keeps its own index: the Black Marsh did not end on side 1 or 3."
            k.box(IX, 52, IW, 188, info, "panel", "dim", sc=2, align="l")
            k.caption(cap, CAP_Y, 76)
            frames.append(k.done())
            caps.append(dict(text=text, calc=calc))
    return frames, caps, (A, shown_tables)


# ---------------------------------------------------------------- the warps output (warps E and F)
# The rooms are those of the spec's worked example (level 9 of map seed 2027, and Cold Plains' cave mouth): inputs,
# not a run. The points and the pairing are computed (the pairing by drlg.warp_pair_slot, the model's F1).
ROOMS9 = [(35, "CAVE PREV W", (1572, 1300, 8, 8), 0), (38, "CAVE DOWN N", (1524, 1364, 8, 8), 4)]
MOUTH = (1072, 952)      # the cave mouth of Cold Plains: an outdoor room carrying slot 6


def warp_point(rect):
    """warps E1: the room centre in subtiles: ((x + w / 2) * 5, (y + h / 2) * 5), w / 2 truncated."""
    x, y, w, h = rect
    return (x + w // 2) * 5, (y + h // 2) * 5


def build_warps(root, theme):
    exe = os.path.join(os.path.dirname(os.path.abspath(root)), "install", "app", "game.exe")
    drlg.load_outdoor(root, exe)
    A = drlg.Act(0, 2027, 0)          # level 3's link list does not depend on the seed (its anchors are fixed)
    drlg.act_links(A)
    v3, w3 = list(A.vis(3)), list(A.warp(3))
    v9, w9 = list(drlg.LV[9]["vis"]), list(drlg.LV[9]["warp"])
    bit3 = {6}                        # the cave mouth carries slot 6 (the worked example)
    bit9 = {m for _n, _s, _r, m in ROOMS9}
    pts = [(n, s, r, m, warp_point(r)) for n, s, r, m in ROOMS9]
    k = K.Kit(W, H, theme)
    frames, caps = [], []

    def hdr(s):
        k.text(20, 12, s, "acc", 2, True)

    def slots(x, y, name, vis, warp, mark=None, got=None, rooms=()):
        k.text(x, y, name, "dim", 2)
        for m in range(8):
            fill = "cur" if m == mark else "panel"
            edge = "acc" if m == got else ("good" if m == mark else ("blue" if m in rooms else "dim"))
            lab = ("%d: LEVEL %d, WARP %d" % (m, vis[m], warp[m])) if vis[m] else ("%d: EMPTY" % m)
            k.box(x, y + 22 + m * 24, 262, 22, [(lab, "txt" if vis[m] else "dim")], fill, edge,
                  sc=2, t=2 if m in rooms else 1, align="l")

    # ---- frame 0: the warp points of level 9
    hdr("WARP POINTS OF CAVE LEVEL 1 (LEVEL 9)")
    k.text(20, 40, "A ROOM WITH A WARP BIT WHOSE SLOT HAS A WARP ID MAKES A POINT", "dim", 2)
    y = 76
    for n, s, r, m, p in pts:
        k.box(20, y, 300, 70, [("ROOM %d: %s" % (n, s), "txt"), ("%d, %d  %d * %d" % r, "dim"), ("WARP BIT OF SLOT %d" % m, "txt")],
              "panel", "dim", sc=2, align="l")
        k.text(340, y + 6, "VIS %d, WARP %d" % (v9[m], w9[m]), "txt", 2)
        k.text(340, y + 30, "POINT = ((X + W / 2) * 5, (Y + H / 2) * 5)", "dim", 1)
        k.text(340, y + 44, "(%d + %d) * 5 = %d" % (r[0], r[2] // 2, p[0]), "good", 2)
        k.text(660, y + 44, "(%d + %d) * 5 = %d" % (r[1], r[3] // 2, p[1]), "good", 2)
        y += 88
    k.text(20, 262, "A SEAM (WARP -1) NEVER MAKES A POINT", "dim", 2)
    k.text(20, 290, "A WAYPOINT ROOM MAKES ONE TOO (NONE IN THIS LEVEL)", "dim", 2)
    k.text(20, 326, "LIST: %d POINTS, IN SUBTILES" % len(pts), "txt", 2)
    k.text(20, 362, "THE ROOMS ARE AN EXAMPLE'S INPUTS; THE POINTS ARE COMPUTED", "dim", 1)
    k.caption("Rooms of Cave Level 1 that carry a warp bit for a slot with a warp id each add one point at their centre, in "
              "subtiles: (%d, %d) and (%d, %d). A waypoint room adds one too." % (pts[0][4] + pts[1][4]), CAP_Y, 76)
    frames.append(k.done())
    caps.append(dict(
        text="Cave Level 1's two warp rooms each give a warp point at the room's centre, in subtiles.",
        calc=["Room list rects (x, y, w, h): %s." % "; ".join("%d: (%d, %d, %d, %d)" % ((n,) + r) for n, _s, r, _m in ROOMS9),
              "Level 9: Vis0 = %d, Warp0 = %d; Vis4 = %d, Warp4 = %d." % (v9[0], w9[0], v9[4], w9[4]),
              "Points: %s." % "; ".join("(%d + %d) * 5, (%d + %d) * 5 = (%d, %d)" % (
                  r[0], r[2] // 2, r[1], r[3] // 2, p[0], p[1]) for n, s, r, m, p in pts)]))
    # ---- frames 1, 2: the two pairings
    cases = [("COLD PLAINS SLOT 6", 3, v3, w3, 9, v9, bit3, bit9, 6, "the cave mouth of Cold Plains"),
             ("CAVE LEVEL 1 SLOT 0", 9, v9, w9, 3, v3, bit9, bit3, 0, "Cave Level 1's stairs room")]
    got_all = []
    for title, src, vs, ws, dst, vd, _bs, bd, m, _what in cases:
        kk, want, tried, got = drlg.warp_pair_slot(vs, vd, src, m, lambda j, bd=bd: j in bd, rank=ws[m] != -1)
        got_all.append((src, m, kk, want, tried, got))
        hdr("WARP PAIRING: %s" % title)
        slots(20, 40, "%s LINKS" % nm(src), vs, ws, mark=m, rooms=_bs)
        slots(300, 40, "%s LINKS" % nm(dst), vd, wd(dst, ws, w3, w9), got=got, rooms=bd)
        back = [j for j in range(8) if vd[j] == src]
        x = 584
        k.text(x, 40, "K = EARLIER SLOTS TO THE SAME LEVEL", "dim", 1)
        k.text(x, 54, "K = %d" % kk, "txt", 2)
        k.text(x, 84, "SLOTS NAMING %d: %s" % (src, ", ".join(str(j) for j in back) or "NONE"), "txt", 2)
        k.text(x, 114, "RANK %d SLOT: %s" % (kk, want if want is not None else "NONE"), "txt", 2)
        if want is not None and want == got:
            k.text(x, 144, "SLOT %d HAS A ROOM: PAIRED" % want, "good", 2)
        else:
            if want is not None:
                k.text(x, 144, "SLOT %d HAS NO ROOM" % want, "bad", 2)
            else:
                k.text(x, 144, "NO SLOT AT THAT RANK", "bad", 2)
            k.text(x, 174, "FALLBACK WALK: %s" % ", ".join(str(j) for j in tried), "txt", 2)
            k.text(x, 204, "FIRST WITH A ROOM: SLOT %s" % got, "good", 2)
        k.text(x, 244, "NO DRAW IS MADE", "dim", 2)
        k.text(x, 284, "BLUE EDGE: A ROOM CARRIES THE", "dim", 1)
        k.text(x, 298, "SLOT'S BIT (AN EXAMPLE'S INPUT)", "dim", 1)
        if want is not None and want == got:
            cap = ("%s slot %d names level %d: %d earlier slot(s) name it, so the rank slot of level %d is slot %d, and that "
                   "slot has a room: paired, with no draw." % (nice(src), m, dst, kk, dst, want))
        elif want is None:
            cap = ("%s slot %d names level %d: %d earlier slots name it, but level %d has only %d slot%s naming back, so "
                   "the rank search fails and the fallback walk takes slot %d, the first with a room." % (
                       nice(src), m, dst, kk, dst, len(back), "" if len(back) == 1 else "s", got))
        else:
            cap = ("%s slot %d names level %d: the rank slot %d has no room, so the fallback walk goes through slots %s "
                   "and pairs with slot %d." % (nice(src), m, dst, want, ", ".join(str(j) for j in tried), got))
        k.caption(cap, CAP_Y, 76)
        frames.append(k.done())
        caps.append(dict(
            text="Slot %d of %s pairs with slot %d of %s%s." % (m, nice(src), got, nice(dst),
                                                                 "" if want == got else " by the fallback walk"),
            calc=["Source level %d slot %d names level %d; k = earlier slots naming level %d = %d." % (src, m, dst, dst, kk),
                  "Slots of level %d naming level %d: %s; the rank slot is %s." % (
                      dst, src, back, want if want is not None else "missing"),
                  "Fallback walk, in slot order: %s; paired slot %s." % (tried if tried else "not needed", got),
                  "No draw is made."]))
    return frames, caps, dict(v3=v3, w3=w3, v9=v9, w9=w9, pts=pts, pairs=got_all)


def wd(dst, ws, w3, w9):
    return w3 if dst == 3 else w9


HELP_LINKS = """<li>The big box is the act's map plane: each level is a rectangle labelled with its level number, placed against its anchor level.</li>
<li>Each step is one call of the entry's pick: it draws on a copy of the act seed (or takes its next stored side) and places the rectangle.</li>
<li>Then the act's check accepts the rectangle or rejects it; after a reject the same entry tries its next side.</li>
<li>Every value is computed by our model of the link builder for the illustrative seed given, not observed in the game.</li>"""
HELP_WARPS = """<li>The first step: a room that carries a warp bit for a slot with a warp id adds one warp point at its centre.</li>
<li>The next steps: a warp slot pairs with a slot of the level it names, by rank among the slots naming that level, or by a fallback walk.</li>
<li>The rooms are an example's inputs; the points and the pairing are computed.</li>"""


def main(argv):
    argv = list(argv)
    if "--schematic" in argv:
        argv.remove("--schematic")
    warps = "--warps" in argv
    if warps:
        argv.remove("--warps")
    targs = list(argv[1:])
    if "--out" in targs:
        del targs[targs.index("--out"):targs.index("--out") + 2]
    if warps:
        targs.append("--warps")
    opts = {"--act": "0", "--diff": "0", "--theme": "dark", "--out": None}
    for o in opts:
        if o in argv:
            i = argv.index(o)
            if i + 1 >= len(argv):
                print(__doc__.strip(), file=sys.stderr)
                return 2
            opts[o] = argv[i + 1]
            del argv[i:i + 2]
    if warps and len(argv) == 1:
        argv.append("1")                         # the warps output takes no seed
    if len(argv) != 2:
        print(__doc__.strip(), file=sys.stderr)
        return 2
    try:
        n, act, diff = int(argv[1], 0), int(opts["--act"]), int(opts["--diff"])
    except ValueError:
        print(__doc__.strip(), file=sys.stderr)
        return 2
    if not (0 < n <= drlg.M32 and act in (0, 1, 3, 4) and 0 <= diff <= 2 and opts["--theme"] in K.THEMES):
        print(__doc__.strip(), file=sys.stderr)
        return 2
    root = argv[0]
    default = "links-warps-schematic" if warps else "links-%x-schematic" % n
    out = opts["--out"] or os.path.join(HERE, "..", "workspace", "render", "anim", default)
    out = anim_common.safe_out(out)
    os.makedirs(out, exist_ok=True)
    if warps:
        frames, caps, _t = build_warps(root, opts["--theme"])
        K.write_illustration(out, "links", frames, caps, W, H, K.palette(opts["--theme"])[1], "warp points animation",
                             HELP_WARPS, targs)
    else:
        frames, caps, _t = build_links(root, act, n, diff, opts["--theme"])
        K.write_illustration(out, "links", frames, caps, W, H, K.palette(opts["--theme"])[1], "link builder animation",
                             HELP_LINKS, targs)
    print("%d frames -> %s" % (len(frames), out))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
