#!/usr/bin/env python3
"""Plan 0055 phase 1.3 (the server frame: the timers and the room activation order, `lane/r55c`): a byte-level survey
of the quest timer registrations and the emulated families of frame/0003. No game run; stdlib and `objdump`.

    python3 -I tools/frame_timers.py adds              every direct call of QUESTS_TimerAdd (0x00543F10): the callback
                                                       (the `mov edx, imm32` nearest before the call) and the period
                                                       (the push nearest before it), with the calling function
    python3 -I tools/frame_timers.py cases [DIR]       write the emulation cases and memory specs (seeded, one
                                                       `random.Random("r55c-<family>")` per family) into DIR
    python3 -I tools/frame_timers.py check [DIR]       compare each family's EmuBoundary output in DIR with the model
                                                       below (at an observed boundary: the boundary, its arguments and
                                                       the call site, by the return address of the `A` line; ADR-0021),
                                                       and score each negative control (a wrong reading run on the same
                                                       cases: the cases it separates, and how many it passes)
    python3 -I tools/frame_timers.py cbscan            the stand-in functions of the timers family (see below)
    python3 -I tools/frame_timers.py manifest [DIR] [--write]   sha256 lines of DIR's kept files (one path base: DIR)

DIR defaults to workspace/logs/r55c/emu. The families (frame/0003 § 8, run:2026-10-30-frame-emu-3):

  timers  QUESTS_TimersRun (0x00543E10, ECX game): tick + 1; at tick 0xFFFFFFFF every due becomes -1 - due; the list
          from its head, next read before the callback; a timer runs when due < tick (unsigned); its callback (ECX game,
          EDX quest) returning AL = 1 unlinks it (the list head or the previous timer's next) and frees it (an observed
          boundary at the free, 0x0040B480: the case ends there, after the unlink); AL != 1 re-arms due = tick + period;
          the running word +4 is 1 during the walk and 0 after. The callbacks are game functions that return a constant
          AL (0x00407DD0 `xor al, al; ret`, 0x004BDAF0 `mov al, 1; ret`: found by `cbscan`), and IsBadCodePtr's import
          slot (0x006CC34C) is given a game function that returns EAX = 0 and pops one argument (0x004BAD70) as a const:
          the stand-in for the OS call, stated in the record.
  deact   RoomsDeactivate (0x0052D240, ECX game): acts 0..4 (Game+0xBC), rooms from the act's head (+0x10), next (+0x7C)
          read before the room's tests; RoomIdleCount (+0x0C := 0 when +0x78 != 0, else +0x0C + 1); a count above 10
          reaches RoomReleaseAllowed (0x0061A3F0, observed: the case ends there).
  sweep   0x0052D310 (EDI game): frame % 1500 (signed) = 0 runs, for act index 0..4, 0x00558B90 (rooms of act a, their
          units +0x74 / next +0xE8: an item, type 4, whose item data +0x24 is non-zero and <= frame (signed) reaches
          UnitGetRoom 0x00620BB0, observed) and 0x00542AC0 (Game+0xD8 + 4a: the act's inactive-record lists, next +0x14;
          each list's item records from +0x08, next +0x00; a record whose expiry +0x04 is non-zero and below the frame
          (signed) is unlinked and freed: observed at 0x0040B480).
  k6      the kind-6 event of a player (0x00580B70) and of a monster (0x005A7F00), ECX game, EDX unit: no record at
          Unit+0xA4, nothing; a record whose frame +0x04 is <= Game+0xA8 (unsigned) reaches the chat free 0x006611A0
          (observed: its two stack arguments, game +0x1C and the record); otherwise UnitQueueEvent (0x005417D0, observed) with kind 6 at the
          record's frame, a = b = 0.
  nru     NewRoomsUpdate (0x0052D160, EDI game): acts 0..4 whose +0x54 is non-zero; the walk from the head reaches
          RoomWandererTick (0x0054F060, observed: ECX game, EDX the first room); an act with the flag and no room has
          +0x54 cleared and the walk goes on to the next act.
"""
import hashlib
import os
import random
import re
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import frame_events as fe  # noqa: E402

ROOT = os.path.dirname(HERE)
DEFDIR = os.path.join(ROOT, "workspace", "logs", "r55c", "emu")
TIMER_ADD = 0x00543F10
FAMILIES = ("timers", "deact", "sweep", "k6", "nru")

# guards (allocator and fatal entries), as in run:2026-10-30-frame-emu-2
GUARDS = (0x00408090, 0x00408A60, 0x00681E09, 0x0040B4B0, 0x0040B430)
FREE = 0x0040B480
CB_AL0, CB_AL1, BADCODE0 = 0x00407DD0, 0x004BDAF0, 0x004BAD70
IAT_BADCODE = 0x006CC34C

