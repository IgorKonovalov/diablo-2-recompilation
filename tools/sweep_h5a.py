"""Plan 0038 batch H5a (drlg-links): the act link builder's unreached branches. Counters around tools/drlg.py gen on
the run:2026-10-17-sweep-links logs, a check of the batch's new logger lines against the link-builder model, and the
offline seed scan that chose the map seeds.

Usage:
  python3 -I tools/sweep_h5a.py logs [LOG ...]            # default: workspace/logs/sweep-links/sweep-links-s*.log
  python3 -I tools/sweep_h5a.py scan FIRST LAST [DIFFS [PICK [DONE]]]   # map seeds FIRST..LAST-1, difficulties
                      "0,1,2"; PICK: a greedy seed cover for that difficulty after the seeds DONE ("82,52")
Unit tests of the pure helpers: python3 -I tools/test_sweep_h5a.py.

`scan` runs the act model alone (drlg.Act, act_links) for acts I, II, IV and V on each map seed and difficulty, with
the picks, the checks and RectTouch wrapped, and counts:
  final    the choice each pick ended on (the B2 table's key: d, (d, f), lo & 1, b or k), per pick and level
  tried    every choice a pick placed, accepted or not
  reject   each check reject by its deciding rule: overlap (the plain test), Rogue table 0 entry, Burial Grounds side,
           Act1B widening (the widened rect[0] overlaps and the plain test passed)
  l27      level 6's side and the act-seed draw's parity, i.e. level 27's index
  touch    LevelSeamsByTouch's RectTouch tests by outcome (shared x edge, shared y edge, corner, apart, overlap)
  backtrack an exhausted pick (no build backtracked in run:2026-10-15-drlg-maze)
and lists the first seeds of each key.

`logs` runs the unchanged GenModel of tools/drlg.py (its own checks, 0 mismatches required) and then checks, per
LevelLinkBuild call (LNK0 .. LNK1), the new logger lines of tools/gdb/drlg-links.py against a replay of the model
from the logged act seed:
  LNKP  0x00677388  after each pick call: entry i, result, rect[i], dir, dir0, flip, flip0, the seed copy
  LNKC  0x006773C5  after each check call: entry i, result
  LNKT  0x00677606 / 0x0067760B  LevelSeamsByTouch's RectTouch call: the two levels, their rects, the result
It prints one `H5A` line per counter: the final choices from LNK1 (checked line by line by gen), the tried choices and
the rejects by rule from LNKP/LNKC (each matched to the model's sequence), level 27's index (LK27) and the Barracks
finder of each level-28 window, and the RectTouch outcomes from LNKT.

Exit 1 on any mismatch. Stdlib only. Read-only.
"""
import collections
import glob
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
ROOT = os.path.dirname(HERE)
LOGS = os.path.join(ROOT, "workspace", "logs", "sweep-links")

PICK_NAME = {0x6760F0: "LinkAnchor", 0x676150: "0x00676150", 0x676280: "0x00676280", 0x676450: "0x00676450",
             0x676650: "0x00676650", 0x6768C0: "LinkPickFixed", 0x6769A0: "0x006769A0", 0x676AE0: "0x00676AE0",
             0x676C00: "0x00676C00", 0x67D830: "0x0067D830", 0x67D8E0: "0x0067D8E0", 0x67D980: "0x0067D980"}
FLIP_PICKS = (0x676450, 0x676650)
CHECKS = {0x6F0750: "1a", 0x6F0840: "1b", 0x6F0930: "plain", 0x6F0A20: "plain", 0x6F0C00: "plain", 0x6F0CF0: "plain",
          0x6F0B10: "plain", 0x6F0DE0: None, 0x6F0ED0: None}
BARRACKS_FINDER = {0: "FindEast", 1: "FindSouth", 2: "FindWest"}     # g_BarracksFinders, k = level 27's index


def choice_key(pick, d, f, dir_anchor, rect=None, prect=None):
    """The B2 table's choice of a placed entry: d for the cycling picks, (d, f) for the flip picks, b for
    0x0067D830/0x0067D8E0, k = b + 2 dir[anchor] for 0x0067D980, lo & 1 for 0x00676C00 (read from the rect: y = P.y - 8
    for 0, P.y + P.h - h + 8 for 1), None for LinkAnchor and LinkPickFixed."""
    if pick in (0x6760F0, 0x6768C0):
        return None
    if pick in FLIP_PICKS:
        return (d, f)
    if pick == 0x67D980:
        return d + 2 * dir_anchor
    if pick == 0x676C00:
        if rect is None or prect is None:
            return None
        return 0 if rect[1] == prect[1] - 8 else 1 if rect[1] == prect[1] + prect[3] - rect[3] + 8 else "?"
    return d


