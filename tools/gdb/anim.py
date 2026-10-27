# gdb Python logger for plan 0050 Phase 2 (animation and frame timing, per-event reproduction): the event entry points
# of anim/0001 § 12, anim/0002 (rate change) and anim/0003 § 9 as ruled at the P1.3 review (plan 0050 Phase 2
# *Boundary*). Sourced by tools/gdb/anim.gdb after tools/gdb/pilot.py (the PLR/MON/CB/RL lines tools/d2pilot.py steers
# by). One line per event, "TAG {json}". Addresses refer to the pinned game.exe (image base 0x400000). Seeds are
# "low:high" hex. Every line carries "fr", the server frame Game+0xA8, and "n", this logger's own line count.
#
# Server units only: a unit is logged when Unit+0x80 (pGame) is the server game pointer (GPTR, 0x0052C312 EDI). A unit
# is {"u": pointer, "t": type, "c": class, "id": guid, "m": mode}.
#
#   SR      UNIT_AnimSetRate 0x00623F50 (stack unit) at its five `ret 0xC` (matched by ESP), players and monsters:
#           ra (the call's return address), rec [name, frames, speed] (Unit+0x50), r (+0x4C s16), sr (+0x3C), seq
#           (+0x30 != 0), c8 (+0xC8), st {67, 68, 69, 93, 96, 99, 102, 105, 10, 154: STATS_GetUnitStat as
#           tools/gdb/skills.py reads it}, ss (states 1, 11, 15, 21, 38, 42, 54, 101 that are on), sk [used skill id,
#           SkillEntry+0x0C flags] or null, pv (path +0x7C) or null; players also eq [[bodyloc, item class, ItemData
#           +0x18 flags, item stat 68, item stat 93, ItemData +0x45 page] for body locations 3, 4, 5], monsters mf (MonsterData +0x16)
#   SCH     SUNIT_ScheduleModeEvents 0x005539B0 (ECX game, EDX unit) closed at its rets 0x00553A0B / 0x00553AF9:
#           T (Game+0xA8 at entry), s0 (UNIT_AnimStartFrame's return at 0x005539CC; diagnostic only), r (+0x4C),
#           L (+0x48), seq (+0x30 != 0), sr (+0x3C), sl (+0x34), rec, sk, q [[kind, frame, a, b], ...] read at the
#           13 `call 0x5417D0` sites of 0x005539B0..0x00553F20 (anim/0001 § 7), a44 (+0x44 at the exit)
#   RSC     the catalogue reschedules 0x00553B10 / 0x00553C70 / 0x00553DC0 (ECX game, EDX unit, one argument;
#           boundary oracles), the same fields, "f" which, "arg"
#   CAN     0x00540E60 (ECX game, EDX unit; kind, x) for kinds 0 and 1: unit, kind, ra
#   PDS/MDS the player / monster event dispatch at the slot-list call sites 0x00540FC4 / 0x005410C4 (ECX game, EDX
#           unit, [esp] kind, a, b; the every-frame lists call it elsewhere): kind 1, or kind 0 with a != 0; MDS "fz"
#           1 when the dispatch will drop it (state 1 on a unit not in DT or DD)
#   MSET    UNIT_SetMode 0x00624690 (stack unit, mode): players, monsters, objects; "to", ra
#   EF      SUNIT_ModeEveryFrame 0x00553F00 (ECX game, EDX unit): the every-frame start; "ph" the event runner's
#           phase at the call (rev 3: breakpoints at the ten list calls of 0x005414D0 and its end, 0x0054158E)
#   OA0/OA1 UNIT_AnimInit 0x00624390 (stack unit) for an object: seed, mode, class, +0x44, +0x48, +0x4C before and at
#           its ten `ret 4` (ESP-matched)
#   OQ      the 23 `call 0x5417D0` sites of the object code (0x00580000..0x0058FFFF with a `shr .., 8` before them)
#           for an object unit: [kind, frame, a, b], site;  OEV  object event 1 0x00581490 (EDX object)
#   WIN/WINX a monster window opened / closed;  FREE  UnitFree 0x00555600 (ECX game, EDX unit) for a player or monster
#   PS0     0x00650899 in sub_00650840_PathStep ([ebp+8] unit, ESI path), after the target revalidation (an
#           oracle: the replan) and before PathVelocityStep, for the windowed units (the player, one monster at a time): path x, y (16.16), v (+0x7C), d (+0x6A, +0x6E), i (+0x24), np
#           (+0x28), pt (the next point, u16 x, y at +0x9C + 4i), pts (the first 24 points), ty (+0x3C), f34 (+0x34), b90 (+0x90), sx, sy (the
#           last step, +0x72 / +0x76), a (+0x88), cnt (+0x8C), mx (+0x84). The step's result is the next PS0's state
#   CT      0x00650215 in sub_00650150_PathStepCollide inside a windowed step: t the tested subtile ([ebp+0xC], x low
#           word, y high word), c the current one ([ebp-4]), r EAX (non-zero free; the oracle of the P1.3 review)
#   AD0     UNIT_AnimAdvance 0x00623E00 (stack unit) for the windowed monster: +0x44, +0x48, +0x4C, +0x4E (the last
#           advance's event byte), +0x30 != 0, +0x34, +0x38, +0x3C, +0x40, rec, used skill. The advance's result is
#           the next AD0's state
#   DR0/DR1 sub_0057F240_RunStaminaDrain (EDI unit) and its rets: stat 10, 154, the armour (body location 3) class;
#           exit eax and stat 10
#   GR0/GRH/GR1  sub_0057CB00_GetHitRoll (def, pkt, hc): def unit, its seed, states, stat 7, pkt total / poison /
#           result / +0x60; GRH the max-HP call's return (0x0057CB3E, the boundary); exit eax and the seed
#   GH      COMBAT_GetHit 0x0057CEE0 (ECX game, EDX attacker; defender, packet): units, result, +0x60, +0x64, total
#   PA0/PA1 sub_0057EEC0_PlayerModeAllowed (ECX game, EDX unit; mode, 1, skill): seed, states, stat 164, used skill;
#           exit eax and seed
#   PL0/PL1 sub_0057EDD0_PlrModeLeaveOk (EAX unit, EBX mode) and its seven rets; PLE inside it: E, the
#           least positive kind-1 event frame (sub_005415A0's return, read at 0x0057ED7A / 0x0057EDBC before the + 5)
#   KBE     sub_005A8520_MonKnockbackEnd entry (unit in ECX/EDX: both logged)
#   CAP     once per kind when its cap is reached
# Windows (ADR-0014 § Log volume): the player is always windowed for PS/CT; one monster at a time is windowed for PS,
# CT and AD, opened at an MSET of a monster into mode 2, 13, 14 or 15 (13 preempts an open walk
# or run window), closed at its next MSET to another mode, after ANIM_WIN_FRAMES (80) frames or at UnitFree; at most
# ANIM_WINS (400) monster windows a session, a new walk or run window at least ANIM_WIN_GAP (50) frames after the last
# one closed. No gdb conditions: a Python stop() method runs before gdb tests a condition, so every filter is here, and
# the per-frame breakpoints sit where they must (PathStep's step, the slot-list dispatch calls, the advance).
import json
import os
import struct

