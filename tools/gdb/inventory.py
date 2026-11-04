# gdb Python logger for plan 0060 Phase 2 (items/0012..0014 harness cases). Sourced by tools/gdb/inventory.gdb after
# tools/gdb/pilot.py (the lines tools/d2pilot.py steers by). One line per event, "TAG {json}"; big payloads are
# zlib+base64 JSON under "z". Addresses refer to the pinned game.exe (image base 0x400000). Nothing here writes game
# memory except the two armed request edits named below (forced, built states; each logs an ARM line when it fires).
#
#   GDI   sub_00555DA0_GroundDropCell entry (ECX room, EDX position pointer; [esp] the caller, [esp+4] out pointer,
#         [esp+8], [esp+12] the size and fallback words): the position, the caller, the game frame, and in "z" the
#         window of collision cells (x-16..x+18, y-15..y+19 around the offset start) of the room and every room of its
#         near list and of their near lists (two hops), with each room's rect and near list (the inputs of
#         tools/item_inventory.py ground_drop_cell, written before the search returns)
#   GDO   0x00555DF5, the search's return: EAX the room, the out cell x, y
#   IPG   sub_00558AA0_ItemPlaceOnGround entry (ECX game, EDX flag, [esp+4] item, room, x, y): the item (id, class,
#         quality, base type via the record index), the frame
#   IPX   0x00558B2B, its end: the item's data +0x24, unit flags +0xC4, mode, path x, y
#   DCI   0x0055A6B4, DropCreateItem after ItemCreate (EAX the item): the item's data +0x24, quality, mode, x, y
#   SWP   sub_00558B90_ActExpiredItemsFree entry (ECX game, EDX act index): the frame and every type-4 unit of the
#         act's rooms: id, class, mode, +0x24, x, y
#   SWF   0x00558BEC, the sweep frees ESI: id, +0x24, frame
#   PKT   the item request handlers 0x16..0x25 and 0x61 (table g_SrvPacketTable) at entry: opcode, the packet's bytes,
#         the frame, the player's inventory list (id, page, x, y, mode); PKR the handler's return value EAX and the list
#   ARM   an armed request edit fired (see below)
#   SD    PKT, PKR, IPG, IPX and DCI carry "gs" (the game seed, game +0xD0); PKT and PKR also "sd" (the server player's
#         seed, unit +0x20, "lo:hi" hex), so a request's draws are the difference between the lines (revision 2)
#   UP0   sub_005BE3F0_ItemUsePotion entry (EDX user, ECX game, [esp+4] item): user type, class, id, the item, the frame,
#         the user's seed and stats 1, 3, 6, 7, 8, 9, 26, 74, 352 (the cache when the list's flag 0x80000000 is set)
#   UD1   0x005BE525, before draw #1 (ECX the seed address, EDX n): the seed, n
#   UD2   0x005BE53B, after draw #2 (EAX r2, EBX r1 >> 1, EDI the amount before the test): the seed after
#   UDV   0x005BE544, the amount after the test (EDI) and EBX (the slot's stat)
#   UAD   0x005BE5C2 the instant UnitAddStat (stack: user, stat, value, 0)
#   UAL   0x005BE602 the timed list's allocation, four stack words
#   UQE   0x005BE6AE the event queue call, four stack words
#   USS   0x005BE6CF the list's SetStat (stack: list, stat, rate, 0)
#   UP1   the entry's return (EAX), the seed and the same stats
#   RV1   0x005419F5 in sub_00541990_InactiveItemRestoreOne: EBX the record's saved word, ECX frame + 15000, the item (EAX),
#         the frame, ebp-0x28..ebp-0x4 raw, the item's +0x24 before the write
#   SV1   0x00541B71 in sub_00541B10_InactiveItemSave: ItemGroundExpiry has returned: EAX saved, the item (EDI), the frame
#   RM    room activity: 0x0061A910 (ActiveRoomFree), 0x0061A660 (RoomClientAdd) and 0x0061A700 (RoomClientRemove) at entry:
#         three stack words, the frame, and for a word that points to memory its +0x0C and +0x78 (a room's idle count
#         and client count)
#
# Armed edits (forced requests, ADR-0014 scope: the server's outcome to a request the client UI cannot make): the file
# workspace/runtime/inv-arm-slotN (N from env INV_SLOT) holds one line "18 page=4" or "23 box=K"; at the next request
# of that opcode the packet's page dword (+0x0D) or box dword (+0x05) is overwritten once and the file removed.
import base64
import json
import os
import struct
import zlib

import gdb