def touch_class(a, b):
    """RectTouch(a, b, -1)'s branch: 'edge gx=0' and 'edge gy=0' (true), 'corner' (both gaps 0), 'apart' (a positive
    gap, or both gaps non-zero and not both negative), 'overlap' (both gaps negative). Gaps as 0x0066B880 computes them."""
    gx = (b[0] - a[2] - a[0]) if a[0] <= b[0] else (a[0] - b[2] - b[0])
    gy = (b[1] - a[3] - a[1]) if a[1] <= b[1] else (a[1] - b[3] - b[1])
    if gx == 0 and gy <= -1:
        return "edge gx=0"
    if gy == 0 and gx <= -1:
        return "edge gy=0"
    if gx == 0 and gy == 0:
        return "corner"
    if gx < 0 and gy < 0:
        return "overlap"
    return "apart"


def seed_of(s):
    lo, hi = s.split(":")
    return int(lo, 16), int(hi, 16)


class Tap:
    """Wraps drlg's picks, checks and touch; records the build's event sequence into self.ev while armed."""

    def __init__(self, drlg):
        self.d = drlg
        self.ev = None
        self.c = collections.Counter()
        self.first = collections.defaultdict(list)
        self.where = None
        self.keys = None
        self.depth = 0
        h = self
        for va, fn in list(drlg.PICK.items()):
            def pick(B, fn=fn, va=va):
                i = B.i
                r = fn(B)
                if h.ev is not None:
                    h.ev.append(("P", i, r, list(B.rect[i]), B.dir[i], B.dir0[i], B.flip[i], B.flip0[i],
                                 (B.seed.lo, B.seed.hi)))
                if r:
                    a = B.t[i][2]
                    k = choice_key(va, B.dir[i], B.flip[i], B.dir[a] if a >= 0 else -1, B.rect[i],
                                   B.rect[a] if a >= 0 else None)
                    if k is not None:
                        h.note("tried %s level %d choice %s" % (PICK_NAME[va], B.t[i][1], k))
                else:
                    h.note("backtrack: %s level %d exhausted" % (PICK_NAME[va], B.t[i][1]))
                return r
            drlg.PICK[va] = pick
        plain, c1a, c1b = drlg._chk_plain, drlg._chk1a, drlg._chk1b

        def reason(B, kind):
            i = B.i
            lv = B.t[i][1]
            if not plain(B):
                return "overlap"
            if kind == "1a" and lv == 1:
                return "Rogue table 0 entry (index %d)" % (B.dir[i] + 4 * B.flip[i] + 8 * B.dir[B.t[i][2]]
                                                          + 32 * B.flip[B.t[i][2]])
            if kind == "1a" and lv == 17:
                return "Burial Grounds side taken"
            if kind == "1b":
                return "Act1B widening"
            return "?"

        def wrap(fn, kind):
            def chk(B):
                h.depth += 1
                try:
                    r = fn(B)
                finally:
                    h.depth -= 1
                if h.depth:               # Act1A/Act1B call the plain test inside: record the outer check only
                    return r
                i = B.i
                if h.ev is not None:
                    h.ev.append(("C", i, r))
                lv = B.t[i][1]
                if kind == "1a" and lv == 1:
                    h.note("Rogue table lookup %s" % ("accept" if r else "reject"))
                if kind == "1b" and i != 0 and plain(B):
                    h.note("Act1B widened test reached (plain test passed): %s" % ("accept" if r else "reject"))
                if not r:
                    h.note("reject %s level %d: %s" % (kind, lv, reason(B, kind)))
                return r
            return chk
        drlg._chk_plain = wrap(plain, "plain")
        drlg._chk1a = wrap(c1a, "1a")
        drlg._chk1b = wrap(c1b, "1b")
        self.raw_plain = plain
        touch = drlg.touch

        def t(a, b):
            r = touch(a, b)
            if h.ev is not None:
                h.ev.append(("T", list(a), list(b), int(r)))
            h.note("RectTouch %s" % touch_class(a, b))
            return r
        drlg.touch = t

    def note(self, k):
        self.c[k] += 1
        if self.keys is not None:
            self.keys.add(k)
        if self.where is not None and len(self.first[k]) < 4 and self.where not in self.first[k]:
            self.first[k].append(self.where)


