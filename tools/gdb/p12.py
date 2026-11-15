# gdb Python logger for plan 0065 case P12 (backlog 2026-11-04 0054-p12, skills/missiles D3): a do-function-1 missile's
# own-cell test in sub_005AE1F0_MissileMoveCollide. Source it after tools/gdb/pilot.py (PLR, CB, RRESEED for the pilot
# and for the cell's grid). Read-only (ADR-0003): nothing here writes game memory or registers. Addresses refer to the
# pinned game.exe (image base 0x400000). One line per event, "TAG {json}".
#
#   MMC   0x005AE2CB, `test al, 5` after PathCellCollision (0x00648EB0) returned the missile's own-cell word: EAX = c
#         (u16, zero-extended at 0x005AE2C8), EBX the missile, ESI its mode (CollideType, unit +0x10), [ebp-0x14] the
#         game, [ebp-0x18] the path. Fields: mid (unit +0x0C), cls (+0x04), ct (ESI), c, x, y (path +0x02, +0x06, the
#         point PathCellCollision tests), sz (path +0x44, the size it passes), cached (path +0x7C: non-zero = the value
#         came from the path's cache +0x54, not a fresh CollisionTest), f (game +0xA8)
#   MMR   the function's two own exits after the test: 0x005AE3F1 (`mov eax, 2`, reached from the own-cell branch
#         0x005AE2D0 and from 0x005AE2B4/0x005AE2BC/0x005AE315/0x005AE3EA) and 0x005AE3C3 (`mov eax, 1`): mid, r (2 or 1)
#
# Only classes in P12_CLS (comma list, default "90", nova: pSrvDoFunc 1, CollideType 3) are written, so the per-frame
# lines stay bounded. Checked by tools/sweep8_check.py p12.
import json
import os
import struct

import gdb


def _p12_main():
    inf = gdb.selected_inferior()
    want = {int(x) for x in os.environ.get("P12_CLS", "90").split(",") if x.strip()}

    def mem(a, n):
        return bytes(inf.read_memory(a, n))

    def u16(a):
        return struct.unpack("<H", mem(a, 2))[0]

    def u32(a):
        return struct.unpack("<I", mem(a, 4))[0]

    def s32(a):
        return struct.unpack("<i", mem(a, 4))[0]

    def reg(n):
        return int(gdb.parse_and_eval("$" + n)) & 0xFFFFFFFF

    def emit(tag, d):
        gdb.write("%s %s\n" % (tag, json.dumps(d, separators=(",", ":"))))

    class Bp(gdb.Breakpoint):
        def __init__(self, addr, fn):
            super().__init__("*0x%08X" % addr, internal=True)
            self.silent = True
            self.fn = fn

        def stop(self):
            try:
                self.fn()
            except Exception as e:  # never stop the game on a logger error
                gdb.write("LOGERR p12 %r\n" % (e,))
            return False

    def on_mmc():
        m = reg("ebx")
        cls = s32(m + 4)
        if cls not in want:
            return
        bp = reg("ebp")
        game, path = u32(bp - 0x14), u32(bp - 0x18)
        emit("MMC", {"mid": u32(m + 0x0C), "cls": cls, "ct": reg("esi"), "c": reg("eax") & 0xFFFF,
                     "x": u16(path + 2), "y": u16(path + 6), "sz": s32(path + 0x44), "cached": u32(path + 0x7C),
                     "f": s32(game + 0xA8) if game else None})

    def mk_mmr(r):
        def on_mmr():
            m = reg("ebx")
            if s32(m + 4) in want:
                emit("MMR", {"mid": u32(m + 0x0C), "r": r})
        return on_mmr

    Bp(0x005AE2CB, on_mmc)
    Bp(0x005AE3F1, mk_mmr(2))
    Bp(0x005AE3C3, mk_mmr(1))
    gdb.write("P12 logger armed\n")


_p12_main()
