#!/usr/bin/env python3
"""Plan 0055 phase 1.2 (the server frame: the unit events and the queue, `lane/r55b`): the event queue's list
operations and the frame's unit-event pass run under Ghidra's p-code emulator (ADR-0015, ADR-0021) with
re/ghidra_scripts/EmuBoundary.java and compared byte for byte with the model below. No game run, no slot.

    python3 -I tools/frame_queue_emu.py cases [--dir D] [--tag T]   write D/<family>.cases and D/<family>.mem
    GHIDRA_PROJ_DIR=... GHIDRA_HEADLESS_MAXMEM=3G tools/ghidra.sh emuboundary D/<f>.cases D/<f>.mem > D/<f>.out
    python3 -I tools/frame_queue_emu.py check [--dir D] [--tag T]   compare every D/<family>.out with the model
    python3 -I tools/frame_queue_emu.py manifest [--dir D] [--write]

Default D: workspace/logs/r55b/emu. Every case draws from random.Random("<tag>-<family>") (default tag `r55b`), so
`cases` regenerates identical files; a development run uses another tag and another directory (reverser rule 6).

The declared image (every case): the game at GAME (+0xA8 frame, +0xB8 the event control), the control CTL (0xA20
bytes: +0x000 the current slot, +0x004 the 5x64 slot heads, +0x504 the slot tails, +0xA04 the five every-frame heads,
+0xA18 the walker's saved next, +0xA1C the first record block), two record blocks POOL and POOL2 (records of 0x30
bytes at the block's start, +0x7080 the block's free list, +0x7084 the next block) and eight units (+0x00 type,
+0x0C guid, +0xDC the unit's record chain). The type-to-list table `g_UnitTypeEventList` (0x006E0B9C, 7 dwords) is
the image's own (declared, never written). Every region is written to zero by the memory spec before each case; the
case writes the non-zero dwords of its state, built by the model's own queue operations (so a pre-state is an input,
not a claim). After the call the whole of CTL, the records of both blocks in use, both block headers and the units
are dumped and compared with the model's state, byte for byte.

Families (entry, what a case covers):
  qat     0x005417D0 UnitQueueEvent(game, unit, kind, frame, a, b) and 0x005416B0 EventQueueAt (ECX kind, EDX game,
          EAX frame; unit, callback, a, b): the kind bound, the frame raise, the record taken from the first block
          with a free record (memset, unit, guid, type, chain head), the append at the slot's tail, the head set only
          when empty, frame -1 sent to the every-frame queue with the callback dropped. A monster's kind-2 event ends
          at UNIT_HasState (0x00639DF0, observed boundary; its arguments unit, 54 are compared, nothing after).
  qef     0x005415E0 EventQueueEveryFrame (EBX kind, EAX unit, EDI game; callback, a, b) and the wrapper 0x00541650:
          the push on the front of the type's every-frame list, flag 4, frame -1.
  free    0x00540CD0 EventFree (ESI record, EDI game): a running record (flag 1) only gets flag 8; otherwise the
          walker's saved next advanced when it is this record, the unlink from its list (head, tail, middle; slot or
          every-frame), the unlink from the unit's chain, the push on the first block's free list, flags = 2.
  cancel  0x00540E60 UNIT_CancelEvents(game, unit, kind, a), 0x00540EA0 (game, unit, kind, callback), 0x00540EE0
          (game, unit: every record of the unit freed, its unit field cleared, the chain head 0) and 0x00540F30.
  run     the five list runners 0x00540F60 (players), 0x00541060 (monsters), 0x00541160 (objects), 0x00541240
          (missiles), 0x00541320 (items), mode 0 (every-frame list) and 1 (the slot list: records due this frame),
          over records whose callback is 0x00541650 (UnitQueueEveryFrame, a real entry with the callback's
          signature: each run queues one every-frame record for its unit) or 0. A record with no callback ends the
          case at its type's dispatch (observed boundary: 0x00581220, 0x005A7F80, 0x00586AD0, 0x005ADCC0,
          0x00562DA0; the arguments and the state at the call are compared, the dispatch is not covered).
  tick    0x005414D0 GameRunUnitEvents(game): the current slot written, the ten walks in their order, each list's
          head read at its own call, over records of every type; a record with no callback ends the case at its
          dispatch, which names the list that ran it.

Not covered: the block allocator (0x00540BB0, 0x0040B430: no case exhausts both blocks; guarded), the fatal paths,
0x005544B0 and everything after UNIT_HasState, every dispatch and event function, game create and free (0x00541470,
0x00541400). Negative controls, one per family, are model variants that must fail where they predict differently.
Stdlib only.
"""
import argparse
import hashlib
import os
import random
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DEFAULT_DIR = os.path.join(ROOT, "workspace", "logs", "r55b", "emu")
EXE = os.path.join(ROOT, "workspace", "install", "app", "game.exe")

