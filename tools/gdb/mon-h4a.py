# gdb Python logger for plan 0038 batch H4a (monsters-a): new tags only, sourced by tools/gdb/mon-h4a.gdb after every
# file that tools/gdb/mon-stats.gdb sources (mon-extra.py included), whose tags it leaves unchanged. One line per event,
# "TAG {json}". Addresses refer to the pinned game.exe (image base 0x400000). Checked by tools/sweep_h4a.py. See
# docs/findings/monsters/0003-special-monsters.md § 6 and the sections "Plan 0038 batch H4a".
#
# SuperUniqueSpawn's tails (sub_005A49B0_SuperUniqueSpawn, the switch at 0x005A4BF7 on the record's +0x08):
#   SUC  at every call instruction of the tail cases (0x005A4BFE..0x005A4E43): site, callee, ECX, EDX, the first five
#        stack dwords (the pushed arguments), the unit seed of EDX when EDX is a unit
#   SUCR at the return address of the calls whose result the tail uses or that create units: site, EAX
#   SURD 0x005A4CDE after Radament's RNG_Range(unit +0x20, 5): EAX, the unit seed after
# The Chaos Sanctuary population gate (sub_0054EBC0_RoomPopulateGate, level 108 only):
#   GQ   0x0054EC27 after sub_005B5210(game) (the quest-record byte): room (EDI), game (EBX), EAX
# Harness helper (not a model input): MON as tools/gdb/pilot.py writes it (its header), at a player's mark and at
#   PATH_SetMarkMask, at most every 0.3 s; the game pointer from GAME_InitSeeds 0x0052C312 (EDI), no line.
import json
import struct
import time

import gdb


