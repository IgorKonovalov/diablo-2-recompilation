# gdb Python logger for plan 0038 batch H6b (sockets): the lines tools/gdb/sockets.py does not write, for
# docs/findings/items/0007-sockets-runewords.md. Sourced by tools/gdb/h6b.gdb after sockets.py. One line per event,
# "TAG {json}", every line with "th" (the gdb thread number). Addresses refer to the pinned game.exe (image base
# 0x400000). Read with objdump; each address is the instruction named.
#
#   HI0 / HIX  ITEMS_InsertSocket 0x00562660 entry / its returns 0x005626D0, 0x0056289E: this logger's own open-insert
#         flag (the lines below marked "insert" are written only while an insert is open on that thread)
#   XY    insert: sub_0063B210_InvPlaceSocketed, at the call 0x0063B27F (sub_00620470, the child's x): the child, the
#         pushed x ([esp+4]) and the inventory count (+0x28) at that moment; XYY at the call 0x0063B287 (sub_006204C0,
#         y: the pushed value); XYB at the call 0x0063B29B (sub_00629ED0, the body location: the pushed value)
#   CUR   insert: 0x005627CB (the p5 test): p5 ([ebp+0x18]), the player ([ebp-0x4]), the player's cursor item
#         (inventory +0x20) before; CURX at 0x005627E3: the cursor item after
#   SLO   insert: sub_00627910_StatListLinkOwner entry: owner, child, flag, the child's list (+0x5C), the list's owner
#         (+0x04) and flags (+0x10); SLB the branch taken: "w11" 0x0062793E (a body-11/12 item), "own" 0x00627950
#         (the list already belongs to the owner: the enable-bit branch), "link" 0x00627984 (0x00626E10 then +0x04)
#   RPE   sub_00558530_ItemReplenishDurTimer / sub_00558580_ItemReplenishQtyTimer entry: which (252/253), item (EDX),
#         the game frame (game +0xA8); RPV after UnitGetStat (0x00558544 / 0x00558594): EAX; RPS at the schedule call
#         0x00558574 / 0x005585C4: the pushed type and frame, the stat value (EBX), the game frame
#   RDS   ITEMS_ReadFull's runeword store 0x0062D1EA (mov [ecx+0x38], ax): the item unit (ESI), its class, the value
#   CPY   sub_0055A2A0_ItemCopy entry: return address, the item (EDX), the two stack arguments, the item's children
#   RCP   0x00563350 entry (re-inserting copies of a parent's children): return address, ECX, EDX, the stack words
#   UIS   the client test's steps (0x004843E0..0x00484496): [name, value] for each test reached, in order: "ui" the UI
#         word (0x004843F8), "filler" (0x00484410), "socketed" (0x00484429), "hasinv" (0x00484433), "maxsockets" (AL,
#         0x0048443D), "identified" (0x00484453), "broken" (0x0048446C), "inventory" (EDI, 0x00484474), "count" and
#         "sockets" (0x0048448A); the result, the return site and the caller ([esp] at the ret); emitted when that changes
#   UIR   the client test sub_004843E0_UiCanInsertSocket at its returns (as sockets.py's UIC): the result and the
#         target's flags and runeword field (u16 ItemData +0x38), emitted when that tuple changes
import json
import struct

import gdb