GAME = 0x14000000
CTL = 0x14100000
POOL = 0x14200000
POOL2 = 0x14300000
UNITS = 0x14400000
NREC1, NREC2 = 24, 8
NUNIT = 8
UNIT_TYPES = [0, 1, 1, 2, 3, 3, 4, 1]
TYPELIST_VA = 0x006E0B9C
CB = 0x00541650             # UnitQueueEveryFrame: (ECX game, EDX unit; kind, a, b), ret 0xC
HASSTATE = 0x00639DF0
RUNNERS = {0: 0x00540F60, 1: 0x00541060, 3: 0x00541160, 2: 0x00541240, 4: 0x00541320}   # by list index
DISPATCH = {0: 0x00581220, 1: 0x005A7F80, 3: 0x00586AD0, 2: 0x005ADCC0, 4: 0x00562DA0}  # by list index
DISPATCH_ARGS = {0: 3, 1: 3, 3: 1, 2: 1, 4: 1}       # stack args pushed: kind, a, b / kind only
TICK_ORDER = [(2, 0), (2, 1), (0, 0), (0, 1), (1, 0), (1, 1), (3, 0), (3, 1), (4, 0), (4, 1)]   # (list, mode)
FATAL = (0x00408090, 0x00408A60, 0x00681E09)
ALLOC = (0x0040B4B0, 0x0040B430, 0x0040B480, 0x00540BB0)
FAMILIES = ("qat", "qef", "free", "cancel", "run", "tick")
M32 = 0xFFFFFFFF


def image_typelist():
    d = open(EXE, "rb").read()
    return list(struct.unpack_from("<7i", d, va2off(d, TYPELIST_VA)))


def va2off(d, va):
    pe = struct.unpack_from("<I", d, 0x3C)[0]
    nsec = struct.unpack_from("<H", d, pe + 6)[0]
    optsz = struct.unpack_from("<H", d, pe + 20)[0]
    so = pe + 24 + optsz
    for i in range(nsec):
        o = so + 40 * i
        vsize, rva, rsize, rptr = struct.unpack_from("<IIII", d, o + 8)
        if 0x400000 + rva <= va < 0x400000 + rva + min(vsize, rsize):
            return rptr + va - 0x400000 - rva
    raise ValueError(hex(va))


TYPELIST = image_typelist()


def s32(v):
    v &= M32
    return v - (1 << 32) if v & 0x80000000 else v


def smod64(v):
    """`and 0x8000003F; jns; dec; or 0xFFFFFFC0; inc`: the signed remainder of v by 64 (C `%`)."""
    v &= M32
    r = v & 0x8000003F
    if r & 0x80000000:
        r = (((r - 1) & M32) | 0xFFFFFFC0) + 1
        r &= M32
    return r


# ------------------------------------------------------------------------------------------------- the memory
class Mem:
    def __init__(self):
        self.b = {}

    def copy(self):
        m = Mem()
        m.b = dict(self.b)
        return m

    def r8(self, a):
        return self.b.get(a & M32, 0)

    def w8(self, a, v):
        self.b[a & M32] = v & 0xFF

    def r16(self, a):
        return self.r8(a) | self.r8(a + 1) << 8

    def w16(self, a, v):
        self.w8(a, v)
        self.w8(a + 1, v >> 8)

    def r32(self, a):
        return self.r16(a) | self.r16(a + 2) << 16

    def w32(self, a, v):
        self.w16(a, v)
        self.w16(a + 2, v >> 16)

    def region(self, a, n):
        return bytes(self.r8(a + i) for i in range(n))


REGIONS = [(GAME, 0x100), (CTL, 0xA20), (POOL, NREC1 * 0x30), (POOL + 0x7080, 8), (POOL2, NREC2 * 0x30),
           (POOL2 + 0x7080, 8), (UNITS, NUNIT * 0x100)]


def unit_addr(j):
    return UNITS + 0x100 * j


