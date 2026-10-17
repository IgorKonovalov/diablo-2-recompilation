"""Tests of tools/stats.py (plan 0041 Phase 2): the LCG distance, the op graph the loader builds, the evaluation and
propagation model on a small hand-built tree, the regeneration tick and the timed-state apply. The model tests read
the stock tables (workspace/merged/data/global/excel) and skip without them. Stdlib only.

    python3 -I tools/test_stats.py
"""
import base64
import json
import os
import sys
import unittest
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import stats  # noqa: E402

HAVE_EXCEL = os.path.isdir(stats.DEFAULT_EXCEL)


def isc_line(T):
    """An ISC log line as tools/gdb/stats.py writes it, built from the table with the loader's rules (so the checker's
    own comparison must find no difference)."""
    tg, deps, opin, b51, b52, b53 = T.isc_graph()
    rows = []
    for i, r in enumerate(T.isc):
        f4 = 4 if r["damagerelated"] == "1" else 0
        f5 = (4 if r["fMin"] == "1" else 0) | (8 if r["fCallback"] == "1" else 0)
        op = int(r["op"] or 0)
        rows.append([f4, f5, int(r["ValShift"] or 0), int(r["MinAccr"] or 0), int(r["keepzero"] or 0), b51[i],
                     b52[i], b53[i], op if 1 <= op <= 13 else 0, tg[i], deps[i], opin[i],
                     [opin[i][k][0] if k < len(opin[i]) else 0 for k in range(3)]])
    z = base64.b64encode(zlib.compress(json.dumps(rows).encode())).decode()
    return {"n": len(rows), "m270": 4, "m274": 8, "z": z}


class LcgTest(unittest.TestCase):
    def test_distance(self):
        a = "00003039:0000029a"
        lo, hi = 0x3039, 0x29A
        for _ in range(5):
            lo, hi = stats.lcg_step(lo, hi)
        self.assertEqual(stats.lcg_distance(a, "%08x:%08x" % (lo, hi), 10), 5)
        self.assertEqual(stats.lcg_distance(a, a, 10), 0)
        self.assertIsNone(stats.lcg_distance(a, "00000001:00000001", 10))