GAME = 0x10000000          # 0x2000 bytes: the game
CTL = 0x10100000           # the quest control (0x18 bytes)
TMR = 0x10110000           # timer records, 0x20 apart (0x14 used)
ACTS = 0x10200000          # five acts, 0x100 apart (0x80 used)
ROOMS = 0x10300000         # rooms, 0x100 apart (0x80 used)
UNITS = 0x10400000         # units, 0x200 apart (0x100 used)
IDATA = 0x10500000         # item data, 0x40 apart
RECL = 0x10600000          # inactive-record lists, 0x20 apart
RECS = 0x10700000          # item records, 0x10 apart
CHAT = 0x10800000          # chat records, 0x20 apart


# ---------------------------------------------------------------------------------------------------------------- adds

def cmd_adds():
    ins = fe.objdump_text()
    syms = fe.symbols()
    funcs = sorted(a for a, v in syms.items() if v[1] == "func")
    import bisect
    n = 0
    for i, (va, mn, op) in enumerate(ins):
        if mn != "call" or not re.match(r"^0x[0-9a-f]+(\s|$)", op) or int(op.split()[0], 16) != TIMER_ADD:
            continue
        cb = per = None
        for j in range(i - 1, max(-1, i - 16), -1):
            v2, m2, o2 = ins[j]
            if m2.startswith("j") or m2 in ("call", "ret", "int3"):
                break
            if cb is None and m2 == "mov" and o2.startswith("edx,0x"):
                cb = int(o2.split(",")[1], 16)
            if per is None and m2 == "push":
                per = o2
        k = bisect.bisect_right(funcs, va) - 1
        fn = syms[funcs[k]][0] if k >= 0 else "?"
        cbn = syms.get(cb, ("unnamed",))[0] if cb is not None else "-"
        print("ADD site=0x%08X fn=%s cb=%s(%s) period=%s" % (va, fn, "0x%08X" % cb if cb else "reg", cbn, per))
        n += 1
    print("ADD total=%d" % n)


# ---------------------------------------------------------------------------------------------------------- emulation

def le(v):
    return struct.pack("<I", v & 0xFFFFFFFF).hex()


class Case:
    def __init__(self, tag):
        self.w, self.d, self.s, self.r, self.call, self.tag = [], [], [], [], None, tag

    def dw(self, a, v):
        self.w.append((a, le(v)))

    def lines(self):
        out = ["# %s" % self.tag]
        out += ["w %08x %s" % x for x in self.w]
        out += ["s %08x %d" % x for x in self.s]
        out += ["r %s %08x" % x for x in self.r]
        out += ["d %08x %d" % x for x in self.d]
        out.append(self.call)
        return out


def spec_lines(observes, extra=()):
    out = ["# r55c memory spec: zeroed regions, guards, observed boundaries"]
    for base, size in ((GAME, 0x2000), (CTL, 0x100), (TMR, 0x400), (ACTS, 0x500), (ROOMS, 0x1800), (UNITS, 0x2000),
                       (IDATA, 0x800), (RECL, 0x200), (RECS, 0x800), (CHAT, 0x200)):
        # 0x800 bytes per directive: in dev1 and dev2 a directive of 0x1000 bytes or more was not applied before
        # each case (the previous case's writes stayed); 0x200..0xFFF bytes were (scratch tests)
        for o in range(0, size, 0x800):
            out.append("bytes %08x %s" % (base + o, "00" * min(0x800, size - o)))
    out += list(extra)
    out += ["guard %08x" % g for g in GUARDS]
    out += ["observe %08x" % o for o in observes]
    return out


# timers ------------------------------------------------------------------------------------------------------------

def timers_cases(rng):
    cases = []
    for n in range(300):
        c = Case("timers %d" % n)
        k = rng.choice([0, 1, 2, 3, 4, 5, 6])
        if n < 40:
            tick = 0xFFFFFFFE          # the wrap: tick becomes 0xFFFFFFFF
        elif n < 60:
            tick = rng.choice([0x7FFFFFFF, 0x80000000, 0xFFFFFFF0])
        else:
            tick = rng.randrange(0, 5000)
        newtick = (tick + 1) & 0xFFFFFFFF
        ts = []
        for i in range(k):
            r = rng.random()
            if r < 0.3:
                due = (newtick + rng.randrange(0, 4)) & 0xFFFFFFFF   # not due (due >= tick)
            elif r < 0.4:
                due = (newtick - 1) & 0xFFFFFFFF                    # boundary: due = tick - 1 runs
            elif r < 0.5 and n >= 40:
                due = rng.choice([0x80000000, 0xFFFFFFF0, 0x7FFFFFFF])  # unsigned compare separators
            else:
                due = (newtick - rng.randrange(1, 300)) & 0xFFFFFFFF
            ret1 = rng.random() < (0.15 if n >= 60 else 0.5 if (n < 40 and i == 0) else 0.0)
            ts.append(dict(due=due, per=rng.randrange(1, 40), quest=0x11000000 + 0x100 * i, ret1=ret1))
        c.dw(GAME + 0x10F4, CTL)
        c.dw(GAME + 0x1C, 0)
        c.dw(CTL + 0x14, tick)
        c.dw(CTL + 0x04, 0)
        c.dw(CTL + 0x10, TMR if ts else 0)
        for i, t in enumerate(ts):
            a = TMR + 0x20 * i
            c.dw(a, CB_AL1 if t["ret1"] else CB_AL0)
            c.dw(a + 4, t["quest"])
            c.dw(a + 8, t["due"])
            c.dw(a + 12, t["per"])
            c.dw(a + 16, TMR + 0x20 * (i + 1) if i + 1 < len(ts) else 0)
        c.d.append((CTL, 0x18))
        c.d.append((TMR, 0x20 * max(1, len(ts))))
        c.call = "call 00543e10 %08x 00000000" % GAME
        c.model = dict(tick=tick, ts=ts)
        cases.append(c)
    return cases