ITEM_OPS = {0x16: 0x0054AAD0, 0x17: 0x0054AB40, 0x18: 0x0054ABB0, 0x19: 0x0054ACD0, 0x1A: 0x0054AD90,
            0x1B: 0x0054AE30, 0x1C: 0x0054AEC0, 0x1D: 0x0054AF50, 0x1E: 0x0054B030, 0x1F: 0x0054B0F0,
            0x20: 0x0054B1E0, 0x21: 0x0054B300, 0x22: 0x0054B380, 0x23: 0x0054B3E0, 0x24: 0x0054B450,
            0x25: 0x0054B4E0, 0x26: 0x0054B560, 0x27: 0x0054B280}
WIN = (-32, 34, -31, 35)         # x0, x1, y0, y1 around the offset start (widened in revision 2: the walk of a wall case ran past +-16)


def _inventory_main():
    inf = gdb.selected_inferior()
    st = {"game": 0, "pend": {}}
    slot = os.environ.get("INV_SLOT", "2")
    arm_path = os.path.join(os.environ.get("INV_RUNTIME", "workspace/runtime"), "inv-arm-slot" + slot)

    def mem(a, n):
        return bytes(inf.read_memory(a, n))

    def u8(a):
        return mem(a, 1)[0]

    def u32(a):
        return struct.unpack("<I", mem(a, 4))[0]

    def s32(a):
        return struct.unpack("<i", mem(a, 4))[0]

    def reg(n):
        return int(gdb.parse_and_eval("$" + n)) & 0xFFFFFFFF

    def arg(k):
        return u32(reg("esp") + 4 * k)

    def emit(tag, d):
        gdb.write("%s %s\n" % (tag, json.dumps(d, separators=(",", ":"))))

    def z(obj):
        return base64.b64encode(zlib.compress(json.dumps(obj, separators=(",", ":")).encode(), 6)).decode()

    def sd(a):
        try:
            return "%08x:%08x" % struct.unpack("<II", mem(a, 8)) if a else None
        except gdb.MemoryError:
            return None

    def gseed():
        g = st["game"]
        return sd(g + 0xD0) if g else None

    def frame(game=None):
        g = game or st["game"]
        return s32(g + 0xA8) if g else None

    def item(u):
        if not u:
            return None
        d = {"u": u, "id": u32(u + 0xC), "c": s32(u + 4), "mode": u32(u + 0x10)}
        idata = u32(u + 0x14)
        if idata:
            d.update(q=u32(idata), e=s32(idata + 0x24), fl=u32(idata + 0x18), pg=u8(idata + 0x45))
        p = u32(u + 0x2C)
        if p:
            d.update(x=s32(p + 0x0C), y=s32(p + 0x10))
        return d

    def inv_list(player):
        out = []
        try:
            inv = u32(player + 0x60)
            it, k = u32(inv + 0x0C), 0
            while it and k < 200:
                k += 1
                d = item(it)
                out.append([d["id"], d["c"], d.get("pg"), d.get("x"), d.get("y"), d["mode"]])
                it = u32(u32(it + 0x14) + 0x64)
        except gdb.MemoryError:
            out.append("err")
        return out

    def near(room):
        n = s32(room + 0x24)
        p = u32(room)
        return list(struct.unpack("<%dI" % n, mem(p, 4 * n))) if (p and 0 < n < 64) else []

    def snap(room, sx, sy):
        hop1 = [room] + [n for n in near(room) if n != room]
        seen, hop2 = set(hop1), []
        for r in hop1[1:]:
            for n in near(r):
                if n not in seen:
                    seen.add(n)
                    hop2.append(n)
        out = []
        for k, r in enumerate(hop1 + hop2):
            x0, y0, w, h = struct.unpack("<iiii", mem(r + 0x4C, 16))
            m = u32(r + 0x20)
            c = u32(m + 0x20) if m else 0
            rows = None
            if c and w > 0 and h > 0 and w * h < 1 << 20:
                rows = []
                for y in range(max(y0, sy + WIN[2]), min(y0 + h, sy + WIN[3] + 1)):
                    xa, xb = max(x0, sx + WIN[0]), min(x0 + w, sx + WIN[1] + 1)
                    if xa < xb:
                        rows.append([y, xa, mem(c + 2 * ((y - y0) * w + (xa - x0)), 2 * (xb - xa)).hex()])
            out.append({"r": r, "hop": 0 if k == 0 else (1 if k < len(hop1) else 2), "rect": [x0, y0, w, h],
                        "near": near(r), "rows": rows, "nocells": rows is None})
        return out

    class Bp(gdb.Breakpoint):
        def __init__(self, addr, fn, temp=False):
            super().__init__("*0x%08X" % addr, internal=True, temporary=temp)
            self.silent = True
            self.fn = fn

        def stop(self):
            try:
                self.fn()
            except Exception as e:  # never stop the game on a logger error; log it instead
                gdb.write("LOGERR inventory %r\n" % (e,))
            return False

    def th():
        t = gdb.selected_thread()
        return t.num if t else 0

    # --- the ground drop's search ------------------------------------------------------------------------------
    def on_gdi():
        room, pos = reg("ecx"), reg("edx")
        x, y = s32(pos), s32(pos + 4)
        st["pend"][th()] = arg(1)
        emit("GDI", {"th": th(), "room": room, "x": x, "y": y, "ret": arg(0), "a1": arg(2), "a2": arg(3),
                     "f": frame(), "z": z(snap(room, x + 2, y + 3))})

    def on_gdo():
        out = u32(reg("ebp") + 8)
        emit("GDO", {"th": th(), "room": reg("eax"), "x": s32(out), "y": s32(out + 4)})

    Bp(0x00555DA0, on_gdi)
    Bp(0x00555DF5, on_gdo)

    # --- placement and creation ---------------------------------------------------------------------------------
    def on_ipg():
        st["game"] = reg("ecx")
        it = arg(1)
        emit("IPG", {"th": th(), "flag": reg("edx"), "item": item(it), "room": arg(2), "x": s32(reg("esp") + 12),
                     "y": s32(reg("esp") + 16), "f": frame(), "gs": gseed()})

    def on_ipx():
        emit("IPX", {"th": th(), "item": item(reg("esi")), "f": frame(), "gs": gseed()})

    def on_dci():
        emit("DCI", {"th": th(), "item": item(reg("eax")), "f": frame(), "gs": gseed()})

    Bp(0x00558AA0, on_ipg)
    Bp(0x00558B2B, on_ipx)
    Bp(0x0055A6B4, on_dci)

    # --- the sweep -------------------------------------------------------------------------------------------------
    def on_swf():
        u = reg("esi")
        emit("SWF", {"th": th(), "item": item(u), "f": frame()})

    # at 0x00558BB7 the call has returned: EAX the act's first room, [ebp-0x8] the frame; the act pointer was pushed
    def on_swp_after():
        game_frame = s32(reg("ebp") - 8)
        r = reg("eax")
        items, k, rk = [], 0, 0
        while r and rk < 4000:
            rk += 1
            u = u32(r + 0x74)
            while u and k < 4000:
                k += 1
                if u32(u) == 4:
                    d = item(u)
                    items.append([d["id"], d["c"], d["mode"], d.get("e"), d.get("x"), d.get("y")])
                u = u32(u + 0xE8)
            r = u32(r + 0x7C)
        emit("SWP", {"th": th(), "f": game_frame, "n": len(items), "items": items})

    Bp(0x00558BB7, on_swp_after)
    Bp(0x00558BEC, on_swf)

    # --- the item requests ----------------------------------------------------------------------------------------
    def armed(op):
        try:
            with open(arm_path) as f:
                line = f.read().strip()
        except OSError:
            return None
        parts = line.split()
        if len(parts) < 2 or int(parts[0], 16) != op:
            return None
        k, v = parts[1].split("=")
        os.remove(arm_path)
        return k, int(v)

    def mk_entry(op):
        def fn():
            game, player, pkt = reg("ecx"), reg("edx"), arg(1)
            st["game"] = game
            a = armed(op)
            if a:
                off = 0x0D if a[0] == "page" else 0x05
                before = u32(pkt + off)
                inf.write_memory(pkt + off, struct.pack("<I", a[1]))
                emit("ARM", {"op": op, "field": a[0], "was": before, "now": a[1]})
            ret = u32(reg("esp"))
            emit("PKT", {"th": th(), "op": op, "pkt": mem(pkt, 17).hex(), "f": frame(game), "ret": ret,
                         "inv": inv_list(player), "plr": player,
                         "sd": sd(player + 0x20), "gs": gseed()})
            st["pend"][("r", th())] = (op, player)
            Bp(ret, on_ret, temp=True)
        return fn

    def on_ret():
        op, player = st["pend"].pop(("r", th()), (None, None))
        if op is None:
            return
        emit("PKR", {"th": th(), "op": op, "eax": reg("eax"), "f": frame(), "inv": inv_list(player) if player else None,
                     "sd": sd(player + 0x20) if player else None, "gs": gseed()})

    for op, addr in ITEM_OPS.items():
        Bp(addr, mk_entry(op))


    # --- the potion's use, the restore, the save and room activity (revision 2) -----------------------------------
    def s16(a):
        return struct.unpack("<h", mem(a, 2))[0]

    def sg(v):
        return v - (1 << 32) if v >= 1 << 31 else v

    def entries(arr, n):
        if not arr or n <= 0 or n > 4096:
            return []
        return [[k, v] for k, v in struct.iter_unpack("<Ii", mem(arr, 8 * n))]

    def stat(u, sid):
        lst = u32(u + 0x5C) if u else 0
        if not lst:
            return None
        cache = bool(u32(lst + 0x10) & 0x80000000)
        arr = entries(u32(lst + 0x48), s16(lst + 0x4C)) if cache else entries(u32(lst + 0x24), s16(lst + 0x28))
        for k, v in arr:
            if k == sid << 16:
                return v
        return 0

    def stats(u):
        return {str(i): stat(u, i) for i in (1, 3, 6, 7, 8, 9, 26, 74, 352)}

    def on_up0():
        user, game, it = reg("edx"), reg("ecx"), arg(1)
        st["game"] = game
        st["use"] = user
        ret = u32(reg("esp"))
        emit("UP0", {"th": th(), "user": user, "ut": u32(user), "ucls": s32(user + 4), "uid": u32(user + 0xC),
                     "item": item(it), "f": frame(game), "sd": sd(user + 0x20), "gs": gseed(), "stats": stats(user)})
        st["usepend"] = th()
        if ret not in st.setdefault("upret", set()):    # one persistent breakpoint per return site
            st["upret"].add(ret)
            Bp(ret, on_up1)

    def on_up1():
        if st.get("usepend") != th():
            return
        st["usepend"] = None
        user = st.get("use", 0)
        emit("UP1", {"th": th(), "eax": reg("eax"), "f": frame(), "sd": sd(user + 0x20) if user else None,
                     "gs": gseed(), "stats": stats(user) if user else None})

    def on_ud1():
        emit("UD1", {"sd": sd(reg("ecx")), "n": sg(reg("edx")), "f": frame()})

    def on_ud2():
        emit("UD2", {"r2": sg(reg("eax")), "h": sg(reg("ebx")), "v": sg(reg("edi")), "sd": sd(reg("esi") + 0x20)})

    def on_udv():
        emit("UDV", {"v": sg(reg("edi")), "stat": sg(reg("ebx"))})

    def on_uad():
        sp = reg("esp")
        emit("UAD", {"user": u32(sp), "stat": s32(sp + 4), "v": s32(sp + 8), "f": frame()})

    def on_ual():
        sp = reg("esp")
        emit("UAL", {"a": [s32(sp + 4 * k) for k in range(4)], "f": frame()})

    def on_uqe():
        sp = reg("esp")
        emit("UQE", {"a": [s32(sp + 4 * k) for k in range(4)], "f": frame()})

    def on_uss():
        sp = reg("esp")
        emit("USS", {"list": u32(sp), "stat": s32(sp + 4), "rate": s32(sp + 8), "f": frame()})

    Bp(0x005BE3F0, on_up0)
    Bp(0x005BE525, on_ud1)
    Bp(0x005BE53B, on_ud2)
    Bp(0x005BE544, on_udv)
    Bp(0x005BE5C2, on_uad)
    Bp(0x005BE602, on_ual)
    Bp(0x005BE6AE, on_uqe)
    Bp(0x005BE6CF, on_uss)

    def on_rv1():
        bp = reg("ebp")
        game = u32(bp + 8)
        it = reg("eax")
        emit("RV1", {"saved": sg(reg("ebx")), "lim": sg(reg("ecx")), "game": game, "f": frame(game), "item": item(it),
                     "loc": mem(bp - 0x28, 0x24).hex()})

    def on_sv1():
        game, itm = reg("ebx"), reg("edi")
        emit("SV1", {"game": game, "f": frame(game), "saved": sg(reg("eax")), "item": item(itm)})

    Bp(0x005419F5, on_rv1)
    Bp(0x00541B71, on_sv1)

    def mk_rm(fn):
        def f():
            sp = reg("esp")
            words = [u32(sp + 4 * k) for k in range(1, 4)]
            d = {"fn": fn, "w": words, "f": frame(), "o": {}}
            for w in words:
                if w > 0x10000:
                    try:
                        d["o"][str(w)] = [s32(w + 0x0C), s32(w + 0x78)]
                    except gdb.MemoryError:
                        pass
            emit("RM", d)
        return f

    Bp(0x0061A910, mk_rm("ActiveRoomFree"))
    Bp(0x0061A660, mk_rm("RoomClientAdd"))
    Bp(0x0061A700, mk_rm("RoomClientRemove"))

    emit("INVRDY", {"slot": slot, "arm": arm_path})


_inventory_main()
