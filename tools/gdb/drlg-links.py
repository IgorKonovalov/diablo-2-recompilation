# gdb Python logger for plan 0038 batch H5a (run:2026-10-17-sweep-links): the act link builder's tried choices and
# check results, the Act1B widening and LevelSeamsByTouch's RectTouch tests. Sourced by tools/gdb/sweep-links.gdb
# after drlg-maze.py (whose LNK0/LNKL/LK27/LNK1/LNKS lines frame these). One line per event, "TAG {json}". Addresses
# refer to the pinned game.exe (image base 0x400000). Seeds are printed "lo:hi".
#
#   LNKP  0x00677388  sub_006772C0_LevelLinkBuild, right after `call edx` (the pick): EAX = result, EDI = entry i;
#                     the LinkBuild block B at [ebp-0x204]: rect[i] (B+8+16i), dir (B+0xFC), dir0 (B+0x138),
#                     flip (B+0x174), flip0 (B+0x1B0) of entry i, and the seed copy (B+0)
#   LNKC  0x006773C5  right after `call eax` (the check): EAX = result, EDI = entry i
#   LNKW  0x00676F30  sub_00676EB0_LinkCheckAct1B after the widened RectGapTest, before the restore (ESI = B,
#                     EDI = 16 i): rect[0] as widened, rect[i], EAX = the test's result (the check's return value)
#   LNKT  0x00677606  sub_006775C0_LevelSeamsByTouch at its RectTouch call (EDI = level a, ESI = level b, ECX = &A.rect,
#                     EDX = &B.rect, [esp] = t)
#   LNKU  0x0067760B  right after it: EAX = the result
import json
import struct

import gdb


def _links_main():
    inf = gdb.selected_inferior()

    def mem(a, n):
        return bytes(inf.read_memory(a, n))

    def u32(a):
        return struct.unpack("<I", mem(a, 4))[0]

    def s32(a):
        return struct.unpack("<i", mem(a, 4))[0]

    def reg(r):
        return int(gdb.parse_and_eval("$" + r)) & 0xFFFFFFFF

    def sreg(r):
        v = reg(r)
        return v - (1 << 32) if v & 0x80000000 else v

    def rect(a):
        return list(struct.unpack("<iiii", mem(a, 16)))

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
                gdb.write("LOGERR links %r\n" % (e,))
            return False

    def on_pick():
        b = reg("ebp") - 0x204
        i = sreg("edi")
        emit("LNKP", {"i": i, "r": sreg("eax"), "rect": rect(b + 8 + 16 * i), "dir": s32(b + 0xFC + 4 * i),
                      "dir0": s32(b + 0x138 + 4 * i), "flip": s32(b + 0x174 + 4 * i), "flip0": s32(b + 0x1B0 + 4 * i),
                      "bseed": "%08x:%08x" % (u32(b), u32(b + 4))})

    def on_check():
        emit("LNKC", {"i": sreg("edi"), "r": sreg("eax")})

    def on_widen():
        b = reg("esi")
        i = reg("edi") >> 4
        emit("LNKW", {"i": i, "r0": rect(b + 8), "ri": rect(b + 8 + 16 * i), "r": sreg("eax")})

    def on_touch():
        emit("LNKT", {"a": sreg("edi"), "b": sreg("esi"), "ra": rect(reg("ecx")), "rb": rect(reg("edx")),
                      "t": s32(reg("esp"))})

    def on_touch_ret():
        emit("LNKU", {"r": sreg("eax")})

    for a, f in [(0x00677388, on_pick), (0x006773C5, on_check), (0x00676F30, on_widen), (0x00677606, on_touch),
                 (0x0067760B, on_touch_ret)]:
        Bp(a, f)
    gdb.write("LINKS logger armed\n")


_links_main()
