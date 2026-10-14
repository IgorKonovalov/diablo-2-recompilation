# gdb Python logger for plan 0019 Phase 2 (unique and set selection, the creation fallbacks): the path through
# sub_00557450_ItemCreateByQuality, docs/findings/items/0004-uniques-sets.md. Sourced by tools/gdb/uniques.gdb
# before tools/gdb/tc-drops.gdb, whose lines it leaves unchanged. One line per event, "TAG {json}" (tools/tc.py and
# tools/quality.py skip JSON lines). Addresses refer to the pinned game.exe (image base 0x400000). Seeds are
# "low:high" hex. "it" = the item unit being created (thread-local, from IC0 to ICX).
#
#   IC0  0x00557450 ItemCreateByQuality entry (ECX game, EDX &item, [esp+4] rec, [esp] return): item class, ItemData
#        quality +0x00, seed +0x04, start seed +0x10, flags +0x18, file index +0x28, ilvl +0x2C, version u16 +0x30;
#        record restore +0x2C, quality +0x30, row+1 +0x40, flags +0x80; game +0x6A, +0x6D, +0x70, +0x74, +0x78
#   ICQ  0x0055757B the switch: quality after the pre-switch overrides (EAX + 1)
#   BLD  each builder entry reached while an IC0 is open: k = unique 0x005566B0, set 0x005C2940, rare 0x005C21A0,
#        magic 0x005565E0, superior 0x005C2AD0, normal 0x00556E80, normal0 0x00556D80, low 0x005C2FB0,
#        normalcase 0x00556F30, crafted 0x005C21D0; item seed, item quality, record quality, file index
#   UMADE 0x005566B0 the made-uniques bits set at Game +0x1B24 (128 dwords) as a list of rows
#   UR   0x00556983 after RNG_RangeOffset in the unique builder: r (EAX), item seed
#   UPK  0x005569AD the unique row (ECX), n (EDI), total [ebp-8], forced [ebp-0x10], the candidate pairs
#        {row, cumBefore} at g_UniqueCandidates 0x008846F8, the row's made bit, item seed
#   UNONE 0x00556942 no unique candidate
#   SR   0x005C26D0 after RNG_RangeB in ITEMS_BuildSetPick: r (EAX), item seed
#   SPK  0x005C26AF after the set filter loop: n (EDI), total [ebp-4], forced [ebp-8], pairs {row, weight} at
#        [ebp-0x814]; SROW 0x005C270D the row (ECX)
#   PROPS 0x0065FEC0 ItemApplyProps entry when called from a builder (return 0x00556A3D or 0x005C272E): mode, item seed
#   BRET the builder results in ItemCreateByQuality: unique 0x005576EF, set 0x00557896 (EAX, file index, item seed)
#   DUR  the failure durability step: k 3 (unique) / 2 (set); has = ItemHasDurability (0x005576FF / 0x005578A6),
#        ver (0x0055770B / 0x005578B2), s72 GetUnitStat(72) (0x0055771D / 0x005578C4), s73 GetUnitBaseStat(73)
#        (0x0055772B / 0x005578D2), w72 and w73 the values written (0x00557746 ESI, 0x00557765 EAX / 0x005578EC,
#        0x0055790A EAX)
#   FB   fallback helper entries: rare 0x005573F0 (&S in ESI), magic 0x00557380 (&S in EBX), superior 0x00557320
#        (&S in ESI), normal 0x005572A0 (S in EAX); S and the item seed
#   ICJ  0x00557943 the join after the builder chain: item seed, quality, record quality, file index
#   ICX  the returns 0x00557A1C (1), 0x00557A27 (0), 0x00557482 (0, early): item seed and quality
import json
import struct

import gdb


