# gdb Python logger for plan 0016 Phase 2 (preset units). Sourced by tools/gdb/drlg-preset.gdb after
# tools/gdb/drlg-gen.py, whose tags (LC0 .. LSRX, PRC, PUR/PURX) it leaves unchanged. One line per event,
# "TAG {json}". Addresses refer to the pinned game.exe (image base 0x400000). Seeds are printed "lo:hi".
# A unit list is [[ptr, type, id, mode, x, y, flags, path], ...] from the head (+0x0C next); path is null or
# the list of 12-byte points [action, x, y] (re/types/preset.h).
#
#   PSL   0x00667A3A  after PresetMapScan's DRLG_PresetUnitDropRolls (EDX gone; instance from PUR):
#                     instance +0x38 list
#   PRR   0x006678E2  DRLG_PresetRoomLoadDs1's call of the drop rolls (EDI room, EDX instance,
#                     [esp] seed pointer = room +0x14): seed in
#   PRRX  0x006678E7  after it (only when PRR fired): seed out, instance +0x38 list
#   PLD   0x00667890  PresetRoomLoadDs1 entry (ECX room): instance, its +0x0C (DS1 loaded) and +0x3C (pending)
#   PLDX  0x0061B757 / 0x0061B348  return to sub_0061B730_RoomActivateB / sub_0061B320_RoomPrepareFiles:
#                     room +0x28, instance +0x3C, instance +0x38 list
#   PTR0  0x0066697D  before DRLG_PresetUnitsToRoom (EDI room): room rect, room +0x5C, instance list
#   PTR1  0x00666982  after it: room +0x5C, instance list
#   RPU   0x005559A0  sub_005559A0_RoomPresetUnits entry (EDX server room, +0x10 DRLG room): the list it walks
#   PSP   0x0055594E  sub_00555910_PresetUnitSpawn after the dispatch (ESI preset unit, EAX unit or 0):
#                     spawned unit, its class (+0x04) and type (+0x00)
#   RPL   0x0061A206  sub_0061A1F0_RoomPopLevelId return (EAX): DRLG room, level id
#   L27   0x006774B1  sub_006772C0_LevelLinkBuild, level 6, before the level-27 index draw (ESI act =
#                     act seed, EAX link value, ECX level 27 preset data)
#   L27X  0x006774F9  the index write (EAX index, ECX preset data): act seed after
#   RSK   0x00666368  sub_00666220 (DRLG_PresetClientUnitsB) takes the three-row skip of the switch at 0x0066638C
#                     (ESI instance, [ebp-0xC] the DS1 row j before the skip, EAX the floor cell's main index);
#                     the row-skip counter of plan 0020 Phase 4; RSKON (once, at load) marks a log that has it
import json
import struct

import gdb

INF = gdb.selected_inferior()


def _mem(addr, n):
    return bytes(INF.read_memory(addr, n))


def _u32(addr):
    return struct.unpack("<I", _mem(addr, 4))[0]


def _s32(addr):
    return struct.unpack("<i", _mem(addr, 4))[0]


def _reg(name):
    return int(gdb.parse_and_eval("$" + name)) & 0xFFFFFFFF


def _seed(p):
    return "%08x:%08x" % struct.unpack("<II", _mem(p, 8))


def _emit(tag, d):
    gdb.write("%s %s\n" % (tag, json.dumps(d, separators=(",", ":"))))


def ulist(p, cap=2048):
    out = []
    while p and len(out) < cap:
        mode, uid, x, nxt, path, typ, y, flags = struct.unpack("<iiiIIiiI", _mem(p, 0x20))
        pts = None
        if path:
            n, pp = struct.unpack("<II", _mem(path, 8))
            pts = [list(struct.unpack("<iii", _mem(pp + 12 * i, 12))) for i in range(min(n, 256))] if pp else []
        out.append([p, typ, uid, mode, x, y, flags, pts])
        p = nxt
    return out


def inst_of(room):
    pr = _u32(room + 0x20)
    return _u32(pr + 8) if pr else 0


def ihead(ps):
    return {"ps": ps, "def": _s32(ps), "idx": _s32(ps + 4), "prect": list(struct.unpack("<iiii", _mem(ps + 0x10, 16)))}


class PBp(gdb.Breakpoint):
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


_scan = []      # instance of the pending PresetMapScan roll (PUR at 0x00667A35, EDX)
_rr = []        # pending PresetRoomLoadDs1 rolls
_pld = []       # rooms of PresetRoomLoadDs1 calls in flight


def on_scan_pre():
    _scan.append(_reg("edx"))


def on_psl():
    ps = _scan.pop() if _scan else 0
    _emit("PSL", dict(ihead(ps), units=ulist(_u32(ps + 0x38))) if ps else {"ps": 0})


def on_prr():
    room, ps, sp = _reg("edi"), _reg("edx"), _u32(_reg("esp"))
    _rr.append((room, ps, sp))
    lv = _u32(room + 0x58)
    _emit("PRR", dict(ihead(ps), room=room, level=lv, lid=_u32(lv + 0x1D0), seedp=sp, isroom=1 if sp == room + 0x14 else 0,
                      seed=_seed(sp), f28=_u32(room + 0x28)))


def on_prrx():
    if not _rr:
        return
    room, ps, sp = _rr.pop()
    _emit("PRRX", {"room": room, "ps": ps, "seed": _seed(sp), "units": ulist(_u32(ps + 0x38))})


