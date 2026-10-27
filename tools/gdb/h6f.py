# gdb Python logger for plan 0038 batch H6f (hirelings, run:2026-10-27-sweep-hirelings): the hire paths that
# run:2026-10-16-hirelings left [I] in docs/findings/hirelings/0001-hirelings.md. Sourced by tools/gdb/h6f.gdb after
# tools/gdb/pilot.py, tools/gdb/vendors.py, tools/gdb/mon-pool.py and tools/gdb/hirelings.py (unchanged; their lines
# HBS/HBT/HSL/HRE/HHI/HHX/MIN/MSL/MSR/MSX/MRH/MCA/MCX/MFK are read with these). One line per event, "TAG {json}";
# addresses refer to the pinned game.exe (image base 0x400000). Every breakpoint only prints and continues.
#
#   OSH  0x00578BD3 NPC_OpenStore, the hire test (EDI = NpcRecord + 0x20, [ebp-8] the NPC class): cls, built
#        (+0x21), trader (+0x23), stock (+0x20)
#   CLN  0x004B5F0F / 0x004B11CE the client's hire list draw / mercenary init, STRTABLE_GetByIndex(ECX) of the name:
#        site, name (the entry's u16), idx (ECX); once per (site, name, idx) per game
#   HSV  0x00577104 HIRE_Hire: VENDOR_StockLevel(player level) returned (EAX): v
#   HQS  0x00577136 / 0x0057717A HIRE_Hire: QUESTRECORD_GetState(word 36 / word 2, bit 0) returned: word, r
#   HRF  0x005773B0 HIRE_Hire's refusal tail: line ([esp], the source line pushed), code ([esp+4])
#   HPG  0x0057728F PayGold call from HIRE_Hire: price ([esp]);  HPR 0x00577294 its return: r
#   GFM0 0x00579180 HIRE_GiveFreeMerc entry (ECX game, EDX player, [esp+4] seller): seller, vf, ret
#   GFMT 0x005791A5 its NpcRecord (EAX): rec, the 0x450-byte table (hex) or null
#   GFMP 0x005791D1 / 0x005791EE PETS_GetUnitOfType(player, 7, dead?) returned: dead (1 / 0), r
#   GFMK 0x005792C6 the picked entry (EDI, before the hired write; EAX = index << 4): i, name, seed, hired, listed
#   GFMX 0x0057934C its return
#   RBE  0x00577010 HIRE_RebuildIfEmpty entry ([esp+4] NpcRecord): ret, listed unhired count of its table
#   MCE  0x005774F0 MERC_Create entry ([esp+4] name, +8 seed, +0xC id, +0x10 class, +0x14 dead): ret
#   MCT  0x005775FF MERC_Create, the hire-table entry of the name (EAX): name, hired, listed;  MCT2 0x0057760C after
#   MCR  0x00577667 / 0x00577563 MERC_Create returns: merc (unit) or null
#   RMH  0x0056AAE3 D2S_ReadMercHeader's MERC_Create call: name, seed, id, class, dead (the pushed arguments)
#   RMD  0x0056ABF5 after its dead branch (ESI merc): flags (+0xC4), mode (+0x10), dead (the header's bit)
#   POD  0x005751A0 PETS_OnDeath entry (EDX player, [esp+4] unit): unit, ret;  PODT 0x005751FF the pet type (EAX)
#   PODN 0x00575251 / 0x00575254 the pet node's flags before / after the dead bit
#   RES0 0x00579C00 MERC_Resurrect entry (EDX player): gold, bank;  RESU 0x00579C81 the dead pet's unit (ESI): flags,
#        mode;  RESC 0x00579CA4 MERC_ResurrectCost returned (EAX) with the unit's stat 12;  RESP 0x00579CAE PayGold
#        returned;  RESF 0x00579D44 the refusal or done tail: line, code;  RESX 0x00579D59 exit: the unit's flags, mode,
#        stat 6, gold, bank
#   KX0  0x0057E990 the kill's experience award (ECX game, EDX killer, [esp+4] victim): killer, victim exp (stat 13)
#   KXG  0x0057EA28 the mercenary's gain from 0x0057E480 (EAX) for the merc (EBX), killer;  KXS 0x0057EA3C the gain
#        after the 86/256 scale when the killer is not the mercenary (EAX)
#   CEG0 0x0057E3F0 MERC_CapExpGain entry (EAX L, ECX unit, [esp+8] gain);  CEGX 0x0057E46C / 0x0057E474 return (EAX)
#   AX0  0x0057E860 MERC_AddExp entry (EAX gain, EDI merc, [esp+8] owner, [esp+0xC] L): gain, L, merc stat 12 and
#        13, owner stat 12, ret;  AXX 0x0057E97F its exit: merc stat 12 and 13
import json
import struct

import gdb


