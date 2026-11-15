#!/usr/bin/env python3
"""Plan 0066 Phase 1, batch S7d (`lane/n66m`): new `tools/rooms.py check` cases over the kept rooms.gdb logs of
run:2026-10-17-lifecycle (13 logs) and run:2026-10-17-h7a-lifecycle (3 logs), for the 14 drlg/lifecycle rows of the
batch (docs/plans/0066-inventory/README.md § 4).

    python3 -I tools/sweep2_s7d.py check [--out F]

One pass per log: `rooms.py`'s `Checker` runs unchanged as the control (its SUMMARY line is printed; its mismatches are
those of the kept checks: 0 on the 13 lifecycle logs, the 4 known `+0xC4` bit-0x2000 records on h7a-h-barb3), then
the observers below run on the same parsed lines:

  paths      13: the reference deltas RM0 -> RMX of every move against the B4/B5 walk counted per path (the model) and
             the same walk counted once per room and distance (the variant "rooms, not paths"); the largest refs seen
  near       14: after each move (RMX), every DRLG room of the new room's near list has an active room (+0x30 != 0) and
             status <= 1; rooms at walk distance 2 and 3 have status <= 2 and <= 3
  rab        16: RoomActivateB (RAB): a DRA follows iff +0x30 = 0 at the call; the room's status at the next RP while no
             move's snapshot gives it a reference
  first78    19: +0x78 at the first new-rooms walk (WG) of a room after its activation, by activation (ACTA inside a
             move, RAB)
  firstrs    21: the restore (RS0 .. RSX) of a populated room: monster, item or unit records met, game and room seeds
             in and out; first activations (no earlier FREE of the DRLG room in the log) apart
  free       25: after a FREE: the room in no later RP list and no later CRC near list until its DRLG room is activated
             again; a later move snapshot of the DRLG room with +0x30 = 0 until then
  order      32: the save decisions where restore 2 comes after a test that cleared save (the order separates them)
  noplayer   37: US lines of type 0; at every FREE the client's current room (the last CRC) is not the freed room;
             every CRC's new room is in its own near list; a freed monster's id met again later (MON, US, MR0)
  loses      49: restored alive records: the mode at the save (US) against the restored mode
  recorder   52: per restore, the MR0 order of record ids against the reverse of the room's save order (MREC after US)
  special    56, 58: H2b, H2c paths: mode, position against the record, room draws, flag-4 records
  wrorder    59: MRC, MRS, MRE, MRX order per created unit
  preset     78: PSU0 lines by walk block (populate, restore only, none, outside a walk); rooms whose populate block
             had a PSU0 and whose later restore-only block has none

Stdlib only. Read-only. Output ends with `S7d total bad=N control_bad=M`.
"""
import argparse
import collections
import io
import json
import os
import sys
from contextlib import redirect_stdout

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import rooms as RM  # noqa: E402

LOGS = [os.path.join(ROOT, "workspace", "logs", "rooms", "lifecycle-%s.log" % s) for s in (
    "cls-n-cold", "cls-nm-jail", "h-flayer", "h-highlands", "n-catacombs", "n-cold", "n-farooze", "n-long", "nm-dark",
    "nm-long", "nm-spider", "town-n2", "town-n")] + [
    os.path.join(ROOT, "workspace", "logs", "rooms", "h7a-%s.log" % s) for s in ("h-barb", "h-barb2", "h-barb3")]


def walk_counts(near, start):
    """(room, distance) -> number of paths, as DrlgRefAdd(start) walks: start at 0, then RefAddNear(start, 1)."""
    out = collections.Counter()
    out[(start, 0)] += 1

    def rec(d, k):
        for n in near.get(d, []):
            if not n:
                continue
            if k < 3:
                rec(n, k + 1)
            out[(n, k)] += 1
    rec(start, 1)
    return out


