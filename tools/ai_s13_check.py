#!/usr/bin/env python3
"""State row 13 (`AiSt13`, The Countess): the block of docs/specs/monsters/ai/catalogue.md S13 against the kept logs. No game.

Written after tools/ai_t28_check.py. It runs the block as written, as a second reading, for each logged decision of state 13:
from the AID line's inputs and the logged results of the boundary calls it checks every boundary call (function, return
address, the words the block states), the unit seed at each call and at AIX, and AiCtl +0x14, +0x18, +0x1C. It also chains
AiCtl +0x14 and +0x18 from one decision's end to the unit's next AID line. It runs no game code; an arm no log reaches is
checked by nothing here, and PATH says which arms the logs reach.

The list behind `AiPathSkillStep` (AiCtl +0x38) is not logged. Its count is taken per unit, per log, from the fires themselves
(the highest fired index + 1), so "v14 < count" can fail only at an index below that; it is an oracle from the log, not a
prediction. Its points are logged only at fires: LIST prints them, and the check requires one point per index in a unit.

Controls: --control NAME changes one rule of the block and must fail decisions, or says that no log separates it.
  no-ten       the A1 test r < aip(3), without the 10
  melee-swap   the melee test reversed
  no-reset     v14 never reset after 700 frames
  reset-1400   the reset at 1400 frames for 700
  no-v18       v18 not written at a fire
  draw-first   the draw made before AiPathSkillStep
  mode-sk1     the fire's mode from Sk1mode for the pushed 4 (a stock class-45 Sk1mode of 4 cannot tell)
  idle-aip1    Idle's argument from aip(1) for aip(2)
  no-step4     the target's region test skipped
  no-step3     the home's region test against the unit's replaced by "differ"
  limit-0      the home distance limit 0 for 40
  limit-20     the home distance limit 20 for 40
  limit-28     the home distance limit 28 for 40 (the logs' largest distance is 29)
  limit-29     the home distance limit 29 for 40: passes, and that is what it says: 30..40 is read, not separated
  ovr-byte     Ovr(0, 100, 0) as Ovr(13, 100, 0)

    python3 -I tools/ai_s13_check.py [--control NAME] LOG...
    python3 -I tools/ai_s13_check.py --r10 [two-draws] LOG...      row 10's own think, state 0 (R10's block)
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import ai  # noqa: E402
import ai_resume  # noqa: E402

ROOM, HEAD, REGION, HOMEDIST = 0x00620BB0, 0x0058EEF0, 0x0061B130, 0x005DC5C0
PATHSET, RUNPT, CANCEL, SKILL, MODE, IDLE, OVR, RUNUNIT = 0x005A6260, 0x005DEDE0, 0x00540E60, 0x005DEAD0, 0x005DDF90, 0x005DE080, 0x005DE190, 0x005DED20
BINS = ((0, 4), (5, 9), (10, 14), (15, 19), (20, 24), (25, 29), (30, 10 ** 9))


class Mis(Exception):
    pass


class Stop(Exception):
    pass


def s32(v):
    return v - (1 << 32) if v >= (1 << 31) else v


def s16(v):
    return v - (1 << 16) if v >= (1 << 15) else v


class Run:
    def __init__(self, dec, control, count):
        self.dec, self.control, self.count = dec, control, count
        a = dec["aid"]
        self.a = a
        self.calls = ai_resume.top_level(dec)
        self.i = 0
        self.seed = ai.seedval(a["s"])
        ctl = bytes.fromhex(a["ctl"])
        self.v14 = s32(int.from_bytes(ctl[0x14:0x18], "little"))
        self.v18 = s32(int.from_bytes(ctl[0x18:0x1C], "little"))
        self.v1c = s32(int.from_bytes(ctl[0x1C:0x20], "little"))
        raw = bytes.fromhex(a["aip"])
        self.aips = [s16(int.from_bytes(raw[i:i + 2], "little")) for i in range(0, len(raw), 2)]
        sk = bytes.fromhex(a["sk"])
        self.skill1 = s16(int.from_bytes(sk[0:2], "little"))
        self.sk1mode = sk[16]
        self.d = a["diff"]
        self.t = a["ctx"][2]
        self.dist = s32(a["ctx"][5])
        self.melee = a["ctx"][6]
        self.T = a["fr"]
        self.path = []

    def aip(self, k):
        return self.aips[3 * (k - 1) + self.d]

    def call(self, fn, ra, ecx=None, edx=None, args=None):
        if self.i >= len(self.calls):
            raise Stop("log ends")
        b = self.calls[self.i]
        self.i += 1
        if b["fn"] != fn or b["ra"] != ra:
            raise Mis("call %d: block %x@%x, log %x@%x" % (self.i, fn, ra, b["fn"], b["ra"]))
        if ai.seedval(b["s"]) != self.seed:
            raise Mis("call %d %x@%x: seed %s, log %s" % (self.i, fn, ra, self.seed, b["s"]))
        if list(b["c"]) != [self.v14, self.v18, self.v1c]:
            raise Mis("call %d %x@%x: ctl %s, log %s" % (self.i, fn, ra, [self.v14, self.v18, self.v1c], b["c"]))
        if ecx is not None and b["ecx"] != ecx:
            raise Mis("call %d %x@%x: ecx %x, log %x" % (self.i, fn, ra, ecx, b["ecx"]))
        if edx is not None and b["edx"] != edx:
            raise Mis("call %d %x@%x: edx %x, log %x" % (self.i, fn, ra, edx, b["edx"]))
        if args is not None and list(b["a"][:len(args)]) != list(args):
            raise Mis("call %d %x@%x: args %s, log %s" % (self.i, fn, ra, args, b["a"][:len(args)]))
        air = self.dec["air"].get(b["n"])
        if air is None:
            raise Stop("no return logged")
        self.seed = ai.seedval(air["s"])
        return air

    def draw(self):
        self.seed = ai.step(self.seed)
        return self.seed[0] % 100

    def step_path(self):
        """AiPathSkillStep; True when a point was fired. The list's words come from the call: an oracle, see the docstring."""
        if self.v14 < self.count:
            b = self.calls[self.i] if self.i < len(self.calls) else None
            pt = (b["a"][3], b["a"][4]) if b else (None, None)
            mode = self.sk1mode if self.control == "mode-sk1" else 4
            self.path.append("fire")
            self.call(SKILL, 0x005E5C02, edx=self.a["u"], args=[mode, self.skill1, 0, pt[0], pt[1]])
            self.v14 += 1
            if self.control != "no-v18":
                self.v18 = self.T
            return True
        limit = 1400 if self.control == "reset-1400" else 700
        self.gap = abs(self.T - self.v18)
        if self.gap > limit and self.control != "no-reset":
            self.v14 = 0
            self.path.append("reset")
        return False

    def run_home(self, ra_set, ra_run):
        self.path.append("runhome@%x" % ra_set)
        self.call(PATHSET, ra_set, edx=1, args=[0, 0])
        r = self.call(RUNPT, ra_run, edx=self.a["u"], args=[self.hx, self.hy])["eax"]
        if r:
            return True
        raise Stop("MonAiRunToPoint refused: CancelEvents and the fall-through are not modelled, no log reaches them")

    def think(self):
        u, a = self.a["u"], self.a
        if not a["ctx"][7]:
            raise Stop("M = 0")
        room = self.call(ROOM, 0x005E5C77, args=[u])["eax"]
        if not room:
            self.path.append("no-room")
            return
        air = self.call(HEAD, 0x005E5CA2, ecx=u, edx=10, args=[0])
        if not air["eax"]:
            raise Stop("no home record: the push is not modelled, no log reaches it")
        if air["eax"] != a["hp"] or not a["head"]:
            raise Stop("the home record is not the logged head")
        head = bytes.fromhex(a["head"])
        if int.from_bytes(head[8:12], "little") != 10:
            raise Mis("the head record's key is not 10")
        self.hx, self.hy = int.from_bytes(head[12:16], "little"), int.from_bytes(head[16:20], "little")
        if not self.hx or not self.hy:
            raise Stop("a zero home word: the refill is not modelled, no log reaches it")
        rh = self.call(REGION, 0x005E5D54, args=[room, self.hx, self.hy])["eax"]
        ru = self.call(REGION, 0x005E5DB8, args=[room, a["x"], a["y"]])["eax"]
        differ = rh != ru
        if self.control == "no-step3":
            differ = True
        if differ:
            if self.run_home(0x005E5DDE, 0x005E5DF2):
                return
        t = a["t"]
        rt = self.call(REGION, 0x005E5E7B, args=[room, t[4], t[5]])["eax"]
        if rt != rh and self.control != "no-step4":
            self.path.append("region-t")
            if a["x"] == self.hx and a["y"] == self.hy:
                self.path.append("at-home")
                if self.dist < 25 and self.step_path():
                    return
                self.path.append("idle10")
                self.call(IDLE, 0x005E5EC2, edx=u, args=[10])
                return
            if self.run_home(0x005E5EEC, 0x005E5EFD):
                return
        self.homedist = self.call(HOMEDIST, 0x005E5F1F, ecx=u, edx=self.hx, args=[self.hy])["eax"]
        limit = {"limit-0": 0, "limit-20": 20, "limit-28": 28, "limit-29": 29}.get(self.control, 40)
        if self.homedist > limit:
            if self.run_home(0x005E5F45, 0x005E5F56):
                return
        r = None
        if self.control == "draw-first":
            r = self.draw()
        if self.step_path():
            return
        if r is None:
            r = self.draw()
        m = bool(self.melee)
        if self.control == "melee-swap":
            m = not m
        idle = self.aip(1) if self.control == "idle-aip1" else self.aip(2)
        if m:
            lim = self.aip(3) if self.control == "no-ten" else self.aip(3) + 10
            if r < lim:
                self.path.append("melee-a1")
                self.call(MODE, 0x005E5FB2, edx=u, args=[4, self.t])
            else:
                self.path.append("melee-idle")
                self.call(IDLE, 0x005E5FC8, edx=u, args=[idle])
        else:
            if r < self.aip(1):
                self.path.append("far-run")
                self.call(OVR, 0x005E5FE7, ecx=u, edx=13 if self.control == "ovr-byte" else 0, args=[100, 0])
                self.call(RUNUNIT, 0x005E5FF4, edx=u, args=[self.t])
            else:
                self.path.append("far-idle")
                self.call(IDLE, 0x005E600C, edx=u, args=[idle])


