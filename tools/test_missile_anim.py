"""Tests of tools/missile_anim.py (plan 0070 Phase 11, batch 4 row 39, lane x17c): a toy missile's creation numbers, its
per-frame step and its hit (docs/specs/skills/missiles.md B1, D2-D4, E1).

Run: python3 -I tools/test_missile_anim.py     (needs no game data: the tool reads none)

The tool: the same arguments give the same bytes, both themes pass the export check's illustration rules, no art decoder
is imported, no text runs past the canvas, no caption is cut, no step text names a tool or a path. The numbers equal the
model: every frame's velocity state and position are fed to tools/skills.py's own frame check (Checker.mf, as if logged)
and none differs; the creation numbers and the roll are recomputed on their own; both ends of the hit (a hit and a miss)
are exercised.
"""
import os
import re
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA = os.path.join(ROOT, "workspace", "merged")
sys.path.insert(0, HERE)
import combat  # noqa: E402
import missile_anim as M  # noqa: E402
import schematic_kit as K  # noqa: E402
import skills  # noqa: E402
import test_schematic_kit as TK  # noqa: E402

SEEDS = (0xC0FFEE, 1, 2, 12345, 0xDEADBEEF, 77, 555, 4242)


def texts(out):
    return [s["text"] for s in TK.steps(out)] + TK.calc_text(out)


