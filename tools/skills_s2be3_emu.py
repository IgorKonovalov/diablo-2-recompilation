#!/usr/bin/env python3
"""Plan 0066 Phase 1, batch S2be part 3 (`lane/n66sb`): catalogue routes under Ghidra's p-code emulator (ADR-0015,
ADR-0021) with re/ghidra_scripts/EmuBoundary.java, on plan 0046's batch 8c machinery (tools/skills_catalogue_emu.py),
pointed at this part's families in its module state only (that file is unchanged).

    python3 -I tools/skills_s2be3_emu.py cases [FAMILY ...] [--dir D]
    GHIDRA_PROJ_DIR=... GHIDRA_HEADLESS_MAXMEM=3G tools/ghidra.sh emuboundary D/<family>.cases D/<family>.mem > D/<family>.out
    python3 -I tools/skills_s2be3_emu.py check [FAMILY ...] [--dir D]
    python3 -I tools/skills_s2be3_emu.py worked                        the worked example's two cases, as read back
    python3 -I tools/skills_s2be3_emu.py manifest [--write] [--dir D]

Default D: workspace/logs/n66sb/s2be/run3. Draws from random.Random("cat8c-<family>") (the catalogue's cmd_cases).

Families:
  tent140  do 140 0x005D2C20 (Baal Tentacle) alone, 1 200 cases: the first two are the catalogue's worked example
           (caster seed (1, 666), difficulty 2, MonStats base 0 so 0x0063EFA0's default arm, no target, base point
           (100, 200)): W1 a room holding (100, 199), try 1's point, so SpawnAtPos at 0x005D2E0C with the seed three
           steps on and n - i = 4 at EBP - 0x14; W2 one room far off with no near rooms, so no room in all four tries
           and return 1 with the seed nine steps on. The rest are batch 8c's do 140 world (move_8c's do 140 arm)
           with difficulty, seeds, target and rooms at random. Model: tent_model / move_8c_model unchanged; controls
           n_mod4 and xy_swap140 (move_8c's).                                                           c104
"""
import argparse
import hashlib
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import skills_catalogue_emu as C  # noqa: E402
import rng as RNG  # noqa: E402

DEFAULT_DIR = os.path.join(ROOT, "workspace", "logs", "n66sb", "s2be", "run3")
WORKED_SEED, WORKED_DIFF, WORKED_XY = (1, 666), 2, (100, 200)


def put_worked(c, row, game, room_hit):
    """Overwrite a generated do 140 case with the worked example's inputs (later `w` lines win)."""
    C.put_seeds_s(c, random.Random(0), row)            # writes both seed words; the caster's then pinned
    c.put(C.SEEDS_S[0], C.le32(WORKED_SEED[0]) + C.le32(WORKED_SEED[1]))
    row["seeds"][0] = WORKED_SEED
    c.put(game + 0x6C, bytes([0, WORKED_DIFF]))
    row["diff"] = WORKED_DIFF
    c.put(C.U + 0x04, C.le32(0))                       # class 0, MonStats row 0's base 0: the default arm
    c.put(C.MSREC + 0x02, C.le16(0))
    row["ucls"] = 0
    row["mb140"][0] = 0
    c.put(C.UP + 0x58, C.le32(0))                      # no path target: the caster's point is the base
    row.update(t=0, tlink=None)
    c.put(C.UP + 0x02, C.le16(WORKED_XY[0]))
    c.put(C.UP + 0x06, C.le16(WORKED_XY[1]))
    row.update(ux=WORKED_XY[0], uy=WORKED_XY[1])
    r0 = C.ROOMS[0]
    x0, y0, w, h = (90, 190, 20, 20) if room_hit else (5000, 5000, 10, 10)
    c.put(r0 + 0x4C, C.le32(x0) + C.le32(y0) + C.le32(w) + C.le32(h))
    c.put(r0 + 0x24, C.le32(0))
    rr = row["rooms"][str(r0)]
    rr[1:6] = [x0, y0, w, h, []]
    c.put(C.UP + 0x1C, C.le32(r0))
    row["uroom"] = r0
    row["worked"] = "W1" if room_hit else "W2"