def on_pld():
    room = _reg("ecx")
    ps = inst_of(room)
    _pld.append((room, ps))
    _emit("PLD", {"room": room, "ps": ps, "ds1": _u32(ps + 0x0C), "pending": _s32(ps + 0x3C)})


def on_pldx():
    if not _pld:
        return
    room, ps = _pld.pop()
    _emit("PLDX", {"room": room, "ps": ps, "f28": _u32(room + 0x28), "pending": _s32(ps + 0x3C),
                   "units": ulist(_u32(ps + 0x38))})


def _room_rect(room):
    return list(struct.unpack("<iiii", _mem(room + 0x34, 16)))


def on_ptr0():
    room = _reg("edi")
    ps = inst_of(room)
    lv = _u32(room + 0x58)
    _emit("PTR0", dict(ihead(ps), room=room, level=lv, lid=_u32(lv + 0x1D0), rect=_room_rect(room),
                       f28=_u32(room + 0x28), rlist=ulist(_u32(room + 0x5C)), units=ulist(_u32(ps + 0x38))))


def on_ptr1():
    room = _reg("edi")
    ps = inst_of(room)
    _emit("PTR1", {"room": room, "ps": ps, "rlist": ulist(_u32(room + 0x5C)), "units": ulist(_u32(ps + 0x38))})


def on_rpu():
    sroom = _reg("edx")
    room = _u32(sroom + 0x10)
    lv = _u32(room + 0x58) if room else 0
    _emit("RPU", {"sroom": sroom, "room": room, "lid": _u32(lv + 0x1D0) if lv else None,
                  "rlist": ulist(_u32(room + 0x5C)) if room else []})


def on_psp():
    pu, unit = _reg("esi"), _reg("eax")
    d = {"sroom": _reg("edi"), "pu": pu, "type": _s32(pu + 0x14), "id": _s32(pu + 4), "x": _s32(pu + 8),
         "y": _s32(pu + 0x18), "unit": unit}
    if unit:
        d["utype"], d["cls"] = _u32(unit), _u32(unit + 4)
    _emit("PSP", d)


def on_rpl():
    sroom = _u32(_reg("ebp") + 8)
    _emit("RPL", {"sroom": sroom, "room": _u32(sroom + 0x10), "pop": _s32_of(_reg("eax"))})


def _s32_of(v):
    return v - (1 << 32) if v & 0x80000000 else v


def on_l27():
    act = _reg("esi")
    _emit("L27", {"act": act, "v": _s32_of(_reg("eax")), "pd": _reg("ecx"), "seed": _seed(act)})


def on_l27x():
    act = _reg("esi")
    _emit("L27X", {"act": act, "idx": _s32_of(_reg("eax")), "pd": _reg("ecx"), "seed": _seed(act)})


for _a, _f in [(0x00667A35, on_scan_pre), (0x00667A3A, on_psl), (0x006678E2, on_prr), (0x006678E7, on_prrx),
               (0x00667890, on_pld), (0x0061B757, on_pldx), (0x0061B348, on_pldx), (0x0066697D, on_ptr0),
               (0x00666982, on_ptr1), (0x005559A0, on_rpu), (0x0055594E, on_psp), (0x0061A206, on_rpl),
               (0x006774B1, on_l27), (0x006774F9, on_l27x)]:
    PBp(_a, _f)


def on_lip():
    lv = _reg("edi")
    pd = _u32(lv + 0x14)
    _emit("LIP", {"level": lv, "id": _u32(lv + 0x1D0), "pd": pd, "idx": _s32(pd + 4) if pd and _u32(lv) == 2 else None})


PBp(0x006424C4, on_lip)   # LIP: sub_006424A0_LevelInit after its re-seed (EDI level): preset data and index


# FLG: the two writers of DRLG room +0x28 bit 0x800000 besides Populate 0 (the RoomPopLevelId-0 flag):
#   0x0066BD92 (EDI room: a neighbour room's level is a town, sub_006426A0) and 0x0066E37E (EAX room: hidden warp tiles)
def on_flg_town():
    _emit("FLG", {"site": 0x0066BD92, "room": _reg("edi")})


def on_flg_warp():
    _emit("FLG", {"site": 0x0066E37E, "room": _reg("eax")})


# PUC: sub_0066BF30_PresetUnitCreate called with a room (ECX): the unit it prepends to room +0x5C, and the caller
def on_puc():
    esp = _reg("esp")
    room = _reg("ecx")
    if room:
        typ, uid, mode, x, y = struct.unpack("<iiiii", _mem(esp + 4, 20))
        _emit("PUC", {"room": room, "ret": _u32(esp), "type": typ, "id": uid, "mode": mode, "x": x, "y": y})


for _a, _f in [(0x0066BD92, on_flg_town), (0x0066E37E, on_flg_warp), (0x0066BF30, on_puc)]:
    PBp(_a, _f)


# RSK (plan 0020 Phase 4): the row skip of DRLG_PresetClientUnitsB, a style-4 floor cell of main 0/4/8/16/29/39
def on_rsk():
    ebp = _reg("ebp")
    _emit("RSK", {"ps": _reg("esi"), "row": _s32(ebp - 0xC), "main": _reg("eax")})


PBp(0x00666368, on_rsk)
_emit("RSKON", {})        # tells tools/drlg.py gen that this log carries every RSK line
