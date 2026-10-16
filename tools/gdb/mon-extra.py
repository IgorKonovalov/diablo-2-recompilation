# gdb Python logger for plan 0038 batch H4b (monsters-b): the extension of tools/gdb/mon-stats.gdb. Sourced after
# tools/gdb/mon-stats.py; it adds tags only and leaves every older tag unchanged, so the existing checkers
# (tools/monspawn.py, tools/monstats.py, tools/monpool.py, tools/collision.py, tools/drlg.py) read its logs as before.
# One line per event, "TAG {json}". Addresses refer to the pinned game.exe (image base 0x400000). Checked by
# tools/sweep_h4b.py. See docs/findings/monsters/0003-special-monsters.md and 0004-stats.md (sections "Plan 0038
# batch H4b").
#
# Skill lists (unit +0xA8; first entry +0x04; an entry: Skills record pointer +0x00, next +0x04, level +0x28; the id is
# (record - DataTables(+0xB98)) / 0x23C):
#   SIK  0x00574137 MonStatsInit right after the eight-slot skill loop (0x005740E0..0x00574135): unit, class, the
#        skill-bonus word [ebp-0x1C] of the MonPlayerBonus record, game difficulty byte +0x6D, skills [[id, level]]
#   HSK  after a flag-1 handler call of mod 26 (teleport) or 30 (aura) (0x005A2155 / 0x005A21AE, after its call
#        0x005A2153 / 0x005A21AC): mod, unit, skills
#   AURS UModAura's UnitSkillAdd calls: 0x005A17AF (row path: unit EDI, skill EDX, level [esp], row ESI / 20) and
#        0x005A175C (class 704: skill EDX, level [esp])
# Restores:
#   RS0  0x005A4440 SpecialMonRestore entry: ECX, EDX, return address, the nine stack arguments, the nine saved mods
#        (bytes at the ninth argument)
#   RS1  0x005A455D after its SpecialModsApply: unit (ESI), class, id, flags +0x16, mods, name seed, us
#   RS2  0x005A4571 after the name-seed write: name seed      RSX 0x005A4583 after the second aura call: the same as RS1
#   MR0  0x005A46E0 MinionRestore entry: ECX, EDX, return address, the five stack arguments, the saved mods (5th arg)
#   MRH  0x005A4815 / 0x005A4834 each handler call (flag 0): unit, mod EDX, handler EAX
#   MRX  0x005A483E the exit: unit, class, id, flags, mods, us
# MonMakeSpecial:
#   MMS0 0x005A4940 entry: game ECX, unit EDX (class, id, flags, mods, us), return address
# DRLG room bit 0x800000, the third writer:
#   HWT  0x0066E37E sub_0066E360_HiddenWarpTilesAdd's OR: room (EAX), +0x28 before, the level id (room +0x58 +0x1D0)
# Client names (sub_004AC870_ClientMonNameBuild, sub_004AD020_ClientMonModsApply; the client thread):
#   CTAB once at load: g_ClientUModHandlers 0x00724D78 (42 dwords), g_ChampionNameStr 0x006DA488 (5 pairs),
#        the always-list 0x006DA4C8 (4 dwords)
#   CMA  0x004AD020 entry: unit, class, id, flags +0x16, su +0x26, name seed +0x14, mods
#   CMH  0x004AD080 / 0x004AD0A5 each client handler call: unit, mod EDX, handler EAX, arg (flag 0x08 bit) [esp]
#   CNB  0x004AC870 builder entry: unit, mod EDX, special [esp+4], return address, class, id, flags, su, name seed
#   CNS  every call of STRTABLE_GetByIndex 0x00524A30 inside the builder: site, index ECX (low 16 bits)
#   CNT  every call of the name setter 0x0063E810 inside the builder: site, unit, the UTF-16 text at EDX
# Watchpoints (H4B_WATCH, comma list; x86 has four debug registers, one per watched dword or byte):
#   "title"   access on g_pUniqueNameTables UniqueTitle pointer 0x0096D488 and its count 0x0096D498 (2 registers)
#   "reg:L"   access on region L +0x2DC and +0x2E0 (monLvl, monLvl2), armed when region L is built (2 registers)
#   "spcw:L"  access on Levels[L] +0x2F (MonSpcWalk; 1 register), armed at the region init
#   WCH  {what, lid, pc (after the access), v}; WCHARM when armed
import json
import os
import struct

import gdb