@C.family("tent140", "8c")
def tent140(rnd, game):
    cases, exp = [], []
    for k in range(1200):
        c = C.Case(C.FN8C["do140"])
        row = {"w": "do140", "sid": C.pick_skill(rnd), "lvl": C.pick_lvl(rnd)}
        C.put_caster(c, rnd, row, types=(1, 1, 1, 0))
        C.put_game_b(c, rnd, row, game)
        C.put_target_a(c, rnd, row, game)
        row["tguid"] = C.u32f(c, C.T + 0x0C) if row["t"] else None
        row["cal"] = C.sor_calcs(c, rnd, row["sid"], (0x138,))
        diff = rnd.choice([0, 1, 2, 0, 1, 2, rnd.randrange(256)])
        c.put(game + 0x6C, bytes([rnd.getrandbits(8), diff]))
        row["diff"] = diff
        mb = [rnd.choice([rnd.randrange(C.NMON), -1, rnd.randint(-0x8000, 0x7FFF)]) for _ in range(C.NMON)]
        for i in range(C.NMON):
            c.put(C.MSREC + 0x1A8 * i + 0x02, C.le16(mb[i]))
        row["mb140"] = mb
        if rnd.random() < 0.8:
            bx, by = C.put_room_pos(c, rnd, row, p=0.9)
            if row["t"] and row["tt"] in (2, 4, 5):
                c.put(C.TP + 0x0C, C.le32(bx) + C.le32(by))
                row.update(tx=bx, ty=by)
            elif row["t"] and C.u32f(c, C.T + 0x2C):
                c.put(C.TP + 0x02, C.le16(bx))
                c.put(C.TP + 0x06, C.le16(by))
                row.update(tx=bx, ty=by)
            elif not row["t"]:
                c.put(C.UP + 0x02, C.le16(bx))
                c.put(C.UP + 0x06, C.le16(by))
                row.update(ux=bx, uy=by)
        if rnd.random() < 0.8:
            r = rnd.choice(C.ROOMS)
            c.put(C.UP + 0x1C, C.le32(r))
            row["uroom"] = r
        if k < 2:
            put_worked(c, row, game, room_hit=(k == 0))
        C.finish_8(c, rnd, row, game, cases, exp)
    return cases, C.mem_8c(), {"cases": exp}


C.CHECKS["tent140"] = C.check9b("tent140", C.move_8c_model, ["n_mod4", "xy_swap140"], C.RS_8C, md_masked=False)


# ----------------------------------------------------------------------------------------------- do 137 past STATE_Set
OBS_D137 = 0x00570590                    # do 137's last call, at 0x005D2793 (return 0x005D2798)
STREC = 0x12670000                       # DataTables+0xBC: the States records (0x3C); record 104's +0x12 written
ST104 = 104
NSWX = 12                                # the target's state words: 6 for 190 states, then the changed half
C.BOUNDS_8C[OBS_D137] = "Do137Next"
C.BOUND_BY_NAME["Do137Next"] = OBS_D137
C.ALLBOUND[OBS_D137] = "Do137Next"


def rflag(room):
    return room + 0xE0


def mem_d137():
    lines = [ln for ln in C.mem_8c() if ln != "observe %08x" % 0x00639DB0]
    lines.insert(0, "dword %08x %08x" % (C.DT + 0xBC, STREC))
    lines.append("observe %08x" % OBS_D137)
    return lines


