# gdb Python logger for plan 0038 batch H6e1 (quest-npc): the items NPC messages give (QUESTS_GiveItem), the three
# NPC item services' tests, the cursor item each service consumes, and the shared tail, as read in
# docs/findings/items/0010-quest-drops.md § 6 and the service branches of NPC_MenuAction (0x00579D60). Sourced by
# tools/gdb/quest-npc.gdb after tools/gdb/quests.py (IMB*/LZ*/PZ, QS/QC, QGS) and tools/gdb/questev.py (EV, ANL/ANY).
# One line per event, "TAG {json}". Addresses refer to the pinned game.exe (image base 0x400000). A unit is
# [type, class, id]; an item is {"u", "q" (ItemData +0x00), "ilvl" (+0x2C), "fl" (+0x18), "st" {70 quantity,
# 72 durability, 73 max durability, 194 sockets}, "mode" (unit +0x10)}; a quest record is the 41 u16 words of the
# player's record for the game's difficulty (PlayerData +0x10 + 4*difficulty, then +0x00: the bits).
#
#   QGV   0x005466B0 QUESTS_GiveItem entry (ECX game, EDX player; stack code, ilvl, quality, dropIfFull): ret, player,
#         code, ilvl, quality, drop, the player's clvl (base stat 12), difficulty, the record words
#   QGC   0x00546700 after ITEMS_CreateForStore (EAX the new item): the item
#   QGD   0x0054671F after the durability write (ESI the item): stats 72 and 73
#   QGX   its exits 0x0054676D (placed), 0x005467BD (dropped), 0x005467CE (no item): site, item
#   CAN   the three service tests ItemCanImbue 0x0062C590, ItemCanPersonalize 0x0062C6A0, ItemCanQuestSocket
#         0x0062C770: at entry the caller's return and the item (with its record's quest byte +0x12A, compactsave
#         +0x143, Nameable +0x145 and the unit's +0xC8 flags); one step {site: EAX} after every call inside the
#         function (the sites below); the line is written at the function's return with the result r
#   CIC   0x0055EEA0 sub_0055EEA0_CursorItemConsume entry (ECX game, EDX player, stack item): ret, player, the item,
#         the player's cursor item (inventory [unit +0x60] +0x20, as INV_GetCursorItem 0x0063C1E0 reads it)
#   CICR  its result (EAX) at the three service call sites' returns 0x0057A098 (imbue), 0x0057A369 (socket),
#         0x0057A573 (personalize)
#   RPA   0x005761C0 sub_005761C0_ItemRepairAll entry from a service (returns 0x0057A0FE, 0x0057A3F2, 0x0057A586;
#         EDX the item): ret, item; RPX at those returns: the same item again
#   IDA   0x0055FE00 sub_0055FE00_ItemIdentifyAttach entry from a service (returns 0x0057A108, 0x0057A3FC,
#         0x0057A590; EDX the item): ret, item, its children count; IDX at those returns: the item again
import json
import struct

import gdb