import gdb

REV = 3  # rev 1: the development logs (dev-, dev2-, dev3-, dev-r1-); rev 2: FREE lines, PS0 "pts"; rev 3: "ph"


def _anim_main():
    inf = gdb.selected_inferior()
    DT_PTR = 0x00744304
    CAPS = {"sr": 40000, "sch": 30000, "mds": 60000, "pds": 40000, "mset": 60000, "oa": 3000, "oq": 3000,
            "ps": 60000, "ad": 40000, "dr": 20000, "gr": 6000, "gh": 8000, "pa": 6000, "pl": 6000, "can": 60000,
            "ct": 60000, "ef": 30000, "oev": 2000}
    for k in list(CAPS):
        v = os.environ.get("ANIM_CAP_" + k.upper())
        if v:
            CAPS[k] = int(v)
    WIN_FRAMES = int(os.environ.get("ANIM_WIN_FRAMES", "80"))
    WINS = int(os.environ.get("ANIM_WINS", "400"))
    WIN_GAP = int(os.environ.get("ANIM_WIN_GAP", "50"))
    QSITES = (0x00553A00, 0x00553A8F, 0x00553AA5, 0x00553AE2, 0x00553B9D, 0x00553C1E, 0x00553C55, 0x00553CF7,
              0x00553D7E, 0x00553DB1, 0x00553E33, 0x00553EB2, 0x00553EE5)
    OQSITES = (0x00581A04, 0x00581D30, 0x00582068, 0x0058216C, 0x0058223C, 0x00583E4C, 0x00583EDB, 0x00583F65,
               0x0058403E, 0x0058438C, 0x005846FF, 0x00584C79, 0x00584EBE, 0x00585F32, 0x005863B7, 0x0058648C,
               0x005865A1, 0x0058672A, 0x00586800, 0x005869E1, 0x00586A9D, 0x0058BDDB, 0x0058D4F6)
    RST = [67, 68, 69, 93, 96, 99, 102, 105, 10, 154]
    STATES = [1, 11, 15, 21, 38, 42, 54, 101]
    st = {"game": 0, "n": {}, "capped": set(), "line": 0, "isc": None, "sr": {}, "sch": None, "oa": {},
          "pl": {}, "dr": {}, "gr": {}, "pa": {}, "ps": {}, "ad": {}, "win": 0, "win_t0": 0, "wins": 0, "plr": 0,
          "rsc": None, "ph": 0}

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

    def take(kind):
        n = st["n"].get(kind, 0)
        if n >= CAPS.get(kind, 20000):
            if kind not in st["capped"]:
                st["capped"].add(kind)
                emit("CAP", {"k": kind, "n": n})
            return False
        st["n"][kind] = n + 1
        return True

    def sd(u):
        return "%08x:%08x" % struct.unpack("<II", mem(u + 0x20, 8)) if u else None

    def frame():
        g = st["game"]
        return u32(g + 0xA8) if g else None

    def server(u):
        if not u or not st["game"]:
            return False
        try:
            return u32(u + 0x80) == st["game"]
        except gdb.MemoryError:
            return False

    def isc_info():
        if st["isc"] is None:
            dt = u32(DT_PTR)
            st["isc"] = (u32(dt + 0xBCC), s32(dt + 0xBD4), u8(0x006CE270))
        return st["isc"]

    def stats(u, want):
        """{stat: value} as STATS_GetUnitStat returns them (layer 0; tools/gdb/skills.py's reading), zeros left out."""
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

    def states_on(u, want=STATES):
        lst = u32(u + 0x5C) if u else 0
        if not lst or not (u32(lst + 0x10) & 0x80000000):
            return []
        bits = u32(lst + 0x58)
        if not bits:
            return []
        out = []
        for s in want:
            if u32(bits + 4 * (s >> 5)) & (1 << (s & 31)):
                out.append(s)
        return out

    def unit(u):
        if not u:
            return None
        return {"u": u, "t": u32(u), "c": s32(u + 4), "id": u32(u + 0x0C), "m": u32(u + 0x10)}

    def rec(u):
        r = u32(u + 0x50)
        if not r:
            return None
        nm = mem(r, 8).split(b"\0")[0].decode("latin-1")
        return [nm, u32(r + 8), u32(r + 0x0C)]

    def used_skill(u):
        sl = u32(u + 0xA8)
        if not sl:
            return None
        e = u32(sl + 0x10)
        if not e:
            return None
        r = u32(e)
        return [s16(r) if r else None, u32(e + 0x0C)]

    def equip(u, locs=(3, 4, 5)):
        inv = u32(u + 0x60)
        out = []
        if not inv or u32(inv) != 0x01020304:
            return out
        it, k = u32(inv + 0x0C), 0
        while it and k < 200:
            idt = u32(it + 0x14)
            if not idt:
                break
            bl = u8(idt + 0x44)
            if u32(it) == 4 and bl in locs:
                s = stats(it, [68, 93])
                out.append([bl, s32(it + 4), u32(idt + 0x18), s.get("68", 0), s.get("93", 0), u8(idt + 0x45)])
            it = u32(idt + 0x64)
            k += 1
        return sorted(out)

    def path_v(u):
        p = u32(u + 0x2C)
        return s32(p + 0x7C) if p else None

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
                gdb.write("LOGERR anim %r\n" % (e,))
            return False

    def on_game():
        st["game"] = reg("edi")
        st["isc"] = None
        emit("AGM", {"game": st["game"]})

    # --- rate --------------------------------------------------------------------------------------------------
    def on_sr0():
        esp = reg("esp")
        u = u32(esp + 4)
        if not server(u) or u32(u) not in (0, 1):
            return
        st["sr"][esp] = (u, u32(esp))

    def on_sr1():
        esp = reg("esp")
        v = st["sr"].pop(esp, None)
        if not v or not take("sr"):
            return
        u, ra = v
        t = u32(u)
        d = {"u": unit(u), "fr": frame(), "ra": ra, "rec": rec(u), "r": s16(u + 0x4C), "sr": s32(u + 0x3C),
             "seq": int(u32(u + 0x30) != 0), "c8": u32(u + 0xC8), "st": stats(u, RST), "ss": states_on(u),
             "sk": used_skill(u), "pv": path_v(u)}
        if t == 0:
            d["eq"] = equip(u)
            if not st["plr"]:
                st["plr"] = u
        else:
            md = u32(u + 0x14)
            d["mf"] = u8(md + 0x16) if md else None
        emit("SR", d)

    # --- schedule ----------------------------------------------------------------------------------------------
    def sch_fields(u):
        return {"u": unit(u), "fr": frame(), "r": s16(u + 0x4C), "L": s32(u + 0x48), "seq": int(u32(u + 0x30) != 0),
                "sr": s32(u + 0x3C), "sl": s32(u + 0x34), "rec": rec(u), "sk": used_skill(u), "a44": s32(u + 0x44)}

    def on_sch0():
        u = reg("edx")
        if not server(u) or not take("sch"):
            st["sch"] = None
            return
        d = sch_fields(u)
        d["T"] = d["fr"]
        d["q"] = []
        st["sch"] = (u, d)

    def on_s0():
        if st["sch"]:
            st["sch"][1]["s0"] = sreg("eax")

    def on_sch1():
        v = st["sch"]
        st["sch"] = None
        if not v:
            return
        u, d = v
        d["a44"] = s32(u + 0x44)
        emit("SCH", d)

    def on_rsc0(which):
        def f():
            esp = reg("esp")
            u = reg("edx")
            if not server(u) or u32(u) not in (0, 1):
                return
            d = sch_fields(u)
            d["f"] = which
            d["arg"] = s32(esp + 4)
            d["q"] = []
            st["rsc"] = (u, d, esp)
        return f

    def on_rsc1():
        v = st["rsc"]
        if not v or reg("esp") != v[2]:
            return
        st["rsc"] = None
        u, d, _ = v
        d["a44"] = s32(u + 0x44)
        emit("RSC", d)

    def on_q():
        # at a `call 0x5417D0` site: ECX game, EDX unit, [esp] kind, frame, a, b
        esp = reg("esp")
        u = reg("edx")
        q = list(struct.unpack("<4i", mem(esp, 16)))
        if st["sch"] and u == st["sch"][0]:
            st["sch"][1]["q"].append(q)
        elif st["rsc"] and u == st["rsc"][0]:
            st["rsc"][1]["q"].append(q)

    def on_oq():
        esp = reg("esp")
        u = reg("edx")
        if u and server(u) and u32(u) == 2 and take("oq"):
            emit("OQ", {"o": unit(u), "fr": frame(), "q": list(struct.unpack("<4i", mem(esp, 16))),
                        "site": reg("eip")})

    def on_can():
        esp = reg("esp")
        u = reg("edx")
        kind = s32(esp + 4)
        if kind not in (0, 1) or not server(u) or u32(u) not in (0, 1) or not take("can"):
            return
        emit("CAN", {"u": u, "k": kind, "fr": frame(), "ra": u32(esp)})

    def dispatch(tag, kind_name):
        # at the slot-list call of the dispatch (0x00540FC4 players, 0x005410C4 monsters): ECX game, EDX unit,
        # [esp] kind (byte), a, b
        def f():
            esp = reg("esp")
            kind, a, b = struct.unpack("<3i", mem(esp, 12))
            if not (kind == 1 or (kind == 0 and a != 0)):
                return
            u = reg("edx")
            if not server(u) or not take(kind_name):
                return
            d = {"u": u, "m": u32(u + 0x10), "k": kind, "a": a, "b": b, "fr": frame()}
            if tag == "MDS":
                d["fz"] = int(1 in states_on(u, [1]) and u32(u + 0x10) not in (0, 12))
            emit(tag, d)
        return f

    # --- mode changes ------------------------------------------------------------------------------------------
    def on_mset():
        esp = reg("esp")
        u, to = u32(esp + 4), s32(esp + 8)
        if not server(u):
            return
        t = u32(u)
        if t not in (0, 1, 2) or not take("mset"):
            return
        m = u32(u + 0x10)
        emit("MSET", {"u": unit(u), "to": to, "fr": frame(), "ra": u32(esp)})
        if t == 1 and m != to:
            w = st["win"]
            if w == u:
                if to not in (2, 13, 14, 15):
                    close_win("mode")
            cool = (frame() or 0) - st.get("win_t1", -9999) >= WIN_GAP
            if to in (2, 13, 14, 15) and ((not st["win"] and (cool or to == 13)) or
                                          (to == 13 and st["win"] and st["win_m"] in (2, 15))) and st["wins"] < WINS:
                if st["win"]:
                    close_win("preempt")
                open_win(u, to)

    def open_win(u, m):
        st["win"] = u
        st["win_m"] = m
        st["win_t0"] = frame() or 0
        st["wins"] += 1
        emit("WIN", {"u": unit(u), "to": m, "fr": frame(), "k": st["wins"]})

    def close_win(why):
        u = st["win"]
        st["win"] = 0
        st["win_t1"] = frame() or 0
        emit("WINX", {"u": u, "why": why, "fr": frame()})

    def on_ef():
        u = reg("edx")
        if server(u) and u32(u) in (0, 1) and take("ef"):
            emit("EF", {"u": u, "m": u32(u + 0x10), "fr": frame(), "ph": st["ph"]})

    def phase(k):
        def f():
            st["ph"] = k
        return f

    def on_free():
        # UnitFree 0x00555600 (ECX game, EDX unit)
        u = reg("edx")
        if not u or not server(u):
            return
        t = u32(u)
        if t in (0, 1) and take("free"):
            emit("FREE", {"u": u, "t": t, "c": s32(u + 4), "m": u32(u + 0x10), "fr": frame()})
        if u == st["win"]:
            close_win("free")

    # --- objects -------------------------------------------------------------------------------------------------
    def on_oa0():
        esp = reg("esp")
        u = u32(esp + 4)
        if not server(u) or u32(u) != 2:
            return
        st["oa"][esp] = (u, {"o": unit(u), "fr": frame(), "s": sd(u), "a44": s32(u + 0x44), "L": s32(u + 0x48),
                             "r": s16(u + 0x4C)})

    def on_oa1():
        esp = reg("esp")
        v = st["oa"].pop(esp, None)
        if not v or not take("oa"):
            return
        u, d = v
        n = emit("OA0", d)
        emit("OA1", {"k": n, "o": u, "s": sd(u), "a44": s32(u + 0x44), "L": s32(u + 0x48), "r": s16(u + 0x4C),
                     "m": u32(u + 0x10)})

    def on_oev():
        u = reg("edx")
        if server(u) and take("oev"):
            emit("OEV", {"o": unit(u), "fr": frame()})

    # --- movement ------------------------------------------------------------------------------------------------
    def path_in(p):
        i, npt = s32(p + 0x24), s32(p + 0x28)
        pt = list(struct.unpack("<HH", mem(p + 0x9C + 4 * i, 4))) if 0 <= i < 64 else None
        pts = [list(struct.unpack("<HH", mem(p + 0x9C + 4 * j, 4))) for j in range(min(max(npt, 0), 24))]
        return {"x": u32(p), "y": u32(p + 4), "v": s32(p + 0x7C), "d": [s32(p + 0x6A), s32(p + 0x6E)], "i": i,
                "np": npt, "pt": pt, "pts": pts, "ty": s32(p + 0x3C), "f34": u32(p + 0x34), "b90": u8(p + 0x90)}

    def on_ps0():
        # 0x00650899 in sub_00650840_PathStep, after the target revalidation and before PathVelocityStep: ESI the
        # path, [ebp+8] the unit (the server's UnitMoveStep passes k 0x400; client callers are dropped by the filter)
        u = u32(reg("ebp") + 8)
        if u != st["plr"] and u != st["win"]:
            st["ctp"] = 0
            return
        p = u32(u + 0x2C)
        if not p or not take("ps"):
            st["ctp"] = 0
            return
        if u == st["win"] and (frame() or 0) - st["win_t0"] > WIN_FRAMES:
            close_win("frames")
            st["ctp"] = 0
            return
        d = {"u": u, "t": u32(u), "m": u32(u + 0x10), "fr": frame(), "k": s32(reg("ebp") + 0xC),
             "sx": s32(p + 0x72), "sy": s32(p + 0x76),
             "a": s32(p + 0x88), "cnt": s32(p + 0x8C), "mx": s32(p + 0x84)}
        d.update(path_in(p))
        emit("PS0", d)
        st["ctp"] = p

    def on_ct1():
        # 0x00650215, after the collision test in sub_00650150_PathStepCollide: ESI path, [ebp+0xC] the tested
        # subtile (x low word, y high word), [ebp-4] the current one, EAX the result
        if not st.get("ctp") or reg("esi") != st["ctp"] or not take("ct"):
            return
        ebp = reg("ebp")
        emit("CT", {"t": u32(ebp + 0xC), "c": u32(ebp - 4), "r": sreg("eax"), "fr": frame()})

    def on_ad0():
        esp = reg("esp")
        u = u32(esp + 4)
        if u != st["win"] or not u or not take("ad"):
            return
        emit("AD0", {"u": u, "m": u32(u + 0x10), "fr": frame(), "a44": s32(u + 0x44), "L": s32(u + 0x48),
                     "r": s16(u + 0x4C), "e4e": u8(u + 0x4E), "seq": int(u32(u + 0x30) != 0), "sl": s32(u + 0x34),
                     "sp": s32(u + 0x38), "sr": s32(u + 0x3C), "m40": s32(u + 0x40), "rec": rec(u),
                     "sk": used_skill(u)})

    def on_dr0():
        esp = reg("esp")
        u = reg("edi")
        if not server(u) or not take("dr"):
            return
        arm = [e[1] for e in equip(u, (3,))]
        n = emit("DR0", {"u": u, "c": s32(u + 4), "fr": frame(), "st": stats(u, [10, 154]), "arm": arm[0] if arm else None,
                         "m": u32(u + 0x10)})
        st["dr"][esp] = (n, u)

    def on_dr1():
        esp = reg("esp")
        v = st["dr"].pop(esp, None)
        if not v:
            return
        n, u = v
        emit("DR1", {"k": n, "r": sreg("eax"), "st": stats(u, [10])})

    # --- get-hit -------------------------------------------------------------------------------------------------
    def on_gr0():
        esp = reg("esp")
        de, pk, hc = struct.unpack("<IIi", mem(esp + 4, 12))
        if not server(de) or not take("gr"):
            return
        n = emit("GR0", {"d": unit(de), "fr": frame(), "s": sd(de), "ss": states_on(de), "hp7": stats(de, [7]).get("7"),
                         "tot": s32(pk + 0x4C), "poi": s32(pk + 0x28), "res": u16(pk + 4), "hc60": u32(pk + 0x60),
                         "hc": hc})
        st["gr"][esp] = (n, de)
        st["gr_n"] = n

    def on_grh():
        if st.get("gr_n"):
            emit("GRH", {"k": st["gr_n"], "hp": sreg("eax")})

    def on_gr1():
        esp = reg("esp")
        v = st["gr"].pop(esp, None)
        if not v:
            return
        n, de = v
        st["gr_n"] = None
        emit("GR1", {"k": n, "r": sreg("eax"), "s": sd(de)})

    def on_gh():
        esp = reg("esp")
        att = reg("edx")
        de, pk = struct.unpack("<II", mem(esp + 4, 8))
        if not server(de) or not take("gh"):
            return
        emit("GH", {"a": unit(att), "d": unit(de), "fr": frame(), "res": u16(pk + 4), "hc60": u32(pk + 0x60),
                    "b64": u8(pk + 0x64), "tot": s32(pk + 0x4C), "ds": sd(de), "ss": states_on(de)})

    def on_pa0():
        esp = reg("esp")
        u = reg("edx")
        if not server(u) or not take("pa"):
            return
        a = list(struct.unpack("<3i", mem(esp + 4, 12)))
        n = emit("PA0", {"u": unit(u), "fr": frame(), "a": a, "s": sd(u), "ss": states_on(u),
                         "st": stats(u, [164]), "sk": used_skill(u)})
        st["pa"][esp] = (n, u)

    def on_pa1():
        esp = reg("esp")
        v = st["pa"].pop(esp, None)
        if not v:
            return
        n, u = v
        emit("PA1", {"k": n, "r": sreg("eax"), "s": sd(u), "m": u32(u + 0x10)})

    def on_pl0():
        esp = reg("esp")
        u = reg("eax")
        if not server(u) or not take("pl"):
            return
        n = emit("PL0", {"u": unit(u), "fr": frame(), "req": sreg("ebx")})
        st["pl"][esp] = n

    def on_ple():
        if not st["pl"]:
            return
        emit("PLE", {"E": sreg("eax"), "fr": frame()})

    def on_pl1():
        n = st["pl"].pop(reg("esp"), None)
        if n:
            emit("PL1", {"k": n, "r": sreg("eax")})

    def on_kbe():
        emit("KBE", {"ecx": reg("ecx"), "edx": reg("edx"), "fr": frame()})

    Bp(0x0052C312, on_game)
    Bp(0x00623F50, on_sr0)
    for a in (0x0062401D, 0x00624110, 0x006241D4, 0x0062430A, 0x0062438B):
        Bp(a, on_sr1)
    Bp(0x005539B0, on_sch0)
    Bp(0x005539CC, on_s0)
    Bp(0x00553A0B, on_sch1)
    Bp(0x00553AF9, on_sch1)
    for a, w in ((0x00553B10, "pct"), (0x00553C70, "skip"), (0x00553DC0, "at")):
        Bp(a, on_rsc0(w))
    for a in (0x00553BA8, 0x00553C60, 0x00553D02, 0x00553DBC, 0x00553E3E, 0x00553EF0):
        Bp(a, on_rsc1)
    for a in QSITES:
        Bp(a, on_q)
    for a in OQSITES:
        Bp(a, on_oq)
    Bp(0x00540E60, on_can)
    Bp(0x00540FC4, dispatch("PDS", "pds"))
    Bp(0x005410C4, dispatch("MDS", "mds"))
    Bp(0x00624690, on_mset)
    Bp(0x00553F00, on_ef)
    # the runner's phases in sub_005414D0_GameRunUnitEvents (anim/0001 § 6): 1 missiles every-frame list, 2 missile
    # slot, 3 players every-frame, 4 player slot, 5 monsters every-frame, 6 monster slot, 7/8 objects, 9/10 items,
    # 11 after the runner; 0 at its entry
    Bp(0x005414D0, phase(0))
    for k, a in enumerate((0x005414F6, 0x00541508, 0x00541517, 0x00541526, 0x00541535, 0x00541547, 0x00541556,
                           0x00541568, 0x00541577, 0x00541589, 0x0054158E), 1):
        Bp(a, phase(k))
    Bp(0x00555600, on_free)
    Bp(0x00624390, on_oa0)
    for a in (0x0062444F, 0x00624480, 0x006244D0, 0x00624501, 0x00624555, 0x0062459A, 0x006245C6, 0x006245E8,
              0x006245FF, 0x00624676):
        Bp(a, on_oa1)
    Bp(0x00581490, on_oev)
    Bp(0x00650899, on_ps0)
    Bp(0x00650215, on_ct1)
    Bp(0x00623E00, on_ad0)
    Bp(0x0057F240, on_dr0)
    for a in (0x0057F246, 0x0057F25C, 0x0057F326, 0x0057F32D):
        Bp(a, on_dr1)
    Bp(0x0057CB00, on_gr0)
    Bp(0x0057CB3E, on_grh)
    for a in (0x0057CB1F, 0x0057CBEC, 0x0057CBF5):
        Bp(a, on_gr1)
    Bp(0x0057CEE0, on_gh)
    Bp(0x0057EEC0, on_pa0)
    for a in (0x0057EEDC, 0x0057EFB8, 0x0057EFEF, 0x0057EFFC):
        Bp(a, on_pa1)
    Bp(0x0057EDD0, on_pl0)
    for a in (0x0057EDF4, 0x0057EE37, 0x0057EE49, 0x0057EE54, 0x0057EE5F, 0x0057EE67, 0x0057EE6F):
        Bp(a, on_pl1)
    Bp(0x0057ED7A, on_ple)
    Bp(0x0057EDBC, on_ple)
    Bp(0x005A8520, on_kbe)
    gdb.write("ANIM logger armed rev %d\n" % REV)
_anim_main()
