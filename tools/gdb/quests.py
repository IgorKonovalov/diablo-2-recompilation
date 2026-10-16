# gdb Python logger for plan 0032 Phase 2 (quest drops, quest rewards, special drops): the quest seed, every quest-bit
# write, the B6 quest-TC test of MONSTER_DropItems, the scripted drops (DropItemAtUnit) and the three NPC item
# services (imbue, socket, personalize), as read in docs/findings/items/0010-quest-drops.md. Sourced by
# tools/gdb/quests.gdb after tools/gdb/pilot.py, tools/gdb/uniques.py, tools/gdb/affixes.py, tools/gdb/vendors.py and
# tools/gdb/mon-pool.py; tools/gdb/tc-drops.gdb is sourced last. One line per event, "TAG {json}". Addresses refer to
# the pinned game.exe (image base 0x400000). Seeds are "low:high" hex; "qs" is the quest seed (Game+0x10F4 -> +0x18),
# "gs" the game seed (Game+0xD0). A unit is [type, class, id] (+0x00, +0x04, +0x0C). A quest word is the u16 at
# record->bits + 2*word (QUESTRECORD_SetState 0x0065C360: bit 16*word + bit, LSB first).
#
#   QI0   0x00545F21 QUESTS_InitGame before the game-seed step (EDI game): gs
#   QI1   0x00545F5F after RNG_SeedInit and QUESTRECORD_Alloc (EBX quest control, EAX game record): qs, gs, grec
#   QS    0x0065C360 QUESTRECORD_SetState entry (stdcall record, word, bit): ret, rec, word, bit, the word before
#   QC    0x0065C3A0 QUESTRECORD_ClearState entry: the same
#   QGS   0x005438B0 QUESTS_GetSeed entry (ECX game): ret, qs (before the caller's draw)
#   B60   0x005A6705 MONSTER_DropItems at the quest-TC test, only when TCQuestId (+0x9E) != 0 (EDI MonStats record,
#         EBX difficulty, [ebp-4] TC so far, [ebp+0xC] monster, [ebp+0x14] kill context): monster unit, TCQuestId,
#         TCQuestCP, TreasureClass4 of the difficulty, tc, ctx, killer (ctx+8) unit
#   B6O   0x005A6743 after sub_0058F0D0_MonsterOwner: owner unit (0 none)
#   B6E   0x005A674C after sub_0063A690_UnitHasExpState: result
#   B6F   0x005A677C after sub_00552F60_GameFindUnit (the exp-state caster): unit
#   B6P   0x005A679E after QUESTS_PlayerRecord (ESI resolved unit, EAX record): unit, rec, the record's word TCQuestId
#   B6G   0x005A67B4 / 0x005A67C9 / 0x005A67E4 after GetState(15 / 1 / TCQuestCP): k 15/1/cp, result
#   B6X   0x005A6817 the TC_DropByIndex call: tc (ECX), killer (EAX)
#   QDI   0x00559A30 sub_00559A30_DropItemAtUnit entry (ECX game, EDX source; stack quality, &ilvl, ...): ret, source
#         unit, code at source+0xB8, quality, qs, difficulty, expansion; from the forge wave (ret 0x005B6865 / 0x005B68F2)
#         also the forge data ([ebp-0x14]: active +3, waves +8, n +0x14)
#   QDX   0x00559CC2 / 0x00559CD7 its returns: item unit (EAX), item quality, ilvl, start seed (ItemData +0x10 .. ), qs
#   IMB0  0x0057A020 imbue (EBX item): item unit, quality, flags (ItemData+0x18), clvl source
#   IMBL  0x0057A0B3 after the clvl read: clvl (EAX)
#   IMB1  0x0057A0CB the ItemCreate call: record ([ebp-0xEC]) index +0x14, quality +0x30, ilvl +0x0C, flags +0x80, gs
#   IMBX  0x0057A0D0 its result: item unit, quality, ilvl, start seed, gs
#   LZ0   0x0057A38F socket (EBX copy, EAX quality, [ebp-0xF8] max sockets): item unit, quality, max
#   LZS   0x0057A3C4 before RNG_RangeB (EAX item seed pointer, [ebp-0xF8] bound): bound, item seed
#   LZR   0x0057A3D1 after it: draw (EAX), item seed
#   LZX   0x0057A3E2 ITEMS_SetSockets call: requested count; LZY 0x0057A3E7 after it: stat 194 (sockets), flags
#   FOP   0x005B5C10 sub_005B5C10_A4Q3_ForgeOperate entry (ECX {game, object, player}): the object's mode (+0x10), the
#         forge data of quest object 24 (game+0x10F4 list, next +0xF4; +0x18 data: state u16 +0, strikes +0xC), the
#         player's word 27
#   PZ    0x0057A62A personalize, after the flag 0x1000000 and sub_00628370_ItemSetPersonalName (EBX copy): flags,
#         name at ItemData+0x4A
import json
import struct