@C.family("d137", "8c")
def d137(rnd, game):
    """do 137 0x005D26F0 as hit_8c's do 137 arm, with STATE_Set 0x00639DB0 run whole (0x00625A70, 0x00452040 on the
    States records, sub_0064C040_UnitMarkUpdated with UnitGetRoom 0x00620BB0 -> 0x00648A80, RoomFlag4 0x0061AB60
    and RoomUpdatedList 0x00619F90), do 137's own UnitMarkUpdated, up to 0x00570590 at 0x005D2793."""
    cases, exp = [], []
    for k in range(1500):
        c = C.Case(C.FN8C["do137"])
        row = {"w": "do137", "sid": C.pick_skill(rnd), "lvl": C.pick_lvl(rnd)}
        C.put_caster(c, rnd, row, types=(1, 1, 1, 0))
        C.put_game_b(c, rnd, row, game)
        C.put_target_a(c, rnd, row, game, types=(1, 1, 1, 1, 0, 2, 3, 4))
        row["tguid"] = C.u32f(c, C.T + 0x0C) if row["t"] else None
        row["cal"] = C.sor_calcs(c, rnd, row["sid"], (0x138,))
        C.put_corpse(c, rnd, row)
        if row["t"] and row["tt"] == 1 and rnd.random() < 0.7:
            C.force_corpse(c, rnd, row)
        m2f = row["m2f"]
        for i in range(C.NMON2):
            m2f[i] = (m2f[i] | 0x1000) if rnd.random() < 0.85 else (m2f[i] & ~0x1000)
            c.put(C.MS2REC + 0x134 * i + 0x04, C.le16(m2f[i]))
        if C.sid_ok(row):
            st = rnd.choice([rnd.randrange(C.NSTATES)] * 10 + [-1, C.NSTATES])
            c.put(C.srec(row) + 0x80, C.le16(st))
            row["ast"] = st
        # the words STATE_Set and UnitMarkUpdated read and write (all dumped, so all written)
        tw = list(row["twords"]) if row.get("twords") is not None else [rnd.getrandbits(32) for _ in range(C.NSW)]
        if rnd.random() < 0.5:                         # state 104 clear or already set, half each
            tw[ST104 >> 5] &= ~(1 << (ST104 & 31))
        else:
            tw[ST104 >> 5] |= 1 << (ST104 & 31)
        ext = [rnd.choice([0, rnd.getrandbits(32)]) for _ in range(NSWX - C.NSW)]
        for i, v in enumerate(tw + ext):
            c.put(C.TSL + 0x200 + 4 * i, C.le32(v))
        if row.get("twords") is not None:
            row["twords"] = tw
        row["tw_all"] = tw + ext
        rec12 = rnd.getrandbits(8)
        c.put(STREC + 0x3C * ST104 + 0x12, bytes([rec12]))
        row["rec12"] = rec12
        tc4, tc8, te0 = rnd.getrandbits(32), rnd.getrandbits(32), rnd.getrandbits(32)
        if rnd.random() < 0.6:
            tc4 &= ~0x2000
        c.put(C.T + 0xC4, C.le32(tc4) + C.le32(tc8))
        c.put(C.T + 0xE0, C.le32(te0))
        row.update(tc4=tc4, tc8=tc8, te0=te0)
        rm = {}
        for r in C.ROOMS:
            f34 = rnd.getrandbits(32) & ~4 if rnd.random() < 0.75 else rnd.getrandbits(32) | 4
            head, fl = rnd.choice([0, rnd.getrandbits(32)]), rnd.getrandbits(32)
            c.put(r + 0x1C, C.le32(head))
            c.put(r + 0x2C, C.le32(rflag(r)))
            c.put(r + 0x34, C.le32(f34))
            c.put(rflag(r), C.le32(fl))
            rm[str(r)] = [f34, head, fl]
        row["rm"] = rm
        dumps = [(C.T + 0xC4, 8), (C.T + 0xE0, 4), (C.TSL + 0x200, 4 * NSWX)]
        for r in C.ROOMS:
            dumps += [(r + 0x1C, 4), (rflag(r), 4)]
        C.finish_8(c, rnd, row, game, cases, exp, dumps)
    return cases, mem_d137(), {"cases": exp}


