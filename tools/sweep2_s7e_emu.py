#!/usr/bin/env python3
"""Plan 0066 Phase 1, batch S7e (`lane/n66u`): emulated reproductions (ADR-0015, ADR-0021, ADR-0029) for the S7e rows,
run with re/ghidra_scripts/EmuBoundary.java and compared with the models below. No game run, no slot.

    python3 -I tools/sweep2_s7e_emu.py cases [--dir D] [--tag T]    write D/<family>.cases, .mem, .meta
    GHIDRA_PROJ_DIR=... GHIDRA_HEADLESS_MAXMEM=3G tools/ghidra.sh emuboundary D/<f>.cases D/<f>.mem > D/<f>.out
    python3 -I tools/sweep2_s7e_emu.py check [--dir D]              compare, account for traced accesses, score the controls
    python3 -I tools/sweep2_s7e_emu.py manifest [--dir D] [--write]  sha256 of every kept file (one path base: D)

Run from the worktree root (the field file's path is relative to it). Default D: workspace/logs/n66u/s7e/run. Every case
draw comes from random.Random("<tag>-<family>") (default tag `n66u`), so `cases` regenerates identical files.

Family ffn (quests/travel rows 19 and 60, the S3e fold of the architect ruling of 2026-11-15): COLL_FindFreeNear
(0x0064DEA0) at sizes 0..3 and an out-of-range size, steps 1 to 5, through its two wrappers and directly:
  act     0x0064E7E0 (room, pos, size, mask, step), ret 0x14: other none, maskA = maskB = mask, fallback 0, radius 50;
          PlayerChangeAct's form (0x0053ADB5: step 5, mask 0x1C89). No walk, so no field state is allocated.
  portal  0x0064E810 (room, pos, other, size, maskA, maskB, fallback), ret 0x1C: radius 50, step 1; called as
          PortalObjectCreate does (0x0056D213: other = pos, size 3, 0x3E01, 0xC01, fallback 0), and with other sizes.
  direct  0x0064DEA0 (room, pos, other, size, maskA, maskB, fallback, radius, step), ret 0x24: an origin other than the
          start, step 5 with the walk.
The world is item_emu3's declared room image (rooms, near lists, maps, cells; the field file `expfield.d2` loaded past
its header), and the walk's 8-byte field state comes from the shared pool through its real allocator on item_emu3's
declared pool page, with the two lock slots (0x006CC218 EnterCriticalSection, 0x006CC214 LeaveCriticalSection) at the
`ret 4` stand-in 0x0066A250: ADR-0029 (a), as run:2026-11-04-ground-emu's `drop` family. The checker compares the
return (a room address of the declared image, or 0) and the position buffer; no address the allocator chose.
The model is quests/travel § B1 with drlg/collision § E's footprints (CellTest, PlusTest, RectTest).

Controls (a wrong reading run on the same cases; `check` prints the cases each separates and how many it passes):
  step1 (rings of step 1)  nowalk (the walk ignored)  walkmaskA (the walk with maskA)  sizeone (every size a cell)
  fixedbase (lookups from the first room)  leq (a later equal distance wins)
Stdlib only.
"""
import argparse
import hashlib
import json
import os
import random
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import item_emu3 as E3  # noqa: E402
import item_inventory as inv  # noqa: E402
import frame_queue_emu as fq  # noqa: E402
from party_emu import parse_out  # noqa: E402
from use_emu import Case, le32  # noqa: E402

ROOT = os.path.dirname(HERE)
DEFAULT_DIR = os.path.join("workspace", "logs", "n66u", "s7e", "run")
M32 = 0xFFFFFFFF
FAMILIES = ("ffn",)
FQ_FAMILIES = ("qx", "mevd", "mevr")
F_FFN, F_ACT, F_PORTAL = 0x0064DEA0, 0x0064E7E0, 0x0064E810
POSB, OTHB = E3.POSB, E3.STATE
CONTROLS = dict(ffn=("step1", "nowalk", "walkmaskA", "sizeone", "fixedbase", "leq"))
COUNTS = dict(ffn=600)


# ------------------------------------------------------------------ the model: drlg/collision § E, quests/travel § B1
def cell_val(hint, x, y):
    r = inv.room_at(hint, x, y)
    if r is None or r.cells is None:
        return None
    return r.cells.get((x, y), 0)


def cell_test(hint, x, y, mask):
    v = cell_val(hint, x, y)
    return inv.BLOCKED if v is None else v & mask


def plus_test(hint, x, y, mask):
    r = inv.room_at(hint, x, y)
    if r is None or r.cells is None:
        return mask & 0xFFFF
    edge = (x == r.x) | (y == r.y) << 1 | (x == r.x + r.w - 1) << 2 | (y == r.y + r.h - 1) << 3
    if edge in (5, 7, 10, 11, 13, 14, 15):
        return mask & 0xFFFF
    res = 0
    for dx, dy, bit in ((0, 0, 0), (-1, 0, 1), (1, 0, 4), (0, -1, 2), (0, 1, 8)):
        if bit and edge & bit:
            res |= cell_test(r, x + dx, y + dy, mask)
        else:
            res |= r.cells.get((x + dx, y + dy), 0) & mask
    return res & 0xFFFF