def row10(argv):
    """Row 10's own think (state 0), R10's block, the same way. `MonPlayerBonus`'s difficulty word is min(d, 2) as a reading: all
    logged decisions are Normal, so it is 0 in each. Control `--r10 two-draws` makes the near arm's second draw from the first."""
    two = argv[0] == "two-draws"
    logs = argv[1:] if two else argv
    n = ok = mis = stop = 0
    paths, msgs = {}, []
    SITES = {"far": (0x005F0B61, 0x005F0B70)}
    for p in logs:
        for d in ai.parse(p)["dec"]:
            a = d["aid"]
            if a["ai"] != 10 or a["st"] != 0:
                continue
            n += 1
            r = Run(d, None, 0)
            u = a["u"]
            try:
                if r.call(ROOM, 0x005F0B2C, args=[u])["eax"] == 0:
                    raise Stop("no room")
                th = 20 - 3 * min(r.d, 2)
                if r.dist > th:
                    r.path.append("far-run")
                    r.call(OVR, SITES["far"][0], ecx=u, edx=13, args=[r.aip(4), 0])
                    r.call(0x005DEFB0, SITES["far"][1], edx=u, args=[r.t, 3])
                elif r.melee:
                    if r.draw() < r.aip(3):
                        r.path.append("melee-a1")
                        r.call(MODE, 0x005F0BCD, edx=u, args=[4, r.t])
                    else:
                        r.path.append("melee-idle")
                        r.call(IDLE, 0x005F0BE3, edx=u, args=[r.aip(2)])
                else:
                    x = r.draw()
                    if x >= r.aip(1):
                        r.path.append("near-idle")
                        r.call(IDLE, 0x005F0CB8, edx=u, args=[r.aip(2)])
                    elif (x if two else r.draw()) < r.aip(5):
                        r.path.append("near-run")
                        r.call(OVR, 0x005F0C75, ecx=u, edx=13, args=[r.aip(4), 0])
                        r.call(0x005DEFB0, 0x005F0C84, edx=u, args=[r.t, 3])
                    else:
                        r.path.append("near-walk")
                        r.call(0x005DEC80, 0x005F0C9C, edx=u, args=[r.t, 7])
                if r.i != len(r.calls):
                    raise Mis("%d logged calls left" % (len(r.calls) - r.i))
                x = d.get("aix") or {}
                if x.get("s") and ai.seedval(x["s"]) != r.seed:
                    raise Mis("exit seed %s, log %s" % (r.seed, x["s"]))
                ok += 1
                for q in r.path:
                    paths[q] = paths.get(q, 0) + 1
            except Mis as e:
                mis += 1
                if len(msgs) < 4:
                    msgs.append("MIS %s id=%d fr=%d %s" % (os.path.basename(p), a["id"], a["fr"], e))
            except Stop as e:
                stop += 1
                if len(msgs) < 4:
                    msgs.append("STOP %s id=%d fr=%d %s" % (os.path.basename(p), a["id"], a["fr"], e))
    if msgs:
        print("\n".join(msgs))
    for q in sorted(paths):
        print("R10PATH %s %d" % (q, paths[q]))
    print("SURVEY ai_r10_check control=%s decisions=%d ok=%d mismatches=%d stopped=%d" % ("two-draws" if two else None, n, ok, mis, stop))