def timers_model(m, variant=None):
    """Return ('ret', ctl, timers) or ('obs', freed_addr, ctl, timers) after the run (dumps as dicts)."""
    tick = (m["tick"] + 1) & 0xFFFFFFFF
    ts = [dict(t, addr=TMR + 0x20 * i, nxt=(TMR + 0x20 * (i + 1) if i + 1 < len(m["ts"]) else 0))
          for i, t in enumerate(m["ts"])]
    if tick == 0xFFFFFFFF and variant != "nowrap":
        for t in ts:
            t["due"] = (-1 - t["due"]) & 0xFFFFFFFF
    head = ts[0]["addr"] if ts else 0
    order = ts if variant != "tailfirst" else list(reversed(ts))
    prev = None
    for t in order:
        if variant == "signed":
            due_ok = struct.unpack("<i", struct.pack("<I", t["due"]))[0] < struct.unpack("<i", struct.pack("<I", tick))[0]
        elif variant == "le":
            due_ok = t["due"] <= tick
        else:
            due_ok = t["due"] < tick
        if due_ok:
            if t["ret1"]:
                if variant == "nounlink":
                    pass
                elif prev is None:
                    head = t["nxt"]
                else:
                    prev["nxt"] = t["nxt"]
                return ("obs", t["addr"], dict(tick=tick, running=1, head=head), ts)
            t["due"] = (t["per"] + tick) & 0xFFFFFFFF if variant != "rearm-due" else (t["due"] + t["per"]) & 0xFFFFFFFF
        prev = t
    return ("ret", None, dict(tick=tick, running=0, head=head), ts)


def _first_removed_prev_none(m, variant=None):
    """The address of the timer the walk frees when it is the list's head at that point (the free at 0x00543EA9,
    returning to 0x00543EAE), else None (the free at 0x00543EC2 after a previous timer, returning to 0x00543EC7)."""
    tick = (m["tick"] + 1) & 0xFFFFFFFF
    dues = [t["due"] for t in m["ts"]]
    if tick == 0xFFFFFFFF and variant != "nowrap":
        dues = [(-1 - d) & 0xFFFFFFFF for d in dues]
    for i, t in enumerate(m["ts"]):
        if dues[i] < tick and t["ret1"]:
            return TMR + 0x20 * i if i == 0 else None
    return None


def timers_expect(m, variant=None):
    kind, freed, ctl, ts = timers_model(m, variant)
    ctlb = bytearray(0x18)
    struct.pack_into("<I", ctlb, 4, ctl["running"])
    struct.pack_into("<I", ctlb, 0x10, ctl["head"])
    struct.pack_into("<I", ctlb, 0x14, ctl["tick"])
    tb = bytearray(0x20 * max(1, len(ts)))
    for i, t in enumerate(ts):
        struct.pack_into("<5I", tb, 0x20 * i, CB_AL1 if t["ret1"] else CB_AL0, t["quest"], t["due"], t["per"], t["nxt"])
    return kind, freed, [ctlb.hex(), tb.hex()]


# deact -------------------------------------------------------------------------------------------------------------

def deact_cases(rng):
    cases = []
    for n in range(300):
        c = Case("deact %d" % n)
        c.dw(GAME + 0x1C, 0)
        acts, ri = [], 0
        for a in range(5):
            if rng.random() < 0.25:
                acts.append(None)
                continue
            rooms = []
            for _ in range(rng.randrange(0, 5)):
                if ri >= 24:
                    break
                hot = n >= 150 and rng.random() < 0.12
                idle = rng.choice([10, 11, 50]) if hot else rng.randrange(0, 10)
                if n < 30 and rng.random() < 0.3:
                    idle = 10                               # 10 -> 11: the boundary
                rooms.append(dict(addr=ROOMS + 0x100 * ri, idle=idle, clients=rng.choice([0, 0, 1, 2])))
                ri += 1
            acts.append(rooms)
        for a, rooms in enumerate(acts):
            if rooms is None:
                continue
            aa = ACTS + 0x100 * a
            c.dw(GAME + 0xBC + 4 * a, aa)
            c.dw(aa + 0x10, rooms[0]["addr"] if rooms else 0)
            for i, r in enumerate(rooms):
                c.dw(r["addr"] + 0x0C, r["idle"])
                c.dw(r["addr"] + 0x78, r["clients"])
                c.dw(r["addr"] + 0x7C, rooms[i + 1]["addr"] if i + 1 < len(rooms) else 0)
                c.dw(r["addr"] + 0x74, 0)
        c.d.append((ROOMS, 0x100 * max(1, ri)))
        c.call = "call 0052d240 %08x 00000000 %08x" % (GAME, GAME)
        c.model = dict(acts=acts, nrooms=ri)
        cases.append(c)
    return cases


