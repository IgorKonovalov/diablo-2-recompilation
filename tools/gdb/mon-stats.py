# gdb Python logger for plan 0025 Phase 2 (monster stats at creation and after the special-mod handlers). Sourced by
# tools/gdb/mon-stats.gdb after the plan 0014-0018 loggers (drlg-gen.py, drlg-roomk.py, mon-spawn.py, collision.py,
# mon-special.py), whose tags it leaves unchanged. One line per event, "TAG {json}". Addresses refer to the pinned
# game.exe (image base 0x400000). "us" is the unit seed (+0x20) as "lo:hi". See docs/findings/monsters/0004-stats.md.
#
# Stat lists (unit +0x5C, a list with flag 0x80000000 in +0x10): "b" the base entries (+0x24 array, +0x28 s16 count)
# as [[stat, param, value], ...]; "f" the full entries (+0x48 / +0x4C); "sub" the attached lists (head +0x3C, next
# +0x2C): [flags +0x10, state u16 +0x14, entries +0x24]. An entry is {u32 stat << 16 | param, s32 value}.
#
# sub_00573CB0_MonStatsInit (ESI = unit; stack game, room, region entry):
#   SI0  entry: unit, id, class, us, game, room and its level id (room +0x10 DRLG room, +0x58 level, +0x1D0), the region
#        entry, its variant-set count (+0x03) and the 48 variant bytes (+0x04), the game bytes
#        +0x6A, +0x6D, +0x70 (expansion), +0x74, and g_PlayersSetting 0x00883D70 (the /players value)
#   SI1  0x00573DC1 after MonPlayerBonus: its out record [ebp-0x24] (hpPct, xpPct, skillBonus, difficulty, players),
#        us (after the appearance pick and the doomknight draws), the 16 appearance bytes MonsterData +0x04
#   SI2  0x00573F83 after MonLvlStats(mask 7): level [ebp-4], L [ebp+0xC], d (EDI), the out record (minHp, maxHp, ac,
#        exp at [ebp-0x5C], [-0x58], [-0x54], [-0x4C])
#   SI3  0x00573F94 after the HP draw: the draw (EAX), us
#   SI4  0x0057406F after MonClassicDiffAdjust: base stats
#   SI5  0x00574226 after the MonProp slots (before MonEquipInit): us, base, full and attached lists
#   SIX  0x0057423A the exit (after MonEquipInit; only after an SI5 of the same unit): us, base, full, sub
# Special-mod handlers (sub_005A2120_SpecialModsApply), the same call points as HD0/HDX and TH0/TH1 of mon-special.py:
#   HST  after a handler with flag 1 (0x005A2155 / 0x005A21AE, only after its call 0x005A2153 / 0x005A21AC): mod,
#        unit, monster flags (MonsterData +0x16), the mod bytes, us, base stats
#   TST  after the group-member thunk's call 0x005A2115 (flag 0): mod, member, the same fields
# Player-count change (no-rescale case): at each PLR point (COLL_PatternMark 0x0064EA90, a player's mark) the logger
#   reads g_PlayersSetting; when it differs from the last value seen, PCHG {old, new} and, for every monster in the
#   game's unit lists (game +0x1320, 128 heads, next +0xE4), LIVE {u, id, cls, mf, stats 6, 7, 12, 13, 100 (base)}.
import json
import struct

import gdb