def final_choices(drlg, A):
    """(pick, level, key) of every placed entry of the act's builds, from the builders' final state."""
    out = []
    for va, B, _, _ in A.builds:
        for i, (p, lv, a, _) in enumerate(B.t):
            k = choice_key(p, B.dir[i], B.flip[i], B.dir[a] if a >= 0 else -1, B.rect[i], B.rect[a] if a >= 0 else None)
            if k is not None:
                out.append((p, lv, k))
    return out


def level27_files(drlg, data):
    """LvlPrest Files of level 27's preset (the first row whose LevelId is 27, as gen's prest_by_level)."""
    import struct
    for rec in drlg.excel_bin(data.root, "lvlprest"):
        if struct.unpack_from("<i", rec, 0x04)[0] == 27:
            return struct.unpack_from("<i", rec, 0x40)[0]
    raise ValueError("no LvlPrest row for level 27")


def cmd_scan(argv):
    import drlg
    a, b = int(argv[0]), int(argv[1])
    diffs = [int(x) for x in argv[2].split(",")] if len(argv) > 2 else [0, 1, 2]
    pick_diff = int(argv[3]) if len(argv) > 3 else None
    done = [int(x) for x in argv[4].split(",")] if len(argv) > 4 else []
    data = drlg.Data(drlg.DEFAULT_DATA, drlg.DEFAULT_EXE)
    drlg.load_outdoor(data.root, data.exe)
    files27 = level27_files(drlg, data)
    T = Tap(drlg)
    errors = 0
    per_seed = collections.defaultdict(set)
    for s in range(a, b):
        for diff in diffs:
            T.keys = per_seed[(s, diff)]
            for acti in (0, 1, 3, 4):
                T.where = (s, diff, acti + 1)
                A = drlg.Act(acti, s, diff)
                try:
                    drlg.act_links(A)
                except drlg.Fatal as e:
                    errors += 1
                    print("H5A scan error: seed %d difficulty %d act %d: %r" % (s, diff, acti + 1, e))
                    continue
                for p, lv, k in final_choices(drlg, A):
                    T.note("final %s level %d choice %s" % (PICK_NAME[p], lv, k))
                if acti == 0:
                    B = A.builds[1][1]
                    lvs = [e[1] for e in B.t]
                    i6, i5 = lvs.index(6), lvs.index(5)
                    if A.idx27 is None:          # no level-6 draw: level 27 keeps its create-time RangeB(Files)
                        k27 = drlg.Seed((A.base + 27) & drlg.M32).range(files27)
                        how = "create-time"
                    else:
                        k27, how = A.idx27, "drawn"
                    T.note("level 6 side %d, level 27 index %s %d (Barracks %s)" % (
                        B.dir[i6], how, k27, BARRACKS_FINDER.get(k27, "-")))
                    T.note("combo table 0x6F0840 difficulty %d: Black Marsh first %d -> side %d, Dark Wood first %d -> %d"
                           % (diff, B.dir0[i6], B.dir[i6], B.dir0[i5], B.dir[i5]))
                if acti == 4:
                    B = A.builds[0][1]
                    T.note("combo table 0x6F0DE0 difficulty %d: Rigid b %d, Arreat first %d -> %d"
                           % (diff, B.dir[2], B.dir0[3], B.dir[3]))
    T.where = None
    T.keys = None
    print("H5A scan: map seeds %d..%d, difficulties %s, acts I II IV V, model errors %d" % (a, b - 1, diffs, errors))
    for k in sorted(T.c):
        print("H5A scan %s  %d  first %s" % (k, T.c[k], T.first.get(k, [])))
    if pick_diff is not None:
        cover(per_seed, pick_diff, done)
    return 1 if errors else 0


def is_target(k):
    """The keys the batch's sessions must reach: every final choice, the tried-only Rogue choices, the rejects by the
    Rogue table and by the Burial Grounds side test, level 27's index 0 and 2 (the Barracks with FindEast, FindWest)."""
    return (k.startswith("final ") or k.startswith("tried 0x00676450") or "Rogue table 0 entry" in k
            or "Burial Grounds side" in k or "(Barracks FindEast)" in k or "(Barracks FindWest)" in k)