def _monh4a_main():
    inf = gdb.selected_inferior()

    def mem(a, n):
        return bytes(inf.read_memory(a, n))

    def u32(a):
        return struct.unpack("<I", mem(a, 4))[0]

    def reg(n):
        return int(gdb.parse_and_eval("$" + n)) & 0xFFFFFFFF

    def emit(tag, d):
        gdb.write("%s %s\n" % (tag, json.dumps(d, separators=(",", ":"))))

    def us(u):
        try:
            if u and u32(u) == 1:
                return "%08x:%08x" % struct.unpack("<II", mem(u + 0x20, 8))
        except gdb.MemoryError:
            pass
        return None

    class Bp(gdb.Breakpoint):
        def __init__(self, addr, fn):
            super().__init__("*0x%08X" % addr, internal=True)
            self.silent = True
            self.fn = fn

        def stop(self):
            try:
                self.fn()
            except Exception as e:  # never stop the game on a logger error; log it instead
                gdb.write("LOGERR mon-h4a %r\n" % (e,))
            return False

    # call sites of the tail cases: site -> callee (read from the disassembly at 0x005A4BFE..0x005A4E43)
    calls = {
        0x005A4C03: 0x00639DB0, 0x005A4C0E: 0x005436B0, 0x005A4C1A: 0x005B0E00, 0x005A4C27: 0x005A4850,
        0x005A4C47: 0x005436B0, 0x005A4C50: 0x00545B50, 0x005A4C5D: 0x005A4850,
        0x005A4C7D: 0x005436B0, 0x005A4C8A: 0x005A4850,
        0x005A4CAA: 0x005436B0, 0x005A4CB7: 0x005A4850,
        0x005A4CD9: 0x0045C390,
        0x005A4CF1: 0x005B23C0, 0x005A4D0A: 0x005B23C0, 0x005A4D1E: 0x005B23C0, 0x005A4D32: 0x005B23C0,
        0x005A4D46: 0x005B23C0, 0x005A4D53: 0x005A4850,
        0x005A4D7E: 0x005B24E0, 0x005A4D89: 0x005436B0, 0x005A4D92: 0x00545B50, 0x005A4D9C: 0x00639DB0,
        0x005A4DA9: 0x005A4850,
        0x005A4DD8: 0x0058F030, 0x005A4DE3: 0x00620BB0, 0x005A4DE9: 0x0063EC70, 0x005A4DFB: 0x005B24E0,
        0x005A4E06: 0x005436B0, 0x005A4E13: 0x005A4850,
        0x005A4E3E: 0x005B24E0, 0x005A4E4B: 0x005A4850,
    }
    # returns logged (the call's site + 5): unit creations, the class lookups, the escort spawns
    rets = {0x005A4CF1, 0x005A4D0A, 0x005A4D1E, 0x005A4D32, 0x005A4D46, 0x005A4D7E, 0x005A4DE3, 0x005A4DE9,
            0x005A4DFB, 0x005A4E3E}

    def on_call(site, to):
        def fn():
            esp, edx = reg("esp"), reg("edx")
            emit("SUC", {"at": site, "to": to, "ecx": reg("ecx"), "edx": edx,
                         "st": list(struct.unpack("<5I", mem(esp, 20))), "us": us(edx)})
        return fn

    def on_ret(site):
        def fn():
            emit("SUCR", {"at": site, "eax": reg("eax")})
        return fn

    for site, to in sorted(calls.items()):
        Bp(site, on_call(site, to))
        if site in rets:
            Bp(site + 5, on_ret(site))

    def on_radament():
        u = reg("edi")
        emit("SURD", {"u": u, "eax": reg("eax"), "us": us(u)})

    Bp(0x005A4CDE, on_radament)

    def on_gate():
        emit("GQ", {"room": reg("edi"), "game": reg("ebx"), "eax": reg("eax")})

    Bp(0x0054EC27, on_gate)

    # --- harness helper (not a model input): MON as tools/gdb/pilot.py writes it, so that tools/d2pilot.py hunt and
    # farm see the monsters; pilot.py itself is not sourced (its PLR, CB and RRESEED would repeat the model loggers').
    hs = {"game": 0, "t": 0.0, "tf": 0.0, "pos": None}
    BOSSES = {156, 211, 229, 242, 243, 250, 256, 267, 526, 544}

    def u16(a):
        return struct.unpack("<H", mem(a, 2))[0]

    def s32(a):
        return struct.unpack("<i", mem(a, 4))[0]

    def stat(u, sid):
        sl = u32(u + 0x5C)
        if not sl:
            return None
        arr, n = u32(sl + 0x24), struct.unpack("<h", mem(sl + 0x28, 2))[0]
        for i in range(max(0, min(n, 512))):
            k, v = struct.unpack("<Ii", mem(arr + 8 * i, 8))
            if k >> 16 == sid and k & 0xFFFF == 0:
                return v
        return None

    def mons(x, y, far):
        g = hs["game"]
        out = []
        if not g:
            return out
        for u in struct.unpack("<128I", mem(g + 0x1320, 512)):
            k = 0
            while u and k < 256:
                k += 1
                try:
                    p = u32(u + 0x2C)
                    if p:
                        mx, my = u16(p + 2), u16(p + 6)
                        md = u32(u + 0x14)
                        near = abs(mx - x) <= 48 and abs(my - y) <= 48
                        if far and not near:
                            near = s32(u + 4) in BOSSES or (md and mem(md + 0x16, 1)[0] & 0x0E)
                        if near:
                            hp = stat(u, 6)
                            out.append({"id": u32(u + 0xC), "cls": s32(u + 4), "mode": u32(u + 0x10), "x": mx,
                                        "y": my, "hp": hp >> 8 if hp is not None else None, "lr": stat(u, 41),
                                        "mf": mem(md + 0x16, 1)[0] if md else None,
                                        "mods": [b for b in mem(md + 0x1C, 9) if b] if md else []})
                except gdb.MemoryError:
                    pass
                u = u32(u + 0xE4)
        return out

    def scan():
        now = time.time()
        if hs["pos"] is None or now - hs["t"] < 0.3:
            return
        hs["t"] = now
        far = now - hs["tf"] >= 2.0
        if far:
            hs["tf"] = now
        emit("MON", {"x": hs["pos"][0], "y": hs["pos"][1], "far": far, "m": mons(hs["pos"][0], hs["pos"][1], far)})
        gdb.flush()

    def on_game():
        hs["game"] = reg("edi")

    def on_mark():
        esp = reg("esp")
        _room, x, y, _pat, mask = struct.unpack("<IiiII", mem(esp + 4, 20))
        if mask == 0x80:
            hs["pos"] = (x, y)
            scan()

    Bp(0x0052C312, on_game)
    Bp(0x0064EA90, on_mark)
    Bp(0x00648C30, scan)
    gdb.write("MONH4A logger armed\n")


_monh4a_main()
