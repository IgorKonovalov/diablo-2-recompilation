# gdb Python logger for plan 0038 batch H6g (run:2026-10-27-sweep-player): the player/creation rows the plan 0034
# run did not reach. Sourced by tools/gdb/h6g.gdb after tools/gdb/player.gdb's files (pilot.py, uniques.py,
# props.py, d2s-io.py, player.py), whose lines it leaves unchanged. One line per event, "TAG {json}"; addresses refer
# to the pinned game.exe (image base 0x400000); every line carries "th" (the gdb thread number). Base stat entries
# are [stat, param, value] lists as player.py's "b".
#
# New character:
#   NCF   0x00569F8F after sub_00537970 (ECX = EDI = client) in NewCharFromStub: client +0x3D4 (NC0 has it at entry)
#   C3W   the writers of client +0x3D4 bit 0 (objdump scan of `[reg+0x3d4]` operands): 0x005397A3 `or [esi], 1`
#         (in sub_00539760_ClientAddPlayerToGame), 0x00537993 `or [ecx], 1` (sub_00537970), 0x00539594
#         `and [ebx], ~1`, 0x0053A3F0 `and [esi], ~1`: the site, the client and the word before the write
# Kill experience:
#   XKE   0x0057E9CF XP_OnMonsterKill's STATS_GetUnitBaseStat(monster, 13) return (EAX), the monster ([ebp+8]) id
# Attribute points (PLAYER_SpendStatPoint 0x00570D60, ECX unit, EDX which):
#   SP0   entry: unit, which, base entries 0..11 and stat 4
#   SPX   its returns 0x00570D9E (str), 0x00570DB0 (energy), 0x00570DD6 (dex), 0x00570DE8 (vit), 0x00570DF0 (refused):
#         the return site, EAX, the unit's base entries (ESI = unit at each)
# Skill points (0x00570080, ECX unit, EDX skill):
#   SKC   0x00570104 after GetUnitBaseStat(unit, 5 newskills): EAX newskills, the cost ([ebp-4]), the skill id (EDI)
#   AS0   0x00647110 SKILLS_AddSkill entry, player units only ([esp+4] unit type 0): skill id, return address, the
#         existing entry with that Skills record and item reference -1 (its level +0x28) or null, the Skills
#         record's maxlvl cell (+0x12C)
#   ASX   its returns 0x0064722C / 0x00647242 (appended), 0x00647271 (existing), 0x0064718F / 0x0064711F (none),
#         for an AS0 line of the thread: the site, EAX, the entry's level
#   SKX   0x0057011F after SKILLS_AddSkill in 0x00570080: EAX, newskills (base stat 5) now
# Belt (sub_0063C600_BeltFreeSlot, stdcall inv, item, out):
#   P63   0x0054D545 the 0x63 packet handler past its size test (EAX the packet): the item id ([eax+1])
#   BF0   0x0063C600 entry: inventory, the item's class and id, the return address
#   BFG   0x0063C6C9 after the belt grid lookup (EBX grid): the box count ([ebp-0x108]), the 16 boxes' item class
#         (or null)
#   BFX   0x0063C765 column path (ECX box, EDI column), 0x0063C785 first-free path (EAX box), 0x0063C750 none
# Death (sub_00535AB0_PlayerDeathExpLossGate, PLAYER_DeathExpLoss, the corpse):
#   DG0   0x00535AB0 the gate (ECX game, EDX player, [esp+4] killer): killer type, class, id, the killer's owner
#         unit type through monster data (not read: the owner test is logged by whether DL0 follows)
#   DL0   0x005359F0 PLAYER_DeathExpLoss (EAX game, [esp+4] unit): difficulty, base entries 12, 13
#   DLP   0x00535A4E: EDX DeathExpPenalty, ESI span T(L) - T(L-1), EAX stat 13
#   DLL   0x00535A5F: ESI loss (penalty x span / 100), EDI exp, EBX T(L-1)
#   DLC   0x00535A8A CLIENT_SetDeathExpLoss call: EDX the kept amount; DLW 0x00535A95 the stat-13 write: EDI new
#   DLX   0x00535A9B the common return: the unit's base entries 12, 13 ([ebp+8])
#   CC0   0x0057F814 PLAYER_CorpseCreate after CLIENT_GetDeathExpLoss: EAX v, the corpse (EDI) id and position
#   CCX   0x0057F875 the share written ([ebp-4] = EAX), before CLIENT_SetDeathExpLoss(0)
#   CP0   0x0057FB70 PLAYER_CorpsePickup (ECX game, EDX picker, [esp+4] corpse): picker id, corpse id, its owner test
#   CPS   0x0057FBC2 the corpse's stat 13 (EAX); CPA 0x0057FBDB the AddExperienceDirect call ([esp] value)
#   AED   0x0057EAB0 sub_0057EAB0_AddExperienceDirect (ECX game, EDX unit, [esp+4] value)
# The capped grant (sub_0058C5C0_ExpGrantCapped, ESI player, [esp+4] game):
#   EG0   entry: the player's base entries 12, 13, 30; EGS 0x0058C650 the grant after the cut (EBX), each loop pass;
#   EGX   0x0058C6C6: the base entries
# The Ancients' altar (sub_0058D310_A5Q5_AltarOperate; plan 0038 rows 2/29, lane h6ga):
#   AL0   0x0058D33F after the quest and altar-data fetch: ESI the quest record, EBX the altar data; quest +0x09 (active),
#         +0x0B (state), +0x0C (step), altar data +0x0C (town-portal count) and +0x4C (mode)
#   ALS   0x0058D361 / 0x0058D38F the send of message 0x4E22 (site "idle" / "active")
import json
import struct