def deact_model(m, variant=None):
    rooms_out = {}
    for rooms in m["acts"]:
        for r in rooms or []:
            rooms_out[r["addr"]] = dict(r)
    obs = None
    order = list(enumerate(m["acts"]))
    if variant == "acts-reverse":
        order = list(reversed(order))
    for a, rooms in order:
        if rooms is None:
            continue
        for r in rooms:
            o = rooms_out[r["addr"]]
            if o["clients"] != 0 and variant != "noreset":
                o["idle"] = 0
            else:
                o["idle"] = (o["idle"] + 1) & 0xFFFFFFFF
            thr = 9 if variant == "ge10" else 10
            if o["idle"] > thr:
                obs = (ACTS + 0x100 * a, r["addr"])
                break
        if obs:
            break
    return obs, rooms_out


def deact_expect(m, variant=None):
    obs, rooms = deact_model(m, variant)
    b = bytearray(0x100 * max(1, m["nrooms"]))
    for addr, r in rooms.items():
        o = addr - ROOMS
        struct.pack_into("<I", b, o + 0x0C, r["idle"])
        struct.pack_into("<I", b, o + 0x78, r["clients"])
        nxt = 0
        for rs in m["acts"]:
            for i, x in enumerate(rs or []):
                if x["addr"] == addr and i + 1 < len(rs):
                    nxt = rs[i + 1]["addr"]
        struct.pack_into("<I", b, o + 0x7C, nxt)
    return ("obs", obs) if obs else ("ret", None), [b.hex()]


# sweep -------------------------------------------------------------------------------------------------------------

def sweep_cases(rng):
    cases = []
    for n in range(300):
        c = Case("sweep %d" % n)
        k = rng.randrange(1, 40)
        if n < 200 or rng.random() < 0.3:
            frame = 1500 * k
        elif rng.random() < 0.5:
            frame = 1500 * k + 20 * rng.randrange(1, 75)        # a multiple of 20, not of 1500
        else:
            frame = 1500 * k + rng.randrange(1, 1500)
        c.dw(GAME + 0xA8, frame)
        c.dw(GAME + 0x1C, 0)
        acts, units, recl, recs = [], 0, 0, 0
        for a in range(5):
            act = dict(present=rng.random() < 0.7, rooms=[], lists=[])
            if act["present"]:
                for _ in range(rng.randrange(0, 3)):
                    us = []
                    for _ in range(rng.randrange(0, 4)):
                        if units >= 16:
                            break
                        typ = rng.choice([1, 2, 4, 4, 4])
                        exp = 0
                        if typ == 4:
                            r = rng.random()
                            exp = (0 if r < 0.3 else frame + rng.randrange(1, 2000) if r < 0.6 else
                                   frame if r < 0.75 else frame - rng.randrange(1, 2000))
                            if n < 150 and exp != 0 and exp <= frame:
                                exp = frame + 1      # the first 150 cases keep every item unexpired
                        us.append(dict(addr=UNITS + 0x200 * units, typ=typ, exp=exp, idata=IDATA + 0x40 * units))
                        units += 1
                    act["rooms"].append(us)
            for _ in range(rng.randrange(0, 3)):
                if recl >= 12:
                    break
                rl = dict(addr=RECL + 0x20 * recl, recs=[])
                recl += 1
                for _ in range(rng.randrange(0, 4)):
                    if recs >= 64:
                        break
                    r = rng.random()
                    e = (0 if r < 0.25 else frame + rng.randrange(0, 3000) if r < 0.7 else
                         frame if r < 0.8 else frame - rng.randrange(1, 3000))
                    if n < 100 and e != 0 and e < frame:
                        e = frame                     # the first 100 cases keep every record
                    rl["recs"].append(dict(addr=RECS + 0x10 * recs, exp=e))
                    recs += 1
                act["lists"].append(rl)
            acts.append(act)
        rooms_used = 0
        for a, act in enumerate(acts):
            if act["present"]:
                aa = ACTS + 0x100 * a
                c.dw(GAME + 0xBC + 4 * a, aa)
                ras = []
                for us in act["rooms"]:
                    ras.append(ROOMS + 0x100 * rooms_used)
                    rooms_used += 1
                c.dw(aa + 0x10, ras[0] if ras else 0)
                for i, us in enumerate(act["rooms"]):
                    ra = ras[i]
                    c.dw(ra + 0x7C, ras[i + 1] if i + 1 < len(ras) else 0)
                    c.dw(ra + 0x74, us[0]["addr"] if us else 0)
                    for j, u in enumerate(us):
                        c.dw(u["addr"], u["typ"])
                        c.dw(u["addr"] + 0x14, u["idata"])
                        c.dw(u["idata"] + 0x24, u["exp"])
                        c.dw(u["addr"] + 0xE8, us[j + 1]["addr"] if j + 1 < len(us) else 0)
            c.dw(GAME + 0xD8 + 4 * a, act["lists"][0]["addr"] if act["lists"] else 0)
            for i, rl in enumerate(act["lists"]):
                c.dw(rl["addr"] + 0x14, act["lists"][i + 1]["addr"] if i + 1 < len(act["lists"]) else 0)
                c.dw(rl["addr"] + 0x08, rl["recs"][0]["addr"] if rl["recs"] else 0)
                for j, r in enumerate(rl["recs"]):
                    c.dw(r["addr"], rl["recs"][j + 1]["addr"] if j + 1 < len(rl["recs"]) else 0)
                    c.dw(r["addr"] + 4, r["exp"])
        c.d.append((RECL, 0x20 * max(1, recl)))
        c.d.append((RECS, 0x10 * max(1, recs)))
        c.r.append(("edi", GAME))
        c.call = "call 0052d310 00000000 00000000"
        c.model = dict(frame=frame, acts=acts, recl=recl, recs=recs)
        cases.append(c)
    return cases


