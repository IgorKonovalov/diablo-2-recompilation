"""Synthetic tests for tools/golden.py (plan 0059 Phase 1): python3 -I tools/test_golden.py

No game file is read. The committed sample set (docs/formats/golden/sample-v1.jsonl) is parsed and checked against
itself, and against a copy with one altered field (which must fail, naming that field).
  - canonical JSON and digests: key order does not matter, a changed value does;
  - field patterns: every committed field name matches FIELDS, an unknown one does not;
  - drop_case on a synthetic TCR .. TCEND call;
  - check: a set passes against itself, fails on one altered field, on a missing case, and reports quirk ids;
  - header version is enforced; sample and merge keep the header.
"""
import copy
import json
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import golden  # noqa: E402

SAMPLE = os.path.join(os.path.dirname(HERE), "docs", "formats", "golden", "sample-v1.jsonl")


class NS:
    def __init__(self, **kw):
        self.__dict__.update(kw)


def write(path, header, cases):
    golden.write_set(path, header, cases)


def mini():
    h = {"golden": "trace", "version": 1, "set": "t", "scope": "world,drops", "game_exe_sha256": None,
         "tables_digest": None}
    c = [{"id": "a", "kind": "predicted", "type": "world", "inputs": {}, "quirks": ["Q-1"],
          "expected": {"chain.A1.map_seed": 5, "chain.B2.level_seed.57": "00000001:0000029a"}},
         {"id": "b", "kind": "observed", "type": "drop", "inputs": {}, "quirks": [],
          "expected": {"chain.G1.count": 1, "chain.G1.pick": [[160, 3]]}}]
    return h, c


class Digests(unittest.TestCase):
    def test_canon(self):
        self.assertEqual(golden.canon({"b": 1, "a": [1, 2]}), '{"a":[1,2],"b":1}')
        self.assertEqual(golden.value_digest({"a": 1, "b": 2}), golden.value_digest({"b": 2, "a": 1}))
        self.assertNotEqual(golden.value_digest({"a": 1}), golden.value_digest({"a": 2}))

    def test_set_digest_order_free(self):
        h, c = mini()
        self.assertEqual(golden.set_digest(h, c), golden.set_digest(h, list(reversed(c))))
        c2 = copy.deepcopy(c)
        c2[0]["expected"]["chain.A1.map_seed"] = 6
        self.assertNotEqual(golden.set_digest(h, c), golden.set_digest(h, c2))
        h2 = dict(h, version=2)
        self.assertNotEqual(golden.set_digest(h, c), golden.set_digest(h2, c))


class Patterns(unittest.TestCase):
    def test_patterns(self):
        self.assertEqual(golden.pattern("chain.B2.level_seed.57"), "chain.B2.level_seed.N")
        self.assertEqual(golden.pattern("chain.G1.count"), "chain.G1.count")
        self.assertIsNone(golden.pattern("chain.B2.level_seed.x"))
        self.assertIsNone(golden.pattern("chain.Z9.nothing"))

    def test_sample_fields_registered(self):
        h, cases = golden.read_set(SAMPLE)
        self.assertEqual(h["version"], 1)
        self.assertGreaterEqual(len(cases), 20)
        self.assertEqual({c["kind"] for c in cases}, {"observed", "predicted"})
        for c in cases:
            self.assertIn(c["kind"], golden.KINDS)
            self.assertEqual(c["quirks"], [])
            for f in c["expected"]:
                self.assertIsNotNone(golden.pattern(f), f)
            if c["kind"] == "observed":
                self.assertIn("log", c["source"])


class DropCase(unittest.TestCase):
    def test_drop_case(self):
        tcr = {"stype": "1", "sclass": "374", "seed": "00000001:0000029a", "tc": "517", "fq": "0", "ilvl": "15",
               "nonodrop": "0", "max": "0", "g6a": "3", "diff": "0", "exp": "1", "gseed": "00000002:00000003",
               "mflags": "00", "suid": "0", "ktype": "0", "kclass": "1"}
        call = [("TCR", tcr), ("_DROP", None), ("_CTX", []), ("PLAYERS", {"players": "2"}),
                ("NDP", {"ndp": "100", "total": "60"}), ("PICK", {"range": "160", "roll": "56", "seed": "x"}),
                ("SEL", {"i": "2"}), ("SUB", {"tc": "203"}), ("QOUT", {"q": "2"}),
                ("CPRE", {"item": "526", "q": "2", "uidx": "0"}), ("TCEND", {"count": "1", "seed": "00000009:0000000a"})]
        c = golden.drop_case(call, 7, {"log": "x.log"})
        self.assertEqual(c["id"], "drop:o:x.log:7")
        self.assertEqual(c["inputs"]["players"], 2)
        self.assertEqual(c["inputs"]["monster_flags"], "00")
        e = c["expected"]
        self.assertEqual((e["chain.G1.nodrop"], e["chain.G1.pick"], e["chain.G1.select"], e["chain.G1.subtc"]),
                         ([[100, 60]], [[160, 56]], [2], [203]))
        self.assertEqual((e["chain.G1.item"], e["chain.G1.count"], e["chain.G1.end_seed"]),
                         ([[526, 2, 0]], 1, "00000009:0000000a"))
        for f in e:
            self.assertIsNotNone(golden.pattern(f))


