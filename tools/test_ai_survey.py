"""Tests of tools/ai_survey.py (plan 0052 Phase 0): the record ranges, the Aiparms.txt section parser and its name
matches, the image table reader on a hand-built PE, and, on the stock tables (workspace/merged/data/global/excel; skipped
without them), the AI index invariants and the batch rule's cover. Stdlib only.

    python3 -I tools/test_ai_survey.py
"""
import os
import struct
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import ai_survey as A  # noqa: E402

EXCEL = os.path.join(os.path.dirname(HERE), "workspace", "merged", "data", "global", "excel")
HAVE_EXCEL = os.path.isdir(EXCEL)

AIPARMS = "\r\n".join([
    "Description of Ai Parameters",
    "",
    "/* ==== */",
    '"Brute" Ai',
    "Yeti",
    "",
    "This Ai always walks towards the player",
    "----------",
    "P1\tPct chance to strike",
    "P2\tPct chance to do",
    "\tAttack2",
    "",
    "Missiles:\tNone",
    "Skills:\t\tNone",
    "Note: a note that closes the section",
    "on two lines.",
    "",
    "Spike Fiend",
    "----------",
    "P1\tDistance",
    "",
])


def tiny_pe(base, sec_va, raw_off, payload):
    """A PE32 image with one section holding payload at RVA sec_va (file offset raw_off)."""
    pe = 0x40
    optsz = 0xE0
    b = bytearray(raw_off + len(payload))
    b[0:2] = b"MZ"
    struct.pack_into("<I", b, 0x3C, pe)
    b[pe:pe + 4] = b"PE\0\0"
    struct.pack_into("<HH", b, pe + 4, 0x14C, 1)
    struct.pack_into("<H", b, pe + 20, optsz)
    struct.pack_into("<I", b, pe + 24 + 28, base)
    so = pe + 24 + optsz
    b[so:so + 8] = b".data\0\0\0"
    struct.pack_into("<IIII", b, so + 8, len(payload), sec_va, len(payload), raw_off)
    b[raw_off:] = payload
    return bytes(b)


class Pure(unittest.TestCase):
    def test_ranges(self):
        self.assertEqual(A.ranges([9, 3, 4, 5]), [(3, 5), (9, 9)])
        self.assertEqual(A.ranges([]), [])

    def test_aiparms_sections(self):
        secs = A.parse_aiparms(AIPARMS)
        self.assertEqual(len(secs), 2)
        self.assertEqual(secs[0]["titles"], ['"Brute" Ai', "Yeti"])
        self.assertEqual(secs[0]["text"], "This Ai always walks towards the player")
        self.assertEqual(secs[0]["params"], {1: "Pct chance to strike", 2: "Pct chance to do Attack2"})
        self.assertEqual(secs[0]["missiles"], "None")
        self.assertEqual(secs[0]["skills"], "None")
        # the Note paragraph belongs to the first section, not to the second's titles
        self.assertEqual(secs[1]["titles"], ["Spike Fiend"])
        self.assertEqual(secs[1]["params"], {1: "Distance"})

    def test_aiparms_matches(self):
        secs = A.parse_aiparms(AIPARMS)
        names = ["None", "Brute", "QuillRat"]
        self.assertEqual(A.norm('"Brute" Ai'), "brute")
        self.assertEqual(A.aiparms_matches(secs, names), [[(1, "name")], []])
        self.assertEqual(A.aiparms_matches(secs, names, {"spikefiend": [2]}), [[(1, "name")], [(2, "display")]])

    def test_table_from_image(self):
        rows = [(1, 0, 0x005EFCF0, 0), (4, 0, 0x005F1800, 0x005F1750)]
        payload = b"\0" * 0x18 + b"".join(struct.pack("<4I", *r) for r in rows)
        img = tiny_pe(0x400000, 0x1000, 0x200, payload)
        self.assertEqual(A.table_from_image(img, 0x401018, 2), rows)
        with self.assertRaises(ValueError):
            A.table_from_image(img, 0x401018, 3)


@unittest.skipUnless(HAVE_EXCEL, "stock tables not extracted")
class Stock(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d = A.Data(EXCEL)
        cls.kv = A.summary(cls.d)

    def test_index(self):
        kv = self.kv
        self.assertEqual(kv["ai_rows"], 148)
        self.assertEqual(kv["ai_bin_is_row"], 148)
        self.assertEqual(kv["ms_ai_name_mismatch"], 0)
        self.assertEqual(kv["ms_ai_bad"], 0)
        self.assertEqual(kv["ai_used"] + kv["ai_unused"], 148)

    def test_unused_rows(self):
        d = self.d
        self.assertEqual([d.ai_names[a] for a in range(148) if not d.users.get(a)], ["None", "ShadowMasterNoInit"])

    def test_hirelings_one_ai(self):
        d = self.d
        self.assertEqual({d.ai_names[d.ai_of[c]] for c in d.hire_classes}, {"Hireable"})

    def test_batches_cover_each_row_once(self):
        rows = [a for _, r in A.batches(self.d) for a in r]
        self.assertEqual(sorted(rows), list(range(148)))


if __name__ == "__main__":
    unittest.main()
