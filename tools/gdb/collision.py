# gdb Python logger for plan 0017 Phase 2 (the room collision grid, docs/findings/drlg/0005-collision.md section 12).
# Sourced by tools/gdb/collision.gdb after tools/gdb/drlg-gen.py, tools/gdb/drlg-roomk.py and tools/gdb/mon-spawn.py,
# whose tags it leaves unchanged. One line per event, "TAG {json}". Addresses refer to the pinned game.exe (image base
# 0x400000). Big payloads are zlib-compressed JSON in base64 under the key "z" (tools/collision.py decodes them).
# "th" is gdb's thread number: the server and the client share one process in a single-player game.
#
# Tiles and activation:
#   TL   once per DT1 tile record seen: pointer, DT1 path (tile +0x58 -> the relocated file's name), tile index
#        ((p - file[+0x110]) / 0x60; DT1_Relocate made +0x110 absolute), orientation +0x14, main +0x18, sub +0x1C, u16 +0x06, the 25 sub-tile
#        bytes at +0x28 (TILE_GetSubtileFlags 0x00604CE0)
#   CB   COLL_MapBuild 0x0064C900, at 0x0064C9FF (after the stamp loop; [ebp-0x10] = the active room, EBX = the new map):
#        room, DRLG room, level, subtile rect +0x4C, and in "z": the near list (+0x00, count +0x24) with each near room's
#        tile rect (+0x5C) and its wall / floor / shadow entries (tile view +0x08: x +0x08, y +0x0C, flags +0x14,
#        tile +0x18, orientation +0x1C), and the map's cells (u16, row-major)
#   TCU  sub_0064C860_TileCollisionUpdate entry: ECX room, EDX entry (x, y, current tile +0x18), new tile [esp+4]
# Marks (COLL_PatternMark 0x0064EA90, COLL_PatternUnmark 0x0064EC10, COLL_RectOrWH 0x0064DE30,
# COLL_RectClearWH 0x0064DC00, COLL_SizeMark 0x0064EA00, COLL_SizeUnmark 0x0064EBA0; all stdcall):
#   CM   {f: PM|PU|RO|RC|SM|SU, room, x, y, a (pattern / size / w), b (mask / h), m (mask of RO/RC), ret}; logged only
#        inside a window: from the room driver's RW1 point to the pass exit PX, on that thread
# The pass:
#   SN   0x0054EC91 (pass entry, after P0): the grid snapshot (ADR-0004 oracle): the room, every room of its near
#        list and every room of their near lists (two hops), each with rect, near list, cells, DRLG room, tile origin,
#        its logic record (flags, first box id, box grid as box ids) and its floor entries in array order; level seed
#        +0x1C4
#   NWP  0x0054DB96 NearWarpTest after the warp-point lookup and the Levels read: the level's warp points (ESI: x[9],
#        y[9], count +0x48) and WarpDist (EDI = Levels +0x0C)
#   NWW  0x0054DBEE after sub_00619E50_ActLevelPointFind(.., 11): the type-11 point (tiles)
#   NW0 / NW1  0x0054DD2F / 0x0054DD34 (around the call): level seed +0x1C4 and the level's active rooms (R1)
# Logic regions (Logicals 1): LG0 0x0066D213 (before LOGIC_FloodAll): orientation, floor and barrier grids, the
#   level counter; LG1 0x0066D277 (after LogicBoxesFromGrid and LogicWallBoxes): the id grid, the boxes;
#   LG2 0x0066D27E (after LOGIC_NeighbourMerge): the boxes
# Corpses (C1): DC at the deadCol tests 0x004B05DB / 0x004B09FB (ESI unit, [ebp+8] MonStats2 record): unit, class,
#   deadCol, path position, room, pattern, mark mask, 5x5 cells; DCX at 0x004B05E8 / 0x004B0A0A: the cells after;
#   DCR at each later SN: the cells of the last deadCol-1 corpses again (up to 6 re-dumps each)
# Missiles (C2): MS at PATH_SetMarkMask 0x00648C30 with mask 0x40 ([esp+8]): path, unit, class, position, room,
#   size +0x44; MSX at its rets 0x00648CB2 / 0x00648CCC: 5x5 cells after
import base64
import json
import struct
import zlib

