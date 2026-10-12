# gdb Python logger for plan 0013 Phase 2 (save round trips at run time). Sourced by tools/gdb/d2s-io.gdb.
# One line per event, "TAG {json}". Addresses refer to the pinned game.exe (image base 0x400000); names
# and offsets are those of docs/findings/save/0001-d2s-io.md and re/types/save.h. Check a log with
#   python3 -I tools/d2sio.py check <excel-dir> <log> [<saved.d2s> ...]
#
# Write side (single player: PLRSAVE_Save -> PLRSAVE_WriteFile -> D2S_WriteSave):
#   PSAVE 0x00532400  PLRSAVE_Save entry (ECX game, EDX unit): return address = who saves
#   SAVE  0x00532240  PLRSAVE_WriteFile entry: return address, the output buffer address; opens the
#                     save window in which SBIT lines are logged
#   WHDR  0x00568F5C  D2S_WriteHeader after the client lookup (EAX client, ESI unit, EDI game): the runtime
#                     sources of the header (client, game, player-data fields) and the unit's stat lists
#   WLVL  0x00569052  D2S_WriteHeader after GetStat(unit, 12): EAX
#   WTIME 0x0056906C  D2S_WriteHeader after time(NULL): EAX
#   SBIT  0x006312B0  ITEMS_SerializeBits entry (ECX item, EDX bit buffer), inside the save window only:
#                     the item's runtime fields and where it starts (file offset in the final pass)
#   WDONE 0x005322C4  PLRSAVE_WriteFile after D2S_WriteSave: size, path, the whole buffer (hex)
# Read side (PLRSAVE_ReadFile -> D2S_ReadSave -> D2S_ReadSaveV92):
#   RHDR  0x0056A090  D2S_ReadHeader entry: the bytes read (hex), their length
#   RSUM  0x0056A0EB  after D2S_Checksum: computed (EAX) vs stored
#   RMAP  0x0056A1FC  before the map-seed test (EBX game, ESI buffer, EDI client): game type, override flag,
#                     game+0x7C, the file's map seed and difficulty byte, and the client fields read so far
#   RMAP2 0x0056A21A  after it: game+0x7C
#   RHRET 0x0056B1C0  D2S_ReadSaveV92 after D2S_ReadHeader: return code, client fields, player-data fields
#   RSTAT 0x0056A5D5  D2S_ReadStatsBits, the SetStat call: id, value, param
#   RITEM 0x00558D28  sub_00558CB0_ItemCreateFromSave after ITEMS_Deserialize (ESI unit, EAX bytes)
#   LFIN  0x0056AF80  D2S_LoadFinish entry (EDX unit): stats 6..9 base and full, stack args (stats 6, 8)
#   LFIN2 0x0056B3C8  after D2S_LoadFinish (EDI unit): the same stats
#   RERR  0x0056B3A7  D2S_ReadSaveV92 failure exit: internal code (ESI) and the mapped code
# Seeds:
#   GAME  0x0052C312 / 0x0052C2E2  GAME_InitSeeds, override and no-override paths (as seed-tree.gdb)
#   ACT   0x00642F1A  DRLG_ActCreate after the act draws: act index, act map seed (+0x458), act seed
# Drops (plan 0004 harness):
#   CPOST 0x0055AEEC  after sub_0055A550_DropCreateItem (EAX item unit): the new item's fields
# String tables (data/0003):
#   TBL   0x00525950  STRTABLE_LoadFile after STRTABLE_Crc16: computed vs stored crc, file size, count
#   TBLX  0x00525959  the crc mismatch branch (fatal error follows)
import hashlib
import json
import struct

import gdb

INF = gdb.selected_inferior()
G_PITEMS = 0x0096CA5C
G_NITEMS = 0x0096CA58
ERRMAP = 0x006E1208

STATE = {"buf": None, "insave": False, "lfin_unit": None}


def mem(addr, n):
    return bytes(INF.read_memory(addr, n))


def u8(addr):
    return mem(addr, 1)[0]


def u16(addr):
    return struct.unpack("<H", mem(addr, 2))[0]


def s16(addr):
    return struct.unpack("<h", mem(addr, 2))[0]


def u32(addr):
    return struct.unpack("<I", mem(addr, 4))[0]


def s32(addr):
    return struct.unpack("<i", mem(addr, 4))[0]


def reg(name):
    return int(gdb.parse_and_eval("$" + name)) & 0xFFFFFFFF


def cstr(addr, n):
    return mem(addr, n).split(b"\0")[0].decode("latin1")


def emit(tag, d):
    gdb.write("%s %s\n" % (tag, json.dumps(d, separators=(",", ":"))))