def _uniques_main():
    inf = gdb.selected_inferior()
    cur = {}

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
        gdb.write("%s %s\n" % (tag, json.dumps(d, separators=(",", ":"))))

    def sd(p):
        return "%08x:%08x" % struct.unpack("<II", mem(p, 8))

    def idata(it):
        return u32(it + 0x14)

    def iseed(it):
        return sd(idata(it) + 4)

    class Bp(gdb.Breakpoint):
        def __init__(self, addr, fn):
            super().__init__("*0x%08X" % addr, internal=True)
            self.silent = True
            self.fn = fn

        def stop(self):
            try:
                self.fn()
            except Exception as e:  # never stop the game on a logger error; log it instead
                gdb.write("LOGERR uniques %r\n" % (e,))
            return False

    def c():
        return cur.get(thn())

    def on_ic0():
        game, it, rec, ret = reg("ecx"), u32(reg("edx")), u32(reg("esp") + 4), u32(reg("esp"))
        cur[thn()] = (it, rec, game)
        d = idata(it)
        emit("IC0", {"th": thn(), "ret": ret, "it": it, "cls": s32(it + 4), "id": u32(it + 0xC),
                     "q": u32(d), "seed": sd(d + 4), "start": u32(d + 0x10), "fl": u32(d + 0x18),
                     "fi": s32(d + 0x28), "ilvl": s32(d + 0x2C), "ver": u16(d + 0x30),
                     "rest": s32(rec + 0x2C), "rq": s32(rec + 0x30), "rrow": u32(rec + 0x40), "rfl": u32(rec + 0x80),
                     "g6a": mem(game + 0x6A, 1)[0] if game else None, "diff": mem(game + 0x6D, 1)[0] if game else None,
                     "exp": u32(game + 0x70) if game else None, "ladder": u32(game + 0x74) if game else None,
                     "gver": u16(game + 0x78) if game else None})

    def on_icq():
        if not c():
            return
        it, rec, _ = c()
        emit("ICQ", {"q": reg("eax") + 1, "iq": u32(idata(it)), "rq": s32(rec + 0x30)})

    def on_bld(k):
        def f():
            if not c():
                return
            it, rec, _ = c()
            d = idata(it)
            emit("BLD", {"k": k, "seed": sd(d + 4), "q": u32(d), "rq": s32(rec + 0x30), "fi": s32(d + 0x28),
                         "start": u32(d + 0x10)})
        return f

    def on_umade():
        if not c():
            return
        game = u32(reg("esp") + 4)
        bits = []
        if game:
            words = struct.unpack("<128I", mem(game + 0x1B24, 512))
            for i, w in enumerate(words):
                while w:
                    b = (w & -w).bit_length() - 1
                    bits.append(32 * i + b)
                    w &= w - 1
        emit("UMADE", {"game": game, "rows": bits})

    def on_ur():
        if c():
            emit("UR", {"r": sreg("eax"), "seed": iseed(c()[0])})

    def on_upk():
        if not c():
            return
        it, _, game = c()
        ebp = reg("ebp")
        n = sreg("edi")
        row = sreg("ecx")
        pairs = list(struct.unpack("<%di" % (2 * n), mem(0x008846F8, 8 * n))) if 0 < n <= 4096 else []
        made = None
        if game and 0 <= row <= 0x1000:
            made = (u32(game + 0x1B24 + 4 * (row >> 5)) >> (row & 31)) & 1
        emit("UPK", {"row": row, "n": n, "total": s32(ebp - 8), "forced": s32(ebp - 0x10),
                     "cand": [pairs[i:i + 2] for i in range(0, len(pairs), 2)], "made": made, "seed": iseed(it)})

    def on_unone():
        if c():
            emit("UNONE", {"seed": iseed(c()[0])})

    def on_spk():
        if not c():
            return
        ebp = reg("ebp")
        n = sreg("edi")
        pairs = list(struct.unpack("<%di" % (2 * n), mem(ebp - 0x814, 8 * n))) if 0 < n <= 256 else []
        emit("SPK", {"n": n, "total": s32(ebp - 4), "forced": s32(ebp - 8),
                     "cand": [pairs[i:i + 2] for i in range(0, len(pairs), 2)], "seed": iseed(c()[0])})

    def on_sr():
        if c():
            emit("SR", {"r": sreg("eax"), "seed": iseed(c()[0])})

    def on_srow():
        if c():
            emit("SROW", {"row": sreg("ecx"), "seed": iseed(c()[0])})

    def on_props():
        ret = u32(reg("esp"))
        if ret not in (0x00556A3D, 0x005C272E) or not c():
            return
        emit("PROPS", {"mode": s32(reg("esp") + 4), "seed": iseed(c()[0])})

    def on_bret(k):
        def f():
            if not c():
                return
            it = c()[0]
            emit("BRET", {"k": k, "ret": sreg("eax"), "fi": s32(idata(it) + 0x28), "seed": iseed(it)})
        return f

    def on_dur(k, what, r, mask=0xFFFFFFFF):
        def f():
            if c():
                v = reg(r) & mask
                emit("DUR", {"k": k, what: v - (1 << 32) if v & 0x80000000 and mask == 0xFFFFFFFF else v})
        return f

    def on_fb(k, how):
        def f():
            if not c():
                return
            s = reg("eax") if how == "eax" else u32(reg(how))
            emit("FB", {"k": k, "S": s, "seed": iseed(c()[0])})
        return f

    def on_icj():
        if not c():
            return
        it, rec, _ = c()
        d = idata(it)
        emit("ICJ", {"seed": sd(d + 4), "q": u32(d), "rq": s32(rec + 0x30), "fi": s32(d + 0x28)})

    def on_icx(v):
        def f():
            t = thn()
            if t not in cur:
                return
            it = cur.pop(t)[0]
            emit("ICX", {"ret": v, "seed": iseed(it), "q": u32(idata(it)), "fi": s32(idata(it) + 0x28)})
        return f

    Bp(0x00557450, on_ic0)
    Bp(0x0055757B, on_icq)
    for a, k in ((0x005566B0, "unique"), (0x005C2940, "set"), (0x005C21A0, "rare"), (0x005565E0, "magic"),
                 (0x005C2AD0, "superior"), (0x00556E80, "normal"), (0x00556D80, "normal0"), (0x005C2FB0, "low"),
                 (0x00556F30, "normalcase"), (0x005C21D0, "crafted")):
        Bp(a, on_bld(k))
    Bp(0x005566B0, on_umade)
    Bp(0x00556983, on_ur)
    Bp(0x005569AD, on_upk)
    Bp(0x00556942, on_unone)
    Bp(0x005C26AF, on_spk)
    Bp(0x005C26D0, on_sr)
    Bp(0x005C270D, on_srow)
    Bp(0x0065FEC0, on_props)
    Bp(0x005576EF, on_bret("unique"))
    Bp(0x00557896, on_bret("set"))
    for k, a_has, a_ver, a72, a73, w72, w72r, w73 in ((3, 0x005576FF, 0x0055770B, 0x0055771D, 0x0055772B,
                                                       0x00557746, "esi", 0x00557765),
                                                      (2, 0x005578A6, 0x005578B2, 0x005578C4, 0x005578D2,
                                                       0x005578EC, "eax", 0x0055790A)):
        Bp(a_has, on_dur(k, "has", "eax"))
        Bp(a_ver, on_dur(k, "ver", "eax", 0xFFFF))
        Bp(a72, on_dur(k, "s72", "eax"))
        Bp(a73, on_dur(k, "s73", "eax"))
        Bp(w72, on_dur(k, "w72", w72r))
        Bp(w73, on_dur(k, "w73", "eax"))
    Bp(0x005573F0, on_fb("rare", "esi"))
    Bp(0x00557380, on_fb("magic", "ebx"))
    Bp(0x00557320, on_fb("superior", "esi"))
    Bp(0x005572A0, on_fb("normal", "eax"))
    Bp(0x00557943, on_icj)
    Bp(0x00557A1C, on_icx(1))
    Bp(0x00557A27, on_icx(0))
    Bp(0x00557482, on_icx(0))
    gdb.write("UNIQUES logger armed\n")


_uniques_main()
