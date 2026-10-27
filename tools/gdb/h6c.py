# gdb Python logger for plan 0038 batch H6c (vendors): the lines tools/gdb/vendors.py does not write, for
# docs/findings/items/0009-vendors.md. Sourced by tools/gdb/h6c.gdb after vendors.py. One line per event,
# "TAG {json}". Addresses refer to the pinned game.exe (image base 0x400000); each is the instruction named, read with
# objdump. Items are dumped as {u unit, id +0x0C, c class +0x04, q ItemData +0x00 quality, fl +0x18 flags, fi +0x28
# file index, pg +0x45 page, x/y the item's path +0x0C/+0x10, st ItemData +0x10 start seed}.
#
#   TLL   sub_00537340_TownLevelLeave entry (ECX game, EDX player; old level, new level): ret, the two levels
#   LUN   sub_00536850_NpcStoreLevelUpNote entry (ECX game, EDX player; level): ret, the pushed value, stat 12
#   NIS   sub_00572C10_NpcInteractStart entry: ret, EBX, EAX, the two stack words
#   NIR   sub_00572F20_NpcInteractRemove entry (ECX game, EDX player; npc, &list): ret, the npc's class
#   ISET  0x00554120 (the unit's interaction set: unit, type, id): ret, the args, the unit's +0x64/+0x68/+0x6C before
#   ICLR  0x00554190 (the unit's interaction cleared: unit): ret, the unit's +0x64/+0x68/+0x6C before
#   HSL   HIRE_SendList 0x00576770 entry: ret, ECX, EDX;  HBR HIRE_BuildStock 0x00576070 entry: ret ([esp])
#   VPG   VENDOR_CreateStockItem 0x00576571 (after sub_0062E880_ItemStorePage): the item, the page (AL)
#   VPA   the InvPlaceItem calls 0x005765C8 (page 1 or the item's page) / 0x0057660B (page 2): k, the 8 stack words
#   VPR   their results 0x005765CD / 0x00576610: k, EAX
#   VPK   0x00576623 the park call (no room on any tab): the item
#   VOK   0x00576633 the item placed: the item (page, x, y after the placement)
#   INVB  at BSX 0x00578BD0 / 0x005794C7 / 0x0057911B: the record's stock inventory after the build, item list
#   INVT  at NPC_TradeOpen 0x00579430 entry: the record's stock inventory (trade) or the player's gamble inventory
#         there (gamble), item list
#   INVG  at 0x00578B24 (GAMBLE_BuildInv's return into sub_00578AE0_GambleEnsure) after a GAMBLE_BuildInv entry
#         (stack player, record): the player's gamble inventory there, item list
#   ICR   0x00557450 sub_00557450_ItemCreateByQuality entry (the IC0 address; [esp+4] the creation record): ret, the
#         record's +0x00, +0x08, +0x0C, +0x14, +0x18 (u32), +0x28 (u16), +0x2A (u16), +0x30, +0x80
#   NB0/NB1  NPC_BuyItem 0x00577830 entry (ECX game, EDX player; stack args) / its returns 0x005779A3, 0x00577F28:
#         EAX; with the NPC's stock and the player's gamble inventories (when the stack's npc id resolves)
#   SIS   sub_00576F50_StoreItemSold entry (ECX game, EDX npc; item, player, mode): the item, mode, gambler;
#         SISP 0x00576FD9 VENDOR_IsPermanent's result (AL); SISR 0x00576FE4 the stock removal call (0x005766D0);
#         SISG 0x00576FFF the gamble-inventory call (0x00576650)
#   CPY0/CPY1  sub_0055A2A0_ItemCopy from the buy (returns 0x005776EE, 0x00577C7F) and the sale (0x0057974C): the
#         source item (EDX) / the copy (EAX at the return address)
#   NS0/NS1  NPC_SellItem 0x00579510 entry / its returns 0x005795CF, 0x005799D6, 0x00579A3F, 0x00579A93
#   NSX   NPC_SellItem's store-copy decision, at the addresses and with the reasons of tools/gdb/economy.py's NSX
#         (plan 0043 Phase 2b), with the game seed
import json
import struct

import gdb


