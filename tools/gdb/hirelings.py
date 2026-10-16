# gdb Python logger for plan 0033 Phase 2 (hirelings): the hire table builds, every HIRELING_RollEntry, the hire,
# the mercenary's creation (fresh hire and from a save), its level and stats, and the magic find of a kill, as read
# in docs/findings/hirelings/0001-hirelings.md. Sourced by tools/gdb/hirelings.gdb after tools/gdb/pilot.py,
# tools/gdb/vendors.py (the NPC seed S, VSC0/VSC1, HB0/HBX, the NPC lines and the TICK heartbeat that
# tools/d2pilot.py npc steers by) and tools/gdb/mon-pool.py (MPS/MPR/MLV: the MonStatsInit level of the mercenary).
# One line per event, "TAG {json}". Addresses refer to the pinned game.exe (image base 0x400000). Seeds "low:high"
# hex; "S" is the NPC seed (Game+0x1D24 -> +0x08).
#
#   HBS  0x00576070 HIRE_BuildStock entry (ECX game, EDX NPC class, [esp+4] NpcRecord): cls, rec, hireBuilt (+0x21),
#        pHireTable (+0x10), S, ret
#   HBT  0x0057619B / 0x005761BD its two returns (after an HBS): cls, the 0x450-byte hire table (hex: 69 entries
#        {u16 name, u16 pad, u32 seed, u32 hired, u32 listed}), S
#   HSL  0x00576770 HIRE_SendList entry ([esp+4] NPC unit): cls, ret
#   HRE  HIRELING_RollEntry, one line at its return 0x00663A06 / 0x00663853 (entry 0x006637F0: ECX version flag, EDX
#        player; [esp+4] seed, [esp+8] act, [esp+0xC] difficulty, [esp+0x10] out): vf, plvl (the player's stat 12),
#        seed, act, diff, ret (the caller), r (EAX), out (15 dwords). The client's list window (ret 0x004B5EAC) rolls
#        its entries every frame: a line is written once per distinct (ret, vf, plvl, seed, act, diff) per game.
#   HHI  0x005770E0 HIRE_Hire entry (EDX player; [esp+4] NPC unit, [esp+8] name index): cls, name, plvl, gold (stat
#        14), bank (stat 15);  HHX 0x00577397 / 0x005773CB its returns: r (EAX), gold, bank
#   MIN  0x00573270 MERC_Init entry (EDX player; [esp+4] merc, [esp+8] id (i16), [esp+0xC] {u16 name, u32 seed at
#        +4}, [esp+0x10] dead): merc class and id, id, name, seed, dead, ret
#   MSL  0x005728C2 MERC_SetLevel after the level is settled (EDI merc, EBX L, [ebp+4] ret): merc, L, ret
#   MSR  0x005728FA its HIRELING_GetRecord result: row (record index) or null
#   MSX  0x00572B94 its return: the merc's base stat entries [stat, param, value] and skills [[skill, level], ...]
#   MRH  0x0056AA50 D2S_ReadMercHeader entry ([esp+4] the header): hdr (32 bytes hex), ret
#   MCA  0x0057754C MERC_Create, the classic act test: mact (EBX, HIRELING_GetAct of the name), pact (ECX), vf
#   MCX  0x0056AAE8 after D2S_ReadMercHeader's MERC_Create: merc (0 = not created), class, id
#   MFK  ITEMS_DropMagicFind (ESI killer) at its returns 0x005585FF / 0x00558603: killer type, class, id, own (the
#        killer's stat 80 as the game reads it, EAX at 0x005585E6), owner (unit at 0x005585ED: type, class, id; mf its
#        base stat 80, mffull the full list's, mfcall the game's read, EAX at 0x005585FB), r (EAX)
import json
import struct

import gdb


