# gdb Python logger for plan 0029 Phase 2 (socket filling and runewords): docs/findings/items/0007-sockets-runewords.md.
# Sourced by tools/gdb/sockets.gdb. One line per event, "TAG {json}". Addresses refer to the pinned game.exe (image
# base 0x400000). Seeds are "low:high" hex. Every line carries "th" (the gdb thread number). Events between INS0 and
# INSX belong to that insert (thread-local).
#
#   PKT   0x0054D750 the server's client-packet dispatcher (sub_0054D750_SrvPacketDispatch; table 0x006E0D18 + 8 op):
#         opcode, length, the first 16 bytes; only opcodes in LOG_OPS (every other opcode is counted: PKTN at each
#         INS0, the counts since the previous one)
#   SP0   0x0054B650 SOCK_PacketInsert entry: length, child id (+1), parent id (+5)
#   SPC   its own checks: 0x0054B685 cursor test (EAX != 0 refuses), 0x0054B692 own-item test, 0x0054B6BD the trade
#         test (the interaction unit's type, 0 skips)
#   SPX   its returns 0x0054B66C, 0x0054B6F4, 0x0054B6FF: EAX
#   INS0  0x00562660 ITEMS_InsertSocket entry: ECX game, EDX player, child id, parent id, p4..p7, return address, the
#         game seed (game+0xD0), the ladder word (game+0x74)
#   CH / PA  the child (0x005626DB, EDI) and the parent (0x005626FA, ESI) once found: UNIT (below)
#   IST   the tests passed, in order: child_item (0x005626E4), child_cursor (0x005626E9), parent_item (0x005626FF),
#         parent_ident (0x00562715), parent_mode (0x00562727), child_sock (0x0056273B), child_ident (0x00562755),
#         parent_socketed (0x00562772), parent_hasinv (0x00562780), inventory (0x00562798), free (0x005627B3)
#   INSX  the returns: refused 0x005626D0 (nf: *notFound), success 0x0056289E; the game seed and, when found, the
#         child and the parent again (UNIT)
#   APE / APX / SLOT / SLOTR / ROLL / ROLLR / WR   as tools/gdb/props.py, while an insert is open (the item seeds are
#         the insert's child's): ItemApplyProps (0x0065FEC0) mode, a2, the item (== child), the gems row index
#         ((row - g_pGems) / 0xC0), the group (5th argument), the child's lists; its returns: item seed, lists
#   EVD   0x0065FCF4 the evaluated max durability func 13 reads (EAX); PDT once, at the first INS0: DataTables
#         (*0x00744304) +0xC6C and +0xC70 (the charged-skill packing words)
#   M0    0x0062BED0 RUNEWORD_Match entry while an insert is open: the item, the return address
#   MK    0x0062BF54 after the children loop: n (EDI), the seven stack words kids[0..6] at [ebp-0x2C] (kids[n..] are
#         what the loop did not write: the stale words the k == n comparison reads)
#   MX    the returns 0x0062BEE4, 0x0062BF2A, 0x0062C04E, 0x0062C059: the row index ((EAX - g_pRunes) / 0x120) or -1
#   RWA   0x006600A0 RUNEWORD_Apply entry: parent, child, a3, the child's item seed, start seed (+0x10), unit seed,
#         the parent's lists; RWX its returns 0x006600B9, 0x00660117: EAX, child seed, the parent's lists
#   RF0 / RFX  0x0055FE80 sub_0055FE80_ItemRefillCharges entry / returns 0x0055FF92, 0x0055FF9C: EAX, parent lists
#   UIC   the client's insert test sub_004843E0_UiCanInsertSocket (.\\UI\\inv.cpp; ECX the cursor item, EAX the target):
#         at its returns 0x0048447A, 0x00484492, 0x00484496 the result (AL), the UI state word 0x007BCBF0, the
#         cursor's class, type, flags, the target's class, flags, quality, ilvl, stat 194 (base entry), inventory
#         count; emitted only when that tuple changes (the test runs on every hover)
# UNIT = {"u": unit, "type", "cls", "id", "mode", "q" quality, "seed" item seed, "start" (+0x10), "useed" (unit
#        +0x20), "fl" flags (+0x18), "fi" (+0x28), "ilvl" (+0x2C), "ver" (+0x30), "rw" (u16 +0x38), "kids" [[unit,
#        cls], ...] (the inventory list, +0x60 -> +0x0C, next ItemData+0x64), "ninv" (inventory +0x28), "b"/"sub" the
#        stat lists as tools/gdb/props.py}
import json
import struct

