# gdb Python logger for plan 0045 Phase 2 (skills and missiles, per-event reproduction): the event entry points of the
# Phase 1 review ruling (plan 0045 log, "the Phase 2 design"), with every seed they touch on entry and exit. Sourced by
# tools/gdb/skills.gdb after tools/gdb/pilot.py (the PLR/MON/CB/RL lines tools/d2pilot.py steers by). One line per
# breakpoint, "TAG {json}". Addresses refer to the pinned game.exe (image base 0x400000). Seeds "low:high" hex.
#
# A unit is {"u": pointer, "t": type, "c": class, "id": guid, "s": seed}; "st" (when given) maps a stat id (or
# "id:layer") to the value STATS_GetUnitStat returns (the full list StatList +0x48 when +0x10 bit 31 is set, else the
# base list +0x24; layer 0), zero values left out; "b328" the base-list stat 328 (STATS_GetUnitBaseStat).
# Every exit line is matched to its entry by ESP (the ESP at a `ret` equals the ESP at the entry) and carries "k", the
# entry's line number in this logger's own count ("n" on the entry line).
#
#   SST0/SST1  SKILLS_SrvStart 0x0056F640 (ECX game, EDX unit; id, lvl, noCost) and its rets: unit, frame, mode,
#              stats 6/8, target; exit eax, seed, 6/8
#   SDO0/SDO1  SKILLS_SrvDo 0x0056F7F0 (id, lvl, pay, item, effect) and its rets: as SST, plus Unit+0xC4
#   PAY0/PAY1  SKILLS_PayCost 0x0056BFE0 (ECX game, EDX unit; id, lvl) and its rets: stats 6, 8 (life, mana)
#   DLY        SKILLS_SetDelayState 0x0056EF90 entry (EDI unit, EAX the delay d): unit, d, frame
#   MC0/MC1    sub_0059FA30_MissileCreate (ECX game, EDX params): the 0x5C-byte block, the owner (stats 337, 141, 166,
#              156, 12, b328) and source seeds; exit: the missile (class, guid, seed, path speed/max/accel/counter,
#              16.16 position, direction, MissileData range/remaining/activate/flags, its stats), owner/source seeds
#   MCM        0x0064A8F0 (MissileCritRoll after SKILLS_GetMasteryBonus(…, 0, 2)) inside an MC: eax
#   MCB0/MCB1  sub_005C9290_MissCbReseedPathXPlusArg (ECX missile, EDX arg) and its ret 0x005C92F4: path +0x10,
#              missile seed, MissileData, path
#   SU0/SU1    sub_00552DF0_UnitSeedInit inside an MC or SP: 0x00552E2F parent seed pointer and value, 0x00552E55 the
#              parent after and the unit's seed
#   MF0/MF1    sub_005ADBB0_MissileDoFrame at 0x005ADC97 (before the pSrvDoFunc call) and 0x005ADCA9 (after it, eax),
#              windowed: only the missiles chosen at creation (at most SKILLS_WIN missiles a session, 8 at once; gdb
#              condition on $skw0..$skw7): frame, position, speed, counter, accel, max, direction, remaining, seed
#   MH0/MH1    MISSILE_HitUnit 0x005ADF10 (ECX game, EDX missile; unit, end) and its rets: the missile (stats), owner
#              and unit seeds; exit eax, seeds, missile stat 328
#   BD0/BD1    MISSILE_BuildDamage 0x005A89A0 (missile, unit, packet) and its ret: missile seed, unit class, packet
#   MA0/MA1    MISSILE_ApplyDamage 0x005AD730 and its ret 0x005AD8DE: missile, owner, defender seeds (boundary)
#   MHT0/MHT1  COMBAT_MeleeHitTest 0x0057EC10 and its rets: attacker, defender seeds (boundary, combat/0001 [C])
#   DQ0/DQ1    COMBAT_DeliverQueued 0x0057D4F0 and its rets (boundary)
#   AD0/AD1    COMBAT_ApplyDamage 0x0057C6C0 and its rets: packet at entry (boundary)
#   THR        0x005347B0 the to-hit debug stub: attacker (EDX), chance, roll, seed after the draw (rev 4: also
#              outside the logged spans, capped by SKILLS_CAP_THR)
#   DRR        0x005347C0 the defence debug stub: unit, chance, roll, label, seed after (rev 4: likewise, _DRR)
#   EVH/EVR    UNIT_DispatchEvent before (0x005C0C8E) and after (0x005C0C90) a handler call: fn, event, unit, other,
#              seeds and life (as tools/gdb/combat.py)
#   PH0/PH1    sub_0057D810_PreventHealHook (EDI attacker, ESI defender) and its ret: stat 117, seeds
#   STA        STATE_ApplyTimed 0x0056E970 (ECX arg block) inside an event: state, length, frame
#   REL        0x0056E132 (SKILLS_RollElemDamage's RangeB): caster seed, n, min
#   PF0/PFC/PFR/PF1  COMBAT_PrgFinisher 0x005D5220 entry, before (0x005D53F8, 0x005D544C) and after each srvprgfunc
#              call, its rets: the attacker's seed (ruling 1)
#   SP0/SP1    sub_0056D940_SpawnOwnedMonster (ECX game, EDX block) and its rets: owner; the created unit
#   SL0/SL1    sub_005C49E0_SummonSetLevel (ECX game, EDX owner; summon, lvl, skill level) and its rets: owner stat
#              12, the summon's stat 12 before and after (rev 2; rev 1 took ECX for the summon)
#   PA0/PA1    sub_00575D90_PetAdd and its ret
#   RSK0/RSK1  do 31's call of 0x005C4430 (0x005C4C7A: EDI the caster, ESI the summon) and its return (0x005C4C7F):
#              the caster's seed before and after, the summon's class (rev 3)
#   ARM0/ARM1  sub_005C8520_SkillDo146Armageddon and its rets: caster seed, SkillEntry+0x18 (logged whenever it fires)
#   MAS0/MAS1  sub_005A4F50_MonAttackStats (ECX unit, EDX mode) and its ret 0x005A5443: seed, stats (rev 4: the
#              elemental stats 48..66, 315..317 too, and the game's +0x6A/+0x6D/+0x70/+0x74 bytes)
#   CU0/CU1    (rev 4) SKILLS_CanUse 0x00647960 (stdcall unit, entry) called from the request handlers (return address
#              0x00549B0F, 0x00549B49, 0x00549BC6, 0x00549C11) and its ten rets: the skill id, the entry's base level
#              (+0x28), item guid (+0x34) and charges (+0x38), the unit's stats 6, 8, its mode, the frame; exit eax
#   CUL        (rev 4) SKILLS_ManaOk's level bonus 0x00647589 inside a CU: EAX the bonus (0x00644180), EDI the base
#   CAP        once per kind when its cap is reached
import json
import os
import struct

