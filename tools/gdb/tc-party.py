# gdb Python part of tools/gdb/tc-party.gdb (plan 0011): who is where when a monster drops.
#
# One breakpoint at TC_DropByIndex entry 0x0055AFA0 (ECX game, EDX source, [esp+4] killer), so its
# lines come before the DROP/TCR lines of the same call (tools/tc.py replay reads them there):
#
#   PLR id=<unit id> cls=<class> mode=<mode> x=<subtile x> y=<subtile y> lvl=<level id> dead=<+0xC6 bit 0>
#       one per player unit in the game's player lists (game+0x1120, 128 heads, next = unit+0xE4)
#   PTY id=<party id> members=<unit id>,<unit id>...
#       one per party in the party list (game+0x1D2C -> +4 first; party +0 u16 id, +4 member list
#       {unit id, next}, +8 next party)
#   KILL src=<source unit> sx=<x> sy=<y> slvl=<level> killer=<unit> ktype=<type> kid=<unit id> kx= ky= klvl=
#        [otype= oid=: a monster killer's owner as sub_0058F0D0_MonsterOwner finds it (plan 0044 Phase 2, MP04)]
#
# Offsets (read in the pinned game.exe, plan 0011, [I]): unit +0x0C id, +0x10 mode, +0x2C path;
# dynamic path +0x02 u16 x, +0x06 u16 y (0x006488C0, 0x00648900), +0x1C room (0x00648A80, used by
# sub_00620BB0_UnitGetRoom for types 0/1/3); room +0x10 -> DRLG room (0x0061A1B0), +0x58 -> level,
# +0x1D0 level id (0x0066BAB0);
# party structures from 0x00540290, 0x00540710 and sub_005405A0_PartyForEachInLevel.
import struct

import gdb

INF = gdb.selected_inferior()


def mem(addr, n):
    return bytes(INF.read_memory(addr, n))


def u32(addr):
    return struct.unpack("<I", mem(addr, 4))[0]


def u16(addr):
    return struct.unpack("<H", mem(addr, 2))[0]


def reg(name):
    return int(gdb.parse_and_eval("$" + name)) & 0xFFFFFFFF


def where(unit):
    """(x, y, level id) of a player or monster unit; -1 where a pointer is missing."""
    try:
        path = u32(unit + 0x2C)
        if not path:
            return -1, -1, -1
        x, y = u16(path + 2), u16(path + 6)
        room = u32(path + 0x1C)
    except gdb.MemoryError:
        return -1, -1, -1
    try:
        lvl = u32(u32(u32(room + 0x10) + 0x58) + 0x1D0) if room else -1
    except gdb.MemoryError:
        lvl = -2
    return x, y, lvl


class DropByIndex(gdb.Breakpoint):
    def stop(self):
        try:
            game, src = reg("ecx"), reg("edx")
            killer = u32(reg("esp") + 4)
            out = []
            for i in range(128):
                u = u32(game + 0x1120 + 4 * i)
                n = 0
                while u and n < 64:
                    x, y, lvl = where(u)
                    out.append("PLR id=%u cls=%u mode=%u x=%d y=%d lvl=%d dead=%u\n" % (
                        u32(u + 0x0C), u32(u + 4), u32(u + 0x10), x, y, lvl, mem(u + 0xC6, 1)[0] & 1))
                    u = u32(u + 0xE4)
                    n += 1
            plist = u32(game + 0x1D2C)
            p = u32(plist + 4) if plist else 0
            n = 0
            while p and n < 16:
                ids = []
                m = u32(p + 4)
                k = 0
                while m and k < 16:
                    ids.append(str(u32(m)))
                    m = u32(m + 4)
                    k += 1
                out.append("PTY id=%u members=%s\n" % (u16(p), ",".join(ids) or "-"))
                p = u32(p + 8)
                n += 1
            sx, sy, sl = where(src)
            line = "KILL src=%08x sx=%d sy=%d slvl=%d killer=%08x" % (src, sx, sy, sl, killer)
            if killer:
                kx, ky, kl = where(killer)
                line += " ktype=%u kid=%u kx=%d ky=%d klvl=%d" % (u32(killer), u32(killer + 0x0C), kx, ky, kl)
                if u32(killer) == 1:
                    # plan 0044 Phase 2 (MP04): the owner sub_0058F0D0_MonsterOwner resolves, MonsterData (+0x14)
                    # +0x28 -> {+0x2C id, +0x30 type} as it passes them to sub_00552F60_GameFindUnit (EDX type, id)
                    md = u32(killer + 0x14)
                    a = u32(md + 0x28) if md else 0
                    if a and u32(a + 0x28):
                        line += " otype=%u oid=%u" % (u32(a + 0x30), u32(a + 0x2C))
            out.append(line + "\n")
            gdb.write("".join(out))
        except gdb.MemoryError as ex:
            gdb.write("KILL error=%r\n" % str(ex).replace(" ", "_"))
        return False


DropByIndex("*0x0055AFA0", internal=True)