import gdb


def _collision_main():
    inf = gdb.selected_inferior()
    tiles = {}                 # tile pointer -> emitted record hash
    win = {}                   # thread -> room of the open RW1..PX window
    dead = []                  # [room, x, y, unit, cls, n]
    pend = {}                  # thread -> pending DC / MS record

    def mem(a, n):
        return bytes(inf.read_memory(a, n))

    def u16(a):
        return struct.unpack("<H", mem(a, 2))[0]

    def u32(a):
        return struct.unpack("<I", mem(a, 4))[0]

    def s32(a):
        return struct.unpack("<i", mem(a, 4))[0]

    def reg(n):
        return int(gdb.parse_and_eval("$" + n)) & 0xFFFFFFFF

    def th():
        t = gdb.selected_thread()
        return t.num if t else 0

    def emit(tag, d):
        gdb.write("%s %s\n" % (tag, json.dumps(d, separators=(",", ":"))))

    def z(obj):
        return base64.b64encode(zlib.compress(json.dumps(obj, separators=(",", ":")).encode(), 6)).decode()

    def cstr(a, n=260):
        return mem(a, n).split(b"\0", 1)[0].decode("latin-1")

    def sd(p):
        return "%08x:%08x" % struct.unpack("<II", mem(p, 8))

    # --- tiles ------------------------------------------------------------------------------------------------
    def tile(p):
        if not p:
            return 0
        b = mem(p, 0x60)
        o, m, s = struct.unpack_from("<iii", b, 0x14)
        key = (o, m, s, b[0x28:0x41], b[6:8])
        if tiles.get(p) != key:
            tiles[p] = key
            name = u32(p + 0x58)
            path, idx = None, None
            if name:
                base = name - 8
                path = cstr(name)
                idx = (p - u32(base + 0x110)) // 0x60
            emit("TL", {"p": p, "f": path, "i": idx, "o": o, "m": m, "s": s, "w6": struct.unpack_from("<H", b, 6)[0],
                        "b": b[0x28:0x41].hex()})
        return p

    def entries(arr, n):
        if not arr or n <= 0:
            return []
        b = mem(arr, 0x30 * n)
        out = []
        for i in range(n):
            x, y, _lb, fl, tp, o = struct.unpack_from("<iiIIIi", b, 0x30 * i + 8)
            out.append([x, y, fl, tile(tp), o])
        return out

    def tileview(room):
        v = u32(room + 8)
        if not v:
            return [], [], []
        w, nw, f, nf, s, ns = struct.unpack("<IiIiIi", mem(v, 24))
        return entries(w, nw), entries(f, nf), entries(s, ns)

    def near(room):
        n = s32(room + 0x24)
        p = u32(room)
        return list(struct.unpack("<%dI" % n, mem(p, 4 * n))) if (p and 0 < n < 64) else []

    def cmap(room):
        m = u32(room + 0x20)
        if not m:
            return None
        x0, y0, w, h = struct.unpack("<iiii", mem(m, 16))
        c = u32(m + 0x20)
        if not c or w <= 0 or h <= 0 or w * h > 1 << 20:
            return [x0, y0, w, h, None]
        return [x0, y0, w, h, mem(c, 2 * w * h).hex()]

    def level_of(room):
        dr = u32(room + 0x10) if room else 0
        return u32(dr + 0x58) if dr else 0

    def lseed(room):
        lv = level_of(room)
        return sd(lv + 0x1C4) if lv else None

    def cell(hint, x, y):
        """RoomAtSubtile (hint, then its near list) and the cell; None when no room holds the point."""
        cand = [hint] + near(hint) if hint else []
        for r in cand:
            if not r:
                continue
            x0, y0, w, h = struct.unpack("<iiii", mem(r + 0x4C, 16))
            if x0 <= x < x0 + w and y0 <= y < y0 + h:
                m = u32(r + 0x20)
                c = u32(m + 0x20) if m else 0
                if not c:
                    return None
                return u16(c + 2 * ((y - y0) * w + (x - x0)))
        return None

    def around(room, x, y, k=2):
        return [[cell(room, x + dx, y + dy) for dx in range(-k, k + 1)] for dy in range(-k, k + 1)]

    class Bp(gdb.Breakpoint):
        def __init__(self, addr, fn):
            super().__init__("*0x%08X" % addr, internal=True)
            self.silent = True
            self.fn = fn

        def stop(self):
            try:
                self.fn()
            except Exception as e:  # never stop the game on a logger error; log it instead
                gdb.write("LOGERR collision %r\n" % (e,))
            return False

    # --- activation -------------------------------------------------------------------------------------------
    def on_cb():
        ebp = reg("ebp")
        room = u32(ebp - 0x10)
        nl = near(room)
        nd = []
        for n in nl:
            W, F, S = tileview(n)
            nd.append([n, u32(n + 0x10), list(struct.unpack("<iiii", mem(n + 0x5C, 16))), W, F, S])
        lv = level_of(room)
        emit("CB", {"th": th(), "room": room, "dr": u32(room + 0x10), "lid": s32(lv + 0x1D0) if lv else None,
                    "rect": list(struct.unpack("<iiii", mem(room + 0x4C, 16))), "map": reg("ebx"),
                    "z": z({"near": nd, "cells": cmap(room)})})

    def on_tcu():
        room, e, new = reg("ecx"), reg("edx"), u32(reg("esp") + 4)
        x, y = struct.unpack("<ii", mem(e + 8, 8)) if e else (None, None)
        emit("TCU", {"th": th(), "room": room, "e": e, "x": x, "y": y, "fl": u32(e + 0x14) if e else None,
                     "old": tile(u32(e + 0x18)) if e else None, "new": tile(new), "o": s32(e + 0x1C) if e else None,
                     "t0": list(struct.unpack("<ii", mem(u32(room + 0x20) + 0x10, 8))) if room and u32(room + 0x20) else None,
                     "ret": u32(reg("esp"))})

    Bp(0x0064C9FF, on_cb)
    Bp(0x0064C860, on_tcu)

    # --- marks (windowed) -------------------------------------------------------------------------------------
    def mark(f, nargs):
        def fn():
            t = th()
            if t not in win:
                return
            sp = reg("esp")
            a = struct.unpack("<%dI" % (nargs + 1), mem(sp, 4 * (nargs + 1)))
            d = {"th": t, "f": f, "room": a[1], "x": struct.unpack("<i", struct.pack("<I", a[2]))[0],
                 "y": struct.unpack("<i", struct.pack("<I", a[3]))[0], "a": a[4], "b": a[5], "ret": a[0]}
            if nargs == 6:
                d["m"] = a[6]
            emit("CM", d)
        return fn

    for addr, f, n in ((0x0064EA90, "PM", 5), (0x0064EC10, "PU", 5), (0x0064DE30, "RO", 6), (0x0064DC00, "RC", 6),
                       (0x0064EA00, "SM", 5), (0x0064EBA0, "SU", 5)):
        Bp(addr, mark(f, n))

    def win_open():
        win[th()] = reg("esi")

    def win_close():
        win.pop(th(), None)

    for a in (0x0052D1CE, 0x0052D101):          # RW1 (after the wanderer tick; presets next)
        Bp(a, win_open)
    for a in (0x0052D1C4, 0x0052D0F6):          # RW0: a new room, close any stale window
        Bp(a, win_close)
    Bp(0x0054EEDD, win_close)                    # PX

    # --- pass entry snapshot ----------------------------------------------------------------------------------
    def logic(dr):
        rec = u32(dr + 0x64) if dr else 0
        if not rec:
            return None
        flags = u32(rec)
        first = u32(rec + 0x30)
        d = {"fl": flags, "n": s32(rec + 4), "first": s32(first + 0x28) if first else None,
             "t": list(struct.unpack("<ii", mem(dr + 0x34, 8)))}
        cells, rows, w, h = struct.unpack("<IIii", mem(rec + 0x1C, 16))
        if cells and rows and 0 < w <= 512 and 0 < h <= 512:
            offs = struct.unpack("<%di" % h, mem(rows, 4 * h))
            ids = {}
            g = []
            for yy in range(h):
                row = struct.unpack("<%dI" % w, mem(cells + 4 * offs[yy], 4 * w))
                for p in row:
                    if p and p not in ids:
                        ids[p] = s32(p + 0x28)
                g.append([ids[p] if p else None for p in row])
            d["grid"] = [w, h, g]
        return d

    def on_sn():
        room = reg("edx")
        t = th()
        rooms = []
        hop1 = [room] + [n for n in near(room) if n != room]
        seen = set(hop1)
        hop2 = []
        for r in hop1[1:]:
            for n in near(r):
                if n not in seen:
                    seen.add(n)
                    hop2.append(n)
        for k, r in enumerate(hop1 + hop2):
            dr = u32(r + 0x10)
            _w, F, _s = tileview(r)
            rooms.append({"r": r, "dr": dr, "hop": 0 if k == 0 else (1 if k < len(hop1) else 2),
                          "rect": list(struct.unpack("<iiii", mem(r + 0x4C, 16))),
                          "trect": list(struct.unpack("<iiii", mem(r + 0x5C, 16))), "near": near(r),
                          "cells": cmap(r), "lg": logic(dr), "floors": F})
        emit("SN", {"th": t, "room": room, "lseed": lseed(room), "z": z({"rooms": rooms, "floors": rooms[0]["floors"]})})
        keep = []
        for dd in dead:
            emit("DCR", {"room": dd[0], "x": dd[1], "y": dd[2], "u": dd[3], "cls": dd[4], "n": dd[5],
                         "cells": around(dd[0], dd[1], dd[2])})
            dd[5] += 1
            if dd[5] < 6:
                keep.append(dd)
        dead[:] = keep

    Bp(0x0054EC91, on_sn)

    # --- NearWarpTest -----------------------------------------------------------------------------------------
    def actives(room):
        lv = level_of(room)
        out, r, k = [], u32(lv + 0x10) if lv else 0, 0
        while r and k < 4096:
            a = u32(r + 0x30)
            if a:
                out.append(a)
            r = u32(r + 0x24)
            k += 1
        return sorted(out)

    def on_nw(tag):
        def fn():
            room = reg("eax") if tag == "NW0" else st_nw.get(th(), 0)
            if tag == "NW0":
                st_nw[th()] = room
            emit(tag, {"th": th(), "room": room, "lseed": lseed(room) if room else None,
                       "act": actives(room) if room else None})
        return fn

    st_nw = {}
    Bp(0x0054DD2F, on_nw("NW0"))
    Bp(0x0054DD34, on_nw("NW1"))

    def on_nwp():
        p = reg("esi")
        xs = list(struct.unpack("<9i", mem(p, 36)))
        ys = list(struct.unpack("<9i", mem(p + 0x24, 36)))
        emit("NWP", {"th": th(), "p": p, "xs": xs, "ys": ys, "n": s32(p + 0x48), "wd": reg("edi")})

    def on_nww():
        ebp = reg("ebp")
        emit("NWW", {"th": th(), "x": s32(ebp - 4), "y": s32(ebp - 8)})

    Bp(0x0054DB96, on_nwp)
    Bp(0x0054DBEE, on_nww)

    # --- logic regions ----------------------------------------------------------------------------------------
    def dgrid(g):
        if not g:
            return None
        cells, rows, w, h = struct.unpack("<IIii", mem(g, 16))
        if not cells or not rows or not (0 < w <= 512 and 0 < h <= 512):
            return [w, h, None]
        offs = struct.unpack("<%di" % h, mem(rows, 4 * h))
        out = []
        for yy in range(h):
            out.append(list(struct.unpack("<%dI" % w, mem(cells + 4 * offs[yy], 4 * w))))
        return [w, h, out]

    def boxes(rec):
        out, b, k = [], u32(rec + 0x30), 0
        while b and k < 4096:
            v = struct.unpack("<12i", mem(b, 0x30))
            out.append({"b": b, "r0": list(v[0:4]), "r": list(v[4:8]), "kind": v[8], "u24": v[9], "id": v[10]})
            b = u32(b + 0x2C)
            k += 1
        return out

    def on_lg0():
        ebp = reg("ebp")
        dr = u32(ebp - 0x24)
        lv = u32(dr + 0x58)
        emit("LG0", {"th": th(), "dr": dr, "lid": s32(lv + 0x1D0), "t": list(struct.unpack("<iiii", mem(dr + 0x34, 16))),
                     "base": s32(ebp - 0xC), "z": z({"orient": dgrid(u32(ebp - 0x1C)), "wall": dgrid(u32(ebp - 0x18)),
                                                      "floor": dgrid(u32(ebp - 0x14)), "barrier": dgrid(ebp - 0x44)})})

    def on_lg(tag):
        def fn():
            dr = reg("edi")
            rec = u32(dr + 0x64)
            lv = u32(dr + 0x58)
            d = {"th": th(), "dr": dr, "fl": u32(rec), "n": s32(rec + 4), "ctr": s32(lv + 0x1DC)}
            pay = {"boxes": boxes(rec)}
            if tag == "LG1":
                pay["ids"] = dgrid(rec + 8)
            d["z"] = z(pay)
            emit(tag, d)
        return fn

    Bp(0x0066D213, on_lg0)
    Bp(0x0066D277, on_lg("LG1"))
    Bp(0x0066D27E, on_lg("LG2"))

    # --- corpses (C1) -----------------------------------------------------------------------------------------
    def pathpos(u):
        p = u32(u + 0x2C)
        if not p:
            return None
        return {"x": u16(p + 2), "y": u16(p + 6), "room": u32(p + 0x1C), "pat": s32(p + 0x48), "mm": u32(p + 0x4C),
                "size": s32(p + 0x44)}

    def on_dc():
        u = reg("esi")
        rec = u32(reg("ebp") + 8)
        pp = pathpos(u)
        d = {"th": th(), "u": u, "type": s32(u), "cls": s32(u + 4), "dc": (mem(rec + 6, 1)[0] >> 3) & 1,
             "pc": int(gdb.parse_and_eval("$pc")) & 0xFFFFFFFF}
        if pp:
            d.update(pp)
            d["cells"] = around(pp["room"], pp["x"], pp["y"])
        pend[("DC", th())] = (u, pp)
        emit("DC", d)

    def on_dcx():
        k = ("DC", th())
        if k not in pend:
            return
        u, pp = pend.pop(k)
        if not pp:
            return
        pp2 = pathpos(u)
        emit("DCX", {"th": th(), "u": u, "cls": s32(u + 4), "pat": pp2["pat"] if pp2 else None,
                     "mm": pp2["mm"] if pp2 else None, "cells": around(pp["room"], pp["x"], pp["y"])})
        dead.append([pp["room"], pp["x"], pp["y"], u, s32(u + 4), 0])
        del dead[:-12]

    Bp(0x004B05DB, on_dc)
    Bp(0x004B09FB, on_dc)
    Bp(0x004B05E8, on_dcx)
    Bp(0x004B0A0A, on_dcx)

    # --- missiles (C2) ----------------------------------------------------------------------------------------
    def on_ms():
        sp = reg("esp")
        p, m = struct.unpack("<II", mem(sp + 4, 8))
        if m != 0x40:
            return
        u = u32(p + 0x30)
        d = {"th": th(), "path": p, "u": u, "type": s32(u) if u else None, "cls": s32(u + 4) if u else None,
             "x": u16(p + 2), "y": u16(p + 6), "room": u32(p + 0x1C), "size": s32(p + 0x44), "pat": s32(p + 0x48),
             "mm0": u32(p + 0x4C)}
        if d["room"]:
            d["cells"] = around(d["room"], d["x"], d["y"])
        pend[("MS", th())] = d
        emit("MS", d)

    def on_msx():
        d = pend.pop(("MS", th()), None)
        if d and d["room"]:
            emit("MSX", {"th": th(), "path": d["path"], "mm": u32(d["path"] + 0x4C),
                         "cells": around(d["room"], d["x"], d["y"])})

    Bp(0x00648C30, on_ms)
    Bp(0x00648CB2, on_msx)
    Bp(0x00648CCC, on_msx)
    gdb.write("COLLISION logger armed\n")


_collision_main()
