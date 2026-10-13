# gdb Python logger for the plan 0016 Phase 2 required cases (drlg/0004 Phase 1b contradictions). Sourced after
# tools/gdb/drlg-gen.py and tools/gdb/drlg-preset.py by drlg-preset-poppad.gdb / drlg-preset-logicals.gdb, which set
# WP_MODE (and WP_DEFS / WP_LEVELS) with a `python` line first. Hardware read watchpoints (x86 debug registers,
# four at most); each hit logs the reading instruction's successor ($pc), the thread and two return addresses.
#
#   WPSET  a read watchpoint placed: address, length, what it watches
#   WPHIT  a read of a watched address: $pc (after the read), thread, [esp], [ebp+4], [[ebp]+4]
#   POPR   0x0066729A  sub_006671E0_PresetPopsUpdate after its pop search (ESI room, [ebp-8] instance): once per
#                      instance, its pop table (+0x40 count, +0x44 index, +0x50 rects) and LvlPrest PopPad (+0x3C)
#   POPU   0x0066729A  the same point: player x (EDI), y ([ebp+8]), found pop index ([ebp-0xC]); on change only
#   POPS   0x00667060  the pop show/hide call (ECX pop rect, [esp+4] main, [esp+8] flag)
#   LGB    0x00666DCD  after sub_0066D110 / sub_0066CCB0 in sub_00666AC0_PresetRoomTilesBuild (EBX room; both paths):
#                      the room's logic record (+0x64): flags, count, and the box list (+0x30, next +0x2C) as 12 dwords each
#   LGW    logicals mode, at POPU: the player's box changed inside a Logicals-1, Populate-1 preset room. The four
#          watches move to: client box +0x28, server box +0x28 (the server room of the same level and rectangle,
#          the box of the same rectangle), and +0x10 (box pointer) of the first wall entry of each room whose
#          +0x10 is that box (RoomTile +0x14 entries, 0x30 each, count +0x18)
import json
import struct

import gdb

INF = gdb.selected_inferior()
G_LVLPREST_ADDR = 0x0096C894
MODE = globals().get("WP_MODE", "poppad")
DEFS = globals().get("WP_DEFS", [])


def _m(a, n):
    return bytes(INF.read_memory(a, n))


def _u(a):
    return struct.unpack("<I", _m(a, 4))[0]


def _i(a):
    return struct.unpack("<i", _m(a, 4))[0]


def _r(n):
    return int(gdb.parse_and_eval("$" + n)) & 0xFFFFFFFF


def _out(tag, d):
    gdb.write("%s %s\n" % (tag, json.dumps(d, separators=(",", ":"))))


_n_wp = [0]


class Watch(gdb.Breakpoint):
    def __init__(self, addr, length, what):
        super().__init__("*(%s *) 0x%08X" % ({4: "int", 8: "long long"}[length], addr), gdb.BP_WATCHPOINT,
                         gdb.WP_READ, internal=True)
        self.silent = True
        self.addr, self.what = addr, what
        _n_wp[0] += 1
        _out("WPSET", {"addr": addr, "len": length, "what": what})

    def stop(self):
        try:
            ebp = _r("ebp")
            try:
                r1, r2 = _u(ebp + 4), _u(_u(ebp) + 4)
            except gdb.MemoryError:
                r1 = r2 = None
            _out("WPHIT", {"addr": self.addr, "what": self.what, "pc": int(gdb.parse_and_eval("$pc")) & 0xFFFFFFFF, "thread": gdb.selected_thread().num,
                           "esp0": _u(_r("esp")), "ret1": r1, "ret2": r2})
        except Exception as e:
            gdb.write("LOGERR %r\n" % (e,))
        return False


class WBp(gdb.Breakpoint):
    def __init__(self, addr, fn):
        super().__init__("*0x%08X" % addr, internal=True)
        self.silent = True
        self.fn = fn

    def stop(self):
        try:
            self.fn()
        except Exception as e:
            gdb.write("LOGERR %r\n" % (e,))
        return False


_static_done = [False]


def place_static():
    """poppad: LvlPrest +0x3C (PopPad) of each WP_DEFS record, plus +0x38 (Pops) of the first as a control."""
    if _static_done[0] or MODE != "poppad":
        return
    base = _u(G_LVLPREST_ADDR)
    if not base:
        return
    _static_done[0] = True
    for k, df in enumerate(DEFS):
        rec = base + df * 0x1B0
        Watch(rec + 0x3C, 4, "LvlPrest[%d].PopPad (+0x3C)" % df)
        if k == 0:
            Watch(rec + 0x38, 4, "LvlPrest[%d].Pops (+0x38), control" % df)


_popr_seen = set()
_popu_last = {}


