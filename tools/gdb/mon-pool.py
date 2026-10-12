# gdb Python logger for plan 0012 Phase 2 (the level monster pools and the monster level).
# Sourced by tools/gdb/mon-pool.gdb. One line per event, "TAG {json}". Addresses refer to the pinned
# game.exe (image base 0x400000). Seeds are printed "lo:hi" (hex). See
# docs/findings/monsters/0001-level-pool.md.
#
#   MPS   0x00547D63  sub_00547D20_MonRegionsInit after its RNG_SeedInit (ESI = game): the game seed
#                     after its step, the low word that seeds the region seed, difficulty (+0x6D),
#                     expansion (+0x70), game type (+0x6A), +0x74, the caller, and the first 16 bytes
#                     of monstats record 723 (the Pandemonium 3 ordinal) and of record 722
#   MPR   0x00547B1A  sub_005479C0_MonRegionsBuild after one level's region is built and its variants
#                     rolled (ESI = region, [EBP+8] = region seed): level id, act, counts, rarity
#                     sum, entries (class, rarity, variant sets), the copied Levels fields, seed after
#   MLV   0x00573E56  sub_00573CB0_MonStatsInit after the monster level is chosen ([EBP-4] = level,
#                     EDI = difficulty index used, ESI = unit, [EBP+8] = game, [EBP+0xC] = room):
#                     class, level, the difficulty used, the game's difficulty and expansion, level id
#   CR0   0x0046C460  sub_0046C460_ClientCritters entry (ECX = client room): room seed (+0x6C), level id
#   CRC   0x0046C548  its call of sub_0046C1A0_ClientCritterCreate: class (ECX), room seed
#   CRX   0x0046C56B  its exit: room seed after
#
# MONPOOL_FORCE_DIFF=0|1|2 in the environment (d2run.py passes it on to gdb) makes MPS write that value
# into the game's difficulty byte (+0x6D) before 0x00547D66 reads it, so a character that can only
# play Normal gives a Nightmare or Hell game; MPS then logs "forced". Everything after game creation
# (towns, NPCs, the monster level) reads the same byte.
import json
import os
import struct

import gdb

INF = gdb.selected_inferior()
G_DATATABLES = 0x00744304


def mem(addr, n):
    return bytes(INF.read_memory(addr, n))


def u8(addr):
    return mem(addr, 1)[0]


def u32(addr):
    return struct.unpack("<I", mem(addr, 4))[0]


def s32(addr):
    return struct.unpack("<i", mem(addr, 4))[0]


def s16(addr):
    return struct.unpack("<h", mem(addr, 2))[0]


def reg(name):
    return int(gdb.parse_and_eval("$" + name)) & 0xFFFFFFFF


def seedat(p):
    lo, hi = struct.unpack("<II", mem(p, 8))
    return "%08x:%08x" % (lo, hi)


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
        except Exception as e:  # never stop the game on a logger error; log it instead
            gdb.write("LOGERR %r\n" % (e,))
        return False


def on_mps():
    game, ebp = reg("esi"), reg("ebp")
    dt = u32(G_DATATABLES)
    ms = u32(dt + 0xA78)
    forced = os.environ.get("MONPOOL_FORCE_DIFF")
    if forced is not None:
        INF.write_memory(game + 0x6D, bytes([int(forced)]))
    emit("MPS", {"forced": None if forced is None else int(forced), "game": game,
                 "gseed": seedat(game + 0xD0), "low": reg("edi"), "diff": u8(game + 0x6D),
                 "exp": u32(game + 0x70), "gtype": u8(game + 0x6A), "f74": u32(game + 0x74),
                 "ret": u32(ebp + 4), "nmonstats": s32(dt + 0xA80),
                 "ms722": mem(ms + 722 * 0x1A8, 16).hex(), "ms723": mem(ms + 723 * 0x1A8, 16).hex()})


def on_mpr():
    r, ebp = reg("esi"), reg("ebp")
    ents = []
    for i in range(u8(r + 0x12)):
        e = r + 0x14 + i * 0x34
        nv = u8(e + 3)
        ents.append([s16(e), u8(e + 2), [mem(e + 4 + 16 * k, 16).hex() for k in range(nv)]])
    emit("MPR", {"id": s32(r + 0x2C0), "act": u8(r), "n": u8(r + 0x10), "rsum": u8(r + 0x11),
                 "ntot": u8(r + 0x12), "ents": ents, "den": s32(r + 0x2B8), "umin": u8(r + 0x2BC),
                 "umax": u8(r + 0x2BD), "wndr": u8(r + 0x2BE), "quest": u8(r + 0x2D8),
                 "mlvl": [s32(r + 0x2DC), s32(r + 0x2E0)], "f0c": s32(r + 0xC), "f2d4": s32(r + 0x2D4),
                 "seed": seedat(u32(ebp + 8))})


def on_mlv():
    unit, ebp = reg("esi"), reg("ebp")
    game, room = u32(ebp + 8), u32(ebp + 0xC)
    lid = None
    if room:
        dr = u32(room + 0x10)
        if dr:
            lid = s32(u32(dr + 0x58) + 0x1D0)
    emit("MLV", {"cls": s32(unit + 4), "lvl": s32(ebp - 4), "d": reg("edi"), "diff": u8(game + 0x6D),
                 "exp": u32(game + 0x70), "lid": lid, "unit": unit})


def room_level(room):
    dr = u32(room + 0x10) if room else 0
    return s32(u32(dr + 0x58) + 0x1D0) if dr else None


def on_cr0():
    room = reg("ecx")
    emit("CR0", {"room": room, "lid": room_level(room), "seed": seedat(room + 0x6C) if room else None})


def on_crc():
    room = u32(reg("ebp") - 0xC)
    cls = reg("ecx")
    emit("CRC", {"room": room, "cls": cls - (1 << 32) if cls & 0x80000000 else cls, "seed": seedat(room + 0x6C)})


def on_crx():
    room = u32(reg("ebp") - 0xC)
    emit("CRX", {"room": room, "seed": seedat(room + 0x6C) if room else None})


Bp(0x0046C460, on_cr0)
Bp(0x0046C548, on_crc)
Bp(0x0046C56B, on_crx)
Bp(0x00547D63, on_mps)
Bp(0x00547B1A, on_mpr)
Bp(0x00573E56, on_mlv)
gdb.write("MONPOOL logger armed\n")