class Check(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.TemporaryDirectory()
        self.p = lambda n: os.path.join(self.d.name, n)

    def tearDown(self):
        self.d.cleanup()

    def run_check(self, setp, cand, **kw):
        import contextlib
        import io
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = golden.cmd_check(NS(set=setp, candidate=cand, fields=kw.get("fields"), limit=20))
        return rc, buf.getvalue()

    def test_self_pass_and_altered_fail(self):
        h, c = mini()
        write(self.p("s"), h, c)
        self.assertEqual(self.run_check(self.p("s"), self.p("s"))[0], 0)
        c2 = copy.deepcopy(c)
        c2[1]["expected"]["chain.G1.pick"] = [[160, 4]]
        write(self.p("c"), h, c2)
        rc, out = self.run_check(self.p("s"), self.p("c"))
        self.assertEqual(rc, 1)
        self.assertIn("chain.G1.pick", out)
        self.assertIn("MISMATCH b [observed]", out)
        self.assertEqual(self.run_check(self.p("s"), self.p("c"), fields="chain.A1")[0], 0)

    def test_outputs_form_missing_field_missing_case_quirks(self):
        h, c = mini()
        write(self.p("s"), h, c)
        with open(self.p("c"), "w") as fh:
            fh.write(json.dumps({"id": "a", "outputs": {"chain.A1.map_seed": 6}}) + "\n")
            fh.write(json.dumps({"id": "b", "outputs": {"chain.G1.count": 1, "chain.G1.pick": [[160, 3]]}}) + "\n")
        rc, out = self.run_check(self.p("s"), self.p("c"))
        self.assertEqual(rc, 1)
        self.assertIn("<missing>", out)
        self.assertIn("quirks Q-1", out)
        with open(self.p("c2"), "w") as fh:
            fh.write(json.dumps({"id": "b", "outputs": c[1]["expected"]}) + "\n")
        rc, out = self.run_check(self.p("s"), self.p("c2"))
        self.assertEqual(rc, 1)
        self.assertIn("MISSING 1", out)

    def test_sample_self_and_altered(self):
        self.assertEqual(self.run_check(SAMPLE, SAMPLE)[0], 0)
        h, cases = golden.read_set(SAMPLE)
        o = next(c for c in cases if c["type"] == "drop")
        o["expected"]["chain.G1.count"] += 1
        write(self.p("alt"), h, cases)
        rc, out = self.run_check(SAMPLE, self.p("alt"))
        self.assertEqual(rc, 1)
        self.assertIn("chain.G1.count", out)

    def test_version_enforced(self):
        h, c = mini()
        write(self.p("v"), dict(h, version=2), c)
        with self.assertRaises(SystemExit):
            golden.read_set(self.p("v"))
        with open(self.p("n"), "w") as fh:
            fh.write(json.dumps({"id": "a"}) + "\n")
        with self.assertRaises(SystemExit):
            golden.read_set(self.p("n"))

    def test_sample_and_merge(self):
        h, cases = golden.read_set(SAMPLE)
        golden.cmd_sample(NS(set=SAMPLE, out=self.p("s1"), worlds=2, drops=3))
        h1, c1 = golden.read_set(self.p("s1"))
        self.assertEqual(h1, h)
        self.assertEqual(len(c1), 5)
        golden.cmd_merge(NS(sets=[self.p("s1"), SAMPLE], out=self.p("m"), name="m"))
        hm, cm = golden.read_set(self.p("m"))
        self.assertEqual(len(cm), len(cases))
        self.assertEqual(hm["set"], "m")


if __name__ == "__main__":
    unittest.main()