class Model:
    """The queue as the code reads (frame/0002 § 2-4). `neg` names one wrong variant (the negative controls)."""

    def __init__(self, m, neg=None):
        self.m = m
        self.neg = neg
        self.obs = None          # (pc, regs dict, stack args) when a modelled call reaches an observed boundary

    # the pieces
    def ctl(self):
        return self.m.r32(GAME + 0xB8)

    def cur(self):
        return s32(self.m.r32(GAME + 0xA8))

    def ulist(self, typ):
        return TYPELIST[typ]

    def ef_head(self, lst):
        return self.ctl() + 0xA04 + 4 * lst

    def slot_head(self, lst, frame):
        return self.ctl() + 4 + 4 * ((lst * 64 + smod64(frame)) & M32)

    def slot_tail(self, lst, frame):
        return self.ctl() + 0x504 + 4 * ((lst * 64 + smod64(frame)) & M32)

    def alloc(self, unit):
        m = self.m
        blk = m.r32(self.ctl() + 0xA1C)
        while blk and m.r32(blk + 0x7080) == 0:
            blk = m.r32(blk + 0x7084)
        if not blk:
            raise RuntimeError("both blocks exhausted (not modelled)")
        rec = m.r32(blk + 0x7080)
        m.w32(blk + 0x7080, m.r32(rec + 0x1C))
        for i in range(0x30):
            m.w8(rec + i, 0)
        m.w32(rec + 8, unit)
        head = m.r32(unit + 0xDC) if unit else 0
        m.w32(rec + 0x24, head)
        if head:
            m.w32(head + 0x28, rec)
        m.w32(rec + 0x28, 0)
        if unit:
            m.w32(unit + 0xDC, rec)
        m.w32(rec + 0x10, m.r32(unit) if unit else 6)
        m.w16(rec + 2, m.r16(rec + 2) & 0xFFFD)
        m.w32(rec + 0xC, m.r32(unit + 0xC) if unit else M32)
        return rec

    def queue_ef(self, kind, unit, cb, a, b):
        m = self.m
        if s32(kind) >= 15:
            return None
        rec = self.alloc(unit)
        m.w16(rec + 2, m.r16(rec + 2) | 4)
        m.w32(rec + 0x14, a)
        m.w8(rec, kind)
        m.w32(rec + 4, M32)
        m.w32(rec + 0x18, b)
        m.w32(rec + 0x2C, cb)
        lst = self.ulist(m.r32(unit) if unit else 6)
        hp = self.ef_head(lst)
        if self.neg == "qef-tail":
            x, prev = m.r32(hp), 0
            while x:
                prev, x = x, m.r32(x + 0x1C)
            m.w32(rec + 0x1C, 0)
            m.w32(rec + 0x20, prev)
            if prev:
                m.w32(prev + 0x1C, rec)
            else:
                m.w32(hp, rec)
            return rec
        h = m.r32(hp)
        m.w32(rec + 0x1C, h)
        m.w32(rec + 0x20, 0)
        if h:
            m.w32(h + 0x20, rec)
        m.w32(hp, rec)
        return rec

    def queue_at(self, kind, unit, frame, cb, a, b):
        m = self.m
        if s32(kind) >= 15:
            return None
        if frame & M32 == M32:
            return self.queue_ef(kind, unit, 0, a, b)
        if s32(frame) <= self.cur():
            frame = (self.cur() + 1) & M32
        if unit and m.r32(unit) == 1 and kind == 2:
            self.obs = (HASSTATE, None, [unit, 0x36])
            return "obs"
        rec = self.alloc(unit)
        m.w32(rec + 0x14, a)
        m.w8(rec, kind)
        m.w32(rec + 4, frame)
        m.w32(rec + 0x18, b)
        m.w32(rec + 0x2C, cb)
        lst = self.ulist(m.r32(rec + 0x10))
        tp = self.slot_tail(lst, frame)
        hp = self.slot_head(lst, frame)
        if self.neg == "qat-head":
            h = m.r32(hp)
            m.w32(rec + 0x1C, h)
            m.w32(rec + 0x20, 0)
            if h:
                m.w32(h + 0x20, rec)
            else:
                m.w32(tp, rec)
            m.w32(hp, rec)
            return rec
        m.w32(rec + 0x1C, 0)
        t = m.r32(tp)
        m.w32(rec + 0x20, t)
        if t:
            m.w32(t + 0x1C, rec)
        m.w32(tp, rec)
        if m.r32(hp) == 0:
            m.w32(hp, rec)
        return rec

    def free(self, rec):
        m = self.m
        fl = m.r16(rec + 2)
        if fl & 1:
            m.w16(rec + 2, fl | 8)
            return
        c = self.ctl()
        if rec == m.r32(c + 0xA18) and self.neg != "free-noadvance":
            m.w32(c + 0xA18, m.r32(rec + 0x1C))
        prev, nxt = m.r32(rec + 0x20), m.r32(rec + 0x1C)
        frame = m.r32(rec + 4)
        lst = self.ulist(m.r32(rec + 0x10))
        if prev:
            m.w32(prev + 0x1C, nxt)
        else:
            hp = self.ef_head(lst) if frame == M32 else self.slot_head(lst, frame)
            m.w32(hp, nxt)
        nxt = m.r32(rec + 0x1C)
        if nxt:
            m.w32(nxt + 0x20, m.r32(rec + 0x20))
        elif frame != M32:
            tp = self.slot_tail(lst, frame)
            if m.r32(tp) == rec:
                m.w32(tp, m.r32(rec + 0x20))
        unit = m.r32(rec + 8)
        if unit:
            n, p = m.r32(rec + 0x24), m.r32(rec + 0x28)
            if n:
                m.w32(n + 0x28, p)
            p = m.r32(rec + 0x28)
            if p:
                m.w32(p + 0x24, m.r32(rec + 0x24))
            else:
                m.w32(unit + 0xDC, m.r32(rec + 0x24))
        blk = m.r32(c + 0xA1C)
        m.w32(rec + 0x1C, m.r32(blk + 0x7080))
        m.w32(rec + 0x20, 0)
        m.w32(blk + 0x7080, rec)
        m.w16(rec + 2, 2)

    def cancel(self, unit, kind, a, by_cb=False):
        m = self.m
        rec = m.r32(unit + 0xDC) if unit else 0
        while rec:
            nxt = m.r32(rec + 0x24)
            if m.r8(rec) == kind & M32:
                if by_cb:
                    match = a == m.r32(rec + 0x2C)
                else:
                    match = a == 0 or m.r32(rec + 0x14) == a or self.neg == "cancel-kindonly"
                if match:
                    self.free(rec)
            rec = nxt

    def free_all(self, unit):
        m = self.m
        rec = m.r32(unit + 0xDC) if unit else 0
        while rec:
            nxt = m.r32(rec + 0x24)
            self.free(rec)
            m.w32(rec + 8, 0)
            rec = nxt
        if unit:
            m.w32(unit + 0xDC, 0)

    def run(self, lst, mode, head):
        """One runner call: returns False when the walk stopped at an observed dispatch."""
        m = self.m
        c = self.ctl()
        m.w32(c + 0xA18, 0)
        rec = head
        while rec:
            if self.neg != "run-nextafter":
                m.w32(c + 0xA18, m.r32(rec + 0x1C))
            due = mode == 0 or s32(m.r32(rec + 4)) == self.cur()
            if due:
                m.w16(rec + 2, m.r16(rec + 2) | 1)
                cb = m.r32(rec + 0x2C)
                unit, kind = m.r32(rec + 8), m.r8(rec)
                a, b = m.r32(rec + 0x14), m.r32(rec + 0x18)
                if cb == 0:
                    args = [kind, a, b][:DISPATCH_ARGS[lst]]
                    self.obs = (DISPATCH[lst], {"ecx": GAME, "edx": unit}, args)
                    return False
                if cb != CB:
                    raise ValueError("unmodelled callback %08x" % cb)
                self.queue_ef(kind, unit, 0, a, b)
                m.w16(rec + 2, m.r16(rec + 2) & 0xFFFE)
                if mode == 1 or m.r16(rec + 2) & 8:
                    if self.neg == "run-nextafter":
                        self.free(rec)
                        m.w32(c + 0xA18, m.r32(rec + 0x1C))
                    else:
                        self.free(rec)
                elif self.neg == "run-nextafter":
                    m.w32(c + 0xA18, m.r32(rec + 0x1C))
            elif self.neg == "run-nextafter":
                m.w32(c + 0xA18, m.r32(rec + 0x1C))
            rec = m.r32(c + 0xA18)
        return True

    def tick(self):
        m = self.m
        c = self.ctl()
        m.w32(c, smod64(m.r32(GAME + 0xA8)))
        order = TICK_ORDER if self.neg != "tick-playersfirst" else [(0, 0), (0, 1), (2, 0), (2, 1)] + TICK_ORDER[4:]
        for lst, mode in order:
            head = m.r32(c + 0xA04 + 4 * lst) if mode == 0 else m.r32(c + 4 + 4 * (lst * 64 + m.r32(c)))
            if not self.run(lst, mode, head):
                return False
        return True


