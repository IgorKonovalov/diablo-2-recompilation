# gdb Python logger for plan 0038 batch H2c (forced): the classic throwable re-pick of TC_ResolveDrops and the entry
# state of the property handlers of funcs 12, 23 and 24. Sourced by tools/gdb/items-h2c.gdb after the items-h2b set
# (pilot.py, uniques.py, affixes.py, props.py, cube.py, h2b.py) and before tools/gdb/tc-drops.gdb; it leaves their
# lines unchanged and shares no tag with them. One line per event, "TAG {json}" (tools/tc.py and tools/quality.py skip
# JSON lines). Addresses refer to the pinned game.exe (image base 0x400000), read with objdump
# (docs/findings/items/0001-tc-resolution.md § 8 read list, docs/findings/items/0006-properties.md § 4 read list).
# Seeds "low:high" hex. Every line carries "th" (the gdb thread number).
#
#   THR  0x0055AE9C in TC_ResolveDrops, the throwable branch after ITEMTYPES_IsThrowable returned non-zero, at the
#        `cmp $0xa,%edx`: item index (u16 [EBP-0x50C]), the call's counter before the increment (EDX), the frame's
#        picks left (s32 at [[EBP-0x51C]]), the game's expansion flag (game [EBP-0x528] +0x70)
#   THF  0x0055AEB0 after the refund `addl $1,(%eax)`: picks left
#   THL  0x0055AEC2 after sub_00633680_ItemIndexByCode('lsd '): the index it returned (AX)
#   E12  0x0065FC40 PROP_Func12_SkillRand entry ([esp+4] item, [esp+8] block): item class, item flags (ItemData+0x18),
#        the block {code, par, min, max}, item seed;  E12V 0x0065FC68 after PROP_RollValue: v (EAX)
#   E23  0x0065FD20 PROP_Func23_Ethereal entry ([esp+4] item, [esp+8] block): unit type, class, item flags, quality,
#        the block, the record's durability bytes (+0x112, +0x113 of the Items record by class, read as
#        ITEMS_GetRecord 0x006335F0 does: count 0x0096CA58, base 0x0096CA5C, 0x1A8 per record); E23E 0x0065FD3C
#        ITEMS_IsEthereal's return (EAX); E23D 0x0065FD46 sub_00629930_ItemHasDurability's return (EAX);
#        E23X 0x0065FD55 / 0x0065FD5A the returns (r 1 / 0): the entry's item, its flags now
#   E24  0x0065F390 PROP_Func24_ParParam entry ([esp+4] item, [esp+8] block, [esp+0x18] prev): the block, prev,
#        item seed;  E24V 0x0065F3BF the value handed to PROP_WriteStat (EAX: prev, or the roll)
import json
import struct

import gdb


def _h2c_main():
    inf = gdb.selected_inferior()
    cur23 = {}    # thread -> the item of the open PROP_Func23_Ethereal call

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
        return struct.unpack("<i", struct.pack("<I", reg(n)))[0]

    def thn():
        t = gdb.selected_thread()
        return t.num if t else 0

    def emit(tag, d):
        d["th"] = thn()
        gdb.write("%s %s\n" % (tag, json.dumps(d, separators=(",", ":"))))

    def sd(p):
        return "%08x:%08x" % struct.unpack("<II", mem(p, 8))

    def item(it):
        d = {"it": it}
        if it and u32(it) == 4:
            idata = u32(it + 0x14)
            d.update({"cls": s32(it + 4)})
            if idata:
                d.update({"fl": u32(idata + 0x18), "q": u32(idata), "iseed": sd(idata + 4)})
        return d

    def block(b):
        if not b:
            return None
        return [s32(b), s32(b + 4), s32(b + 8), s32(b + 12)]

    class Bp(gdb.Breakpoint):
        def __init__(self, addr, fn):
            super().__init__("*0x%08X" % addr, internal=True)
            self.silent = True
            self.fn = fn

        def stop(self):
            try:
                self.fn()
            except Exception as e:  # never stop the game on a logger error; log it instead
                gdb.write("LOGERR h2c %r\n" % (e,))
            return False

    def on_thr():
        ebp = reg("ebp")
        game = u32(ebp - 0x528)
        emit("THR", {"item": u16(ebp - 0x50C), "n": sreg("edx"), "left": s32(u32(ebp - 0x51C)),
                     "exp": u32(game + 0x70)})

    def on_thf():
        emit("THF", {"left": s32(u32(reg("ebp") - 0x51C))})

    def on_thl():
        emit("THL", {"lsd": reg("eax") & 0xFFFF})

    def on_e12():
        esp = reg("esp")
        d = item(u32(esp + 4))
        d["blk"] = block(u32(esp + 8))
        emit("E12", d)

    def on_e12v():
        emit("E12V", {"v": sreg("eax")})

    def on_e23():
        esp = reg("esp")
        it = u32(esp + 4)
        cur23[thn()] = it
        d = item(it)
        d["utype"] = u32(it) if it else None
        d["blk"] = block(u32(esp + 8))
        if it and u32(it) == 4:
            base, n = u32(0x0096CA5C), u32(0x0096CA58)
            cls = s32(it + 4)
            if base and 0 <= cls < n:
                r = base + 0x1A8 * cls
                d.update({"dur": u8(r + 0x112), "nodur": u8(r + 0x113)})
        emit("E23", d)

    def on_e23e():
        emit("E23E", {"eth": reg("eax")})

    def on_e23d():
        emit("E23D", {"hasdur": reg("eax")})

    def on_e23x(r):
        def f():
            d = item(cur23.pop(thn(), 0))
            d["r"] = r
            emit("E23X", d)
        return f

    def on_e24():
        esp = reg("esp")
        d = item(u32(esp + 4))
        d["blk"] = block(u32(esp + 8))
        d["prev"] = s32(esp + 0x18)
        emit("E24", d)

    def on_e24v():
        emit("E24V", {"v": sreg("eax")})

    Bp(0x0055AE9C, on_thr)
    Bp(0x0055AEB0, on_thf)
    Bp(0x0055AEC2, on_thl)
    Bp(0x0065FC40, on_e12)
    Bp(0x0065FC68, on_e12v)
    Bp(0x0065FD20, on_e23)
    Bp(0x0065FD3C, on_e23e)
    Bp(0x0065FD46, on_e23d)
    Bp(0x0065FD55, on_e23x(1))
    Bp(0x0065FD5A, on_e23x(0))
    Bp(0x0065F390, on_e24)
    Bp(0x0065F3BF, on_e24v)
    gdb.write("H2C logger armed\n")


_h2c_main()
