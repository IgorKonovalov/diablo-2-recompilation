# gdb Python logger for plan 0008 Phase 3 (generator dispatch, room-creation order, preset file
# choice). Sourced by tools/gdb/drlg-gen.gdb. One line per event, "TAG {json}". Addresses refer to
# the pinned game.exe (image base 0x400000). Seeds are printed "lo:hi".
#
#   LC0   0x00642B67  DRLG_LevelCreate after RNG_SeedInit (ESI = level): id, DrlgType, act base, seed
#   LC1   0x00642B91  DRLG_LevelCreate after the create dispatch: seed, preset data (+0x14)[1]
#   LI0   0x006424C4  sub_006424A0_LevelInit after its RNG_SeedInit (EDI = level): seed, preset index
#   LI1   0x006424DC / 0x006424F4 / 0x0064250C  after the generator (EDI = level): seed, room count
#   RC    0x0066B3E0  DRLG_RoomCreate entry (ECX = level, EDX = type): level seed before, caller
#   RL    0x0066B970  sub_0066B970_LevelRoomLink (ECX = level, EDX = room): room rect, type, +0x04,
#                     +0x50, level seed
#   PIC   0x00666ED0  sub_00666ED0_PresetInstanceCreate entry (ECX level, EDX def): Files, seed in,
#                     which seed (level or other), caller
#   PICX  0x00666FC0  its exit (EAX = instance): drawn index, seed out
#   PIO   0x00666EC0  sub_00666EC0_PresetSetFile (ECX instance, EDX index): outdoor override
#   MFR   0x006738C0  sub_006738C0_MazePresetFile entry (EAX forced index, EDI level, [esp+4] instance)
#   MFRX  0x006738DE / 0x006739F8  its exits: instance index, level seed
#   PRC   0x00667ED0  sub_00667ED0_PresetRoomsCreate entry (ECX level, EDX instance): def, index,
#                     the File cell it will load, preset rect, flags, single-room flag, seed
#   PUR   0x00667A35  PresetMapScan's call of DRLG_PresetUnitDropRolls (oracle, drlg/preset):
#                     seed in;  PURX 0x00667A3A: seed out
#   MZ0   0x00673B41  maze build after its first DRLG_RoomCreate: level seed (maze window start, modelled since plan 0022)
#   MZ1   0x00673F44  maze build before the per-room preset loop: level seed (maze window end),
#                     the level's room list in list order
#   OD0   0x00675360  outdoor build entry: level seed (oracle window start)
#   OD1   0x006750F0  sub_006750F0_OutdoorRoomsCreate entry: level seed (oracle window end)
#   LSR   0x006706A0  sub_006706A0_LvlSubRoll entry (ECX room, EDX SubType, [esp+4] SubTheme): room seed
#   LSRX  0x00670731 / 0x0067073A  its exits: mask (EAX), room seed
import json
import struct

import gdb

INF = gdb.selected_inferior()
G_LVLPREST = 0x0096C894


def mem(addr, n):
    return bytes(INF.read_memory(addr, n))


def u32(addr):
    return struct.unpack("<I", mem(addr, 4))[0]


def s32(addr):
    return struct.unpack("<i", mem(addr, 4))[0]


def reg(name):
    return int(gdb.parse_and_eval("$" + name)) & 0xFFFFFFFF


def cstr(addr, n=64):
    return mem(addr, n).split(b"\0", 1)[0].decode("latin-1")


def seedat(p):
    lo, hi = struct.unpack("<II", mem(p, 8))
    return "%08x:%08x" % (lo, hi)


def lseed(level):
    return seedat(level + 0x1C4)


def lhead(level):
    act = u32(level + 0x1B4)
    return {"level": level, "id": u32(level + 0x1D0), "drlg": u32(level), "ltype": u32(level + 0x1C0),
            "client": u32(act + 0x478), "seed": lseed(level)}


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


def preset_idx(level):
    d = u32(level + 0x14)
    return s32(d + 4) if d else None


def on_lc0():
    lv = reg("esi")
    d = lhead(lv)
    d["base"] = u32(u32(lv + 0x1B4) + 0x470)
    emit("LC0", d)


def on_lc1():
    lv = reg("esi")
    d = {"level": lv, "id": u32(lv + 0x1D0), "seed": lseed(lv)}
    if u32(lv) == 2:
        d["idx"] = preset_idx(lv)
    emit("LC1", d)


def on_li0():
    lv = reg("edi")
    d = lhead(lv)
    d["base"] = u32(u32(lv + 0x1B4) + 0x470)
    if d["drlg"] == 2:
        d["idx"] = preset_idx(lv)
    emit("LI0", d)


def on_li1():
    lv = reg("edi")
    emit("LI1", {"level": lv, "id": u32(lv + 0x1D0), "seed": lseed(lv), "nrooms": s32(lv + 0x8)})


def on_rc():
    lv, t = reg("ecx"), reg("edx")
    emit("RC", {"level": lv, "type": t, "seed": lseed(lv), "ret": u32(reg("esp"))})