def sweep_model(m, variant=None):
    frame = m["frame"]
    lists = [[dict(addr=rl["addr"], recs=[dict(r) for r in rl["recs"]]) for rl in act["lists"]] for act in m["acts"]]
    if (frame % (20 if variant == "every20" else 1500)) != 0:
        return ("ret", None), lists
    order = list(range(5)) if variant != "acts-reverse" else list(range(4, -1, -1))
    for a in order:
        act = m["acts"][a]
        if act["present"] and variant != "recs-first":
            for us in act["rooms"]:
                for u in us:
                    e = u["exp"]
                    hit = (e != 0 and e < frame) if variant == "item-lt" else (e != 0 and e <= frame)
                    if u["typ"] == 4 and hit:
                        return ("obs", ("unit", u["addr"])), lists
        for rl in lists[a]:
            for i, r in enumerate(rl["recs"]):
                e = r["exp"]
                hit = (e != 0 and e <= frame) if variant == "rec-le" else (e != 0 and e < frame)
                if hit:
                    del rl["recs"][i]
                    return ("obs", ("rec", r["addr"], rl["addr"], i)), lists
        if act["present"] and variant == "recs-first":
            for us in act["rooms"]:
                for u in us:
                    e = u["exp"]
                    if u["typ"] == 4 and e != 0 and e <= frame:
                        return ("obs", ("unit", u["addr"])), lists
    return ("ret", None), lists


def sweep_expect(m, variant=None):
    res, lists = sweep_model(m, variant)
    lb = bytearray(0x20 * max(1, m["recl"]))
    rb = bytearray(0x10 * max(1, m["recs"]))
    orig = {}
    for act in m["acts"]:
        for rl in act["lists"]:
            for j, r in enumerate(rl["recs"]):
                orig[r["addr"]] = (rl["recs"][j + 1]["addr"] if j + 1 < len(rl["recs"]) else 0, r["exp"])
    for a, act in enumerate(m["acts"]):
        for i, rl in enumerate(act["lists"]):
            o = rl["addr"] - RECL
            struct.pack_into("<I", lb, o + 0x14, act["lists"][i + 1]["addr"] if i + 1 < len(act["lists"]) else 0)
            new = lists[a][i]["recs"]
            struct.pack_into("<I", lb, o + 0x08, new[0]["addr"] if new else 0)
            for r in rl["recs"]:
                nx, e = orig[r["addr"]]
                struct.pack_into("<II", rb, r["addr"] - RECS, nx, e & 0xFFFFFFFF)
            for j, r in enumerate(new):
                if j > 0:
                    pass
            # the unlink writes the previous record's next (or the list head) only
            if res[0] == "obs" and res[1][0] == "rec" and res[1][2] == rl["addr"]:
                idx = res[1][3]
                if idx > 0:
                    prev = rl["recs"][idx - 1]["addr"]
                    struct.pack_into("<I", rb, prev - RECS, orig[res[1][1]][0])
    return res, [lb.hex(), rb.hex()]


# k6 ----------------------------------------------------------------------------------------------------------------

