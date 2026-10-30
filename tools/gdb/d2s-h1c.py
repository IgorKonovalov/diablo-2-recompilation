# gdb Python logger for plan 0038 batch H1c (run:2026-10-27-sweep-d2s-legacy): the legacy reader's steps, on top of
# tools/gdb/d2s-io.py, d2s-h1b.py and d2s-h1a.py (all sourced first by tools/gdb/d2s-h1c.gdb, unchanged). One line per
# event, "TAG {json}"; every name here starts with h1c_. Addresses refer to the pinned game.exe (image base 0x400000);
# names are those of docs/findings/save/0001-d2s-io.md (lane/rlg).
#
# Calls (entry line, then the return line at the caller's return address, both with the raw words the line names):
#   NCL / NCLR  0x00532590 sub_00532590_NewCharLegacy: ECX, EDX, [esp+4..0x10] / EAX
#   MOS / MOSR  0x00533C70 sub_00533C70_ReadMercOldSave: ECX (game), EDX, [esp+4] owner, [esp+8] buffer, [esp+0xC]
#               version, [esp+0x10] bytes left, [esp+0x14] -> length out, the first 0x12 bytes at the buffer / EAX and
#               the length written
#   MXO / MXOR  0x00533BF0 sub_00533BF0_MercExpFromOldSave: ECX game, DX hireling id, [esp+4] experience / EAX
#   MCR / MCRR  0x005774F0 MERC_Create: ECX game, EDX owner, [esp+4..0x14] (name, seed, id, record +0x08, dead) / EAX
#   SEC / SECR  the legacy reader's section readers: header 0x00532690, quests 0x00532BE0, waypoints 0x00532C70, NPCs
#               0x00532D00, stats 0x00532DA0, skills 0x00532E90, item list 0x005337F0, corpses 0x005339A0, hotkey tail
#               0x00533F70: name, ECX, EDX, [esp+4..0x10] / EAX
#   V71 / V71R  0x00533350 sub_00533350_ItemListReadV71 entry / return
#   OIC / OICR  0x00530F40 sub_00530F40_ItemCreateFromOldRec: the 0x48-byte record in the old form (hex) / EAX
#   OPL / OPLR  0x00531040 OldItemPlace and 0x00531390 OldItemPlaceCorpse: ECX, EDX, [esp+4..0x10] / EAX
#   INS / INSR  0x00562660 ITEMS_InsertSocket: ECX, EDX, [esp+4] child, [esp+8] parent, the return address / EAX, when
#               the return address is one of the version-71 reader's sites 0x005311BA or 0x005313F5 (INSA: any other
#               caller is counted, not logged)
#   UB0   0x005566E5 ITEMS_BuildUnique after the item version: the item (EDI), the version (ESI), the base record
#         (EBX), the creation record ([ebp+0x10]) +0x2C and +0x40
#   UBR   0x00556757 the restore branch taken (record +0x2C non-zero): the record's +0x40, the item, the item version
#         at the file index, the unique row (EAX)
import json
import struct

import gdb

h1c_INF = gdb.selected_inferior()


def h1c_mem(addr, n):
    return bytes(h1c_INF.read_memory(addr, n))


def h1c_u16(a):
    return struct.unpack("<H", h1c_mem(a, 2))[0]


def h1c_u32(a):
    return struct.unpack("<I", h1c_mem(a, 4))[0]


def h1c_reg(name):
    return int(gdb.parse_and_eval("$" + name)) & 0xFFFFFFFF


def h1c_emit(tag, d):
    gdb.write("%s %s\n" % (tag, json.dumps(d, separators=(",", ":"))))


def h1c_stack(n):
    esp = h1c_reg("esp")
    return [h1c_u32(esp + 4 + 4 * i) for i in range(n)]


class h1c_Ret(gdb.Breakpoint):
    """One-shot breakpoint at a call's return address (disabled when it fires: a breakpoint that never stops the
    game is not deleted by gdb, and a stale one would log the next call's return again)."""

    def __init__(self, addr, fn):
        super().__init__("*0x%08X" % addr, internal=True)
        self.silent = True
        self.fn = fn

    def stop(self):
        self.enabled = False
        try:
            self.fn()
        except Exception as e:
            gdb.write("LOGERR %s %r\n" % (self.fn.__name__, e))
        return False