def statlist(unit):
    """Base and full stat arrays of a unit: [[id, param, value], ...] (entry = u32 (id << 16 | param), s32)."""
    out = {"base": None, "full": None}
    lst = u32(unit + 0x5C)
    if not lst:
        return out
    for key, (pa, pn) in (("base", (0x24, 0x28)), ("full", (0x48, 0x4C))):
        if key == "full" and not (u32(lst + 0x10) & 0x80000000):
            continue
        arr, n = u32(lst + pa), s16(lst + pn)
        if not arr or n <= 0 or n > 1024:
            out[key] = []
            continue
        raw = mem(arr, 8 * n)
        out[key] = [[k >> 16, k & 0xFFFF, v] for k, v in struct.iter_unpack("<Ii", raw)]
    return out


def pick(st, ids):
    """{id: value} for param 0 of the given ids, from a stat array (absent ids omitted)."""
    if st is None:
        return None
    return {str(i): v for i, p, v in st if p == 0 and i in ids}


def client_fields(c):
    return {"cls": u8(c + 0x08), "status": u16(c + 0x0A), "name": cstr(c + 0x0D, 16), "act": u8(c + 0x1AC),
            "wsw": u8(c + 0x45C), "c480": mem(c + 0x480, 3).hex(), "c488": u32(c + 0x488)}


def game_fields(g):
    return {"g6a": u8(g + 0x6A), "g6d": u8(g + 0x6D), "g70": u32(g + 0x70), "g74": u32(g + 0x74),
            "g78": u32(g + 0x78), "g7c": u32(g + 0x7C), "g84": u32(g + 0x84)}


def pdata_fields(unit):
    pd = u32(unit + 0x14)
    return {"pd": [u32(pd + o) for o in range(0x70, 0x90, 4)]} if pd else {}


def item_fields(it):
    d = {"unit": it, "id": u32(it + 0x0C), "cls": s32(it + 4), "mode": u32(it + 0x10), "seed28": u32(it + 0x28),
         "rng20": "%08x:%08x" % (u32(it + 0x20), u32(it + 0x24))}
    cls = d["cls"]
    if 0 <= cls < u32(G_NITEMS):
        d["code"] = mem(u32(G_PITEMS) + cls * 0x1A8 + 0x80, 4).decode("latin1")
    idt = u32(it + 0x14)
    if idt:
        d.update(q=u32(idt), flags=u32(idt + 0x18), ilvl=s32(idt + 0x2C), ver=u16(idt + 0x30),
                 auto=u16(idt + 0x36), body=u8(idt + 0x44), page=struct.unpack("b", mem(idt + 0x45, 1))[0],
                 gfx=u8(idt + 0x49), iseed="%08x:%08x" % (u32(idt + 4), u32(idt + 8)))
    return d


# --- write side ---------------------------------------------------------------------------------------

def on_psave():
    emit("PSAVE", {"ret": u32(reg("esp")), "game": reg("ecx"), "unit": reg("edx")})


def on_save():
    esp = reg("esp")
    STATE["buf"] = esp - 4 - 0x25F8  # PLRSAVE_WriteFile's [ebp-0x25F8] once its prologue has run
    STATE["insave"] = True
    emit("SAVE", {"ret": u32(esp), "game": reg("ecx"), "unit": reg("edx"), "buf": STATE["buf"]})


def on_whdr():
    c, unit, g = reg("eax"), reg("esi"), reg("edi")
    d = {"client": c, "unit": unit}
    d.update(client_fields(c))
    d.update(game_fields(g))
    d.update(pdata_fields(unit))
    st = statlist(unit)
    d["stats"] = st["base"]
    d["full"] = pick(st["full"], range(0, 16))
    emit("WHDR", d)


def on_wlvl():
    emit("WLVL", {"stat12": reg("eax")})


def on_wtime():
    emit("WTIME", {"time": reg("eax")})


def on_sbit():
    if not STATE["insave"]:
        return
    it, ctx = reg("ecx"), reg("edx")
    esp = reg("esp")
    p, cap, nbytes, bit = u32(ctx), s32(ctx + 4), s32(ctx + 8), s32(ctx + 12)
    d = item_fields(it)
    buf = STATE["buf"]
    final = buf is not None and buf <= p < buf + 0x2000
    d.update(args=[u32(esp + 4), u32(esp + 8), u32(esp + 12)], ptr=p, nbytes=nbytes, bit=bit, final=final,
             off=(p - buf) if final else None)
    emit("SBIT", d)


def on_wdone():
    ebp = reg("ebp")
    size = s32(ebp - 0x25FC)
    buf = ebp - 0x25F8
    data = mem(buf, size) if 0 < size <= 0x2000 else b""
    STATE["insave"] = False
    emit("WDONE", {"size": size, "buf": buf, "path": cstr(ebp - 0x1F8, 260), "sha256": hashlib.sha256(data).hexdigest(),
                   "hex": data.hex()})


