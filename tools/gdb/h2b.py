# gdb Python logger for plan 0038 batch H2b (run:2026-10-20-sweep-items-chain): the game seed, unit seed and item seed
# around item creation, the ITEMS_SetSockets clamps, and the builder failure points of classic throwing weapons.
# Sourced by tools/gdb/items-h2b.gdb after tools/gdb/uniques.py, affixes.py, props.py and cube.py, before
# tools/gdb/tc-drops.gdb; it leaves their lines unchanged and shares no tag with them. One line per event,
# "TAG {json}" (tools/tc.py and tools/quality.py skip JSON lines). Addresses refer to the pinned game.exe (image base
# 0x400000), read with objdump (docs/findings/items/0004-uniques-sets.md § Plan 0038 batch H2b). Seeds "low:high" hex.
# Every line carries "th" (the gdb thread number).
#
#   GS0  0x00558D90 sub_00558D90_ItemCreate entry (ECX game, EDX record, [esp] return, [esp+4] arg): game seed
#        (game+0xD0), record item index (+0x14), record +0x2C (the seed-in-record switch), +0x48, +0x4C, game +0x70
#   GS1  0x0055532F in sub_00555230_SUnitCreate after sub_00552E90_ItemSeedInit (EBX type, 4 only; ESI unit, EDI game):
#        game seed, unit seed (Unit+0x20), Unit+0x28, item seed (ItemData+0x04) and start (+0x10)
#   GS2  0x00558E1F in ItemCreate after SUnitCreate returns (EAX unit, EBX game): the same fields
#   GS3  0x00558E53 the record-seed branch (taken only when arg or record +0x2C is non-zero)
#   GS4  0x00558E7E after it (EDI unit, EBX game): the same fields
#   GQ0  0x00557450 sub_00557450_ItemCreateByQuality entry (ECX game, [EDX] item): game seed, unit seed, item seed
#   GQJ  0x00557943 its join (ICJ), and GQX its returns 0x00557A1C / 0x00557A27 / 0x00557482: the same fields, from
#        the game and item GQ0 saw on this thread
#   SS0  0x0062BCB0 ITEMS_SetSockets entry ([esp+4] item, [esp+8] n): return, class, quality, n, stat-194 path below
#   SSP  0x0062BD05 after p = invwidth x invheight (EAX) and the cap min(p, 6) (ESI)
#   SSQ  0x0062BD79 after the quality switch: cap (ESI), n (EBX)
#   SSM  0x0062BD82 the ItemMaxSockets value (EDX) against the cap (ESI)
#   SSN  0x0062BD8F the cap after ItemMaxSockets (ESI), n (EBX)
#   SSW  0x0062BDC4 the write: value (EBX)
#   SSR  0x0062BDD2 the return (written or not)
#   MB0  0x00556673 ITEMS_BuildMagic after its two picks: prefix id (DI), suffix id (BX)
#   MBF  0x0055667D its failure return (both 0)
#   RNE  0x005C1A6E (sub_005C19A0_PickRareNameV0) / 0x005C1B7E (ITEMS_PickRareName): the candidate count (EDI)
#   RBF  0x005C1E71 ITEMS_BuildRareAffixes' failure return
#   OBJP the waypoint objects' positions for tools/d2pilot.py wpchain (tools/gdb/vendors.py's walk of Game+0x1520 on
#        the PLR address 0x0064EA90, at most every 0.5 s; the game from GAME_InitSeeds 0x0052C312, EDI), one line per
#        (class, level)
import json
import struct
import time

import gdb