def _hirelings_main():
    inf = gdb.selected_inferior()
    DT_PTR = 0x00744304
    G_HIRE = 0x0096BDD0
    st = {"game": 0, "seen": set(), "roll": [], "hb": None, "msl": None, "mfk": {}}

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

    def sd(p):
        return "%08x:%08x" % struct.unpack("<II", mem(p, 8))

    def S(g=None):
        g = g or st["game"]
        if not g:
            return None
        c = u32(g + 0x1D24)
        return sd(c + 8) if c else None

    def base_stats(u):
        lst = u32(u + 0x5C) if u else 0
        if not lst:
            return []
        arr, n = u32(lst + 0x24), s16(lst + 0x28)
        if not arr or n <= 0 or n > 1024:
            return []
        return [[k >> 16, k & 0xFFFF, v] for k, v in struct.iter_unpack("<Ii", mem(arr, 8 * n))]

    def stat(u, sid):
        for s, p, v in base_stats(u):
            if s == sid and p == 0:
                return v
        return 0

    def skills(u):
        sl = u32(u + 0xA8)
        if not sl:
            return []
        base = u32(u32(DT_PTR) + 0xB98)
        out, e, guard = [], u32(sl + 4), 0
        while e and guard < 64:
            r = u32(e)
            out.append([(r - base) // 0x23C if r else None, s32(e + 0x28)])
            e, guard = u32(e + 4), guard + 1
        return out

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
                gdb.write("LOGERR hirelings %r\n" % (e,))
            return False

    def on_game():
        st["game"] = reg("edi")
        st["seen"] = set()

    def on_hbs():
        esp = reg("esp")
        g, rec = reg("ecx"), u32(esp + 4)
        st["game"] = g
        st["hb"] = (sreg("edx"), rec)
        emit("HBS", {"cls": sreg("edx"), "rec": rec, "built": u8(rec + 0x21), "tab": u32(rec + 0x10), "S": S(g),
                     "ret": u32(esp)})

    def on_hbt():
        if not st["hb"]:
            return
        cls, rec = st["hb"]
        st["hb"] = None
        t = u32(rec + 0x10)
        emit("HBT", {"cls": cls, "tab": mem(t, 0x450).hex() if t else None, "built": u8(rec + 0x21), "S": S()})

    def on_hsl():
        esp = reg("esp")
        npc = u32(esp + 4)
        emit("HSL", {"cls": s32(npc + 4) if npc else None, "ret": u32(esp)})

    def on_hre0():
        esp = reg("esp")
        pl = reg("edx")
        st["roll"].append({"vf": reg("ecx"), "plvl": stat(pl, 12) if pl else None, "seed": u32(esp + 4),
                           "act": s32(esp + 8), "diff": s32(esp + 12), "out": u32(esp + 16), "ret": u32(esp)})

    def on_hrex():
        if not st["roll"]:
            return
        d = st["roll"].pop()
        key = (d["ret"], d["vf"], d["plvl"], d["seed"], d["act"], d["diff"])
        if d["ret"] == 0x004B5EAC:
            if key in st["seen"]:
                return
            st["seen"].add(key)
        out = d.pop("out")
        d["r"] = sreg("eax")
        d["o"] = list(struct.unpack("<15i", mem(out, 60)))
        emit("HRE", d)

    def on_hhi():
        esp = reg("esp")
        pl, npc = reg("edx"), u32(esp + 4)
        st["hhi"] = pl
        emit("HHI", {"cls": s32(npc + 4) if npc else None, "name": u16(esp + 8), "plvl": stat(pl, 12),
                     "gold": stat(pl, 14), "bank": stat(pl, 15)})

    def on_hhx():
        pl = st.pop("hhi", 0)
        emit("HHX", {"r": sreg("eax"), "gold": stat(pl, 14) if pl else None, "bank": stat(pl, 15) if pl else None})

    def on_min():
        esp = reg("esp")
        info = u32(esp + 12)
        emit("MIN", {"merc": unit(u32(esp + 4)), "id": s16(esp + 8), "name": u16(info) if info else None,
                     "seed": u32(info + 4) if info else None, "dead": s32(esp + 16), "ret": u32(esp)})

    def on_msl():
        m = reg("edi")
        st["msl"] = m
        emit("MSL", {"merc": unit(m), "L": sreg("ebx"), "ret": u32(reg("ebp") + 4)})

    def on_msr():
        r = reg("eax")
        base = u32(G_HIRE)
        emit("MSR", {"row": (r - base) // 0x118 if r else None})

    def on_msx():
        m, st["msl"] = st["msl"], None
        if not m:
            return
        emit("MSX", {"merc": unit(m), "b": base_stats(m), "sk": skills(m)})

    def on_mrh():
        esp = reg("esp")
        emit("MRH", {"hdr": mem(u32(esp + 4), 32).hex(), "ret": u32(esp)})

    def on_mca():
        emit("MCA", {"mact": sreg("ebx"), "pact": sreg("ecx"), "vf": u32(reg("edi") + 0x70)})

    def on_mcx():
        emit("MCX", {"merc": unit(reg("eax"))})

    def on_mfk0():
        k = reg("esi")
        st["mfk"] = {"killer": unit(k), "own": None, "owner": None}

    def on_mfk_own():
        st["mfk"]["own"] = sreg("eax")

    def full_stat(u, sid):
        """The value of a stat in a unit's full list (base plus item and state bonuses: StatList +0x48, s16 count
        +0x4C, when +0x10 bit 31 is set), else None."""
        lst = u32(u + 0x5C) if u else 0
        if not lst or not (u32(lst + 0x10) & 0x80000000):
            return None
        arr, n = u32(lst + 0x48), s16(lst + 0x4C)
        if not arr or n <= 0 or n > 1024:
            return None
        for k, v in struct.iter_unpack("<Ii", mem(arr, 8 * n)):
            if k == sid << 16:
                return v
        return 0

    def on_mfk_owner():
        o = reg("eax")
        if o:
            st["mfk"]["owner"] = dict(unit(o), mf=stat(o, 80), mffull=full_stat(o, 80))

    def on_mfk_ownval():
        if st.get("mfk", {}).get("owner") is not None:
            st["mfk"]["owner"]["mfcall"] = sreg("eax")

    def on_mfkx():
        d = st.get("mfk") or {}
        st["mfk"] = {}
        d["r"] = sreg("eax")
        emit("MFK", d)

    Bp(0x0052C312, on_game)
    Bp(0x00576070, on_hbs)
    Bp(0x0057619B, on_hbt)
    Bp(0x005761BD, on_hbt)
    Bp(0x00576770, on_hsl)
    Bp(0x006637F0, on_hre0)
    Bp(0x00663A06, on_hrex)
    Bp(0x00663853, on_hrex)
    Bp(0x005770E0, on_hhi)
    Bp(0x00577397, on_hhx)
    Bp(0x005773CB, on_hhx)
    Bp(0x00573270, on_min)
    Bp(0x005728C2, on_msl)
    Bp(0x005728FA, on_msr)
    Bp(0x00572B94, on_msx)
    Bp(0x0056AA50, on_mrh)
    Bp(0x0057754C, on_mca)
    Bp(0x0056AAE8, on_mcx)
    Bp(0x005585D0, on_mfk0)
    Bp(0x005585E6, on_mfk_own)
    Bp(0x005585ED, on_mfk_owner)
    Bp(0x005585FB, on_mfk_ownval)
    Bp(0x005585FF, on_mfkx)
    Bp(0x00558603, on_mfkx)
    gdb.write("HIRELINGS logger armed\n")


_hirelings_main()