class Missile(unittest.TestCase):
    def test_deterministic_both_themes_and_clean(self):
        out = TK.same_both_themes(self, "missile_anim.py", [], "msl")
        self.assertEqual(len(TK.steps(out)), 11)
        for t in texts(out):
            self.assertNotRegex(t, r"\.py|tools/|workspace")
        K.TEXT_CLIPPED.clear()
        K.CAPTION_CUT.clear()
        for seed in SEEDS:
            for theme in ("dark", "light"):
                M.build(seed, theme)
        self.assertEqual((K.TEXT_CLIPPED, K.CAPTION_CUT), ([], []))
        self.assertEqual(M.main([DATA, "--seed", "0"]), 2)
        self.assertEqual(M.main([DATA, "--seed", "zz"]), 2)
        self.assertEqual(M.main([DATA, "--theme", "grey"]), 2)
        self.assertEqual(M.main([DATA, "extra"]), 2)

    def test_creation_numbers_recomputed(self):
        tr = M.run(0xC0FFEE)
        cr = tr["cr"]
        # ((VelLev * lvl) / 8 + Vel) << 8, then * 75 / 100; range = LevRange * lvl + Range; activate = range - Activate
        self.assertEqual(cr["v0"], ((8 * 10) // 8 + 24) << 8)
        self.assertEqual(cr["v"], cr["v0"] * 75 // 100)
        self.assertEqual((cr["range"], cr["left"], cr["activate"]), (1 * 10 + 8, 18, 18 - 12))
        self.assertEqual((cr["accel"], cr["maxv"]), (1024, 32 << 8))

    def test_creation_equals_the_models_creation_check(self):
        """skills.Checker.mc, fed the toy's creation as an MC0/MC1 pair with a stub row: velocity, accel and cap, range,
        frames left and activate as the model computes them from the row and the level (B1)."""
        import struct
        cr = M.run(0xC0FFEE)["cr"]
        row = dict(vellev=M.ROW["VelLev"], vel=M.ROW["Vel"], canslow=0, accel=M.ROW["Accel"], maxvel=M.ROW["MaxVel"],
                   levrange=M.ROW["LevRange"], range=M.ROW["Range"], subloop=0, substop=0, substart=0,
                   activate=M.ROW["Activate"], skill=0, mskill=0, srcdmg=0, srcmiss=0, pierce=0)
        ck = skills.Checker(type("T", (), {"mrec": lambda self, c: row})())
        blk = bytearray(0x5C)
        struct.pack_into("<i", blk, 0x30, M.LVL)
        pre = (0x1234, 0x29A)
        post = skills.step(pre)
        m = {"path": {"v": cr["v"], "a": cr["accel"], "mx": cr["maxv"]},
             "md": {"rng": cr["range"], "act": cr["activate"], "rem": cr["left"], "sk": 0, "lv": M.LVL},
             "s": skills.sd_fmt((post[0], skills.INIT_HIGH))}
        inner = [("SU0", {"pre": skills.sd_fmt(pre)}), ("SU1", {"post": skills.sd_fmt(post)})]
        self.assertEqual(ck.mc("toy", {"n": 1, "p": bytes(blk).hex()}, {"m": m}, inner), cr["v"])
        self.assertEqual(dict(ck.bad), {}, ck.miss)
        for kind in ("MC.vel", "MC.accel", "MC.range", "MC.left"):
            self.assertEqual(ck.ok[kind], 1, kind)

    def test_every_frame_equals_the_models_frame_check(self):
        for seed in SEEDS:
            tr = M.run(seed)
            ck = skills.Checker(None)
            left = tr["cr"]["left"]
            fr = tr["frames"]
            self.assertGreater(len(fr), 10)
            for f in fr:
                def path(s):
                    return dict(v=s["v"], a=s["a"], cnt=s["cnt"], mx=s["mx"], x=s["x"], y=s["y"], dx=M.DIR[0], dy=M.DIR[1])
                d0 = {"n": f["n"], "do": 1, "r": 1, "s": "a", "m": 1, "md": {"rem": left}, "path": path(f["d0"])}
                d1 = {"n": f["n"], "do": 1, "r": 1, "s": "a", "md": {"rem": f["left"]}, "path": path(f["d1"])}
                ck.mf("toy", d0, d1)
                self.assertEqual(f["left"], left - 1)
                left = f["left"]
            self.assertEqual(dict(ck.bad), {}, ck.miss)
            self.assertEqual(ck.ok["MF.vel"], len(fr))
            self.assertEqual(ck.ok["MF.pos"], len(fr))
            self.assertEqual(ck.ok["MF.left"] if "MF.left" in ck.ok else len(fr), len(fr))
            # the velocity capped once, accelerated on every fifth step before that (D4)
            self.assertEqual(sum(1 for f in fr if f["capped"]), 1)
            self.assertEqual([f["n"] for f in fr if f["fifth"]], [5])
            self.assertEqual(fr[-1]["d1"]["v"], 32 << 8)

    def test_collisions_start_at_the_activate_mark_and_the_hit_frame_holds_the_monster(self):
        tr = M.run(1)
        cr = tr["cr"]
        for f in tr["frames"]:
            self.assertEqual(f["tests"], f["left"] <= cr["activate"])
        hit = tr["hit"]
        self.assertTrue(hit["unit"])
        self.assertEqual(hit["cell"], tr["mon"])
        self.assertLessEqual(hit["left"], cr["activate"])
        # no earlier frame ended on the monster's cell with the test on
        self.assertFalse(any(f["unit"] for f in tr["frames"][:-1]))

    def test_the_roll_is_the_owners_next_draw_low_mod_100(self):
        ends = set()
        for seed in range(1, 60):
            tr = M.run(seed)
            r, _s = combat.rng_range((seed, 666), 100)
            self.assertEqual(tr["roll"]["r"], r)
            self.assertEqual(tr["roll"]["hit"], r < M.HIT_CHANCE)
            ends.add(tr["roll"]["hit"])
        self.assertEqual(ends, {True, False})        # both branches run

    def test_a_hit_and_a_miss_say_what_the_spec_says(self):
        hit = next(s for s in range(1, 200) if M.run(s)["roll"]["hit"])
        miss = next(s for s in range(1, 200) if not M.run(s)["roll"]["hit"])
        for seed, word in ((hit, "a hit"), (miss, "a miss")):
            _f, caps, _p, _tr = M.build(seed, "dark")
            self.assertEqual(len(caps), 11)
            flat = " ".join(c["text"] + " " + " ".join(c["calc"]) for c in caps)
            self.assertIn(word, flat)
            if word == "a hit":
                self.assertIn("CollideKill missile is freed", flat)
            else:
                self.assertIn("no damage is built", flat)
                self.assertNotIn("is built and applied", flat)

    def test_labels_use_no_x_for_times(self):
        with open(os.path.join(HERE, "missile_anim.py"), encoding="utf-8") as fh:
            src = fh.read()
        self.assertEqual(re.findall(r"(?:%d|[0-9)]) [Xx] |[A-Z] X [A-Z] /| [Xx] (?:%d|[0-9(])", src), [])


if __name__ == "__main__":
    unittest.main()
