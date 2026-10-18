# gdb Python logger for plan 0043 Phase 2 (the item economy): prices, repair, buy and sell, gold, hire and resurrect,
# death, Cain, the wear events, quantity and charges, the replenish ticks, and a read watchpoint on Charsi's store
# record (docs/findings/items/0011-economy.md). Sourced by tools/gdb/economy.gdb after tools/gdb/pilot.py and
# tools/gdb/vendors.py (the lines tools/d2pilot.py steers by). One line per event, "TAG {json}"; every line carries
# "fr" (server game +0xA8). An exit breakpoint sits on a function's ret instruction, where ESP equals the entry ESP,
# which pairs the two. Addresses refer to the pinned game.exe (image base 0x400000). Seeds are "low:high" hex.
#
# Every entry and exit line carries "sn": the game seed (game +0xD0), the server player's seed (unit +0x20), its gold
# (stat 14) and stash gold (stat 15), read from the player's full-stat cache. Items are dumped as
#   {u unit, c class, q quality, fl ItemData+0x18, fi +0x28, v version +0x30, aa automagic +0x36, pre [+0x38 x3],
#    suf [+0x3E x3], ear +0x48, lf list flags, own [[key, value]...] (+0x24), cache [[key, value]...] (+0x48),
#    ch [socketed child classes] (item +0x60 inventory, first +0x0C, next ItemData +0x64), sd item seed}
# with key = stat << 16 | param.
#
#   ECON    once per game: the data-table fields the checker cross-checks (items, affixes, skills shift/mask)
#   PR0/PR1 ITEMS_TradePriceCore 0x0062EFB0 (ECX player, EDX item; stack difficulty, quest record, npc class, mode)
#           / its returns: "k" a payload id; the payload (mode, difficulty, npc, the player's stats 12 and 87, the quest
#           record's 0x60 bytes, the item) is written only the first time it is seen ("p"); "ra" the return address;
#           PR1 "v" the result (EAX)
#   RC0/RC1 sub_0062FE60_RepairCost entry (stack: game, player, npc, difficulty, quest record, callback) / returns
#   NR0/NR1 sub_00578050_NpcRepair (ECX game, EDX player; npc id, item id, flags, ...) / returns: the player's
#           equipped and carried items' D/M/q/flags
#   IR0/IR1 sub_005761C0_ItemRepairAll (ECX game, EDX item; player) / returns; IB0/IB1 sub_0055F900_ItemRepairBroken
#   NB0/NB1 NPC_BuyItem 0x00577830, NS0/NS1 NPC_SellItem 0x00579510 (ECX game, EDX player; stack args) / returns
#   PG0/PG1 sub_00576D90_PayGold (EDX player; amount) / returns (EAX)
#   GG0/GG1 sub_0055B060_PlayerGiveGold (ECX game, EDX player; amount) / returns
#   UG0/UG1 sub_0053FF00_UnitAddGoldStat (ECX unit, EDX stat; delta) / returns, for the player
#   SG0/SG1 sub_00564D50_StashGoldMove / returns;  GP0/GP1 sub_0055C850_GoldPickup / return
#   MC0/MC1 MERC_ResurrectCost 0x006637B0 (stack: mercenary) / return;  MR0/MR1 MERC_Resurrect 0x00579C00 / return,
#           with the mercenary's seed
#   DG0/DG1 PLAYER_DeathGoldLoss 0x005357D0 (ESI player; game, killer) / returns: L, gold, stash, game +0x6A, killer
#           type/class and its owner, stat 175
#   DA0/DA1 sub_0055A090_DropGoldAmount (ECX game, EDX unit; amount, out, count) / return
#   GA0/GA1 the gold item amount at creation (0x00557AD9: ilvl = record +0x0C, the item seed; 0x00557AF6: the amount
#           EDI after the floor, the record's +0x54, the item seed)
#   GF0/GF1 sub_005589A0_DropGoldFind (EBX killer, EDI gold item): gold before; GFK 0x005589BE / GFO 0x005589D8 the
#           killer's and its owner's gold find (EAX); GF1 at 0x00558A08: gold after
#   GPL     sub_00559300_DropGoldPile 0x00559338: the level's monster level (EAX)
#   DL0/DL1 ITEMS_DurabilityLossRoll 0x00559E30 (ECX game, EDX seed owner; item) / returns: the owner's type, class
#           and seed, the game's expansion word +0x70, the item; after: the owner's seed, the item
#   CD0/CD1 COMBAT_DurabilityLoss 0x0057D3D0 (EAX attacker; game, defender) / returns: both units' type, class and
#           seed; CDS 0x0057D480: W (EBX) and the 7 slots' items (classes); CDU 0x0057D491 u (EAX) and the defender's
#           seed; CDW 0x0057D49C w (EAX) and the seed
#   IC0/IC1 sub_0056C310_ItemConsumeOne (ECX game, EDX player; item) / returns: the item
#   UA0/UA1 PLAYER_UseAmmo 0x0056C3F0 entry / returns: the player's seed
#   UC0/UC1 sub_0056BEC0_UseCharge entry / returns: the stat 204 entries of every item of the player
#   RP0/RP1 ITEMEVENT_Replenish 0x00562D30 (ECX game, EDX item) / return: the item
#   CI0/CI1 NPC_CainIdentify 0x00578460 (ECX game, EDX player; npc id) / returns: the unidentified items
#   SWW     a read watchpoint (4 bytes) on Charsi's (class 154) NpcStoreRec +0x24, set at the first price call or
#           trade open: pc, [esp], the EBP-chain return addresses; SWC the same on the record's +0x00 (the class
#           dword NPCSTORE_FindRec compares), the positive control, at most 40 lines
import base64
import hashlib
import json
import struct
import zlib

