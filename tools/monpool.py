"""Model of the level monster pools ("monster regions") and of the monster level (plan 0012).

Usage:
  python3 -I tools/monpool.py pool  <excel-dir> --seed N --diff D [--draw K] [--exp 0|1] [--level ID ...]
  python3 -I tools/monpool.py check <excel-dir> <run.log> [...]
  python3 -I tools/monpool.py mlvl  <excel-dir> --cls C --level ID --diff D --exp 0|1

<excel-dir> is a data/global/excel directory (e.g. workspace/merged/data/global/excel). Records are the
.bin files the game loads (levels, monstats, monstats2), read by position.

The model (docs/findings/monsters/0001-level-pool.md, fn: names from re/symbols.csv):
  * At game creation sub_00547D20_MonRegionsInit steps the game seed once: L = Step(game seed).low, and
    a local region seed R = Init(L). Under `-seed N` the game seed starts as Init(N) and this is its
    first draw (--draw K: K-th draw, default 1).
  * sub_005479C0_MonRegionsBuild walks level ids 1 .. nLevels-1 in order, all from R:
      pool build (sub_005475E0_MonRegionPool): candidates = the `mon` slots (normal) or `nmon` slots
      (nightmare, hell) up to the first blank (Levels +0x33 / +0x34, filled at load); picks =
      min(NumMon, 13, len(candidates)); for each pick: i = Range(R, remaining); c = list[i]; on the first
      pick only, if `rangedspawn`, up to 20 redraws until monstats `rangedtype`; remove list[i];
      keep c only if monstats `isSpawn` (entry: class, Rarity; rarity sum and count updated).
      then for each kept entry, sub_005BDB20_MonVariantRoll(R, entry, 3): appearance sets from
      monstats2 +0x15 (16 component counts) and +0x25 (cap = 1 << b).
  * Monster level (sub_00573CB0_MonStatsInit): d = min(difficulty, 2), d = 0 for the five hireling
    classes; level = MonStats Level[d]; if expansion and d > 0 and not noRatio and not boss:
    level = Levels MonLvlEx[d] of the monster's level (sub_0061DCA0_LevelMonLvl, 1 if no level).

  * Critters (sub_0046C460_ClientCritters, client side, per client room, room seed +0x6C): for each
    `cmon` slot up to the first blank: Step; if low % 100 < cpct: n = Range(MaxGrp - MinGrp) + MinGrp of
    the class (monstats record), times camt if non-zero; n creations of that class. A room with no
    critter is checked to its seed after; otherwise up to the first creation (whose own draws are not
    modelled) and the first slot's class and count.

`check` reads the MPS / MPR / MLV / CR0-CRC-CRX lines of tools/gdb/mon-pool.gdb logs (header "# d2run seed=N") and
compares every logged value with the model: the game-seed draw index of MPS, every region's entries,
variant sets, copied Levels fields and seed after, every monster level. Exit 0 only if all match.
Stdlib only. Read-only.
"""
import json
import os
import re
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from excel_bin import find_file, read_bin  # noqa: E402
from rng import MASK, MULT, INIT_HIGH  # noqa: E402

HIRELINGS = {271, 338, 359, 560, 561}  # sub_0063EE90_HirelingType: roguehire, act2hire, act3hire, act5hire1/2


class Seed:
    def __init__(self, low, high=INIT_HIGH):
        self.low, self.high = low & MASK, high & MASK

    def step(self):
        v = self.low * MULT + self.high
        self.low, self.high = v & MASK, (v >> 32) & MASK
        return self.low

    def range(self, n):
        if n < 1:
            return 0
        return self.step() % n

    def __str__(self):
        return "%08x:%08x" % (self.low, self.high)