# ------------------------------------------------------------------------------------------------- the cases
def mem_spec():
    out = ["guard %08x" % a for a in FATAL + ALLOC]
    for a, n in REGIONS:
        out.append("bytes %08x %s" % (a, "00" * n))
    out.append("const bytes %08x %s" % (TYPELIST_VA, struct.pack("<7i", *TYPELIST).hex()))
    return out


def fresh(rnd, cur, split=False):
    """An empty game: the control, two blocks with shuffled free lists, eight units."""
    m = Mem()
    m.w32(GAME + 0xA8, cur)
    m.w32(GAME + 0xB8, CTL)
    m.w32(CTL + 0xA1C, POOL)
    m.w32(POOL + 0x7084, POOL2)
    for base, n in ((POOL, NREC1), (POOL2, NREC2)):
        order = list(range(n))
        rnd.shuffle(order)
        if split and base == POOL:
            order = []
        prev = 0
        for i in reversed(order):
            m.w32(base + 0x30 * i + 0x1C, prev)
            prev = base + 0x30 * i
        m.w32(base + 0x7080, prev)
    for j, t in enumerate(UNIT_TYPES):
        u = unit_addr(j)
        m.w32(u, t)
        m.w32(u + 0xC, rnd.randrange(1, 0x10000))
        m.w32(u + 0x80, GAME)
    return m


