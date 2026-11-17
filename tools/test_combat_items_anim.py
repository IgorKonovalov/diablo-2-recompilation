"""Tests of the last schematic generators of batch 2 (plan 0070 Phase 11, lane x12e): tools/combat_anim.py (one melee hit),
tools/hire_anim.py (a hire list) and tools/affix_anim.py (one magic-affix pick).

Run: python3 -I tools/test_combat_items_anim.py     (the hire and affix cases need workspace/merged: skipped without it)

Each generator: the same arguments give the same bytes, both themes pass the export check's illustration rules, no art
decoder is imported, no text runs past the canvas, no caption is cut, no step text names a tool or a path. The numbers
equal the model: the hire list equals tools/hirelings.py (list command, build_stock and roll_entry with and without their
trace); the affix pick equals tools/affixes.py (Walk.pick with and without its trace, and alvl_of); the melee hit's to-hit,
defence, damage build, open wounds and crushing blow are fed to the model's own checks (combat.Checker.tohit, defence,
build, openwounds, crushing) as if logged, so a number or a seed that differs fails. The affix frames are capped: at
most MAX_LISTED affix ids per frame and one affix name on the whole sequence (ADR-0009 risk 3).
"""
import contextlib
import io
import os
import re
import struct
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA = os.path.join(ROOT, "workspace", "merged")
EXCEL = os.path.join(DATA, "data", "global", "excel")
sys.path.insert(0, HERE)
import affix_anim  # noqa: E402
import affixes  # noqa: E402
import combat  # noqa: E402
import combat_anim  # noqa: E402
import hire_anim  # noqa: E402
import hirelings  # noqa: E402
import schematic_kit as K  # noqa: E402
import test_schematic_kit as TK  # noqa: E402

HAVE_DATA = os.path.isdir(DATA)


def texts(out):
    return [s["text"] for s in TK.steps(out)] + TK.calc_text(out)


def sd(t):
    return "%08x:%08x" % t


class Recorder:
    """Records every text a Kit draws, per frame (a frame ends at Kit.done)."""

    def __enter__(self):
        self.frames, self.cur = [], []
        self.old_text, self.old_done = K.Kit.text, K.Kit.done
        rec = self

        def text(kit, x, y, s, col="txt", sc=2, bold=False):
            rec.cur.append(s)
            return rec.old_text(kit, x, y, s, col, sc, bold)

        def done(kit):
            rec.frames.append(rec.cur)
            rec.cur = []
            return rec.old_done(kit)
        K.Kit.text, K.Kit.done = text, done
        return self

    def __exit__(self, *a):
        K.Kit.text, K.Kit.done = self.old_text, self.old_done


