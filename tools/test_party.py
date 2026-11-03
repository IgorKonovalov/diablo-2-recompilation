#!/usr/bin/env python3
"""Tests for tools/player.py's kill model (plan 0058 Phase 1): the share's integer steps against the instruction forms,
the member tests, the n = 1 credit and the cap. The code itself is compared by tools/party_emu.py.
Run: python3 -I tools/test_party.py"""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import party_emu  # noqa: E402
import player  # noqa: E402

T = party_emu.XT()


def unit(uid, x, y, level=30, **kw):
    u = dict(type=0, cls=0, id=uid, mode=1, x=x, y=y, room=2, base={12: level, 13: (level - 1) << 25 | 5, 29: 0})
    u.update(kw)
    return u


def monster(x=1000, y=1000, exp=1000, mlvl=30, **kw):
    u = dict(type=1, cls=1, id=900, mode=0, x=x, y=y, room=2, base={12: mlvl, 13: exp})
    u.update(kw)
    return u


def xc_units(ev):
    return [e[1] for e in ev if e[0] == "XC"]


class Share(unittest.TestCase):
    def test_total_truncates(self):
        self.assertEqual(player.xp_share_total(100, 2), 100 + 8900 // 256)
        self.assertEqual(player.xp_share_total(63, 3), 63 + (2 * 63 * 89) // 256)

    def test_total_wraps_at_the_bound(self):
        top = (2 ** 31 - 1) // 89
        self.assertEqual(player.xp_share_total(top, 2), top + (top * 89) // 256)
        over = player.i32((top + 1) * 89)
        self.assertLess(over, 0)
        self.assertEqual(player.xp_share_total(top + 1, 2), top + 1 - ((-over) // 256))
        self.assertNotEqual(player.xp_share_total(top + 1, 2), player.xp_share_total(top + 1, 2, floor=True))

    def test_input_is_not_rounded_to_f32(self):
        q = player.xp_share_q(player.xp_share_total(63, 2), 162)
        self.assertEqual(player.xp_share_input(81, q), 41)
        self.assertEqual(player.xp_share_input(81, q, f32_product=True), 42)

    def test_inputs_for_eight(self):
        got = player.xp_share_inputs(1000, [10] * 8)
        self.assertEqual(got, [int(10 * player.f32((1000 + 7 * 1000 * 89 // 256) / 80.0))] * 8)


class Members(unittest.TestCase):
    def world(self, *us, guids=None):
        return player.KillWorld(list(us), [dict(id=3, guids=guids or [u["id"] for u in us if u["type"] == 0])])

    def test_bound_is_from_the_monster_and_inclusive(self):
        m = monster()
        a, b, c = unit(1, 1000 + 80, 1000), unit(2, 1000, 1000 + 81), unit(3, 1000 - 48, 1000 + 64)
        got, fatal = player.party_collect(self.world(a, b, c, m), a, m)
        self.assertEqual([u["id"] for u, _ in got], [1, 3])
        self.assertFalse(fatal)
        got, _ = player.party_collect(self.world(a, b, c, m), a, m, type("O", (player.KillOpts,), {"strict": True}))
        self.assertEqual(got, [])

    def test_d2_wraps_to_32_bits(self):
        m = monster(x=65535, y=1000)
        k = unit(1, 65530, 1000)
        o = unit(2, 1, 1512)    # 65534^2 + 512^2 = 2^32 + 4
        got, _ = player.party_collect(self.world(k, o, m), k, m)
        self.assertEqual([u["id"] for u, _ in got], [1, 2])

    def test_position_zero_drops_the_member(self):
        m = monster(x=0)
        k = unit(1, 1, 1000)
        self.assertEqual(player.party_collect(self.world(k, m), k, m)[0], [])
        m = monster()
        k, o = unit(1, 1000, 1000), unit(2, 0, 1000)
        self.assertEqual([u["id"] for u, _ in player.party_collect(self.world(k, o, m), k, m)[0]], [1])

    def test_ninth_is_fatal_only_when_it_passes(self):
        m = monster()
        us = [unit(i + 1, 1000, 1000) for i in range(9)]
        self.assertTrue(player.party_collect(self.world(*us, m), us[0], m)[1])
        us[8]["mode"] = 0x11
        got, fatal = player.party_collect(self.world(*us, m), us[0], m)
        self.assertFalse(fatal)
        self.assertEqual(len(got), 8)

    def test_level_is_the_credited_players(self):
        m = monster(room=5)
        k, o, p = unit(1, 1000, 1000, room=2), unit(2, 1000, 1000, room=5), unit(3, 1000, 1000, room=2)
        self.assertEqual([u["id"] for u, _ in player.party_collect(self.world(k, o, p, m), k, m)[0]], [1, 3])

    def test_list_order(self):
        m = monster()
        a, b = unit(1, 1000, 1000), unit(2, 1000, 1000)
        got, _ = player.party_collect(self.world(a, b, m, guids=[2, 1]), a, m)
        self.assertEqual([u["id"] for u, _ in got], [2, 1])


class Kill(unittest.TestCase):
    def test_one_member_credits_the_killer_whoever_it_is(self):
        m = monster()
        k, o = unit(1, 1500, 1000), unit(2, 1000, 1000, level=40)
        W = player.KillWorld([k, o, m], [dict(id=3, guids=[1, 2])])
        ev, end = player.kill_events(W, T, k, m)
        self.assertEqual(end, "ret")
        self.assertEqual(xc_units(ev), [1])
        self.assertEqual([e for e in ev if e[0] == "XC"][0][2:4], (1000, 30))

    def test_no_member_no_experience(self):
        m = monster()
        k, o = unit(1, 1500, 1000), unit(2, 1600, 1000)
        W = player.KillWorld([k, o, m], [dict(id=3, guids=[1, 2])])
        self.assertEqual(player.kill_events(W, T, k, m), ([], "ret"))

    def test_unpartied_has_no_test(self):
        m = monster()
        k = unit(1, 9000, 1000, mode=0x11)
        ev, _ = player.kill_events(player.KillWorld([k, m]), T, k, m)
        self.assertEqual(xc_units(ev), [1])

    def test_minion_and_state_credit(self):
        m = monster()
        p, q = unit(1, 1000, 1000), unit(2, 1000, 1000)
        s = dict(type=1, cls=1, id=300, mode=1, x=1, y=1, room=2, base={}, link=(0, 1))
        W = player.KillWorld([p, q, s, m])
        self.assertIs(W.credit(s, m), p)
        s2 = dict(s, states=57, flag0x800=(0, 2))
        self.assertIs(W.credit(s2, m), q)
        s3 = dict(s, states=60, flag0x800=(0, 2))
        self.assertIs(W.credit(s3, m), p)
        self.assertIs(W.credit(s, dict(m, states=59, flag0x800=(0, 2))), q)
        self.assertIsNone(W.credit(dict(s, link=None), m))
        self.assertIs(W.credit(p, dict(m, states=59, flag0x800=(0, 2))), p)

    def test_mercenary_part(self):
        self.assertEqual(player.trunc_sar8(1000 * 86), 335)
        self.assertEqual(player.trunc_sar8(-255), 0)
        self.assertEqual(player.trunc_sar8(-256), -1)


if __name__ == "__main__":
    unittest.main()