import gdb


def _h6g_main():
    inf = gdb.selected_inferior()
    DT_PTR = 0x00744304
    pend = {}       # thread -> AS0 skill id while SKILLS_AddSkill is open for a player

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

    def entries(u):
        lst = u32(u + 0x5C)
        if not lst:
            return []
        arr, n = u32(lst + 0x24), s16(lst + 0x28)
        if not arr or n <= 0 or n > 1024:
            return []
        return [[k >> 16, k & 0xFFFF, v] for k, v in struct.iter_unpack("<Ii", mem(arr, 8 * n))]

    def some(u, ids):
        return [e for e in entries(u) if e[0] in ids]

    def pos(u):
        try:
            p = u32(u + 0x2C)
            return [u16(p + 2), u16(p + 6)] if p else None
        except gdb.MemoryError:
            return None

    def skill_rec(sid):
        dt = u32(DT_PTR)
        return u32(dt + 0xB98) + 0x23C * sid

    class Bp(gdb.Breakpoint):
        def __init__(self, addr, fn):
            super().__init__("*0x%08X" % addr, internal=True)
            self.silent = True
            self.fn = fn

        def stop(self):
            try:
                self.fn()
            except Exception as e:  # never stop the game on a logger error; log it instead
                gdb.write("LOGERR h6g %r\n" % (e,))
            return False

    # ---- the new character: client +0x3D4 after sub_00537970
    def on_ncf():
        c = reg("edi")
        emit("NCF", {"client": c, "c3d4": u32(c + 0x3D4)})

    def c3w(site, r):
        def f():
            c = reg(r)
            emit("C3W", {"site": site, "client": c, "before": u32(c + 0x3D4)})
        return f

    # ---- kill experience: the monster's base stat 13 as XP_OnMonsterKill reads it
    def on_xke():
        mon = u32(reg("ebp") + 8)
        emit("XKE", {"v": sreg("eax"), "mid": u32(mon + 0x0C) if mon else None, "mcls": s32(mon + 4) if mon else None})

    # ---- attribute points
    def on_sp0():
        u = reg("ecx")
        emit("SP0", {"unit": u, "which": sreg("edx"), "b": some(u, range(0, 12))})

    def spx(site):
        def f():
            u = reg("esi")
            emit("SPX", {"site": site, "eax": reg("eax"), "unit": u, "b": some(u, range(0, 12))})
        return f

    # ---- skill points
    def on_skc():
        emit("SKC", {"newskills": sreg("eax"), "cost": s32(reg("ebp") - 4), "skill": sreg("edi"), "unit": reg("esi")})

    def on_skx():
        u = reg("esi")
        e = reg("eax")
        emit("SKX", {"eax": e, "lvl": s32(e + 0x28) if e else None, "b5": some(u, (5,))})

    def on_as0():
        sp = reg("esp")
        u, sid = u32(sp + 4), s32(sp + 8)
        if not u or u32(u) != 0:
            return
        rec = skill_rec(sid) if 0 <= sid < 0x400 else 0
        ex = None
        sl = u32(u + 0xA8)
        e, guard = (u32(sl + 4) if sl else 0), 0
        while e and guard < 512:
            if u32(e) == rec and s32(e + 0x34) == -1:
                ex = {"e": e, "lvl": s32(e + 0x28)}
                break
            e, guard = u32(e + 4), guard + 1
        pend[thn()] = sid
        emit("AS0", {"unit": u, "skill": sid, "ra": u32(sp), "ex": ex,
                     "maxlvl": s32(rec + 0x12C) if rec else None})

    def asx(site):
        def f():
            sid = pend.pop(thn(), None)
            if sid is None:
                return
            e = reg("eax")
            emit("ASX", {"site": site, "skill": sid, "eax": e, "lvl": s32(e + 0x28) if e else None})
        return f

    # ---- belt
    def on_p63():
        emit("P63", {"item": u32(reg("eax") + 1)})

    def on_bf0():
        sp = reg("esp")
        it = u32(sp + 8)
        emit("BF0", {"inv": u32(sp + 4), "icls": s32(it + 4) if it else None, "iid": u32(it + 0x0C) if it else None,
                     "ra": u32(sp)})

    def on_bfg():
        g = reg("ebx")
        n = u8(reg("ebp") - 0x108)
        boxes = []
        if g:
            arr = u32(g + 0x0C)
            for k in range(16):
                it = u32(arr + 4 * k) if arr else 0
                boxes.append(s32(it + 4) if it else None)
        emit("BFG", {"grid": g, "n": n, "boxes": boxes})

    def bfx(kind):
        def f():
            if kind == "col":
                emit("BFX", {"path": "col", "box": reg("ecx"), "col": reg("edi")})
            elif kind == "free":
                emit("BFX", {"path": "free", "box": reg("eax")})
            else:
                emit("BFX", {"path": "none"})
        return f

    # ---- death and the corpse
    def on_dg0():
        k = u32(reg("esp") + 4)
        d = {"game": reg("ecx"), "unit": reg("edx"), "killer": k}
        if k:
            d.update({"ktype": u32(k), "kcls": s32(k + 4), "kid": u32(k + 0x0C)})
        emit("DG0", d)

    def on_dl0():
        g, u = reg("eax"), u32(reg("esp") + 4)
        emit("DL0", {"diff": u8(g + 0x6D), "unit": u, "b": some(u, (12, 13)) if u else None})

    def on_dlp():
        emit("DLP", {"pen": reg("edx"), "span": reg("esi"), "exp": reg("eax")})

    def on_dll():
        emit("DLL", {"loss": reg("esi"), "exp": reg("edi"), "t0": reg("ebx")})

    def on_dlc():
        emit("DLC", {"kept": sreg("edx")})

    def on_dlw():
        emit("DLW", {"new": reg("edi")})

    def on_dlx():
        u = u32(reg("ebp") + 8)
        emit("DLX", {"b": some(u, (12, 13)) if u else None})

    def on_cc0():
        c = reg("edi")
        emit("CC0", {"v": sreg("eax"), "corpse": c, "cid": u32(c + 0x0C), "xy": pos(c)})

    def on_ccx():
        emit("CCX", {"share": sreg("eax")})

    def on_cp0():
        c = u32(reg("esp") + 4)
        p = reg("edx")
        emit("CP0", {"picker": u32(p + 0x0C) if p else None, "corpse": c, "cid": u32(c + 0x0C) if c else None,
                     "xy": pos(c) if c else None})

    def on_cps():
        emit("CPS", {"v": sreg("eax")})

    def on_cpa():
        emit("CPA", {"v": s32(reg("esp"))})

    def on_aed():
        u = reg("edx")
        emit("AED", {"unit": u, "v": s32(reg("esp") + 4), "b": some(u, (12, 13)) if u else None})

    # ---- the capped grant
    def on_eg0():
        u = reg("esi")
        g = u32(reg("esp") + 4)
        emit("EG0", {"unit": u, "diff": u8(g + 0x6D), "b": some(u, (12, 13, 29, 30))})

    def on_egs():
        emit("EGS", {"grant": sreg("ebx")})

    def on_egx():
        u = reg("esi")
        emit("EGX", {"unit": u, "b": some(u, (12, 13, 29, 30))})

    def on_al0():
        q = reg("esi")
        a = reg("ebx")
        emit("AL0", {"q": q, "active": u8(q + 9), "state": u8(q + 0xB), "step": u8(q + 0xC), "portals": s32(a + 0xC),
                     "mode": s32(a + 0x4C)})

    def als(site):
        def f():
            emit("ALS", {"site": site})
        return f

    Bp(0x0058D33F, on_al0)
    Bp(0x0058D361, als("idle"))
    Bp(0x0058D38F, als("active"))
    Bp(0x00569F8F, on_ncf)
    for a, r in ((0x005397A3, "esi"), (0x00537993, "ecx"), (0x00539594, "ebx"), (0x0053A3F0, "esi")):
        Bp(a, c3w(a, r))
    Bp(0x0057E9CF, on_xke)
    Bp(0x00570D60, on_sp0)
    for a, s in ((0x00570D9E, "str"), (0x00570DB0, "energy"), (0x00570DD6, "dex"), (0x00570DE8, "vit"),
                 (0x00570DF0, "refused")):
        Bp(a, spx(s))
    Bp(0x00570104, on_skc)
    Bp(0x0057011F, on_skx)
    Bp(0x00647110, on_as0)
    for a, s in ((0x0064722C, "append"), (0x00647242, "append"), (0x00647271, "existing"), (0x0064718F, "none"),
                 (0x0064711F, "none")):
        Bp(a, asx(s))
    Bp(0x0054D545, on_p63)
    Bp(0x0063C600, on_bf0)
    Bp(0x0063C6C9, on_bfg)
    Bp(0x0063C765, bfx("col"))
    Bp(0x0063C785, bfx("free"))
    Bp(0x0063C750, bfx("none"))
    Bp(0x00535AB0, on_dg0)
    Bp(0x005359F0, on_dl0)
    Bp(0x00535A4E, on_dlp)
    Bp(0x00535A5F, on_dll)
    Bp(0x00535A8A, on_dlc)
    Bp(0x00535A95, on_dlw)
    Bp(0x00535A9B, on_dlx)
    Bp(0x0057F814, on_cc0)
    Bp(0x0057F875, on_ccx)
    Bp(0x0057FB70, on_cp0)
    Bp(0x0057FBC2, on_cps)
    Bp(0x0057FBDB, on_cpa)
    Bp(0x0057EAB0, on_aed)
    Bp(0x0058C5C0, on_eg0)
    Bp(0x0058C650, on_egs)
    Bp(0x0058C6C6, on_egx)
    gdb.write("H6G logger armed\n")


_h6g_main()