def _monstats_main():
    inf = gdb.selected_inferior()
    G_PLAYERS = 0x00883D70
    st = {"game": 0, "ms5": set(), "hd": {}, "th": {}, "players": None}

    def mem(a, n):
        return bytes(inf.read_memory(a, n))

    def u8(a):
        return mem(a, 1)[0]

    def u16(a):
        return struct.unpack("<H", mem(a, 2))[0]

    def s16(a):
        return struct.unpack("<h", mem(a, 2))[0]

    def u32(a):
        return struct.unpack("<I", mem(a, 4))[0]

    def s32(a):
        return struct.unpack("<i", mem(a, 4))[0]

    def reg(n):
        return int(gdb.parse_and_eval("$" + n)) & 0xFFFFFFFF

    def sreg(n):
        v = reg(n)
        return v - (1 << 32) if v & 0x80000000 else v

    def thn():
        t = gdb.selected_thread()
        return t.num if t else 0

    def us(u):
        return "%08x:%08x" % struct.unpack("<II", mem(u + 0x20, 8))

    def emit(tag, d):
        gdb.write("%s %s\n" % (tag, json.dumps(d, separators=(",", ":"))))

    def arr(p, off_a, off_n):
        a, n = u32(p + off_a), s16(p + off_n)
        if not a or n <= 0 or n > 512:
            return []
        return [[k >> 16, k & 0xFFFF, v] for k, v in struct.iter_unpack("<Ii", mem(a, 8 * n))]

    def lists(u, full=True):
        lst = u32(u + 0x5C)
        if not lst:
            return {"b": None}
        d = {"b": arr(lst, 0x24, 0x28)}
        if full:
            ex = u32(lst + 0x10) & 0x80000000
            d["lf"] = u32(lst + 0x10)
            d["f"] = arr(lst, 0x48, 0x4C) if ex else None
            sub = []
            p = u32(lst + 0x3C) if ex else 0
            k = 0
            while p and k < 32:
                k += 1
                sub.append([u32(p + 0x10), u16(p + 0x14), arr(p, 0x24, 0x28)])
                p = u32(p + 0x2C)
            d["sub"] = sub
        return d

    def mdata(u):
        md = u32(u + 0x14)
        if not md:
            return {}
        return {"mf": u16(md + 0x16), "mods": list(mem(md + 0x1C, 9))}

    class Bp(gdb.Breakpoint):
        def __init__(self, addr, fn):
            super().__init__("*0x%08X" % addr, internal=True)
            self.silent = True
            self.fn = fn

        def stop(self):
            try:
                self.fn()
            except Exception as e:  # never stop the game on a logger error; log it instead
                gdb.write("LOGERR %r\n" % (e,))
            return False

    # --- MonStatsInit --------------------------------------------------------------------------------------------
    def on_ms0():
        u, esp = reg("esi"), reg("esp")
        game, room, ent = u32(esp + 4), u32(esp + 8), u32(esp + 0xC)
        if not u or s32(u) != 1:
            return
        st["game"] = game
        dr = u32(room + 0x10) if room else 0
        lid = s32(u32(dr + 0x58) + 0x1D0) if dr else None
        emit("SI0", {"u": u, "id": u32(u + 0xC), "cls": s32(u + 4), "us": us(u), "game": game, "room": room,
                     "lid": lid, "ent": ent, "nvar": u8(ent + 3) if ent else None,
                     "vb": mem(ent + 4, 48).hex() if ent else None, "g6a": u8(game + 0x6A), "g6d": u8(game + 0x6D),
                     "exp": u32(game + 0x70), "g74": u32(game + 0x74), "pset": s32(G_PLAYERS)})

    def on_ms1():
        u, ebp = reg("esi"), reg("ebp")
        pb = struct.unpack("<5i", mem(ebp - 0x24, 20))
        md = u32(u + 0x14)
        emit("SI1", {"u": u, "pb": list(pb), "us": us(u), "app": mem(md + 4, 16).hex() if md else None})

    def on_ms2():
        u, ebp = reg("esi"), reg("ebp")
        o = struct.unpack("<4i", mem(ebp - 0x5C, 16))
        emit("SI2", {"u": u, "lvl": s32(ebp - 4), "L": s32(ebp + 0xC), "d": sreg("edi"),
                     "o": [o[0], o[1], o[2], s32(ebp - 0x4C)]})

    def on_ms3():
        u = reg("esi")
        emit("SI3", {"u": u, "r": reg("eax"), "us": us(u)})

    def on_ms4():
        u = reg("esi")
        emit("SI4", {"u": u, "b": lists(u, False)["b"]})

    def on_ms5():
        u = reg("esi")
        st["ms5"].add(u)
        d = {"u": u, "us": us(u)}
        d.update(lists(u))
        emit("SI5", d)

    def on_msx():
        u = reg("esi")
        if u not in st["ms5"]:
            return
        st["ms5"].discard(u)
        d = {"u": u, "us": us(u)}
        d.update(lists(u))
        emit("SIX", d)

    Bp(0x00573CB0, on_ms0)
    Bp(0x00573DC1, on_ms1)
    Bp(0x00573F83, on_ms2)
    Bp(0x00573F94, on_ms3)
    Bp(0x0057406F, on_ms4)
    Bp(0x00574226, on_ms5)
    Bp(0x0057423A, on_msx)

    # --- handlers ------------------------------------------------------------------------------------------------
    def on_hd0():
        st["hd"][thn()] = (reg("edi"), reg("esi"))

    def on_hdx():
        p = st["hd"].pop(thn(), None)
        if p is None:
            return          # 0x005A2155 / 0x005A21AE are also the jump targets of a null handler
        u, m = p
        d = {"m": m, "u": u, "us": us(u)}
        d.update(mdata(u))
        d["b"] = lists(u, False)["b"]
        emit("HST", d)

    for a in (0x005A2153, 0x005A21AC):
        Bp(a, on_hd0)
    for a in (0x005A2155, 0x005A21AE):
        Bp(a, on_hdx)

    def on_th0():
        st["th"][thn()] = (reg("ecx"), reg("edx"))

    def on_th1():
        p = st["th"].pop(thn(), None)
        if p is None:
            return
        u, m = p
        d = {"m": m, "u": u, "us": us(u)}
        d.update(mdata(u))
        d["b"] = lists(u, False)["b"]
        emit("TST", d)

    Bp(0x005A2113, on_th0)
    Bp(0x005A2115, on_th1)

    # --- player-count change ---------------------------------------------------------------------------------------
    def on_plr():
        esp = reg("esp")
        if u32(esp + 0x14) != 0x80:
            return
        p = s32(G_PLAYERS)
        old = st["players"]
        st["players"] = p
        if old is None or old == p or not st["game"]:
            return
        emit("PCHG", {"old": old, "new": p})
        g = st["game"]
        heads = struct.unpack("<128I", mem(g + 0x1320, 512))
        for u in heads:
            k = 0
            while u and k < 512:
                k += 1
                try:
                    if s32(u) == 1:
                        lst = u32(u + 0x5C)
                        b = arr(lst, 0x24, 0x28) if lst else []
                        sv = {str(i): v for i, prm, v in b if prm == 0 and i in (6, 7, 12, 13, 100)}
                        d = {"u": u, "id": u32(u + 0xC), "cls": s32(u + 4), "s": sv}
                        d.update(mdata(u))
                        emit("LIVE", d)
                except gdb.MemoryError:
                    break
                u = u32(u + 0xE4)
        gdb.flush()

    Bp(0x0064EA90, on_plr)
    gdb.write("MONSTATS logger armed\n")


_monstats_main()