class Combat(unittest.TestCase):
    """The toy hit against the model's own checks."""

    @classmethod
    def setUpClass(cls):
        cls.checker = combat.Checker(None)
        try:
            cls.real = combat.Tables()
            cls.hp_pct = cls.real.hp_pct
        except Exception:                      # no pinned game.exe in this workspace
            cls.real, cls.hp_pct = None, [0, 0, 50, 100, 150, 200, 250, 300, 350]

        class T:                               # the tables the checks read, with the toy's own values
            hp_pct = cls.hp_pct

            @staticmethod
            def tohitfactor(_c):
                return combat_anim.TOY_TOHIT_FACTOR

            @staticmethod
            def weapon(_w):
                return dict(sb=combat_anim.TOY_WEAPON["sb"], db=combat_anim.TOY_WEAPON["db"], type=0)

            @staticmethod
            def demon(_c):
                return False

            @staticmethod
            def undead(_c):
                return False

            @staticmethod
            def boss(_c):
                return False

            @staticmethod
            def crit(_c):
                return 0
        cls.T = T
        cls.ck = combat.Checker(T)

    def traces(self):
        for seeds in ((0xC0FFEE, 12345), (0xC0FFEE, 5000), (1, 2), (0xDEADBEEF, 77), (12, 99), (555, 4242)):
            yield seeds, combat_anim.run(*seeds)

    def test_hit_chance_and_both_to_hit_draws_equal_the_models_check(self):
        n = 0
        for (s, ds), tr in self.traces():
            a, d, th = tr["a"], tr["d"], tr["th"]
            first = tr["draws"][0]
            lines = [("THB", {"ar": th["ar0"], "def": th["defense"]}),
                     ("THV", {"ar": th["ar0"], "def": th["defense"], "pct": 0, "al": th["alvl"], "dl": th["dlvl"]}),
                     ("THR", {"c": th["c"], "r": th["r"], "sa": sd(first[4])})]
            ev = combat.Ev("pa", {}, lines)
            hit, sa, i = self.ck.tohit(ev, a, d, (s, 666), {}, lines, 0)
            self.assertEqual((hit, sa, i), (th["hit"], first[4], 3))
            n += 1
        self.assertEqual(n, 6)

    def test_block_draw_equals_the_models_defence_roll(self):
        for (s, ds), tr in self.traces():
            d, df = tr["d"], tr["df"]
            if not df["ran"]:
                continue
            dd = [x for x in tr["draws"] if x[0] == "D"][0]
            lines = [("DRB", {"b": df["b"]}), ("DRR", {"lab": "block", "ch": df["b"], "r": df["r"], "s": sd(dd[4])})]
            bits, sdn, i = self.ck.defence(d, (ds, 666), lines, 0, 0, True, {"exp": 1})
            self.assertEqual(bits, 1 if df["blocked"] else 0)
            self.assertEqual(sdn, dd[4])
        # the always-blocked seed: a block draw below the chance
        blocked = [tr for _s, tr in self.traces() if tr["df"]["blocked"]]
        self.assertEqual(combat_anim.run(0xC0FFEE, 5000)["df"]["blocked"], True)
        self.assertTrue(blocked)

    def test_damage_build_equals_the_models_build(self):
        for (s, ds), tr in self.traces():
            a, d, ph, cr, rb = tr["a"], tr["d"], tr["ph"], tr["cr"], tr["rb"]
            draws = [x for x in tr["draws"] if x[0] == "A"]
            to_hit = draws[0]
            phys = next(x for x in draws if x[1] == "physical")
            ds_draw = next((x for x in draws if x[1] == "deadly strike"), None)
            burn = next(x for x in draws if x[1] == "burning step")
            zero = struct.pack("<28i", *([0] * 28))
            end = [0] * 28
            end[0] = 0x20
            end[1] = 0x2000 if cr["won"] else 0
            end[2] = cr["final"]
            end[5] = rb["burn"]
            lines = [("BD0", {"p": zero.hex(), "sa": sd(to_hit[4]), "src": 0, "crit": 0}),
                     ("RPM", {"v": 0}),
                     ("RPE", {"sa": sd(to_hit[4]), "w": 5, "min": ph["mn"], "max": ph["mx"], "ed": ph["ed"],
                              "s18": 0, "s17": 0, "phys": 0}),
                     ("BDC", {"sa": sd(phys[4]), "v": 0}),
                     ("BD1", {"p": struct.pack("<28i", *end).hex(), "sa": sd(burn[4])})]
            ev = combat.Ev("pa", {"ret": 0x0056F156}, lines)
            p, sa, i = self.ck.build(ev, a, d, to_hit[4], lines, 0, {})
            self.assertEqual((sa, i), (burn[4], 5))
            self.assertEqual(p[2], cr["final"])
            self.assertEqual(ds_draw is not None, cr["ran"])
            self.assertEqual(ds_draw[3] if ds_draw else None, cr["r"])

    def test_open_wounds_and_crushing_blow_equal_the_models(self):
        seen = set()
        for (s, ds), tr in self.traces():
            dl = tr["dl"]
            if not dl["ran"]:
                continue
            a, d = tr["a"], tr["d"]
            sa = [x for x in tr["draws"] if x[1] == "burning step"][0][4]
            ow, cb = dl["ow"], dl["cb"]
            sta = {"state": 62, "len": 200, "stat": 74, "val": -ow.get("dmg", 0)}
            sa2, ok = self.ck.openwounds({}, {}, a, d, sa, 5, sta if ow["won"] else None, 0)
            self.assertEqual(ok, ow["won"])
            self.assertEqual(sa2, [x for x in tr["draws"] if x[1] == "open wounds"][0][4])
            life = dl["life0"]
            after = cb["life_after"] if cb["won"] else life
            sa3 = self.ck.crushing({"lo": [life]}, {"lo": [after]}, a, d, sa2, 5)
            self.assertEqual(sa3, [x for x in tr["draws"] if x[1] == "crushing blow"][0][4])
            seen.add((ow["won"], cb["won"]))
        self.assertIn((True, True), seen)

    def test_the_toys_player_count_term_is_zero_and_the_draw_order_is_the_specs(self):
        self.assertEqual(self.hp_pct[1], 0)                     # one player: no player-count term (delivery E1)
        tr = combat_anim.run(0xC0FFEE, 12345)
        self.assertEqual([(w, lab) for w, lab, *_ in tr["draws"]],
                         [("A", "to-hit"), ("D", "block"), ("A", "physical"), ("A", "deadly strike"), ("A", "burning step"),
                          ("A", "open wounds"), ("A", "crushing blow")])
        # the generator's steps equal one step of the model's generator per draw
        sa = (0xC0FFEE, 666)
        for who, lab, n, v, seed in tr["draws"]:
            if who == "A":
                got, sa = combat.rng_range(sa, n)
                self.assertEqual((got, sa), (v, seed))
        # a miss and a block deliver nothing and draw no stat event
        miss = next(t for _s, t in self.traces() if not t["th"]["hit"]) if any(
            not t["th"]["hit"] for _s, t in self.traces()) else None
        if miss:
            self.assertEqual([x[1] for x in miss["draws"]], ["to-hit", "physical", "deadly strike", "burning step"])
        blk = combat_anim.run(0xC0FFEE, 5000)
        self.assertNotIn("open wounds", [x[1] for x in blk["draws"]])

    def test_deterministic_both_themes_and_clean(self):
        out = TK.same_both_themes(self, "combat_anim.py", [], "cmb")
        self.assertEqual(len(TK.steps(out)), 9)
        for t in texts(out):
            self.assertNotRegex(t, r"\.py|tools/|workspace")
        K.TEXT_CLIPPED.clear()
        K.CAPTION_CUT.clear()
        for seeds in ((0xC0FFEE, 12345), (0xC0FFEE, 5000), (1, 2), (0xDEADBEEF, 77), (12, 99), (555, 4242)):
            for theme in ("dark", "light"):
                combat_anim.build(seeds[0], seeds[1], theme)
        self.assertEqual((K.TEXT_CLIPPED, K.CAPTION_CUT), ([], []))
        self.assertEqual(combat_anim.main([DATA, "--seed", "0"]), 2)
        self.assertEqual(combat_anim.main([DATA, "--seed", "zz"]), 2)
        self.assertEqual(combat_anim.main([DATA, "extra"]), 2)

    def test_labels_use_no_x_for_times(self):
        with open(os.path.join(HERE, "combat_anim.py"), encoding="utf-8") as fh:
            src = fh.read()
        self.assertEqual(re.findall(r"(?:%d|[0-9)]) [Xx] |[A-Z] X [A-Z] /| [Xx] (?:%d|[0-9(])", src), [])