def greedy(sets, targets):
    """Greedy set cover: [(seed, newly covered keys)] until no seed adds a target. Ties go to the lowest seed."""
    left, out = set(targets), []
    while left:
        best = max(sorted(sets), key=lambda s: len(sets[s] & left))
        new = sets[best] & left
        if not new:
            break
        out.append((best, sorted(new)))
        left -= new
    return out, left


def target_key(k):
    """A key as the tags count it: a choice per pick function (the level dropped), one Rogue-table reject."""
    if "Rogue table 0 entry" in k:
        return "reject 1a level 1: Rogue table 0 entry"
    if k.startswith("final ") or k.startswith("tried "):
        w = k.split()
        return " ".join(w[:2] + w[4:])
    return k


def cover(per_seed, diff, done=()):
    """Greedy seeds for the targets of difficulty diff that the seeds in `done` (sessions already run) left."""
    sets = {s: {target_key(k) for k in ks if is_target(k)} for (s, d), ks in per_seed.items() if d == diff}
    targets = set().union(*sets.values())
    for s in done:
        print("H5A cover done seed %d: %s" % (s, "; ".join(sorted(sets.get(s, set()) & targets))))
        targets -= sets.get(s, set())
    picks, left = greedy(sets, targets)
    print("H5A cover difficulty %d: %d targets, %d seeds" % (diff, len(targets), len(picks)))
    for s, new in picks:
        print("H5A cover seed %d: %s" % (s, "; ".join(new)))
    if left:
        print("H5A cover not covered: %s" % sorted(left))


# ------------------------------------------------------------------------------------------------------------ logs

def parse(path):
    for line in open(path, errors="replace"):
        tag, _, rest = line.partition(" ")
        if tag in ("LNK0", "LNKP", "LNKC", "LNK1", "LK27", "LNKT", "LNKU", "LNKW", "LC1") and rest.startswith("{"):
            try:
                yield tag, json.loads(rest)
            except ValueError:
                continue


def check_log(drlg, T, path, out):
    """Replay every logged LevelLinkBuild from its LNK0 act seed and compare the LNKP/LNKC sequence; LNKT results
    against RectTouch on the logged rects. Returns the mismatch count."""
    bad = 0
    cur = None
    pend_t = None
    for tag, d in parse(path):
        if tag == "LNK0":
            va = d["table"]
            A = drlg.Act(d["acti"], 1, d["diff"])
            A.seed = drlg.Seed(*seed_of(d["seed"]))
            T.ev = []
            chk = {"1a": drlg._chk1a, "1b": drlg._chk1b, "plain": drlg._chk_plain, None: None}[CHECKS[va]]
            after = drlg.outdoor_flags if va in (0x6F0750, 0x6F0840) else None
            T.where = os.path.basename(path)
            B = drlg.link_build(A, va, chk, after)
            cur = dict(va=va, B=B, ev=T.ev, got=[], acti=d["acti"], diff=d["diff"], client=d["client"])
            T.ev = None
        elif tag in ("LNKP", "LNKC") and cur is not None:
            if tag == "LNKP":
                cur["got"].append(("P", d["i"], d["r"], d["rect"], d["dir"], d["dir0"], d["flip"], d["flip0"],
                                   seed_of(d["bseed"])))
            else:
                cur["got"].append(("C", d["i"], d["r"]))
        elif tag == "LNK1" and cur is not None:
            ev, got = cur["ev"], cur["got"]
            side = "client" if cur["client"] else "server"
            if not got:
                out["LevelLinkBuild calls with no LNKP/LNKC lines (%s)" % side] += 1
                cur = None
                continue
            ok = ev == got
            out["LevelLinkBuild calls replayed (%s), event sequence %s" % (side, "matched" if ok else "MISMATCH")] += 1
            if not ok:
                bad += 1
                n = next((k for k in range(min(len(ev), len(got))) if ev[k] != got[k]), min(len(ev), len(got)))
                print("H5A MISMATCH %s table %#x at event %d: model %s, log %s" % (
                    os.path.basename(path), cur["va"], n, ev[n:n + 1], got[n:n + 1]))
            else:
                B = cur["B"]
                for e in got:
                    if e[0] == "P" and e[2]:
                        i = e[1]
                        p, lv, a, _ = B.t[i]
                        k = choice_key(p, e[4], e[6], B.dir[a] if a >= 0 else -1, e[3], B.rect[a] if a >= 0 else None)
                        if k is not None:
                            out["log tried (LNKP) %s choice %s" % (PICK_NAME[p], k)] += 1
                    elif e[0] == "C":
                        lv = B.t[e[1]][1]
                        out["log check (LNKC) %s level %d: %s" % (CHECKS[cur["va"]], lv, "accept" if e[2] else "reject")] += 1
                for p, lv, k in final_choices(drlg, type("A", (), {"builds": [(cur["va"], B, 0, 0)]})):
                    out["log final (LNK1) %s choice %s" % (PICK_NAME[p], k)] += 1
                R0 = B.rect[0]
                for w in cur.get("widen", []):
                    good = w["r0"] == [R0[0], R0[1] - 200, R0[2], R0[3] + 200]
                    out["log Act1B rect[0] widened to (x, y - 200, w, h + 200) of the model's rect[0]: %s"
                        % ("yes" if good else "MISMATCH")] += 1
                    if not good:
                        bad += 1
            cur = None
        elif tag == "LK27":
            out["log LK27: level 27 index %d" % d["idx"]] += 1
        elif tag == "LC1" and d.get("id") == 27:
            out["log LC1: level 27 create-time index %s" % d.get("idx")] += 1
        elif tag == "LNKT":
            pend_t = d
        elif tag == "LNKU" and pend_t is not None:
            r = d["r"]
            cls = touch_class(pend_t["ra"], pend_t["rb"])
            good = (r != 0) == cls.startswith("edge")
            out["log RectTouch (LNKT) %d -> %d: %s, result %d %s" % (
                pend_t["a"], pend_t["b"], cls, r, "as modelled" if good else "MISMATCH")] += 1
            if not good:
                bad += 1
            pend_t = None
        elif tag == "LNKW":
            widened = [d["r0"][0], d["r0"][1], d["r0"][2], d["r0"][3]]
            ov = drlg.gap_overlap(widened, d["ri"])
            good = (d["r"] != 0) == (not ov)
            out["log Act1B widened test (LNKW): %s %s" % ("accept" if d["r"] else "reject",
                                                       "as modelled" if good else "MISMATCH")] += 1
            if not good:
                bad += 1
            if cur is not None:
                cur.setdefault("widen", []).append(d)
    return bad