def main(argv):
    if argv and argv[0] == "--r10":
        return row10(argv[1:])
    control = None
    if argv and argv[0] == "--control":
        control = argv[1]
        argv = argv[2:]
    decs = []
    for p in argv:
        for d in ai.parse(p)["dec"]:
            if d["aid"]["st"] == 13:
                decs.append((os.path.basename(p), d))
    # the list, from the fires
    lists = {}
    for p, d in decs:
        e = lists.setdefault((p, d["aid"]["id"]), {"pts": {}, "first": d["aid"]["fr"], "last": d["aid"]["fr"], "n": 0, "start": None})
        e["last"] = d["aid"]["fr"]
        e["n"] += 1
        ctl = bytes.fromhex(d["aid"]["ctl"])
        if e["start"] is None:
            e["start"] = (s32(int.from_bytes(ctl[0x14:0x18], "little")), s32(int.from_bytes(ctl[0x18:0x1C], "little")))
        for b in ai_resume.top_level(d):
            if b["fn"] == SKILL and b["ra"] == 0x005E5C02:
                e["pts"].setdefault(b["c"][0], set()).add((b["a"][3], b["a"][4]))
    n = ok = mis = stop = 0
    paths, msgs, cross, hd, chain = {}, [], {}, [], {"pairs": 0, "bad": 0}
    gaps_reset, gaps_kept, cmds = [], [], {}
    prev = {}
    for p, d in decs:
        a = d["aid"]
        n += 1
        pts = lists[(p, a["id"])]["pts"]
        r = Run(d, control, max(pts) + 1 if pts else 0)
        key = (p, a["id"])
        if key in prev:
            chain["pairs"] += 1
            if prev[key] != (r.v14, r.v18):
                chain["bad"] += 1
                if len(msgs) < 6:
                    msgs.append("CHAINBAD %s id=%d fr=%d model %s log %s" % (p, a["id"], a["fr"], prev[key], (r.v14, r.v18)))
        try:
            r.think()
            if r.i != len(r.calls):
                raise Mis("%d logged calls left" % (len(r.calls) - r.i))
            x = d.get("aix") or {}
            if x.get("s") and ai.seedval(x["s"]) != r.seed:
                raise Mis("exit seed %s, log %s" % (r.seed, x["s"]))
            ok += 1
            prev[key] = (r.v14, r.v18)
            for q in r.path:
                paths[q] = paths.get(q, 0) + 1
                b = next(i for i, (lo, hi) in enumerate(BINS) if lo <= r.dist <= hi) if r.dist >= 0 else 6
                cross.setdefault(q, [0] * len(BINS))[b] += 1
            if hasattr(r, "homedist"):
                hd.append(r.homedist)
            if hasattr(r, "gap"):
                (gaps_reset if "reset" in r.path else gaps_kept).append(r.gap)
            if r.path:
                k = (r.path[-1], d["msm"][0][0]["cmd"][0] if d["msm"] else None, d["msm"][0][0]["cmd"][5] if d["msm"] else None)
                cmds[k] = cmds.get(k, 0) + 1
        except Mis as e:
            mis += 1
            prev.pop(key, None)
            if len(msgs) < 6:
                msgs.append("MIS %s id=%d fr=%d %s" % (p, a["id"], a["fr"], e))
        except Stop as e:
            stop += 1
            prev.pop(key, None)
            if len(msgs) < 6:
                msgs.append("STOP %s id=%d fr=%d %s" % (p, a["id"], a["fr"], e))
    if msgs:
        print("\n".join(msgs))
    if control is None:
        # who holds which state: AID and AIN lines of every unit, per log
        for p0 in argv:
            r0 = ai.parse(p0)
            per = {}
            for d in r0["dec"]:
                a = d["aid"]
                e = per.setdefault(a["id"], {"st": set(), "c": a["c"], "n": 0, "fr": a["fr"], "last": a["fr"], "hd": bool(a["hp"]), "sq": []})
                e["st"].add(a["st"])
                e["n"] += 1
                e["last"] = a["fr"]
            for x in r0["ain"]:
                if x["id"] in per:
                    per[x["id"]]["st"].add(x["st"])
            two = sum(1 for e in per.values() if len(e["st"]) > 1)
            print("STATES %s units=%d units_with_two_states=%d" % (os.path.basename(p0), len(per), two))
            for i, e in sorted(per.items()):
                if e["c"] == 45:
                    print("  C45 id=%d states=%s decisions=%d frames=%d..%d head_record=%s" % (i, sorted(e["st"]), e["n"], e["fr"], e["last"], e["hd"]))
        for p, d in decs[:1] + [x for x in decs if x[0] != decs[0][0]][:3]:
            a = d["aid"]
            print("FIRST %s id=%d fr=%d dist=%d melee=%d calls=%s" % (p, a["id"], a["fr"], s32(a["ctx"][5]), a["ctx"][6], ["%x" % b["ra"] for b in ai_resume.top_level(d)][-2:]))
        for (p, i), e in sorted(lists.items()):
            print("UNIT %s id=%d decisions=%d frames=%d..%d first_v14=%d first_v18=%d count_from_fires=%s multi_point_indices=%d" % (
                p, i, e["n"], e["first"], e["last"], e["start"][0], e["start"][1], max(e["pts"]) + 1 if e["pts"] else 0,
                sum(1 for v in e["pts"].values() if len(v) > 1)))
            print("LIST %s id=%d %s" % (p, i, " ".join("%d:%d,%d" % (k, *sorted(v)[0]) for k, v in sorted(e["pts"].items()))))
        print("BINS " + " ".join("%d-%s" % (lo, hi if hi < 10 ** 8 else "") for lo, hi in BINS))
        for q in sorted(paths):
            print("PATH %s %d by_dist=%s" % (q, paths[q], cross[q]))
        print("HOMEDIST n=%d min=%d max=%d" % (len(hd), min(hd), max(hd)))
        print("CHAIN unit_pairs=%d bad=%d" % (chain["pairs"], chain["bad"]))
        print("RESETGAP at_resets=%s largest_without_reset=%d" % (sorted(gaps_reset), max(gaps_kept)))
        for k in sorted(cmds, key=str):
            print("CMD arm=%s msm0_mode=%s msm0_pathtype=%s n=%d" % (k[0], k[1], k[2], cmds[k]))
    print("SURVEY ai_s13_check control=%s decisions=%d ok=%d mismatches=%d stopped=%d chain_bad=%d" % (control, n, ok, mis, stop, chain["bad"]))


if __name__ == "__main__":
    main(sys.argv[1:])