def populate(rnd, m, n, units=None, cb=0, frames=None, cbs=None):
    """n random queue operations through the model (a pre-state, not a claim)."""
    md = Model(m)
    made = []
    for _ in range(n):
        j = rnd.choice(units if units is not None else range(NUNIT))
        u = unit_addr(j)
        kind = rnd.choice([0, 1, 3, 5, 7, 12]) if m.r32(u) == 1 else rnd.randrange(0, 15)
        a, b = rnd.choice([0, 0, 1, 2, rnd.getrandbits(32)]), rnd.getrandbits(32)
        c = rnd.choice(cbs) if cbs else cb
        if rnd.random() < 0.3:
            r = md.queue_ef(kind, u, c, a, b)
        else:
            f = rnd.choice(frames) if frames else md.cur() + rnd.choice([1, 2, 3, 5, 63, 64, 65, 128, 300])
            r = md.queue_at(kind, u, f & M32, c, a, b)
        if r and r != "obs":
            made.append(r)
    return made


def emit_state(m):
    lines = []
    for a, n in REGIONS:
        i = 0
        while i < n:
            if m.r32(a + i) == 0:
                i += 4
                continue
            j = i
            while j < n and m.r32(a + j) != 0:
                j += 4
            lines.append("w %08x %s" % (a + i, m.region(a + i, j - i).hex()))
            i = j
    return lines


def dumps():
    return ["d %08x %d" % (a, n) for a, n in REGIONS]


def hx(v):
    return "%08x" % (v & M32)


def gen_qat(rnd):
    cases = []
    for i in range(400):
        cur = rnd.choice([1, 2, 63, 64, 65, 1000, rnd.randrange(1, 2000000)])
        m = fresh(rnd, cur, split=(i % 17 == 0))
        j = rnd.randrange(NUNIT)
        u = unit_addr(j)
        kind = rnd.choice(list(range(15)) * 3 + [15, 16, 0x7F, 0xFFFFFFFF, 0x80000000])
        if m.r32(u) == 1 and kind == 2 and i % 4:
            kind = 0
        if i % 10 == 0:       # a monster's AI event: the observed boundary at UNIT_HasState
            j, kind = 1, 2
            u = unit_addr(j)
        rel = rnd.choice([None, -1000, -1, 0, 1, 2, 3, 31, 63, 64, 65, 127, 128, 5000])
        frame = M32 if rel is None else (cur + rel) & M32
        # crowd the slot the new record lands in (its own frame, and the frames 64 on), plus the rest at random
        tgt = cur + 1 if rel is None or rel <= 0 else cur + rel
        populate(rnd, m, rnd.randrange(0, 5), units=[j], frames=[tgt, tgt, tgt + 64])
        populate(rnd, m, rnd.randrange(0, 5))
        cb = rnd.choice([0, 0, CB, rnd.getrandbits(32)])
        a, b = rnd.getrandbits(32), rnd.getrandbits(32)
        direct = i % 3 == 0
        cases.append(dict(m=m, op=("qat", kind, u, frame, cb if direct else 0, a, b), direct=direct))
    return cases


def gen_qef(rnd):
    cases = []
    for i in range(150):
        cur = rnd.randrange(1, 100000)
        m = fresh(rnd, cur, split=(i % 13 == 0))
        populate(rnd, m, rnd.randrange(0, 8))
        u = unit_addr(rnd.randrange(NUNIT))
        kind = rnd.choice(list(range(15)) * 2 + [15, 20, 0xFFFFFFFF])
        cb = rnd.choice([0, CB, rnd.getrandbits(32)])
        a, b = rnd.getrandbits(32), rnd.getrandbits(32)
        direct = i % 2 == 0
        cases.append(dict(m=m, op=("qef", kind, u, cb if direct else 0, a, b), direct=direct))
    return cases


def gen_free(rnd):
    cases = []
    while len(cases) < 300:
        cur = rnd.randrange(1, 100000)
        m = fresh(rnd, cur)
        frames = None
        if rnd.random() < 0.5:   # crowd one slot list
            f = cur + rnd.choice([1, 2, 64])
            frames = [f, f, f, f + 64]
        made = populate(rnd, m, rnd.randrange(1, 9), units=rnd.choice([None, [1, 2], [3]]), frames=frames)
        if not made:
            continue
        rec = rnd.choice(made)
        if rnd.random() < 0.2:
            m.w16(rec + 2, m.r16(rec + 2) | 1)
        r = rnd.random()
        if r < 0.35:
            m.w32(CTL + 0xA18, rec)
        elif r < 0.6:
            m.w32(CTL + 0xA18, rnd.choice(made))
        if rnd.random() < 0.15:
            m.w32(rec + 8, 0)    # a record whose unit was cleared (0x00540EE0) but not yet freed
        cases.append(dict(m=m, op=("free", rec)))
    return cases


