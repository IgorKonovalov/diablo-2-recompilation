# gdb Python logger for plan 0008 Phase 2 (k per room). Sourced by tools/gdb/drlg-roomk.gdb.
#
# One line per event, "TAG {json}". Addresses refer to the pinned game.exe (image base 0x400000).
# Every value is read from the 32-bit game process; pointers are printed as integers.
#
#   RRESEED  0x0066EE40  sub_0066EE40_DrlgRoomReseed entry (ECX = DRLG room): the model's inputs that
#                        do not change during the window (rect, flags, DT1 list, neighbours, warps).
#   LSUB     0x006707A0  sub_006707A0_LvlSubApply entry (ECX = param struct): pass, seed, the three
#                        OutRoom grids (model input for k_sub).
#   LSUBX    0x00670808  its ret: seed after the pass, and the groups of the records used (game memory).
#   TINIT    0x0066EE70  sub_0066EE70_DrlgRoomTypeInit entry (ECX = room): seed, the grids the tile
#                        build walks, and which neighbours are built (+0x54) with their seeds.
#   O89      0x0066D9E0  sub_0066D9E0_Orient89Unit entry (ESI = room): oracle, seed in.
#   O89D     0x0066DAC1  its RNG_Range(room+0x14, 3) call: the oracle's one draw.
#   RACT     0x0064233A  DRLG_RoomActivate before its step (ESI = room): seed = init(+0x04) after k steps.
#   AROOM    0x0064236E  after DUNGEON_RoomCreate: active-room seed.
#   RTFREE   0x0066F0B0  RoomTile free (ECX = room).
import json
import struct

import gdb

INF = gdb.selected_inferior()

G_DT1_CACHE = 0x008ADBB4
G_LEVELDEFS = 0x0096C890
G_LVLPREST = 0x0096C894
G_LVLWARP = 0x0096CA00
G_LVLSUB = 0x0096CA10
G_LVLSUB_IDX = 0x0096CA18


def mem(addr, n):
    return bytes(INF.read_memory(addr, n))


def u32(addr):
    return struct.unpack("<I", mem(addr, 4))[0]


def s32(addr):
    return struct.unpack("<i", mem(addr, 4))[0]


def reg(name):
    return int(gdb.parse_and_eval("$" + name)) & 0xFFFFFFFF


def cstr(addr, n=260):
    b = mem(addr, n)
    return b.split(b"\0", 1)[0].decode("latin-1")


def seed(room):
    lo, hi = struct.unpack("<II", mem(room + 0x14, 8))
    return "%08x:%08x" % (lo, hi)


def grid(g):
    """Grid struct {cells, rowoffs, w, h, owned} -> [w, h, hex cells row-major]."""
    cells, rows, w, h = struct.unpack("<IIii", mem(g, 16))
    if cells == 0 or w <= 0 or h <= 0 or w > 512 or h > 512:
        return [w, h, ""]
    offs = struct.unpack("<%dI" % h, mem(rows, 4 * h))
    out = []
    for y in range(h):
        out.append("".join("%08x" % v for v in struct.unpack("<%dI" % w, mem(cells + 4 * offs[y], 4 * w))))
    return [w, h, "".join(out)]


_dt1_names = {}


def dt1_name(index_ptr):
    if index_ptr not in _dt1_names:
        node = u32(G_DT1_CACHE)
        while node:
            _dt1_names[u32(node + 0x108)] = cstr(node)
            node = u32(node + 0x10C)
    return _dt1_names.get(index_ptr, "?%08x" % index_ptr)


def level_info(room):
    lvl = u32(room + 0x58)
    act = u32(lvl + 0x1B4)
    lid = u32(lvl + 0x1D0)
    # Warp id array as fn 0x0066AEC0 resolves it: act+0x90 override list, else leveldefs(+0x68).
    arr, node = None, u32(act + 0x90)
    while node:
        k = u32(node)
        if k == 0:
            break
        if k == lid:
            arr = node + 0x24
            break
        node = u32(node + 0x44)
    if arr is None:
        arr = u32(G_LEVELDEFS) + lid * 0x9C + 0x68
    warps = list(struct.unpack("<8i", mem(arr, 32)))
    return {"level": lid, "ltype": u32(lvl + 0x1C0), "act": mem(act + 0x480, 1)[0],
            "actflag": u32(act + 0x478), "warpids": warps}


