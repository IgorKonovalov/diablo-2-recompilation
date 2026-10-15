# gdb Python logger for plan 0026 Phase 2 (the outdoor generators). Sourced by tools/gdb/drlg-outdoor.gdb after
# tools/gdb/drlg-gen.py (whose OD0/OD1, PIC/PIO, PRC and RL lines it complements) and tools/gdb/drlg-maze.py (LNK*,
# LNKS, LWP). One line per event, "TAG {json}". Addresses refer to the pinned game.exe (image base 0x400000).
#
#   ODD   0x00675360 .. 0x006750F0  a hardware write watchpoint on the level seed (+0x1C4) from the outdoor build's
#                     entry (sub_00675360_OutdoorLevelBuild, ECX = level) to sub_006750F0_OutdoorRoomsCreate (EBX =
#                     level): every level-seed step of the outdoor window, collected and written as one line at the
#                     window's end: "lo" the new seed lo per step, "pc" the step's $pc (where the write retired)
#   ODG   0x006750F0  the window's end: the level's rect (+0x1C), the outdoor record (+0x14) flags (+0x00), cw/ch
#                     (+0x5C/+0x60), and the three grids the generators write, row-major: "defs" (+0x04), "grid0"
#                     (+0x18), "cells" (+0x2C) (DrlgGrid: +0 cells, +4 row offsets, +8 w, +0xC h)
import json
import struct

import gdb


def _outdoor_main():
    inf = gdb.selected_inferior()
    st = {}

    def mem(a, n):
        return bytes(inf.read_memory(a, n))

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
            except Exception as e:
                gdb.write("LOGERR outdoor %r\n" % (e,))
            return False

    class SeedWatch(gdb.Breakpoint):
        def __init__(self, level):
            super().__init__("*(int *) 0x%08X" % (level + 0x1C4), gdb.BP_WATCHPOINT, gdb.WP_WRITE, internal=True)
            self.silent = True
            self.level = level
            self.lo, self.pc = [], []

        def stop(self):
            try:
                self.lo.append(u32(self.level + 0x1C4))
                self.pc.append(int(gdb.parse_and_eval("$pc")) & 0xFFFFFFFF)
            except Exception as e:
                gdb.write("LOGERR outdoor %r\n" % (e,))
            return False

    def grid(g):
        cells, rows, w, h = u32(g), u32(g + 4), s32(g + 8), s32(g + 0xC)
        if not cells or w <= 0 or h <= 0:
            return []
        out = []
        for y in range(h):
            off = s32(rows + 4 * y) if rows else y * w
            out.extend(struct.unpack("<%dI" % w, mem(cells + 4 * off, 4 * w)))
        return out

    def on_od0():
        lv = reg("ecx")
        old = st.pop(lv, None)
        if old:
            old.delete()
        st[lv] = SeedWatch(lv)

    def on_od1():
        lv = reg("ebx")
        w = st.pop(lv, None)
        if w:
            w.delete()
            emit("ODD", {"level": lv, "id": u32(lv + 0x1D0), "n": len(w.lo), "lo": w.lo, "pc": w.pc})
        o = u32(lv + 0x14)
        emit("ODG", {"level": lv, "id": u32(lv + 0x1D0), "client": u32(u32(lv + 0x1B4) + 0x478),
                     "rect": list(struct.unpack("<iiii", mem(lv + 0x1C, 16))), "oflags": u32(o),
                     "cw": s32(o + 0x5C), "ch": s32(o + 0x60),
                     "defs": grid(o + 0x04), "grid0": grid(o + 0x18), "cells": grid(o + 0x2C)})

    for a, f in [(0x00675360, on_od0), (0x006750F0, on_od1)]:
        Bp(a, f)
    gdb.write("OUTDOOR logger armed\n")


_outdoor_main()
