# gdb Python logger for plan 0065 case MP32 (multiplayer/0001 § 2; multiplayer/0002 §§ 1, 3): the gold pickup and the
# party share on the HOST (the server game, ADR-0008). Source it after tools/gdb/pilot.py and tools/gdb/two-players.py
# (PLRS: both players' party, level, mode and position), as tools/gdb/two-gold.gdb does. Read-only (ADR-0003).
# Addresses refer to the pinned game.exe (image base 0x400000). One line per event, "TAG {json}".
#
#   GP0   0x0055C87C in sub_0055C850_GoldPickup, after both stat-14 reads (ESI the picker, EDI its cap from
#         PLAYER_GoldCap 0x00622E70, [ebp-0xC] its gold, EBX the pile's amount, [ebp+0xC] the pile, [ebp+8] the game):
#         pid, cap, gold, amt, the pile's id and +0xC8, and "pl": every player of the game (game +0x1120, 128 heads,
#         next +0xE4) as [id, gold (base stat 14), level (base stat 12), mode]
#   GPO   0x0055C8A9, UnitGetOwner(game, pile)'s result (EAX): [type, class, id] or null
#   GS0   0x00540900 sub_00540900_PartyGoldShare entry (ECX game, EDX picker, [esp+4] amt)
#   GSN   0x00540A20, the `idiv` of the share (EAX amt, [ebp-4] n, the members PartyCountAliveCb counted)
#   GC    0x0054066C in sub_00540650_PartyGoldClip (EBX the member, ESI the share, EDI its cap, EAX its gold)
#   GSF   0x00540ADF, the picker's final clip in the share's loop path (ESI the picker, EBX left, EDI its cap, EAX its gold)
#   GA    0x0053FF00 sub_0053FF00_UnitAddGoldStat entry (ECX unit, EDX stat, [esp+4] the amount)
#   GPR   0x0055C8DC, the share's return stored as the pickup's rest (EAX)
#   GPE   0x0055C92F, the pickup's adds done: "pl" as at GP0
# Ready line "TWO-GOLD logger armed". Checked by tools/mp_check.py gold.
import json
import struct

import gdb


def _two_gold_main():
    inf = gdb.selected_inferior()
    st = {"game": 0}

    def mem(a, n):
        return bytes(inf.read_memory(a, n))

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

    def emit(tag, d):
        g = st["game"]
        try:
            d["f"] = s32(g + 0xA8) if g else None
        except gdb.MemoryError:
            d["f"] = None
        gdb.write("%s %s\n" % (tag, json.dumps(d, separators=(",", ":"))))

    def base_stat(u, sid):
        lst = u32(u + 0x5C)
        if not lst:
            return None
        arr, n = u32(lst + 0x24), s16(lst + 0x28)
        if not arr or n <= 0 or n > 1024:
            return None
        for k, v in struct.iter_unpack("<Ii", mem(arr, 8 * n)):
            if k == sid << 16:
                return v
        return 0

    def tci(u):
        return [u32(u), s32(u + 4), u32(u + 0x0C)] if u else None

    def players(game):
        out = []
        for i in range(128):
            u, k = u32(game + 0x1120 + 4 * i), 0
            while u and k < 16:
                out.append([u32(u + 0x0C), base_stat(u, 14), base_stat(u, 12), u32(u + 0x10)])
                u, k = u32(u + 0xE4), k + 1
        return out

    class Bp(gdb.Breakpoint):
        def __init__(self, addr, fn):
            super().__init__("*0x%08X" % addr, internal=True)
            self.silent = True
            self.fn = fn

        def stop(self):
            try:
                self.fn()
            except Exception as e:  # never stop the game on a logger error
                gdb.write("LOGERR two-gold %r\n" % (e,))
            return False

    def on_gp0():
        bp = reg("ebp")
        game, pile, picker = u32(bp + 8), u32(bp + 0x0C), reg("esi")
        st["game"] = game
        emit("GP0", {"pid": u32(picker + 0x0C), "cap": sreg("edi"), "gold": s32(bp - 0x0C), "amt": sreg("ebx"),
                     "pile": u32(pile + 0x0C) if pile else None, "c8": u32(pile + 0xC8) if pile else None,
                     "pl": players(game)})

    def on_gpo():
        emit("GPO", {"owner": tci(reg("eax"))})

    def on_gs0():
        emit("GS0", {"pid": u32(reg("edx") + 0x0C), "amt": s32(reg("esp") + 4)})

    def on_gsn():
        emit("GSN", {"amt": sreg("eax"), "n": s32(reg("ebp") - 4)})

    def on_gc():
        emit("GC", {"mid": u32(reg("ebx") + 0x0C), "share": sreg("esi"), "cap": sreg("edi"), "gold": sreg("eax")})

    def on_gsf():
        emit("GSF", {"pid": u32(reg("esi") + 0x0C), "left": sreg("ebx"), "cap": sreg("edi"), "gold": sreg("eax")})

    def on_ga():
        u = reg("ecx")
        emit("GA", {"uid": u32(u + 0x0C) if u else None, "stat": reg("edx"), "v": s32(reg("esp") + 4)})

    def on_gpr():
        emit("GPR", {"rest": sreg("eax")})

    def on_gpe():
        emit("GPE", {"pl": players(st["game"]) if st["game"] else None})

    for a, f in ((0x0055C87C, on_gp0), (0x0055C8A9, on_gpo), (0x00540900, on_gs0), (0x00540A20, on_gsn),
                 (0x0054066C, on_gc), (0x00540ADF, on_gsf), (0x0053FF00, on_ga), (0x0055C8DC, on_gpr),
                 (0x0055C92F, on_gpe)):
        Bp(a, f)
    gdb.write("TWO-GOLD logger armed\n")


_two_gold_main()
