"""Tests of tools/skills.py (plan 0045 Phase 2): the LCG step and distance, the payment (cost, floor, refusal, a
non-player), a missile creation (velocity, range, seeds, the owner's critical draws, the pierce count) and a missile
frame (the fifth-step acceleration, the position step), each on hand-built log lines and checked both ways (the right
values pass, a wrong one is a mismatch). The model tests read the stock tables (workspace/merged/data/global/excel) and
skip without them. Stdlib only.

    python3 -I tools/test_skills.py
"""
import json
import os
import struct
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import skills  # noqa: E402

HAVE_EXCEL = os.path.isdir(skills.DEFAULT_EXCEL)


def write_log(lines):
    fd, path = tempfile.mkstemp(suffix=".log")
    with os.fdopen(fd, "w") as fh:
        for tag, d in lines:
            fh.write("%s %s\n" % (tag, json.dumps(d)))
    return path


class Lcg(unittest.TestCase):
    def test_step(self):
        # RNG spec: low' = low * 0x6AC690C5 + high (64-bit), split
        v = 1 * 0x6AC690C5 + 0x29A
        self.assertEqual(skills.step((1, 0x29A)), (v & 0xFFFFFFFF, v >> 32))
        t = (5, 0x29A)
        for _ in range(7):
            t = skills.step(t)
        self.assertEqual(skills.steps_between((5, 0x29A), t), 7)

    def test_tdiv(self):
        self.assertEqual(skills.tdiv(-7, 2), -3)
        self.assertEqual(skills.tdiv(7, 2), 3)


