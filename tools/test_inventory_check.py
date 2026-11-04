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


class Exclusion(unittest.TestCase):
    """The sweep exclusion class: a player's drop in no later dump and not freed is excluded only when the player's level
    record differs from the drop's level at every later sweep; with the player still on the level it stays a mismatch."""

    def log(self, later_lids):
        p = os.path.join(tempfile.mkdtemp(), "x.log")
        it = {"id": 9, "c": 587, "mode": 4, "q": 2, "e": 0}
        with open(p, "w") as f:
            f.write('PLR {"lid":103}\n')
            f.write("IPG " + json.dumps({"item": it, "f": 100, "room": 1, "x": 1, "y": 1}) + "\n")
            f.write("IPX " + json.dumps({"item": dict(it, e=15100), "f": 100}) + "\n")
            for lid in later_lids:
                f.write('PLR {"lid":%d}\n' % lid)
                f.write("SWP " + json.dumps({"f": 16500, "items": []}) + "\n")
        return p

    def run_check(self, p):
        preds = ic.predict([p])
        return ic.check(preds, [p], show=False)

    def test_player_still_on_level_is_a_mismatch(self):
        mism, _ = self.run_check(self.log([103]))
        self.assertTrue([m for m in mism if m[0]["kind"] == "sweep"])

    def test_player_elsewhere_is_excluded(self):
        mism, _ = self.run_check(self.log([102]))
        self.assertFalse([m for m in mism if m[0]["kind"] == "sweep"])

    def test_player_back_on_level_at_one_sweep_is_a_mismatch(self):
        mism, _ = self.run_check(self.log([102, 103]))
        self.assertTrue([m for m in mism if m[0]["kind"] == "sweep"])

    def test_no_player_record_is_a_mismatch(self):
        p = self.log([])
        with open(p, "a") as f:
            f.write("SWP " + json.dumps({"f": 16500, "items": []}) + "\n")
        mism, _ = self.run_check(p)
        self.assertTrue([m for m in mism if m[0]["kind"] == "sweep"])


class SaveExclusion(unittest.TestCase):
    """An item saved with its released room (SV1 logged) before the predicted free is not a sweep case; a save after the
    predicted free does not excuse an item that was not freed."""

    def log(self, sv_frame):
        p = os.path.join(tempfile.mkdtemp(), "s.log")
        it = {"id": 9, "c": 587, "mode": 4, "q": 2, "e": 0}
        with open(p, "w") as f:
            f.write('PLR {"lid":103}\n')
            f.write("IPG " + json.dumps({"item": it, "f": 100, "room": 1, "x": 1, "y": 1}) + "\n")
            f.write("IPX " + json.dumps({"item": dict(it, e=15100), "f": 100}) + "\n")
            f.write("SV1 " + json.dumps({"f": sv_frame, "saved": 18000, "item": dict(it, e=15100)}) + "\n")
            f.write("SWP " + json.dumps({"f": 16500, "items": [[9, 587, 3, 15100, 1, 1]]}) + "\n")
        return p

    def sweep_mism(self, p):
        mism, _ = ic.check(ic.predict([p]), [p], show=False)
        return [m for m in mism if m[0]["kind"] == "sweep"]

    def test_saved_before_the_predicted_free(self):
        self.assertEqual(self.sweep_mism(self.log(5000)), [])

    def test_saved_after_the_predicted_free_is_a_mismatch(self):
        self.assertTrue(self.sweep_mism(self.log(17000)))


class Restore(unittest.TestCase):
    def test_restore_rule(self):
        self.assertEqual(ic.restore_expect(0, 17000), 0)
        self.assertEqual(ic.restore_expect(20000, 17000), 20000)
        self.assertEqual(ic.restore_expect(15000, 17000), 17000)
        self.assertEqual(ic.restore_expect(17000, 17000), 17000)


class Potion(unittest.TestCase):
    def fake(self, wrong_seed=False):
        """A log of one hp1 use built from the model's own draws, with the stated stats; known outcome."""
        if not os.path.exists(ic.EXCEL):
            self.skipTest("no excel tables")
        classes = ic.item_classes()
        c = next(i for i, x in enumerate(classes) if x[0] == "hp1")
        low, high = 0x1234, 0x5678
        u = ii.Unit(typ=0, cls=1, low=low, high=high, stats={ii.VIT: 300, ii.ENE: 50})
        v = ii.potion_scale(u, ii.HPREGEN, 30)
        r2 = ii.Unit(typ=0, cls=1, low=low, high=high)
        a = r2.range(300)
        b = r2.range(100)
        s0, s1 = "%08x:%08x" % (low, high), "%08x:%08x" % (u.low, u.high)
        d = tempfile.mkdtemp()
        p = os.path.join(d, "u.log")
        ln = int(ic.misc_rows()["hp1"]["len"])
        tot = v
        with open(p, "w") as f:
            f.write("UP0 " + json.dumps({"user": 1, "ut": 0, "ucls": 1, "uid": 5, "item": {"c": c}, "f": 1000, "sd": s0,
                                         "stats": {"3": 300, "1": 50}}) + "\n")
            f.write("UD1 " + json.dumps({"sd": s0, "n": 300, "f": 1000}) + "\n")
            f.write("UD2 " + json.dumps({"r2": b, "h": a >> 1, "v": ii.life_mul(0, 1, 30 << 8), "sd": s1}) + "\n")
            f.write("UDV " + json.dumps({"v": v, "stat": 74}) + "\n")
            f.write("UAL " + json.dumps({"a": [0, 2, 1000 + ln, 0], "f": 1000}) + "\n")
            f.write("USS " + json.dumps({"list": 1, "stat": 74, "rate": ii.tdiv(tot, ln) + (1 if wrong_seed else 0), "f": 1000}) + "\n")
            f.write("UP1 " + json.dumps({"eax": 1, "f": 1000, "sd": s1, "stats": {}}) + "\n")
        return p

    def test_model_matches_its_own_log(self):
        p = self.fake()
        mism, _ = ic.check(ic.predict([p]), [p], show=False)
        self.assertEqual(mism, [])

    def test_a_rate_off_by_one_is_a_mismatch(self):
        p = self.fake(wrong_seed=True)
        mism, _ = ic.check(ic.predict([p]), [p], show=False)
        self.assertTrue(mism)

    def test_onedraw_reading_fails(self):
        p = self.fake()
        mism, _ = ic.check(ic.predict([p], "onedraw"), [p], show=False)
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