class S7d:
    def __init__(self):
        self.c = collections.defaultdict(collections.Counter)
        self.bad = collections.Counter()
        self.ex = collections.defaultdict(list)

    def note(self, sec, key, ok=True, ex=None):
        self.c[sec][key] += 1
        if not ok:
            self.bad[sec] += 1
            self.c[sec]["FAILED: " + key] += 1
            if ex is not None and len(self.ex[sec]) < 6:
                self.ex[sec].append("%s: %s" % (key, ex))

    def log(self, name, L):
        for f in (self.paths, self.near, self.rab, self.first78, self.firstrs, self.free, self.order, self.noplayer,
                  self.loses, self.recorder, self.special, self.wrorder, self.preset):
            f(name, L)

    # ---- 13
    def paths(self, name, L):
        i = 0
        while i < len(L):
            ln, tag, d = L[i]
            if tag != "RM0":
                i += 1
                continue
            j = i + 1
            while j < len(L) and L[j][1] not in ("RMX", "RM0"):
                j += 1
            if j >= len(L) or L[j][1] != "RMX":
                i = j
                continue
            x = L[j][2]
            before = {int(k): v for k, v in d["s"].items()}
            after = {int(k): v for k, v in x["s"].items()}
            near = {k: list(v[10]) for k, v in after.items()}
            for k, v in before.items():
                if not near.get(k):
                    near[k] = list(v[10])
            old, new = d["old"], d["new"]
            add = walk_counts(near, new) if new and old != new else collections.Counter()
            rem = collections.Counter()
            if old and old != new and before.get(old) and before[old][0]:
                rem = walk_counts(near, old)
            sadd = collections.Counter({k: 1 for k in add})
            srem = collections.Counter({k: 1 for k in rem})
            for k in set(before) & set(after):
                for dd in range(4):
                    got = (after[k][dd] - before[k][dd]) & 0xFFFF
                    got = got - 0x10000 if got >= 0x8000 else got
                    m = add[(k, dd)] - rem[(k, dd)]
                    v = sadd[(k, dd)] - srem[(k, dd)]
                    self.note("paths", "reference delta = the walk counted per path", got == m,
                              "%s:%d room %d d%d log %d model %d" % (name, ln, k, dd, got, m))
                    if m != v:
                        self.note("paths", "  separating (per room differs from per path): the log differs from per room", got != v,
                                  "%s:%d" % (name, ln))
            for k, v in after.items():
                self.c["paths-max"]["refs[3] %s" % ("0" if v[3] == 0 else ("1-9" if v[3] < 10 else ("10-39" if v[3] < 40 else "40+")))] += 1
                self.c["paths-max"]["largest refs[3]"] = max(self.c["paths-max"]["largest refs[3]"], v[3])
            i = j + 1

    # ---- 14
    def near(self, name, L):
        for ln, tag, d in L:
            if tag != "RMX" or not d.get("new"):
                continue
            s = {int(k): v for k, v in d["s"].items()}
            new = d["new"]
            if new not in s:
                self.note("near", "new room in the RMX snapshot", False, "%s:%d" % (name, ln))
                continue
            for n in s[new][10]:
                if not n:
                    continue
                v = s.get(n)
                if v is None:
                    self.c["near"]["near room outside the snapshot"] += 1
                    continue
                self.note("near", "a room of the new room's near list: active (+0x30 != 0) and status <= 1",
                          v[6] != 0 and v[4] <= 1, "%s:%d room %d st %d a30 %x" % (name, ln, n, v[4], v[6]))
            d2 = {n2 for n in s[new][10] if n for n2 in (s.get(n, [None] * 11)[10] or [])} - set(s[new][10])
            for n in d2:
                v = s.get(n)
                if v is not None and n:
                    self.c["near"]["a room two near steps away, not in the near list: status %d, active %s" % (v[4], v[6] != 0)] += 1

    # ---- 16
    def rab(self, name, L):
        pend = {}
        for k, (ln, tag, d) in enumerate(L):
            if tag == "RAB":
                nxt = next((e for _, t, e in L[k + 1:k + 40] if t in ("DRA", "RAB", "RP", "RM0")), None)
                dra = nxt is not None and nxt.get("d") == d["d"] and "pop" in nxt
                self.note("rab", "a DRA follows iff +0x30 = 0 at the call", dra == (d["a30"] == 0),
                          "%s:%d a30 %x" % (name, ln, d["a30"]))
                self.c["rab"]["RAB +0x30 %s, status %d, caller %x" % ("0" if d["a30"] == 0 else "set", d["st"], d["caller"])] += 1
                if d["a30"] == 0 and d["st"] == 4:
                    pend[d["d"]] = ln
            elif tag in ("RM0", "RMX"):
                for kk, v in d["s"].items():
                    if int(kk) in pend and any(v[0:4]):
                        self.c["rab"]["a RAB room given a reference by a later move before the next RP"] += 1
                        pend.pop(int(kk))
            elif tag == "RP":
                for act in d["acts"]:
                    if not act:
                        continue
                    for e in act["rooms"]:
                        if e[1] in pend:
                            self.note("rab", "RAB room (status 4, no move reference) at the next RP: active, status 4", e[5] == 4,
                                      "%s:%d st %d" % (name, ln, e[5]))
                            pend.pop(e[1])

    # ---- 19
    def first78(self, name, L):
        kind = {}
        inrm = False
        for k, (ln, tag, d) in enumerate(L):
            if tag == "RM0":
                inrm = True
            elif tag == "RMX":
                inrm = False
            elif tag == "ACTA":
                kind[d["d"]] = "ACTA (client move)" if d.get("in") else "ACTA outside a move"
            elif tag == "RAB" and d["a30"] == 0:
                kind[d["d"]] = "RAB"
            elif tag == "WG":
                rs = next((e for _, t, e in L[k + 1:k + 400] if t in ("RS0", "WG", "RP")), None)
                if rs is None or "gs" not in rs or rs.get("r") != d["r"]:
                    continue
                kd = kind.pop(rs["d"], None)
                if kd is None:
                    continue
                if kd.startswith("ACTA (client"):
                    self.note("first78", "first walk after a client activation: +0x78 >= 1", d["n78"] >= 1,
                              "%s:%d n78 %d" % (name, ln, d["n78"]))
                else:
                    self.c["first78"]["first walk after %s: +0x78 %s" % (kd, ">= 1" if d["n78"] >= 1 else "0")] += 1
        del inrm

    # ---- 21
    def firstrs(self, name, L):
        freed = set()
        for k, (ln, tag, d) in enumerate(L):
            if tag == "FREE":
                freed.add(d["d"])
            elif tag == "WG" and not d["fl"] & 1:
                j = k + 1
                rs = None
                while j < len(L) and L[j][1] not in ("WG", "RP", "CRC", "RM0"):
                    if L[j][1] == "RS0" and L[j][2]["r"] == d["r"]:
                        rs = j
                        break
                    j += 1
                if rs is None:
                    continue
                s0 = L[rs][2]
                m = rs + 1
                met = []
                end = None
                while m < len(L) and L[m][1] not in ("WG", "RS0", "RP"):
                    if L[m][1] in ("MR0", "IR0", "UR0"):
                        met.append(L[m][1])
                    if L[m][1] == "RSX":
                        end = L[m][2]
                        break
                    m += 1
                first = s0["d"] not in freed
                lab = "first activation" if first else "re-activation of a room never walked"
                if end is None:
                    self.c["firstrs"]["%s: no RSX before the next walk line" % lab] += 1
                    continue
                ok = not met and end["gs"] == s0["gs"] and end["rs"] == s0["rs"]
                self.note("firstrs", "populated room, %s: no record, game and room seeds unchanged" % lab, ok,
                          "%s:%d met %s" % (name, L[rs][0], met[:3]))

    # ---- 25
    def free(self, name, L):
        gone = {}          # freed active room -> its DRLG room, until the next RP
        dgone = {}
        susp = {}
        for ln, tag, d in L:
            if tag == "FREE":
                gone[d["r"]] = d["d"]
                dgone[d["d"]] = ln
                self.c["free"]["FREE lines"] += 1
            elif tag in ("DRA", "ACTA"):
                dgone.pop(d["d"], None)
            elif tag == "RP":
                listed = {e[0]: e[1] for act in d["acts"] if act for e in act["rooms"]}
                for r, dd in gone.items():
                    if r in listed and listed[r] == dd:
                        self.note("free", "freed room absent from the next RP list (or the pointer reused by another DRLG room)", False,
                                  "%s:%d" % (name, ln))
                    else:
                        self.note("free", "freed room absent from the next RP list (or the pointer reused by another DRLG room)", True)
                        if r in listed:
                            self.c["free"]["  of which the pointer reused by another DRLG room"] += 1
                for r, (cln, dd) in susp.items():
                    self.note("free", "a freed pointer in a CRC near list before the next RP: reused by another DRLG room",
                              r in listed and listed[r] != dd, "%s:%d" % (name, cln))
                gone, susp = {}, {}
            elif tag == "CRC":
                lst = set(d["nn"]) | set(d["on"])
                for r, dd in gone.items():
                    if r in lst:
                        susp[r] = (ln, dd)
                    else:
                        self.c["free"]["freed room in no CRC near list before the next RP"] += 1
            elif tag in ("RM0", "RMX"):
                for kk, v in d["s"].items():
                    if int(kk) in dgone:
                        self.note("free", "a freed DRLG room's snapshot before its next activation: +0x30 = 0", v[6] == 0,
                                  "%s:%d room %s a30 %x" % (name, ln, kk, v[6]))

    # ---- 32
    def order(self, name, L):
        u = None
        for ln, tag, d in L:
            if tag == "US":
                u = d
            elif tag == "USD" and u is not None and u["t"] == 1:
                sub = d["sub"]
                dead = sub.get("dead", 0)
                cleared = []
                if u["m"] == 12 and sub.get("draw") and sub["draw"][0] != 0:
                    cleared.append("mode-12 draw")
                if dead and sub.get("ud"):
                    cleared.append("udead")
                if dead and sub.get("al") == 2:
                    cleared.append("alignment 2")
                if dead and sub.get("mt18"):
                    cleared.append("MonTypeFlag 0x18")
                if u["c4"] & 0x200:
                    cleared.append("+0xC4 0x200")
                if u["c4"] & 0x80000000:
                    cleared.append("owned")
                rb = sub.get("rb")
                if cleared and rb == 2:
                    self.note("order", "restore 2 after a clearing test: saved (restore 2 decides last)", d["save"] == 1,
                              "%s:%d %s" % (name, ln, cleared))
                    self.c["order-cases"][(u["c"], tuple(cleared))] += 1
                elif cleared:
                    self.c["order"]["a clearing test, restore %s: saved %d" % (rb, d["save"])] += 1
                if u["m"] == 12:
                    self.c["order"]["mode 12: draw logged %s, dead %s, saved %d" % ("draw" in sub, dead, d["save"])] += 1
                u = None

    # ---- 37
    def noplayer(self, name, L):
        cur = None
        last_us = None
        freed_ids = {}
        for ln, tag, d in L:
            if tag == "CRC":
                cur = d["new"]
                if d["new"]:
                    self.note("noplayer", "a client's new room is in its own near list", d["new"] in d["nn"], "%s:%d" % (name, ln))
                else:
                    self.c["noplayer"]["CRC with new room 0 (leaving)"] += 1
            elif tag == "US":
                if d["t"] == 0:
                    self.note("noplayer", "a US line of a player (type 0)", False, "%s:%d" % (name, ln))
                self.c["noplayer"]["US lines"] += 1
                last_us = d
            elif tag == "USD":
                if last_us and last_us["t"] == 1 and not d["save"] and not d.get("kept"):
                    freed_ids[last_us["id"]] = ln
            elif tag == "FREE":
                self.note("noplayer", "the freed room is not the client's current room", d["r"] != cur, "%s:%d" % (name, ln))
            elif tag == "MON":
                for m in d.get("m", []):
                    if m["id"] in freed_ids and ln > freed_ids[m["id"]]:
                        self.note("noplayer", "a monster freed with its room (not saved, not kept) is met again (MON)", False,
                                  "%s:%d id %d" % (name, ln, m["id"]))
                        freed_ids.pop(m["id"])
            elif tag == "MR0":
                rid = RM.mrec_parse(d["b"])["id"]
                if rid in freed_ids:
                    self.note("noplayer", "a monster freed with its room is restored (MR0)", False, "%s:%d" % (name, ln))
        self.c["noplayer"]["monsters freed with their room, not met again (MON, MR0) to the log's end"] += len(freed_ids)

    # ---- 49
    def loses(self, name, L):
        mode_at_save = {}
        u = None
        for k, (ln, tag, d) in enumerate(L):
            if tag == "US" and d["t"] == 1:
                u = d
            elif tag == "MREC" and u is not None:
                r = RM.mrec_parse(d["b"])
                mode_at_save[(r["id"], r["fr"])] = u["m"]
            elif tag == "MRC" and d.get("u"):
                mr0 = next((L[j][2] for j in range(k - 1, max(0, k - 60), -1) if L[j][1] == "MR0"), None)
                if mr0 is None:
                    continue
                r = RM.mrec_parse(mr0["b"])
                m0 = mode_at_save.get((r["id"], r["fr"]))
                if m0 is None:
                    self.c["loses"]["restored without its save in the log"] += 1
                    continue
                if r["fl"] & 4:
                    self.c["loses"]["flag-4 record: saved mode %d -> restored %d" % (m0, d["m"])] += 1
                    continue
                self.note("loses", "alive record: restored in mode 1", d["m"] == 1, "%s:%d" % (name, ln))
                self.c["loses-modes"]["saved mode %d -> restored %d" % (m0, d["m"])] += 1

    # ---- 52
    def recorder(self, name, L):
        saved = collections.defaultdict(list)       # DRLG room -> record ids in save order (the release in progress)
        by_r = {}
        pend = collections.defaultdict(list)
        u = None
        for k, (ln, tag, d) in enumerate(L):
            if tag == "US":
                u = d
            elif tag == "MREC" and u is not None:
                pend[u["r"]].append(RM.mrec_parse(d["b"])["id"])
            elif tag == "FREE":
                if pend.get(d["r"]):
                    saved[d["d"]] = pend.pop(d["r"]) + saved.get(d["d"], [])
                pend.pop(d["r"], None)
            elif tag == "RS0":
                by_r[d["r"]] = d["d"]
                ids = []
                j = k + 1
                while j < len(L) and L[j][1] not in ("RSM", "RS0", "WG", "RP"):
                    if L[j][1] == "MR0":
                        ids.append(RM.mrec_parse(L[j][2]["b"])["id"])
                    j += 1
                want = saved.pop(d["d"], [])
                if not ids and not want:
                    continue
                self.note("recorder", "restore order = the reverse of the save order", ids == list(reversed(want)),
                          "%s:%d got %s want %s" % (name, ln, ids[:5], list(reversed(want))[:5]))
                if len(ids) > 1:
                    self.c["recorder"]["restores with 2 or more records (separating the order)"] += 1
                    self.c["recorder-ids"]["ids increasing along the restore %s" % (ids == sorted(ids))] += 1

    # ---- 56, 58
    def special(self, name, L):
        for k, (ln, tag, d) in enumerate(L):
            if tag != "MR0":
                continue
            r = RM.mrec_parse(d["b"])
            fl = r["fl"]
            if r["c8"] & 0x100 or (fl & 0x400 and fl & 0x180):
                continue
            path = "minion" if fl & 0x20 else ("special" if fl & 1 else None)
            if path is None:
                continue
            mrc = next((L[j][2] for j in range(k + 1, min(len(L), k + 60)) if L[j][1] in ("MRC", "MR0", "RSM")), None)
            if mrc is None or "path" not in mrc or not mrc.get("u"):
                self.c["special"]["%s: no creation logged" % path] += 1
                continue
            sec = "special" if path == "special" else "minion"
            self.note(sec, "%s: mode 1 (record flag 4 %s)" % (path, "set" if fl & 4 else "clear"), mrc["m"] == 1,
                      "%s:%d" % (name, ln))
            at = (mrc["x"], mrc["y"]) == (r["x"], r["y"])
            kr = RM.steps_between(RM.seed_t(d["rs"]), RM.seed_t(mrc["rs"]), 400)
            self.c[sec + "-detail"]["%s: path %s, at the record's x, y %s, room draws %s" % (path, "+".join(mrc["path"]), at, kr)] += 1
            if path == "minion" and kr == 3:
                self.note("minion", "minion, 3 room draws (the first try, radius -1): at the record's x, y", at,
                          "%s:%d" % (name, ln))
            if path == "special" and fl & 0x20:
                self.note("special", "flag 0x20 and 1: minion path", False)

    # ---- 59
    def wrorder(self, name, L):
        for k, (ln, tag, d) in enumerate(L):
            if tag != "MRC" or not d.get("u"):
                continue
            seq = []
            for j in range(k + 1, min(len(L), k + 80)):
                t = L[j][1]
                if t in ("MRS", "MRE", "MRX"):
                    seq.append(t)
                if t in ("MRX", "MR0", "RSM"):
                    break
            self.c["wrorder"]["after MRC: %s" % ",".join(seq)] += 1

    # ---- 78
    def preset(self, name, L):
        block = None       # (kind, d) of the current walk block
        withpsu = set()
        for k, (ln, tag, d) in enumerate(L):
            if tag == "WG":
                fl = d["fl"]
                kind = "populate" if not fl & 1 else ("restore only" if not fl & 2 else "nothing")
                rs = next((e for _, t, e in L[k + 1:k + 400] if t in ("RS0", "WG", "RP")), None)
                dd = rs["d"] if rs is not None and "gs" in rs and rs.get("r") == d["r"] else None
                block = [kind, dd, 0]
                if kind == "restore only" and dd in withpsu:
                    self.c["preset"]["restore-only walk of a room whose populate walk had a PSU0"] += 1
                    self.note("preset", "  no PSU0 in it", True)
                    block.append("sep")
            elif tag in ("RP", "CRC", "RM0"):
                if block and len(block) > 3 and block[2]:
                    self.note("preset", "  no PSU0 in it", False, "%s:%d" % (name, ln))
                block = None
            elif tag == "PSU0":
                if block is None:
                    self.c["preset"]["PSU0 outside a walk block"] += 1
                    continue
                self.note("preset", "PSU0 in a walk block: populate only", block[0] == "populate",
                          "%s:%d %s" % (name, ln, block[0]))
                block[2] += 1
                if block[1] is not None:
                    withpsu.add(block[1])

    def report(self, w):
        for sec in sorted(self.c):
            w("== %s%s" % (sec, (" (bad %d)" % self.bad[sec]) if sec in self.bad or "-" not in sec else ""))
            for k, v in sorted(self.c[sec].items(), key=lambda kv: str(kv[0])):
                w("  %-110s %7s" % (k, v))
            for e in self.ex[sec]:
                w("  example: %s" % e)
        w("S7d total bad=%d" % sum(self.bad.values()))


class Run(RM.Checker):
    def __init__(self, T, obs):
        super().__init__(T, False)
        self.obs = obs
        self.town_follow = []
        self.items_saved = []
        self.item_bytes = {}
        self.mrecs = {}
        self.lids_restored = collections.Counter()

    def log(self, name, L):
        super().log(name, L)
        self.obs.log(name, L)


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["check"])
    ap.add_argument("--out")
    ap.add_argument("--logs", nargs="*")
    a = ap.parse_args(argv)
    S = S7d()
    C = Run(RM.Tables(RM.DEFAULT_EXCEL), S)
    for p in (a.logs or LOGS):
        C.run(p)
    buf = io.StringIO()
    with redirect_stdout(buf):
        ctl = C.report()
    out = open(a.out, "w") if a.out else sys.stdout
    w = (lambda s="": out.write(s + "\n"))
    summ = [x for x in buf.getvalue().splitlines() if x.startswith("SUMMARY") or "MISMATCHES" in x or x.startswith("  ") and ": " in x and "mismatch" in x.lower()]
    w("== control: tools/rooms.py Checker, unchanged")
    for x in summ:
        w("  " + x.strip())
    S.report(w)
    w("control_bad=%d" % ctl)
    if a.out:
        out.close()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