import gdb

LOG_OPS = {0x13, 0x17, 0x18, 0x19, 0x1A, 0x1B, 0x1C, 0x1D, 0x1F, 0x20, 0x21, 0x22, 0x23, 0x24, 0x25, 0x26, 0x27,
           0x28, 0x29, 0x2A, 0x2C, 0x2D, 0x30, 0x31, 0x32, 0x33, 0x34, 0x35, 0x36, 0x37, 0x38, 0x3F, 0x4F, 0x5F, 0x60}


def _sockets_main():
    inf = gdb.selected_inferior()
    ins = {}       # thread -> {"child": unit or 0, "parent": unit or 0, "game": game, "nf": ptr}
    apd = {}       # thread -> ItemApplyProps depth inside the insert
    other = {}
    pdt = {"done": False}
    G_GEMS, G_RUNES = 0x0096CA94, 0x0096CA9C
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
                    sub.append([u32(node + 0x14), u32(node + 0x10), entries(node), u32(node + 0x04)])
                    node, guard = u32(node + 0x2C), guard + 1
        return {"b": entries(lst), "sub": sub}

    def kids(it):
        inv = u32(it + 0x60)
        if not inv:
            return [], None
        out, c, guard = [], u32(inv + 0x0C), 0
        while c and guard < 16:
            out.append([c, s32(c + 4)])
            d = idata(c)
            c, guard = (u32(d + 0x64) if d else 0), guard + 1
        return out, s32(inv + 0x28)

    def unit(u):
        if not u:
            return None
        out = {"u": u, "type": u32(u), "cls": s32(u + 4), "id": u32(u + 0x0C), "mode": u32(u + 0x10),
               "useed": sd(u + 0x20)}
        d = idata(u)
        if out["type"] == 4 and d:
            out.update({"q": u32(d), "seed": sd(d + 4), "start": u32(d + 0x10), "fl": u32(d + 0x18),
                        "fi": s32(d + 0x28), "ilvl": s32(d + 0x2C), "ver": u16(d + 0x30), "rw": u16(d + 0x38)})
            k, n = kids(u)
            out["kids"], out["ninv"] = k, n
            out.update(lists(u))
        return out

    def cur():
        return ins.get(thn())

    def item_seed():
        c = cur()
        return sd(idata(c["child"]) + 4) if c and c["child"] else None

    def in_ap():
        return cur() is not None and apd.get(thn(), 0) > 0

    class Bp(gdb.Breakpoint):
        def __init__(self, addr, fn):
            super().__init__("*0x%08X" % addr, internal=True)
            self.silent = True
            self.fn = fn

        def stop(self):
            try:
                self.fn()
            except Exception as e:  # never stop the game on a logger error; log it instead
                gdb.write("LOGERR sockets %r\n" % (e,))
            return False

    # ---- the client's own test (hover and click)
    uic = {"args": None, "last": None}

    def on_uic0():
        uic["args"] = (reg("ecx"), reg("eax"))

    def citem(u):
        if not u:
            return None
        d = idata(u)
        b = {(k, p): v for k, p, v in (lists(u)["b"] or [])}
        out = {"cls": s32(u + 4), "type": u32(u), "fl": u32(d + 0x18) if d else None, "q": u32(d) if d else None,
               "ilvl": s32(d + 0x2C) if d else None, "s194": b.get((194, 0), 0)}
        inv = u32(u + 0x60)
        out["ninv"] = s32(inv + 0x28) if inv else None
        return out

    def on_uicx():
        a = uic["args"]
        if a is None:
            return
        uic["args"] = None
        if not a[0] or not a[1]:
            return
        res = reg("eax") & 0xFF
        cur_, tgt = citem(a[0]), citem(a[1])
        key = json.dumps([res, cur_, tgt], sort_keys=True)
        if key == uic["last"]:
            return
        uic["last"] = key
        emit("UIC", {"r": res, "ui": u32(0x007BCBF0), "cur": cur_, "tgt": tgt})

    # ---- the client packets
    def on_pkt():
        esp = reg("esp")
        p, n = u32(esp + 4), u32(esp + 8)
        op = u8(p) if p else -1
        if op in LOG_OPS:
            emit("PKT", {"op": op, "len": n, "hex": mem(p, min(n, 16)).hex() if p and n else ""})
        else:
            other[op] = other.get(op, 0) + 1

    def on_sp0():
        esp = reg("esp")
        p, n = u32(esp + 4), u32(esp + 8)
        emit("SP0", {"len": n, "child": u32(p + 1) if n >= 5 else None, "parent": u32(p + 5) if n >= 9 else None})

    def on_spc(what, regname):
        def f():
            if what == "trade":
                emit("SPC", {"t": what, "itype": u32(reg("eax"))})
            else:
                emit("SPC", {"t": what, "eax": reg(regname)})
        return f

    def on_spx():
        emit("SPX", {"eax": sreg("eax")})

    # ---- the insert
    def on_ins0():
        esp = reg("esp")
        game = reg("ecx")
        ins[thn()] = {"child": 0, "parent": 0, "game": game, "nf": u32(esp + 0xC)}
        apd[thn()] = 0
        if not pdt["done"] and u32(DT_PTR):
            pdt["done"] = True
            dt = u32(DT_PTR)
            emit("PDT", {"c6c": u32(dt + 0xC6C), "c70": u32(dt + 0xC70)})
        if other:
            emit("PKTN", {"%02x" % k: v for k, v in sorted(other.items())})
            other.clear()
        emit("INS0", {"game": game, "player": reg("edx"), "cid": u32(esp + 4), "pid": u32(esp + 8),
                      "p": [u32(esp + 0x10), u32(esp + 0x14), u32(esp + 0x18), u32(esp + 0x1C)], "ret": u32(esp),
                      "gseed": sd(game + 0xD0), "ladder": u32(game + 0x74)})

    def on_child():
        c = cur()
        if c is not None:
            c["child"] = reg("edi")
            emit("CH", unit(c["child"]))

    def on_parent():
        c = cur()
        if c is not None:
            c["parent"] = reg("esi")
            emit("PA", unit(c["parent"]))

    def on_ist(name):
        def f():
            if cur() is not None:
                emit("IST", {"s": name})
        return f

    def on_insx(ok):
        def f():
            c = ins.pop(thn(), None)
            if c is None:
                return
            out = {"ret": 1 if ok else 0, "nf": u32(c["nf"]) if not ok else 0, "gseed": sd(c["game"] + 0xD0)}
            out["child"] = unit(c["child"])
            out["parent"] = unit(c["parent"])
            emit("INSX", out)
        return f

    # ---- the property machinery inside an insert
    def on_ape():
        c = cur()
        if c is None:
            return
        apd[thn()] = apd.get(thn(), 0) + 1
        esp = reg("esp")
        mode, a2, item, row, grp = s32(esp + 4), u32(esp + 8), u32(esp + 0xC), u32(esp + 0x10), s32(esp + 0x14)
        g = u32(G_GEMS)
        out = {"mode": mode, "a2": a2, "same": item == c["child"], "row": (row - g) // 0xC0 if g and row >= g else None,
               "grp": grp, "a6": s32(esp + 0x18), "ret": u32(esp), "seed": sd(idata(item) + 4)}
        out.update(lists(item))
        emit("APE", out)

    def on_apx():
        if not in_ap():
            return
        apd[thn()] -= 1
        out = {"seed": item_seed()}
        out.update(lists(cur()["child"]))
        emit("APX", out)

    def on_slot():
        if cur() is None:
            return
        ebp, edi, esi = reg("ebp"), reg("edi"), reg("esi")
        dt = u32(DT_PTR)
        prow = (edi - u32(dt + 0xA4)) // 0x2E
        blk = u32(ebp + 0x20)
        b = list(struct.unpack("<iiii", mem(blk, 16))) if blk else None
        func = u8(edi + 0x18 + esi)
        out = {"k": esi, "prop": prow, "func": func, "set": u8(edi + 0x2 + esi), "stat": u16(edi + 0x20 + 2 * esi),
               "val": s16(edi + 0xA + 2 * esi), "prev": sreg("ebx"), "blk": b, "st": u32(ebp + 0x24),
               "fl": u32(ebp + 0x28), "seed": item_seed()}
        if func in (11, 19) and b is not None and 0 <= b[1] < s32(dt + 0xBA0):
            sk = u32(dt + 0xB98) + 0x23C * b[1]
            out["req"] = s16(sk + 0x174)
            out["maxlvl"] = s16(sk + 0x12C)
        emit("SLOT", out)

    def on_slotr():
        if cur() is not None:
            emit("SLOTR", {"r": sreg("eax"), "seed": item_seed()})

    def on_roll():
        if cur() is not None:
            emit("ROLL", {"min": sreg("edx"), "max": s32(reg("esp") + 4), "seed": item_seed()})

    def on_rollr():
        if cur() is not None:
            emit("ROLLR", {"v": sreg("eax"), "seed": item_seed()})

    def on_evd():
        if cur() is not None:
            emit("EVD", {"at": "f13", "v": sreg("eax")})

    def on_wr():
        if cur() is None:
            return
        esp = reg("esp")
        emit("WR", {"stat": s16(esp + 0x10), "param": s32(esp + 0x14), "v": s32(esp + 0x18), "set": s32(esp + 0xC),
                    "st": u32(esp + 0x1C), "fl": reg("edx")})

    # ---- the runeword
    def on_m0():
        if cur() is not None:
            esp = reg("esp")
            emit("M0", {"item": u32(esp + 4), "ret": u32(esp)})

    def on_mk():
        if cur() is not None:
            ebp = reg("ebp")
            emit("MK", {"n": reg("edi"), "kids": [s32(ebp - 0x2C + 4 * k) for k in range(7)]})

    def on_mx():
        if cur() is not None:
            eax = reg("eax")
            r = u32(G_RUNES)
            emit("MX", {"row": (eax - r) // 0x120 if eax and r and eax >= r else -1})

    def on_rwa():
        if cur() is None:
            return
        esp = reg("esp")
        parent, child = u32(esp + 4), u32(esp + 8)
        d = idata(child)
        out = {"parent": parent, "child": child, "a3": u32(esp + 0xC), "seed": sd(d + 4), "start": u32(d + 0x10),
               "useed": sd(child + 0x20), "ccls": s32(child + 4), "same": child == cur()["child"]}
        out.update(lists(parent))
        emit("RWA", out)

    def on_rwx():
        c = cur()
        if c is None:
            return
        out = {"eax": sreg("eax"), "seed": item_seed()}
        out.update(lists(c["parent"]))
        emit("RWX", out)

    def on_rf0():
        if cur() is not None:
            emit("RF0", {"parent": u32(reg("esp") + 4)})

    def on_rfx():
        c = cur()
        if c is not None:
            out = {"eax": sreg("eax")}
            out.update(lists(c["parent"]))
            emit("RFX", out)

    Bp(0x004843E0, on_uic0)
    for a in (0x0048447A, 0x00484492, 0x00484496):
        Bp(a, on_uicx)
    Bp(0x0054D750, on_pkt)
    Bp(0x0054B650, on_sp0)
    Bp(0x0054B685, on_spc("cursor", "eax"))
    Bp(0x0054B692, on_spc("own", "eax"))
    Bp(0x0054B6BA, on_spc("trade", "eax"))
    for a in (0x0054B66C, 0x0054B6F4, 0x0054B6FF):
        Bp(a, on_spx)
    Bp(0x00562660, on_ins0)
    Bp(0x005626DB, on_child)
    Bp(0x005626FA, on_parent)
    for a, n in ((0x005626E4, "child_item"), (0x005626E9, "child_cursor"), (0x005626FF, "parent_item"),
                 (0x00562715, "parent_ident"), (0x00562727, "parent_mode"), (0x0056273B, "child_sock"),
                 (0x00562755, "child_ident"), (0x00562772, "parent_socketed"), (0x00562780, "parent_hasinv"),
                 (0x00562798, "inventory"), (0x005627B3, "free")):
        Bp(a, on_ist(n))
    Bp(0x005626D0, on_insx(False))
    Bp(0x0056289E, on_insx(True))
    Bp(0x0065FEC0, on_ape)
    for a in (0x0065FF4C, 0x0065FFA9, 0x0066002F, 0x00660081):
        Bp(a, on_apx)
    Bp(0x0065FDF5, on_slot)
    Bp(0x0065FDF7, on_slotr)
    Bp(0x0065E9E0, on_roll)
    for a in (0x0065E9F3, 0x0065EA24, 0x0065EA3F):
        Bp(a, on_rollr)
    Bp(0x0065EA50, on_wr)
    Bp(0x0065FCF4, on_evd)
    Bp(0x0062BED0, on_m0)
    Bp(0x0062BF54, on_mk)
    for a in (0x0062BEE4, 0x0062BF2A, 0x0062C04E, 0x0062C059):
        Bp(a, on_mx)
    Bp(0x006600A0, on_rwa)
    for a in (0x006600B9, 0x00660117):
        Bp(a, on_rwx)
    Bp(0x0055FE80, on_rf0)
    for a in (0x0055FF92, 0x0055FF9C):
        Bp(a, on_rfx)
    gdb.write("SOCKETS logger armed\n")


_sockets_main()