def rect_split(q, r):
    left, top, right, bottom = q
    if top > bottom or left > right:
        return []
    p0 = [left, top, right, bottom]
    out = []
    if right >= r.x + r.w:
        p0[2] = r.x + r.w - 1
        out.append((r.x + r.w, top, right, bottom))
    if bottom >= r.y + r.h:
        p0[3] = r.y + r.h - 1
        out.append((p0[0], p0[3] + 1, p0[2], bottom))
    return [tuple(p0)] + out


def rect_test(hint, q, mask):
    r = inv.room_at(hint, q[0], q[1])
    if r is None or r.cells is None:
        return inv.BLOCKED
    pieces = rect_split(q, r)
    if not pieces:
        return inv.BLOCKED
    l, t, rt, b = pieces[0]
    res = 0
    for y in range(t, b + 1):
        for x in range(l, rt + 1):
            res |= r.cells.get((x, y), 0) & mask
    for p in pieces[1:]:
        res |= rect_test(r, p, mask)
    return res & 0xFFFF


def coll_test(hint, x, y, size, mask, ctl=None):
    """CollisionTest 0x0064D9B0 (drlg/collision E1)."""
    if ctl == "sizeone" and 0 <= size <= 3:
        size = 1
    if size in (0, 1):
        return cell_test(hint, x, y, mask)
    if size == 2:
        return plus_test(hint, x, y, mask)
    if size == 3:
        return rect_test(hint, (x - 1, y - 1, x + 1, y + 1), mask)
    return 0xFFFF


def find_free_near(room0, x0, y0, origin, field, size, ma, mb, fallback, radius, stp, ctl=None):
    """COLL_FindFreeNear 0x0064DEA0 (quests/travel B1). -> (room or None, x, y)."""
    if ctl == "step1":
        stp = 1
    if ctl == "nowalk":
        origin = None
    walkmask = ma if ctl == "walkmaskA" else mb
    base = [inv.room_at(room0, x0, y0)]

    def lookup(x, y):
        return inv.room_at(room0 if ctl == "fixedbase" else base[0], x, y)

    def blocked(r, x, y):
        if coll_test(r, x, y, size, ma, ctl):
            return True
        return origin is not None and inv.line_blocked(field, origin[0], origin[1], r, x, y, walkmask)

    b0 = base[0]
    if b0 is not None and not blocked(b0, x0, y0):
        return b0, x0, y0
    best, pos = -1, (x0, y0)

    def try_(x, y):
        nonlocal best, pos
        r = lookup(x, y)
        if r is None:
            return
        base[0] = r
        if blocked(r, x, y):
            return
        d = abs(x - x0) + abs(y - y0)
        if best == -1 or d < best or (ctl == "leq" and d == best):
            best, pos = d, (x, y)

    xl = xh = x0
    yl, yh, w = y0 - 1, y0 + 1, 2
    while (xh - x0 + 1) < radius:
        for y in range(yl, yh + 1, stp):
            for x in range(xl - 1, xh + 2, w):
                try_(x, y)
        for x in range(xl, xh + 1, stp):
            for y in range(yl, yh + 1, w):
                try_(x, y)
        if best != -1:
            break
        xl -= stp
        xh += stp
        yl -= stp
        yh += stp
        w += 2 * stp
    if best == -1 and not fallback:
        return None, x0, y0
    return lookup(pos[0], pos[1]), pos[0], pos[1]


# ------------------------------------------------------------------ the cases
def world(rnd, px, py, kind):
    w, h = rnd.randrange(8, 25), rnd.randrange(8, 25)
    ox, oy = rnd.randrange(0, w), rnd.randrange(0, h)
    r0 = E3.new_room(px - ox, py - oy, w, h)
    rooms = [r0]
    if kind in ("rooms", "walls") or rnd.random() < 0.4:
        for (dx, dy, nw, nh) in rnd.sample(((w, 0, 14, h), (-14, 0, 14, h), (0, h, w, 14), (0, -14, w, 14)), rnd.randrange(1, 5)):
            rooms.append(E3.new_room(r0["x"] + dx, r0["y"] + dy, nw, nh))
    bits = (0x1, 0x8, 0x80, 0x400, 0x800, 0x1000, 0x200, 0x2000)
    dens = dict(open=0.1, crowded=0.45, rooms=0.3, walls=0.12, edge=0.3)[kind]
    for r in rooms:
        E3.fill(rnd, r, dens, bits)
    if kind == "walls":
        for r in rooms:
            for _ in range(rnd.randrange(2, 9)):
                b = rnd.choice((0x1, 0x400, 0x800))
                x1, y1 = rnd.randrange(r["x"], r["x"] + r["w"]), rnd.randrange(r["y"], r["y"] + r["h"])
                for t in range(rnd.randrange(3, 16)):
                    x, y = (x1 + t, y1) if rnd.random() < 0.5 else (x1, y1 + t)
                    if r["x"] <= x < r["x"] + r["w"] and r["y"] <= y < r["y"] + r["h"]:
                        r["cells"][(x, y)] = r["cells"].get((x, y), 0) | b
    if rnd.random() < 0.08:
        rooms[rnd.randrange(len(rooms))]["nomap"] = rnd.choice((1, 2))
    n = len(rooms)
    for k, r in enumerate(rooms):
        others = [j for j in range(n) if j != k]
        rnd.shuffle(others)
        r["near"] = others if rnd.random() < 0.6 else others[:rnd.randrange(0, n)]
    # the start cell blocked, mostly, so that the search runs
    if rnd.random() < 0.85:
        r0["cells"][(px, py)] = r0["cells"].get((px, py), 0) | rnd.choice((0x1, 0x800, 0x400, 0x1000))
    return rooms


