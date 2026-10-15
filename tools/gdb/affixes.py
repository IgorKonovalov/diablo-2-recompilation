# gdb Python logger for plan 0021 Phase 2 (affix selection): the affix builders as read in
# docs/findings/items/0005-affixes.md. Sourced by tools/gdb/affixes.gdb after tools/gdb/uniques.py and before
# tools/gdb/tc-drops.gdb, whose lines it leaves unchanged; its tags differ from the uniques.py tags, so
# tools/uniques.py reads these logs as before. One line per event, "TAG {json}". Addresses refer to the pinned
# game.exe (image base 0x400000). Seeds are "low:high" hex, always the item seed (ItemData+0x04). "ret" is the
# return address of the call being logged.
#
#   AF0  0x005C1560 ITEMS_PickMagicAffix entry (stdcall: item, needSpawnable, mustRoll, applyProps, isPrefix,
#        forcedId, autoGroup): the arguments, the item's quality, ilvl and version, its prefixes (+0x38) and
#        suffixes (+0x3E) so far, and the seed
#   AFC  0x005C1821 after the candidate scan: alvl [ebp+0x18], magic lvl [ebp-0x14], count [ebp-4], W [ebp-8], the
#        candidate ids (merged index + 1) from the list at [ebp-0x1020] ({id, rec} pairs; at most 511 stored)
#   AFX  0x005C183E after RNG_RangeOffset(seed, 0, W + 1): x (EAX), seed
#   AFR  the returns of ITEMS_PickMagicAffix (0x005C157E, 0x005C15CD, 0x005C189B, 0x005C18C1, 0x005C18D0): id (AX), seed
#   RN   0x005C1B95 after the rare name draw in ITEMS_PickRareName: prefix side (from the return address), n (EDI),
#        r (EAX), the candidate ids from [ebp-0x1008] (+1), seed
#   RNX  the returns of ITEMS_PickRareName (0x005C1BAD 0, 0x005C1BBB id): AX, seed
#   RC   0x005C1CB1 the rare affix count [ebp-0x20], seed
#   APR0 0x0065FEC0 sub_0065FEC0_ItemApplyProps entry from an affix builder (return 0x005C18B8 pick, 0x005C1E09 rare
#        prefix, 0x005C1E2C rare suffix, 0x005C2AA0 superior, 0x00557A11 automagic): mode, the record as a merged
#        affix id (or a QualityItems row for the superior call), seed
#   APR1 those return addresses: seed (the oracle's exit)
#   STF0 0x005C1260 ITEMS_RollStaffMods entry from a builder (return 0x0055669D magic, 0x005C1E3E rare, 0x005C2AAA
#        superior, 0x005C2F98 low, 0x00556E31 normal v0, 0x00556F5A normal: ITEMS_BuildNormal tail-jumps to it
#        at 0x00556F24, so it returns into sub_00556F30_ItemBuildNormalCase): seed
#   STF1 those return addresses: seed
#   STFC inside ITEMS_RollStaffMods, when the type's StaffMods class c (EDI at 0x005C1285) is < 7 and has skills:
#        c and firstSkill(c), the EAX that 0x006460F0(c, 0) returns at 0x005C128A
#   SUPD 0x005C2A2A each superior row draw (ESI), tried flag, seed; SUPT 0x005C2A4E the type test result (EAX)
#   LOWR 0x005C2D85 the low-quality row (EAX), the row count, seed
#   ETB0 0x00556CA0 sub_00556CA0_ItemRollEthereal entry (return 0x00557979), ETB1 0x00557979: seed (the ethereal
#        boundary; tagged ETH0/ETH1 before plan 0027 Phase 3, renamed so that tools/gdb/props.py's ETH0/ETHR/ETHX
#        can share a log with it: tools/gdb/items-chain.gdb)
#   SCK0 0x00556B60 sub_00556B60_ItemRollSockets entry (return 0x00557997), SCK1 0x00557997: seed
#   AV0  entry of a version-0 body (0x005C12F0 pick, 0x005C19A0 name, 0x005C1E80 rare): should never appear
import json
import struct