import gdb


def _quests_main():
    inf = gdb.selected_inferior()
    st = {"lzitem": 0, "imbitem": 0}

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

    def seed(a):
        return "%08x:%08x" % (u32(a), u32(a + 4))

    def unit(u):
        if not u:
            return 0
        return [u32(u), s32(u + 4), u32(u + 0xC)]

    def qs(game):
        qc = u32(game + 0x10F4) if game else 0
        return seed(qc + 0x18) if qc else None

    def code(a):
        v = u32(a)
        return mem(a, 4).decode("latin1") if v else 0

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
        """item unit, quality, ilvl, flags, start seed, class"""
        if not u:
            return 0
        d = u32(u + 0x14)
        return {"u": unit(u), "q": u32(d), "ilvl": u32(d + 0x2C) if d else None, "fl": "%08x" % u32(d + 0x18),
                "seed": "%08x" % u32(d + 0x10) if d else None}

    def word(rec, w):
        return u16(u32(rec) + 2 * w) if rec and u32(rec) else None

    class Bp(gdb.Breakpoint):
        def __init__(self, addr, fn):
            super().__init__("*0x%08X" % addr, internal=True)
            self.silent = True
            self.fn = fn

        def stop(self):
            try:
                self.fn()
            except Exception as e:  # never stop the game on a logger error; log it instead
                gdb.write("LOGERR quests %r\n" % (e,))
            return False

    def on_qi0():
        g = reg("edi")
        st["game"] = g
        emit("QI0", {"game": g, "gs": seed(g + 0xD0)})

    def on_qi1():
        g, qc = reg("edi"), reg("ebx")
        emit("QI1", {"game": g, "qs": seed(qc + 0x18), "gs": seed(g + 0xD0), "grec": reg("eax")})

    def on_qs(tag):
        def f():
            esp = reg("esp")
            rec, w, b = u32(esp + 4), u32(esp + 8), u32(esp + 12)
            emit(tag, {"ret": "%08x" % u32(esp), "rec": rec, "w": w, "b": b, "old": word(rec, w)})
        return f

    def on_qgs():
        emit("QGS", {"ret": "%08x" % u32(reg("esp")), "qs": qs(reg("ecx"))})

    def on_b60():
        rec, ebx, ebp = reg("edi"), reg("ebx"), reg("ebp")
        qid = u8(rec + 0x9E)
        if not qid:
            return
        st["b6"] = True
        ctx = u32(ebp + 0x14)
        k = u32(ctx + 8) if ctx else 0
        emit("B60", {"mon": unit(u32(ebp + 0xC)), "qid": qid, "cp": u8(rec + 0x9F), "diff": ebx,
                     "tc4": u16(rec + 0x8C + 8 * ebx), "tc": s32(ebp - 4), "ctx": ctx, "killer": unit(k)})

    def on_b6o():
        emit("B6O", {"owner": unit(reg("eax"))})

    def on_b6e():
        emit("B6E", {"exp": reg("eax")})

    def on_b6f():
        emit("B6F", {"caster": unit(reg("eax"))})

    def on_b6p():
        u, rec = reg("esi"), reg("eax")
        w = u8(reg("edi") + 0x9E)
        emit("B6P", {"unit": unit(u), "rec": rec, "word": word(rec, w)})

    def on_b6g(k):
        def f():
            emit("B6G", {"k": k, "r": reg("eax")})
        return f

    def on_b6x():
        if not st.pop("b6", False):
            return
        emit("B6X", {"tc": reg("ecx"), "killer": unit(reg("eax"))})

    def on_qdi():
        esp, g, src, ebp = reg("esp"), reg("ecx"), reg("edx"), reg("ebp")
        ret = u32(esp)
        d = {"ret": "%08x" % ret, "src": unit(src), "code": code(src + 0xB8), "q": u32(esp + 4), "qs": qs(g),
             "diff": u8(g + 0x6D), "exp": u32(g + 0x70)}
        if ret in (0x005B6865, 0x005B68F2):
            fd = u32(ebp - 0x14)
            d["forge"] = {"act": u8(fd + 3), "waves": s32(fd + 8), "n": s32(fd + 0x14)}
        st["qdi_game"] = g
        emit("QDI", d)

    def on_qdx():
        g = st.get("qdi_game", 0)
        emit("QDX", {"item": item(reg("eax")), "qs": qs(g) if g else None})

    def on_imb0():
        it = reg("ebx")
        st["imbitem"] = it
        emit("IMB0", {"item": item(it), "game": reg("edi")})

    def on_imbl():
        emit("IMBL", {"clvl": reg("eax")})

    def on_imb1():
        ebp, g = reg("ebp"), reg("edi")
        r = ebp - 0xEC
        emit("IMB1", {"index": u32(r + 0x14), "q": u32(r + 0x30), "ilvl": u32(r + 0x0C), "f80": "%08x" % u32(r + 0x80),
                      "gs": seed(g + 0xD0)})

    def on_imbx():
        g = reg("edi")
        emit("IMBX", {"item": item(reg("eax")), "gs": seed(g + 0xD0)})

    def on_lz0():
        it, ebp = reg("ebx"), reg("ebp")
        st["lzitem"] = it
        emit("LZ0", {"item": item(it), "q": reg("eax"), "max": s32(ebp - 0xF8)})

    def on_lzs():
        emit("LZS", {"bound": s32(reg("ebp") - 0xF8), "seed": seed(reg("eax")), "pseed": reg("eax")})
        st["lzseed"] = reg("eax")

    def on_lzr():
        p = st.get("lzseed")
        emit("LZR", {"r": reg("eax"), "seed": seed(p) if p else None})

    def on_lzx():
        emit("LZX", {"n": s32(reg("ebp") - 0xF8)})

    def on_lzy():
        it = st.get("lzitem")
        emit("LZY", {"sockets": stat(it, 194) if it else None, "item": item(it)})

    def quest_obj(g, qid):
        qc = u32(g + 0x10F4) if g else 0
        q = u32(qc) if qc else 0
        k = 0
        while q and k < 64:
            if u32(q) == qid:
                return q
            q = u32(q + 0xF4)
            k += 1
        return 0

    def on_fop():
        c = reg("ecx")
        g, obj, plr = u32(c), u32(c + 4), u32(c + 8)
        q = quest_obj(g, 24)
        fd = u32(q + 0x18) if q else 0
        pd = u32(plr + 0x14) if plr else 0
        rec = u32(pd + 0x10 + 4 * u8(g + 0x6D)) if pd else 0
        emit("FOP", {"mode": u32(obj + 0x10) if obj else None, "state": u16(fd) if fd else None,
                     "strikes": s32(fd + 0xC) if fd else None, "w27": word(rec, 27)})

    def on_pz():
        it = reg("ebx")
        d = u32(it + 0x14)
        emit("PZ", {"item": item(it), "name": mem(d + 0x4A, 16).split(b"\0")[0].decode("latin1") if d else None})

    Bp(0x00545F21, on_qi0)
    Bp(0x00545F5F, on_qi1)
    Bp(0x0065C360, on_qs("QS"))
    Bp(0x0065C3A0, on_qs("QC"))
    Bp(0x005438B0, on_qgs)
    Bp(0x005A6705, on_b60)
    Bp(0x005A6743, on_b6o)
    Bp(0x005A674C, on_b6e)
    Bp(0x005A677C, on_b6f)
    Bp(0x005A679E, on_b6p)
    Bp(0x005A67B4, on_b6g(15))
    Bp(0x005A67C9, on_b6g(1))
    Bp(0x005A67E4, on_b6g("cp"))
    Bp(0x005A6817, on_b6x)
    Bp(0x00559A30, on_qdi)
    Bp(0x00559CC2, on_qdx)
    Bp(0x00559CD7, on_qdx)
    Bp(0x0057A020, on_imb0)
    Bp(0x0057A0B3, on_imbl)
    Bp(0x0057A0CB, on_imb1)
    Bp(0x0057A0D0, on_imbx)
    Bp(0x0057A38F, on_lz0)
    Bp(0x0057A3C4, on_lzs)
    Bp(0x0057A3D1, on_lzr)
    Bp(0x0057A3E2, on_lzx)
    Bp(0x0057A3E7, on_lzy)
    Bp(0x0057A62A, on_pz)
    Bp(0x005B5C10, on_fop)
    gdb.write("QUESTS logger armed\n")


_quests_main()
