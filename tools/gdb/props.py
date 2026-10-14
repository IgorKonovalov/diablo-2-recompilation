# gdb Python logger for plan 0024 Phase 2 (base stats, the property roll, ethereal and sockets):
# docs/findings/items/0006-properties.md. Sourced by tools/gdb/props.gdb after tools/gdb/uniques.py and before
# tools/gdb/tc-drops.gdb, whose lines it leaves unchanged. One line per event, "TAG {json}" (tools/tc.py and
# tools/quality.py skip JSON lines). Addresses refer to the pinned game.exe (image base 0x400000). Seeds are
# "low:high" hex. "it" = the item unit. Every line carries "th" (the gdb thread number).
#
#   IIS0  0x00557AB0 sub_00557AB0_ItemInitStats entry (EDX = &item, [esp+4] rec, [esp+8] doQuality): class, unit seed
#         (Unit+0x20), item seed (ItemData+0x04), start seed (+0x10), ilvl (+0x2C), version (+0x30), item quality
#         (+0x00), rec ilvl (+0x0C) and quantity (+0x54)
#   IIS1  0x00557E21 after the picture draw (ESI = &item): unit seed, item seed, picture (ItemData+0x49), the base
#         entries of the unit's stat list (see LISTS)
#   APE   0x0065FEC0 sub_0065FEC0_ItemApplyProps entry, while an ItemCreateByQuality call is open on the thread:
#         mode, a2, row pointer, return address, item seed, quality, file index, ilvl, version, item flags,
#         for mode 0 the affix id ((row - base) / 0x90 + 1, base at g_MagicAffixInfo+4 0x0096CA80) and the three
#         blocks at row+0x24, for mode 1 the two blocks at row+0x0C; then LISTS
#   SLOT  0x0065FDF5 PROP_ApplyBlock, the handler call: slot k (ESI), the properties row (EDI - DataTables+0xA4) / 0x2E,
#         func, set, stat, val, prev (EBX), the block {code, par, min, max}, state and flags, item seed;
#         for func 11 and 19 also the skill row's reqlevel (s16 +0x174) and maxlvl (s16 +0x12C)
#   SLOTR 0x0065FDF7 after the handler: return value (EAX), item seed
#   ROLL  0x0065E9E0 PROP_RollValue entry (EDX min, [esp+4] max), item seed; ROLLR at its three returns
#         (0x0065E9F3, 0x0065EA24, 0x0065EA3F): EAX, item seed
#   WR    0x0065EA50 PROP_WriteStat entry (EDX flags; stack a2, block, set, stat, param, value, state)
#   EVD   the evaluated max durability read by func 13 (0x0065FCF4, EAX) and by the ethereal roll (0x00556D68, EAX)
#   APX   the returns of ItemApplyProps (0x0065FF4C, 0x0065FFA9, 0x0066002F, 0x00660081): item seed, then LISTS
#   ETH0  0x00556CA0 sub_00556CA0_ItemRollEthereal entry (EBX rec, ESI item): rec +0x80, +0x44, item seed
#   ETHR  0x00556D0C after its RNG_Range: r (EAX), item seed
#   ETHX  0x00556D74 its return: item flags (ItemData+0x18), item seed
#   SOK0  0x00556B60 sub_00556B60_ItemRollSockets entry (EDI item, EBX rec): rec +0x80, +0x44, quality, item seed
#   SOKM  0x00556BA3 ItemMaxSockets (AL); SOKR 0x00556C14 after its RNG_Range: r (EAX), item seed
#   SSET  0x0062BCB0 ITEMS_SetSockets entry ([esp+8] count): count, start seed; SOKX at the returns 0x00556C63,
#         0x00556C91: item seed
#   PDT   once, at the first APE: DataTables (*0x00744304) +0xC6C and +0xC70 (the charged-skill packing words)
#   LX    the ItemCreateByQuality returns 0x00557A1C / 0x00557A27 / 0x00557482: item seed, quality, file index,
#         item flags, picture, then LISTS
# LISTS = "b": the base entries of the unit's stat list (Unit+0x5C, array +0x24, s16 count +0x28; entry
#         {u32 stat << 16 | param, s32 value}) as [stat, param, value]; "sub": every list chained from it (+0x3C,
#         then +0x40; next +0x2C) as [state (+0x14), flags (+0x10), entries].
import json
import struct

import gdb