def _h2b_main():
    inf = gdb.selected_inferior()
    cur = {}      # thread -> (game, item) while an ItemCreateByQuality call is open
    st = {"game": 0, "t": 0.0, "wps": set()}
    WP_CLASSES = {119, 145, 156, 157, 237, 238, 288, 323, 324, 398, 402, 429, 494, 496, 511, 539}   # d2pilot.py

    def mem(a, n):
        return bytes(inf.read_memory(a, n))

    def u32(a):
        return struct.unpack("<I", mem(a, 4))[0]

    def s32(a):
        return struct.unpack("<i", mem(a, 4))[0]

    def reg(n):
        return int(gdb.parse_and_eval("$" + n)) & 0xFFFFFFFF

    def thn():
        t = gdb.selected_thread()
        return t.num if t else 0

    def emit(tag, d):
        d["th"] = thn()
        gdb.write("%s %s\n" % (tag, json.dumps(d, separators=(",", ":"))))

    def sd(p):
        return "%08x:%08x" % struct.unpack("<II", mem(p, 8))

    def unit_fields(game, unit):
        d = {"gseed": sd(game + 0xD0) if game else None}
        if unit:
            d.update({"unit": unit, "utype": u32(unit), "cls": s32(unit + 4), "useed": sd(unit + 0x20),
                      "u28": u32(unit + 0x28)})
            idata = u32(unit + 0x14) if u32(unit) == 4 else 0
            if idata:
                d.update({"iseed": sd(idata + 4), "start": u32(idata + 0x10)})
        return d

    class Bp(gdb.Breakpoint):
        def __init__(self, addr, fn):
            super().__init__("*0x%08X" % addr, internal=True)
            self.silent = True
            self.fn = fn

        def stop(self):
            try:
                self.fn()
            except Exception as e:  # never stop the game on a logger error; log it instead
                gdb.write("LOGERR h2b %r\n" % (e,))
            return False

    def on_gs0():
        game, rec, esp = reg("ecx"), reg("edx"), reg("esp")
        emit("GS0", {"ret": u32(esp), "arg": u32(esp + 4), "game": game, "gseed": sd(game + 0xD0),
                     "rec": rec, "idx": s32(rec + 0x14), "r2c": u32(rec + 0x2C), "r48": u32(rec + 0x48),
                     "r4c": u32(rec + 0x4C), "exp": u32(game + 0x70)})

    def on_gs1():
        if reg("ebx") != 4:
            return
        emit("GS1", unit_fields(reg("edi"), reg("esi")))

    def on_gs2():
        emit("GS2", unit_fields(reg("ebx"), reg("eax")))

    def on_gs3():
        emit("GS3", {"r48": u32(reg("esi") + 0x48), "r4c": u32(reg("esi") + 0x4C)})

    def on_gs4():
        emit("GS4", unit_fields(reg("ebx"), reg("edi")))

    def on_gq0():
        game, it = reg("ecx"), u32(reg("edx"))
        cur[thn()] = (game, it)
        emit("GQ0", unit_fields(game, it))

    def on_gq(tag, end):
        def f():
            c = cur.get(thn())
            if not c:
                return
            d = unit_fields(*c)
            if end is not None:
                d["r"] = end
                cur.pop(thn(), None)
            emit(tag, d)
        return f

    def on_ss0():
        esp = reg("esp")
        it, n = u32(esp + 4), s32(esp + 8)
        d = {"ret": u32(esp), "it": it, "n": n}
        if it and u32(it) == 4:
            idata = u32(it + 0x14)
            d.update({"cls": s32(it + 4), "q": u32(idata) if idata else None})
        emit("SS0", d)

    def on_ssp():
        emit("SSP", {"p": reg("eax"), "cap": reg("esi")})

    def on_ssq():
        emit("SSQ", {"cap": reg("esi"), "n": reg("ebx")})

    def on_ssm():
        emit("SSM", {"maxs": reg("edx"), "cap": reg("esi")})

    def on_ssn():
        emit("SSN", {"cap": reg("esi"), "n": reg("ebx")})

    def on_ssw():
        emit("SSW", {"v": reg("ebx")})

    def on_ssr():
        emit("SSR", {})

    def on_mb0():
        emit("MB0", {"p": reg("edi") & 0xFFFF, "s": reg("ebx") & 0xFFFF})

    def on_mbf():
        emit("MBF", {})

    def on_rne(v):
        def f():
            it = u32(reg("ebp") + 8)
            d = {"v": v, "n": reg("edi")}
            if it and u32(it) == 4:
                d["iseed"] = sd(u32(it + 0x14) + 4)
            emit("RNE", d)
        return f

    def on_rbf():
        emit("RBF", {})

    def on_game():
        st["game"] = reg("edi")

    def on_plr():
        now = time.time()
        if now - st["t"] < 0.5 or not st["game"]:
            return
        st["t"] = now
        heads = struct.unpack("<128I", mem(st["game"] + 0x1520, 512))
        for u in heads:
            k = 0
            while u and k < 512:
                k += 1
                try:
                    cls = s32(u + 4)
                    sp = u32(u + 0x2C)
                    if cls in WP_CLASSES and sp:
                        room = u32(sp)
                        lid = u32(u32(u32(room + 0x10) + 0x58) + 0x1D0) if room and u32(room + 0x10) else None
                        if (cls, lid) not in st["wps"]:
                            st["wps"].add((cls, lid))
                            gdb.write("OBJP %s\n" % json.dumps({"unit": u, "cls": cls, "x": s32(sp + 0x0C),
                                                                "y": s32(sp + 0x10), "mode": u32(u + 0x10),
                                                                "lid": lid}, separators=(",", ":")))
                except gdb.MemoryError:
                    pass
                u = u32(u + 0xE4)

    Bp(0x0052C312, on_game)
    Bp(0x0064EA90, on_plr)
    Bp(0x00558D90, on_gs0)
    Bp(0x0055532F, on_gs1)
    Bp(0x00558E1F, on_gs2)
    Bp(0x00558E53, on_gs3)
    Bp(0x00558E7E, on_gs4)
    Bp(0x00557450, on_gq0)
    Bp(0x00557943, on_gq("GQJ", None))
    Bp(0x00557A1C, on_gq("GQX", 1))
    Bp(0x00557A27, on_gq("GQX", 0))
    Bp(0x00557482, on_gq("GQX", 0))
    Bp(0x0062BCB0, on_ss0)
    Bp(0x0062BD05, on_ssp)
    Bp(0x0062BD79, on_ssq)
    Bp(0x0062BD82, on_ssm)
    Bp(0x0062BD8F, on_ssn)
    Bp(0x0062BDC4, on_ssw)
    Bp(0x0062BDD2, on_ssr)
    Bp(0x00556673, on_mb0)
    Bp(0x0055667D, on_mbf)
    Bp(0x005C1A6E, on_rne(0))
    Bp(0x005C1B7E, on_rne(1))
    Bp(0x005C1E71, on_rbf)
    gdb.write("H2B logger armed\n")


_h2b_main()