@unittest.skipUnless(HAVE_EXCEL, "no workspace excel tables")
class ModelTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.T = stats.Tables(stats.DEFAULT_EXCEL)
        cls.I = stats.ISC(isc_line(cls.T))

    def test_isc_selfcheck(self):
        C = stats.Checker(self.T)
        C.cur_log, C.cur_line = "test", 0
        C.check_isc(self.I)
        self.assertEqual(dict(C.bad), {})
        self.assertGreater(C.n["isc_field"], 5000)

    def tree(self):
        """A player (Barbarian, level 80, strength 100) wearing one armour: base defense 100, ac% 50 (op 13 on the
        item list), ac/lvl 24 (op 4: 24 x level >> 3 on the item list)."""
        sid = self.T.stat_id
        k = lambda name, p=0: sid[name] << 16 | p
        item = {"p": 0x200, "f": stats.EXT | stats.OPSRC, "s": 0, "u": 0x10, "ct": 4,
                "own": [[k("armorclass"), 100]], "cache": [], "ow": {"u": 0x20, "t": 4, "c": 0}, "ch": [
                    {"p": 0x300, "f": 0x40, "s": 0, "u": 0x20, "ct": 4,
                     "own": [[k("item_armor_percent"), 50], [k("item_armor_perlevel"), 24]]}], "off": []}
        plr = {"p": 0x100, "f": stats.EXT, "s": 0, "u": 0, "ct": 0,
               "own": [[k("strength"), 100], [k("level"), 80], [k("vitality"), 50]],
               "cache": [[k("strength"), 100], [k("level"), 80], [k("vitality"), 50]],
               "ow": {"u": 0x10, "t": 0, "c": 4}, "ch": [item], "off": []}
        return plr

    def test_evaluate_ops(self):
        M = stats.Model(self.I, self.T, None)
        M.reset(self.tree(), 0x10)
        x = M.L[0x200]
        ac = self.T.stat_id["armorclass"] << 16
        # 100 + MulDiv(100, 50, 100) (op 13) + (24 x 80) >> 3 (op 4) = 100 + 50 + 240
        self.assertEqual(M.evaluate(x, ac), 390)

    def test_link_predicts_writes(self):
        """Linking the armour under the player propagates each of its active entries; armorclass is an op target
        (+0x52), so the player's list re-evaluates it (StatRecompute, a CacheWrite of the sum: op 13 needs an item
        owner, op 4 a linked unit)."""
        M = stats.Model(self.I, self.T, None)
        tree = self.tree()
        item = tree.pop("ch")[0]
        tree["ch"] = []
        M.reset(tree, 0x10)
        x = M.add_tree(dict(item, cache=[[self.T.stat_id["armorclass"] << 16, 390]]))
        ul = M.L[0x100]
        x.parent, x.u = ul.p, 0x10
        ul.ch.insert(0, x.p)
        gen = M.link_gen(ul, x, 1)
        out = []
        for e in gen:                       # the op-4 recompute on the item first (0x20000000), then the propagation
            out.append(e)
            if e[0] == "CW":
                M.cache_write(M.L[e[1]], e[2], e[3])
        prp = [e for e in out if e[0] == "PRP"]
        self.assertEqual(prp, [("PRP", 0x100, self.T.stat_id["armorclass"] << 16, 390)])
        ca = list(M.propagate(ul, prp[0][2], prp[0][3]))
        self.assertEqual(ca, [("CW", 0x100, self.T.stat_id["armorclass"] << 16, 390)])

    def test_tick(self):
        """Life +stat 74 floored at 256; stamina walking (mode 2) max >> 9; mana max / (ManaRegen x 25)."""
        M = stats.Model(self.I, self.T, None)
        tree = self.tree()
        sid = self.T.stat_id
        tree["cache"] += [[sid["hitpoints"] << 16, 300], [sid["maxhp"] << 16, 100000], [sid["hitpoints"] << 16, 300]]
        tree["cache"] = list({k: v for k, v in tree["cache"]}.items())
        tree["cache"] += [[sid["hpregen"] << 16, -100], [sid["stamina"] << 16, 1000], [sid["maxstamina"] << 16, 51200],
                          [sid["mana"] << 16, 0], [sid["maxmana"] << 16, 120000]]
        M.reset(tree, 0x10)
        C = stats.Checker(self.T)
        p = C.predict_tick(M, {"v": [0] * 10, "m": 2, "sb": []})
        self.assertEqual(p[6][0], 256)
        self.assertEqual(p[10][0], 1000 + (51200 >> 9))
        mr = int(self.T.charstats[4]["ManaRegen"]) * 25
        self.assertEqual(p[8][0], 120000 // mr)

    def test_apply(self):
        """A second request with the same state, skill and level refreshes; a lower level is refused; a new state
        makes a list with the timed flag and expiry frame + duration."""
        M = stats.Model(self.I, self.T, None)
        tree = self.tree()
        tree["ch"].append({"p": 0x400, "f": 2, "s": 34, "u": 0x10, "ct": 0, "x": 151, "sk": 99, "sl": 10,
                           "own": []})
        M.reset(tree, 0x10)
        C = stats.Checker(self.T)
        req = {"state": 34, "len": 51, "sk": 99, "sl": 10, "stat": -1, "val": 0, "sb": [], "fr": 150}
        r = C.predict_apply(M, req)
        self.assertEqual((r[0], r[2]), ("refresh", 201))
        r = C.predict_apply(M, dict(req, sl=5))
        self.assertEqual(r[0], "refuse")
        r = C.predict_apply(M, dict(req, state=47, sk=119))
        self.assertEqual(r[0], "new")
        self.assertEqual(r[1]["x"], 201)
        self.assertTrue(r[1]["f"] & 2)


if __name__ == "__main__":
    unittest.main()