def on_rl():
    lv, r = reg("ecx"), reg("edx")
    x, y, w, h = struct.unpack("<iiii", mem(r + 0x34, 16))
    d = {"level": lv, "room": r, "type": u32(r + 0x48), "rect": [x, y, w, h], "r04": u32(r + 4),
         "mask": u32(r + 0x50), "f28": u32(r + 0x28), "seed": lseed(lv), "ret": u32(reg("esp"))}
    if d["type"] == 2 and u32(r + 0x20):
        pr = u32(r + 0x20)
        d["pdef"] = s32(pr)
        d["pfidx"] = s32(pr + 4)
    emit("RL", d)


_pic = []


def on_pic():
    lv, df = reg("ecx"), reg("edx")
    esp = reg("esp")
    sp = u32(esp + 8)
    rec = u32(G_LVLPREST) + df * 0x1B0
    _pic.append((lv, sp))
    emit("PIC", {"level": lv, "def": df, "files": s32(rec + 0x40), "seedp": sp,
                 "islevel": 1 if sp == lv + 0x1C4 else 0, "seed": seedat(sp), "ret": u32(esp),
                 "rect": list(struct.unpack("<iiii", mem(u32(esp + 4), 16)))})


def on_picx():
    ps = reg("eax")
    lv, sp = _pic.pop() if _pic else (0, 0)
    emit("PICX", {"level": lv, "ps": ps, "def": s32(ps), "idx": s32(ps + 4), "seed": seedat(sp) if sp else None})


def on_pio():
    emit("PIO", {"ps": reg("ecx"), "idx": reg("edx")})


def on_mfr():
    lv = reg("edi")
    ps = u32(reg("esp") + 4)
    emit("MFR", {"level": lv, "ps": ps, "forced": s32_of(reg("eax")), "def": s32(ps), "seed": lseed(lv)})


def s32_of(v):
    return v - (1 << 32) if v & 0x80000000 else v


def on_mfrx():
    lv = reg("edi")
    ps = u32(reg("esp") + 4)
    emit("MFRX", {"level": lv, "ps": ps, "idx": s32(ps + 4), "seed": lseed(lv)})


def on_prc():
    lv, ps = reg("ecx"), reg("edx")
    esp = reg("esp")
    rec = u32(ps + 8)
    idx = s32(ps + 4)
    emit("PRC", {"level": lv, "ps": ps, "def": s32(ps), "idx": idx,
                 "file": cstr(rec + 0x44 + idx * 0x3C) if 0 <= idx < 6 else None,
                 "prect": list(struct.unpack("<iiii", mem(ps + 0x10, 16))),
                 "flags": u32(esp + 4), "single": u32(esp + 8), "seed": lseed(lv)})


_pur = []


def on_pur_pre():
    sp = u32(reg("esp"))
    _pur.append(sp)
    emit("PUR", {"seedp": sp, "seed": seedat(sp), "ps": reg("edx")})


def on_purx():
    sp = _pur.pop() if _pur else 0
    emit("PURX", {"seedp": sp, "seed": seedat(sp) if sp else None})


def on_mz0():
    lv = reg("esi")
    emit("MZ0", {"level": lv, "id": u32(lv + 0x1D0), "seed": lseed(lv)})


def on_mz1():
    lv = reg("esi")
    rooms, r = [], u32(lv + 0x10)
    while r and len(rooms) < 4096:
        x, y, w, h = struct.unpack("<iiii", mem(r + 0x34, 16))
        pr = u32(r + 0x20)
        rooms.append([r, u32(r + 0x48), x, y, w, h, s32(pr) if pr else None, s32(pr + 4) if pr else None])
        r = u32(r + 0x24)
    emit("MZ1", {"level": lv, "id": u32(lv + 0x1D0), "seed": lseed(lv), "rooms": rooms})


def on_od0():
    lv = reg("ecx")
    emit("OD0", {"level": lv, "id": u32(lv + 0x1D0), "seed": lseed(lv)})


def on_od1():
    lv = reg("ebx")
    emit("OD1", {"level": lv, "id": u32(lv + 0x1D0), "seed": lseed(lv)})


def on_lsr():
    r = reg("ecx")
    emit("LSR", {"room": r, "stype": s32_of(reg("edx")), "theme": s32(reg("esp") + 4), "seed": seedat(r + 0x14)})


def on_lsrx():
    r = reg("edi")
    emit("LSRX", {"room": r, "mask": reg("eax"), "seed": seedat(r + 0x14)})


def on_lsrx0():
    r = reg("edi")
    emit("LSRX", {"room": r, "mask": 0, "seed": seedat(r + 0x14)})


for addr, fn in [(0x00642B67, on_lc0), (0x00642B91, on_lc1), (0x006424C4, on_li0),
                 (0x006424DC, on_li1), (0x006424F4, on_li1), (0x0064250C, on_li1),
                 (0x0066B3E0, on_rc), (0x0066B970, on_rl), (0x00666ED0, on_pic), (0x00666FC0, on_picx),
                 (0x00666EC0, on_pio), (0x006738C0, on_mfr), (0x006738DE, on_mfrx), (0x006739F8, on_mfrx),
                 (0x00667ED0, on_prc), (0x00667A35, on_pur_pre), (0x00667A3A, on_purx),
                 (0x00673B41, on_mz0), (0x00673F44, on_mz1), (0x00675360, on_od0), (0x006750F0, on_od1),
                 (0x006706A0, on_lsr), (0x00670731, on_lsrx), (0x0067073A, on_lsrx0)]:
    Bp(addr, fn)