def _quest_npc_main():
    inf = gdb.selected_inferior()
    st = {"can": None, "rpa": 0, "ida": 0}

    def mem(a, n):
        return bytes(inf.read_memory(a, n))

    def u8(a):
        return mem(a, 1)[0]

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

    def emit(tag, d):
        gdb.write("%s %s\n" % (tag, json.dumps(d, separators=(",", ":"))))

    def unit(u):
        if not u:
            return 0
        return [u32(u), s32(u + 4), u32(u + 0xC)]

    def stats(u, ids):
        out = {}
        sl = u32(u + 0x5C)
        if not sl:
            return out
        arr, n = u32(sl + 0x24), s16(sl + 0x28)
        if not arr or n <= 0 or n > 512:
            return out
        b = mem(arr, 8 * n)
        for i in range(n):
            k, v = struct.unpack_from("<Ii", b, 8 * i)
            if k & 0xFFFF == 0 and (k >> 16) in ids:
                out[str(k >> 16)] = v
        return out

    def item(u):
        if not u:
            return 0
        try:
            if u32(u) != 4:
                return {"u": unit(u)}
            d = u32(u + 0x14)
            return {"u": unit(u), "q": u32(d) if d else None, "ilvl": u32(d + 0x2C) if d else None,
                    "fl": "%08x" % u32(d + 0x18) if d else None, "st": stats(u, (70, 72, 73, 194)),
                    "mode": u32(u + 0x10), "kids": kids(u)}
        except gdb.MemoryError:
            return {"u": None}

    def kids(u):
        """the items the item holds: its inventory (unit +0x60, magic 0x1020304) from the first item (+0x0C), each
        next one at ItemData +0x64 (0x0063B2C0, 0x0063DFA0, as 0x0062A270 walks it)"""
        try:
            inv = u32(u + 0x60)
            if not inv or u32(inv) != 0x1020304:
                return 0
            n, c = 0, u32(inv + 0xC)
            while c and n < 8:
                if u32(c) == 4:
                    n += 1
                d = u32(c + 0x14)
                c = u32(d + 0x64) if d else 0
            return n
        except gdb.MemoryError:
            return {"u": None}

    def code_of(a):
        v = u32(a)
        return struct.pack("<I", v).decode("latin1") if v else 0

    def record(plr, g):
        try:
            pd = u32(plr + 0x14) if plr else 0
            rec = u32(pd + 0x10 + 4 * u8(g + 0x6D)) if pd and g else 0
            bits = u32(rec) if rec else 0
            if not bits:
                return None
            return list(struct.unpack("<41H", mem(bits, 82)))
        except gdb.MemoryError:
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
                gdb.write("LOGERR quest-npc %r\n" % (e,))
            return False

    # ---- QUESTS_GiveItem
    def on_qgv():
        esp, g, plr = reg("esp"), reg("ecx"), reg("edx")
        clvl = stats(plr, (12,)).get("12") if plr else None
        emit("QGV", {"ret": "%08x" % u32(esp), "pl": unit(plr), "code": code_of(esp + 4), "ilvl": s32(esp + 8),
                     "q": s32(esp + 12), "drop": s32(esp + 16), "clvl": clvl, "diff": u8(g + 0x6D),
                     "rec": record(plr, g)})

    def on_qgc():
        emit("QGC", {"item": item(reg("eax"))})

    def on_qgd():
        it = reg("esi")
        emit("QGD", {"item": item(it)})

    def on_qgx(site):
        def f():
            it = reg("eax") if site != 0x005467CE else 0
            emit("QGX", {"site": "%08x" % site, "item": item(it)})
        return f

    # ---- the three service tests
    def on_can(fn):
        def f():
            esp = reg("esp")
            it = u32(esp + 4)
            d = {"fn": "%08x" % fn, "ret": "%08x" % u32(esp), "item": item(it), "c8": "%08x" % u32(it + 0xC8),
                 "steps": []}
            st["can"] = d
        return f

    def on_step(site, kind):
        def f():
            d = st["can"]
            if d is None:
                return
            eax = reg("eax")
            if kind == "rec":           # EAX the ItemsTxt record: quest +0x12A, compactsave +0x143, Nameable +0x145
                v = {"quest": u8(eax + 0x12A), "compact": u8(eax + 0x143), "nameable": u8(eax + 0x145)}
            elif kind == "code":
                v = struct.pack("<I", eax).decode("latin1")
            elif kind == "al":
                v = eax & 0xFF
            else:
                v = eax - (1 << 32) if eax & 0x80000000 else eax
            d["steps"].append(["%08x" % site, v])
        return f

    def on_canret(fn, r):
        def f():
            d = st["can"]
            if d is None or d["fn"] != "%08x" % fn:
                return
            d["r"] = reg("eax") & 0xFF if r is None else r
            d["at"] = "%08x" % int(gdb.parse_and_eval("$pc"))
            emit("CAN", d)
            st["can"] = None
        return f

    # ---- the cursor item each service consumes
    def on_cic():
        esp, plr = reg("esp"), reg("edx")
        inv = u32(plr + 0x60) if plr else 0
        cur = u32(inv + 0x20) if inv and u32(inv) == 0x1020304 else 0
        it = u32(esp + 4)
        emit("CIC", {"ret": "%08x" % u32(esp), "pl": unit(plr), "item": item(it), "cursor": item(cur),
                     "same": int(it == cur and it != 0)})

    def on_cicr(site):
        def f():
            emit("CICR", {"site": "%08x" % site, "r": reg("eax")})
        return f

    # ---- the shared tail
    SVC_RET = {0x0057A0FE: "imbue", 0x0057A3F2: "socket", 0x0057A586: "personalize"}
    IDA_RET = {0x0057A108: "imbue", 0x0057A3FC: "socket", 0x0057A590: "personalize"}

    def on_rpa():
        ret = u32(reg("esp"))
        if ret not in SVC_RET:
            return
        st["rpa"] = reg("edx")
        emit("RPA", {"ret": "%08x" % ret, "svc": SVC_RET[ret], "item": item(st["rpa"])})

    def on_rpx(site):
        def f():
            emit("RPX", {"site": "%08x" % site, "svc": SVC_RET[site], "item": item(st["rpa"])})
        return f

    def on_ida():
        ret = u32(reg("esp"))
        if ret not in IDA_RET:
            return
        st["ida"] = reg("edx")
        emit("IDA", {"ret": "%08x" % ret, "svc": IDA_RET[ret], "item": item(st["ida"])})

    def on_idx(site):
        def f():
            emit("IDX", {"site": "%08x" % site, "svc": IDA_RET[site], "item": item(st["ida"])})
        return f

    Bp(0x005466B0, on_qgv)
    Bp(0x00546700, on_qgc)
    Bp(0x0054671F, on_qgd)
    for s in (0x0054676D, 0x005467BD, 0x005467CE):
        Bp(s, on_qgx(s))
    # ItemCanImbue: GetType, ItemMagicStockable, ItemTypeThrowable, the record, ITEMS_GetCode, 0x0062A270 (holds
    # socketed items), ITEMS_CheckFlags 0x800, ITEMS_GetQuality
    Bp(0x0062C590, on_can(0x0062C590))
    for s, k in ((0x0062C5CA, "v"), (0x0062C5F7, "v"), (0x0062C613, "v"), (0x0062C61D, "rec"), (0x0062C62C, "code"),
                 (0x0062C63A, "v"), (0x0062C653, "v"), (0x0062C65D, "v")):
        Bp(s, on_step(s, k))
    Bp(0x0062C67B, on_canret(0x0062C590, 1))
    Bp(0x0062C686, on_canret(0x0062C590, 0))
    Bp(0x0062C68E, on_canret(0x0062C590, 0))
    # ItemCanPersonalize: GetType, ITEMS_GetBaseType x3, ITEMS_CheckFlags 0x100, ItemGetFlags, compactsave
    # (0x0062A2B0), the record (Nameable)
    Bp(0x0062C6A0, on_can(0x0062C6A0))
    for s, k in ((0x0062C6DA, "v"), (0x0062C6FF, "v"), (0x0062C70A, "v"), (0x0062C715, "v"), (0x0062C72F, "v"),
                 (0x0062C739, "v"), (0x0062C747, "v"), (0x0062C754, "rec")):
        Bp(s, on_step(s, k))
    Bp(0x0062C762, on_canret(0x0062C6A0, None))
    Bp(0x0062C766, on_canret(0x0062C6A0, 0))
    # ItemCanQuestSocket: GetType, the record, ITEMS_GetCode, 0x0062A270, ITEMS_CheckFlags 0x800, ItemMaxSockets
    # (AL), ITEMS_GetSockets (AL)
    Bp(0x0062C770, on_can(0x0062C770))
    for s, k in ((0x0062C7AA, "v"), (0x0062C7D2, "rec"), (0x0062C7E1, "code"), (0x0062C805, "v"), (0x0062C81E, "v"),
                 (0x0062C828, "al"), (0x0062C832, "al")):
        Bp(s, on_step(s, k))
    Bp(0x0062C83A, on_canret(0x0062C770, None))
    Bp(0x0062C83E, on_canret(0x0062C770, 0))
    Bp(0x0055EEA0, on_cic)
    for s in (0x0057A098, 0x0057A369, 0x0057A573):
        Bp(s, on_cicr(s))
    Bp(0x005761C0, on_rpa)
    for s in SVC_RET:
        Bp(s, on_rpx(s))
    Bp(0x0055FE00, on_ida)
    for s in IDA_RET:
        Bp(s, on_idx(s))
    gdb.write("QUEST-NPC logger armed\n")


_quest_npc_main()