def cmd_logs(paths):
    import drlg
    paths = paths or sorted(glob.glob(os.path.join(LOGS, "sweep-links-s*.log")))
    data = drlg.Data(drlg.DEFAULT_DATA, drlg.DEFAULT_EXE)
    m = drlg.GenModel(data, False, False, drlg.PresetUnitData(drlg.DEFAULT_DATA, drlg.DEFAULT_EXE))
    out = collections.Counter()
    check = drlg.GenModel.maze_check

    def maze_check(g, path, L, d):        # level 28 windows: matched or not, with the Barracks finder the model took
        f0 = g.fail
        r = check(g, path, L, d)
        M = getattr(L, "mz_model", None)
        if L.id == 28 and M is not None:
            k = M.L.l27[0]
            out["maze window level 28 (Barracks), level 27 index %s, %s: %s" % (
                k, BARRACKS_FINDER.get(k, "?"), "matched" if g.fail == f0 else "MISMATCH")] += 1
        return r
    drlg.GenModel.maze_check = maze_check
    drlg.load_links(os.path.join(data.root, "data", "global", "excel"), data.exe)
    for p in paths:
        m.run(p)
        print("log %s" % os.path.relpath(p, ROOT))
    T = Tap(drlg)
    bad = 0
    for p in paths:
        bad += check_log(drlg, T, p, out)
    for k in sorted(out):
        print("H5A %s  %d" % (k, out[k]))
    for k in sorted(T.c):           # the model's reading of the replayed builds (each matched the logged sequence)
        if k.startswith(("reject", "Rogue table", "Act1B", "backtrack")):
            print("H5A replay %s  %d" % (k, T.c[k]))
    for k in sorted(m.cov):
        if any(s in k for s in ("link", "level-27", "Barracks", "maze windows")):
            print("H5A gen %s  %d" % (k, m.cov[k]))
    print("H5A gen: %d checks, %d mismatches over %d logs; logger lines: %d mismatches" % (m.checks, m.fail, len(paths), bad))
    return 1 if (m.fail or bad) else 0


def main(argv):
    if len(argv) >= 2 and argv[1] == "logs":
        return cmd_logs(argv[2:])
    if len(argv) >= 4 and argv[1] == "scan":
        return cmd_scan(argv[2:])
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