import gdb


def _economy_main():
    inf = gdb.selected_inferior()
    st = {"game": 0, "plr": 0, "plist": 0, "pk": {}, "pend": {}, "econ": False, "watch": None, "nw": 0}
    DT_PTR = 0x00744304

    def mem(a, n):
        return bytes(inf.read_memory(a, n))

    def u8(a):
        return mem(a, 1)[0]

    def s8(a):
        return struct.unpack("<b", mem(a, 1))[0]

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

    def sreg(n):
        v = reg(n)
        return v - (1 << 32) if v & 0x80000000 else v

    def arg(k):
        return u32(reg("esp") + 4 * k)

    def sarg(k):
        return s32(reg("esp") + 4 * k)

    def frame():
        g = st["game"]
        try:
            return u32(g + 0xA8) if g else None
        except gdb.MemoryError:
            return None

    def emit(tag, d):
        d["fr"] = frame()
        gdb.write("%s %s\n" % (tag, json.dumps(d, separators=(",", ":"))))

    def sd(a):
        try:
            return "%08x:%08x" % struct.unpack("<II", mem(a, 8)) if a else None
        except gdb.MemoryError:
            return None

    def entries(arr, n):
        if not arr or n <= 0 or n > 4096:
            return []
        return [[k, v] for k, v in struct.iter_unpack("<Ii", mem(arr, 8 * n))]

    def lists(u):
        lst = u32(u + 0x5C) if u else 0
        if not lst:
            return 0, [], []
        lf = u32(lst + 0x10)
        own = entries(u32(lst + 0x24), s16(lst + 0x28))
        cache = entries(u32(lst + 0x48), s16(lst + 0x4C)) if lf & 0x80000000 else []
        return lf, own, cache

    def stat(u, sid, param=0, base=False):
        lf, own, cache = lists(u)
        key = sid << 16 | param
        for k, v in (own if base or not lf & 0x80000000 else cache):
            if k == key:
                return v
        return 0

    def player():
        p = st["plr"]
        if p:
            try:
                if u32(p) == 0 and u32(p + 0x5C) == st["plist"] and st["plist"]:
                    return p
            except gdb.MemoryError:
                pass
        st["plr"], st["plist"] = 0, 0
        g = st["game"]
        if not g:
            return 0
        heads = struct.unpack("<128I", mem(g + 0x1120, 512))
        for h in heads:
            u, k = h, 0
            while u and k < 64:
                if u32(u) == 0:
                    st["plr"], st["plist"] = u, u32(u + 0x5C)
                    return u
                u = u32(u + 0xE4)
                k += 1
        return 0

    def snap():
        p = player()
        d = {"gs": sd(st["game"] + 0xD0) if st["game"] else None}
        if p:
            d.update(ps=sd(p + 0x20), g=stat(p, 14), sg=stat(p, 15), lv=stat(p, 12))
        return d

    def children(it):
        out = []
        inv = u32(it + 0x60)
        if inv and u32(inv) == 0x01020304:
            x, k = u32(inv + 0x0C), 0
            while x and k < 8:
                if u32(x) == 4:
                    out.append(s32(x + 4))
                idt = u32(x + 0x14)
                x = u32(idt + 0x64) if idt else 0
                k += 1
        return out

    def item(it, full=True):
        if not it:
            return None
        d = {"u": it, "t": u32(it), "c": s32(it + 4)}
        if d["t"] != 4:
            return d
        idt = u32(it + 0x14)
        if idt:
            d.update(q=u32(idt), fl=u32(idt + 0x18), fi=s32(idt + 0x28), v=u16(idt + 0x30), aa=u16(idt + 0x36),
                     pre=list(struct.unpack("<3H", mem(idt + 0x38, 6))), suf=list(struct.unpack("<3H", mem(idt + 0x3E, 6))),
                     ear=u8(idt + 0x48), pg=s8(idt + 0x69), bl=u8(idt + 0x44))
        lf, own, cache = lists(it)
        d.update(lf=lf, own=own, cache=cache, sd=sd(it + 0x20))
        if full:
            d["ch"] = children(it)
        return d

    def unit(u):
        if not u:
            return None
        try:
            d = {"u": u, "t": u32(u), "c": s32(u + 4), "s": sd(u + 0x20)}
        except gdb.MemoryError:
            return {"u": u}
        return d

    def inv_items(p):
        """The player's items: the inventory list (Inventory +0x0C, next ItemData +0x64)."""
        out = []
        inv = u32(p + 0x60) if p else 0
        if inv and u32(inv) == 0x01020304:
            x, k = u32(inv + 0x0C), 0
            while x and k < 200:
                if u32(x) == 4:
                    out.append(x)
                idt = u32(x + 0x14)
                x = u32(idt + 0x64) if idt else 0
                k += 1
        return out

    def wear_state(it):
        idt = u32(it + 0x14)
        return {"u": it, "c": s32(it + 4), "fl": u32(idt + 0x18) if idt else None, "d": stat(it, 72),
                "m": stat(it, 73), "m0": stat(it, 73, base=True), "n": stat(it, 70)}

    def ra_chain(n=4):
        out, bp = [], reg("ebp")
        for _ in range(n):
            try:
                out.append(u32(bp + 4))
                bp = u32(bp)
            except gdb.MemoryError:
                break
            if not bp:
                break
        return out

    class Bp(gdb.Breakpoint):
        def __init__(self, addr, fn):
            super().__init__("*0x%08X" % addr, internal=True)
            self.silent = True
            self.fn = fn

        def stop(self):
            try:
                self.fn()
            except Exception as e:  # never stop the game on a logger error; log it instead
                gdb.write("LOGERR economy %r\n" % (e,))
            return False

    def on_game():
        st["game"] = reg("edi")
        st["plr"], st["plist"], st["econ"] = 0, 0, False

    def econ():
        if st["econ"]:
            return
        st["econ"] = True
        dt = u32(DT_PTR)
        emit("ECON", {"items": s32(dt + 0xE28), "affixes": s32(0x0096CA7C), "isc": s32(dt + 0xBD4),
                      "skills": s32(dt + 0xBA0), "types": s32(dt + 0xBFC), "uniques": s32(dt + 0xC28),
                      "sets": s32(dt + 0xC1C), "shift": s32(dt + 0xC6C), "mask": s32(dt + 0xC70),
                      "npcs": s32(0x0096C5DC), "exp": u32(st["game"] + 0x70) if st["game"] else None,
                      "gtype": u8(st["game"] + 0x6A) if st["game"] else None})

    # ---------------------------------------------------------------- generic entry / exit pairs
    def pair(tag0, tag1, entry_addr, ret_addrs, f0, f1=None):
        def on0():
            d = f0() or {}
            d["ra"] = u32(reg("esp"))
            try:
                d["ra2"] = u32(reg("ebp") + 4)      # the caller's return address (its EBP frame), e.g. the price
            except gdb.MemoryError:                # wrapper's caller
                pass
            d["sn"] = snap()
            st["pend"][(tag0, reg("esp"))] = d.get("_ctx")
            d.pop("_ctx", None)
            emit(tag0, d)

        def on1():
            ctx = st["pend"].pop((tag0, reg("esp")), None)
            d = (f1(ctx) if f1 else {}) or {}
            d["v"] = sreg("eax")
            d["sn"] = snap()
            emit(tag1, d)

        Bp(entry_addr, on0)
        for a in ret_addrs:
            Bp(a, on1)

    # ---------------------------------------------------------------- prices
    def pr0():
        econ()
        if st["watch"] is None and st["game"]:
            set_watch()
        pl, it = reg("ecx"), reg("edx")
        diff, qrec, npc, mode = sarg(1), arg(2), sarg(3), sarg(4)
        qb = None
        if qrec:
            buf = u32(qrec)
            qb = mem(buf, 0x60).hex() if buf else None
        p = {"m": mode, "d": diff, "npc": npc, "plv": stat(pl, 12) if pl else None,
             "prp": stat(pl, 87) if pl else None, "pt": u32(pl) if pl else None, "qb": qb, "it": item(it)}
        key = hashlib.sha1(json.dumps(p, sort_keys=True).encode()).hexdigest()[:16]
        out = {"k": key}
        if key not in st["pk"]:
            st["pk"][key] = 1
            out["p"] = p
        return dict(out, _ctx=key)

    def pr1(ctx):
        return {"k": ctx}

    pair("PR0", "PR1", 0x0062EFB0, [0x0062EFFC, 0x0062F01F, 0x0062F09A, 0x0062F0BB, 0x0062FD45, 0x0062FD72,
                                    0x0062FD8B, 0x0062FD98], pr0, pr1)

    def rc0():
        return {"a": [arg(k) for k in range(1, 7)]}

    pair("RC0", "RC1", 0x0062FE60, [0x0062FE74, 0x0062FF62], rc0)

    def worn(p):
        return [wear_state(x) for x in inv_items(p)]

    def nr0():
        p = reg("edx")
        return {"a": [arg(k) for k in range(1, 5)], "its": worn(p), "_ctx": p}

    def nr1(p):
        return {"its": worn(p) if p else None}

    pair("NR0", "NR1", 0x00578050, [0x00578155, 0x00578421, 0x0057845A], nr0, nr1)

    def ir0():
        it = reg("edx")
        d = wear_state(it)
        d["ch204"] = [e for e in lists(it)[2] if e[0] >> 16 == 204]
        return {"it": d, "_ctx": it}

    def ir1(it):
        d = wear_state(it)
        d["ch204"] = [e for e in lists(it)[2] if e[0] >> 16 == 204]
        return {"it": d}

    pair("IR0", "IR1", 0x005761C0, [0x0057625F, 0x005762A3], ir0, ir1)
    pair("IB0", "IB1", 0x0055F900, [0x0055F9B2], ir0, ir1)

    def gen0():
        return {"r": [reg("ecx"), reg("edx")], "a": [arg(k) for k in range(1, 5)]}

    def nb0():
        d = gen0()
        d["npc"] = None
        return d

    pair("NB0", "NB1", 0x00577830, [0x005779A3, 0x00577F28], nb0)
    pair("NS0", "NS1", 0x00579510, [0x005795CF, 0x005799D6, 0x00579A3F, 0x00579A93], gen0)
    pair("PG0", "PG1", 0x00576D90, [0x00576DBD, 0x00576DDC, 0x00576E14, 0x00576E3A], gen0)
    pair("GG0", "GG1", 0x0055B060, [0x0055B0AA, 0x0055B0EB, 0x0055B0FF], gen0)
    pair("SG0", "SG1", 0x00564D50, [0x00564E3A, 0x00564E60, 0x00564EAF, 0x00564EC4, 0x00564EF4], gen0)
    pair("GP0", "GP1", 0x0055C850, [0x0055C994], gen0)

    def ug0():
        u = reg("ecx")
        if u != player():
            return {"np": 1, "_ctx": None}
        sid = reg("edx")
        return {"st": sid, "dv": sarg(1), "old": stat(u, sid), "cap": stat(u, 12) * 10000, "_ctx": (u, sid)}

    def ug1(ctx):
        if not ctx:
            return {"np": 1}
        return {"new": stat(ctx[0], ctx[1])}

    pair("UG0", "UG1", 0x0053FF00, [0x0053FF2D, 0x0053FF5B, 0x0053FF78, 0x0053FF8C], ug0, ug1)

    # ---------------------------------------------------------------- hire, resurrect, death, Cain
    def mc0():
        m = arg(1)
        return {"merc": unit(m), "mlv": stat(m, 12) if m else None}

    pair("MC0", "MC1", 0x006637B0, [0x006637DE], mc0)

    def mr0():
        return {"r": [reg("ecx"), reg("edx")], "a": [arg(1)]}

    pair("MR0", "MR1", 0x00579C00, [0x00579D5D], mr0)

    def dg0():
        p, game, killer = reg("esi"), arg(1), arg(2)
        k = unit(killer) if killer else None
        if killer and u32(killer) == 1:
            try:
                k["mf"] = u16(u32(killer + 0x14) + 0x16)
            except gdb.MemoryError:
                pass
        return {"p": p, "gt": u8(game + 0x6A) if game else None, "killer": k, "s175": stat(p, 175),
                "_ctx": p}

    def dg1(p):
        return {"s175": stat(p, 175) if p else None}

    pair("DG0", "DG1", 0x005357D0, [0x005359D0, 0x005359E4], dg0, dg1)

    def da0():
        return {"amt": arg(1), "max": sarg(3), "unit": unit(reg("edx"))}

    pair("DA0", "DA1", 0x0055A090, [0x0055A1F4], da0)

    def ci0():
        p = reg("edx")
        un = [x for x in inv_items(p) if not u32(u32(x + 0x14) + 0x18) & 0x10]
        return {"a": [arg(1)], "unid": len(un), "_ctx": p}

    def ci1(p):
        un = [x for x in inv_items(p) if not u32(u32(x + 0x14) + 0x18) & 0x10] if p else []
        return {"unid": len(un)}

    pair("CI0", "CI1", 0x00578460, [0x005784B9, 0x0057860A], ci0, ci1)

    # ---------------------------------------------------------------- gold amounts
    def ga0():
        it = u32(reg("esi"))
        rec = u32(reg("ebp") + 8)
        emit("GA0", {"it": it, "ilvl": s32(rec + 0x0C), "sd": sd(it + 0x20), "ra": u32(reg("ebp") + 4)})

    def ga1():
        it = u32(reg("esi"))
        rec = u32(reg("ebp") + 8)
        emit("GA1", {"it": it, "amt": sreg("edi"), "r54": s32(rec + 0x54), "sd": sd(it + 0x20)})

    Bp(0x00557AD9, ga0)
    Bp(0x00557AF6, ga1)

    def gf0():
        k, it = reg("ebx"), reg("edi")
        emit("GF0", {"k": unit(k), "it": it, "gold": stat(it, 14) if it else None})

    def gfk():
        emit("GFK", {"v": sreg("eax")})

    def gfo():
        emit("GFO", {"v": sreg("eax")})

    def gf1():
        it = reg("edi")
        emit("GF1", {"it": it, "gold": stat(it, 14) if it else None})

    Bp(0x005589A0, gf0)
    Bp(0x005589BE, gfk)
    Bp(0x005589D8, gfo)
    Bp(0x00558A08, gf1)

    def gpl():
        emit("GPL", {"mlv": sreg("eax"), "ra": u32(reg("ebp") + 4)})

    Bp(0x00559338, gpl)

    # ---------------------------------------------------------------- wear
    def dl0():
        g, o, it = reg("ecx"), reg("edx"), arg(1)
        d = {"o": unit(o), "exp": u32(g + 0x70), "it": item(it, full=False), "_ctx": (o, it)}
        d["it"].update(wear_state(it))
        return d

    def dl1(ctx):
        if not ctx:
            return {}
        o, it = ctx
        return {"o": unit(o), "it": wear_state(it)}

    pair("DL0", "DL1", 0x00559E30, [0x00559F45, 0x0055A04B, 0x0055A080], dl0, dl1)

    def cd0():
        a, d = reg("eax"), arg(2)
        return {"att": unit(a), "def": unit(d), "_ctx": (a, d)}

    def cd1(ctx):
        a, d = ctx if ctx else (0, 0)
        return {"att": unit(a), "def": unit(d)}

    pair("CD0", "CD1", 0x0057D3D0, [0x0057D4CA, 0x0057D4E3], cd0, cd1)

    def cds():
        bp = reg("ebp")
        slots = []
        for k in range(7):
            x = u32(bp - 0x20 + 4 * k)
            slots.append(s32(x + 4) if x else None)
        emit("CDS", {"w": sreg("ebx"), "slots": slots})

    def cdu(tag):
        def f():
            d = u32(reg("ebp") + 0xC)
            emit(tag, {"v": reg("eax"), "s": sd(d + 0x20)})
        return f

    Bp(0x0057D480, cds)
    Bp(0x0057D491, cdu("CDU"))
    Bp(0x0057D49C, cdu("CDW"))

    # ---------------------------------------------------------------- quantity, charges, replenish
    def ic0():
        it = arg(1)
        return {"it": wear_state(it) if it else None, "_ctx": it}

    def ic1(it):
        return {"it": wear_state(it) if it else None}

    pair("IC0", "IC1", 0x0056C310, [0x0056C3E0, 0x0056C3EB], ic0, ic1)
    pair("UA0", "UA1", 0x0056C3F0, [0x0056C48F, 0x0056C4D2], gen0)

    def charges():
        p = player()
        out = []
        for x in inv_items(p):
            es = [e for e in lists(x)[2] if e[0] >> 16 == 204]
            if es:
                out.append([x, s32(x + 4), es])
        return out

    def uc0():
        d = gen0()
        d["eax"] = reg("eax")
        d["ch"] = charges()
        return d

    def uc1(ctx):
        return {"ch": charges()}

    pair("UC0", "UC1", 0x0056BEC0, [0x0056BEE0, 0x0056BFCE, 0x0056BFD9], uc0, uc1)

    def rp0():
        it = reg("edx")
        d = wear_state(it)
        d.update(s252=stat(it, 252), s253=stat(it, 253), ms=stat(it, 254))
        return {"it": d, "_ctx": it}

    def rp1(it):
        return {"it": wear_state(it) if it else None}

    pair("RP0", "RP1", 0x00562D30, [0x00562D99], rp0, rp1)

    # ---------------------------------------------------------------- the store record watchpoint (question 9)
    class Watch(gdb.Breakpoint):
        def __init__(self, addr, tag="SWW", cap=2000):
            super().__init__("*(int*)0x%08X" % addr, gdb.BP_WATCHPOINT, gdb.WP_READ, internal=True)
            self.silent = True
            self.addr, self.tag, self.cap, self.n = addr, tag, cap, 0

        def stop(self):
            try:
                self.n += 1
                if self.n <= self.cap:
                    # the pc from the frame: "$eip" does not convert on this gdb (wow64), which cost the first
                    # sessions their watch lines (LOGERR "Cannot convert value to long", one per hit)
                    pc = int(gdb.selected_frame().pc()) & 0xFFFFFFFF
                    emit(self.tag, {"a": self.addr, "pc": pc, "esp0": u32(reg("esp")), "ras": ra_chain()})
            except Exception as e:
                gdb.write("LOGERR economy watch %s %r\n" % (self.tag, e))
            return False

    def set_watch():
        g = st["game"]
        c = u32(g + 0x1D24)
        if not c:
            return
        recs = u32(c + 4)
        for i in range(64):
            r = recs + 0x44 * i
            if u32(r) == 154:
                try:
                    Watch(r + 0x24)
                    Watch(r + 0x00, "SWC", 40)     # positive control: the class dword NPCSTORE_FindRec compares
                    st["watch"] = r
                    emit("SWSET", {"rec": r, "b": mem(r + 0x24, 4).hex()})
                except Exception as e:
                    st["watch"] = 0
                    emit("SWSET", {"rec": r, "err": repr(e)})
                return

    def on_to():
        if st["watch"] is None and st["game"]:
            set_watch()

    Bp(0x0052C312, on_game)
    Bp(0x00579430, on_to)


_economy_main()