def h1c_call(tag, nstack=4, extra=None):
    """Entry callback logging TAG, and a TAGR line at the return address."""
    def entry():
        esp = h1c_reg("esp")
        ret = h1c_u32(esp)
        d = {"ecx": h1c_reg("ecx"), "edx": h1c_reg("edx"), "st": h1c_stack(nstack), "ret": ret}
        if extra:
            d.update(extra())
        h1c_emit(tag, d)
        outp = h1c_u32(esp + 0x14) if tag == "MOS" else 0

        def back():
            r = {"eax": h1c_reg("eax")}
            if tag == "MOS":
                r["len"] = h1c_u32(outp)
            h1c_emit(tag + "R", r)
        h1c_Ret(ret, back)
    entry.__name__ = "h1c_" + tag
    return entry


def h1c_mos_extra():
    buf = h1c_u32(h1c_reg("esp") + 8)
    return {"bytes": h1c_mem(buf, 0x12).hex()}


def h1c_sec(name):
    def entry():
        esp = h1c_reg("esp")
        ret = h1c_u32(esp)
        h1c_emit("SEC", {"sec": name, "ecx": h1c_reg("ecx"), "edx": h1c_reg("edx"), "st": h1c_stack(4), "ret": ret})
        h1c_Ret(ret, lambda: h1c_emit("SECR", {"sec": name, "eax": h1c_reg("eax")}))
    entry.__name__ = "h1c_sec_" + name
    return entry


H1C_INS = {"n": 0}


def h1c_ins():
    esp = h1c_reg("esp")
    ret = h1c_u32(esp)
    if ret not in (0x005311BA, 0x005313F5):
        H1C_INS["n"] += 1
        return
    h1c_emit("INS", {"ecx": h1c_reg("ecx"), "edx": h1c_reg("edx"), "child": h1c_u32(esp + 4),
                     "parent": h1c_u32(esp + 8), "ret": ret, "others": H1C_INS["n"]})
    h1c_Ret(ret, lambda: h1c_emit("INSR", {"eax": h1c_reg("eax"), "ret": ret}))


def h1c_ub0():
    ebp = h1c_reg("ebp")
    rec = h1c_u32(ebp + 0x10)
    item = h1c_reg("edi")
    h1c_emit("UB0", {"item": item, "version": h1c_reg("esi") & 0xFFFF, "base": h1c_reg("ebx"), "rec": rec,
                     "r2c": h1c_u32(rec + 0x2C), "r40": h1c_u32(rec + 0x40)})


def h1c_ubr():
    ebp = h1c_reg("ebp")
    rec = h1c_u32(ebp + 0x10)
    h1c_emit("UBR", {"item": h1c_reg("edi"), "base": h1c_reg("ebx"), "r2c": h1c_u32(rec + 0x2C),
                     "r40": h1c_u32(rec + 0x40), "eax": h1c_reg("eax")})


class h1c_Bp(gdb.Breakpoint):
    def __init__(self, addr, fn):
        super().__init__("*0x%08X" % addr, internal=True)
        self.silent = True
        self.fn = fn

    def stop(self):
        try:
            self.fn()
        except Exception as e:  # never stop the game on a logger error; log it instead
            gdb.write("LOGERR %s %r\n" % (getattr(self.fn, "__name__", "?"), e))
        return False


h1c_Bp(0x00532590, h1c_call("NCL", 4))
h1c_Bp(0x00533C70, h1c_call("MOS", 6, h1c_mos_extra))
h1c_Bp(0x00533BF0, h1c_call("MXO", 2))
h1c_Bp(0x005774F0, h1c_call("MCR", 6))
h1c_Bp(0x00533350, h1c_call("V71", 4))
h1c_Bp(0x00531040, h1c_call("OPL", 4))
h1c_Bp(0x00531390, h1c_call("OPL", 4))
h1c_Bp(0x00530F40, h1c_call("OIC", 4))
for _a, _n in ((0x00532690, "header"), (0x00532BE0, "quests"), (0x00532C70, "waypoints"), (0x00532D00, "npcs"),
               (0x00532DA0, "stats"), (0x00532E90, "skills"), (0x005337F0, "items"), (0x005339A0, "corpses"),
               (0x00533F70, "tail")):
    h1c_Bp(_a, h1c_sec(_n))
h1c_Bp(0x00562660, h1c_ins)
h1c_Bp(0x005566E5, h1c_ub0)
h1c_Bp(0x00556757, h1c_ubr)
