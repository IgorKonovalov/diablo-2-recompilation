# gdb Python logger for plan 0065 cases H2, H3 and B8 (backlog 2026-11-04 reverser plan-0060 cross-check
# contradictions; items/0017 H2, H3, B8; items/use F1f, D3, D5; items/inventory F6). Source it after tools/gdb/pilot.py
# and tools/gdb/inventory.py (UP0..UP1, USS, PKT, GDI, IPG: the potion use, the requests, the ground drops), as
# tools/gdb/sweep8-use.gdb does. Read-only (ADR-0003): nothing here writes game memory or registers (this file has no
# armed edit; inventory.py's arm file is never written by tools/sweep8_sessions.py). Addresses refer to the pinned
# game.exe (image base 0x400000). One line per event, "TAG {json}".
#
# H2, the blend of two potions (sub_005BE3F0_ItemUsePotion; ESI the user, EDI the Misc record, [ebp-8] the game):
#   URM   0x005BE480, after UNIT_FindStatListByState (0x006256B0, called at 0x005BE462 with the record's state, s16
#         +0x98): list ([ebp-4], 0 = none found), rem ([ebp-0x10] = the list's end 0x00626090 − frame, 0 without a
#         list), len ([ebp-0x14], 0x00627C20's return), state, the user's id, the frame
#   UBL   0x005BE6C1, before the `idiv`: num (EBX = old rate × rem + v), den (ECX = len + rem), list ([ebp-4]),
#         stat ([ebp-0xC]), slot ([ebp-0x1C], 0..2)
#   UFL   0x00580650 in sub_00580610_LifeRegenTick: the healthpot (100) list freed at the maximum (EBX list, ESI unit)
#   UFM   0x005807B7 in PLAYER_ManaRegenTick: the manapot (106) list freed (EBX list, EDI unit)
# H3, a potion to the hireling:
#   T26   0x00562453 in sub_00562390_PlayerUseBeltItem (request 0x26; ESI game, EDI the player, EBX the item): the
#         packet's flag ([ebp+0x18]), the player's type, the game's expansion word (game +0x70), the item
#   T26A  0x0056246C, T26B 0x00562478, T26C 0x00562484: ITEMS_UnitIsType (0x00629BB0) results for types 0x4C, 0x51,
#         0x50 (EAX); T26P 0x00562499: the pet lookup 0x00574EC0(…, 7) result (EAX: the hireling or 0)
#   T61   0x0054D230 sub_0054D230_MercGiveCursorItem entry (request 0x61): ECX, EDX and three stack words
#   T61A  0x0054D294, T61B 0x0054D2A4, T61C 0x0054D2B4: ITEMS_UnitIsType results for 0x4C, 0x51, 0x50 (EAX, ESI the item)
#   IU0   0x005BF240 sub_005BF240_ItemUse entry (ECX game, EDX user, [esp+4] the item): the user's type, class, id,
#         the item, the return address
# B8, a death with a belt:
#   CCR   0x0057F700 PLAYER_CorpseCreate entry (ECX game, EDX the player): the player's item list (id, class, page,
#         x, y, mode, ItemData +0x44 body), the frame
#   CCN   0x0057F72D, `cmp eax, 0xF` after 0x0063D5F0 (the corpse path's count): EAX (above 15: sub_0057F540_
#         CorpseOverflowDrop at 0x0057F735, else the slot loop)
#   CMB   0x0057F410 sub_0057F410_CorpseMoveBodyItem entry (EDI the player, ESI the item, [esp+4] the game): the item
#   BOV0  0x005608C0 sub_005608C0_BeltOverflow entry (ECX game, EDX the player, [esp+4] the new belt or 0): the return
#         address (0x0057F47F: the corpse's call at 0x0057F47A), the belt word, the player's item list
#   BOV1  its return (a breakpoint at each return address met): the player's item list after
# Ready line "USE8 logger armed". Checked by tools/sweep8_check.py h2 / h3 / b8.
import json
import struct

import gdb


