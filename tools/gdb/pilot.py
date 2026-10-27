# gdb Python helper for scripted play (plan 0019 Phase 2): the lines tools/d2pilot.py steers by, without the heavy
# model loggers of plans 0014-0018. Nothing here feeds a model. One line per event, "TAG {json}" (tools/tc.py and
# tools/quality.py skip JSON lines). Addresses refer to the pinned game.exe (image base 0x400000).
#
#   GPTR     0x0052C312 (GAME_InitSeeds, EDI = game): the server game pointer the MON scan walks
#   RL       0x0066B970 (DRLG room added to its level: ECX level, EDX room): level pointer, room, tile rect, preset
#            def (type 2), and the room's warp nodes (room +0x4C list, LvlWarp record index and id) as drlg-roomk.py
#            (lane/rdp: also "lid", the level id at level +0x1D0, so that d2pilot's warp_dest knows a warp's
#            destination level before the player has been there)
#   RRESEED  0x0066EE40 (room activation, ECX = DRLG room): room and level id
#   CB       0x0064C9FF (COLL_MapBuild after the stamp loop; [ebp-0x10] room): sub-tile rect and the cells only,
#            zlib+base64 JSON under "z" as collision.py writes them ({"cells": [x0, y0, w, h, hex]})
#   PLR      COLL_PatternMark 0x0064EA90 with mask 0x80 (a player's mark): thread, room, level id, x, y; when moved
#   WRP      0x0066E21F in sub_0066E1C0_WarpUnitAdd (ESI = DRLG room, EDI = LvlWarp row): the warp unit's offset in
#            the room after the row's offsets are added ([ebp+0xC], ECX), the room's tile rect, the level id
#   MON      at a PLR line, at most every 0.3 s: the server's monsters within 48 sub-tiles of that position, from the
#            game's unit lists (game +0x1320: 128 heads of type 1, next = unit +0xE4): unit id, class, mode, x, y,
#            hit points (base stat 6 >> 8), lightning resist (base stat 41), monster flags (MonsterData +0x16) and
#            the non-zero mod bytes (MonsterData +0x1C). Base stats: unit +0x5C stat list, +0x24 array of
#            {u32 id << 16 | layer, s32 value} sorted, +0x28 s16 count (STATS_GetUnitBaseStat 0x006253B0 ->
#            0x00624ED0 -> 0x00624B90). Every 2 s the scan ("far": true) also lists, wherever they are, the act and
#            quest bosses (MonStats rows in BOSSES) and the units whose monster flags have 0x0E (unique, champion,
#            superunique). Also emitted, with the same rate limit, at PATH_SetMarkMask 0x00648C30 (every new
#            missile path, so the scan goes on while the player stands still and casts), around the last PLR position.
import base64
import json
import os
import struct
import time
import zlib

import gdb