import gdb


def _skills_main():
    inf = gdb.selected_inferior()
    DT_PTR = 0x00744304
    CAPS = {"sst": 6000, "sdo": 6000, "mc": 12000, "mh": 8000, "ev": 6000, "mas": 4000, "sp": 600, "thr": 20000, "drr": 20000, "msst": 2500,
            "msdo": 2500}
    for k in list(CAPS):
        v = os.environ.get("SKILLS_CAP_" + k.upper())
        if v:
            CAPS[k] = int(v)
    WIN = int(os.environ.get("SKILLS_WIN", "30"))
    UST = [6, 7, 8, 9, 12, 19, 117, 141, 156, 166, 337, 329, 330, 331, 332, 357, 68, 25, 21, 22, 23, 24, 159, 160]
    MST = [12, 19, 21, 22, 25, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 103, 104,
           106, 120, 121, 122, 141, 315, 316, 317, 326, 327, 328, 329, 330, 331, 332, 357]
    # rev 4: MonAttackStats' writes (19, 21, 22 and the elemental stats) and a summon's stats at creation
    MAST = [12, 19, 21, 22, 23, 24, 25, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 315,
            316, 317]
    SPST = [6, 7, 8, 9, 12, 19, 21, 22, 31, 36, 37, 39, 41, 43, 45, 100]
    LABELS = {0x006E1738: "block", 0x006E1730: "wblock", 0x006E1728: "dodge", 0x006E1720: "avoid", 0x006E1718: "evade"}
    st = {"game": 0, "n": {}, "capped": set(), "open": {}, "line": 0, "isc": None, "win": {}, "wins": 0, "depth": 0}

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

    def emit(tag, d):
        st["line"] += 1
        d["n"] = st["line"]
        gdb.write("%s %s\n" % (tag, json.dumps(d, separators=(",", ":"))))
        return st["line"]

    def sd(u):
        return "%08x:%08x" % struct.unpack("<II", mem(u + 0x20, 8)) if u else None

    def frame():
        g = st["game"]
        return u32(g + 0xA8) if g else None

    def isc_info():
        if st["isc"] is None:
            dt = u32(DT_PTR)
            st["isc"] = (u32(dt + 0xBCC), s32(dt + 0xBD4), u8(0x006CE270))
        return st["isc"]

    def stats(u, want):
        """{key: value} of the wanted stats as STATS_GetUnitStat returns them (layer 0; combat.py's reading)."""
        lst = u32(u + 0x5C) if u else 0
        if not lst:
            return {}
        full = u32(lst + 0x10) & 0x80000000
        if full:
            arr, n = u32(lst + 0x48), s16(lst + 0x4C)
        else:
            arr, n = u32(lst + 0x24), s16(lst + 0x28)
        if not arr or n <= 0 or n > 2048:
            return {}
        owner = u32(lst + 0x44)
        otype = u32(owner) if owner else None
        base, nrec, mask = isc_info()
        out = {}
        ws = set(want)
        for k, v in struct.iter_unpack("<Ii", mem(arr, 8 * n)):
            sid, lay = k >> 16, k & 0xFFFF
            if sid == 180 and 180 in ws and v:
                out["180:%d" % lay] = v
                continue
            if lay or sid not in ws:
                continue
            if full and owner and otype in (0, 1) and 0 <= sid < nrec:
                rec = base + sid * 0x144
                if u8(rec + 5) & mask:
                    mn = s32(rec + 0x2C)
                    if v < mn:
                        v = (mn << u8(rec + 0x18)) & 0xFFFFFFFF
                        v = v - (1 << 32) if v & 0x80000000 else v
            if v:
                out[str(sid)] = v
        return out

    def base_stat(u, sid):
        lst = u32(u + 0x5C) if u else 0
        if not lst:
            return 0
        arr, n = u32(lst + 0x24), s16(lst + 0x28)
        if not arr or n <= 0 or n > 2048:
            return 0
        for k, v in struct.iter_unpack("<Ii", mem(arr, 8 * n)):
            if k == sid << 16:
                return v
        return 0

    def stat_layer(u, sid, lay):
        """the value of (stat, layer) in the list stats() reads, without the min clamp (rev 4: a handler's stat)."""
        lst = u32(u + 0x5C) if u else 0
        if not lst:
            return 0
        full = u32(lst + 0x10) & 0x80000000
        if full:
            arr, n = u32(lst + 0x48), s16(lst + 0x4C)
        else:
            arr, n = u32(lst + 0x24), s16(lst + 0x28)
        if not arr or n <= 0 or n > 2048:
            return 0
        want = (sid << 16) | lay
        for k, v in struct.iter_unpack("<Ii", mem(arr, 8 * n)):
            if k == want:
                return v
        return 0

    def unit(u, want=None):
        if not u:
            return None
        t = u32(u)
        d = {"u": u, "t": t, "c": s32(u + 4), "id": u32(u + 0x0C), "m": u32(u + 0x10), "s": sd(u)}
        if want:
            d["st"] = stats(u, want)
        return d

    def path_info(m):
        p = u32(m + 0x2C)
        if not p:
            return None
        return {"x": u32(p), "y": u32(p + 4), "v": s32(p + 0x7C), "mx": s32(p + 0x84), "a": s32(p + 0x88),
                "cnt": s32(p + 0x8C), "dx": s32(p + 0x6A), "dy": s32(p + 0x6E), "x10": u16(p + 0x10),
                "f34": u32(p + 0x34), "tu": u32(p + 0x58)}

    def mdata(m):
        md = u32(m + 0x14)
        if not md:
            return None
        return {"act": s16(md + 8), "sk": s16(md + 0xA), "lv": s16(md + 0xC), "rng": s16(md + 0xE),
                "rem": s16(md + 0x10), "fl": u32(md + 0x14)}

    def take(kind):
        n = st["n"].get(kind, 0)
        if n >= CAPS.get(kind, 3000):
            if kind not in st["capped"]:
                st["capped"].add(kind)
                emit("CAP", {"k": kind, "n": n})
            return False
        st["n"][kind] = n + 1
        return True

    def opened(kind, esp, data):
        st["open"][(kind, esp)] = data
        st["depth"] += 1
        gdb.set_convenience_variable("sk_open", st["depth"])

    def closed(kind, esp):
        d = st["open"].pop((kind, esp), None)
        if d is not None:
            st["depth"] = max(0, st["depth"] - 1)
            gdb.set_convenience_variable("sk_open", st["depth"])
        return d

    def any_open():
        return st["depth"] > 0

    class Bp(gdb.Breakpoint):
        def __init__(self, addr, fn, cond=None):
            super().__init__("*0x%08X" % addr, internal=True)
            self.silent = True
            self.fn = fn
            if cond:
                self.condition = cond

        def stop(self):
            try:
                self.fn()
            except Exception as e:  # never stop the game on a logger error; log it instead
                gdb.write("LOGERR skills %r\n" % (e,))
            return False

    def on_game():
        st["game"] = reg("edi")
        st["isc"] = None

    # --- skill start and do --------------------------------------------------------------------------------------
    def skill_entry(kind, nargs):
        def f():
            esp = reg("esp")
            u = reg("edx")
            if not u:
                return
            t = u32(u)
            k2 = kind if t == 0 else "m" + kind
            if t not in (0, 1) or not take(k2):
                return
            args = list(struct.unpack("<%di" % nargs, mem(esp + 4, 4 * nargs)))
            n = emit(kind.upper() + "0", {"u": unit(u, [6, 8]), "a": args, "fr": frame(), "c4": u32(u + 0xC4),
                                          "ret": u32(esp)})
            opened(kind, esp, (n, u))
        return f

    def skill_exit(kind):
        def f():
            esp = reg("esp")
            d = closed(kind, esp)
            if not d:
                return
            n, u = d
            emit(kind.upper() + "1", {"k": n, "r": sreg("eax"), "s": sd(u), "st": stats(u, [6, 8]),
                                      "c4": u32(u + 0xC4), "fr": frame()})
        return f

    def on_pay0():
        if not any_open():
            return
        esp = reg("esp")
        u = reg("edx")
        n = emit("PAY0", {"u": u, "a": list(struct.unpack("<2i", mem(esp + 4, 8))), "st": stats(u, [6, 7, 8, 9])})
        st["open"][("pay", esp)] = (n, u)

    def on_pay1():
        d = st["open"].pop(("pay", reg("esp")), None)
        if d:
            emit("PAY1", {"k": d[0], "r": sreg("eax"), "st": stats(d[1], [6, 7, 8, 9])})

    def on_dly():
        emit("DLY", {"u": reg("edi"), "d": sreg("eax"), "fr": frame()})

    # --- missiles ------------------------------------------------------------------------------------------------
    def on_mc0():
        esp = reg("esp")
        p = reg("edx")
        blk = mem(p, 0x5C)
        owner, src = struct.unpack_from("<II", blk, 4)
        if not take("mc"):
            return
        o = unit(owner, UST) if owner else None
        if o:
            o["b328"] = base_stat(owner, 328)
        n = emit("MC0", {"p": blk.hex(), "o": o, "src": unit(src) if src and src != owner else None,
                         "fr": frame()})
        opened("mc", esp, (n, owner, src))

    def on_mcm():
        if any_open():
            emit("MCM", {"v": sreg("eax"), "u": reg("esi"), "s": sd(reg("esi"))})

    def on_mc1():
        esp = reg("esp")
        d = closed("mc", esp)
        if not d:
            return
        n, owner, src = d
        m = reg("eax")
        out = {"k": n, "m": None, "so": sd(owner) if owner else None, "ss": sd(src) if src else None}
        if m:
            mi = unit(m, MST)
            mi["b328"] = base_stat(m, 328)
            mi["path"] = path_info(m)
            mi["md"] = mdata(m)
            out["m"] = mi
            if st["wins"] < WIN:
                free = [k for k in range(8) if not st["win"].get(k)]
                if free:
                    st["win"][free[0]] = m
                    st["wins"] += 1
                    gdb.set_convenience_variable("skw%d" % free[0], m)
                    out["win"] = free[0]
        emit("MC1", out)

    def on_mcb0():
        if not any_open():
            return
        m, a = reg("ecx"), reg("edx")
        p = u32(m + 0x2C)
        n = emit("MCB0", {"m": m, "arg": a, "x10": u16(p + 0x10) if p else None, "s": sd(m), "md": mdata(m)})
        st["open"][("mcb", reg("esp"))] = (n, m)

    def on_mcb1():
        d = st["open"].pop(("mcb", reg("esp")), None)
        if d:
            emit("MCB1", {"k": d[0], "s": sd(d[1]), "md": mdata(d[1]), "path": path_info(d[1])})

    def on_su0():
        if not any_open():
            return
        u, p = reg("edi"), reg("esi")
        emit("SU0", {"u": u, "t": u32(u), "c": s32(u + 4), "p": p, "pre": "%08x:%08x" % (u32(p), u32(p + 4))})

    def on_su1():
        if not any_open():
            return
        u, p = reg("edi"), reg("esi")
        emit("SU1", {"u": u, "p": p, "post": "%08x:%08x" % (u32(p), u32(p + 4)), "s": sd(u), "u28": u32(u + 0x28)})

    def win_slot(m):
        for k, v in st["win"].items():
            if v == m:
                return k
        return None

    def on_mf0():
        m = reg("edi")
        if win_slot(m) is None:
            return
        rec = u32(u32(DT_PTR) + 0xB64) + s32(m + 4) * 0x1A4
        emit("MF0", {"m": m, "fr": frame(), "path": path_info(m), "md": mdata(m), "s": sd(m),
                     "do": s16(rec + 0xC)})

    def on_mf1():
        m = reg("edi")
        k = win_slot(m)
        if k is None:
            return
        r = sreg("eax")
        emit("MF1", {"m": m, "r": r, "path": path_info(m), "md": mdata(m), "s": sd(m)})
        if r == 2:
            st["win"][k] = None
            gdb.set_convenience_variable("skw%d" % k, 0)

    def on_free():
        # UnitFree 0x00555600 (ECX game, EDX unit): a windowed missile freed elsewhere leaves the window
        u = reg("edx")
        k = win_slot(u)
        if k is not None:
            emit("MFX", {"m": u})
            st["win"][k] = None
            gdb.set_convenience_variable("skw%d" % k, 0)

    def on_mh0():
        esp = reg("esp")
        m = reg("edx")
        un, end = u32(esp + 4), s32(esp + 8)
        if not take("mh"):
            return
        mi = unit(m, MST)
        mi["md"] = mdata(m)
        n = emit("MH0", {"m": mi, "d": unit(un, [6, 7, 156, 166]) if un else None, "end": end, "fr": frame()})
        opened("mh", esp, (n, m, un))

    def on_mh1():
        esp = reg("esp")
        d = closed("mh", esp)
        if not d:
            return
        n, m, un = d
        emit("MH1", {"k": n, "r": sreg("eax"), "sm": sd(m), "sd": sd(un) if un else None,
                     "m328": stats(m, [328]).get("328", 0), "md": mdata(m)})

    def on_bd0():
        if not any_open():
            return
        esp = reg("esp")
        m, un, p = u32(esp + 4), u32(esp + 8), u32(esp + 0xC)
        n = emit("BD0", {"m": m, "d": un, "sm": sd(m), "dc": s32(un + 4) if un else None, "dt": u32(un) if un else None})
        st["open"][("bd", esp)] = (n, m, p)

    def on_bd1():
        d = st["open"].pop(("bd", reg("esp")), None)
        if d:
            n, m, p = d
            emit("BD1", {"k": n, "p": mem(p, 0x70).hex(), "sm": sd(m)})

    def boundary(tag, kind, ua, ub, extra=None):
        def f0():
            if not any_open():
                return
            esp = reg("esp")
            a, b = ua(), ub()
            d = {"a": a, "b": b, "sa": sd(a), "sb": sd(b)}
            if extra:
                d.update(extra())
            n = emit(tag + "0", d)
            st["open"][(kind, esp)] = (n, a, b)

        def f1():
            d = st["open"].pop((kind, reg("esp")), None)
            if d:
                n, a, b = d
                emit(tag + "1", {"k": n, "sa": sd(a), "sb": sd(b), "r": sreg("eax")})
        return f0, f1

    def esp_arg(i):
        return lambda: u32(reg("esp") + 4 * i)

    def r_(n):
        return lambda: reg(n)

    def on_thr():
        a = reg("edx")
        # rev 4: also outside the logged spans (every to-hit roll, capped), so the chaining can add a unit's own
        # rolls between its skill events (part 1 review ruling (c))
        if not any_open() and not take("thr"):
            return
        esp = reg("esp")
        emit("THR", {"a": a, "c": s32(esp + 8), "r": s32(esp + 12), "sa": sd(a)})

    def on_drr():
        esp = reg("esp")
        u = u32(esp + 4)
        if not any_open() and not take("drr"):
            return
        emit("DRR", {"u": u, "ch": s32(esp + 8), "r": s32(esp + 12),
                     "lab": LABELS.get(u32(esp + 16), hex(u32(esp + 16))), "s": sd(u)})

    def on_evh():
        esp = reg("esp")
        u, o = u32(esp), u32(esp + 4)
        if not any_open() and not take("ev"):
            return
        par = u32(esp + 12)
        pk = u32(esp + 8)
        d = {"fn": reg("eax"), "e": reg("edx"), "u": unit(u, [6, 7, 8, 9]), "o": o, "par": par,
             "so": sd(o), "fr": frame()}
        # rev 4: the handler's own stat (record +0x0C = stat << 16 | layer) on the unit, the other unit's type, class
        # and stats 6, 7, and the packet's first 0x70 bytes
        d["sv"] = stat_layer(u, par >> 16, par & 0xFFFF) if par >> 16 < 0x400 else None
        d["ot"] = unit(o, [6, 7, 12]) if o else None
        if o and u32(o) == 1 and u32(o + 0x14):
            d["ot"]["mf"] = u16(u32(o + 0x14) + 0x16)        # MonsterData +0x16 (sub_005A0180's flag word)
        d["pk"] = mem(pk, 0x70).hex() if pk else None
        n = emit("EVH", d)
        st["open"].setdefault("ev", []).append((n, u, o))

    def on_evr():
        lst = st["open"].get("ev")
        if not lst:
            return
        n, u, o = lst.pop()
        emit("EVR", {"k": n, "r": sreg("eax"), "su": sd(u), "so": sd(o), "st": stats(u, [6, 7, 8, 9]),
                     "ost": stats(o, [6, 7]) if o else None})

    def on_ph0():
        a, d = reg("edi"), reg("esi")
        n = emit("PH0", {"a": a, "d": d, "s117": stats(a, [117]).get("117", 0) if a else 0, "sa": sd(a), "sd": sd(d),
                         "ta": u32(a) if a else None, "td": u32(d) if d else None, "dc": s32(d + 4) if d else None})
        st["open"][("ph", reg("esp"))] = (n, a, d)

    def on_ph1():
        d = st["open"].pop(("ph", reg("esp")), None)
        if d:
            emit("PH1", {"k": d[0], "sa": sd(d[1]), "sd": sd(d[2])})

    def on_sta():
        blk = reg("ecx")
        v = struct.unpack("<8i", mem(blk, 32))
        if not any_open() and v[7] not in (52, 121):
            return
        emit("STA", {"a": v[0] & 0xFFFFFFFF, "d": v[1] & 0xFFFFFFFF, "len": v[4], "stat": v[5], "val": v[6],
                     "state": v[7], "fr": frame()})

    def on_rel():
        if not any_open():
            return
        ebp = reg("ebp")
        emit("REL", {"u": reg("esi"), "s": sd(reg("esi")), "n": sreg("edx"), "min": s32(ebp + 8)})

    # --- the progressive finisher --------------------------------------------------------------------------------
    def on_pf0():
        esp = reg("esp")
        a = reg("edx")
        n = emit("PF0", {"a": a, "ecx": reg("ecx"), "arg": s32(esp + 4), "sa": sd(a), "fr": frame()})
        st["open"][("pf", esp)] = (n, a)
        st["pfa"] = a

    def on_pfc():
        a = st.get("pfa")
        if a:
            emit("PFC", {"fn": reg("eax"), "sa": sd(a)})

    def on_pfr():
        a = st.get("pfa")
        if a:
            emit("PFR", {"sa": sd(a), "r": sreg("eax")})

    def on_pf1():
        d = st["open"].pop(("pf", reg("esp")), None)
        if d:
            emit("PF1", {"k": d[0], "sa": sd(d[1]), "r": sreg("eax")})
            st["pfa"] = None

    # --- summons -------------------------------------------------------------------------------------------------
    def on_sp0():
        esp = reg("esp")
        b = reg("edx")
        if not take("sp"):
            return
        blk = mem(b, 0x28)
        o = struct.unpack_from("<I", blk, 4)[0]
        n = emit("SP0", {"blk": blk.hex(), "o": unit(o, [12]) if o else None, "fr": frame()})
        opened("sp", esp, (n, o))

    def on_sp1():
        d = closed("sp", reg("esp"))
        if not d:
            return
        n, o = d
        m = reg("eax")
        emit("SP1", {"k": n, "m": unit(m, SPST) if m else None, "so": sd(o) if o else None})

    def on_sl0():
        # rev 2: ECX is the game, the summon is the first stack argument (rev 1 read ECX as the summon)
        esp = reg("esp")
        o = reg("edx")
        a = list(struct.unpack("<3i", mem(esp + 4, 12)))
        m = a[0] & 0xFFFFFFFF
        n = emit("SL0", {"m": m, "ecx": reg("ecx"), "o": o, "a": a, "m12": stats(m, [12]).get("12", 0) if m else None,
                         "o12": stats(o, [12]).get("12", 0) if o else None})
        st["open"][("sl", esp)] = (n, m)

    def on_sl1():
        d = st["open"].pop(("sl", reg("esp")), None)
        if d:
            emit("SL1", {"k": d[0], "m12": stats(d[1], [12]).get("12", 0)})

    def on_rsk0():
        c, m = reg("edi"), reg("esi")
        st["rsk"] = (emit("RSK0", {"u": c, "s": sd(c), "m": m, "c": u32(m + 4) if m else None}), c)

    def on_rsk1():
        d = st.pop("rsk", None)
        if d:
            emit("RSK1", {"k": d[0], "s": sd(d[1])})

    def on_pa0():
        esp = reg("esp")
        n = emit("PA0", {"ecx": reg("ecx"), "edx": reg("edx"), "a": list(struct.unpack("<3I", mem(esp + 4, 12)))})
        st["open"][("pa", esp)] = n

    def on_pa1():
        n = st["open"].pop(("pa", reg("esp")), None)
        if n:
            emit("PA1", {"k": n})

    # --- Armageddon (not tier A; logged whenever it fires: ruling 1) ---------------------------------------------
    def on_arm0():
        esp = reg("esp")
        u = reg("edx")
        n = emit("ARM0", {"u": u, "s": sd(u), "a": list(struct.unpack("<2i", mem(esp + 4, 8))), "fr": frame()})
        st["open"][("arm", esp)] = (n, u)

    def on_arm1():
        d = st["open"].pop(("arm", reg("esp")), None)
        if d:
            emit("ARM1", {"k": d[0], "s": sd(d[1]), "r": sreg("eax")})

    # --- SKILLS_CanUse at the request (rev 4) ---------------------------------------------------------------------
    CU_RETS = (0x00549B0F, 0x00549B49, 0x00549BC6, 0x00549C11)

    def on_cu0():
        esp = reg("esp")
        if u32(esp) not in CU_RETS:        # the client's per-frame checks (0x004D9FC5, 0x0055C…) are not requests
            return
        u, e = u32(esp + 4), u32(esp + 8)
        if not u or not e:
            return
        rec = u32(e)
        n = emit("CU0", {"u": unit(u, [6, 8, 9]), "sk": s16(rec) if rec else None, "ret": u32(esp),
                         "bl": s32(e + 0x28), "it": s32(e + 0x34), "ch": s32(e + 0x38), "fr": frame()})
        st["cu"] = (n, esp, u)

    def on_cul():
        d = st.get("cu")
        if d:
            emit("CUL", {"k": d[0], "bonus": sreg("eax"), "base": sreg("edi")})

    def on_cu1():
        d = st.get("cu")
        if d and reg("esp") == d[1]:
            emit("CU1", {"k": d[0], "r": sreg("eax"), "s": sd(d[2])})
            st["cu"] = None

    # --- MonAttackStats ------------------------------------------------------------------------------------------
    def on_mas0():
        u, mode = reg("ecx"), sreg("edx")
        if not u or u32(u) != 1 or not take("mas"):
            return
        esp = reg("esp")
        g = st["game"]
        n = emit("MAS0", {"mode": mode, "u": unit(u, MAST), "fr": frame(),
                          "diff": u8(g + 0x6D) if g else None,
                          "g": [u8(g + 0x6A), u8(g + 0x6D), u32(g + 0x70), u32(g + 0x74)] if g else None})
        st["open"][("mas", esp)] = (n, u)

    def on_mas1():
        d = st["open"].pop(("mas", reg("esp")), None)
        if d:
            emit("MAS1", {"k": d[0], "s": sd(d[1]), "st": stats(d[1], MAST)})

    Bp(0x0052C312, on_game)
    Bp(0x0056F640, skill_entry("sst", 3))
    for a in (0x0056F6E8, 0x0056F7D0, 0x0056F7D9):
        Bp(a, skill_exit("sst"))
    Bp(0x0056F7F0, skill_entry("sdo", 5))
    for a in (0x0056F8BB, 0x0056FACF, 0x0056FAE4, 0x0056FAED):
        Bp(a, skill_exit("sdo"))
    Bp(0x0056BFE0, on_pay0)
    for a in (0x0056BFFC, 0x0056C040, 0x0056C0D5, 0x0056C0EE, 0x0056C109, 0x0056C148, 0x0056C15D):
        Bp(a, on_pay1)
    Bp(0x0056EF90, on_dly)
    Bp(0x0059FA30, on_mc0)
    for a in (0x0059FA4C, 0x0059FD20, 0x0059FED0):
        Bp(a, on_mc1)
    Bp(0x0064A8F0, on_mcm)
    Bp(0x005C9290, on_mcb0)
    Bp(0x005C92F4, on_mcb1)
    Bp(0x00552E2F, on_su0)
    Bp(0x00552E55, on_su1)
    for k in range(8):
        gdb.set_convenience_variable("skw%d" % k, 0)
    cond = " || ".join("$edi == $skw%d" % k for k in range(8))
    Bp(0x005ADC97, on_mf0, cond)
    Bp(0x005ADCA9, on_mf1, cond)
    Bp(0x00555600, on_free, " || ".join("$edx == $skw%d" % k for k in range(8)))
    Bp(0x005ADF10, on_mh0)
    for a in (0x005AE0D0, 0x005AE1DB, 0x005AE1E9):
        Bp(a, on_mh1)
    Bp(0x005A89A0, on_bd0)
    Bp(0x005A8C63, on_bd1)
    gdb.set_convenience_variable("sk_open", 0)
    for tag, kind, entry, rets, ua, ub, extra in (
            ("MA", "ma", 0x005AD730, (0x005AD8DE,), r_("edx"), esp_arg(1), None),
            ("MHT", "mht", 0x0057EC10, (0x0057EC6E, 0x0057ECB8, 0x0057ED44), r_("edx"), esp_arg(1), None),
            ("DQ", "dq", 0x0057D4F0, (0x0057D560, 0x0057D66D, 0x0057D683), r_("edx"), esp_arg(1), None),
            ("AD", "ad", 0x0057C6C0, (0x0057C6F5, 0x0057C73E, 0x0057C97B), r_("edx"), esp_arg(1),
             lambda: {"p": mem(u32(reg("esp") + 12), 0x70).hex()})):
        f0, f1 = boundary(tag, kind, ua, ub, extra)
        Bp(entry, f0, "$sk_open > 0")
        for a in rets:
            Bp(a, f1, "$sk_open > 0")
    Bp(0x005347B0, on_thr)
    Bp(0x005347C0, on_drr)
    Bp(0x005C0C8E, on_evh)
    Bp(0x005C0C90, on_evr)
    Bp(0x0057D810, on_ph0)
    Bp(0x0057D899, on_ph1)
    Bp(0x0056E970, on_sta)
    Bp(0x0056E132, on_rel, "$sk_open > 0")
    Bp(0x005D5220, on_pf0)
    for a in (0x005D53F8, 0x005D544C):
        Bp(a, on_pfc)
    for a in (0x005D53FA, 0x005D544E):
        Bp(a, on_pfr)
    for a in (0x005D54A3, 0x005D5874):
        Bp(a, on_pf1)
    Bp(0x0056D940, on_sp0)
    for a in (0x0056D99A, 0x0056DAA6):
        Bp(a, on_sp1)
    Bp(0x005C49E0, on_sl0)
    for a in (0x005C4A79, 0x005C4AEF):
        Bp(a, on_sl1)
    Bp(0x005C4C7A, on_rsk0)
    Bp(0x005C4C7F, on_rsk1)
    Bp(0x00575D90, on_pa0)
    Bp(0x00575E82, on_pa1)
    Bp(0x005C8520, on_arm0)
    for a in (0x005C85EB, 0x005C8734, 0x005C8779):
        Bp(a, on_arm1)
    Bp(0x00647960, on_cu0)
    Bp(0x00647589, on_cul)
    for a in (0x006479BC, 0x006479D5, 0x006479E8, 0x00647A0C, 0x00647A24, 0x00647A3E, 0x00647A53, 0x00647A6C,
              0x00647A85, 0x00647A8F):
        Bp(a, on_cu1)
    Bp(0x005A4F50, on_mas0)
    Bp(0x005A5443, on_mas1)
    emit("SKILLSLOG", {"rev": 4, "win": WIN, "caps": CAPS})
    gdb.write("SKILLS logger armed\n")


_skills_main()