@unittest.skipUnless(HAVE_EXCEL, "stock tables not extracted")
class Model(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.T = skills.Tables()

    def run_lines(self, lines):
        p = write_log(lines)
        try:
            C = skills.Checker(self.T)
            C.run(p)
            return C
        finally:
            os.unlink(p)

    def pay_lines(self, sid, lvl, m0, m1, r, t=0):
        return [("SDO0", {"u": {"u": 100, "t": t, "c": 1, "id": 1, "m": 10, "s": "00000001:0000029a"},
                          "a": [sid, lvl, 1, 0, 0], "n": 1}),
                ("PAY0", {"u": 100, "a": [sid, lvl], "st": {"8": m0}, "n": 2}),
                ("PAY1", {"k": 2, "r": r, "st": {"8": m1}, "n": 3}),
                ("SDO1", {"k": 1, "r": 1, "s": "00000001:0000029a", "st": {}, "n": 4})]

    def test_pay(self):
        # Teleport (54): mana 24, lvlmana -1, manashift 8: level 1 costs 24 << 8 = 6144 (the dev log's payment)
        C = self.run_lines(self.pay_lines(54, 1, 2048000, 2041856, 1))
        self.assertEqual((C.ok["PAY"], sum(C.bad.values())), (1, 0))
        C = self.run_lines(self.pay_lines(54, 1, 2048000, 2041855, 1))
        self.assertEqual(C.bad["PAY"], 1)
        # level 25: (24 - 1 * 24) << 8 = 0, floored at minmana 1 * 256
        r = self.T.srec(54)
        self.assertEqual((r["mana"], r["lvlmana"], r["shift"], r["minmana"]), (24, -1, 8, 1))
        C = self.run_lines(self.pay_lines(54, 25, 1000, 744, 1))
        self.assertEqual((C.ok["PAY"], C.info["PAY floor binds"]), (1, 1))
        # cost above the mana: nothing taken, result 0 (ignored by the caller)
        C = self.run_lines(self.pay_lines(54, 1, 100, 100, 0))
        self.assertEqual((C.ok["PAY"], C.info["PAY refused (cost above mana)"]), (1, 1))
        # a monster pays nothing and gets 1
        C = self.run_lines(self.pay_lines(54, 1, 0, 0, 1, t=1))
        self.assertEqual((C.ok["PAY"], C.info["PAY non-player"]), (1, 1))

    def mc_lines(self, cls, lvl, path, md, mseed, owner_s, owner_after, ost=None, mst=None, b328=0, pre="00000005:00000007"):
        blk = bytearray(0x5C)
        struct.pack_into("<I", blk, 0, 0x21)
        struct.pack_into("<I", blk, 4, 200)
        struct.pack_into("<i", blk, 0x10, cls)
        struct.pack_into("<ii", blk, 0x2C, 0, lvl)
        post = skills.sd_fmt(skills.step(skills.sd_parse(pre)))
        o = {"u": 200, "t": 1, "c": 160, "id": 9, "m": 4, "s": owner_s, "st": ost or {}, "b328": b328}
        return [("MC0", {"p": blk.hex(), "o": o, "src": None, "fr": 10, "n": 1}),
                ("SU0", {"u": 300, "t": 3, "c": cls, "p": 1, "pre": pre, "n": 2}),
                ("SU1", {"u": 300, "p": 1, "post": post, "s": mseed or "%s:0000029a" % post[:8], "u28": 0, "n": 3}),
                ("MC1", {"k": 1, "m": {"u": 300, "t": 3, "c": cls, "id": 1, "m": 3,
                                       "s": mseed or "%s:0000029a" % post[:8], "st": mst or {}, "b328": 0,
                                       "path": path, "md": md}, "so": owner_after, "ss": None, "n": 4})]

    def test_mc_arrow(self):
        # arrow (13): Vel 14 -> (14 << 8) * 75 / 100 = 2688, MaxVel 14 -> 3584, range 40, SrcDamage 128: one
        # critical draw on the owner's seed (stats 337 and 141 zero, no mastery), Pierce with stats 166/156 zero
        own = "65031f47:06897ace"
        after = skills.sd_fmt(skills.step(skills.sd_parse(own)))
        path = {"v": 2688, "mx": 3584, "a": 0}
        md = {"act": 40, "sk": 0, "lv": 1, "rng": 40, "rem": 40}
        C = self.run_lines(self.mc_lines(13, 1, path, md, None, own, after))
        self.assertEqual(sum(C.bad.values()), 0, C.miss)
        self.assertEqual((C.ok["MC.vel"], C.ok["MC.owner"], C.ok["MC.seed"], C.ok["MC.pierce"]), (1, 1, 1, 1))
        C = self.run_lines(self.mc_lines(13, 1, path, md, None, own, own))          # no draw: a mismatch
        self.assertEqual(C.bad["MC.owner"], 1)
        C = self.run_lines(self.mc_lines(13, 1, dict(path, v=2689), md, None, own, after))
        self.assertEqual(C.bad["MC.vel"], 1)
        C = self.run_lines(self.mc_lines(13, 1, path, md, "00000001:0000029a", own, after))
        self.assertEqual(C.bad["MC.seed"], 1)

    def test_mc_pierce(self):
        # pierce chance 50: the local seed Init(b328) stepped while low % 100 < 50, at most four times
        own = "65031f47:06897ace"
        after = skills.sd_fmt(skills.step(skills.sd_parse(own)))
        t, cnt = (77, 0x29A), 0
        for _ in range(4):
            t = skills.step(t)
            if t[0] % 100 < 50:
                cnt += 1
            else:
                break
        path = {"v": 2688, "mx": 3584, "a": 0}
        md = {"act": 40, "sk": 0, "lv": 1, "rng": 40, "rem": 40}
        C = self.run_lines(self.mc_lines(13, 1, path, md, None, own, after, ost={"166": 50}, b328=77,
                                         mst={"328": cnt} if cnt else {}))
        self.assertEqual(C.ok["MC.pierce"], 1, C.miss)
        C = self.run_lines(self.mc_lines(13, 1, path, md, None, own, after, ost={"166": 50}, b328=77,
                                         mst={"328": cnt + 1}))
        self.assertEqual(C.bad["MC.pierce"], 1)

    def mf_lines(self, p0, p1, rem=(40, 39)):
        md0, md1 = {"rem": rem[0]}, {"rem": rem[1]}
        return [("MF0", {"m": 5, "fr": 1, "path": p0, "md": md0, "s": "00000001:0000029a", "do": 1, "n": 1}),
                ("MF1", {"m": 5, "r": 1, "path": p1, "md": md1, "s": "00000001:0000029a", "n": 2})]

    def test_mf(self):
        # the dev log's first windowed step: v 1536, dir (-3811, 1500): s = (1536 * 0x400) >> 6 = 24576,
        # dx = (-3811 * 24576) >> 12 = -22866, dy = 9000
        p0 = {"x": 354582528, "y": 313098240, "v": 1536, "mx": 2048, "a": 0, "cnt": 0, "dx": -3811, "dy": 1500}
        p1 = dict(p0, x=354559662, y=313107240)
        C = self.run_lines(self.mf_lines(p0, p1))
        self.assertEqual((C.ok["MF.pos"], C.ok["MF.vel"], C.ok["MF.left"], sum(C.bad.values())), (1, 1, 1, 0))
        C = self.run_lines(self.mf_lines(p0, dict(p1, x=354559663)))
        self.assertEqual(C.bad["MF.pos"], 1)
        # acceleration: the counter at 4 reaches the fifth step, v += accel (negative), the counter restarts
        q0 = dict(p0, v=5000, a=-1000, cnt=4, mx=6000)
        s = (4000 * 0x400) >> 6
        q1 = dict(q0, v=4000, cnt=0, x=q0["x"] + ((-3811 * s) >> 12), y=q0["y"] + ((1500 * s) >> 12))
        C = self.run_lines(self.mf_lines(q0, q1))
        self.assertEqual((C.ok["MF.vel"], C.ok["MF.pos"], C.info["MF fifth steps (C3)"]), (1, 1, 1), C.miss)
        # a per-frame acceleration (the contradicted lead) would give v 4000 at the first step: a mismatch here
        r0 = dict(q0, cnt=0)
        C = self.run_lines(self.mf_lines(r0, dict(q1, cnt=0)))
        self.assertEqual(C.bad["MF.vel"], 1)

    def test_sl(self):
        # Raise Skeleton at owner level 86, skill level 20: min(max(86 * 3 / 4 + 20, 1), 86) = 84 (case C1); the
        # caster's level (the contradicted lead) is a mismatch
        def lines(got, lvl=0, L=86):
            return [("SL0", {"m": 7, "o": 8, "a": [7, lvl, 20], "m12": 0, "o12": L, "n": 1}),
                    ("SL1", {"k": 1, "m12": got, "n": 2})]
        C = self.run_lines(lines(84))
        self.assertEqual((C.ok["SL.level"], C.info["SL from the owner's level (C1)"]), (1, 1))
        self.assertEqual(self.run_lines(lines(86)).bad["SL.level"], 1)
        self.assertEqual(self.run_lines(lines(5, lvl=5)).ok["SL.level"], 1)
        self.assertEqual(self.run_lines(lines(3, L=3)).ok["SL.level"], 1)        # 2 + 20 capped at 3

    def test_rsk(self):
        # do 31's class draw (0x005C4430): one caster step for class 363 at level > 2, none at level 2; 364 always one
        s0 = (0x1234, 0x29A)
        s1 = skills.sd_fmt(skills.step(s0))

        def lines(c, lvl, after):
            return [("SDO0", {"u": {"u": 100, "t": 0, "c": 2, "id": 1, "m": 10, "s": skills.sd_fmt(s0)},
                              "a": [70, lvl, 1, 0, 0], "n": 1}),
                    ("SP1", {"k": 9, "m": {"u": 7, "c": c}, "so": skills.sd_fmt(s0), "n": 2}),
                    ("RSK0", {"u": 100, "s": skills.sd_fmt(s0), "m": 7, "c": c, "n": 3}),
                    ("RSK1", {"k": 3, "s": after, "n": 4}),
                    ("SDO1", {"k": 1, "r": 1, "s": after, "st": {}, "n": 5})]
        C = self.run_lines(lines(363, 20, s1))
        self.assertEqual((C.ok["RSK.seed"], C.ok["SDO.seed"], sum(C.bad.values())), (1, 1, 0))
        self.assertEqual(self.run_lines(lines(363, 2, skills.sd_fmt(s0))).ok["RSK.seed"], 1)
        self.assertEqual(self.run_lines(lines(363, 2, s1)).bad["RSK.seed"], 1)
        self.assertEqual(self.run_lines(lines(364, 1, s1)).ok["RSK.seed"], 1)
        self.assertEqual(self.run_lines(lines(363, 20, skills.sd_fmt(s0))).bad["SDO.seed"], 1)


    # ---- part 2 (lane/p45k): MonAttackStats, the handlers, SKILLS_CanUse, the summon's seed
    def test_mas(self):
        # a class with an El1 attack in some mode at a chance below 100 (Normal): one RNG_Range(100) on the unit seed;
        # the stats written are 21, 22, 19 and, when the roll is below the chance, El1's type stats
        T = self.T
        cls = next(c for c in range(len(T.ms)) if T.ms[c][0xFE] and 0 < T.ms[c][0x104] < 100 and
                   T.ms[c][0x101] not in (0, 10) and not T.ms[c][0x0C] & 4 and
                   struct.unpack_from("<H", T.ms[c], 0xA8)[0] == 0xFFFF)
        mode = T.ms[cls][0xFE]
        C0 = skills.Checker(T)
        s0 = (0x1000, 0x29A)
        w, t, draws, notes = C0.mas_model(cls, 10, 0, 1, mode, s0)
        self.assertEqual((draws, t), (1, skills.step(s0)))

        def lines(st1, seed1):
            u = {"u": 5, "t": 1, "c": cls, "id": 3, "m": 1, "s": skills.sd_fmt(s0), "st": {"12": 10}}
            return [("MAS0", {"mode": mode, "u": u, "fr": 1, "diff": 0, "g": [3, 0, 1, 0], "n": 1}),
                    ("MAS1", {"k": 1, "s": seed1, "st": st1, "n": 2})]
        st1 = {"12": 10}
        st1.update({str(k): v for k, v in w.items() if v})
        C = self.run_lines(lines(st1, skills.sd_fmt(t)))
        self.assertEqual((C.ok["MAS.seed"], C.ok["MAS.stats"], sum(C.bad.values())), (1, 1, 0))
        self.assertEqual(self.run_lines(lines(st1, skills.sd_fmt(s0))).bad["MAS.seed"], 1)
        st_bad = dict(st1)
        st_bad["21"] = st_bad.get("21", 0) + 1
        self.assertEqual(self.run_lines(lines(st_bad, skills.sd_fmt(t))).bad["MAS.stats"], 1)

    def test_handler(self):
        # open wounds (0x005BFE60): one draw on the handler's unit; mana after kill (0x005C0130): none, mana += v << 8
        s0 = (0x2000, 0x29A)

        def ev(fn, sv, after, st0=None, st1=None, e=5):
            return [("EVH", {"fn": fn, "e": e, "u": {"u": 1, "t": 0, "c": 4, "id": 1, "m": 1, "s": skills.sd_fmt(s0),
                                                    "st": st0 or {}}, "o": 2, "par": 135 << 16, "so": "0:0",
                             "sv": sv, "ot": {"u": 2, "t": 1, "c": 5, "id": 9}, "n": 1}),
                    ("EVR", {"k": 1, "r": 0, "su": after, "so": "0:0", "st": st1 or {}, "n": 2})]
        one = skills.sd_fmt(skills.step(s0))
        self.assertEqual(self.run_lines(ev(0x005BFE60, 0, skills.sd_fmt(s0))).ok["EVH.seed"], 1)  # stat 0: no draw
        C = self.run_lines(ev(0x005BFE60, 50, one))
        self.assertEqual((C.ok["EVH.seed"], C.bad["EVH.seed"]), (1, 0))
        self.assertEqual(self.run_lines(ev(0x005BFE60, 50, skills.sd_fmt(s0))).bad["EVH.seed"], 1)
        st0, st1 = {"8": 1000, "9": 5000}, {"8": 1000 + (6 << 8), "9": 5000}
        C = self.run_lines(ev(0x005C0130, 6, skills.sd_fmt(s0), st0, st1, e=9))
        self.assertEqual((C.ok["EVH.seed"], C.ok["EVH.mana"], sum(C.bad.values())), (1, 1, 0))
        self.assertEqual(self.run_lines(ev(0x005C0130, 6, skills.sd_fmt(s0), st0, st0, e=9)).bad["EVH.mana"], 1)

    def test_canuse(self):
        # Meteor (56): a cost above the mana is code 1; in a delay state (DLY at frame 100 for 30 frames) code 8
        P = self.T.srec(56)
        cost = (P["lvlmana"] * 4 + P["mana"]) << P["shift"]

        def lines(mana, fr, r, dly=True):
            out = [("DLY", {"u": 1, "d": 30, "fr": 100, "n": 1})] if dly else []
            return out + [("CU0", {"u": {"u": 1, "t": 0, "c": 1, "id": 1, "m": 1, "s": "1:2", "st": {"8": mana}},
                                   "sk": 56, "ret": 0x00549B0F, "bl": 5, "it": -1, "ch": 0, "fr": fr, "n": 2}),
                          ("CUL", {"k": 2, "bonus": 0, "base": 5, "n": 3}),
                          ("CU1", {"k": 2, "r": r, "s": "1:2", "n": 4})]
        self.assertEqual(self.run_lines(lines(cost - 1, 200, 1)).ok["CU.code"], 1)
        self.assertEqual(self.run_lines(lines(cost, 200, 0)).ok["CU.code"], 1)
        self.assertEqual(self.run_lines(lines(cost, 120, 8)).ok["CU.code"], 1)
        self.assertEqual(self.run_lines(lines(cost, 120, 0)).bad["CU.code"], 1)
        self.assertEqual(self.run_lines(lines(cost, 130, 0)).ok["CU.code"], 1)

    def test_summon_seed(self):
        pre = (0x3000, 0x4000)
        post = skills.step(pre)

        def lines(s):
            return [("SP0", {"blk": "00" * 0x28, "o": None, "fr": 1, "n": 1}),
                    ("SU0", {"u": 7, "t": 1, "c": 419, "p": 9, "pre": skills.sd_fmt(pre), "n": 2}),
                    ("SU1", {"u": 7, "p": 9, "post": skills.sd_fmt(post), "s": s, "u28": 0, "n": 3}),
                    ("SP1", {"k": 1, "m": {"u": 7, "t": 1, "c": 419, "id": 4, "m": 8, "s": s, "st": {}}, "so": None,
                             "n": 4})]
        C = self.run_lines(lines(skills.sd_fmt((post[0], 0x29A))))
        self.assertEqual((C.ok["SP.seed"], C.ok["SP.gameseed"], C.bad["SP.seed"]), (1, 1, 0))
        self.assertEqual(C.bad["SP.stats"], 1)                     # SP1 carries no life: the stats check fails
        self.assertEqual(self.run_lines(lines(skills.sd_fmt((post[0] + 1, 0x29A)))).bad["SP.seed"], 1)


if __name__ == "__main__":
    unittest.main()
