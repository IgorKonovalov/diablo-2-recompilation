# gdb Python logger for plan 0038 batch H6e2 (quest-items): the quest items, the quest chests and objects, the
# duplicate test, the item-move gate and object event 7, as read in docs/findings/items/0010-quest-drops.md § 5 and
# § 9. Sourced by tools/gdb/quest-items.gdb after tools/gdb/quests.py (whose QDI/QDX/QGS/QS/OOP lines it relies on)
# and before tools/gdb/tc-drops.gdb. One line per event, "TAG {json}". Addresses refer to the pinned game.exe (image
# base 0x400000). A unit is [type, class, id]; an item is {"u", "code", "q", "fl", "s356"}; a quest record is the 41
# u16 words of the player's record for the game's difficulty (PlayerData +0x10 + 4*difficulty, then +0x00: the bits).
#
#   QOW   0x0058450E OBJ_OperateDispatch at its OperateFn call (ESI object, EDI player, EBX game): object unit, class,
#         its mode (+0x10), the OperateFn slot (objects.txt row +0x1B3), the player's record words
#   QOE   0x005449E0 QUESTS_ObjectEvent entry (ECX game, EDX object; EBP still OBJ_EventDispatch's frame): object
#         unit, class, mode, ret [esp], the event index [ebp+8], OBJ_EventDispatch's return [ebp+4], the next return
#         [[ebp]+4]
#   QOT   the entries of the 16 event-7 targets of items/0010 § 9 (the target, its return address)
#   QGV   0x005466B0 QUESTS_GiveItem entry (ECX game, EDX player; stack code, ilvl, quality, dropIfFull): ret, player,
#         code, ilvl, quality, drop, the record words; QGX 0x0054676D / 0x005467BD / 0x005467CE its exits: item (EAX)
#   QDC   0x00585970 sub_00585970_DropItemCodeAt entry (ECX game, EDX source; stack code, quality): ret, source, code,
#         quality
#   OCD   0x00585B90 sub_00585B90_ObjectChestDrop entry (ECX operate context, EDX): ret, edx, the last QDX item read
#         again (its flags after the script's own flag writes)
#   PFI   0x00558110 sub_00558110_PlayerFindItemByCode entry (ECX game, EDX player, stack code): ret, player, code,
#         difficulty; PFX 0x00558123 / 0x005581EC / 0x005581F5 its exits: the item found (EAX) or 0
#   PSX   0x00558169 / 0x005581D2 PlayerFindItemByCode after its two stat-356 reads (EAX the value, EBX game): the
#         value, the difficulty it is compared with
#   IQG   0x0055CC90 sub_0055CC90_ItemQuestGate entry (ECX game, EDX player, stack item): ret, player, item, the
#         record words, difficulty; IQX at its four callers' return addresses (0x0055D016, 0x005631E3, 0x00563636,
#         0x00567309): the result (EAX)
#   IHD   0x0055CA40's three callers' return addresses (0x0055CD1A, 0x0055CEDD, 0x0055CF26): the result (EAX)
#   ORF   0x0059DC70 sub_0059DC70_A2Q6_OrificeOperate entry; OSP 0x0059DD80 sub_0059DD80_A2Q6_StaffPlaced entry
import json
import struct

import gdb