def gen_ffn(rnd, i):
    c = Case()
    px, py = rnd.randrange(3000, 9000), rnd.randrange(3000, 9000)
    form = ("act", "act", "portal", "direct")[i % 4]
    kind = ("open", "crowded", "rooms", "walls", "edge")[(i // 4) % 5]
    if form != "act" and rnd.random() < 0.6:
        kind = "walls"          # straight runs of the walk's bits: free footprints whose walk back is blocked
    rooms = world(rnd, px, py, kind)
    E3.put_world(c, rooms)
    for k, r in enumerate(rooms):          # the map's height (+0x0C), which item_emu3's size-1 image leaves unset
        c.d32(E3.MAPS + k * 0x100 + 0xC, r["h"])
    c.put(POSB, le32(px) + le32(py))
    meta = dict(f="ffn", form=form, kind=kind, px=px, py=py, rooms=E3.jsonable(rooms))
    if form == "act":
        size = rnd.choice((0, 1, 1, 2, 2, 3, 3, 4)) if i % 9 else 2
        stp = 5 if i % 3 else rnd.choice((1, 2, 3, 4))
        mask = 0x1C89 if i % 5 else rnd.choice((0x3E01, 0xC01, 0x1))
        meta.update(size=size, step=stp, ma=mask, mb=mask, fallback=0, radius=50, origin=None)
        c.dump(POSB, 8)
        return c.call(F_ACT, 0, 0, E3.room_addr(0), POSB, size, mask, stp), meta
    if form == "portal":
        size = 3 if i % 3 else rnd.choice((0, 1, 2))
        ma, mb = (0x3E01, 0xC01) if i % 5 else (rnd.choice((0x3E01, 0x1C89, 0x1)), rnd.choice((0xC01, 0x801, 0x1)))
        fb = 0 if i % 7 else 1
        meta.update(size=size, step=1, ma=ma, mb=mb, fallback=fb, radius=50, origin=[px, py])
        c.lines.append("s %08x 16" % E3.POOLMEM)
        c.dump(POSB, 8)
        return c.call(F_PORTAL, 0, 0, E3.room_addr(0), POSB, POSB, size, ma, mb, fb), meta
    size = rnd.choice((1, 2, 3))
    stp = rnd.choice((5, 5, 5, 2, 3))
    ox, oy = px + rnd.randrange(-6, 7), py + rnd.randrange(-6, 7)
    ma, mb = rnd.choice(((0x1C89, 0xC01), (0x3E01, 0xC01), (0x3E01, 0x801)))
    fb = rnd.choice((0, 1))
    radius = rnd.choice((50, 50, 12, 20))
    meta.update(size=size, step=stp, ma=ma, mb=mb, fallback=fb, radius=radius, origin=[ox, oy])
    c.put(OTHB, le32(ox) + le32(oy))
    c.lines.append("s %08x 16" % E3.POOLMEM)
    c.dump(POSB, 8)
    return c.call(F_FFN, 0, 0, E3.room_addr(0), POSB, OTHB, size, ma, mb, fb, radius, stp), meta


GEN = dict(ffn=gen_ffn)


def mem_spec(f):
    return E3.mem_spec("drop")


def cmd_cases(d, tag, count=None):
    os.makedirs(d, exist_ok=True)
    for f in FAMILIES:
        rnd = random.Random("%s-%s" % (tag, f))
        blocks, metas = [], []
        for i in range(count or COUNTS[f]):
            b, m = GEN[f](rnd, i)
            blocks.append(b)
            metas.append(m)
        open(os.path.join(d, f + ".cases"), "w").write("\n".join(blocks) + "\n")
        open(os.path.join(d, f + ".mem"), "w").write(mem_spec(f))
        json.dump(metas, open(os.path.join(d, f + ".meta"), "w"))
        print("CASES %s %d" % (f, len(metas)))
    for f in FQ_FAMILIES:
        cases = FQ_GEN[f](random.Random("%s-%s" % (tag, f)), count)
        with open(os.path.join(d, f + ".cases"), "w") as fh:
            for c in cases:
                fh.write("\n".join(fq.emit_state(c["m"]) + c.get("extra", []) + fq_dumps(c) + fq_call_lines(c)) + "\n")
        open(os.path.join(d, f + ".mem"), "w").write("\n".join(fq_mem_spec(f)) + "\n")
        json.dump(dict(tag=tag, count=count or FQ_COUNTS[f]), open(os.path.join(d, f + ".meta"), "w"))
        print("CASES %s %d" % (f, len(cases)))


# ------------------------------------------------------------------ the check
def predict_ffn(m, FB, ctl=None):
    rooms = E3.model_rooms(m["rooms"])
    org = tuple(m["origin"]) if m["origin"] else None
    r, x, y = find_free_near(rooms[0], m["px"], m["py"], org, FB, m["size"], m["ma"], m["mb"], m["fallback"], m["radius"], m["step"], ctl)
    ra = 0 if r is None else E3.room_addr(rooms.index(r))
    return ra, x, y


POPS = dict(act=0x14, portal=0x1C, direct=0x24)


def got_ffn(r):
    c = r["c"]
    if c[3] in ("STOP", "OBS"):
        return None
    eax = E3.field(c, "eax")
    pos = dict(r["d"]).get(POSB)
    return eax, int.from_bytes(pos[:4], "little", signed=True), int.from_bytes(pos[4:8], "little", signed=True)


def outcome_ffn(m, want):
    ra, x, y = want
    if (x, y) == (m["px"], m["py"]):
        return "%s start%s" % (m["form"], "" if ra else " refused")
    return "%s moved d=%d" % (m["form"], abs(x - m["px"]) + abs(y - m["py"]))


FFN_ACCOUNTED = ((0x0064D41C, 0x0064D450, "COLL_PlusTest's edge switch table (13 entries), in .text"),)


def ffn_accounted(k):
    kind, pc, addr, size = k
    return kind == "R" and any(lo <= addr < hi for lo, hi, _ in FFN_ACCOUNTED)


def cmd_check(d):
    FB = E3.field_bytes()
    bad_total = 0
    for f in FAMILIES:
        ms = json.load(open(os.path.join(d, f + ".meta")))
        cases, tail = parse_out(os.path.join(d, f + ".out"))
        n = bad = stops = 0
        outs, ctl_sep, ctl_pass = {}, {c: 0 for c in CONTROLS[f]}, {c: 0 for c in CONTROLS[f]}
        per = {}
        for i, (m, r) in enumerate(zip(ms, cases)):
            n += 1
            got = got_ffn(r)
            want = predict_ffn(m, FB)
            if got is None:
                stops += 1
                bad += 1
                print("STOP %d %s" % (i, " ".join(r["c"][3:6])))
                continue
            pop = int(r["c"][5].split("=")[1]) if r["c"][5].startswith("pop=") else None
            if got != (want[0], want[1], want[2]) or pop != POPS[m["form"]]:
                bad += 1
                if bad <= 10:
                    print("MISMATCH %d %s got %s want %s pop %s" % (i, m["form"], got, want, pop))
            k = outcome_ffn(m, want)
            outs[k] = outs.get(k, 0) + 1
            key = "%s size%d step%d" % (m["form"], m["size"], m["step"])
            per[key] = per.get(key, 0) + 1
            for ct in CONTROLS[f]:
                cw = predict_ffn(m, FB, ct)
                if cw != want:
                    ctl_sep[ct] += 1
                    if cw == got:
                        ctl_pass[ct] += 1
                    per["sep %s %s" % (ct, m["form"])] = per.get("sep %s %s" % (ct, m["form"]), 0) + 1
        if len(cases) != len(ms):
            bad += abs(len(cases) - len(ms))
        print("S7E %s cases=%d outputs=%d mismatches=%d stops=%d" % (f, n, len(cases), bad, stops))
        for k in sorted(per):
            print("S7E %s count %s: %d" % (f, k, per[k]))
        for k in sorted(outs):
            print("S7E %s outcome %s: %d" % (f, k, outs[k]))
        for ct in CONTROLS[f]:
            print("S7E %s control %s separating=%d passed=%d" % (f, ct, ctl_sep[ct], ctl_pass[ct]))
        reads = {}
        for kind in ("R", "W"):
            for pc, addr, size, count in tail[kind]:
                reads[(kind, pc, addr, size)] = count
        un = [k for k in sorted(reads) if not E3.accounted((f,) + k) and not ffn_accounted(k)]
        print("S7E %s traced=%d unaccounted=%d" % (f, len(reads), len(un)))
        for k in un[:20]:
            print("UNACCOUNTED %s %08x %08x %d" % k)
        bad_total += bad + len(un)
    for f in FQ_FAMILIES:
        bad_total += check_fq(f, d)
    print("S7E result=%s" % ("ok" if bad_total == 0 else "BAD"))
    return 0 if bad_total == 0 else 1


# ------------------------------------------------------------------ the queue families (frame_queue_emu's image and model)
# qx    (sim/frame rows 35, 37): EventQueueAt 0x005416B0 and UnitQueueEvent 0x005417D0 with a current frame at or past the
#       counter's wrap (negative as i32) and frames on both sides; UnitQueueEventCb 0x00541800 (ECX game, EDX unit; kind,
#       frame, callback, a, b; ret 0x14) with frame -1 and others. A monster's kind 2 ends at UNIT_HasState (observed).
# mevd  (row 46): MonEventDispatch 0x005A7F80 (ECX game, EDX unit; kind, a, b; ret 0xC) with UNIT_HasState 0x00639DF0,
#       UNIT_TestStateBit 0x00625B70 and UnitIsDead 0x005541B0 run whole; a case ends at the handler table's entry
#       (g_MonEventFuncs 0x006E2490, image data, each non-zero entry observed) or returns.
# mevr  (row 47): MonEventsRun 0x00541060 (EAX head, EBX control; ECX game; mode) over monsters some of which are frozen
#       (state 1), records with no callback dispatched through MonEventDispatch run whole: a dropped record goes on to
#       the runner's flag clear and free; a record that reaches a handler ends the case there.
TGAME = fq.GAME + 0x1000      # the game's words from +0x1000 (QUESTS_TimersRun's +0x10F4), declared for every case
SLR = 0x14500000            # stat lists (0x40 apart) and their state bit arrays (from +0x400, 0x10 apart), one per unit
DTS = 0x14600000            # the DataTables' state count at +0xC4
MON_FUNCS_VA = 0x006E2490
FREEZE_SKIP = (3, 4, 5, 8, 12)
FQ_CONTROLS = dict(qx=("unsigned", "keepcb"), mevd=("nofreeze", "deadignored", "skipnone"), mevr=("nofreeze", "freeall"))
FQ_COUNTS = dict(qx=400, mevd=500, mevr=300)


def mon_funcs():
    d = open(fq.EXE, "rb").read()
    return list(struct.unpack_from("<15I", d, fq.va2off(d, MON_FUNCS_VA)))


MON_FUNCS = mon_funcs()


class S7Model(fq.Model):
    def __init__(self, m, neg=None, cnt=0):
        fq.Model.__init__(self, m, None)
        self.neg7 = neg
        self.cnt = cnt

    def queue_at(self, kind, unit, frame, cb, a, b):
        if fq.s32(kind) < 15 and frame & M32 == M32 and self.neg7 == "keepcb":
            return self.queue_ef(kind, unit, cb, a, b)
        if fq.s32(kind) < 15 and frame & M32 != M32 and self.neg7 == "unsigned":
            curu = self.m.r32(fq.GAME + 0xA8)
            f2 = (curu + 1) & M32 if frame & M32 <= curu else frame & M32
            self.m.w32(fq.GAME + 0xA8, (fq.s32(f2) - 1) & M32)
            try:
                return fq.Model.queue_at(self, kind, unit, f2, cb, a, b)
            finally:
                self.m.w32(fq.GAME + 0xA8, curu)
        return fq.Model.queue_at(self, kind, unit, frame, cb, a, b)

    def dead(self, u):
        m = self.m
        if self.neg7 == "deadignored":
            return False
        if u == 0 or m.r8(u + 0xC6) & 1:
            return True
        t, mode = m.r32(u), m.r32(u + 0x10)
        if t == 0:
            return mode in (0, 0x11)
        if t == 1:
            return mode in (0, 0xC)
        return True

    def has_state(self, u, st):
        m = self.m
        if u == 0:
            return False
        t = fq.s32(m.r32(u))
        if t < 0 or (t > 1 and t != 3):
            return False
        if st < 0 or st >= fq.s32(self.cnt):
            return False
        sl = m.r32(u + 0x5C)
        if not sl or not m.r32(sl + 0x10) & 0x80000000:
            return False
        return bool(m.r32(m.r32(sl + 0x58) + 4 * (st >> 5)) & (1 << (st & 31)))

    def dispatch(self, game, u, kind, a, b):
        """MonEventDispatch: None when it returns, else the handler boundary (pc, regs, stack args)."""
        if kind & M32 > 14:
            return None
        skip = FREEZE_SKIP if self.neg7 != "skipnone" else ()
        if self.neg7 != "nofreeze" and kind not in skip and self.has_state(u, 1) and not self.dead(u):
            return None
        h = MON_FUNCS[kind]
        if h == 0:
            return None
        return (h, {"ecx": game, "edx": u}, [a, b])

    def run(self, lst, mode, head):
        if lst != 1:
            return fq.Model.run(self, lst, mode, head)
        m = self.m
        c = self.ctl()
        m.w32(c + 0xA18, 0)
        rec = head
        while rec:
            m.w32(c + 0xA18, m.r32(rec + 0x1C))
            due = mode == 0 or fq.s32(m.r32(rec + 4)) == self.cur()
            if due:
                m.w16(rec + 2, m.r16(rec + 2) | 1)
                cb = m.r32(rec + 0x2C)
                unit, kind = m.r32(rec + 8), m.r8(rec)
                a, b = m.r32(rec + 0x14), m.r32(rec + 0x18)
                if cb == 0:
                    o = self.dispatch(fq.GAME, unit, kind, a, b)
                    if o:
                        self.obs = o
                        return False
                elif cb == fq.CB:
                    self.queue_ef(kind, unit, 0, a, b)
                else:
                    raise ValueError("unmodelled callback %08x" % cb)
                m.w16(rec + 2, m.r16(rec + 2) & 0xFFFE)
                if mode == 1 or m.r16(rec + 2) & 8 or (self.neg7 == "freeall" and cb == 0):
                    self.free(rec)
            rec = m.r32(c + 0xA18)
        return True


def put_mon(rnd, c, m, j):
    """A unit's mode, the +0xC6 bit, its stat list and state bits (state 1 set or not), as case writes."""
    u = fq.unit_addr(j)
    m.w32(u + 0x10, rnd.choice((0, 1, 2, 0xC, 0x11, 3)))
    if rnd.random() < 0.15:
        m.w8(u + 0xC6, rnd.choice((1, 3)))
    if rnd.random() < 0.9:
        sl = SLR + 0x40 * j
        bits = SLR + 0x400 + 0x10 * j
        m.w32(u + 0x5C, sl)
        flag = 0x80000000 if rnd.random() < 0.85 else 0
        word = rnd.getrandbits(32) & ~2
        if rnd.random() < 0.6:
            word |= 2
        c["extra"] += ["w %08x %s" % (sl + 0x10, struct.pack("<I", flag).hex()),
                       "w %08x %s" % (sl + 0x58, struct.pack("<I", bits).hex()),
                       "w %08x %s" % (bits, struct.pack("<I", word).hex())]
        c["sl"][j] = (flag, word)


def fq_case(m, op, cnt, extra2=(), **kw):
    c = dict(m=m, op=op, cnt=cnt, extra=["w %08x %s" % (DTS + 0xC4, struct.pack("<I", cnt & M32).hex())] + list(extra2), sl={})
    c.update(kw)
    return c


def gen_qx(rnd, count=None):
    cases = []
    for i in range(count or FQ_COUNTS["qx"]):
        cur = rnd.choice([0x7FFFFFFF, 0x80000000, 0x80000001, 0x80000040, 0xFFFFFFFE, 0xFFFFFFC0, 0xC0000000,
                          rnd.randrange(0x80000000, 0x100000000)])
        m = fq.fresh(rnd, cur, split=(i % 6 == 5))
        j = rnd.randrange(fq.NUNIT)
        u = fq.unit_addr(j)
        kind = rnd.choice(list(range(15)) + [15, 0xFFFFFFFF])
        if i % 8 == 7:                     # UnitFreeAllEvents (0x00540EE0) over records in slot and every-frame lists
            fq.populate(rnd, m, rnd.randrange(2, 10), units=[j, j, j, (j + 1) % fq.NUNIT],
                        frames=[fq.s32(cur + 1), fq.s32(cur + 2), fq.s32(cur + 65), fq.s32(cur + 300)])
            chain, x = [], m.r32(u + 0xDC)
            while x:
                chain.append(x)
                x = m.r32(x + 0x24)
            if chain and rnd.random() < 0.6:
                m.w32(fq.CTL + 0xA18, rnd.choice(chain))
            cases.append(fq_case(m, ("qx", "fa", 0, u, 0, 0, 0, 0), 0))
            continue
        if i % 16 == 3:                    # QUESTS_TimersRun (0x00543E10) with no quest control at game+0x10F4
            ex = ["w %08x %s" % (TGAME + 4 * k, struct.pack("<I", rnd.getrandbits(32)).hex()) for k in range(0x3C) if k != 0x3D]
            ex.append("w %08x 00000000" % (fq.GAME + 0x10F4))
            cases.append(fq_case(m, ("qx", "tnull", 0, 0, 0, 0, 0, 0), 0, extra2=ex))
            continue
        if m.r32(u) == 1 and kind == 2 and i % 5:
            kind = 0
        rel = rnd.choice([None, -3, -1, 0, 1, 2, 64, 65, 300])
        if rel is None:
            frame = M32
        elif rnd.random() < 0.35:
            frame = rnd.choice([1, 2, 63, 64, 1000, 0x7FFFFFFE, 0x7FFFFFFF, rnd.randrange(1, 0x80000000)])
        else:
            frame = (cur + rel) & M32
        populate_frames = [((cur + 1) & M32), frame if frame != M32 else (cur + 1) & M32]
        fq.populate(rnd, m, rnd.randrange(0, 5), units=[j], frames=[fq.s32(x) for x in populate_frames])
        cb = rnd.choice([0, fq.CB, rnd.getrandbits(32)])
        a, b = rnd.getrandbits(32), rnd.getrandbits(32)
        form = ("direct", "uqe", "cb", "cb")[i % 4]
        if form == "cb" and rnd.random() < 0.5:
            frame = M32
        cases.append(fq_case(m, ("qx", form, kind, u, frame, cb, a, b), 0))
    return cases


def gen_mevd(rnd, count=None):
    cases = []
    for i in range(count or FQ_COUNTS["mevd"]):
        m = fq.fresh(rnd, rnd.randrange(1, 100000))
        cnt = rnd.choice((0, 1, 2, 64, 200, 200, 200))
        c = fq_case(m, None, cnt)
        j = rnd.randrange(fq.NUNIT)
        put_mon(rnd, c, m, j)
        kind = rnd.choice(list(range(15)) * 3 + [15, 0x10, 0xFFFFFFFF])
        c["op"] = ("mevd", fq.unit_addr(j), kind, rnd.getrandbits(32), rnd.getrandbits(32))
        cases.append(c)
    return cases


def gen_mevr(rnd, count=None):
    cases = []
    mons = [j for j, t in enumerate(fq.UNIT_TYPES) if t == 1]
    for i in range(count or FQ_COUNTS["mevr"]):
        cur = rnd.randrange(200, 100000)
        mode = i % 2
        m = fq.fresh(rnd, cur - rnd.choice([1, 3, 10, 64]))
        c = fq_case(m, None, 200)
        frames = [cur, cur, cur, cur + 64, cur + 1]
        cbs = [fq.CB, 0, 0, 0] if i % 3 else [0]
        fq.populate(rnd, m, rnd.randrange(1, 9), units=mons, cbs=cbs, frames=frames)
        for j in mons:
            put_mon(rnd, c, m, j)
            if i % 4 != 3:                 # mostly frozen and alive, so that most records are dropped
                u = fq.unit_addr(j)
                if rnd.random() < 0.8:
                    m.w32(u + 0x10, rnd.choice((1, 2, 3)))
                    m.w8(u + 0xC6, 0)
        for x in range(fq.NREC1):
            rec = fq.POOL + 0x30 * x
            if m.r32(rec + 4) == M32 and m.r16(rec + 2) & 4 and rnd.random() < 0.15:
                m.w16(rec + 2, m.r16(rec + 2) | 8)
        m.w32(fq.GAME + 0xA8, cur)
        m.w32(fq.CTL, fq.smod64(cur))
        m.w32(fq.CTL + 0xA18, rnd.getrandbits(32))
        head = m.r32(fq.CTL + 0xA04 + 4) if mode == 0 else m.r32(fq.CTL + 4 + 4 * (64 + fq.smod64(cur)))
        c["op"] = ("mevr", 1, mode, head)
        cases.append(c)
    return cases


FQ_GEN = dict(qx=gen_qx, mevd=gen_mevd, mevr=gen_mevr)


def fq_mem_spec(f):
    out = fq.mem_spec() + ["bytes %08x %s" % (SLR, "00" * 0x800), "bytes %08x %s" % (DTS, "00" * 0x100),
                           "bytes %08x %s" % (TGAME, "00" * 0x100),
                           "dword 00744304 %08x" % DTS]
    if f == "qx":
        out += ["observe %08x" % fq.HASSTATE]
    else:
        out += ["observe %08x" % h for h in sorted(set(MON_FUNCS)) if h]
    return out


def fq_dumps(c):
    return fq.dumps() + ["d %08x %d" % (TGAME, 0x100)]


def fq_call_lines(c):
    op = c["op"]
    hx = fq.hx
    if op[0] == "qx":
        _, form, kind, u, frame, cb, a, b = op
        if form == "direct":
            return ["r eax %s" % hx(frame), "call 005416b0 %s %s %s %s %s %s" % (hx(kind), hx(fq.GAME), hx(u), hx(cb), hx(a), hx(b))]
        if form == "fa":
            return ["call 00540ee0 %s %s" % (hx(fq.GAME), hx(u))]
        if form == "tnull":
            return ["call 00543e10 %s 0" % hx(fq.GAME)]
        if form == "uqe":
            return ["call 005417d0 %s %s %s %s %s %s" % (hx(fq.GAME), hx(u), hx(kind), hx(frame), hx(a), hx(b))]
        return ["call 00541800 %s %s %s %s %s %s %s" % (hx(fq.GAME), hx(u), hx(kind), hx(frame), hx(cb), hx(a), hx(b))]
    if op[0] == "mevd":
        _, u, kind, a, b = op
        return ["call 005a7f80 %s %s %s %s %s" % (hx(fq.GAME), hx(u), hx(kind), hx(a), hx(b))]
    if op[0] == "mevr":
        _, lst, mode, head = op
        return ["r eax %s" % hx(head), "r ebx %s" % hx(fq.CTL), "call 00541060 %s 0 %s" % (hx(fq.GAME), hx(mode))]
    raise ValueError(op)


def fq_apply(c, neg=None):
    m = c["m"].copy()
    md = S7Model(m, neg, c["cnt"])
    op = c["op"]
    if op[0] == "qx":
        _, form, kind, u, frame, cb, a, b = op
        if form == "fa":
            md.free_all(u)
            return m, None, 0
        if form == "tnull":
            return m, None, 0
        md.queue_at(kind, u, frame, 0 if form == "uqe" else cb, a, b)
        return m, md.obs, {"direct": 16, "uqe": 16, "cb": 20}[form]
    if op[0] == "mevd":
        _, u, kind, a, b = op
        return m, md.dispatch(fq.GAME, u, kind, a, b), 12
    _, lst, mode, head = op
    md.run(lst, mode, head)
    return m, md.obs, 4


def fq_compare(c, out, neg=None):
    m, obs, pop = fq_apply(c, neg)
    if "stop" in out:
        return False, "STOP " + out["stop"]
    if obs:
        pc, regs, args = obs
        if out.get("obs_pc") != pc:
            return False, "boundary %s != %08x" % (out.get("obs_pc"), pc)
        got = list(struct.unpack_from("<%dI" % len(args), out["stack"], 4))
        if got != [x & M32 for x in args]:
            return False, "boundary args %r != %r" % (got, args)
        for k, v in (regs or {}).items():
            if int(out["regs"][k], 16) != v:
                return False, "boundary %s=%s != %08x" % (k, out["regs"][k], v)
    else:
        if "obs_pc" in out:
            return False, "unexpected boundary %08x" % out["obs_pc"]
        if out.get("pop") != pop:
            return False, "pop %s != %s" % (out.get("pop"), pop)
    for a, n in fq.REGIONS:
        if out["dumps"].get(a) != m.region(a, n):
            return False, "region %08x differs" % a
    return True, ""


def fq_label(c):
    op = c["op"]
    m0, obs, _ = fq_apply(c)
    if op[0] == "qx":
        _, form, kind, u, frame, cb, a, b = op
        if form == "fa":
            lists = set()
            x = c["m"].r32(u + 0xDC)
            while x:
                lists.add("ef" if c["m"].r32(x + 4) == M32 else "slot%d" % fq.smod64(c["m"].r32(x + 4)))
                x = c["m"].r32(x + 0x24)
            walker = c["m"].r32(fq.CTL + 0xA18) != 0
            return "fa lists=%s%s" % (min(len(lists), 3), " walker" if walker else "")
        if form == "tnull":
            return "tnull returned"
        split = c["m"].r32(fq.POOL + 0x7080) == 0
        cur = fq.s32(c["m"].r32(fq.GAME + 0xA8))
        if obs:
            return "%s boundary HasState" % form
        if fq.s32(kind) >= 15:
            return "%s kind refused" % form
        if frame & M32 == M32:
            return "%s frame -1%s" % (form, " cb dropped" if cb else "")
        side = "cur<0" if cur < 0 else "cur>=0"
        raised = fq.s32(frame) <= cur
        return "%s %s frame%s %s%s" % (form, side, "<0" if fq.s32(frame) < 0 else ">=0", "raised" if raised else "kept",
                                       " block2" if split else "")
    if op[0] == "mevd":
        return "handler" if obs else "returned"
    return "handler" if obs else "walk ended"


def check_fq(f, d):
    meta = json.load(open(os.path.join(d, f + ".meta")))
    cases = FQ_GEN[f](random.Random("%s-%s" % (meta["tag"], f)), meta["count"])
    outs, traced = fq.read_out(os.path.join(d, f + ".out"))
    bad = 0
    if len(outs) != len(cases):
        bad += 1
        print("COUNT %s %d != %d" % (f, len(outs), len(cases)))
    labels, sep, passed = {}, {k: 0 for k in FQ_CONTROLS[f]}, {k: 0 for k in FQ_CONTROLS[f]}
    for c, o in zip(cases, outs):
        ok, why = fq_compare(c, o)
        if not ok:
            bad += 1
            if bad <= 10:
                print("MISMATCH %s %d %s %r" % (f, o["n"], why, c["op"][:3]))
        k = fq_label(c)
        labels[k] = labels.get(k, 0) + 1
        mw, ow, _ = fq_apply(c)
        for ct in FQ_CONTROLS[f]:
            mn, on, _ = fq_apply(c, ct)
            if any(mw.region(a, n) != mn.region(a, n) for a, n in fq.REGIONS) or ow != on:
                sep[ct] += 1
                passed[ct] += fq_compare(c, o, ct)[0]
    print("S7E %s cases=%d outputs=%d mismatches=%d traced=%d" % (f, len(cases), len(outs), bad, len(traced)))
    for k in sorted(labels):
        print("S7E %s outcome %s: %d" % (f, k, labels[k]))
    for ct in FQ_CONTROLS[f]:
        print("S7E %s control %s separating=%d passed=%d" % (f, ct, sep[ct], passed[ct]))
    un = [t for t in traced if not fq_accounted(t)]
    for t in un[:20]:
        print("UNACCOUNTED %s" % t)
    return bad + len(un)


FQ_ACCOUNTED = ((0x006E0B9C, 0x006E0BB8, "g_UnitTypeEventList: image data, no write xref (run:2026-10-30-frame-emu-2)"),
                (0x006CE268, 0x006CE2E8, "the bit masks of UNIT_TestStateBit: image data"),
                (0x006E2490, 0x006E24CC, "g_MonEventFuncs: image data"),
                (0x005A7FE0, 0x005A7FF2, "MonEventDispatch's switch tables, in .text"),
                (0x00744304, 0x00744308, "g_pDataTables, spec"))


def fq_accounted(line):
    p = line.split()
    return p[0] == "R" and any(lo <= int(p[2], 16) < hi for lo, hi, _ in FQ_ACCOUNTED)


def cmd_manifest(d, write):
    names = sorted(x for x in os.listdir(d) if not x.startswith("manifest") and os.path.isfile(os.path.join(d, x)))
    lines = ["%s  %s" % (hashlib.sha256(open(os.path.join(d, x), "rb").read()).hexdigest(), x) for x in names]
    if write:
        open(os.path.join(d, "manifest.sha256"), "w").write("\n".join(lines) + "\n")
    print("\n".join(lines))


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=("cases", "check", "manifest"))
    ap.add_argument("--dir", default=DEFAULT_DIR)
    ap.add_argument("--tag", default="n66u")
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--count", type=int, default=None, help="a development run's case count (the kept run uses COUNTS)")
    a = ap.parse_args(argv)
    if a.cmd == "cases":
        cmd_cases(a.dir, a.tag, a.count)
        return 0
    if a.cmd == "check":
        return cmd_check(a.dir)
    cmd_manifest(a.dir, a.write)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
