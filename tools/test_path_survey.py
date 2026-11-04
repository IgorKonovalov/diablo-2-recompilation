#!/usr/bin/env python3
"""Tests of the direction-table part of tools/path_survey.py (backlog 2026-11-04, docs/tables/PathDirTables.md): the
section reader on a hand-built PE image, the table specs' internal consistency, and, on the pinned image (skipped
without it), the values the findings state, the extents between neighbouring tables and the width of every recorded
reading instruction (objdump; skipped without it).

    python3 -I tools/test_path_survey.py
"""
import os
import re
import shutil
import struct
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import path_survey as S  # noqa: E402

EXE = os.path.join(os.path.dirname(HERE), "workspace", "install", "app", "game.exe")
HAVE_EXE = os.path.isfile(EXE)
HAVE_OBJDUMP = shutil.which("objdump") is not None


def tiny_pe(base, rva, payload):
    """One section at rva holding payload, in a minimal PE header the readers understand."""
    pe = 0x80
    data = bytearray(0x400 + len(payload))
    struct.pack_into("<I", data, 0x3C, pe)
    struct.pack_into("<H", data, pe + 6, 1)          # one section
    struct.pack_into("<H", data, pe + 20, 0xE0)      # optional header size
    struct.pack_into("<I", data, pe + 24 + 28, base)  # image base
    so = pe + 24 + 0xE0
    struct.pack_into("<IIII", data, so + 8, len(payload), rva, len(payload), 0x400)
    data[0x400:] = payload
    return bytes(data)


class Reader(unittest.TestCase):
    def test_bytes_and_words_agree(self):
        payload = struct.pack("<4i", 5, -1, 0, 7)
        d = tiny_pe(0x400000, 0x1000, payload)
        self.assertEqual(S.read_bytes(d, 0x401000, 16), payload)
        self.assertEqual(S.read_u32s(d, 0x401004, 2), [0xFFFFFFFF, 0])
        self.assertEqual(S.read_bytes(d, 0x401008, 4), struct.pack("<i", 0))

    def test_past_the_section_raises(self):
        d = tiny_pe(0x400000, 0x1000, b"\0" * 8)
        with self.assertRaises(ValueError):
            S.read_bytes(d, 0x401004, 8)

    def test_table_values_signed_and_bytes(self):
        payload = struct.pack("<3i", -2, 3, -1) + bytes([4, 255, 6])
        d = tiny_pe(0x400000, 0x1000, payload)
        self.assertEqual(S.table_values(d, dict(va=0x401000, kind="i32", count=3)), [-2, 3, -1])
        self.assertEqual(S.table_values(d, dict(va=0x40100C, kind="u8", count=3)), [4, 255, 6])

    def test_crc_depends_on_every_value(self):
        a = S.crc([1, 2, 3])
        self.assertNotEqual(a, S.crc([1, 2, 4]))
        self.assertEqual(a, S.crc([1, 2, 3]))


class Specs(unittest.TestCase):
    def test_every_table_has_a_row_width_and_readers(self):
        names = set()
        for t in S.DIRTABLES:
            self.assertNotIn(t["name"], names)
            names.add(t["name"])
            self.assertIn(t["read"], ("DWORD", "WORD", "BYTE"))
            if t["kind"] == "u8":
                self.assertEqual(t["read"], "BYTE")
            self.assertTrue(t["readers"])
            self.assertNotEqual(t["name"] in S.MD_ROWS, t["name"] in S.RULES)
        self.assertEqual(names, set(S.MD_ROWS) | set(S.RULES))

    def test_mismatches_counts_each_element_and_length(self):
        self.assertEqual(S.mismatches([1, 2, 3], [1, 2, 3]), 0)
        self.assertEqual(S.mismatches([1, 2, 3], [1, 9, 3]), 1)
        self.assertEqual(S.mismatches([1, 2, 3], [1, 2]), 1)

    def test_operand_size(self):
        self.assertEqual(S.operand_size("mov    ax,WORD PTR [edx*8+0x6f1d9c]"), "WORD")
        self.assertEqual(S.operand_size("movzx  eax,BYTE PTR [eax+eax*2+0x6f1648]"), "BYTE")
        self.assertEqual(S.operand_size("mov    eax,ds:0x6eb7d4"), "DWORD")
        self.assertIsNone(S.operand_size("ret"))