def _monextra_main():
    inf = gdb.selected_inferior()
    DT_PTR = 0x00744304
    st = {"hd": {}}

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
        v = reg(n)
        return v - (1 << 32) if v & 0x80000000 else v

    def thn():
        t = gdb.selected_thread()
        return t.num if t else 0

    def us(u):
        return "%08x:%08x" % struct.unpack("<II", mem(u + 0x20, 8))

    def emit(tag, d):
        gdb.write("%s %s\n" % (tag, json.dumps(d, separators=(",", ":"))))

    def skills(u):
        sl = u32(u + 0xA8)
        if not sl:
            return None
        base = u32(u32(DT_PTR) + 0xB98)
        out, e, guard = [], u32(sl + 4), 0
        while e and guard < 64:
            r = u32(e)
            out.append([(r - base) // 0x23C if r else None, s32(e + 0x28)])
            e, guard = u32(e + 4), guard + 1
        return out

    def mon(u):
        if not u:
            return None
        d = {"u": u, "type": u32(u), "cls": s32(u + 4), "id": u32(u + 0xC)}
        md = u32(u + 0x14) if u32(u) == 1 else 0
        if md:
            d.update({"mf": u16(md + 0x16), "su": u16(md + 0x26), "ns": u16(md + 0x14), "mods": list(mem(md + 0x1C, 9))})
        try:
            d["us"] = us(u)
        except gdb.MemoryError:
            pass
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
                gdb.write("LOGERR mon-extra %r\n" % (e,))
            return False

    # --- skill lists -----------------------------------------------------------------------------------------------
    def on_sik():
        u, ebp = reg("esi"), reg("ebp")
        g = u32(ebp + 8)
        emit("SIK", {"u": u, "cls": s32(u + 4), "bonus": s32(ebp - 0x1C), "g6d": u8(g + 0x6D) if g else None,
                     "sk": skills(u)})

    Bp(0x00574137, on_sik)

    def on_hd0():
        st["hd"][thn()] = (reg("edi"), reg("esi"))

    def on_hdx():
        p = st["hd"].pop(thn(), None)
        if p is None:
            return
        u, m = p
        if m in (26, 30):
            emit("HSK", {"m": m, "u": u, "sk": skills(u)})

    for a in (0x005A2153, 0x005A21AC):
        Bp(a, on_hd0)
    for a in (0x005A2155, 0x005A21AE):
        Bp(a, on_hdx)

    def on_aurs(kind):
        def f():
            esp = reg("esp")
            d = {"k": kind, "u": reg("edi"), "skill": sreg("edx"), "lvl": s32(esp)}
            if kind == "row":
                d["row"] = reg("esi") // 20
            emit("AURS", d)
        return f

    Bp(0x005A17AF, on_aurs("row"))
    Bp(0x005A175C, on_aurs("704"))

    # --- restores and MonMakeSpecial -------------------------------------------------------------------------------
    def on_rs0():
        esp = reg("esp")
        a = list(struct.unpack("<9I", mem(esp + 4, 36)))
        saved = list(mem(a[8], 9)) if a[8] else None
        emit("RS0", {"ecx": reg("ecx"), "edx": reg("edx"), "ret": u32(esp), "a": a, "saved": saved})

    def on_rs(tag):
        def f():
            emit(tag, mon(reg("esi")))
        return f

    Bp(0x005A4440, on_rs0)
    Bp(0x005A455D, on_rs("RS1"))
    Bp(0x005A4571, on_rs("RS2"))
    Bp(0x005A4583, on_rs("RSX"))

    def on_mr0():
        esp = reg("esp")
        a = list(struct.unpack("<5I", mem(esp + 4, 20)))
        saved = list(mem(a[4], 9)) if a[4] else None
        emit("MR0", {"ecx": reg("ecx"), "edx": reg("edx"), "ret": u32(esp), "a": a, "saved": saved})

    def on_mrh():
        emit("MRH", {"u": reg("esi"), "m": reg("edx"), "h": reg("eax")})

    Bp(0x005A46E0, on_mr0)
    Bp(0x005A4815, on_mrh)
    Bp(0x005A4834, on_mrh)
    Bp(0x005A483E, on_rs("MRX"))

    def on_mms0():
        emit("MMS0", {"game": reg("ecx"), "unit": mon(reg("edx")), "ret": u32(reg("esp"))})

    Bp(0x005A4940, on_mms0)

    # --- the third writer of room bit 0x800000 ---------------------------------------------------------------------
    def on_hwt():
        r = reg("eax")
        lv = u32(r + 0x58)
        emit("HWT", {"room": r, "f28": u32(r + 0x28), "lid": s32(lv + 0x1D0) if lv else None})

    Bp(0x0066E37E, on_hwt)

    # --- client names ----------------------------------------------------------------------------------------------
    emit("CTAB", {"handlers": list(struct.unpack("<42I", mem(0x00724D78, 168))),
                  "champ": [list(p) for p in struct.iter_unpack("<II", mem(0x006DA488, 40))],
                  "always": list(struct.unpack("<4I", mem(0x006DA4C8, 16)))})

    def on_cma():
        emit("CMA", mon(reg("ecx")))

    def on_cmh():
        emit("CMH", {"u": reg("ebx"), "m": reg("edx"), "h": reg("eax"), "arg": u32(reg("esp"))})

    def on_cnb():
        esp = reg("esp")
        d = {"m": sreg("edx"), "special": u32(esp + 4), "ret": u32(esp)}
        d.update(mon(reg("ecx")) or {"u": 0})
        emit("CNB", d)

    def on_cns(site):
        def f():
            emit("CNS", {"site": site, "idx": reg("ecx") & 0xFFFF})
        return f

    def on_cnt(site):
        def f():
            p = reg("edx")
            raw = mem(p, 256) if p else b""
            txt = None
            if p:
                n = 0
                while n + 1 < len(raw) and (raw[n] or raw[n + 1]):
                    n += 2
                txt = raw[:n].decode("utf-16-le", "replace")
            emit("CNT", {"site": site, "u": reg("ecx"), "text": txt})
        return f

    Bp(0x004AD020, on_cma)
    Bp(0x004AD080, on_cmh)
    Bp(0x004AD0A5, on_cmh)
    Bp(0x004AC870, on_cnb)
    # every call site of 0x00524A30 and 0x0063E810 between 0x004AC870 and 0x004ACB76 (r2 `pd`, 2026-10-16)
    sites = {"s": [], "t": []}
    insn = mem(0x004AC870, 0x004ACB80 - 0x004AC870)
    for i in range(len(insn) - 5):
        if insn[i] == 0xE8:
            tgt = (0x004AC870 + i + 5 + struct.unpack("<i", insn[i + 1:i + 5])[0]) & 0xFFFFFFFF
            if tgt == 0x00524A30:
                sites["s"].append(0x004AC870 + i)
            elif tgt == 0x0063E810:
                sites["t"].append(0x004AC870 + i)
    for a in sites["s"]:
        Bp(a, on_cns(a))
    for a in sites["t"]:
        Bp(a, on_cnt(a))
    emit("CSITES", {"getbyindex": sites["s"], "setname": sites["t"]})

    # --- watchpoints -----------------------------------------------------------------------------------------------
    class Watch(gdb.Breakpoint):
        def __init__(self, addr, size, what, lid):
            spec = "*(unsigned %s *)0x%08X" % ({1: "char", 4: "int"}[size], addr)
            super().__init__(spec, gdb.BP_WATCHPOINT, gdb.WP_ACCESS, internal=True)
            self.silent = True
            self.what, self.lid, self.addr, self.size = what, lid, addr, size

        def stop(self):
            try:
                v = u8(self.addr) if self.size == 1 else u32(self.addr)
                emit("WCH", {"what": self.what, "lid": self.lid, "pc": int(gdb.parse_and_eval("$pc")) & 0xFFFFFFFF,
                             "v": v})
            except Exception as e:
                gdb.write("LOGERR mon-extra watch %r\n" % (e,))
            return False

    spec = [w.strip() for w in os.environ.get("H4B_WATCH", "").split(",") if w.strip()]
    wreg = {int(w.split(":")[1]) for w in spec if w.startswith("reg:")}
    wspc = {int(w.split(":")[1]) for w in spec if w.startswith("spcw:")}
    live = []
    if "title" in spec:
        for a, what in ((0x0096D488, "title-ptr"), (0x0096D498, "title-count")):
            try:
                live.append(Watch(a, 4, what, None))
                emit("WCHARM", {"what": what, "addr": a})
            except Exception as e:
                gdb.write("LOGERR mon-extra arm %s %r\n" % (what, e))
    rlive = []

    def on_regions_init():
        while rlive:
            rlive.pop().delete()
        lv = u32(u32(DT_PTR) + 0xC58)
        for lid in wspc:
            try:
                rlive.append(Watch(lv + 0x220 * lid + 0x2F, 1, "spcwalk", lid))
                emit("WCHARM", {"what": "spcwalk", "lid": lid, "addr": lv + 0x220 * lid + 0x2F})
            except Exception as e:
                gdb.write("LOGERR mon-extra arm spcwalk %r\n" % (e,))

    def on_region_built():
        r = reg("esi")
        lid = s32(r + 0x2C0)
        if lid in wreg:
            for off, what in ((0x2DC, "monlvl"), (0x2E0, "monlvl2")):
                try:
                    rlive.append(Watch(r + off, 4, what, lid))
                    emit("WCHARM", {"what": what, "lid": lid, "addr": r + off, "v": u32(r + off)})
                except Exception as e:
                    gdb.write("LOGERR mon-extra arm %s %r\n" % (what, e))

    Bp(0x005479C0, on_regions_init)
    Bp(0x00547B1A, on_region_built)
    gdb.write("MONEXTRA logger armed\n")


_monextra_main()