def gen_cancel(rnd):
    cases = []
    while len(cases) < 150:
        cur = rnd.randrange(1, 100000)
        m = fresh(rnd, cur)
        made = populate(rnd, m, rnd.randrange(0, 12), units=[1, 1, 1, 2, 4], cbs=[0, CB])
        u = unit_addr(1)
        chain = []
        x = m.r32(u + 0xDC)
        while x:
            chain.append(x)
            x = m.r32(x + 0x24)
        if chain and rnd.random() < 0.5:
            m.w32(CTL + 0xA18, rnd.choice(chain))
        if chain and rnd.random() < 0.2:
            x = rnd.choice(chain)
            m.w16(x + 2, m.r16(x + 2) | 1)
        which = rnd.choice(["cancel", "cancel", "cancelcb", "freeall", "freeall2"])
        kind = rnd.choice([0, 1, 3, 5, 7, 12, 2])
        a = rnd.choice([0, 0, 1, 2]) if which == "cancel" else rnd.choice([0, CB])
        cases.append(dict(m=m, op=(which, u, kind, a)))
    return cases


def gen_run(rnd):
    cases = []
    for i in range(300):
        cur = rnd.randrange(200, 100000)
        lst = [0, 1, 3, 2, 4][i % 5]
        mode = (i // 5) % 2
        typ = {0: 0, 1: 1, 3: 2, 2: 3, 4: 4}[lst]
        units = [j for j, t in enumerate(UNIT_TYPES) if t == typ]
        m = fresh(rnd, cur - rnd.choice([1, 3, 10, 64]))
        md = Model(m)
        obs_case = i % 3 == 0
        cbs = [CB, CB, CB, 0] if obs_case else [CB]
        # due now (cur), due later in the same slot (cur + 64k), elsewhere
        frames = [cur, cur, cur, cur + 64, cur + 128, cur + 1]
        populate(rnd, m, rnd.randrange(1, 9), units=units, cbs=cbs, frames=frames)
        populate(rnd, m, rnd.randrange(0, 4), cbs=[CB])
        for x in range(NREC1):   # a few every-frame records already asked to be freed
            rec = POOL + 0x30 * x
            if m.r32(rec + 4) == M32 and m.r16(rec + 2) & 4 and rnd.random() < 0.15:
                m.w16(rec + 2, m.r16(rec + 2) | 8)
        m.w32(GAME + 0xA8, cur)
        m.w32(CTL, smod64(cur))
        m.w32(CTL + 0xA18, rnd.getrandbits(32))
        head = m.r32(CTL + 0xA04 + 4 * lst) if mode == 0 else m.r32(CTL + 4 + 4 * (lst * 64 + smod64(cur)))
        cases.append(dict(m=m, op=("run", lst, mode, head)))
    return cases


def gen_tick(rnd):
    cases = []
    for i in range(100):
        cur = rnd.randrange(200, 100000)
        m = fresh(rnd, cur - rnd.choice([1, 2, 5, 64]))
        cbs = [CB, CB, CB, CB, 0] if i % 2 else [CB]
        frames = [cur, cur, cur + 64, cur + 1]
        populate(rnd, m, rnd.randrange(3, 14), cbs=cbs, frames=frames)
        m.w32(GAME + 0xA8, cur)
        m.w32(CTL, rnd.randrange(64))         # stale: the pass writes it
        m.w32(CTL + 0xA18, rnd.getrandbits(32))
        cases.append(dict(m=m, op=("tick",)))
    return cases


GEN = {"qat": gen_qat, "qef": gen_qef, "free": gen_free, "cancel": gen_cancel, "run": gen_run, "tick": gen_tick}
NEG = {"qat": "qat-head", "qef": "qef-tail", "free": "free-noadvance", "cancel": "cancel-kindonly",
       "run": "run-nextafter", "tick": "tick-playersfirst"}


def call_lines(c):
    op = c["op"]
    m = c["m"]
    if op[0] == "qat":
        _, kind, u, frame, cb, a, b = op
        if c["direct"]:
            return ["r eax %s" % hx(frame), "call 005416b0 %s %s %s %s %s %s" % (hx(kind), hx(GAME), hx(u), hx(cb),
                                                                              hx(a), hx(b))]
        return ["call 005417d0 %s %s %s %s %s %s" % (hx(GAME), hx(u), hx(kind), hx(frame), hx(a), hx(b))]
    if op[0] == "qef":
        _, kind, u, cb, a, b = op
        if c["direct"]:
            return ["r eax %s" % hx(u), "r ebx %s" % hx(kind), "r edi %s" % hx(GAME),
                    "call 005415e0 0 0 %s %s %s" % (hx(cb), hx(a), hx(b))]
        return ["call 00541650 %s %s %s %s %s" % (hx(GAME), hx(u), hx(kind), hx(a), hx(b))]
    if op[0] == "free":
        return ["r esi %s" % hx(op[1]), "r edi %s" % hx(GAME), "call 00540cd0 0 0"]
    if op[0] in ("cancel", "cancelcb", "freeall", "freeall2"):
        which, u, kind, a = op
        fn = {"cancel": "00540e60", "cancelcb": "00540ea0", "freeall": "00540ee0", "freeall2": "00540f30"}[which]
        if which in ("freeall", "freeall2"):
            return ["call %s %s %s" % (fn, hx(GAME), hx(u))]
        return ["call %s %s %s %s %s" % (fn, hx(GAME), hx(u), hx(kind), hx(a))]
    if op[0] == "run":
        _, lst, mode, head = op
        return ["r eax %s" % hx(head), "r ebx %s" % hx(CTL), "call %08x %s 0 %s" % (RUNNERS[lst], hx(GAME), hx(mode))]
    if op[0] == "tick":
        return ["call 005414d0 %s 0" % hx(GAME)]
    raise ValueError(op)


def apply_model(c, neg=None):
    """(state after, observed boundary or None, expected pop)."""
    m = c["m"].copy()
    md = Model(m, neg)
    op = c["op"]
    pop = None
    if op[0] == "qat":
        _, kind, u, frame, cb, a, b = op
        md.queue_at(kind, u, frame, cb, a, b)
        pop = 16
    elif op[0] == "qef":
        _, kind, u, cb, a, b = op
        md.queue_ef(kind, u, cb, a, b)
        pop = 12
    elif op[0] == "free":
        md.free(op[1])
        pop = 0
    elif op[0] in ("cancel", "cancelcb"):
        md.cancel(op[1], op[2], op[3], by_cb=op[0] == "cancelcb")
        pop = 8
    elif op[0] in ("freeall", "freeall2"):
        md.free_all(op[1])
        pop = 0
    elif op[0] == "run":
        md.run(op[1], op[2], op[3])
        pop = 4
    elif op[0] == "tick":
        md.tick()
        pop = 0
    return m, md.obs, pop


def cmd_cases(d, tag):
    os.makedirs(d, exist_ok=True)
    for fam in FAMILIES:
        rnd = random.Random("%s-%s" % (tag, fam))
        cases = GEN[fam](rnd)
        with open(os.path.join(d, fam + ".cases"), "w") as f:
            for c in cases:
                f.write("\n".join(emit_state(c["m"]) + dumps() + call_lines(c)) + "\n")
        spec = mem_spec()
        if fam in ("qat", "run", "tick"):
            spec += ["observe %08x" % HASSTATE] + ["observe %08x" % a for a in DISPATCH.values()]
        with open(os.path.join(d, fam + ".mem"), "w") as f:
            f.write("\n".join(spec) + "\n")
        print("CASES %s %d" % (fam, len(cases)))


# ------------------------------------------------------------------------------------------------- the check
def read_out(path):
    calls, traced = [], []
    for ln in open(path):
        p = ln.split()
        if not p:
            continue
        if p[0] == "C":
            c = {"n": int(p[1]), "dumps": {}}
            if p[3] == "STOP":
                c["stop"] = " ".join(p[4:])
            elif p[3] == "OBS":
                c["obs_pc"] = int(p[4], 16)
                c["regs"] = dict(x.split("=") for x in p[6:])
            else:
                kv = dict(x.split("=") for x in p[3:])
                c["pop"] = int(kv["pop"])
            calls.append(c)
        elif p[0] == "A":
            calls[-1]["stack"] = bytes.fromhex(p[1])
        elif p[0] == "D":
            calls[-1]["dumps"][int(p[1], 16)] = bytes.fromhex(p[2]) if len(p) > 2 else b""
        elif p[0] in ("R", "W"):
            traced.append(ln.strip())
    return calls, traced


def compare(c, out, neg=None):
    m, obs, pop = apply_model(c, neg)
    if "stop" in out:
        return False, "STOP " + out["stop"]
    if obs:
        pc, regs, args = obs
        if out.get("obs_pc") != pc:
            return False, "boundary %s != %08x" % (out.get("obs_pc"), pc)
        st = out["stack"]
        got = list(struct.unpack_from("<%dI" % len(args), st, 4))
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
    for a, n in REGIONS:
        if out["dumps"].get(a) != m.region(a, n):
            got, want = out["dumps"].get(a) or b"", m.region(a, n)
            k = next((i for i in range(min(len(got), len(want))) if got[i] != want[i]), None)
            return False, "region %08x differs at +0x%x" % (a, k if k is not None else -1)
    return True, ""


def check_family(fam, d, tag):
    rnd = random.Random("%s-%s" % (tag, fam))
    cases = GEN[fam](rnd)
    outs, traced = read_out(os.path.join(d, fam + ".out"))
    bad, match, nsep, nnegpass, nobs = [], 0, 0, 0, 0
    if len(outs) != len(cases):
        bad.append("case count %d != %d" % (len(outs), len(cases)))
    for c, o in zip(cases, outs):
        ok, why = compare(c, o)
        match += ok
        nobs += "obs_pc" in o
        if not ok:
            bad.append("case %d: %s %r" % (o["n"], why, c["op"][:2]))
        mw, ow, _ = apply_model(c)
        mn, on, _ = apply_model(c, NEG[fam])
        sep = any(mw.region(a, n) != mn.region(a, n) for a, n in REGIONS) or ow != on
        nsep += sep
        if sep:
            nok, _ = compare(c, o, NEG[fam])
            nnegpass += nok
    line = ("FR55B %s cases=%d match=%d bad=%d boundary=%d traced=%d neg=%s neg_separating=%d neg_passed=%d"
            % (fam, len(cases), match, len(bad), nobs, len(traced), NEG[fam], nsep, nnegpass))
    return line, bad[:20], traced[:20]


def family_counts(fam, tag):
    """What the cases exercise, for the record."""
    rnd = random.Random("%s-%s" % (tag, fam))
    cases = GEN[fam](rnd)
    cnt = {}

    def inc(k):
        cnt[k] = cnt.get(k, 0) + 1
    for c in cases:
        op = c["op"]
        m = c["m"]
        if fam == "qat":
            _, kind, u, frame, cb, a, b = op
            cur = s32(m.r32(GAME + 0xA8))
            if s32(kind) >= 15:
                inc("rejected")
            elif frame == M32:
                inc("every-frame")
            elif s32(frame) <= cur:
                inc("raised")
            elif m.r32(u) == 1 and kind == 2:
                inc("boundary")
            else:
                inc("kept")
            if s32(kind) < 0:
                inc("negative-kind")
            if frame == M32 and c["direct"] and cb and s32(kind) < 15:
                inc("every-frame-callback-dropped")
            mw, _, _ = apply_model(c)
            mn, _, _ = apply_model(c, NEG[fam])
            if any(mw.region(a2, n2) != mn.region(a2, n2) for a2, n2 in REGIONS):
                inc("slot-nonempty")
            if m.r32(POOL + 0x7080) == 0:
                inc("second-block")
        elif fam == "free":
            rec = op[1]
            if m.r16(rec + 2) & 1:
                inc("running")
            else:
                inc("ef" if m.r32(rec + 4) == M32 else "slot")
                if m.r32(CTL + 0xA18) == rec:
                    inc("advance")
                if m.r32(rec + 0x20) == 0:
                    inc("at-head")
                if m.r32(rec + 0x1C) == 0:
                    inc("at-tail")
                if m.r32(rec + 8) == 0:
                    inc("no-unit")
        elif fam == "cancel":
            inc(op[0])
        elif fam == "run":
            inc("list%d-mode%d" % (op[1], op[2]))
            if op[2] == 1:
                x = op[3]
                while x:
                    if s32(m.r32(x + 4)) != s32(m.r32(GAME + 0xA8)):
                        inc("slot-record-not-due")
                    x = m.r32(x + 0x1C)
            _, obs, _ = apply_model(c)
            if obs:
                inc("boundary")
        elif fam == "tick":
            _, obs, _ = apply_model(c)
            inc("boundary" if obs else "complete")
        elif fam == "qef":
            inc("rejected" if s32(op[1]) >= 15 else "kept")
    return "FR55B %s counts %s" % (fam, " ".join("%s=%d" % (k, cnt[k]) for k in sorted(cnt)))


def cmd_check(d, tag):
    allok = True
    for fam in FAMILIES:
        p = os.path.join(d, fam + ".out")
        if not os.path.exists(p):
            print("FR55B %s missing" % fam)
            allok = False
            continue
        line, bad, traced = check_family(fam, d, tag)
        print(line)
        for b in bad:
            print("  BAD", b)
        for t in traced:
            print("  TRACED", t)
        if bad or traced:
            allok = False
        print(family_counts(fam, tag))
    print("FR55B result=%s" % ("ok" if allok else "FAIL"))


def cmd_manifest(d, write):
    rows = []
    for fam in FAMILIES:
        for ext in ("cases", "mem", "out"):
            p = os.path.join(d, "%s.%s" % (fam, ext))
            if os.path.exists(p):
                rows.append("%s  %s" % (hashlib.sha256(open(p, "rb").read()).hexdigest(), os.path.basename(p)))
    p = os.path.join(d, "check.txt")
    if os.path.exists(p):
        rows.append("%s  %s" % (hashlib.sha256(open(p, "rb").read()).hexdigest(), "check.txt"))
    text = "\n".join(rows) + "\n"
    if write:
        with open(os.path.join(d, "manifest.sha256"), "w") as f:
            f.write(text)
    sys.stdout.write(text)


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["cases", "check", "manifest"])
    ap.add_argument("--dir", default=DEFAULT_DIR)
    ap.add_argument("--tag", default="r55b")
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args(argv)
    if a.cmd == "cases":
        cmd_cases(a.dir, a.tag)
    elif a.cmd == "check":
        cmd_check(a.dir, a.tag)
    else:
        cmd_manifest(a.dir, a.write)


if __name__ == "__main__":
    main(sys.argv[1:])