class Tables:
    def __init__(self, excel_dir):
        self.lv, sz = read_bin(find_file(excel_dir, "levels", ".bin"))
        assert sz == 0x220, sz
        self.ms, sz = read_bin(find_file(excel_dir, "monstats", ".bin"))
        assert sz == 0x1A8, sz
        self.ms2, sz = read_bin(find_file(excel_dir, "monstats2", ".bin"))
        assert sz == 0x134, sz

    # levels
    def slots(self, lid, off):
        r, out = self.lv[lid], []
        for k in range(25):  # DRLG_LoadLevels: count up to the first negative slot, at most 25
            v = struct.unpack_from("<h", r, off + 2 * k)[0]
            if v < 0:
                break
            out.append(v)
        return out

    def lvl_u8(self, lid, off):
        return self.lv[lid][off]

    def monlvl(self, lid, d, exp):
        if not (0 < lid < len(self.lv)) or d > 2:
            return 1
        return struct.unpack_from("<h", self.lv[lid], (0x16 if exp else 0x10) + 2 * d)[0]

    # monstats
    def msrec(self, c):
        return self.ms[c] if 0 <= c < len(self.ms) else None

    def ranged(self, c):
        r = self.msrec(c)
        return r is not None and bool(r[0x0F] & 0x10)

    def is_spawn(self, c):
        r = self.msrec(c)
        return r is not None and bool(r[0x0C] & 0x01)

    def ms2rec(self, c):
        r = self.msrec(c)
        if r is None:
            return None
        i = struct.unpack_from("<h", r, 0x18)[0]
        return self.ms2[i] if 0 <= i < len(self.ms2) else None


def variant_roll(t, seed, ent, n=3):
    """sub_005BDB20_MonVariantRoll: ent = [class, rarity, sets(list of 16-int lists)]."""
    m2 = t.ms2rec(ent[0])
    if m2 is None:
        return
    comp = list(m2[0x15:0x25])
    have = len(ent[2])
    n = min(n, (1 << (m2[0x25] & 31)) - have)
    if n <= 0:
        return
    if have + n > 3:
        n = 3 - have
    if n <= 0:
        return
    sets = ent[2]
    if have == 0:
        sets.append([0 if c < 2 else seed.range(c) for c in comp])
        n -= 1
    if n == 0:
        return
    cand = [i for i in range(16) if comp[i] > 1]
    k = len(cand)
    if k == 0:
        return
    if k == 1:
        a = b = cand[0]
    else:
        u = seed.range(k)
        a = cand[u]
        cand[u] = cand[k - 1]
        b = cand[seed.range(k - 1)]

    def roll(c):  # inline Range with no draw for a count of 0
        return 0 if c == 0 else seed.step() % c

    for _ in range(n):
        tries = 3
        while True:
            new = list(sets[0])
            new[a] = roll(comp[a])
            if a != b:
                new[b] = roll(comp[b])
            dup = False
            for s in sets:
                if s == new:
                    tries -= 1
                    dup = True
            if not dup or tries == 0:
                break
        sets.append(new)


def build_pool(t, seed, lid, diff):
    """sub_005475E0_MonRegionPool. Returns the entry list [class, rarity, sets]."""
    numon = min(t.lvl_u8(lid, 0x32), 13)
    cand = t.slots(lid, 0x68 if diff else 0x36)
    picks = min(numon, len(cand))
    ranged_rule = t.lvl_u8(lid, 0x31) != 0
    ents = []
    for p in range(picks):
        if len(cand) < 1:
            break
        i = seed.range(len(cand))
        c = cand[i]
        if p == 0 and ranged_rule:
            for _ in range(20):
                if t.ranged(c):
                    break
                i = seed.range(len(cand))
                c = cand[i]
        del cand[i]
        if t.is_spawn(c):
            ents.append([c, t.ms[c][0x2E], []])
    return ents


def build_all(t, low, diff, exp):
    """sub_005479C0_MonRegionsBuild from region seed Init(low). Yields (lid, region dict, seed str)."""
    seed = Seed(low)
    for lid in range(1, len(t.lv)):
        ents = build_pool(t, seed, lid, diff)
        for e in ents:
            variant_roll(t, seed, e, 3)
        r = t.lv[lid]
        reg = {"id": lid, "act": r[3], "n": len(ents), "rsum": sum(e[1] for e in ents) & 0xFF, "ntot": len(ents),
               "ents": [[e[0], e[1], [bytes(s).hex() for s in e[2]]] for e in ents],
               "den": struct.unpack_from("<i", r, 0x1C + 4 * diff)[0], "umin": r[0x28 + diff],
               "umax": r[0x2B + diff], "wndr": r[0x2E], "quest": r[0x30],
               "mlvl": [t.monlvl(lid, diff, exp)] * 2, "f0c": -1, "f2d4": -1}
        yield lid, reg, str(seed)


