# gdb Python logger for plan 0037 Phase 2 (combat formulas, per-event reproduction): the server attack events of
# docs/findings/combat/0001-formulas.md with every seed snapshot and value oracle tools/combat.py check needs. Sourced
# by tools/gdb/combat.gdb after tools/gdb/pilot.py (the PLR/MON/CB/RL lines tools/d2pilot.py steers by). One line per
# breakpoint, "TAG {json}". Addresses refer to the pinned game.exe (image base 0x400000). Seeds "low:high" hex.
#
# Units are {"u": pointer, "t": type, "c": class, "id": unit id, "m": mode, "s": seed, "c4": Unit +0xC4 flags (bit 31
# read by COMBAT_DamagePercent; logger r3 on), "f": monster type flags
# (MonsterData +0x16), "st": {stat[:layer]: value}} where the stats are the read lists of the Phase 1 review brief,
# read as STATS_GetUnitStat 0x00625480 reads them (the full list StatList +0x48 when +0x10 bit 31 is set, else the base
# list +0x24; the ItemStatCost minimum of 0x00624F60 applied), zero values left out.
#
# Event lines (an "event" is one COMBAT_MeleeHitTest .. COMBAT_DeliverQueued, one MISSILE_ApplyDamage, or one
# MonAttackStats; only events whose attacker or defender is a player or a hireling are logged, per-kind caps below):
#   EV0   0x0057EC10 COMBAT_MeleeHitTest entry: k kind, ret, g {frame, diff, exp, players}, a/d units, arPct, rx
#   THB   0x0057DA28 (player attacker) PlayerBaseToHit = eax, DEF after +stat 32/33 = [ebp-8]
#   THV   0x0057DADB AR = edi, DEF = esi, pct = [ebp-4], alvl = [ebp-0x14], dlvl = [ebp-0x18]
#   THR   0x005347B0 (the to-hit debug stub, called at 0x0057DB72): c, r, attacker seed after the draw
#   DRB   0x0057DFE0 UnitBlockChance = eax;  DRM 0x0057E007 UnitIsMoving = eax
#   DRR   0x005347C0 (the defence debug stub): unit, chance, roll, label (block, wblock, dodge, avoid, evade), seed after
#   WBC   0x0057DD98 / 0x0057DED3 WeaponBlockChance = eax;  WBS 0x0057DDB0 / 0x0057DEEF the skill check value
#   BD0   0x0057B7D0 COMBAT_BuildDamage entry: packet (0x70 bytes hex), crit flag, srcdam, attacker seed
#   RPT   0x0057B44F two-hand test = eax;  RPM 0x0057B596 mastery damage = eax
#   RPE   0x0057B5B2 ed = ebx, min = [ebp+0xc], max = [ebp+0x10], s18 = [ebp+0x14], s17 = [ebp-4], phys in, srcdam,
#         weapon item class
#   BDC   0x0057B8CA mastery critical chance = esi
#   BD1   0x0057BD89 builder done: packet, attacker seed
#   RD0   0x0057C1E0 COMBAT_ApplyReductions entry: packet;  RDP 0x0057C2AF percent P = eax;  RD1 0x0057C3CA packet
#   AD0   0x0057C6C0 COMBAT_ApplyDamage entry: packet, doRed, both units' 6..11 and seeds;  AD1 at its returns
#   EVH   0x005C0C8E UNIT_DispatchEvent before the handler call: fn, event, unit, other, param, seeds, life;
#   EVR   0x005C0C90 after it: eax, seeds, life
#   LE1   0x0057C82B after COMBAT_Leech: attacker 6..9, seed, packet steal fields
#   MH0/MH1 0x0057C83A / 0x0057C844 around sub_005A4390_MonOnHitSkill (a monster attacker's hit; logger r6): seeds
#   STA   0x0056E970 STATE_ApplyTimed entry (ECX = arg block): state, length, stat, value, frame
#   DU0/DU1 0x0057D5F6 / 0x0057D5FB around COMBAT_DurabilityLoss;  KB0/KB1 0x0057D64A / 0x0057D64F around knockback;
#   GH0/GH1 0x0057D658 / 0x0057D65D (melee) and 0x005AD8D3 / 0x005AD8D8 (missile) around COMBAT_GetHit: seeds
#   PRG   0x005D3680 / 0x005D3790 / 0x005D3880 / 0x005D3970 (progressive-charge hooks) and 0x005D537B (their RNG_Step):
#         the event is dropped by the checker (Phase 1 review ruling 3)
#   EVX   COMBAT_DeliverQueued returns 0x0057D560 / 0x0057D66D / 0x0057D683 (matched by ESP): seeds and 6..11
#   MS0   0x005AD757 MISSILE_ApplyDamage after the owner lookup: missile, owner, defender, packet, seeds
#   MSX   0x005AD8DE its return
#   MAS0  0x005A4F50 MonAttackStats entry (ECX unit, EDX mode 4, 5 or 7..14); MAS1 its return 0x005A5443: seed, stats
#   RGN   0x00580610 a player's life regeneration tick (ESI unit) and 0x005A6920 a monster's regeneration event (EDX
#         unit; logger r7), only inside a window opened by an STA of state 62 (open
#         wounds) or 2 (poison) on a logged defender (gdb condition $esi == $combat_win, one window at a time): frame,
#         stat 6, 74, 7 and the base list's stat 74 (r8); at most 250 frames, 30 windows a session
#         (the tick's result is read at the next RGN: stat 6 after the write)
#   CAP   once per kind when its cap is reached
import json
import os
import struct

