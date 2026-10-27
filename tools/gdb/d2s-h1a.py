# gdb Python logger for plan 0038 batch H1a (run:2026-10-27-sweep-d2s-load): the load-side lines the
# malformed, edited and old-format saves need, on top of tools/gdb/d2s-io.py and tools/gdb/d2s-h1b.py (both
# unchanged; sourced first by tools/gdb/d2s-h1a.gdb). One line per event, "TAG {json}". Addresses refer to the
# pinned game.exe (image base 0x400000); names are those of docs/findings/save/0001-d2s-io.md.
#
#   RSV   0x0053447A PLRSAVE_ReadFile after its D2S_ReadSave call: the code (EAX) and the bytes fread returned
#         ([ebp-0x2604]); the code 9 of D2S_ReadSave's own length and magic tests never reaches RHRET or RERR
#   LEG   0x00534020 the legacy reader (version < 92) entry: the version and length of the buffer ([esp+4], [esp+8])
#   LEGR  0x00534380 after the legacy reader returned to D2S_ReadSave: EAX
#   PLD   0x00539809 ClientAddPlayerToGame after its PlayerLoad call: EAX (the code the join tests)
#   RCST  0x0056A167 D2S_ReadHeader after D2S_CheckStatus: EAX, the file status word (u16 [esi+0x24]), game
#         +0x70 (expansion), +0x6D (difficulty), +0x6A (game type)
#   RACT  0x0056A1F3 D2S_ReadHeader after the act clamp: the file's difficulty byte of the game's difficulty and
#         the act the client gets (AL)
#   RSKC  0x0056A710 D2S_ReadSkills entry: the version and count arguments ([esp+0xC], [esp+0x10])
#   RSTV  0x0056A620 D2S_ReadStats entry: version ([esp+0xC]) and the stat-slot count ([esp+0x10])
#   RSTL  0x0056A6D0 D2S_ReadStats' old-form SetStat call: id, value, param ([esp+4], [esp+8], [esp+0xC])
#   RQW   0x0056B210 D2S_ReadSaveV92 after D2S_ReadQuests: EAX and the three 96-byte quest records of the
#         player (player data +0x10/+0x14/+0x18, each a pointer whose u32 at +0 is the record's bytes)
#   RWP   0x0056B22F after D2S_ReadWaypoints: EAX and the three 16-byte waypoint records (player data +0x1C/+0x20/+0x24)
#   RIX   0x00558D28 (as RITEM): item data +0x18 flags, +0x00 quality, +0x28 file index, +0x1C/+0x20 realm pair,
#         +0x48 (u8) and the 16 name bytes at +0x4A
import json
import struct

import gdb

h1a_INF = gdb.selected_inferior()


def h1a_mem(addr, n):
    return bytes(h1a_INF.read_memory(addr, n))


def h1a_u8(a):
    return h1a_mem(a, 1)[0]


def h1a_u16(a):
    return struct.unpack("<H", h1a_mem(a, 2))[0]


def h1a_u32(a):
    return struct.unpack("<I", h1a_mem(a, 4))[0]


def h1a_s32(a):
    return struct.unpack("<i", h1a_mem(a, 4))[0]


def h1a_reg(name):
    return int(gdb.parse_and_eval("$" + name)) & 0xFFFFFFFF


def h1a_emit(tag, d):
    gdb.write("%s %s\n" % (tag, json.dumps(d, separators=(",", ":"))))


def h1a_rsv():
    h1a_emit("RSV", {"code": h1a_reg("eax"), "nread": h1a_u32(h1a_reg("ebp") - 0x2604)})


def h1a_leg():
    esp = h1a_reg("esp")
    buf, n = h1a_u32(esp + 4), h1a_u32(esp + 8)
    h1a_emit("LEG", {"version": h1a_u32(buf + 4) if n >= 8 else None, "len": n})


def h1a_legr():
    h1a_emit("LEGR", {"code": h1a_reg("eax")})