def _pilot_main():
    inf = gdb.selected_inferior()
    st = {"game": 0, "t": 0.0}
    plr = {}
    G_LVLWARP = 0x0096CA00

    def mem(a, n):
        return bytes(inf.read_memory(a, n))

    def u16(a):
        return struct.unpack("<H", mem(a, 2))[0]

    def s16(a):
        return struct.unpack("<h", mem(a, 2))[0]

    def u32(a):
        return struct.unpack("<I", mem(a, 4))[0]

    def s32(a):
        return struct.unpack("<i", mem(a, 4))[0]

    def reg(n):
        return int(gdb.parse_and_eval("$" + n)) & 0xFFFFFFFF

    def thn():
        t = gdb.selected_thread()
        return t.num if t else 0

    def emit(tag, d):
        gdb.write("%s %s\n" % (tag, json.dumps(d, separators=(",", ":"))))

    def z(obj):
        return base64.b64encode(zlib.compress(json.dumps(obj, separators=(",", ":")).encode(), 6)).decode()

    def level_of(room):
        dr = u32(room + 0x10) if room else 0
        return s32(u32(dr + 0x58) + 0x1D0) if dr else None

    def warps(r):
        base = u32(G_LVLWARP)
        out, node, k = [], u32(r + 0x4C), 0
        while node and k < 16:
            rec = u32(node + 0x10)
            out.append([(rec - base) // 0x30 if rec else -1, s32(rec) if rec else None,
                        list(struct.unpack("<8i", mem(node, 32)))])
            node = u32(node + 4)
            k += 1
        return out

    def stat(u, sid):
        sl = u32(u + 0x5C)
        if not sl:
            return None
        arr, n = u32(sl + 0x24), s16(sl + 0x28)
        if not arr or n <= 0 or n > 512:
            return None
        b = mem(arr, 8 * n)
        key = sid << 16
        for i in range(n):
            k, v = struct.unpack_from("<Ii", b, 8 * i)
            if k == key:
                return v
        return None

    class Bp(gdb.Breakpoint):
        def __init__(self, addr, fn):
            super().__init__("*0x%08X" % addr, internal=True)
            self.silent = True
            self.fn = fn

        def stop(self):
            try:
                self.fn()
            except Exception as e:  # never stop the game on a logger error; log it instead
                gdb.write("LOGERR pilot %r\n" % (e,))
            return False

    def on_game():
        st["game"] = reg("edi")
        emit("GPTR", {"game": st["game"]})

    def on_rl():
        lv, r = reg("ecx"), reg("edx")
        x, y, w, h = struct.unpack("<iiii", mem(r + 0x34, 16))
        d = {"level": lv, "lid": s32(lv + 0x1D0), "room": r, "type": u32(r + 0x48), "rect": [x, y, w, h],
             "warps": warps(r)}
        if d["type"] == 2 and u32(r + 0x20):
            d["pdef"] = s32(u32(r + 0x20))
        emit(os.environ.get("PILOT_RL_TAG", "RL"), d)   # drlg-maze.gdb: "PRL", beside drlg-gen.py's RL

    def on_rreseed():
        r = reg("ecx")
        emit("RRESEED", {"room": r, "level": u32(u32(r + 0x58) + 0x1D0), "warps": warps(r)})

    def on_cb():
        room = u32(reg("ebp") - 0x10)
        m = u32(room + 0x20)
        cells = None
        if m:
            x0, y0, w, h = struct.unpack("<iiii", mem(m, 16))
            c = u32(m + 0x20)
            cells = [x0, y0, w, h, mem(c, 2 * w * h).hex() if c and 0 < w * h <= 1 << 20 else None]
        emit("CB", {"th": thn(), "room": room, "lid": level_of(room),
                    "rect": list(struct.unpack("<iiii", mem(room + 0x4C, 16))), "z": z({"cells": cells})})

    BOSSES = {156, 211, 229, 242, 243, 250, 256, 267, 526, 544}   # act bosses and quest bosses by MonStats row

    def mons(x, y, far=False):
        g = st["game"]
        out = []
        if not g:
            return out
        heads = struct.unpack("<128I", mem(g + 0x1320, 512))
        for u in heads:
            k = 0
            while u and k < 256:
                k += 1
                try:
                    p = u32(u + 0x2C)
                    if p:
                        mx, my = u16(p + 2), u16(p + 6)
                        md = u32(u + 0x14)
                        near = abs(mx - x) <= 48 and abs(my - y) <= 48
                        if far and not near:
                            near = s32(u + 4) in BOSSES or (md and mem(md + 0x16, 1)[0] & 0x0E)
                        if near:
                            hp = stat(u, 6)
                            out.append({"id": u32(u + 0xC), "cls": s32(u + 4), "mode": u32(u + 0x10), "x": mx, "y": my,
                                        "hp": hp >> 8 if hp is not None else None, "lr": stat(u, 41),
                                        "mf": mem(md + 0x16, 1)[0] if md else None,
                                        "mods": [b for b in mem(md + 0x1C, 9) if b] if md else []})
                except gdb.MemoryError:
                    pass
                u = u32(u + 0xE4)
        return out

    def on_plr():
        esp = reg("esp")
        room, x, y, _pat, mask = struct.unpack("<IiiII", mem(esp + 4, 20))
        if mask != 0x80:
            return
        t = thn()
        last = plr.get(t)
        now = time.time()
        moved = not (last and abs(last[0] - x) < 2 and abs(last[1] - y) < 2 and last[2] == room)
        if moved:
            plr[t] = (x, y, room)
            emit("PLR", {"th": t, "room": room, "lid": level_of(room), "x": x, "y": y})
        st["pos"] = (x, y)
        if now - st["t"] >= 0.3:
            st["t"] = now
            far = now - st.get("tf", 0) >= 2.0
            if far:
                st["tf"] = now
            emit("MON", {"x": x, "y": y, "far": far, "m": mons(x, y, far)})
        if moved:
            gdb.flush()

    def on_tick():
        # also scan while the player stands and casts: PATH_SetMarkMask runs for every new missile
        now = time.time()
        if "pos" in st and now - st["t"] >= 0.3:
            st["t"] = now
            x, y = st["pos"]
            far = now - st.get("tf", 0) >= 2.0
            if far:
                st["tf"] = now
            emit("MON", {"x": x, "y": y, "far": far, "m": mons(x, y, far)})
            gdb.flush()

    def on_wrp():
        r = reg("esi")
        emit("WRP", {"room": r, "lid": u32(u32(r + 0x58) + 0x1D0), "rect": list(struct.unpack("<iiii", mem(r + 0x34, 16))),
                     "dx": s32(reg("ebp") + 0xC), "dy": reg("ecx") - (1 << 32 if reg("ecx") & 0x80000000 else 0), "rec": (reg("edi") - u32(G_LVLWARP)) // 0x30})

    Bp(0x0052C312, on_game)
    Bp(0x0066E21F, on_wrp)
    Bp(0x0066B970, on_rl)
    Bp(0x0066EE40, on_rreseed)
    Bp(0x0064C9FF, on_cb)
    Bp(0x0064EA90, on_plr)
    Bp(0x00648C30, on_tick)
    gdb.write("PILOT logger armed\n")


_pilot_main()