import gdb


def _affixes_main():
    inf = gdb.selected_inferior()
    stash = {}          # thread -> item of the open ITEMS_PickMagicAffix / ItemApplyProps / staff-mods call
    G_MAGIC = 0x0096CA7C
    G_QUALITY = 0x0096CC50
    PROPS_RET = {0x005C18B8: "pick", 0x005C1E09: "rare-p", 0x005C1E2C: "rare-s", 0x005C2AA0: "superior",
                 0x00557A11: "auto"}
    STAFF_RET = {0x0055669D: "magic", 0x005C1E3E: "rare", 0x005C2AAA: "superior", 0x005C2F98: "low",
                 0x00556E31: "normal0", 0x00556F5A: "normal"}

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

    def idata(it):
        return u32(it + 0x14)

    def iseed(it):
        return "%08x:%08x" % struct.unpack("<II", mem(idata(it) + 4, 8))

    def affix_id(rec):
        base = u32(G_MAGIC + 4)
        return (rec - base) // 0x90 + 1 if rec and base else None

    class Bp(gdb.Breakpoint):
        def __init__(self, addr, fn):
            super().__init__("*0x%08X" % addr, internal=True)
            self.silent = True
            self.fn = fn

        def stop(self):
            try:
                self.fn()
            except Exception as e:  # never stop the game on a logger error; log it instead
                gdb.write("LOGERR affixes %r\n" % (e,))
            return False

    def on_af0():
        esp = reg("esp")
        ret, it = u32(esp), u32(esp + 4)
        a = struct.unpack("<6i", mem(esp + 8, 24))
        stash[("af", thn())] = it
        d = idata(it)
        emit("AF0", {"ret": ret, "spawn": a[0], "must": a[1], "apply": a[2], "pre": a[3], "forced": a[4],
                     "auto": a[5], "q": u32(d), "ilvl": s32(d + 0x2C), "ver": u16(d + 0x30),
                     "p": list(struct.unpack("<3H", mem(d + 0x38, 6))), "s": list(struct.unpack("<3H", mem(d + 0x3E, 6))),
                     "seed": iseed(it)})

    def on_afc():
        ebp = reg("ebp")
        n = s32(ebp - 4)
        k = min(max(n, 0), 511)
        pairs = struct.unpack("<%dI" % (2 * k), mem(ebp - 0x1020, 8 * k)) if k else ()
        it = u32(ebp + 8)
        emit("AFC", {"alvl": s32(ebp + 0x18), "m": s32(ebp - 0x14), "n": n, "W": s32(ebp - 8),
                     "ids": [pairs[2 * i] + 1 for i in range(k)], "seed": iseed(it)})

    def on_afx():
        it = u32(reg("ebp") + 8)
        emit("AFX", {"x": sreg("eax"), "seed": iseed(it)})

    def on_afr():
        it = stash.pop(("af", thn()), None)
        emit("AFR", {"id": reg("eax") & 0xFFFF, "seed": iseed(it) if it else None})

    def on_rn():
        ebp = reg("ebp")
        n = sreg("edi")
        k = min(max(n, 0), 511)
        ids = struct.unpack("<%dI" % (2 * k), mem(ebp - 0x1008, 8 * k))[0::2] if k else ()
        it = u32(ebp + 8)
        emit("RN", {"n": n, "r": sreg("eax"), "ids": [i + 1 for i in ids], "seed": iseed(it)})

    def on_rn0():
        esp = reg("esp")
        stash[("rn", thn())] = u32(esp + 4)
        emit("RN0", {"pre": reg("ecx"), "seed": iseed(u32(esp + 4))})

    def on_rnx():
        it = stash.pop(("rn", thn()), None)
        emit("RNX", {"id": reg("eax") & 0xFFFF, "seed": iseed(it) if it else None})

    def on_rc():
        ebp = reg("ebp")
        emit("RC", {"count": s32(ebp - 0x20), "seed": iseed(reg("esi"))})

    def on_apr0():
        esp = reg("esp")
        ret = u32(esp)
        if ret not in PROPS_RET:
            return
        mode, it, rec = s32(esp + 4), u32(esp + 0xC), u32(esp + 0x10)
        stash[("pr", thn())] = it
        if PROPS_RET[ret] == "superior":
            qb = u32(G_QUALITY + 4)
            rid = (rec - qb) // 0x70 if qb else None
        else:
            rid = affix_id(rec)
        emit("APR0", {"k": PROPS_RET[ret], "mode": mode, "rec": rid, "seed": iseed(it)})

    def on_apr1():
        it = stash.pop(("pr", thn()), None)
        if it:
            emit("APR1", {"seed": iseed(it)})

    def on_stf0():
        ret = u32(reg("esp"))
        if ret not in STAFF_RET:
            return
        it = reg("ecx")
        stash[("st", thn())] = it
        emit("STF0", {"k": STAFF_RET[ret], "seed": iseed(it)})

    def on_stf1():
        it = stash.pop(("st", thn()), None)
        if it:
            emit("STF1", {"seed": iseed(it)})

    def on_stc0():
        if ("st", thn()) in stash:
            stash[("stc", thn())] = reg("edi")

    def on_stc1():
        c = stash.pop(("stc", thn()), None)
        if c is not None:
            emit("STFC", {"cls": c, "first": sreg("eax")})

    def on_supd():
        it = u32(reg("ebp") - 0x14)
        esi = reg("esi")
        emit("SUPD", {"row": esi, "tried": mem(reg("ebp") - 0x10 + esi, 1)[0] if esi < 10 else None,
                      "seed": iseed(it)})

    def on_supt():
        emit("SUPT", {"ok": reg("eax")})

    def on_lowr():
        it = reg("edi")
        emit("LOWR", {"row": reg("eax"), "n": s32(reg("esi")), "seed": iseed(it)})

    def on_x0(tag, want_ret, itreg):
        def f():
            if u32(reg("esp")) != want_ret:
                return
            it = reg(itreg) if itreg else None
            stash[(tag, thn())] = it
            emit(tag + "0", {"seed": iseed(it)})
        return f

    def on_x1(tag):
        def f():
            it = stash.pop((tag, thn()), None)
            if it:
                emit(tag + "1", {"seed": iseed(it)})
        return f

    def on_av0(k):
        def f():
            emit("AV0", {"k": k, "ret": u32(reg("esp"))})
        return f

    Bp(0x005C1560, on_af0)
    Bp(0x005C1821, on_afc)
    Bp(0x005C183E, on_afx)
    for a in (0x005C157E, 0x005C15CD, 0x005C189B, 0x005C18C1, 0x005C18D0):
        Bp(a, on_afr)
    Bp(0x005C1AB0, on_rn0)
    Bp(0x005C1B95, on_rn)
    for a in (0x005C1AE8, 0x005C1BAD, 0x005C1BBB):
        Bp(a, on_rnx)
    Bp(0x005C1CB1, on_rc)
    Bp(0x0065FEC0, on_apr0)
    for a in PROPS_RET:
        Bp(a, on_apr1)
    Bp(0x005C1260, on_stf0)
    for a in STAFF_RET:
        Bp(a, on_stf1)
    Bp(0x005C1285, on_stc0)
    Bp(0x005C128A, on_stc1)
    Bp(0x005C2A2A, on_supd)
    Bp(0x005C2A4E, on_supt)
    Bp(0x005C2D85, on_lowr)
    # ethereal: the item is in ESI at the call (0x00557972 mov esi,[edi]); sockets: in EDI (0x0055798F)
    Bp(0x00556CA0, on_x0("ETB", 0x00557979, "esi"))
    Bp(0x00557979, on_x1("ETB"))
    Bp(0x00556B60, on_x0("SCK", 0x00557997, "edi"))
    Bp(0x00557997, on_x1("SCK"))
    for a, k in ((0x005C12F0, "pick"), (0x005C19A0, "name"), (0x005C1E80, "rare")):
        Bp(a, on_av0(k))
    gdb.write("AFFIXES logger armed\n")


_affixes_main()