def _h6b_main():
    inf = gdb.selected_inferior()
    open_ins = {}

    def mem(a, n):
        return bytes(inf.read_memory(a, n))

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

    def thn():
        t = gdb.selected_thread()
        return t.num if t else 0

    def emit(tag, d):
        d["th"] = thn()
        gdb.write("%s %s\n" % (tag, json.dumps(d, separators=(",", ":"))))

    def ins():
        return open_ins.get(thn())

    def kids(it):
        inv = u32(it + 0x60)
        if not inv:
            return None
        out, c, guard = [], u32(inv + 0x0C), 0
        while c and guard < 16:
            out.append(s32(c + 4))
            d = u32(c + 0x14)
            c, guard = (u32(d + 0x64) if d else 0), guard + 1
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
                gdb.write("LOGERR h6b %r\n" % (e,))
            return False

    def on_hi0():
        open_ins[thn()] = True
        emit("HI0", {"ret": u32(reg("esp"))})

    def on_hix(ok):
        def f():
            if open_ins.pop(thn(), None):
                emit("HIX", {"ok": ok})
        return f

    def on_xy():
        if ins():
            esp, esi = reg("esp"), reg("esi")
            emit("XY", {"item": u32(esp), "x": s32(esp + 4), "count": s32(esi + 0x28)})

    def on_xyy():
        if ins():
            esp = reg("esp")
            emit("XYY", {"item": u32(esp), "y": s32(esp + 4)})

    def on_xyb():
        if ins():
            esp = reg("esp")
            emit("XYB", {"item": u32(esp), "body": s32(esp + 4)})

    def cursor(player):
        if not player:
            return None
        inv = u32(player + 0x60)
        return u32(inv + 0x20) if inv else None

    def on_cur():
        if ins():
            ebp = reg("ebp")
            pl = u32(ebp - 4)
            emit("CUR", {"p5": u32(ebp + 0x18), "player": pl, "cursor": cursor(pl)})

    def on_curx():
        if ins():
            pl = u32(reg("ebp") - 4)
            emit("CURX", {"player": pl, "cursor": cursor(pl)})

    def on_slo():
        if ins():
            esp = reg("esp")
            owner, child, flag = u32(esp + 4), u32(esp + 8), u32(esp + 0xC)
            lst = u32(child + 0x5C) if child else 0
            emit("SLO", {"owner": owner, "child": child, "flag": flag, "list": lst,
                         "lowner": u32(lst + 4) if lst else None, "lflags": u32(lst + 0x10) if lst else None})

    def on_slb(b):
        def f():
            if ins():
                emit("SLB", {"b": b})
        return f

    def on_rpe(which):
        def f():
            game = reg("ecx")
            emit("RPE", {"stat": which, "item": reg("edx"), "frame": u32(game + 0xA8), "ins": bool(ins())})
        return f

    def on_rpv(which):
        def f():
            emit("RPV", {"stat": which, "v": sreg("eax")})
        return f

    def on_rps(which):
        def f():
            esp = reg("esp")
            emit("RPS", {"stat": which, "type": u32(esp), "at": u32(esp + 4), "v": sreg("ebx"),
                         "frame": u32(reg("esi") + 0xA8)})
        return f

    def on_rds():
        esi = reg("esi")
        emit("RDS", {"item": esi, "cls": s32(esi + 4), "v": reg("eax") & 0xFFFF})

    def on_cpy():
        esp, it = reg("esp"), reg("edx")
        emit("CPY", {"ret": u32(esp), "item": it, "cls": s32(it + 4) if it else None, "a1": u32(esp + 4),
                     "a2": u32(esp + 8), "kids": kids(it) if it else None})

    def on_rcp():
        esp = reg("esp")
        emit("RCP", {"ret": u32(esp), "ecx": reg("ecx"), "edx": reg("edx"),
                     "a": [u32(esp + 4), u32(esp + 8), u32(esp + 0xC)]})

    uir = {"args": None, "last": None}

    def on_uir0():
        uir["args"] = (reg("ecx"), reg("eax"))

    def on_uirx():
        a = uir["args"]
        uir["args"] = None
        if a is None or not a[0] or not a[1]:
            return
        t = a[1]
        d = u32(t + 0x14)
        out = {"r": reg("eax") & 0xFF, "cur": s32(a[0] + 4), "tgt": s32(t + 4), "fl": u32(d + 0x18) if d else None,
               "rw": u16(d + 0x38) if d else None, "kids": kids(t)}
        key = json.dumps(out, sort_keys=True)
        if key != uir["last"]:
            uir["last"] = key
            emit("UIR", out)

    # the client test's steps, in order: each value at the instruction after the call (or load) that a test reads
    uis = {"steps": None, "last": None}

    def on_uis0():
        uis["steps"] = []

    def on_uis(name, regname, mask=0xFFFFFFFF):
        def f():
            if uis["steps"] is not None:
                uis["steps"].append([name, reg(regname) & mask])
        return f

    def on_uis_cnt():
        if uis["steps"] is not None:
            uis["steps"].append(["count", reg("eax")])
            uis["steps"].append(["sockets", reg("esi")])

    def on_uisx(addr):
        def f():
            st = uis["steps"]
            uis["steps"] = None
            if st is None:
                return
            out = {"r": reg("eax") & 0xFF, "ret": addr, "caller": u32(reg("esp")), "steps": st}
            key = json.dumps(out, sort_keys=True)
            if key != uis["last"]:
                uis["last"] = key
                emit("UIS", out)
        return f

    Bp(0x004843E0, on_uis0)
    for a, n, r, m in ((0x004843F8, "ui", "eax", 0xFFFFFFFF), (0x00484410, "filler", "eax", 0xFFFFFFFF),
                       (0x00484429, "socketed", "eax", 0xFFFFFFFF), (0x00484433, "hasinv", "eax", 0xFFFFFFFF),
                       (0x0048443D, "maxsockets", "eax", 0xFF), (0x00484453, "identified", "eax", 0xFFFFFFFF),
                       (0x0048446C, "broken", "eax", 0xFFFFFFFF), (0x00484474, "inventory", "edi", 0xFFFFFFFF)):
        Bp(a, on_uis(n, r, m))
    Bp(0x0048448A, on_uis_cnt)
    for a in (0x0048447A, 0x00484492, 0x00484496):
        Bp(a, on_uisx(a))

    Bp(0x00562660, on_hi0)
    Bp(0x005626D0, on_hix(0))
    Bp(0x0056289E, on_hix(1))
    Bp(0x0063B27F, on_xy)
    Bp(0x0063B287, on_xyy)
    Bp(0x0063B29B, on_xyb)
    Bp(0x005627CB, on_cur)
    Bp(0x005627E3, on_curx)
    Bp(0x00627910, on_slo)
    Bp(0x0062793E, on_slb("w11"))
    Bp(0x00627950, on_slb("own"))
    Bp(0x00627984, on_slb("link"))
    Bp(0x00558530, on_rpe(252))
    Bp(0x00558580, on_rpe(253))
    Bp(0x00558544, on_rpv(252))
    Bp(0x00558594, on_rpv(253))
    Bp(0x00558574, on_rps(252))
    Bp(0x005585C4, on_rps(253))
    Bp(0x0062D1EA, on_rds)
    Bp(0x0055A2A0, on_cpy)
    Bp(0x00563350, on_rcp)
    Bp(0x004843E0, on_uir0)
    for a in (0x0048447A, 0x00484492, 0x00484496):
        Bp(a, on_uirx)
    gdb.write("H6B logger armed\n")


_h6b_main()
