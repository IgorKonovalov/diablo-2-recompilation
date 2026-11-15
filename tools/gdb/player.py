# gdb Python logger for plan 0034 Phase 2 (new character, starting items, experience, level-up):
# docs/findings/player/0001-creation.md. Sourced by tools/gdb/player.gdb after tools/gdb/uniques.py and
# tools/gdb/props.py (ItemCreateByQuality, ItemInitStats, the builders, ItemApplyProps, ethereal, sockets, the final
# lists) and tools/gdb/d2s-io.py (the save written and read), whose lines it leaves unchanged. One line per event,
# "TAG {json}". Addresses refer to the pinned game.exe (image base 0x400000). Seeds are "low:high" hex; "gs" is the
# game seed (Game+0xD0) at the event. Every line carries "th" (the gdb thread number).
#
# New character (sub_00569F80_NewCharFromStub; lines between NC0 and NCX belong to it, thread-local):
#   NC0   0x00569F80 entry (EAX client, EBX game): gs; game +0x6A, +0x6D (difficulty), +0x70 (expansion), +0x74
#         (ladder), +0x78 (item version), +0x7C (map seed); client class (+0x08), status (+0x0A), name (+0x0D),
#         act (+0x1AC), +0x3D4
#   NCU   0x00569FAC after SUnitCreate: the unit (EAX): type, class, id, unit seed (+0x20), +0x28, mode; gs
#   NCP   0x00569FB8 after sub_00569F20_PlayerUnitInit: the same, gs
#   NCS   0x00569FCD after the unit is sent to the client (0x00571F90): gs
#   NCB   0x00569FE4 after PLAYER_InitBaseStats: gs, the unit's base stat entries
#   NCI   0x00569FEE after PLAYER_GiveStartItems: gs
#   NCQ   0x0056A06C before QuestsPlayerJoin (0x00546270): gs, player data +0x70 (right skill) and +0x74 (left)
#   NCX   0x0056A077 after it: gs, the player as PUNIT (stats, skills, mouse skills, every item as UNIT)
#   SIC0  0x00534C70 sub_00534C70_StartItemCreate entry (EAX player): slot ([esp+8]), item index ([esp+0xC]), gs
#   CREC  0x00559DFC ITEMS_CreateForStore's ItemCreate call (EDX the 0x84-byte record): +0x00 source, +0x0C ilvl,
#         +0x14 index, +0x18, +0x28, +0x2A, +0x30 quality, +0x40, +0x80 flags; gs. CRECX 0x00559E01: the new item
#         as UNIT, gs
#   SICX  0x00534D4B its return: the item (ESI) as UNIT (item_singleskill and quantity applied), gs
#   ISL   0x00534EC8 the end of one copy in sub_00534D60_StartItemSlot: slot ([ebp+0xC]), copy ([ebp-8]), the item
#         (ESI) as UNIT after placement and durability, gs
# Experience and level-up (any time):
#   XK0   0x0057E990 XP_OnMonsterKill entry (ECX game, EDX killer, [esp+4] monster): gs, killer type/id/class, the
#         monster's type, class, id, base stat entries (12 level, 13 experience among them)
#         Plan 0065 Phase 0 (revision 2): "kxs" and "vxs", the killer's and the monster's states that are in the exp
#         mask, read as sub_0063A690_UnitHasExpState reads them (0x0063A130): the unit's stat list (+0x5C) with flag
#         0x80000000 at +0x10, its state bit array at +0x58, ANDed word by word with the mask array at data tables
#         (0x00744304) +0x144 over (+0xC4 states + 31) / 32 words; a list of state numbers, [] for none, null without
#         such a list.
#   XS*   plan 0065 Phase 0 (revision 2): sub_0057E7B0_XpCreditPlayer's steps for a monster killer (EAX the killer,
#         [ebp+0xC] the victim): XSO 0x0057E7DF MonsterOwner's result (EAX); XSK 0x0057E7E9 / XSV 0x0057E807
#         UnitHasExpState of the killer / the victim (EAX); XSKL 0x0057E7F8 / XSVL 0x0057E816 StatListFindFlag(…, 0x800)
#         (EAX, the list); XSL 0x0057E822 the list's owner type (EAX, sub_00625250_StatListOwnerType) and XSG
#         0x0057E82A its guid (EAX, sub_006252B0_StatListOwnerGuid); XSF 0x0057E835 the unit GameFindUnit returned
#         (EAX); XSR the returns 0x0057E846 (EAX, a player) and 0x0057E84B (none, r null). Each line: the unit's type, class, id.
#   XC0   0x0057E480 XP_Compute entry (EAX exp, EDI player level, EBX unit, [esp+4] game, [esp+8] monster level)
#   XCP   0x0057E4CE after XP_LevelDiffPenalty (EAX); XCR 0x0057E4D4 after XP_ApplyExpRatio (EAX);
#   XC85  0x0057E4E0 after GetUnitStat(unit, 85) (EAX); XCX the returns 0x0057E4FF (EAX), 0x0057E4AA (1),
#         0x0057E4BD (0)
#   XA0   0x0057E510 PLAYER_AddExperience entry (ESI player; [esp+4] game, [esp+8] old level, [esp+0xC] add):
#         the player's base entries; XAX at its returns 0x0057E58F / 0x0057E591: the base entries
#   LU0   0x00570880 PLAYER_LevelUp entry (ECX game, EDX unit): gs, unit seed (+0x20), +0x28, base entries;
#         LUM   the full maxima the refill reads: UnitGetMaxHp 0x00570935, UnitGetMaxMana 0x0057097B,
#         UnitGetMaxStamina 0x005709AD (EAX; base plus item bonuses);
#         LUX 0x00570A45 its return: the same. Between LU0 and LUX (and between NC0 and NCX), RNG enters every call
#         of the RNG functions (RNG_Step, RNG_Range, RNG_RangeB, RNG_RangePow2, RNG_RangePow2Plus, RNG_RangeOffset,
#         RNG_RandLoHi, sub_005BDFF0_ARoomSeedStep) on the thread: the function, the seed pointer (ECX), whether it is
#         the game seed or the unit's seed, and the return address
#   LCG   between LU0 and LUX (and between NC0 and NCX, the control: the item creations step), every execution of an LCG multiplier site (tools/gdb/lcg-sites.txt, 852 'mov reg,
#         0x6AC690C5' in .text; inlined steps included) on the thread: the site, gs, the unit seed
#   GL0   0x0057EB10 PLAYER_GrantLevel entry: ECX, EDX and the first two stack arguments as they are
# PUNIT = {"u", "cls", "id", "useed", "seed28", "b" (base stat entries), "skills" [[id, level, itemref, +0x08], ...],
#          "left"/"right" (skill list +0x08 / +0x0C entry ids), "pd70", "pd74", "items" [UNIT...]}
# UNIT  = as tools/gdb/cube.py, plus "body" (ItemData+0x44)
import json
import struct