def monster_level(t, cls, lid, diff, exp):
    d = min(diff, 2)
    if cls in HIRELINGS:
        d = 0
    r = t.ms[cls]
    lvl = struct.unpack_from("<h", r, 0xAA + 2 * d)[0]
    if exp and d > 0 and not (r[0x0C] & 0x04) and not (r[0x0C] & 0x40):
        lvl = t.monlvl(lid if lid is not None else 0, d, exp)
    return lvl, d


def critters(t, lid, seed):
    """sub_0046C460_ClientCritters on a client room of level lid, up to its first creation.
    Returns (class, count, seed) for the first slot that creates critters, with the room seed at its
    first sub_0046C1A0_ClientCritterCreate call, or (None, 0, seed after) if no slot creates any.
    The create call itself draws from the same room seed (placement and the client unit seed), which is
    not modelled here (monsters/spawn), so later slots are not predicted."""
    if not (0 < lid < len(t.lv)):
        return None, 0, seed
    r = t.lv[lid]
    for k in range(4):
        c = struct.unpack_from("<h", r, 0xCC + 2 * k)[0]
        if c < 0:
            break
        pct = struct.unpack_from("<h", r, 0xD4 + 2 * k)[0] & MASK
        if seed.step() % 100 < pct:
            m = t.ms[c]
            n = seed.range(m[0x30] - m[0x2F]) + m[0x2F]
            amt = struct.unpack_from("<h", r, 0xDC + 2 * k)[0]
            if amt:
                n *= amt
            if n > 0:
                return c, n, seed
    return None, 0, seed


def first_draw_low(n, k):
    s = Seed(n)
    for _ in range(k):
        s.step()
    return s


def draw_index(n, gseed, limit=100000):
    lo, hi = (int(x, 16) for x in gseed.split(":"))
    s = Seed(n)
    for k in range(limit + 1):
        if (s.low, s.high) == (lo, hi):
            return k
        s.step()
    return None


def parse_log(path):
    seed, args, events = None, "", []
    with open(path, errors="replace") as fh:
        for ln in fh:
            m = re.match(r"# d2run seed=(\d+)(.*)", ln)
            if m:
                seed, args = int(m.group(1)), m.group(2)
                continue
            m = re.match(r"(MPS|MPR|MLV|CR0|CRC|CRX) (\{.*\})\s*$", ln)
            if m:
                events.append((m.group(1), json.loads(m.group(2))))
    return seed, args, events