def _use8_main():
    inf = gdb.selected_inferior()
    st = {"game": 0, "bov": {}, "bovret": set()}

    def mem(a, n):
        return bytes(inf.read_memory(a, n))

    def u8(a):
        return mem(a, 1)[0]

    def s16(a):
        return struct.unpack("<h", mem(a, 2))[0]

    def u32(a):
        return struct.unpack("<I", mem(a, 4))[0]

    def s32(a):
        return struct.unpack("<i", mem(a, 4))[0]

    def reg(n):
        return int(gdb.parse_and_eval("$" + n)) & 0xFFFFFFFF

    def sreg(n):
        v = reg(n)
        return v - (1 << 32) if v & 0x80000000 else v

    def th():
        t = gdb.selected_thread()
        return t.num if t else 0

    def emit(tag, d):
        gdb.write("%s %s\n" % (tag, json.dumps(d, separators=(",", ":"))))

    def frame(game=None):
        g = game or st["game"]
        try:
            return s32(g + 0xA8) if g else None
        except gdb.MemoryError:
            return None

    def unit(u):
        if not u:
            return None
        try:
            return {"u": u, "t": u32(u), "c": s32(u + 4), "id": u32(u + 0x0C), "mode": u32(u + 0x10)}
        except gdb.MemoryError:
            return {"u": u, "err": 1}

    def item(u):
        if not u:
            return None
        d = unit(u)
        try:
            idata = u32(u + 0x14)
            if idata:
                d.update(pg=u8(idata + 0x45), body=u8(idata + 0x44))
            p = u32(u + 0x2C)
            if p:
                d.update(x=s32(p + 0x0C), y=s32(p + 0x10))
        except gdb.MemoryError:
            d["err"] = 1
        return d

    def inv_list(player):
        out = []
        try:
            inv = u32(player + 0x60)
            it, k = (u32(inv + 0x0C) if inv else 0), 0
            while it and k < 200:
                k += 1
                d = item(it)
                out.append([d["id"], d["c"], d.get("pg"), d.get("x"), d.get("y"), d["mode"], d.get("body")])
                it = u32(u32(it + 0x14) + 0x64)
        except gdb.MemoryError:
            out.append("err")
        return out

    class Bp(gdb.Breakpoint):
        def __init__(self, addr, fn):
            super().__init__("*0x%08X" % addr, internal=True)
            self.silent = True
            self.fn = fn

        def stop(self):
            try:
                self.fn()
            except Exception as e:  # never stop the game on a logger error
                gdb.write("LOGERR use8 %r\n" % (e,))
            return False

    # ---- H2
    def on_urm():
        bp = reg("ebp")
        game = u32(bp - 8)
        st["game"] = game
        emit("URM", {"th": th(), "uid": u32(reg("esi") + 0x0C), "list": u32(bp - 4), "rem": s32(bp - 0x10),
                     "len": s32(bp - 0x14), "state": s16(reg("edi") + 0x98), "f": frame(game)})

    def on_ubl():
        bp = reg("ebp")
        emit("UBL", {"th": th(), "num": sreg("ebx"), "den": sreg("ecx"), "list": u32(bp - 4), "stat": s32(bp - 0x0C),
                     "slot": s32(bp - 0x1C), "f": frame()})

    def mk_free(tag, ureg):
        def on_free():
            u = reg(ureg)
            emit(tag, {"th": th(), "uid": u32(u + 0x0C), "list": reg("ebx"), "f": frame()})
        return on_free

    # ---- H3
    def on_t26():
        bp, g, p = reg("ebp"), reg("esi"), reg("edi")
        st["game"] = g
        emit("T26", {"th": th(), "flag": u32(bp + 0x18), "pt": u32(p), "pid": u32(p + 0x0C), "exp": u32(g + 0x70),
                     "item": item(reg("ebx")), "f": frame(g)})

    def mk_res(tag, ty, ireg):
        def on_res():
            emit(tag, {"th": th(), "type": ty, "r": reg("eax"), "iid": u32(reg(ireg) + 0x0C)})
        return on_res

    def on_t26p():
        emit("T26P", {"th": th(), "pet": unit(reg("eax"))})

    def on_t61():
        sp = reg("esp")
        emit("T61", {"th": th(), "ecx": reg("ecx"), "edx": reg("edx"), "a": [u32(sp + 4 * k) for k in (1, 2, 3)],
                     "f": frame()})

    def on_iu0():
        sp = reg("esp")
        emit("IU0", {"th": th(), "user": unit(reg("edx")), "item": item(u32(sp + 4)), "ret": u32(sp), "f": frame()})

    # ---- B8
    def on_ccr():
        g, p = reg("ecx"), reg("edx")
        st["game"] = g
        emit("CCR", {"th": th(), "pid": u32(p + 0x0C), "inv": inv_list(p), "f": frame(g)})

    def on_ccn():
        emit("CCN", {"th": th(), "n": reg("eax")})

    def on_cmb():
        emit("CMB", {"th": th(), "pid": u32(reg("edi") + 0x0C), "item": item(reg("esi")), "f": frame()})

    def on_bov0():
        sp = reg("esp")
        g, p, ret = reg("ecx"), reg("edx"), u32(sp)
        st["game"] = g
        st["bov"][th()] = p
        emit("BOV0", {"th": th(), "ret": ret, "pid": u32(p + 0x0C), "belt": u32(sp + 4), "inv": inv_list(p),
                      "f": frame(g)})
        if ret not in st["bovret"]:
            st["bovret"].add(ret)
            Bp(ret, on_bov1)

    def on_bov1():
        p = st["bov"].pop(th(), None)
        if p:
            emit("BOV1", {"th": th(), "pid": u32(p + 0x0C), "inv": inv_list(p), "f": frame()})

    for a, f in ((0x005BE480, on_urm), (0x005BE6C1, on_ubl), (0x00580650, mk_free("UFL", "esi")),
                 (0x005807B7, mk_free("UFM", "edi")),
                 (0x00562453, on_t26), (0x0056246C, mk_res("T26A", 0x4C, "ebx")), (0x00562478, mk_res("T26B", 0x51, "ebx")),
                 (0x00562484, mk_res("T26C", 0x50, "ebx")), (0x00562499, on_t26p),
                 (0x0054D230, on_t61), (0x0054D294, mk_res("T61A", 0x4C, "esi")), (0x0054D2A4, mk_res("T61B", 0x51, "esi")),
                 (0x0054D2B4, mk_res("T61C", 0x50, "esi")), (0x005BF240, on_iu0),
                 (0x0057F700, on_ccr), (0x0057F72D, on_ccn), (0x0057F410, on_cmb), (0x005608C0, on_bov0)):
        Bp(a, f)
    gdb.write("USE8 logger armed\n")


_use8_main()