def _props_main():
    inf = gdb.selected_inferior()
    ic = {}        # thread -> (item, rec) while an ItemCreateByQuality call is open
    iis = {}       # thread -> item while an ItemInitStats call is open
    ap = {}        # thread -> depth of ItemApplyProps
    once = {"pdt": False}
    DT_PTR = 0x00744304

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

    def sreg(n):
        v = reg(n)
        return v - (1 << 32) if v & 0x80000000 else v

    def thn():
        t = gdb.selected_thread()
        return t.num if t else 0

    def emit(tag, d):
        d["th"] = thn()
        gdb.write("%s %s\n" % (tag, json.dumps(d, separators=(",", ":"))))

    def sd(p):
        return "%08x:%08x" % struct.unpack("<II", mem(p, 8))

    def idata(it):
        return u32(it + 0x14)

    def iseed(it):
        return sd(idata(it) + 4)

    def entries(lst):
        arr, n = u32(lst + 0x24), s16(lst + 0x28)
        if not arr or n <= 0 or n > 1024:
            return []
        return [[k >> 16, k & 0xFFFF, v] for k, v in struct.iter_unpack("<Ii", mem(arr, 8 * n))]

    def lists(it):
        lst = u32(it + 0x5C)
        if not lst:
            return {"b": None, "sub": []}
        sub = []
        if u32(lst + 0x10) & 0x80000000:
            for head in (0x3C, 0x40):
                node, guard = u32(lst + head), 0
                while node and guard < 64:
                    sub.append([u32(node + 0x14), u32(node + 0x10), entries(node)])
                    node, guard = u32(node + 0x2C), guard + 1
        return {"b": entries(lst), "sub": sub}

    def blocks(p, n):
        return [list(struct.unpack("<iiii", mem(p + 16 * i, 16))) for i in range(n)]

    def cur():
        return ic.get(thn())

    def in_ap():
        return cur() is not None and ap.get(thn(), 0) > 0

    class Bp(gdb.Breakpoint):
        def __init__(self, addr, fn):
            super().__init__("*0x%08X" % addr, internal=True)
            self.silent = True
            self.fn = fn

        def stop(self):
            try:
                self.fn()
            except Exception as e:  # never stop the game on a logger error; log it instead
                gdb.write("LOGERR props %r\n" % (e,))
            return False

    def on_ic0():
        ic[thn()] = (u32(reg("edx")), u32(reg("esp") + 4))
        ap[thn()] = 0

    def on_icx():
        c = ic.pop(thn(), None)
        if not c:
            return
        it = c[0]
        d = idata(it)
        out = {"seed": sd(d + 4), "q": u32(d), "fi": s32(d + 0x28), "fl": u32(d + 0x18), "gfx": u8(d + 0x49)}
        out.update(lists(it))
        emit("LX", out)

    def on_iis0():
        it, rec = u32(reg("edx")), u32(reg("esp") + 4)
        iis[thn()] = it
        d = idata(it)
        emit("IIS0", {"it": it, "cls": s32(it + 4), "useed": sd(it + 0x20), "iseed": sd(d + 4),
                      "start": u32(d + 0x10), "ilvl": s32(d + 0x2C), "ver": u16(d + 0x30), "q": u32(d),
                      "rec": rec, "rilvl": s32(rec + 0xC) if rec else None, "rqty": s32(rec + 0x54) if rec else None,
                      "doq": u32(reg("esp") + 8)})

    def on_iis1():
        it = u32(reg("esi"))
        if iis.pop(thn(), None) != it:
            return
        d = idata(it)
        emit("IIS1", {"it": it, "useed": sd(it + 0x20), "iseed": sd(d + 4), "gfx": u8(d + 0x49),
                      "b": lists(it)["b"]})

    def on_ape():
        c = cur()
        if not c:
            return
        it = c[0]
        ap[thn()] = ap.get(thn(), 0) + 1
        dt = u32(DT_PTR)
        if not once["pdt"] and dt:
            once["pdt"] = True
            emit("PDT", {"c6c": u32(dt + 0xC6C), "c70": u32(dt + 0xC70)})
        esp = reg("esp")
        mode, a2, item, row = s32(esp + 4), u32(esp + 8), u32(esp + 0xC), u32(esp + 0x10)
        d = idata(it)
        out = {"mode": mode, "a2": a2, "same": item == it, "row": row, "ret": u32(esp), "seed": sd(d + 4),
               "q": u32(d), "fi": s32(d + 0x28), "ilvl": s32(d + 0x2C), "ver": u16(d + 0x30), "fl": u32(d + 0x18)}
        if mode == 0 and row:
            base = u32(0x0096CA80)
            out["aid"] = (row - base) // 0x90 + 1 if base and row >= base else None
            out["name"] = mem(row, 32).split(b"\0")[0].decode("latin1")
            out["blk"] = blocks(row + 0x24, 3)
        elif mode == 1 and row:
            out["blk"] = blocks(row + 0x0C, 2)
        out.update(lists(it))
        emit("APE", out)

    def on_apx():
        if not in_ap():
            return
        it = cur()[0]
        ap[thn()] -= 1
        out = {"seed": iseed(it)}
        out.update(lists(it))
        emit("APX", out)

    def on_slot():
        if not in_ap():
            return
        it = cur()[0]
        ebp, edi, esi = reg("ebp"), reg("edi"), reg("esi")
        dt = u32(DT_PTR)
        prow = (edi - u32(dt + 0xA4)) // 0x2E
        blk = u32(ebp + 0x20)
        b = list(struct.unpack("<iiii", mem(blk, 16))) if blk else None
        func = u8(edi + 0x18 + esi)
        out = {"k": esi, "prop": prow, "func": func, "set": u8(edi + 0x2 + esi), "stat": u16(edi + 0x20 + 2 * esi),
               "val": s16(edi + 0xA + 2 * esi), "prev": sreg("ebx"), "blk": b, "st": u32(ebp + 0x24),
               "fl": u32(ebp + 0x28), "seed": iseed(it)}
        if func in (11, 19) and b is not None and 0 <= b[1] < s32(dt + 0xBA0):
            sk = u32(dt + 0xB98) + 0x23C * b[1]
            out["req"] = s16(sk + 0x174)
            out["maxlvl"] = s16(sk + 0x12C)
        emit("SLOT", out)

    def on_slotr():
        if in_ap():
            emit("SLOTR", {"r": sreg("eax"), "seed": iseed(cur()[0])})

    def on_roll():
        if in_ap():
            emit("ROLL", {"min": sreg("edx"), "max": s32(reg("esp") + 4), "seed": iseed(cur()[0])})

    def on_rollr():
        if in_ap():
            emit("ROLLR", {"v": sreg("eax"), "seed": iseed(cur()[0])})

    def on_wr():
        if not in_ap():
            return
        esp = reg("esp")
        emit("WR", {"stat": s16(esp + 0x10), "param": s32(esp + 0x14), "v": s32(esp + 0x18), "set": s32(esp + 0xC),
                    "st": u32(esp + 0x1C), "fl": reg("edx")})

    def on_evd(where):
        def f():
            if cur():
                emit("EVD", {"at": where, "v": sreg("eax")})
        return f

    def on_eth0():
        if cur():
            rec = reg("ebx")
            emit("ETH0", {"rfl": u32(rec + 0x80), "r44": u32(rec + 0x44), "seed": iseed(cur()[0])})

    def on_ethr():
        if cur():
            emit("ETHR", {"r": sreg("eax"), "seed": iseed(cur()[0])})

    def on_ethx():
        if cur():
            it = cur()[0]
            emit("ETHX", {"fl": u32(idata(it) + 0x18), "seed": iseed(it)})

    def on_sok0():
        if cur():
            it, rec = reg("edi"), reg("ebx")
            emit("SOK0", {"same": it == cur()[0], "rfl": u32(rec + 0x80), "r44": u32(rec + 0x44),
                          "q": u32(idata(it)), "seed": iseed(it)})

    def on_sokm():
        if cur():
            emit("SOKM", {"ms": reg("eax") & 0xFF})

    def on_sokr():
        if cur():
            emit("SOKR", {"r": sreg("eax"), "seed": iseed(cur()[0])})

    def on_sset():
        if cur():
            it = u32(reg("esp") + 4)
            emit("SSET", {"n": s32(reg("esp") + 8), "start": u32(idata(it) + 0x10), "same": it == cur()[0]})

    def on_sokx():
        if cur():
            emit("SOKX", {"seed": iseed(cur()[0])})

    Bp(0x00557450, on_ic0)
    for a in (0x00557A1C, 0x00557A27, 0x00557482):
        Bp(a, on_icx)
    Bp(0x00557AB0, on_iis0)
    Bp(0x00557E21, on_iis1)
    Bp(0x0065FEC0, on_ape)
    for a in (0x0065FF4C, 0x0065FFA9, 0x0066002F, 0x00660081):
        Bp(a, on_apx)
    Bp(0x0065FDF5, on_slot)
    Bp(0x0065FDF7, on_slotr)
    Bp(0x0065E9E0, on_roll)
    for a in (0x0065E9F3, 0x0065EA24, 0x0065EA3F):
        Bp(a, on_rollr)
    Bp(0x0065EA50, on_wr)
    Bp(0x0065FCF4, on_evd("f13"))
    Bp(0x00556D68, on_evd("eth"))
    Bp(0x00556CA0, on_eth0)
    Bp(0x00556D0C, on_ethr)
    Bp(0x00556D74, on_ethx)
    Bp(0x00556B60, on_sok0)
    Bp(0x00556BA3, on_sokm)
    Bp(0x00556C14, on_sokr)
    Bp(0x0062BCB0, on_sset)
    for a in (0x00556C63, 0x00556C91):
        Bp(a, on_sokx)
    gdb.write("PROPS logger armed\n")


_props_main()