def _quest_items_main():
    inf = gdb.selected_inferior()
    st = {"last_item": 0}

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

    def stat(u, sid):
        sl = u32(u + 0x5C)
        if not sl:
            return None
        arr, n = u32(sl + 0x24), s16(sl + 0x28)
        if not arr or n <= 0 or n > 512:
            return None
        b = mem(arr, 8 * n)
        for i in range(n):
            k, v = struct.unpack_from("<Ii", b, 8 * i)
            if k == sid << 16:
                return v
        return None

    def item(u):
        if not u:
            return 0
        try:
            if u32(u) != 4:
                return {"u": unit(u)}
            d = u32(u + 0x14)
            # the item's code: ItemsTxt record of class +0x04 is not read here; ItemData has no code, so the code is
            # taken from the item's base record through the class id at the QDI/PFI/IQG caller (the "code" field of
            # those lines); the unit's class is enough to tell the bases apart
            return {"u": unit(u), "q": u32(d) if d else None, "fl": "%08x" % u32(d + 0x18) if d else None,
                    "s356": stat(u, 356), "mode": u32(u + 0x10)}
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
                gdb.write("LOGERR quest-items %r\n" % (e,))
            return False

    def on_qow():
        o, plr, g = reg("esi"), reg("edi"), reg("ebx")
        st["game"] = g
        emit("QOW", {"obj": unit(o), "cls": s32(o + 4) if o else None, "mode": u32(o + 0x10) if o else None,
                     "fn": u8(u32(reg("ebp") + 0x10) + 0x1B3), "pl": unit(plr), "rec": record(plr, g),
                     "diff": u8(g + 0x6D)})

    def on_qoe():
        esp, ebp, o = reg("esp"), reg("ebp"), reg("edx")
        emit("QOE", {"obj": unit(o), "cls": s32(o + 4) if o else None, "mode": u32(o + 0x10) if o else None,
                     "ret": "%08x" % u32(esp), "ev": u32(ebp + 8), "r1": "%08x" % u32(ebp + 4),
                     "r2": "%08x" % u32(u32(ebp) + 4)})

    def on_qot(fn):
        def f():
            emit("QOT", {"fn": "%08x" % fn, "ret": "%08x" % u32(reg("esp"))})
        return f

    def on_qgv():
        esp, g, plr = reg("esp"), reg("ecx"), reg("edx")
        emit("QGV", {"ret": "%08x" % u32(esp), "pl": unit(plr), "code": code_of(esp + 4), "ilvl": s32(esp + 8),
                     "q": s32(esp + 12), "drop": s32(esp + 16), "rec": record(plr, g), "diff": u8(g + 0x6D)})

    def on_qgx(site):
        def f():
            it = reg("eax") if site != 0x005467CE else 0
            emit("QGX", {"site": "%08x" % site, "item": item(it)})
        return f

    def on_qdc():
        esp = reg("esp")
        emit("QDC", {"ret": "%08x" % u32(esp), "src": unit(reg("edx")), "code": code_of(esp + 4),
                     "q": s32(esp + 8)})

    def on_qdx():
        st["last_item"] = reg("eax")

    def on_ocd():
        esp = reg("esp")
        emit("OCD", {"ret": "%08x" % u32(esp), "edx": reg("edx"), "last": item(st.get("last_item", 0))})

    def on_pfi():
        esp, g, plr = reg("esp"), reg("ecx"), reg("edx")
        emit("PFI", {"ret": "%08x" % u32(esp), "pl": unit(plr), "code": code_of(esp + 4), "diff": u8(g + 0x6D)})

    def on_pfx(site):
        def f():
            emit("PFX", {"site": "%08x" % site, "item": item(reg("eax"))})
        return f

    def on_psx(site):
        def f():
            emit("PSX", {"site": "%08x" % site, "s356": s32_of(reg("eax")), "diff": u8(reg("ebx") + 0x6D)})
        return f

    def s32_of(v):
        return v - (1 << 32) if v & 0x80000000 else v

    def on_iqg():
        esp, g, plr = reg("esp"), reg("ecx"), reg("edx")
        it = u32(esp + 4)
        emit("IQG", {"ret": "%08x" % u32(esp), "pl": unit(plr), "item": item(it), "rec": record(plr, g),
                     "diff": u8(g + 0x6D)})

    def on_res(tag, site):
        def f():
            emit(tag, {"site": "%08x" % site, "r": reg("eax")})
        return f

    def on_orf():
        c = reg("ecx")
        emit("ORF", {"ret": "%08x" % u32(reg("esp")), "pl": unit(u32(c + 8))})

    def on_osp():
        emit("OSP", {"ret": "%08x" % u32(reg("esp")), "pl": unit(reg("edx"))})

    Bp(0x0058450E, on_qow)
    Bp(0x005449E0, on_qoe)
    for fn in (0x00593290, 0x0059B710, 0x005B5750, 0x005942C0, 0x0058A730, 0x00588CA0, 0x00594630, 0x005BCAC0,
               0x005B85E0, 0x005956C0, 0x005B6710, 0x0058B940, 0x0058A500, 0x00589540, 0x0058C0E0):
        Bp(fn, on_qot(fn))
    Bp(0x005466B0, on_qgv)
    for s in (0x0054676D, 0x005467BD, 0x005467CE):
        Bp(s, on_qgx(s))
    Bp(0x00585970, on_qdc)
    Bp(0x00559CC2, on_qdx)
    Bp(0x00559CD7, on_qdx)
    Bp(0x00585B90, on_ocd)
    Bp(0x00558110, on_pfi)
    for s in (0x00558123, 0x005581EC, 0x005581F5):
        Bp(s, on_pfx(s))
    for s in (0x00558169, 0x005581D2):
        Bp(s, on_psx(s))
    Bp(0x0055CC90, on_iqg)
    for s in (0x0055D016, 0x005631E3, 0x00563636, 0x00567309):
        Bp(s, on_res("IQX", s))
    for s in (0x0055CD1A, 0x0055CEDD, 0x0055CF26):
        Bp(s, on_res("IHD", s))
    Bp(0x0059DC70, on_orf)
    Bp(0x0059DD80, on_osp)
    gdb.write("QUEST-ITEMS logger armed\n")


_quest_items_main()
