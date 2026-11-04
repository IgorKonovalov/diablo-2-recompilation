"""No-game tests of tools/inventory_check.py and the plan 0060 Phase 2 model functions (fake logs built from
tools/item_inventory.py's own rooms, so every outcome is known). Run: python3 -I tools/test_inventory_check.py"""
import base64
import json
import os
import sys
import tempfile
import unittest
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import inventory_check as ic  # noqa: E402
import item_inventory as ii  # noqa: E402

FIELD = ic.field() if os.path.exists(ic.FIELD_FILE) else None


def room_z(blocked=()):
    """One room 0..99 x 0..99 whose window around (50, 50) holds cells with `blocked` cells set to 0x01."""
    rows = []
    for y in range(35, 70):
        row = bytearray()
        for x in range(34, 69):
            row += (1 if (x, y) in blocked else 0).to_bytes(2, "little")
        rows.append([y, 34, bytes(row).hex()])
    rooms = [{"r": 1000, "hop": 0, "rect": [0, 0, 100, 100], "near": [], "rows": rows, "nocells": False}]
    return base64.b64encode(zlib.compress(json.dumps(rooms).encode())).decode()


def write_log(path, gdi, gdo=None, extra=()):
    with open(path, "w") as f:
        f.write("GDI " + json.dumps(gdi) + "\n")
        if gdo:
            f.write("GDO " + json.dumps(gdo) + "\n")
        for tag, d in extra:
            f.write("%s %s\n" % (tag, json.dumps(d)))


@unittest.skipIf(FIELD is None, "expfield.d2 not extracted")
class Check(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()

    def run_check(self, logs, wrong=None):
        pred = os.path.join(self.d, "p.pred")
        with open(pred, "w") as f:
            for p in ic.predict(logs, wrong):
                f.write(json.dumps(p) + "\n")
        preds = [json.loads(l) for l in open(pred)]
        return ic.check(preds, logs, show=False)

    def case(self, blocked, name):
        z = room_z(blocked)
        gi = {"th": 1, "room": 1000, "x": 50, "y": 50, "ret": 0, "a1": 1, "a2": 1, "f": 10, "z": z}
        rm = ic.build_rooms(z)
        r, x, y = ii.ground_drop_cell(rm[1000], 50, 50, FIELD, 1)
        p = os.path.join(self.d, name)
        write_log(p, gi, {"th": 1, "room": 1000, "x": x, "y": y})
        return p, (x, y)

    def test_open_ground_start_cell(self):
        p, xy = self.case((), "a.log")
        self.assertEqual(xy, (52, 53))
        mism, _ = self.run_check([p])
        self.assertEqual(mism, [])

    def test_blocked_start_ring_one(self):
        p, xy = self.case({(52, 53)}, "b.log")
        self.assertEqual(max(abs(xy[0] - 52), abs(xy[1] - 53)), 1)
        mism, _ = self.run_check([p])
        self.assertEqual(mism, [])

    def test_deliberate_wrong_fails(self):
        p, _ = self.case((), "c.log")
        mism, _ = self.run_check([p], wrong="nooffset")
        self.assertTrue(mism)

    def test_a_flat_control_is_reported(self):
        p, _ = self.case((), "d.log")
        _, flat = self.run_check([p])
        self.assertIn("noline", flat)         # open ground cannot tell the line mask from none
        self.assertNotIn("nooffset", flat)    # the offset start can

    def test_page4_and_the_wrong_reading(self):
        raw = bytes([0x18]) + (9).to_bytes(4, "little") + (5).to_bytes(4, "little") + (3).to_bytes(4, "little") + (4).to_bytes(4, "little")
        inv_b = [[9, 587, 255, 0, 0, 4]]
        inv_a = [[9, 587, 4, 5, 3, 0]]
        p = os.path.join(self.d, "e.log")
        with open(p, "w") as f:
            f.write('PLR {"lid":103}\n')
            f.write('ARM {"op":24,"field":"page","was":0,"now":4}\n')
            f.write("PKT " + json.dumps({"op": 24, "pkt": raw.hex(), "inv": inv_b}) + "\n")
            f.write("PKR " + json.dumps({"op": 24, "eax": 0, "inv": inv_a}) + "\n")
        mism, _ = self.run_check([p])
        self.assertEqual(mism, [])
        mism, _ = self.run_check([p], wrong="stashopen")
        self.assertTrue(mism)

    def test_expiry_and_monster(self):
        p = os.path.join(self.d, "f.log")
        it = {"id": 9, "c": 587, "mode": 4, "q": 2, "e": 0}
        with open(p, "w") as f:
            f.write("IPG " + json.dumps({"item": it, "f": 100, "room": 1, "x": 1, "y": 1}) + "\n")
            f.write("IPX " + json.dumps({"item": dict(it, e=15100), "f": 100}) + "\n")
            f.write("DCI " + json.dumps({"item": dict(it, id=10, e=0), "f": 100}) + "\n")
            f.write("SWP " + json.dumps({"f": 15000, "items": [[9, 587, 3, 15100, 1, 1], [10, 587, 3, 0, 1, 1]]}) + "\n")
            f.write("SWP " + json.dumps({"f": 16500, "items": [[10, 587, 3, 0, 1, 1]]}) + "\n")
            f.write("SWF " + json.dumps({"item": dict(it, e=15100), "f": 16500}) + "\n")
        mism, _ = self.run_check([p])
        self.assertEqual(mism, [])
        mism, _ = self.run_check([p], wrong="monster15000")
        self.assertTrue(mism)


class Model(unittest.TestCase):
    def test_pkt18(self):
        self.assertEqual(ii.pkt18_expect(4, True, 5, 3, 1, 1, True), (0, 4, (5, 3)))
        self.assertEqual(ii.pkt18_expect(4, False, 5, 3, 1, 1, True)[0], 3)
        self.assertEqual(ii.pkt18_expect(5, True, 0, 0, 1, 1, True)[0], 2)
        self.assertEqual(ii.pkt18_expect(4, True, 5, 4, 1, 1, False)[0], 3)       # classic stash is 6 x 4
        self.assertEqual(ii.pkt18_expect(4, True, 5, 3, 1, 1, True, ctl="stashopen")[0], 3)

    def test_belt23(self):
        self.assertTrue(ii.belt23_expect(12))
        self.assertFalse(ii.belt23_expect(16))
        self.assertFalse(ii.belt23_expect(3, occupied=(3,)))
        self.assertFalse(ii.belt23_expect(12, numboxes=12, ctl="numboxes"))


if __name__ == "__main__":
    unittest.main()