def h1a_pld():
    h1a_emit("PLD", {"code": h1a_reg("eax")})


def h1a_rcst():
    esi, g = h1a_reg("esi"), h1a_reg("ebx")
    h1a_emit("RCST", {"code": h1a_reg("eax"), "status": h1a_u16(esi + 0x24), "g70": h1a_u32(g + 0x70),
                      "g6d": h1a_u8(g + 0x6D), "g6a": h1a_u8(g + 0x6A)})


def h1a_ract():
    esi, g = h1a_reg("esi"), h1a_reg("ebx")
    d = h1a_u8(g + 0x6D)
    h1a_emit("RACT", {"diff": d, "file": h1a_u8(esi + 0xA8 + d), "act": h1a_reg("eax") & 0xFF})


def h1a_rskc():
    esp = h1a_reg("esp")
    h1a_emit("RSKC", {"version": h1a_u32(esp + 0xC), "count": h1a_s32(esp + 0x10)})


def h1a_rstv():
    esp = h1a_reg("esp")
    h1a_emit("RSTV", {"version": h1a_u32(esp + 0xC), "count": h1a_s32(esp + 0x10)})


def h1a_rstl():
    esp = h1a_reg("esp")
    h1a_emit("RSTL", {"id": h1a_u32(esp + 4), "value": h1a_s32(esp + 8), "param": h1a_u32(esp + 0xC)})


def h1a_pd():
    unit = h1a_reg("edi")
    return h1a_u32(unit + 0x14) if unit else 0


def h1a_rqw():
    pd = h1a_pd()
    recs = []
    for d in range(3):
        rec = h1a_u32(pd + 0x10 + 4 * d) if pd else 0
        buf = h1a_u32(rec) if rec else 0
        recs.append(h1a_mem(buf, 0x60).hex() if buf else None)
    h1a_emit("RQW", {"code": h1a_reg("eax"), "recs": recs})


def h1a_rwp():
    pd = h1a_pd()
    recs = []
    for d in range(3):
        rec = h1a_u32(pd + 0x1C + 4 * d) if pd else 0
        recs.append(h1a_mem(rec, 16).hex() if rec else None)
    h1a_emit("RWP", {"code": h1a_reg("eax"), "recs": recs})


def h1a_rix():
    it = h1a_reg("esi")
    idt = h1a_u32(it + 0x14)
    if not idt:
        h1a_emit("RIX", {"unit": it, "idata": 0})
        return
    h1a_emit("RIX", {"unit": it, "id": h1a_u32(it + 0x0C), "flags": h1a_u32(idt + 0x18), "q": h1a_u32(idt),
                     "fidx": h1a_s32(idt + 0x28), "realm": [h1a_u32(idt + 0x1C), h1a_u32(idt + 0x20)],
                     "b48": h1a_u8(idt + 0x48), "name": h1a_mem(idt + 0x4A, 16).split(b"\0")[0].decode("latin1"),
                     "nbytes": h1a_reg("eax")})


class h1a_Bp(gdb.Breakpoint):
    def __init__(self, addr, fn):
        super().__init__("*0x%08X" % addr, internal=True)
        self.silent = True
        self.fn = fn

    def stop(self):
        try:
            self.fn()
        except Exception as e:  # never stop the game on a logger error; log it instead
            gdb.write("LOGERR %s %r\n" % (self.fn.__name__, e))
        return False


for _a, _f in ((0x0053447A, h1a_rsv), (0x00534020, h1a_leg), (0x00534380, h1a_legr), (0x00539809, h1a_pld),
               (0x0056A167, h1a_rcst), (0x0056A1F3, h1a_ract), (0x0056A710, h1a_rskc), (0x0056A620, h1a_rstv),
               (0x0056A6D0, h1a_rstl), (0x0056B210, h1a_rqw), (0x0056B22F, h1a_rwp), (0x00558D28, h1a_rix)):
    h1a_Bp(_a, _f)