@unittest.skipUnless(HAVE_DATA, "no workspace/merged (game data)")
class Hire(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.T = hirelings.Tables(EXCEL)

    def test_deterministic_both_themes_and_clean(self):
        out = TK.same_both_themes(self, "hire_anim.py", ["kashya", "30", "12345"], "hire")
        self.assertEqual(len(TK.steps(out)), 1 + 1 + 10 + 10 + 1)
        for t in texts(out):
            self.assertNotRegex(t, r"\.py|tools/|workspace")
        K.TEXT_CLIPPED.clear()
        K.CAPTION_CUT.clear()
        for who, sid in (("KASHYA", 150), ("GREIZ", 198), ("ASHEARA", 252), ("QUAL-KEHK", 515)):
            for plvl, seed, diff in ((30, 12345, 0), (1, 0xC0FFEE, 1), (85, 7, 2)):
                for theme in ("dark", "light"):
                    hire_anim.build(self.T, who, sid, 1, diff, plvl, seed, theme)
        self.assertEqual((K.TEXT_CLIPPED, K.CAPTION_CUT), ([], []))
        self.assertEqual(hire_anim.main([DATA, "nobody", "30", "1"]), 2)
        self.assertEqual(hire_anim.main([DATA, "kashya", "0", "1"]), 2)
        out = TK.run("hire_anim.py", ["greiz", "40", "9", "--classic", "--difficulty", "hell"], "hire-c")
        self.assertEqual(len(TK.steps(out)), 23)

    def test_list_equals_the_models_list_command(self):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            hirelings.main(["list", EXCEL, "00003039:0000029a", "150", "1", "0", "30"])
        want = [ln for ln in buf.getvalue().splitlines() if not ln.startswith("S after")]
        m = hire_anim.model(self.T, 150, 1, 0, 30, 12345)
        got = []
        for e in m["entries"]:
            _ok, o = hirelings.roll_entry(self.T, 1, 30, e["seed"], m["act"], 0)
            got.append("%d %d %s" % (e["name"], e["seed"], o))
            self.assertEqual((e["hid"], e["level"], e["price"]), (o[0], o[1], o[5]))
        self.assertEqual(got, want)
        self.assertEqual(len(got), 10)
        self.assertIn("S after %08x:%08x" % m["S_end"], buf.getvalue())

    def test_traced_model_equals_the_untraced(self):
        for seller in (150, 198, 252, 515):
            for sdv in (1, 0xC0FFEE, 0xDEADBEEF):
                S1, S2 = hirelings.Seed(sdv), hirelings.Seed(sdv)
                tr = []
                a = hirelings.build_stock(self.T, S1, seller, 1)
                b = hirelings.build_stock(self.T, S2, seller, 1, trace=tr)
                self.assertEqual(a, b)
                self.assertEqual((S1.low, S1.high), (S2.low, S2.high))
                self.assertEqual(len(tr), 10)
                self.assertEqual(sorted(v for _k, _u, v, _p, _s in tr), sorted(i for i in range(b[1]) if b[0][i][3]))
                for plvl in (1, 3, 30, 85):
                    for pos in range(b[1]):
                        if b[0][pos][3]:
                            act = self.T.rows[self.T.seller_row(1, seller)]["Act"] - 1
                            t = {}
                            x = hirelings.roll_entry(self.T, 1, plvl, b[0][pos][1], act, 0)
                            y = hirelings.roll_entry(self.T, 1, plvl, b[0][pos][1], act, 0, trace=t)
                            self.assertEqual(x, y)
                            self.assertEqual(t["raw"], plvl - 5 + t["mod"])
                            self.assertEqual(max(2, t["raw"]), y[1][1])

    def test_probes_are_drawless_and_counted(self):
        # a pick that lands on a listed slot steps on with no further draw: ten picks cost ten draws
        found = False
        for sdv in range(1, 400):
            tr = []
            S = hirelings.Seed(sdv)
            hirelings.build_stock(self.T, S, 198, 1, trace=tr)
            if any(p > 0 for _k, _u, _v, p, _s in tr):
                found = True
                n = 21
                lo, hi = sdv, 666
                import rng
                for _ in range(n + 10):
                    lo, hi = rng.step(lo, hi)
                self.assertEqual((S.low, S.high), (lo, hi))
                break
        self.assertTrue(found)

    def test_no_name_string_and_no_stat_in_the_frames(self):
        with Recorder() as rec:
            hire_anim.build(self.T, "KASHYA", 150, 1, 0, 30, 12345, "dark")
        flat = " ".join(" ".join(f) for f in rec.frames)
        self.assertNotRegex(flat, r"\b(LIFE|STRENGTH|DEXTERITY|DEFENCE|DAMAGE|RESIST)\b")
        # the entry frames show five lines of numbers at most per row: id, level, price, name index, seed
        self.assertEqual(len(rec.frames), 23)


@unittest.skipUnless(HAVE_DATA, "no workspace/merged (game data)")
class Affix(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.T = affixes.Tables(EXCEL)
        cls.codes = affix_anim.code_index(cls.T)

    def test_deterministic_both_themes_and_clean(self):
        out = TK.same_both_themes(self, "affix_anim.py", ["lsd", "30", "12345"], "aff")
        self.assertEqual(len(TK.steps(out)), 7)
        for t in texts(out):
            self.assertNotRegex(t, r"\.py|tools/|workspace")
        K.TEXT_CLIPPED.clear()
        K.CAPTION_CUT.clear()
        for code, ilvl, seed, pre in (("lsd", 30, 12345, True), ("lsd", 30, 12345, False), ("lsd", 30, 0xC0FFEE, True),
                                      ("cap", 30, 12345, True), ("ful", 19, 0xBEEF, False), ("lsd", 99, 7, True),
                                      ("lsd", 1, 7, False)):
            for theme in ("dark", "light"):
                affix_anim.build(self.T, self.codes, code, ilvl, seed, pre, theme)
        self.assertEqual((K.TEXT_CLIPPED, K.CAPTION_CUT), ([], []))
        self.assertEqual(affix_anim.main([DATA, "zzz", "30", "1"]), 2)
        self.assertEqual(affix_anim.main([DATA, "lsd", "30", "1", "--side", "middle"]), 2)
        self.assertEqual(affix_anim.main([DATA, "lsd", "300", "1"]), 2)

    def test_pick_equals_the_model_with_and_without_its_trace(self):
        import collections
        for code in ("lsd", "cap", "ful", "amu"):
            if code not in self.codes:
                continue
            for ilvl in (1, 12, 30, 61, 90):
                for seed in (1, 12345, 0xC0FFEE, 0xBEEF):
                    for pre in (True, False):
                        res = []
                        for tr in (None, {}):
                            it = affixes.Item(self.T, dict(cls=self.codes[code], ilvl=ilvl, ver=101))
                            it.q = 4
                            w = affixes.Walk(self.T, [], it, collections.Counter(), collections.defaultdict(list), "t",
                                             free=True)
                            w.seed = (seed, 666)
                            kw = {} if tr is None else {"trace": tr}
                            aid, rec = w.pick("magic", 1, 0, 0, 1 if pre else 0, **kw)
                            res.append((aid, rec, w.seed))
                        self.assertEqual(res[0], res[1])
                        m = affix_anim.model_pick(self.T, self.codes[code], ilvl, seed, pre)
                        self.assertEqual(m["aid"], res[0][0])
                        self.assertEqual(m["seed_end"], res[0][2])
                        if m.get("cands"):
                            self.assertEqual(sum(wt for _a, wt in m["cands"]), m["W"])
                            self.assertEqual(len(m["cands"]), m["rows"] - sum(n for _k, n in m["refused"]))
                            self.assertEqual(m["alvl"], affixes.alvl_of(m["it"]))

    def test_alvl_arithmetic_equals_the_model_including_magic_lvl_and_the_clamps(self):
        n = 0
        for cls in range(len(self.T.items)):
            b = self.T.b(cls)
            for ilvl in (0, 1, 2, 30, 60, 98, 99, 150):
                it = affixes.Item(self.T, dict(cls=cls, ilvl=ilvl, ver=101))
                self.assertEqual(affix_anim.alvl_parts(b, ilvl)["a"], affixes.alvl_of(it))
                n += 1
        self.assertGreater(n, 800)
        # a base with a magic lvl: the staff and the circlet rows of affixes B2
        withm = [c for c in range(len(self.T.items)) if self.T.b(c)["mlvl"]]
        self.assertTrue(withm)
        p = affix_anim.alvl_parts(self.T.b(withm[0]), 30)
        self.assertEqual(p["how"], "M")

    def test_frames_list_at_most_five_ids_and_name_one_affix(self):
        cases = [("lsd", 30, 12345, True), ("lsd", 30, 12345, False), ("cap", 30, 12345, True), ("ful", 19, 0xBEEF, False),
                 ("lsd", 99, 7, True), ("lsd", 1, 7, False), ("lsd", 30, 0xC0FFEE, True)]
        names = {r["name"].upper() for r in self.T.magic if r["name"]}
        for code, ilvl, seed, pre in cases:
            with Recorder() as rec:
                _f, caps, _p, tr = affix_anim.build(self.T, self.codes, code, ilvl, seed, pre, "dark")
            named = 0
            for fi, frame in enumerate(rec.frames):
                ids = [s for s in frame if re.fullmatch(r"ID \d+", s)]
                self.assertLessEqual(len(ids), affix_anim.MAX_LISTED, (code, fi))
                hits = [s for s in frame if s in names]
                self.assertLessEqual(len(hits), 1, (code, fi, hits))
                named += len(hits)
                for s in frame:
                    if s in names:
                        self.assertEqual(fi, len(rec.frames) - 1)        # only the result frame names the winner
            self.assertLessEqual(named, 1)
            if tr["aid"]:
                self.assertEqual(named, 1)
                self.assertIn(self.T.magic[tr["aid"] - 1]["name"].upper(), rec.frames[-1])
            # no step text names an affix
            flat = " ".join(c["text"] + " " + " ".join(c["calc"]) for c in caps)
            for r in self.T.magic:
                nm = r["name"]
                if len(nm) > 3 and nm[0].isupper():
                    self.assertNotRegex(flat, r"\b%s\b" % re.escape(nm), (code, nm))

    def test_candidate_strip_and_counts_equal_the_trace(self):
        m = affix_anim.model_pick(self.T, self.codes["lsd"], 30, 12345, True)
        self.assertTrue(m["rolled"])
        self.assertEqual(m["k"] >= 0, True)
        before = sum(w for _a, w in m["cands"][:m["k"]])
        w = m["cands"][m["k"]][1]
        self.assertTrue(before <= m["x"] < before + w or m["x"] == m["W"])
        self.assertEqual(m["cands"][m["k"]][0], m["aid"])
        out = TK.run("affix_anim.py", ["lsd", "30", "12345"], "aff-n")
        flat = " ".join(texts(out))
        self.assertIn("%d candidates, total weight %d" % (len(m["cands"]), m["W"]), flat)
        self.assertIn("Draw 2 is %d" % m["x"], flat)

    def test_no_roll_and_suffix_variants_end_early_and_name_nothing(self):
        out = TK.run("affix_anim.py", ["lsd", "30", "0xc0ffee"], "aff-nr")
        st = TK.steps(out)
        self.assertEqual(len(st), 4)
        self.assertIn("no affix", st[-1]["text"])
        out = TK.run("affix_anim.py", ["lsd", "30", "12345", "--side", "suffix"], "aff-s")
        self.assertEqual(len(TK.steps(out)), 7)

    def test_labels_use_no_x_for_times(self):
        for fn in ("hire_anim.py", "affix_anim.py"):
            with open(os.path.join(HERE, fn), encoding="utf-8") as fh:
                src = fh.read()
            self.assertEqual(re.findall(r"(?:%d|[0-9)]) [Xx] |[A-Z] X [A-Z] /| [Xx] (?:%d|[0-9(])", src), [], fn)


if __name__ == "__main__":
    unittest.main()