# --- read side ----------------------------------------------------------------------------------------

def on_rhdr():
    esp = reg("esp")
    cur, end = u32(u32(esp + 4)), u32(esp + 8)
    n = end - cur
    data = mem(cur, n) if 0 < n <= 0x2000 else b""
    emit("RHDR", {"len": n, "sha256": hashlib.sha256(data).hexdigest(), "hex": data.hex(), "client": reg("edx"),
                  "game": reg("ecx")})


def on_rsum():
    ebp = reg("ebp")
    emit("RSUM", {"computed": reg("eax"), "stored": u32(ebp + 0xC), "len": u32(ebp - 0xC),
                  "size_field": u32(reg("esi") + 8)})


def on_rmap():
    g, b, c, ebp = reg("ebx"), reg("esi"), reg("edi"), reg("ebp")
    d = {"bit7": u32(ebp + 0xC), "file_map": u32(b + 0xAB), "file_diff": mem(b + 0xA8, 3).hex(),
         "file_2c": u32(b + 0x2C)}
    d.update(game_fields(g))
    d.update(client_fields(c))
    STATE["rgame"] = g
    emit("RMAP", d)


def on_rmap2():
    emit("RMAP2", {"g7c": u32(STATE["rgame"] + 0x7C)})


def on_rhret():
    ebp = reg("ebp")
    code = reg("eax")
    d = {"code": code}
    c = u32(ebp - 8)
    unit = u32(u32(ebp + 0x10))
    if code == 0 and c:
        d.update(client_fields(c))
        if unit:
            d.update(pdata_fields(unit))
    emit("RHRET", d)


def on_rstat():
    v = reg("eax")
    emit("RSTAT", {"id": reg("edi"), "value": v - (1 << 32) if v & 0x80000000 else v, "param": reg("ebx")})


def on_ritem():
    d = item_fields(reg("esi"))
    d["nbytes"] = reg("eax")
    emit("RITEM", d)


def on_lfin():
    unit, esp = reg("edx"), reg("esp")
    st = statlist(unit)
    emit("LFIN", {"unit": unit, "arg6": s32(esp + 4), "arg8": s32(esp + 8), "base": pick(st["base"], range(0, 16)),
                  "full": pick(st["full"], range(0, 16))})


def on_lfin2():
    unit = reg("edi")
    st = statlist(unit)
    emit("LFIN2", {"unit": unit, "base": pick(st["base"], range(0, 16)), "full": pick(st["full"], range(0, 16))})


def on_rerr():
    esi = reg("esi")
    emit("RERR", {"internal": esi, "mapped": u32(ERRMAP + 4 * esi) if esi < 64 else None})


# --- seeds, drops, string tables --------------------------------------------------------------------

def on_game_ov():
    g = reg("edi")
    emit("GAME", {"path": "override", "g84": u32(g + 0x84), "g7c": u32(g + 0x7C),
                  "seed": "%08x:%08x" % (u32(g + 0xD0), u32(g + 0xD4))})


def on_game_no():
    g = reg("edi")
    emit("GAME", {"path": "clock", "g84": u32(g + 0x84), "map": reg("eax"),
                  "seed": "%08x:%08x" % (u32(g + 0xD0), u32(g + 0xD4))})


def on_act():
    a = reg("esi")
    emit("ACT", {"idx": u8(a + 0x480), "map": u32(a + 0x458), "seed": "%08x:%08x" % (u32(a), u32(a + 4))})


def on_cpost():
    it = reg("eax")
    if it:
        emit("CPOST", item_fields(it))


def on_tbl():
    f = reg("esi")
    emit("TBL", {"computed": u16(reg("ebp") - 4), "stored": u16(f), "file_size": u32(f + 0x11), "count": u16(f + 2)})


def on_tblx():
    emit("TBLX", {"fatal": "crc"})


class Bp(gdb.Breakpoint):
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


for _a, _f in ((0x00532400, on_psave), (0x00532240, on_save), (0x00568F5C, on_whdr), (0x00569052, on_wlvl),
               (0x0056906C, on_wtime), (0x006312B0, on_sbit), (0x005322C4, on_wdone),
               (0x0056A090, on_rhdr), (0x0056A0EB, on_rsum), (0x0056A1FC, on_rmap), (0x0056A21A, on_rmap2),
               (0x0056B1C0, on_rhret), (0x0056A5D5, on_rstat), (0x00558D28, on_ritem), (0x0056AF80, on_lfin),
               (0x0056B3C8, on_lfin2), (0x0056B3A7, on_rerr),
               (0x0052C312, on_game_ov), (0x0052C2E2, on_game_no), (0x00642F1A, on_act),
               (0x0055AEEC, on_cpost), (0x00525950, on_tbl), (0x00525959, on_tblx)):
    Bp(_a, _f)