def k6_cases(rng):
    cases = []
    for n in range(200):
        c = Case("k6 %d" % n)
        fn = 0x00580B70 if n % 2 == 0 else 0x005A7F00
        frame = rng.randrange(1, 200000)
        r = rng.random()
        if r < 0.1:
            rec = 0
            exp = 0
        else:
            rec = CHAT
            r2 = rng.random()
            exp = (frame if r2 < 0.15 else frame + 1 if r2 < 0.3 else frame - rng.randrange(1, 500) if r2 < 0.6 else
                   frame + rng.randrange(2, 3000) if r2 < 0.85 else rng.choice([0x80000000, 0xFFFFFF00]))
        pool = 0x12340000 + n
        c.dw(GAME + 0xA8, frame)
        c.dw(GAME + 0x1C, pool)
        unit = UNITS
        c.dw(unit, 0 if fn == 0x00580B70 else 1)
        c.dw(unit + 0xA4, rec)
        if rec:
            c.dw(CHAT + 4, exp)
        c.d.append((unit + 0xA4, 4))
        c.call = "call %08x %08x %08x 0 0" % (fn, GAME, unit)
        c.model = dict(fn=fn, frame=frame, rec=rec, exp=exp, pool=pool, unit=unit)
        cases.append(c)
    return cases


def k6_model(m, variant=None):
    if not m["rec"]:
        return ("ret", None)
    if variant == "signed":
        due = struct.unpack("<i", le_b(m["exp"]))[0] <= struct.unpack("<i", le_b(m["frame"]))[0]
    elif variant == "lt":
        due = m["exp"] < m["frame"]
    else:
        due = m["exp"] <= m["frame"]
    if due:
        return ("obs", (0x006611A0, m["pool"], m["rec"]))
    return ("obs", (0x005417D0, 6, m["exp"], 0, 0))


def le_b(v):
    return struct.pack("<I", v & 0xFFFFFFFF)


# nru ---------------------------------------------------------------------------------------------------------------

def nru_cases(rng):
    cases = []
    for n in range(200):
        c = Case("nru %d" % n)
        acts, ri = [], 0
        for a in range(5):
            if rng.random() < 0.2:
                acts.append(None)
                continue
            flag = rng.random() < (0.25 if n < 100 else 0.5)
            k = rng.randrange(0, 3) if rng.random() < 0.6 else 0
            rooms = []
            for _ in range(k):
                rooms.append(ROOMS + 0x100 * ri)
                ri += 1
            acts.append(dict(flag=flag, rooms=rooms))
        for a, act in enumerate(acts):
            if act is None:
                continue
            aa = ACTS + 0x100 * a
            c.dw(GAME + 0xBC + 4 * a, aa)
            c.dw(aa + 0x54, 1 if act["flag"] else 0)
            c.dw(aa + 0x10, act["rooms"][0] if act["rooms"] else 0)
            for i, r in enumerate(act["rooms"]):
                c.dw(r + 0x7C, act["rooms"][i + 1] if i + 1 < len(act["rooms"]) else 0)
            c.d.append((aa + 0x54, 4))
        c.r.append(("edi", GAME))
        c.call = "call 0052d160 00000000 00000000"
        c.model = dict(acts=acts)
        cases.append(c)
    return cases


def nru_model(m, variant=None):
    flags = {a: (act["flag"] if act else None) for a, act in enumerate(m["acts"])}
    order = list(range(5)) if variant != "acts-reverse" else list(range(4, -1, -1))
    for a in order:
        act = m["acts"][a]
        if act is None or not act["flag"]:
            continue
        if act["rooms"]:
            room = act["rooms"][-1] if variant == "tail" else act["rooms"][0]
            return ("obs", room), flags
        if variant != "noclear":
            flags[a] = False
    return ("ret", None), flags


# ------------------------------------------------------------------------------------------------------------ writers

def family_cases(fam):
    rng = random.Random("r55c-" + fam)
    return {"timers": timers_cases, "deact": deact_cases, "sweep": sweep_cases, "k6": k6_cases,
            "nru": nru_cases}[fam](rng)


def family_spec(fam):
    if fam == "timers":
        return spec_lines([FREE], ["const dword %08x %08x" % (IAT_BADCODE, BADCODE0)])
    if fam == "deact":
        return spec_lines([0x0061A3F0, 0x005433F0, 0x0061A910])
    if fam == "sweep":
        return spec_lines([FREE, 0x00620BB0])
    if fam == "k6":
        return spec_lines([0x006611A0, 0x005417D0, 0x0064C040])
    if fam == "nru":
        return spec_lines([0x0054F060, 0x005559A0, 0x00542B40, 0x00552610, 0x0054EC90, 0x0061A4D0])
    raise SystemExit(fam)


def cmd_cases(d):
    os.makedirs(d, exist_ok=True)
    for fam in FAMILIES:
        with open(os.path.join(d, fam + ".cases"), "w") as f:
            for c in family_cases(fam):
                f.write("\n".join(c.lines()) + "\n")
        with open(os.path.join(d, fam + ".mem"), "w") as f:
            f.write("\n".join(family_spec(fam)) + "\n")
        print("CASES %s %d" % (fam, len(family_cases(fam))))


# ------------------------------------------------------------------------------------------------------------ checker

RX_C = re.compile(r"^C (\d+) ([0-9a-f]+) (.*)$")