import gdb


def _player_main():
    inf = gdb.selected_inferior()
    nc = {}        # thread -> {"game", "client", "unit"} while NewCharFromStub is open
    lu = {}        # thread -> {"game", "unit"} while PLAYER_LevelUp is open
    DT_PTR = 0x00744304
    RNG_FNS = {0x0045C370: "RNG_Step", 0x0045C390: "RNG_Range", 0x0045C3E0: "RNG_RangeB",
               0x00472210: "RNG_RangePow2", 0x00472240: "RNG_RangePow2Plus", 0x00472280: "RNG_RangeOffset",
               0x004BC500: "RNG_RandLoHi", 0x005BDFF0: "ARoomSeedStep"}

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

    def thn():
        t = gdb.selected_thread()
        return t.num if t else 0

    def emit(tag, d):
        d["th"] = thn()
        gdb.write("%s %s\n" % (tag, json.dumps(d, separators=(",", ":"))))

    def sd(p):
        return "%08x:%08x" % struct.unpack("<II", mem(p, 8))

    def cstr(a, n):
        return mem(a, n).split(b"\0")[0].decode("latin1")

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
                    sub.append([u32(node + 0x14), u32(node + 0x10), entries(node)])
                    node, guard = u32(node + 0x2C), guard + 1
        return {"b": entries(lst), "sub": sub}

    def unit(u):
        if not u:
            return None
        out = {"u": u, "type": u32(u), "cls": s32(u + 4), "id": u32(u + 0x0C), "mode": u32(u + 0x10),
               "useed": sd(u + 0x20), "seed28": u32(u + 0x28)}
        d = idata(u)
        if out["type"] == 4 and d:
            out.update({"q": u32(d), "seed": sd(d + 4), "start": u32(d + 0x10), "fl": u32(d + 0x18),
                        "fi": s32(d + 0x28), "ilvl": s32(d + 0x2C), "ver": u16(d + 0x30), "page": u8(d + 0x45),
                        "body": u8(d + 0x44),
                        "p": list(struct.unpack("<3H", mem(d + 0x38, 6))),
                        "s": list(struct.unpack("<3H", mem(d + 0x3E, 6))),
                        "rn": [u16(d + 0x32), u16(d + 0x34)], "auto": u16(d + 0x36)})
            try:
                path = u32(u + 0x2C)
                out["xy"] = [u32(path + 0x0C), u32(path + 0x10)] if path else None
            except Exception:  # noqa: BLE001
                out["xy"] = None
            out.update(lists(u))
        return out

    def skills(u):
        sl = u32(u + 0xA8)
        if not sl:
            return [], None, None
        base = u32(u32(DT_PTR) + 0xB98)

        def sid(e):
            if not e:
                return None
            r = u32(e)
            return (r - base) // 0x23C if r else None
        out, e, guard = [], u32(sl + 4), 0
        while e and guard < 512:
            out.append([sid(e), s32(e + 0x28), s32(e + 0x34), s32(e + 8)])
            e, guard = u32(e + 4), guard + 1
        return out, sid(u32(sl + 8)), sid(u32(sl + 0x0C))

    def items(u):
        inv = u32(u + 0x60)
        out = []
        if not inv:
            return out
        c, guard = u32(inv + 0x0C), 0
        while c and guard < 256:
            out.append(unit(c))
            d = idata(c)
            c, guard = (u32(d + 0x64) if d else 0), guard + 1
        return out

    def punit(u):
        sk, left, right = skills(u)
        pd = u32(u + 0x14)
        return {"u": u, "cls": s32(u + 4), "id": u32(u + 0x0C), "useed": sd(u + 0x20), "seed28": u32(u + 0x28),
                "b": lists(u)["b"], "skills": sk, "left": left, "right": right,
                "pd70": s32(pd + 0x70) if pd else None, "pd74": s32(pd + 0x74) if pd else None,
                "items": items(u)}

    def cur():
        return nc.get(thn())

    def gs():
        c = cur()
        return sd(c["game"] + 0xD0) if c else None

    class Bp(gdb.Breakpoint):
        def __init__(self, addr, fn, enabled=True):
            super().__init__("*0x%08X" % addr, internal=True)
            self.silent = True
            self.fn = fn
            self.enabled = enabled

        def stop(self):
            try:
                self.fn()
            except Exception as e:  # never stop the game on a logger error; log it instead
                gdb.write("LOGERR player %r\n" % (e,))
            return False

    rng_bps = []
    lcg_bps = []

    def rng_arm():
        on = bool(nc or lu)
        for b in rng_bps:
            if b.enabled != on:
                b.enabled = on
        on = bool(lu or nc)
        for b in lcg_bps:
            if b.enabled != on:
                b.enabled = on

    # ---- the new character
    def on_nc0():
        client, game = reg("eax"), reg("ebx")
        nc[thn()] = {"game": game, "client": client, "unit": None}
        rng_arm()
        emit("NC0", {"game": game, "client": client, "gs": sd(game + 0xD0), "g6a": u8(game + 0x6A),
                     "diff": u8(game + 0x6D), "exp": u32(game + 0x70), "ladder": u32(game + 0x74),
                     "iver": u16(game + 0x78), "map": u32(game + 0x7C), "cls": u8(client + 0x08),
                     "status": u16(client + 0x0A), "name": cstr(client + 0x0D, 16), "act": u8(client + 0x1AC),
                     "c3d4": u32(client + 0x3D4)})

    def unit_line(tag):
        def f():
            c = cur()
            if not c:
                return
            u = reg("eax") if tag == "NCU" else c["unit"]
            c["unit"] = u
            emit(tag, {"u": u, "type": u32(u), "cls": s32(u + 4), "id": u32(u + 0x0C), "useed": sd(u + 0x20),
                       "seed28": u32(u + 0x28), "mode": u32(u + 0x10), "gs": gs()})
        return f

    def gs_line(tag):
        def f():
            if cur():
                emit(tag, {"gs": gs()})
        return f

    def on_ncb():
        c = cur()
        if c:
            emit("NCB", {"gs": gs(), "b": lists(c["unit"])["b"]})

    def on_ncq():
        c = cur()
        if c:
            pd = u32(c["unit"] + 0x14)
            emit("NCQ", {"gs": gs(), "pd70": s32(pd + 0x70), "pd74": s32(pd + 0x74)})

    def on_ncx():
        c = nc.get(thn())
        if not c:
            return
        emit("NCX", {"gs": gs(), "p": punit(c["unit"])})
        nc.pop(thn(), None)
        rng_arm()

    def on_sic0():
        if cur():
            sp = reg("esp")
            emit("SIC0", {"player": reg("eax"), "slot": s32(sp + 8), "idx": s32(sp + 12), "gs": gs()})

    def on_crec():
        if not cur():
            return
        r = reg("edx")
        emit("CREC", {"src": u32(r), "ilvl": s32(r + 0x0C), "idx": s32(r + 0x14), "k18": s32(r + 0x18),
                      "w28": u16(r + 0x28), "ver": u16(r + 0x2A), "q": s32(r + 0x30), "row1": s32(r + 0x40),
                      "pre": list(struct.unpack("<3i", mem(r + 0x68, 12))),
                      "suf": list(struct.unpack("<3i", mem(r + 0x74, 12))), "rfl": u32(r + 0x80), "gs": gs()})

    def on_crecx():
        if cur():
            emit("CRECX", {"it": unit(reg("eax")), "gs": gs()})

    def on_sicx():
        if cur():
            emit("SICX", {"it": unit(reg("esi")), "gs": gs()})

    def on_isl():
        if cur():
            bp = reg("ebp")
            emit("ISL", {"slot": s32(bp + 0x0C), "copy": s32(bp - 8), "it": unit(reg("esi")), "gs": gs()})

    # ---- experience and level-up
    def exp_states(u):
        """The unit's states inside the exp mask, as 0x0063A130 tests them (read-only); None without a state list."""
        lst = u32(u + 0x5C)
        if not lst or not u32(lst + 0x10) & 0x80000000:
            return None
        arr = u32(lst + 0x58)
        dt = u32(DT_PTR)
        mask, n = u32(dt + 0x144), s32(dt + 0xC4)
        if not arr or not mask or n <= 0 or n > 4096:
            return None
        words = (n + 31) // 32
        a = struct.unpack("<%dI" % words, mem(arr, 4 * words))
        m = struct.unpack("<%dI" % words, mem(mask, 4 * words))
        return [32 * w + b for w in range(words) for b in range(32) if (a[w] & m[w]) >> b & 1]

    def on_xk0():
        game, killer, mon = reg("ecx"), reg("edx"), u32(reg("esp") + 4)
        d = {"game": game, "gs": sd(game + 0xD0), "killer": killer}
        if killer:
            d.update({"ktype": u32(killer), "kcls": s32(killer + 4), "kid": u32(killer + 0x0C),
                      "kxs": exp_states(killer)})
        if mon:
            d.update({"mtype": u32(mon), "mcls": s32(mon + 4), "mid": u32(mon + 0x0C), "mb": lists(mon)["b"],
                      "vxs": exp_states(mon)})
        emit("XK0", d)

    def tci(u):
        """[type, class, id] of a unit pointer, or None."""
        return [u32(u), s32(u + 4), u32(u + 0x0C)] if u else None

    def xs_unit(tag):
        def f():
            emit(tag, {"r": tci(reg("eax"))})
        return f

    def xs_val(tag):
        def f():
            emit(tag, {"r": reg("eax")})
        return f

    def on_xc0():
        sp = reg("esp")
        v = reg("eax")
        emit("XC0", {"exp": v - (1 << 32) if v & 0x80000000 else v, "clvl": reg("edi"), "unit": reg("ebx"), "mlvl": s32(sp + 8)})

    def eax_line(tag):
        def f():
            v = reg("eax")
            emit(tag, {"v": v - (1 << 32) if v & 0x80000000 else v})
        return f

    def const_line(tag, v):
        def f():
            emit(tag, {"v": v})
        return f

    def on_xa0():
        sp, p = reg("esp"), reg("esi")
        emit("XA0", {"unit": p, "old": s32(sp + 8), "add": u32(sp + 12), "cls": s32(p + 4), "b": lists(p)["b"]})

    def on_xax():
        p = reg("esi")
        if not p or u32(p) != 0:
            return
        emit("XAX", {"unit": p, "b": lists(p)["b"]})

    def on_lu0():
        game, u = reg("ecx"), reg("edx")
        lu[thn()] = {"game": game, "unit": u}
        rng_arm()
        emit("LU0", {"unit": u, "cls": s32(u + 4), "gs": sd(game + 0xD0), "useed": sd(u + 0x20),
                     "seed28": u32(u + 0x28), "b": lists(u)["b"]})

    def on_lux():
        c = lu.pop(thn(), None)
        if not c:
            return
        rng_arm()
        u = c["unit"]
        emit("LUX", {"unit": u, "gs": sd(c["game"] + 0xD0), "useed": sd(u + 0x20), "seed28": u32(u + 0x28),
                     "b": lists(u)["b"]})

    def lu_max(k):
        def f():
            if thn() in lu:
                emit("LUM", {"k": k, "v": reg("eax")})
        return f

    def on_gl0():
        emit("GL0", {"ecx": reg("ecx"), "edx": reg("edx"), "a1": s32(reg("esp") + 4), "a2": s32(reg("esp") + 8)})

    def on_rng(addr):
        name = RNG_FNS[addr]

        def f():
            t = thn()
            c = nc.get(t) or lu.get(t)
            if not c:
                return
            p = reg("ecx")
            u = c.get("unit")
            emit("RNG", {"fn": name, "p": p, "game": p == c["game"] + 0xD0,
                         "unit": bool(u) and p == u + 0x20, "seed": sd(p) if p else None,
                         "ret": u32(reg("esp")), "in": "nc" if t in nc else "lu"})
        return f

    Bp(0x00569F80, on_nc0)
    Bp(0x00569FAC, unit_line("NCU"))
    Bp(0x00569FB8, unit_line("NCP"))
    Bp(0x00569FCD, gs_line("NCS"))
    Bp(0x00569FE4, on_ncb)
    Bp(0x00569FEE, gs_line("NCI"))
    Bp(0x0056A06C, on_ncq)
    Bp(0x0056A077, on_ncx)
    Bp(0x00534C70, on_sic0)
    Bp(0x00559DFC, on_crec)
    Bp(0x00559E01, on_crecx)
    Bp(0x00534D4B, on_sicx)
    Bp(0x00534EC8, on_isl)
    Bp(0x0057E990, on_xk0)
    Bp(0x0057E480, on_xc0)
    Bp(0x0057E4CE, eax_line("XCP"))
    Bp(0x0057E4D4, eax_line("XCR"))
    Bp(0x0057E4E0, eax_line("XC85"))
    Bp(0x0057E4FF, eax_line("XCX"))
    Bp(0x0057E4AA, const_line("XCX", 1))
    Bp(0x0057E4BD, const_line("XCX", 0))
    Bp(0x0057E510, on_xa0)
    for a in (0x0057E58F, 0x0057E591):
        Bp(a, on_xax)
    Bp(0x00570880, on_lu0)
    Bp(0x00570A45, on_lux)
    Bp(0x00570935, lu_max("hp"))
    Bp(0x0057097B, lu_max("mana"))
    Bp(0x005709AD, lu_max("stamina"))
    Bp(0x0057EB10, on_gl0)
    # plan 0065 Phase 0: XpCreditPlayer's steps (revision 2)
    for a, f in ((0x0057E7DF, xs_unit("XSO")), (0x0057E7E9, xs_val("XSK")), (0x0057E7F8, xs_val("XSKL")),
                 (0x0057E807, xs_val("XSV")), (0x0057E816, xs_val("XSVL")), (0x0057E822, xs_val("XSL")),
                 (0x0057E82A, xs_val("XSG")), (0x0057E835, xs_unit("XSF")), (0x0057E846, xs_unit("XSR")),
                 (0x0057E84B, lambda: emit("XSR", {"r": None}))):
        Bp(a, f)
    for a in RNG_FNS:
        rng_bps.append(Bp(a, on_rng(a), enabled=False))

    def on_lcg(addr):
        def f():
            t = thn()
            c = lu.get(t) or nc.get(t)
            if c:
                u = c.get("unit")
                emit("LCG", {"at": addr, "in": "lu" if t in lu else "nc", "gs": sd(c["game"] + 0xD0),
                             "useed": sd(u + 0x20) if u else None})
        return f
    for line in open("tools/gdb/lcg-sites.txt"):
        line = line.strip()
        if line and not line.startswith("#"):
            a = int(line, 16)
            lcg_bps.append(Bp(a, on_lcg(a), enabled=False))
    gdb.write("PLAYER logger armed\n")


_player_main()