import gdb


def _combat_main():
    inf = gdb.selected_inferior()
    DT_PTR = 0x00744304
    HIRE = {271, 338, 359, 560, 561}
    CAPS = {"pa": 800, "ma": 500, "ha": 300, "mas": 300, "md": 300, "pm": 300, "o": 300}
    for k in list(CAPS):
        v = os.environ.get("COMBAT_CAP_" + k.upper())
        if v:
            CAPS[k] = int(v)
    READ = [0, 1, 2, 3, 6, 7, 8, 9, 10, 11, 12, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 31, 32, 33, 34, 35, 36, 37, 38,
            39, 40, 41, 42, 43, 44, 45, 46, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66,
            74, 100, 101, 103, 104, 106, 110, 111, 115, 116, 117, 118, 119, 120, 121, 122, 123, 124, 134, 135, 136, 141,
            142, 143, 144, 145, 146, 147, 148, 149, 153, 171, 182, 315, 316, 317, 325, 326, 327, 329, 330, 331, 332,
            333, 334, 335, 336, 337, 338, 339, 340, 357]
    READSET = set(READ)
    MAS_MODES = {4, 5, 7, 8, 9, 10, 11, 12, 13, 14}    # MonMode attack, cast, skill and sequence modes
    LAYERED = {179, 180, 348}
    LABELS = {0x006E1738: "block", 0x006E1730: "wblock", 0x006E1728: "dodge", 0x006E1720: "avoid", 0x006E1718: "evade"}
    st = {"game": 0, "cur": None, "n": {}, "capped": set(), "dq": {}, "ad": {}, "ev": [], "mas": {}, "ms": {},
          "win": {}, "wins": 0, "isc": None}

    def mem(a, n):
        return bytes(inf.read_memory(a, n))

    def u8(a):
        return mem(a, 1)[0]

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

    def sd(u):
        return "%08x:%08x" % struct.unpack("<II", mem(u + 0x20, 8)) if u else None

    def isc_info():
        if st["isc"] is None:
            dt = u32(DT_PTR)
            st["isc"] = (u32(dt + 0xBCC), s32(dt + 0xBD4), u8(0x006CE270))
        return st["isc"]

    def stats(u):
        """{key: value} of the READ stats as STATS_GetUnitStat returns them (layer 0, and every layer of LAYERED)."""
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
        for k, v in struct.iter_unpack("<Ii", mem(arr, 8 * n)):
            sid, lay = k >> 16, k & 0xFFFF
            if sid in LAYERED:
                if v:
                    out["%d:%d" % (sid, lay)] = v
                continue
            if lay or sid not in READSET:
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
        """STATS_GetUnitBaseStat 0x006253B0: the base list (StatList +0x24, s16 count +0x28), layer 0 (logger r8)."""
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

    def life(u):
        s = stats(u)
        return [s.get(str(k), 0) for k in (6, 7, 8, 9, 10, 11)]

    def frame(g=None):
        g = g or st["game"]
        return u32(g + 0xA8) if g else None

    def unit(u, full=True):
        if not u:
            return None
        t = u32(u)
        d = {"u": u, "t": t, "c": s32(u + 4), "id": u32(u + 0x0C), "m": u32(u + 0x10), "s": sd(u), "c4": u32(u + 0xC4)}
        if t == 1:
            md = u32(u + 0x14)
            if md:
                d["f"] = u8(md + 0x16)
        p = u32(u + 0x2C)
        if p and t in (0, 1):
            d["xy"] = [struct.unpack("<H", mem(p + 2, 2))[0], struct.unpack("<H", mem(p + 6, 2))[0]]
        if full:
            d["st"] = stats(u)
        return d

    def involved(u):
        if not u:
            return False
        t = u32(u)
        return t == 0 or (t == 1 and s32(u + 4) in HIRE)

    def is_player(u):
        return bool(u) and u32(u) == 0

    def gctx(g):
        return {"frame": u32(g + 0xA8), "diff": u8(g + 0x6D), "exp": u32(g + 0x70)}

    def take(kind):
        n = st["n"].get(kind, 0)
        if n >= CAPS.get(kind, 300):
            if kind not in st["capped"]:
                st["capped"].add(kind)
                emit("CAP", {"k": kind, "n": n})
            return False
        st["n"][kind] = n + 1
        return True

    def cur():
        return st["cur"]

    def pair_seeds(e):
        return {"sa": sd(e["a"]), "sd": sd(e["d"])}

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
                gdb.write("LOGERR combat %r\n" % (e,))
            return False

    def on_game():
        st["game"] = reg("edi")
        st["isc"] = None

    # --- melee events -------------------------------------------------------------------------------------------
    def on_ev0():
        esp = reg("esp")
        g, a, d = reg("ecx"), reg("edx"), u32(esp + 4)
        st["cur"] = None
        if not a or not d or not (involved(a) or involved(d)):
            return
        ta = u32(a)
        if ta == 0:
            kind = "pa"
        elif involved(a):
            kind = "ha"
        elif involved(d):
            kind = "ma"
        else:
            return
        if not take(kind):
            return
        st["game"] = g
        st["cur"] = {"a": a, "d": d, "k": kind}
        emit("EV0", {"k": kind, "ret": u32(esp), "g": gctx(g), "a": unit(a), "d": unit(d), "arPct": s32(esp + 8),
                     "rx": s32(esp + 12)})

    def on_thb():
        e = cur()
        if not e or reg("ebx") != e["a"]:
            return
        ebp = reg("ebp")
        emit("THB", {"ar": sreg("eax"), "def": s32(ebp - 8)})

    def on_thv():
        e = cur()
        if not e or reg("ebx") != e["a"]:
            return
        ebp = reg("ebp")
        emit("THV", {"ar": sreg("edi"), "def": sreg("esi"), "pct": s32(ebp - 4), "al": s32(ebp - 0x14),
                     "dl": s32(ebp - 0x18)})

    def on_thr():
        e = cur()
        a = reg("edx")
        if not e or a != e["a"]:
            return
        esp = reg("esp")
        emit("THR", {"c": s32(esp + 8), "r": s32(esp + 12), "sa": sd(a)})

    def on_drb():
        if not cur() and not st["ms"].get("cur"):
            return
        emit("DRB", {"u": reg("esi"), "b": sreg("eax")})

    def on_drm():
        if not cur() and not st["ms"].get("cur"):
            return
        emit("DRM", {"u": reg("esi"), "mv": sreg("eax")})

    def on_drr():
        esp = reg("esp")
        u = u32(esp + 4)
        e = cur()
        ms = None
        if not e or u not in (e["a"], e["d"]):
            ms = st["ms"].get("cur")
            if not ms or u != ms["d"]:
                return
        emit("DRR", {"u": u, "ch": s32(esp + 8), "r": s32(esp + 12), "lab": LABELS.get(u32(esp + 16), hex(u32(esp + 16))),
                     "s": sd(u)})

    def on_wbc():
        if not cur() and not st["ms"].get("cur"):
            return
        emit("WBC", {"u": reg("esi"), "wb": sreg("eax")})

    def on_wbs1():
        if not cur() and not st["ms"].get("cur"):
            return
        emit("WBS", {"v": s32(reg("ebp") - 4)})

    def on_wbs2():
        if not cur() and not st["ms"].get("cur"):
            return
        emit("WBS", {"v": s32(reg("ebp") - 8)})

    def pkt(p):
        return mem(p, 0x70).hex()

    def on_bd0():
        e = cur()
        a = reg("edx")
        if not e or a != e["a"]:
            return
        esp = reg("esp")
        p = u32(esp + 8)
        st["bd"] = p
        emit("BD0", {"p": pkt(p), "crit": s32(esp + 12), "src": u8(esp + 16), "sa": sd(a), "d": u32(esp + 4)})

    def on_rpt():
        e = cur()
        if not e or reg("esi") != e["a"]:
            return
        emit("RPT", {"v": sreg("eax")})

    def on_rpm():
        e = cur()
        if not e or reg("esi") != e["a"]:
            return
        emit("RPM", {"v": sreg("eax")})

    def on_rpe():
        e = cur()
        if not e or reg("esi") != e["a"]:
            return
        ebp = reg("ebp")
        w = u32(ebp + 8)
        emit("RPE", {"ed": sreg("ebx"), "min": s32(ebp + 0xC), "max": s32(ebp + 0x10), "s18": s32(ebp + 0x14),
                     "s17": s32(ebp - 4), "phys": s32(ebp + 0x18), "src": u8(ebp + 0x1C),
                     "w": s32(w + 4) if w else None, "sa": sd(e["a"])})

    def on_bdc():
        e = cur()
        if not e or reg("edi") != e["a"]:
            return
        emit("BDC", {"v": sreg("esi"), "sa": sd(e["a"])})

    def on_bd1():
        e = cur()
        if not e or reg("edi") != e["a"]:
            return
        emit("BD1", {"p": pkt(reg("ebx")), "sa": sd(e["a"]), "sd": sd(e["d"])})

    def red_ok(a, d):
        e = cur()
        if e and a == e["a"] and d == e["d"]:
            return True
        ms = st["ms"].get("cur")
        return bool(ms) and d == ms["d"]

    def on_rd0():
        esp = reg("esp")
        a, d = reg("edx"), u32(esp + 4)
        if not red_ok(a, d):
            st["rd"] = None
            return
        p = u32(esp + 8)
        st["rd"] = p
        emit("RD0", {"p": pkt(p), "a": a, "d": d, "da": unit(a, False) if a else None})

    def on_rdp():
        if not st.get("rd"):
            return
        emit("RDP", {"P": sreg("eax")})

    def on_rd1():
        p = st.get("rd")
        if not p:
            return
        st["rd"] = None
        emit("RD1", {"p": pkt(p)})

    def on_ad0():
        esp = reg("esp")
        a, d = reg("edx"), u32(esp + 4)
        if not red_ok(a, d) and not (cur() and d == cur()["a"]):
            return
        p = u32(esp + 12)
        st["ad"][esp] = (a, d, p)
        emit("AD0", {"p": pkt(p), "red": s32(esp + 8), "a": a, "d": d, "la": life(a) if a else None, "ld": life(d),
                     "sa": sd(a), "sd": sd(d), "fr": frame()})

    def on_ad1():
        esp = reg("esp")
        x = st["ad"].pop(esp, None)
        if not x:
            return
        a, d, p = x
        emit("AD1", {"p": pkt(p), "la": life(a) if a else None, "ld": life(d), "sa": sd(a), "sd": sd(d)})

    def on_evh():
        e = cur()
        ms = st["ms"].get("cur")
        if not e and not ms:
            return
        esp = reg("esp")
        u, o = u32(esp), u32(esp + 4)
        st["ev"].append((esp, u, o))
        emit("EVH", {"fn": reg("eax"), "e": reg("edx"), "u": u, "o": o, "par": u32(esp + 12),
                     "su": sd(u), "so": sd(o), "lu": life(u), "lo": life(o) if o else None})

    def on_evr():
        if not st["ev"]:
            return
        esp = reg("esp")
        k, u, o = st["ev"].pop()
        emit("EVR", {"r": sreg("eax"), "su": sd(u), "so": sd(o), "lu": life(u), "lo": life(o) if o else None,
                     "ok": esp == k + 0x14})

    def on_le1():
        e = cur()
        ms = st["ms"].get("cur")
        a = reg("ebx")
        if not ((e and a == e["a"]) or (ms and a == ms["o"])):
            return
        p = reg("edi")
        emit("LE1", {"la": life(a), "sa": sd(a), "st": list(struct.unpack("<3i", mem(p + 0x38, 12)))})

    def on_mh(tag):
        x = st["ad"].get(min(st["ad"])) if st["ad"] else None   # the innermost open COMBAT_ApplyDamage
        if x:
            emit(tag, {"sa": sd(x[0]), "sd": sd(x[1])})

    def on_sta():
        e = cur()
        ms = st["ms"].get("cur")
        if not e and not ms:
            return
        blk = reg("ecx")
        v = struct.unpack("<8i", mem(blk, 32))
        fr = frame()
        emit("STA", {"a": v[0] & 0xFFFFFFFF, "d": v[1] & 0xFFFFFFFF, "len": v[4], "stat": v[5], "val": v[6],
                     "state": v[7], "x": [v[2], v[3]], "fr": fr})
        d = v[1] & 0xFFFFFFFF
        if v[7] in (62, 2) and st["wins"] < 30 and d:
            if d not in st["win"]:
                st["wins"] += 1
            st["win"] = {d: fr + 250}
            # one window at a time: the tick's breakpoint has a gdb condition on $combat_win, set here (a breakpoint
            # is not enabled or changed inside stop(); a convenience variable may be) (logger r5)
            gdb.set_convenience_variable("combat_win", d)

    def seeds_line(tag):
        e = cur()
        if not e:
            return
        emit(tag, pair_seeds(e))

    def on_prg():
        if cur() or st["ms"].get("cur"):
            emit("PRG", {"pc": reg("eip")})

    def on_dq0():
        esp = reg("esp")
        a, d = reg("edx"), u32(esp + 4)
        e = cur()
        if e and a == e["a"] and d == e["d"]:
            st["dq"][esp] = (a, d)

    def on_dqx():
        esp = reg("esp")
        x = st["dq"].pop(esp, None)
        if not x:
            return
        a, d = x
        e = cur()
        if e and (a, d) == (e["a"], e["d"]):
            emit("EVX", {"sa": sd(a), "sd": sd(d), "la": life(a), "ld": life(d), "fr": frame()})
            st["cur"] = None

    # --- missiles --------------------------------------------------------------------------------------------------
    def on_ms0():
        ebp = reg("ebp")
        m, o = reg("esi"), reg("eax")
        d = u32(ebp + 8)
        p = u32(ebp + 0xC)
        if not d or not (involved(d) or involved(o)):
            return
        kind = "md" if involved(d) else "pm"
        if not take(kind):
            return
        g = u32(ebp - 8)
        st["game"] = g or st["game"]
        st["ms"]["cur"] = {"m": m, "o": o, "d": d, "k": kind, "esp": ebp + 4}
        emit("MS0", {"k": kind, "g": gctx(st["game"]), "mi": unit(m, False), "o": unit(o), "d": unit(d), "p": pkt(p),
                     "sm": sd(m), "so": sd(o), "sd": sd(d), "mrec": s32(m + 4)})

    def on_msx():
        ms = st["ms"].get("cur")
        if not ms:
            return
        st["ms"]["cur"] = None
        emit("MSX", {"so": sd(ms["o"]), "sd": sd(ms["d"]), "sm": sd(ms["m"]), "lo": life(ms["o"]), "ld": life(ms["d"]),
                     "fr": frame()})

    def on_gh0m():
        ms = st["ms"].get("cur")
        if ms:
            emit("GH0", {"so": sd(ms["o"]), "sd": sd(ms["d"])})

    def on_gh1m():
        ms = st["ms"].get("cur")
        if ms:
            emit("GH1", {"so": sd(ms["o"]), "sd": sd(ms["d"])})

    # --- MonAttackStats ----------------------------------------------------------------------------------------------
    def on_mas0():
        u, mode = reg("ecx"), sreg("edx")
        if not u or u32(u) != 1 or mode not in MAS_MODES:
            return
        if not take("mas"):
            return
        esp = reg("esp")
        st["mas"][esp] = u
        emit("MAS0", {"mode": sreg("edx"), "u": unit(u), "g": gctx(st["game"]) if st["game"] else None})

    def on_mas1():
        esp = reg("esp")
        u = st["mas"].pop(esp, None)
        if not u:
            return
        emit("MAS1", {"u": u, "s": sd(u), "st": stats(u)})

    # --- the regeneration tick (windowed) --------------------------------------------------------------------------
    def on_rgn(r="esi"):
        u = reg(r)
        end = st["win"].get(u)
        if end is None:
            return
        fr = frame()
        if fr is not None and fr > end:
            del st["win"][u]
            gdb.set_convenience_variable("combat_win", 0)
            return
        s = stats(u)
        emit("RGN", {"u": u, "t": u32(u), "fr": fr, "hp": s.get("6", 0), "mx": s.get("7", 0), "rg": s.get("74", 0),
                     "b74": base_stat(u, 74)})

    Bp(0x0052C312, on_game)
    Bp(0x0057EC10, on_ev0)
    Bp(0x0057DA28, on_thb)
    Bp(0x0057DADB, on_thv)
    Bp(0x005347B0, on_thr)
    Bp(0x0057DFE0, on_drb)
    Bp(0x0057E007, on_drm)
    Bp(0x005347C0, on_drr)
    Bp(0x0057DD98, on_wbc)
    Bp(0x0057DED3, on_wbc)
    Bp(0x0057DDB0, on_wbs1)
    Bp(0x0057DEEF, on_wbs2)
    Bp(0x0057B7D0, on_bd0)
    Bp(0x0057B44F, on_rpt)
    Bp(0x0057B596, on_rpm)
    Bp(0x0057B5B2, on_rpe)
    Bp(0x0057B8CA, on_bdc)
    Bp(0x0057BD89, on_bd1)
    Bp(0x0057C1E0, on_rd0)
    Bp(0x0057C2AF, on_rdp)
    Bp(0x0057C3CA, on_rd1)
    Bp(0x0057C6C0, on_ad0)
    for a in (0x0057C6F5, 0x0057C73E, 0x0057C97B):
        Bp(a, on_ad1)
    Bp(0x005C0C8E, on_evh)
    Bp(0x005C0C90, on_evr)
    Bp(0x0057C82B, on_le1)
    Bp(0x0056E970, on_sta)
    Bp(0x0057C83A, lambda: on_mh("MH0"))       # sub_005A4390_MonOnHitSkill, a monster attacker's hit (logger r6)
    Bp(0x0057C844, lambda: on_mh("MH1"))
    Bp(0x0057D5F6, lambda: seeds_line("DU0"))
    Bp(0x0057D5FB, lambda: seeds_line("DU1"))
    Bp(0x0057D64A, lambda: seeds_line("KB0"))
    Bp(0x0057D64F, lambda: seeds_line("KB1"))
    Bp(0x0057D658, lambda: seeds_line("GH0"))
    Bp(0x0057D65D, lambda: seeds_line("GH1"))
    for a in (0x005D3680, 0x005D3790, 0x005D3880, 0x005D3970, 0x005D537B):
        Bp(a, on_prg)
    Bp(0x0057D4F0, on_dq0)
    for a in (0x0057D560, 0x0057D66D, 0x0057D683):
        Bp(a, on_dqx)
    Bp(0x005AD757, on_ms0)
    Bp(0x005AD8D3, on_gh0m)
    Bp(0x005AD8D8, on_gh1m)
    Bp(0x005AD8DE, on_msx)
    Bp(0x005A4F50, on_mas0)
    Bp(0x005A5443, on_mas1)
    gdb.set_convenience_variable("combat_win", 0)
    rgn = Bp(0x00580610, on_rgn)                                  # a player's tick (ESI unit)
    rgn.condition = "$esi == $combat_win"
    rgm = Bp(0x005A6920, lambda: on_rgn("edx"))                   # a monster's regeneration event (EDX unit, r7)
    rgm.condition = "$edx == $combat_win"
    emit("COMBATLOG", {"rev": 8})
    gdb.write("COMBAT logger armed\n")


_combat_main()