def parse_out(path):
    res, cur = [], None
    traced = 0
    for ln in open(path):
        ln = ln.rstrip("\n")
        m = RX_C.match(ln)
        if m:
            rest = m.group(3)
            if rest.startswith("OBS"):
                p = rest.split()
                regs = dict(x.split("=") for x in p[2:] if "=" in x and not x.startswith("steps"))
                cur = dict(kind="obs", pc=int(p[1], 16), regs={k: int(v, 16) for k, v in regs.items()}, dumps=[])
            elif rest.startswith("STOP"):
                cur = dict(kind="stop", text=rest, dumps=[])
            else:
                cur = dict(kind="ret", text=rest, dumps=[])
            res.append(cur)
        elif ln.startswith("A ") and cur is not None:
            cur["stack"] = bytes.fromhex(ln[2:])
        elif ln.startswith("D ") and cur is not None:
            cur["dumps"].append(ln.split()[2])
        elif ln.startswith("R ") or ln.startswith("W "):
            traced += 1
    return res, traced


def ret_addr(o):
    """The return address at the observed boundary (ADR-0021: the call site is asserted with the boundary)."""
    return struct.unpack_from("<I", o.get("stack", b"\0" * 4), 0)[0]


def stack_args(o, n):
    st = o.get("stack", b"")
    return [struct.unpack_from("<I", st, 4 + 4 * i)[0] for i in range(n)]


def check_timers(cases, outs, variant=None):
    good, counts = 0, {}
    for c, o in zip(cases, outs):
        kind, freed, dumps = timers_expect(c.model, variant)
        ok = o["kind"] == kind and o["dumps"] == dumps
        if ok and kind == "obs":
            site = 0x00543EAE if freed == _first_removed_prev_none(c.model, variant) else 0x00543EC7
            ok = o["pc"] == FREE and o["regs"]["edx"] == freed and ret_addr(o) == site
        good += ok
        if variant is None:
            k = "removed" if kind == "obs" else "complete"
            counts[k] = counts.get(k, 0) + 1
            if c.model["tick"] == 0xFFFFFFFE and c.model["ts"]:
                counts["wrap"] = counts.get("wrap", 0) + 1
    return good, counts


def check_deact(cases, outs, variant=None):
    good, counts = 0, {}
    for c, o in zip(cases, outs):
        (kind, obs), dumps = deact_expect(c.model, variant)
        ok = o["kind"] == kind and o["dumps"] == dumps
        if ok and kind == "obs":
            ok = o["pc"] == 0x0061A3F0 and stack_args(o, 2) == [obs[0], obs[1]] and ret_addr(o) == 0x0052D289
        good += ok
        if variant is None:
            counts["released" if kind == "obs" else "complete"] = counts.get("released" if kind == "obs" else "complete", 0) + 1
    return good, counts


def check_sweep(cases, outs, variant=None):
    good, counts = 0, {}
    for c, o in zip(cases, outs):
        res, dumps = sweep_expect(c.model, variant)
        ok = o["kind"] == res[0] and o["dumps"] == dumps
        if ok and res[0] == "obs":
            if res[1][0] == "unit":
                ok = o["pc"] == 0x00620BB0 and stack_args(o, 1) == [res[1][1]] and ret_addr(o) == 0x00558BF2
            else:
                ok = o["pc"] == FREE and o["regs"]["edx"] == res[1][1] and ret_addr(o) == 0x00542B20
        good += ok
        if variant is None:
            k = "off-period" if c.model["frame"] % 1500 else (res[1][0] if res[0] == "obs" else "complete")
            counts[k] = counts.get(k, 0) + 1
    return good, counts


def check_k6(cases, outs, variant=None):
    good, counts = 0, {}
    for c, o in zip(cases, outs):
        exp = k6_model(c.model, variant)
        if exp[0] == "ret":
            ok = o["kind"] == "ret" and o["dumps"] == [le(c.model["rec"])]
            k = "none"
        elif exp[1][0] == 0x006611A0:
            ok = o["kind"] == "obs" and o["pc"] == 0x006611A0 and stack_args(o, 2) == [exp[1][1], exp[1][2]] and \
                ret_addr(o) == (0x00580B9D if c.model["fn"] == 0x00580B70 else 0x005A7F2D)
            k = "free"
        else:
            ok = o["kind"] == "obs" and o["pc"] == 0x005417D0 and stack_args(o, 4) == list(exp[1][1:]) and \
                o["regs"]["ecx"] == GAME and o["regs"]["edx"] == c.model["unit"] and \
                ret_addr(o) == (0x00580BCD if c.model["fn"] == 0x00580B70 else 0x005A7F5D)
            k = "requeue"
        good += ok
        if variant is None:
            k = ("player-" if c.model["fn"] == 0x00580B70 else "monster-") + k
            counts[k] = counts.get(k, 0) + 1
    return good, counts