@unittest.skipUnless(HAVE_EXE, "pinned image not present")
class Image(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.t = {t["name"]: (t, v) for t, v in S.dirtables(EXE)}

    def v(self, name):
        return self.t[name][1]

    def test_counts(self):
        self.assertEqual(sum(len(v) for _, v in self.t.values()), 946)
        self.assertEqual(len(self.t), 16)

    def test_octant_column_zero_is_the_outdoor_finding_list(self):
        # drlg/0008 tabulates column 0 by 5 dx' + dy' + 12: 5 4 4 4 3 | 6 5 4 3 2 | 6 6 6 2 2 | 6 7 0 1 2 | 7 0 0 0 1
        col0 = self.v("g_DirOctant")[0::3]
        self.assertEqual(col0, [5, 4, 4, 4, 3, 6, 5, 4, 3, 2, 6, 6, 6, 2, 2, 6, 7, 0, 1, 2, 7, 0, 0, 0, 1])
        self.assertLessEqual(max(self.v("g_DirOctant")), 7)

    def test_triples_are_axis_directions_or_none(self):
        # path/0001: every entry is 0, 2, 4, 6 or 255
        self.assertTrue(set(self.v("g_PathDirTriples")) <= {0, 2, 4, 6, 255})

    def test_step_tables(self):
        self.assertEqual(self.v("g_PathDir8"), self.v("g_PathStep8Long"))
        self.assertEqual(self.v("g_PathStep8Long")[:2], [1, 0])
        t15 = self.v("g_T15Step")
        self.assertEqual(t15[:2], [0, -1])
        self.assertEqual(t15[:16], t15[16:])

    def test_t15_dir_from_step_inverts_t15_step(self):
        step = self.v("g_T15Step")
        dfs = self.v("g_T15DirFromStep")   # index 3 dy + dx, centred: element k is index k - 4
        for d in range(8):
            dx, dy = step[2 * d], step[2 * d + 1]
            self.assertEqual(dfs[3 * dy + dx + 4], d)
        self.assertEqual(dfs[4], -1)

    def test_distnear_corner_and_diagonal_rule(self):
        d = self.v("g_PathDistNear")
        self.assertEqual(d[0], -1)
        self.assertEqual(d[63], 11)
        self.assertEqual(d[3], 0)

    def test_dirtable_rows(self):
        t = self.v("g_PathDirTable")
        self.assertEqual(t[:3], [0, 4096, 0])
        self.assertEqual(t[-3:], [2896, 2896, 7])
        self.assertEqual(S.table_values(S.load_image(EXE), dict(va=0x006EB7D4, kind="i32", count=2)), [0, 0])

    def test_sign_table_centre(self):
        s = self.v("g_PathSignTable")
        self.assertEqual(len(s), 81)
        self.assertEqual(s[40], 0)
        self.assertEqual(s[41], 1)
        self.assertEqual(s[39], -1)

    def test_sign_table_rule(self):
        # the observed relation, not the code's statement: entry(a, b) = sign a when |a| >= |b|, else 0, for |a|, |b| <= 4
        s = self.v("g_PathSignTable")
        for a in range(-4, 5):
            for b in range(-4, 5):
                self.assertEqual(s[40 + a + 9 * b], ((a > 0) - (a < 0)) if abs(a) >= abs(b) else 0, (a, b))

    def test_dirtable_relations(self):
        import math
        t = self.v("g_PathDirTable")
        for q in range(128):
            a = math.atan2(q, 127)
            self.assertEqual(t[3 * q:3 * q + 3], [int(4096 * math.sin(a)), int(4096 * math.cos(a)),
                                                   min(7, int(a / (math.pi / 32)))], q)

    def test_split_of_the_elements(self):
        kept = sum(len(self.v(n)) for n in S.MD_ROWS)
        ruled = sum(len(self.v(n)) for n in S.RULES)
        self.assertEqual((kept, ruled), (278, 668))

    def test_every_rule_equals_the_image_bit_for_bit(self):
        rep = S.rule_report(list(self.t.values()))
        self.assertEqual(len(rep), len(S.RULES))
        for name, n, bad, ci, cr in rep:
            self.assertEqual((name, bad, ci), (name, 0, cr))

    def test_one_changed_element_is_found_in_every_ruled_table(self):
        for name, rule in S.RULES.items():
            v = list(self.v(name))
            for i in (0, len(v) // 2, len(v) - 1):
                w = list(v)
                w[i] += 1
                self.assertEqual(S.mismatches(w, rule()), 1, (name, i))

    def test_face_step_rule_is_the_stated_expression(self):
        # d = ((i + 32) & 63) - 32; t = (|d| + 7) >> 3; sign(d) * min(8, t * t); no value is written here, the image is the oracle
        v = self.v("g_PathFaceStep")
        for i in range(64):
            d = ((i + 32) & 63) - 32
            e = (1 if d > 0 else -1 if d < 0 else 0) * min(8, ((abs(d) + 7) >> 3) ** 2)
            self.assertEqual(v[i], e, i)
        self.assertEqual(S.crc(v), 951300365)

    def test_face_step_mutated_element_fails_the_survey(self):
        v = list(self.v("g_PathFaceStep"))
        for i in range(64):
            w = list(v)
            w[i] += 1
            self.assertEqual(S.mismatches(w, S.RULES["g_PathFaceStep"]()), 1, i)
            rep = S.rule_report([(self.t["g_PathFaceStep"][0], w)])
            self.assertEqual(rep[0][2], 1)

    def test_dirtable_z_has_room_in_double(self):
        # the rule's quotient is never near an integer, so a correctly rounded or a near-correct atan gives one result
        self.assertGreater(S.dirtable_z_margin(), 0.007)

    def test_dirtable_integer_columns_are_the_definition(self):
        # the largest x with x^2 (q^2 + 127^2) <= 4096^2 q^2, and y likewise with 127^2 for q^2
        t = self.v("g_PathDirTable")
        for q in range(128):
            d = q * q + 127 * 127
            for x, top in ((t[3 * q], q * q), (t[3 * q + 1], 127 * 127)):
                self.assertLessEqual(x * x * d, 4096 * 4096 * top)
                self.assertGreater((x + 1) * (x + 1) * d, 4096 * 4096 * top)

    def test_distnear_second_copy(self):
        c = S.table_values(S.load_image(EXE), dict(va=S.DIST_COPY_VA, kind="i32", count=64))
        self.assertEqual(c, self.v("g_PathDistNear"))

    def test_doc_blocks_are_the_kept_tables_and_nothing_else(self):
        doc = open(os.path.join(os.path.dirname(HERE), "docs", "tables", "PathDirTables.md")).read()
        blocks = re.findall(r"^#### (g_\w+)  `0x[0-9A-F]{8}`\n\n```\n(.*?)\n```$", doc, re.M | re.S)
        self.assertEqual({n for n, _ in blocks}, set(S.MD_ROWS))
        for n, body in blocks:
            self.assertEqual(body, S.fmt_rows(self.v(n), S.MD_ROWS[n]), n)

    def test_doc_states_each_table_checksum(self):
        doc = open(os.path.join(os.path.dirname(HERE), "docs", "tables", "PathDirTables.md")).read()
        for n in self.t:
            self.assertRegex(doc, r"\| `%s` \|[^\n]*\| %d \|" % (n, S.crc(self.v(n))))

    def test_neighbours_do_not_overlap(self):
        spans = sorted((t["va"], t["va"] + t["count"] * (4 if t["kind"] == "i32" else 1), t["name"])
                       for t, _ in self.t.values())
        for a, b in zip(spans, spans[1:]):
            self.assertLessEqual(a[1], b[0], "%s overlaps %s" % (a[2], b[2]))

    @unittest.skipUnless(HAVE_OBJDUMP, "objdump not present")
    def test_every_recorded_reader_has_the_stated_width(self):
        rep = S.reader_report(EXE)
        self.assertEqual(len(rep), sum(len(t["readers"]) for t in S.DIRTABLES))
        # the doc's count: 71 table and reader pairs, 67 instructions; a dropped reader changes it
        self.assertEqual((len(rep), len({r[1] for r in rep})), (71, 67))
        bad = [r for r in rep if not r[4]]
        self.assertEqual(bad, [])


if __name__ == "__main__":
    unittest.main()