def d137_model(row, game, br, neg=None):
    br["do137"] += 1
    if not C.sid_ok(row):
        br["nosid"] += 1
        return C.ret_8(row, 0)
    st = C.s16(row["ast"])
    if not 0 <= st < C.NSTATES:
        br["nostate"] += 1
        return C.ret_8(row, 0)
    t = C.tgt_unit(row)
    if not t:
        br["notarget"] += 1
        return C.ret_8(row, 0, bit6=True)
    if not C.corpse590(row):
        br["notcorpse"] += 1
        return C.ret_8(row, 0, bit6=True)
    mem = {}
    tc4, tc8, te0 = row["tc4"], row["tc8"], row["te0"]
    tw = list(row["tw_all"])
    if row.get("twords") is not None:                # STATE_Set -> 0x00625A70(T, 104, 1)
        b = 1 << (ST104 & 31)
        old = tw[ST104 >> 5] & b
        tw[ST104 >> 5] |= b
        if neg == "old_inv":
            old = not old
        if not old:
            tw[((C.NSTATES + 31) >> 5) + (ST104 >> 5) if neg != "chg_nsw" else C.NSW + 1 + (ST104 >> 5)] |= b
            if row["rec12"] & 1:
                tc8 |= 8
            br["bit_new"] += 1
        else:
            br["bit_had"] += 1
    else:
        br["nolist"] += 1
    rm = {k: list(v) for k, v in row["rm"].items()}
    room = row.get("troom", 0)                       # a monster: [T+0x2C]+0x1C, 0 without a path
    for _ in range(2):                               # STATE_Set's UnitMarkUpdated, then do 137's
        if not room:
            br["noroom"] += 1
            break
        f34, head, fl = rm[str(room)]
        if f34 & 4 and neg != "f34_any":
            br["roomflag4"] += 1
            break
        if tc4 & 0x2000:
            br["marked"] += 1
            continue
        tc4 |= 0x2000
        rm[str(room)] = [f34, t, 1]
        te0 = head
        br["linked"] += 1
    mem[C.T + 0xC4] = C.le32(tc4) + C.le32(tc8)
    mem[C.T + 0xE0] = C.le32(te0)
    mem[C.TSL + 0x200] = b"".join(C.le32(v) for v in tw)
    for r in C.ROOMS:
        _, head, fl = rm[str(r)]
        mem[r + 0x1C] = C.le32(head)
        mem[rflag(r)] = C.le32(fl)
    br["next"] += 1
    return C.obs_8(row, "Do137Next", {"ecx": game, "edx": C.U}, [C.U, st, row["sid"], row["lvl"]], 0x005D2798,
                   bit6=True, mem=mem)


C.CHECKS["d137"] = C.check9b("d137", d137_model, ["old_inv", "chg_nsw", "f34_any"], C.RS_8C, md_masked=False)


def cmd_worked(a):
    """The two worked cases as the model reads them, against the spec's table (rng.step from (1, 666))."""
    import json
    meta = json.load(open(os.path.join(a.dir, "tent140.json")))
    lo, hi = WORKED_SEED
    steps = []
    for _ in range(9):
        lo, hi = RNG.step(lo, hi)
        steps.append((lo, hi))
    print("WORKED steps " + " ".join("%08x,%08x" % s for s in steps))
    for row in meta["cases"][:2]:
        n, sp, useed = C.tent_model(row)
        print("WORKED %s n=%d spawn=%s seed_end=%08x,%08x" % (
            row.get("worked"), n, None if sp is None else (sp[0], sp[1], sp[3] + 1, n - sp[3]), useed[0], useed[1]))
    return 0


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("cmd", choices=("cases", "check", "worked", "manifest"))
    ap.add_argument("family", nargs="*")
    ap.add_argument("--dir", default=DEFAULT_DIR)
    ap.add_argument("--write", action="store_true")
    o = ap.parse_args(argv)
    if o.cmd == "worked":
        return cmd_worked(o)
    if o.cmd == "manifest":
        lines = []
        for dp, _, fs in os.walk(o.dir):
            for f in sorted(fs):
                if f == "manifest.sha256":
                    continue
                p = os.path.join(dp, f)
                lines.append("%s  %s" % (hashlib.sha256(open(p, "rb").read()).hexdigest(), os.path.relpath(p, o.dir)))
        lines.sort(key=lambda s: s.split("  ", 1)[1])
        txt = "\n".join(lines) + "\n"
        if o.write:
            open(os.path.join(o.dir, "manifest.sha256"), "w").write(txt)
        sys.stdout.write(txt)
        return 0
    fams = o.family or ["tent140", "d137"]
    return C.main([o.cmd] + fams + ["--dir", o.dir, "--batch", "8c"])


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