def check_nru(cases, outs, variant=None):
    good, counts = 0, {}
    for c, o in zip(cases, outs):
        (kind, room), flags = nru_model(c.model, variant)
        dumps = [le(1 if flags[a] else 0) for a in range(5) if c.model["acts"][a] is not None]
        ok = o["kind"] == kind and o["dumps"] == dumps
        if ok and kind == "obs":
            ok = o["pc"] == 0x0054F060 and o["regs"]["edx"] == room and o["regs"]["ecx"] == GAME and \
                ret_addr(o) == 0x0052D1C9
        good += ok
        if variant is None:
            counts["walked" if kind == "obs" else "complete"] = counts.get("walked" if kind == "obs" else "complete", 0) + 1
    return good, counts


CHECKS = {"timers": (check_timers, ["tailfirst", "le", "signed", "nowrap", "rearm-due", "nounlink"]),
          "deact": (check_deact, ["ge10", "noreset", "acts-reverse"]),
          "sweep": (check_sweep, ["every20", "item-lt", "rec-le", "acts-reverse", "recs-first"]),
          "k6": (check_k6, ["lt", "signed"]),
          "nru": (check_nru, ["tail", "noclear", "acts-reverse"])}


def cmd_check(d):
    allok = True
    for fam in FAMILIES:
        cases = family_cases(fam)
        outs, traced = parse_out(os.path.join(d, fam + ".out"))
        fn, negs = CHECKS[fam]
        stops = sum(1 for o in outs if o["kind"] == "stop")
        if len(outs) != len(cases):
            print("FR55C %s cases=%d outs=%d result=bad" % (fam, len(cases), len(outs)))
            allok = False
            continue
        good, counts = fn(cases, outs)
        ok = good == len(cases) and stops == 0 and traced == 0
        allok &= ok
        print("FR55C %s cases=%d match=%d bad=%d stopped=%d traced=%d" % (fam, len(cases), good, len(cases) - good,
                                                                         stops, traced))
        print("FR55C %s counts %s" % (fam, " ".join("%s=%d" % kv for kv in sorted(counts.items()))))
        for v in negs:
            # a case separates the wrong reading when its prediction differs from the real one's
            sep = passed = 0
            for c, o in zip(cases, outs):
                g1, _ = fn([c], [o])
                g2, _ = fn([c], [o], v)
                if g1 != g2 or not _same(fam, c, v):
                    sep += 1
                    passed += g2
            print("FR55C %s neg=%s separating=%d passed=%d" % (fam, v, sep, passed))
            allok &= passed == 0 and sep > 0
    print("FR55C result=%s" % ("ok" if allok else "bad"))


def _same(fam, c, v):
    """True when the variant predicts exactly what the real reading predicts for this case."""
    m = c.model
    if fam == "timers":
        return timers_expect(m) == timers_expect(m, v)
    if fam == "deact":
        return deact_expect(m) == deact_expect(m, v)
    if fam == "sweep":
        return sweep_expect(m) == sweep_expect(m, v)
    if fam == "k6":
        return k6_model(m) == k6_model(m, v)
    if fam == "nru":
        return nru_model(m) == nru_model(m, v)
    return True


def cmd_manifest(d, write):
    names = sorted(f for f in os.listdir(d) if f.split(".")[-1] in ("cases", "mem", "out", "txt", "err")
                   and f != "manifest.sha256")
    lines = ["%s  %s" % (hashlib.sha256(open(os.path.join(d, f), "rb").read()).hexdigest(), f) for f in names]
    if write:
        with open(os.path.join(d, "manifest.sha256"), "w") as f:
            f.write("\n".join(lines) + "\n")
    print("\n".join(lines))


def cmd_cbscan():
    """Game functions whose whole body is `xor al, al; ret`, `mov al, 1; ret` or `xor eax, eax; ret 4`, each preceded
    by int3 padding or a ret (a function start): the stand-ins used by the timers family."""
    d, secs = fe.load_pe()
    pats = {"xor al,al; ret": bytes.fromhex("32c0c3"), "mov al,1; ret": bytes.fromhex("b001c3"),
            "xor eax,eax; ret 4": bytes.fromhex("33c0c20400")}
    for name, sva, vsize, rptr, rsize, flags in secs:
        if not flags & 0x20000000:
            continue
        body = d[rptr:rptr + min(vsize, rsize)]
        for pn, pb in pats.items():
            hits = []
            i = body.find(pb)
            while i >= 0:
                if i > 0 and body[i - 1] in (0xCC, 0xC3):
                    hits.append(sva + i)
                i = body.find(pb, i + 1)
            print("CB %s hits=%d first=%s" % (pn, len(hits), " ".join("0x%08X" % h for h in hits[:6])))


def main(argv):
    if not argv:
        sys.exit(__doc__)
    cmd = argv[0]
    d = argv[1] if len(argv) > 1 and not argv[1].startswith("--") else DEFDIR
    if cmd == "adds":
        cmd_adds()
    elif cmd == "cbscan":
        cmd_cbscan()
    elif cmd == "cases":
        cmd_cases(d)
    elif cmd == "check":
        cmd_check(d)
    elif cmd == "manifest":
        cmd_manifest(d, "--write" in argv)
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main(sys.argv[1:])