def check(excel_dir, paths):
    t = Tables(excel_dir)
    total = bad = 0
    for path in paths:
        n, args, events = parse_log(path)
        counts = {}
        cur = None  # (diff, exp, generator of predicted regions)
        pred = {}
        diff = exp = None
        crit, got_cls, crit_rooms = None, [], [0, 0]
        for tag, d in events:
            counts[tag] = counts.get(tag, 0) + 1
            if tag == "MPS":
                k = draw_index(n, d["gseed"]) if n else None
                diff, exp = d["diff"], d["exp"]
                total += 1
                ok = k == 1 and d["low"] == int(d["gseed"].split(":")[0], 16)
                if not ok:
                    bad += 1
                    print(f"MISMATCH {path}: MPS game-seed draw index {k} (want 1), low {d['low']:08x}")
                ms723 = t.ms[723][:16].hex() if len(t.ms) > 723 else None
                total += 1
                if d["ms723"] != ms723 or d["ms722"] != t.ms[722][:16].hex() or d["nmonstats"] != len(t.ms):
                    bad += 1
                    print(f"MISMATCH {path}: monstats records 722/723 or count differ from monstats.bin")
                pred = {lid: (reg, s) for lid, reg, s in build_all(t, d["low"], diff, exp)}
                print(f"{path}: seed={n}{args} MPS diff={diff} forced={d.get('forced')} exp={exp} gtype={d['gtype']} "
                      f"game-seed draw={k} ret=0x{d['ret']:08x}")
            elif tag == "MPR":
                total += 1
                want, wseed = pred.get(d["id"], (None, None))
                got = dict(d)
                gseed = got.pop("seed")
                if want is None or want != got or wseed != gseed:
                    bad += 1
                    if bad <= 20:
                        print(f"MISMATCH {path}: MPR level {d['id']}\n  want {json.dumps(want)} {wseed}\n"
                              f"  got  {json.dumps(got)} {gseed}")
            elif tag == "CR0":
                crit = d if d["seed"] else None
                got_cls = []
            elif tag == "CRC":
                got_cls.append((d["cls"], d["seed"]))
            elif tag == "CRX" and crit is not None and crit["room"] == d["room"]:
                total += 1
                lo, hi = (int(x, 16) for x in crit["seed"].split(":"))
                c, cnt, sd = critters(t, crit["lid"] or 0, Seed(lo, hi))
                if c is None:
                    ok = not got_cls and str(sd) == d["seed"]
                else:
                    run = 0
                    while run < len(got_cls) and got_cls[run][0] == c:
                        run += 1
                    nxt = got_cls[run][0] if run < len(got_cls) else None
                    ok = bool(got_cls) and got_cls[0] == (c, str(sd)) and (run == cnt or nxt == c)
                crit_rooms[c is not None] += 1
                if not ok:
                    bad += 1
                    if bad <= 40:
                        print(f"MISMATCH {path}: critters room {crit['room']:08x} level {crit['lid']}: "
                              f"want first slot {c} x{cnt} at {sd}, got {got_cls[:4]} end {d['seed']}")
                crit = None
            elif tag == "MLV":
                total += 1
                want, wd = monster_level(t, d["cls"], d["lid"], d["diff"], d["exp"])
                if (want, wd) != (d["lvl"], d["d"]):
                    bad += 1
                    if bad <= 40:
                        print(f"MISMATCH {path}: MLV class {d['cls']} level {d['lid']} diff {d['diff']} "
                              f"exp {d['exp']}: want ({want}, d={wd}) got ({d['lvl']}, d={d['d']})")
        print(f"  {path}: " + " ".join(f"{k}={v}" for k, v in sorted(counts.items()))
              + f" critter-rooms none={crit_rooms[0]} some={crit_rooms[1]}")
    print(f"monpool: {total - bad}/{total} match")
    return 0 if bad == 0 and total else 1


def opt(argv, name, default=None, conv=int, many=False):
    vals = [conv(argv[i + 1]) for i, a in enumerate(argv) if a == name and i + 1 < len(argv)]
    if many:
        return vals
    return vals[-1] if vals else default


def main(argv):
    if len(argv) >= 2 and argv[0] == "check":
        return check(argv[1], argv[2:])
    if len(argv) >= 2 and argv[0] == "pool":
        t = Tables(argv[1])
        n, diff = opt(argv, "--seed"), opt(argv, "--diff", 0)
        k, exp = opt(argv, "--draw", 1), opt(argv, "--exp", 1)
        want = set(opt(argv, "--level", many=True))
        s = first_draw_low(n, k)
        print(f"game seed Init({n}) after {k} step(s): {s}; region seed = Init({s.low:08x})")
        for lid, reg, seed in build_all(t, s.low, diff, exp):
            if want and lid not in want:
                continue
            ents = " ".join(f"{c}(r{r},{len(v)}v)" for c, r, v in reg["ents"])
            print(f"level {lid:3d} act {reg['act']} mlvl {reg['mlvl'][0]:3d} pool [{ents}] seed after {seed}")
        return 0
    if len(argv) >= 2 and argv[0] == "mlvl":
        t = Tables(argv[1])
        lvl, d = monster_level(t, opt(argv, "--cls"), opt(argv, "--level"), opt(argv, "--diff", 0),
                               opt(argv, "--exp", 1))
        print(f"monster level {lvl} (difficulty index {d})")
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