def _h6f_main():
    inf = gdb.selected_inferior()
    st = {"seen": set(), "mct": None, "res": None, "ax": None}

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

    def s16(a):
        return struct.unpack("<h", mem(a, 2))[0]

    def reg(n):
        return int(gdb.parse_and_eval("$" + n)) & 0xFFFFFFFF

    def sreg(n):
        v = reg(n)
        return v - (1 << 32) if v & 0x80000000 else v

    def emit(tag, d):
        gdb.write("%s %s\n" % (tag, json.dumps(d, separators=(",", ":"))))
        gdb.flush()

    def stat(u, sid):
        lst = u32(u + 0x5C) if u else 0
        if not lst:
            return None
        arr, n = u32(lst + 0x24), s16(lst + 0x28)
        if not arr or n <= 0 or n > 1024:
            return 0
        for k, v in struct.iter_unpack("<Ii", mem(arr, 8 * n)):
            if k == sid << 16:
                return v
        return 0

    def unit(u):
        return {"u": u, "type": u32(u), "cls": s32(u + 4), "id": u32(u + 0x0C)} if u else None

    class Bp(gdb.Breakpoint):
        def __init__(self, addr, fn):
            super().__init__("*0x%08X" % addr, internal=True)
            self.silent = True
            self.fn = fn

        def stop(self):
            try:
                self.fn()
            except Exception as e:  # never stop the game on a logger error; log it instead
                gdb.write("LOGERR h6f %r\n" % (e,))
            return False

    def on_game():
        st["seen"] = set()

    def on_osh():
        e = reg("edi")
        emit("OSH", {"cls": s32(reg("ebp") - 8), "stock": u8(e), "built": u8(e + 1), "trader": u8(e + 3)})

    def cln(site, nameptr):
        def f():
            name = u16(u32(nameptr()))
            idx = reg("ecx") & 0xFFFF
            k = (site, name, idx)
            if k in st["seen"]:
                return
            st["seen"].add(k)
            emit("CLN", {"site": site, "name": name, "idx": idx})
        return f

    def on_hsv():
        emit("HSV", {"v": sreg("eax")})

    def hqs(word):
        def f():
            emit("HQS", {"word": word, "r": sreg("eax")})
        return f

    def on_hrf():
        esp = reg("esp")
        emit("HRF", {"line": u32(esp), "code": u32(esp + 4)})

    def on_hpg():
        emit("HPG", {"price": s32(reg("esp"))})

    def on_hpr():
        emit("HPR", {"r": sreg("eax")})

    def on_gfm0():
        esp = reg("esp")
        emit("GFM0", {"seller": s32(esp + 4), "vf": u32(reg("ecx") + 0x70), "ret": u32(esp)})

    def on_gfmt():
        rec = reg("eax")
        t = u32(rec + 0x10) if rec else 0
        emit("GFMT", {"rec": rec, "tab": mem(t, 0x450).hex() if t else None})

    def gfmp(dead):
        def f():
            emit("GFMP", {"dead": dead, "r": reg("eax")})
        return f

    def on_gfmk():
        e = reg("edi")
        emit("GFMK", {"i": reg("eax") >> 4, "name": u16(e), "seed": u32(e + 4), "hired": u32(e + 8),
                      "listed": u32(e + 12)})

    def on_gfmx():
        emit("GFMX", {})

    def on_rbe():
        esp = reg("esp")
        rec = u32(esp + 4)
        t = u32(rec + 0x10) if rec else 0
        left = None
        if t:
            b = mem(t, 0x450)
            left = sum(1 for i in range(69) if struct.unpack_from("<I", b, 16 * i + 12)[0]
                       and not struct.unpack_from("<I", b, 16 * i + 8)[0])
        emit("RBE", {"ret": u32(esp), "rec": rec, "left": left})

    def on_mce():
        esp = reg("esp")
        emit("MCE", {"name": u16(esp + 4), "seed": u32(esp + 8), "id": u16(esp + 12), "cls": s32(esp + 16),
                     "dead": s32(esp + 20), "ret": u32(esp)})

    def on_mct():
        e = reg("eax")
        st["mct"] = e
        emit("MCT", {"name": u16(e), "hired": u32(e + 8), "listed": u32(e + 12)})

    def on_mct2():
        e, st["mct"] = st["mct"], None
        if e:
            emit("MCT2", {"name": u16(e), "hired": u32(e + 8), "listed": u32(e + 12)})

    def on_mcr():
        emit("MCR", {"merc": unit(reg("eax"))})

    def on_rmh():
        esp = reg("esp")
        emit("RMH", {"name": u16(esp), "seed": u32(esp + 4), "id": u16(esp + 8), "cls": s32(esp + 12),
                     "dead": u32(esp + 16)})

    def on_rmd():
        m = reg("esi")
        emit("RMD", {"merc": unit(m), "flags": u32(m + 0xC4), "mode": u32(m + 0x10), "dead": u32(reg("ebp") - 0xC)})

    def on_pod():
        esp = reg("esp")
        emit("POD", {"unit": unit(u32(esp + 4)), "ret": u32(esp)})

    def on_podt():
        emit("PODT", {"type": sreg("eax")})

    def podn(when):
        def f():
            emit("PODN", {"when": when, "flags": u32(reg("esi"))})
        return f

    def on_res0():
        p = reg("edx")
        st["res"] = {"p": p, "m": None}
        emit("RES0", {"gold": stat(p, 14), "bank": stat(p, 15)})

    def on_resu():
        m = reg("esi")
        if st["res"] is not None:
            st["res"]["m"] = m
        emit("RESU", {"merc": unit(m), "flags": u32(m + 0xC4), "mode": u32(m + 0x10), "L": stat(m, 12)})

    def on_resc():
        r = st["res"] or {}
        emit("RESC", {"cost": reg("eax"), "L": stat(r.get("m"), 12) if r.get("m") else None})

    def on_resp():
        emit("RESP", {"r": sreg("eax")})

    def on_resf():
        esp = reg("esp")
        emit("RESF", {"line": u32(esp), "code": u32(esp + 4)})

    def on_resx():
        r, st["res"] = st["res"] or {}, None
        m, p = r.get("m"), r.get("p")
        emit("RESX", {"flags": u32(m + 0xC4) if m else None, "mode": u32(m + 0x10) if m else None,
                      "hp": stat(m, 6) if m else None, "gold": stat(p, 14) if p else None,
                      "bank": stat(p, 15) if p else None})

    def on_kx0():
        esp = reg("esp")
        v = u32(esp + 4)
        emit("KX0", {"killer": unit(reg("edx")), "victim": unit(v), "vexp": stat(v, 13) if v else None})

    def on_kxg():
        emit("KXG", {"gain": sreg("eax"), "merc": unit(reg("ebx")), "killer": u32(reg("ebp") - 0x10)})

    def on_kxs():
        emit("KXS", {"gain": sreg("eax")})

    def on_ceg0():
        esp = reg("esp")
        emit("CEG0", {"L": sreg("eax"), "unit": unit(reg("ecx")), "gain": u32(esp + 8), "ret": u32(esp)})

    def on_cegx():
        emit("CEGX", {"r": reg("eax")})

    def on_ax0():
        esp = reg("esp")
        m, o = reg("edi"), u32(esp + 8)
        emit("AX0", {"gain": sreg("eax"), "L": s32(esp + 12), "merc": unit(m), "m12": stat(m, 12),
                     "m13": stat(m, 13), "o12": stat(o, 12), "ret": u32(esp)})

    def on_axx():
        m = reg("edi")
        emit("AXX", {"m12": stat(m, 12), "m13": stat(m, 13)})

    Bp(0x0052C312, on_game)
    Bp(0x00578BD3, on_osh)
    Bp(0x004B5F0F, cln("list", lambda: reg("ebp") - 0x18))
    Bp(0x004B11CE, cln("init", lambda: reg("ebp") - 0x14))
    Bp(0x00577104, on_hsv)
    Bp(0x00577136, hqs(36))
    Bp(0x0057717A, hqs(2))
    Bp(0x005773B0, on_hrf)
    Bp(0x0057728F, on_hpg)
    Bp(0x00577294, on_hpr)
    Bp(0x00579180, on_gfm0)
    Bp(0x005791A5, on_gfmt)
    Bp(0x005791D1, gfmp(1))
    Bp(0x005791EE, gfmp(0))
    Bp(0x005792C6, on_gfmk)
    Bp(0x0057934C, on_gfmx)
    Bp(0x00577010, on_rbe)
    Bp(0x005774F0, on_mce)
    Bp(0x005775FF, on_mct)
    Bp(0x0057760C, on_mct2)
    Bp(0x00577667, on_mcr)
    Bp(0x00577563, on_mcr)
    Bp(0x0056AAE3, on_rmh)
    Bp(0x0056ABF5, on_rmd)
    Bp(0x005751A0, on_pod)
    Bp(0x005751FF, on_podt)
    Bp(0x00575251, podn("before"))
    Bp(0x00575254, podn("after"))
    Bp(0x00579C00, on_res0)
    Bp(0x00579C81, on_resu)
    Bp(0x00579CA4, on_resc)
    Bp(0x00579CAE, on_resp)
    Bp(0x00579D44, on_resf)
    Bp(0x00579D59, on_resx)
    Bp(0x0057E990, on_kx0)
    Bp(0x0057EA28, on_kxg)
    Bp(0x0057EA3C, on_kxs)
    Bp(0x0057E3F0, on_ceg0)
    Bp(0x0057E46C, on_cegx)
    Bp(0x0057E474, on_cegx)
    Bp(0x0057E860, on_ax0)
    Bp(0x0057E97F, on_axx)
    gdb.write("H6F logger armed\n")


_h6f_main()