def _h6c_main():
    inf = gdb.selected_inferior()
    st = {"game": 0, "nb": None}
    # the trade and gamble classes of NPC_MenuAction (items/0009 § 3)
    STORE_CLASSES = {147, 148, 154, 177, 178, 199, 202, 252, 253, 254, 255, 257, 405, 511, 512, 513, 514}

    def mem(a, n):
        return bytes(inf.read_memory(a, n))

    def u8(a):
        return mem(a, 1)[0]

    def u16(a):
        return struct.unpack("<H", mem(a, 2))[0]

    def u32(a):
        return struct.unpack("<I", mem(a, 4))[0]

    def s32(a):
        return struct.unpack("<i", mem(a, 4))[0]

    def reg(n):
        return int(gdb.parse_and_eval("$" + n)) & 0xFFFFFFFF

    def sreg(n):
        v = reg(n)
        return v - (1 << 32) if v & 0x80000000 else v

    def arg(k):
        return u32(reg("esp") + 4 * k)

    def sd(p):
        return "%08x:%08x" % struct.unpack("<II", mem(p, 8))

    def emit(tag, d):
        gdb.write("%s %s\n" % (tag, json.dumps(d, separators=(",", ":"))))

    def item(u):
        if not u:
            return None
        try:
            d = {"u": u, "id": u32(u + 0xC), "c": s32(u + 4)}
            idata = u32(u + 0x14)
            if idata:
                d.update(q=u32(idata), fl=u32(idata + 0x18), fi=s32(idata + 0x28), pg=u8(idata + 0x45),
                         st=u32(idata + 0x10))
            p = u32(u + 0x2C)
            if p:
                d.update(x=s32(p + 0x0C), y=s32(p + 0x10))
            return d
        except gdb.MemoryError:
            return {"u": u, "err": 1}

    def inv_items(inv):
        out = []
        if not inv:
            return out
        try:
            it = u32(inv + 0x0C)
            k = 0
            while it and k < 512:
                k += 1
                d = item(it)
                out.append([d.get("id"), d.get("c"), d.get("pg"), d.get("x"), d.get("y"), d.get("q")])
                idata = u32(it + 0x14)
                it = u32(idata + 0x64) if idata else 0
        except gdb.MemoryError:
            out.append("err")
        return out

    def rec_of(game, cls):
        c = u32(game + 0x1D24)
        if not c:
            return None
        recs = u32(c + 4)
        for i in range(64):
            r = recs + 0x44 * i
            if u32(r) == cls:
                return r
        return None

    def ginv_of(rec, pid):
        n = u32(rec + 0x08)
        k = 0
        while n and k < 64:
            k += 1
            if u32(n + 4) == pid:
                return u32(n)
            n = u32(n + 8)
        return 0

    def stat12(u):                      # the unit's level from its stat list (+0x5C), the base stats array
        try:
            sl = u32(u + 0x5C)
            if not sl:
                return None
            base, n = u32(sl + 0x24), u16(sl + 0x28)
            for i in range(min(n, 512)):
                e = base + 8 * i
                if u16(e + 2) == 12 and u16(e) == 0:
                    return s32(e + 4)
        except gdb.MemoryError:
            pass
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
                gdb.write("LOGERR h6c %r\n" % (e,))
            return False

    def on_tll():
        st["game"] = reg("ecx")
        emit("TLL", {"ret": arg(0), "old": s32(reg("esp") + 4), "new": s32(reg("esp") + 8), "plr": reg("edx")})
        gdb.flush()

    def on_lun():
        st["game"] = reg("ecx")
        emit("LUN", {"ret": arg(0), "a1": s32(reg("esp") + 4), "plr": reg("edx"), "lvl": stat12(reg("edx"))})
        gdb.flush()

    def on_nis():
        emit("NIS", {"ret": arg(0), "eax": reg("eax"), "ebx": reg("ebx"), "a1": arg(1), "a2": arg(2)})

    def on_nir():
        npc = arg(1)
        emit("NIR", {"ret": arg(0), "plr": reg("edx"), "npc": npc, "cls": s32(npc + 4) if npc else None})

    def ustate(u):
        return [s32(u + 0x64), s32(u + 0x68), u8(u + 0x6C)] if u else None

    def on_iset():
        u = arg(1)
        emit("ISET", {"ret": arg(0), "unit": u, "type": s32(reg("esp") + 8), "id": s32(reg("esp") + 12),
                      "before": ustate(u)})

    def on_iclr():
        u = arg(1)
        emit("ICLR", {"ret": arg(0), "unit": u, "before": ustate(u)})

    def on_hsl():
        emit("HSL", {"ret": arg(0), "ecx": reg("ecx"), "edx": reg("edx")})

    def on_hbr():
        emit("HBR", {"ret": arg(0)})

    def on_vpg():
        emit("VPG", {"it": item(reg("esi")), "page": reg("eax") & 0xFF})

    def on_vpa(k):
        def f():
            emit("VPA", {"k": k, "a": [u32(reg("esp") + 4 * i) for i in range(8)]})
        return f

    def on_vpr(k):
        def f():
            emit("VPR", {"k": k, "v": sreg("eax")})
        return f

    def on_vpk():
        emit("VPK", {"it": item(reg("esi"))})

    def on_vok():
        emit("VOK", {"it": item(reg("esi"))})

    st["bsrec"] = None

    def on_bs0():
        st["bsrec"] = (reg("ecx"), arg(2) - 0x20)

    def on_invb():
        if st["bsrec"]:
            g, rec = st["bsrec"]
            emit("INVB", {"cls": s32(rec), "items": inv_items(u32(rec + 4))})

    def on_invt():
        g, plr, npc = reg("ecx"), reg("edx"), arg(1)
        st["game"] = g
        cls = s32(npc + 4)
        rec = rec_of(g, cls)
        if not rec:
            return
        gamble = s32(reg("esp") + 12)
        inv = ginv_of(rec, u32(plr + 0xC)) if gamble else u32(rec + 4)
        emit("INVT", {"cls": cls, "gamble": gamble, "items": inv_items(inv)})

    def on_gb0():
        st["gb"] = (u32(reg("esp") + 4), u32(reg("esp") + 8))

    def on_invg():
        if st.get("gb"):
            plr, rec = st.pop("gb")
            emit("INVG", {"cls": s32(rec), "items": inv_items(ginv_of(rec, u32(plr + 0xC)))})
            gdb.flush()

    def on_icr():
        r = arg(1)
        if not r:
            return
        emit("ICR", {"ret": arg(0), "src": u32(r), "g": u32(r + 8), "ilvl": s32(r + 0xC), "idx": s32(r + 0x14),
                     "k18": u32(r + 0x18), "w28": u16(r + 0x28), "w2a": u16(r + 0x2A), "q": s32(r + 0x30),
                     "f80": u32(r + 0x80)})

    def npc_by_id(g, nid):
        heads = struct.unpack("<128I", mem(g + 0x1320, 512))     # the monster lists, as vendors.py's NPC line
        for u in heads:
            k = 0
            while u and k < 256:
                k += 1
                if u32(u + 0xC) == nid and s32(u + 4) in STORE_CLASSES:
                    return u
                u = u32(u + 0xE4)
        return 0

    def inv_state(g, plr, npc):
        if not npc:
            return {}
        cls = s32(npc + 4)
        rec = rec_of(g, cls)
        if not rec:
            return {"cls": cls}
        return {"cls": cls, "stock": inv_items(u32(rec + 4)), "ginv": inv_items(ginv_of(rec, u32(plr + 0xC)))}

    def on_nb0():
        g, plr = reg("ecx"), reg("edx")
        st["game"] = g
        a = [u32(reg("esp") + 4 * i) for i in range(1, 7)]
        npc = 0
        try:                             # the first stack word is the NPC unit (run:2026-10-27-sweep-vendors, dev)
            if u32(a[0]) == 1 and s32(a[0] + 4) in STORE_CLASSES:
                npc = a[0]
        except gdb.MemoryError:
            pass
        for v in a[:2]:
            npc = npc or npc_by_id(g, v)
        st["nb"] = (g, plr, npc)
        d = {"a": a, "npc": npc}
        d.update(inv_state(g, plr, npc))
        emit("NB0", d)

    def on_nb1():
        if not st["nb"]:
            return
        g, plr, npc = st["nb"]
        st["nb"] = None
        d = {"eax": sreg("eax")}
        d.update(inv_state(g, plr, npc))
        emit("NB1", d)
        gdb.flush()

    def on_sis():
        g, npc = reg("ecx"), reg("edx")
        rec = rec_of(g, s32(npc + 4))
        emit("SIS", {"it": item(arg(1)), "plr": arg(2), "mode": s32(reg("esp") + 12), "cls": s32(npc + 4),
                     "gambler": u32(rec + 0xC) if rec else None})

    def on_sisp():
        emit("SISP", {"al": reg("eax") & 0xFF})

    def on_tag(tag):
        def f():
            emit(tag, {})
        return f

    CPY_RET = {0x005776EE: "buy", 0x00577C7F: "buy2", 0x0057974C: "sell"}

    def on_cpy0():
        ret = arg(0)
        if ret in CPY_RET:
            emit("CPY0", {"k": CPY_RET[ret], "src": item(reg("edx"))})

    def on_cpy1(a):
        def f():
            emit("CPY1", {"k": CPY_RET[a], "copy": item(reg("eax"))})
        return f

    def on_ns0():
        emit("NS0", {"ecx": reg("ecx"), "edx": reg("edx"), "a": [u32(reg("esp") + 4 * i) for i in range(1, 5)]})

    def on_ns1():
        emit("NS1", {"eax": sreg("eax")})
        gdb.flush()

    NSX_AT = {0x00579653: "quality 1 named Cracked", 0x0057966F: "flag 0x100", 0x00579681: "base type 7",
              0x005796A1: "flag 0x1000000", 0x005796C1: "flag 0x400000 (ethereal)", 0x005796DD: "0x0055F590",
              0x005796EF: "0x00575FA0 (unique carry1)", 0x00579714: "gamble view", 0x0057971B: "tests done",
              0x00579734: "permanent test", 0x0057974C: "after ItemCopy", 0x0057977E: "store page",
              0x005797CE: "placed (page 1 try)", 0x0057981C: "placed (page 2 try)", 0x00579784: "copy freed (page 0xFF)",
              0x0057987B: "copy freed (not placed)", 0x00579824: "copy freed (page 2 not placed)"}

    def nsx(a):
        def f():
            d = {"at": a, "why": NSX_AT[a], "gs": sd(st["game"] + 0xD0) if st["game"] else None}
            if a == 0x0057971B:
                d["ok"] = u32(reg("ebp") - 4)
            elif a == 0x00579734:
                d["al"] = reg("eax") & 0xFF
            elif a == 0x0057974C:
                d["copy"] = item(reg("eax"))
            elif a == 0x0057977E:
                d["page"] = reg("eax") & 0xFF
            elif a in (0x005797CE, 0x0057981C):
                d["v"] = sreg("eax")
            emit("NSX", d)
        return f

    Bp(0x00537340, on_tll)
    Bp(0x00536850, on_lun)
    Bp(0x00572C10, on_nis)
    Bp(0x00572F20, on_nir)
    Bp(0x00554120, on_iset)
    Bp(0x00554190, on_iclr)
    Bp(0x00576770, on_hsl)
    Bp(0x00576070, on_hbr)
    Bp(0x00576571, on_vpg)
    Bp(0x005765C8, on_vpa(1))
    Bp(0x0057660B, on_vpa(2))
    Bp(0x005765CD, on_vpr(1))
    Bp(0x00576610, on_vpr(2))
    Bp(0x00576623, on_vpk)
    Bp(0x00576633, on_vok)
    Bp(0x00576980, on_bs0)
    for a in (0x00578BD0, 0x005794C7, 0x0057911B):
        Bp(a, on_invb)
    Bp(0x00579430, on_invt)
    Bp(0x00578790, on_gb0)
    Bp(0x00578B24, on_invg)
    Bp(0x00557450, on_icr)
    Bp(0x00577830, on_nb0)
    for a in (0x005779A3, 0x00577F28):
        Bp(a, on_nb1)
    Bp(0x00576F50, on_sis)
    Bp(0x00576FD9, on_sisp)
    Bp(0x00576FE4, on_tag("SISR"))
    Bp(0x00576FFF, on_tag("SISG"))
    Bp(0x0055A2A0, on_cpy0)
    for a in CPY_RET:
        if a != 0x0057974C:             # the sale's copy is NSX "after ItemCopy" at the same address
            Bp(a, on_cpy1(a))
    Bp(0x00579510, on_ns0)
    for a in (0x005795CF, 0x005799D6, 0x00579A3F, 0x00579A93):
        Bp(a, on_ns1)
    for a in NSX_AT:
        Bp(a, nsx(a))
    gdb.write("H6C logger armed\n")


_h6c_main()