def warp_nodes(room):
    base = u32(G_LVLWARP)
    out, node = [], u32(room + 0x4C)
    while node:
        rec = u32(node + 0x10)
        out.append({"rec": (rec - base) // 0x30 if rec else -1, "id": s32(rec) if rec else None})
        node = u32(node + 4)
    return out


def room_head(room):
    x, y, w, h = struct.unpack("<iiii", mem(room + 0x34, 16))
    return {"room": room, "seed": seed(room), "type": u32(room + 0x48), "f28": u32(room + 0x28),
            "rect": [x, y, w, h]}


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


def on_rreseed():
    r = reg("ecx")
    d = room_head(r)
    d.update(level_info(r))
    d["r04"] = u32(r + 4)
    d["mask"] = u32(r + 0x50)
    d["rt"] = u32(r + 0x54)
    d["dt1"] = [dt1_name(p) for p in struct.unpack("<32I", mem(r + 0x68, 128)) if p]
    n = s32(r + 0x2C)
    d["nb"] = list(struct.unpack("<%dI" % n, mem(u32(r + 8), 4 * n))) if n > 0 else []
    d["warps"] = warp_nodes(r)
    if d["type"] == 2:
        p = u32(r + 0x20)
        ps = u32(p + 8)
        lp = u32(ps + 8)
        ds1 = u32(ps + 0xC)
        d["preset"] = {"def": s32(p), "lvlprest": (lp - u32(G_LVLPREST)) // 0x1B0,
                       "killedge": s32(lp + 0x18), "fillblanks": s32(lp + 0x1C), "animate": s32(lp + 0x14),
                       "prect": list(struct.unpack("<iiii", mem(ps + 0x10, 16))),
                       "nwall": s32(ds1 + 0x14), "nfloor": s32(ds1 + 0x18)}
    emit("RRESEED", d)


_lsub = []


def on_lsub():
    p = reg("ecx")
    r = u32(p)
    t = s32(p + 0x30)
    o = u32(p + 4)
    d = {"room": r, "seed": seed(r), "stype": t, "theme": s32(p + 0x34), "smask": u32(p + 0x38),
         "orient": grid(o), "wall": grid(o + 0x14), "floor": grid(o + 0x28)}
    if t >= 0:
        d["rec"] = s32(u32(G_LVLSUB_IDX) + 4 * t)
    _lsub.append((r, t, u32(p + 0x38)))
    emit("LSUB", d)


def ds1_groups(rec_addr):
    ds1 = u32(rec_addr + 0x50)
    if not ds1:
        return None
    n, arr = s32(ds1 + 0x4C), u32(ds1 + 0x50)
    return [list(struct.unpack("<iiii", mem(arr + 0x18 * i, 16))) for i in range(max(n, 0))]


def on_lsubx():
    """Seed after the pass, and the substitution groups of every record the pass used, as the game
    holds them (a truncated DS1 is read past its end)."""
    r, t, m = _lsub.pop() if _lsub else (0, -1, 0)
    d = {"room": r, "seed": seed(r) if r else None, "groups": {}}
    if t >= 0:
        idx = s32(u32(G_LVLSUB_IDX) + 4 * t)
        i = 0
        while m:
            if m & 1:
                d["groups"][str(idx + i)] = ds1_groups(u32(G_LVLSUB) + (idx + i) * 0x15C)
            m >>= 1
            i += 1
    emit("LSUBX", d)


def on_tinit():
    r = reg("ecx")
    d = room_head(r)
    t = d["type"]
    p = u32(r + 0x20)
    if t == 1:
        d["grids"] = {"orient": grid(p), "wall": grid(p + 0x14), "floor": grid(p + 0x28)}
    elif t == 2:
        ds1 = u32(u32(p + 8) + 0xC)
        nw, nf = s32(ds1 + 0x14), s32(ds1 + 0x18)
        d["grids"] = {"floor": [grid(p + 0xB0 + 0x14 * i) for i in range(nf)],
                      "wall": [grid(p + 0x10 + 0x14 * i) for i in range(nw)],
                      "orient": [grid(p + 0x60 + 0x14 * i) for i in range(nw)],
                      "shadow": grid(p + 0xD8)}
    n = s32(r + 0x2C)
    nbs = struct.unpack("<%dI" % n, mem(u32(r + 8), 4 * n)) if n > 0 else ()
    d["nbstate"] = [[q, 1 if u32(q + 0x54) else 0, seed(q)] for q in nbs]
    d["rt"] = u32(r + 0x54)
    emit("TINIT", d)


def on_o89():
    r = reg("esi")
    emit("O89", {"room": r, "seed": seed(r), "tile": u32(reg("esp") + 4)})


def on_o89d():
    r = reg("esi")
    emit("O89D", {"room": r, "seed": seed(r)})


def on_ract():
    r = reg("esi")
    emit("RACT", {"room": r, "r04": u32(r + 4), "seed": seed(r)})


def on_aroom():
    r, a = reg("esi"), reg("eax")
    lo, hi = struct.unpack("<II", mem(a + 0x6C, 8))
    emit("AROOM", {"room": r, "aroom": a, "seed": seed(r), "aseed": "%08x:%08x" % (lo, hi),
                   "flags": u32(a + 0x34)})


def on_rtfree():
    r = reg("ecx")
    emit("RTFREE", {"room": r, "rt": u32(r + 0x54), "f28": u32(r + 0x28)})


for addr, fn in [(0x0066EE40, on_rreseed), (0x006707A0, on_lsub), (0x00670808, on_lsubx),
                 (0x0066EE70, on_tinit), (0x0066D9E0, on_o89), (0x0066DAC1, on_o89d),
                 (0x0064233A, on_ract), (0x0064236E, on_aroom), (0x0066F0B0, on_rtfree)]:
    Bp(addr, fn)