def on_pop_search():
    room = _r("esi")
    ebp = _r("ebp")
    inst = _u(ebp - 8)
    x, y, found = _r("edi"), _i(ebp + 8), _i(ebp - 0xC)
    if inst and inst not in _popr_seen:
        _popr_seen.add(inst)
        n = _i(inst + 0x40)
        rec = _u(inst + 8)
        _out("POPR", {"room": room, "ps": inst, "def": _i(inst), "n": n, "poppad": _i(rec + 0x3C),
                      "idx": [_i(_u(inst + 0x44) + 4 * k) for k in range(n)],
                      "main": [_i(_u(inst + 0x48) + 4 * k) for k in range(n)],
                      "rects": [list(struct.unpack("<iiii", _m(_u(inst + 0x50) + 16 * k, 16))) for k in range(n)]})
    key = (room, inst)
    if _popu_last.get(key) != (x, y, found):
        _popu_last[key] = (x, y, found)
        _out("POPU", {"room": room, "ps": inst, "x": x if x < 0x80000000 else x - (1 << 32), "y": y, "found": found})
        if MODE == "logicals":
            on_lg_player(room, x, y)


def on_pops():
    esp, ecx = _r("esp"), _r("ecx")
    _out("POPS", {"room": _r("ebx"), "rect": list(struct.unpack("<iiii", _m(ecx, 16))), "main": _i(esp + 4),
                  "flag": _i(esp + 8)})


def on_lgb():
    room = _r("ebx")
    lv = _u(room + 0x58)
    lid = _u(lv + 0x1D0)
    lg = _u(room + 0x64)
    if not lg:
        return
    flags, n = _u(lg), _i(lg + 4)
    copy = "client" if _u(room + 0x28) & 0x40000 else "server"
    pr = _u(room + 0x20)
    inst = _u(pr + 8) if pr else 0
    _out("LGB", {"room": room, "lid": lid, "copy": copy, "def": _i(inst) if inst else None,
                 "rect": list(struct.unpack("<iiii", _m(room + 0x34, 16))), "flags": flags, "n": n,
                 "boxes": [list(v) for _, v in box_list(room)]})
    _rooms[room] = (lid, copy, tuple(_m(room + 0x34, 16)))


_rooms = {}          # DRLG room -> (level id, copy, rect bytes), from LGB
_watches = []
_lg_cur = [None]


def box_list(room):
    lg = _u(room + 0x64)
    out, b = [], (_u(lg + 0x30) if lg else 0)
    while b and len(out) < 4096:
        out.append((b, struct.unpack("<12i", _m(b, 0x30))))
        b = _u(b + 0x2C)
    return out


def wall_with_box(room, box):
    t = _u(room + 0x54)
    if not t:
        return 0
    arr, n = _u(t + 0x14), _u(t + 0x18)
    for k in range(min(n, 8192)):
        if _u(arr + 0x30 * k + 0x10) == box:
            return arr + 0x30 * k + 0x10
    return 0


def on_lg_player(room, x, y):
    """logicals mode: follow the player's box in a Logicals-1, Populate-1 preset room (client copy)."""
    pr = _u(room + 0x20)
    if not pr or room not in _rooms:
        return
    rec = _u(_u(pr + 8) + 8)
    if _i(rec + 0x0C) != 1 or _i(rec + 0x08) != 1 or not _u(_u(room + 0x64)) & 2:
        return
    tx, ty = x // 5, y // 5
    cb = next((b for b, v in box_list(room) if v[0] <= tx < v[2] and v[1] <= ty < v[3]), 0)
    if not cb or _lg_cur[0] == (room, cb):
        return
    _lg_cur[0] = (room, cb)
    lid, _, rect = _rooms[room]
    srv = next((r for r, (l2, c2, r2) in _rooms.items() if c2 == "server" and l2 == lid and r2 == rect), 0)
    crect = struct.unpack("<4i", _m(cb, 16))
    sb = next((b for b, v in box_list(srv) if tuple(v[:4]) == crect), 0) if srv else 0
    for w in _watches:
        w.delete()
    del _watches[:]
    _n_wp[0] = 0
    _out("LGW", {"room": room, "lid": lid, "x": x, "y": y, "box": cb, "region": _i(cb + 0x28), "srv": srv, "sbox": sb})
    for what, a in (("client box +0x28 region id", cb + 0x28), ("server box +0x28 region id", sb + 0x28 if sb else 0),
                    ("client wall entry +0x10 box pointer", wall_with_box(room, cb)),
                    ("server wall entry +0x10 box pointer", wall_with_box(srv, sb) if sb else 0)):
        if a:
            _watches.append(Watch(a, 4, "%s, level %d" % (what, lid)))


def on_lc0_static():
    place_static()


place_static()
for _a, _f in [(0x0066729A, on_pop_search), (0x00667060, on_pops), (0x00666DCD, on_lgb),
               (0x00642B67, on_lc0_static)]:
    WBp(_a, _f)
