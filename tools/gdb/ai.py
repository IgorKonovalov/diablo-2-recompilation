# gdb Python logger for plan 0052 Phase 2 (monster AI, per-event reproduction). Sourced by tools/gdb/ai.gdb after
# tools/gdb/pilot.py (the PLR/MON/CB/RL lines tools/d2pilot.py steers by). One line per event, "TAG {json}". Addresses
# refer to the pinned game.exe (image base 0x400000). Seeds are "low:high" hex. Every line carries "fr", the server
# frame Game+0xA8, and "n", this logger's own line count. One AI decision is one call of the think function of
# sub_005B1740_MonAiEvent (docs/findings/ai/0001 § 1); the lines of a decision share "k" (the AID line's "n").
#
#   AGM   0x0052C312 (GAME_InitSeeds, EDI = game): the server game pointer
#   AIN   sub_005B1740_MonAiEvent (ECX game, EDX unit; ret 8) for a server monster near the player whose event ended
#         before the think call (the pre-checks, the target search, MonSpcWalk): u, id, c, ai (MonStats +0x1E), st
#         (AiCtl.state), s0 (the unit seed at entry), s1 (at exit), fr
#   AID   the think call, 0x005B186F (`call eax`, ESI unit, EDI game, [ebp-0x24] the AiCtx): the decision's inputs: u, id,
#         c, ai, st, th (AiCtl.think), cx (the AiCtx address), g (game), mdp (MonsterData), ctlp (AiCtl), hp (the
#         head record address), md (MonsterData +0x54), m (unit mode +0x10), c4 (Unit +0xC4), x, y (path
#         +2, +6), s0 (seed at event entry), s (seed at the call), diff (Game +0x6D), ms (MonStats record), ms2 (record
#         count at DataTables +0xA80), ctx [AiCtl, +4, target, +0xC, +0x10, dist, melee, MonStats, MonStats2],
#         ctl (AiCtl, 0x40 bytes hex), head (the AiCtl +0x20 record, 0x1C bytes hex or null), aip (MonStats +0x56,
#         24 u16 hex: aip k of difficulty d at 3(k-1)+d), sk (MonStats +0x170, Skill1..8 s16 and Sk1..8mode, 24 bytes
#         hex), ad [aidel +0x4F, aidist +0x52], t (the target: type, class, id, mode, x, y, path flag) or null,
#         pl [x, y] of the first player
#   AIB   a call of one of the boundary functions BND (the observed boundaries of the tools/ai_cat_emu*.py models) from
#         the think function's code (return address in 0x005B14E0..0x005B1650 or 0x005E0000..0x005FFFFF, from rev 3 also in the three callee
#         windows of THINK_LO) while the
#         decision is open: k, fn, ra, ecx, edx, a (six stack words), b (8 dwords at a stack-pointing argument, by
#         argument index), s (the unit seed), c (AiCtl +0x14, +0x18, +0x1C), c4; at most AI_BMAX (8) per decision
#   MSM0/MSM1  sub_005A7C20_MonSetMode (stack: game, cmd, flag) entry and its five rets, while a decision is open:
#         k, ra, the command block (mode, unit, target, x, y, +0x15, +0x18, +0x1C), s; exit: eax, s
#   PP0/PP1    sub_00649970_PathPlan entry (stack: path, unit, flag) and its six rets, while a decision is open: k, the
#         path type, s; exit: eax, s
#   SST0/SST1  SKILLS_SrvStart 0x0056F640 (ECX game, EDX unit; id, lvl, noCost) and its rets, for a server monster near
#         the player (open decision or not): u, fr, id, lvl, s; exit: eax, s
#   AIX   the event's ret 0x005B1876 after a think call: k, s (the unit seed at the exit), nb (boundary lines)
#   CAP   once per kind when its cap is reached
# Filter (ADR-0014 § Log volume): server monsters (Unit +0 = 1) within AI_RADIUS (80) sub-tiles of the first player
# on each axis; per-row cap AI_CAP_ROW (200) and per-session cap AI_CAP_SESSION (3000) of decisions, AI_CAP_AIN (600)
# for AIN lines, all per game (the counters restart at each AGM line, so a case of a shared process has its own). No gdb conditions: a Python stop() method runs before gdb tests a condition, so every filter is here;
# the boundary breakpoints are enabled only while a decision is open.
import json
import os
import struct

import gdb

REV = 3   # rev 1: the development logs (dev-*); rev 2: the six PathPlan rets (rev 1 logged the first three); rev 3: the
#          return-address windows of MonsterOwner, 0x005DE830 and 0x005DF850 (the models' sites 0x0058F0FF, 0x005DE864,
#          0x005DF97B)


def _ai_main():
    inf = gdb.selected_inferior()
    DT_PTR = 0x00744304
    CAP_ROW = int(os.environ.get("AI_CAP_ROW", "200"))
    CAP_SESSION = int(os.environ.get("AI_CAP_SESSION", "3000"))
    CAP_AIN = int(os.environ.get("AI_CAP_AIN", "600"))
    CAP_SST = int(os.environ.get("AI_CAP_SST", "4000"))
    RADIUS = int(os.environ.get("AI_RADIUS", "80"))
    BMAX = int(os.environ.get("AI_BMAX", "8"))
    BND = (
        0x00463740, 0x00463860, 0x0046ACE0, 0x00472210, 0x004E6C70, 0x004EFCB0, 0x00540E60, 0x005415A0, 0x005417D0,
        0x00544300, 0x0054DA60, 0x0054DC40, 0x00552F60, 0x00552FD0, 0x00553540, 0x00554010, 0x005541B0, 0x00554200,
        0x00554EA0, 0x0056DEB0, 0x0056EDE0, 0x005701B0, 0x00574BD0, 0x00574DE0, 0x0057CCB0, 0x0058ED10, 0x0058EE80,
        0x0058EEF0, 0x0058EF40, 0x0058F0D0, 0x0058F730, 0x00599420, 0x0059C330, 0x005A0180, 0x005A01E0, 0x005A6190,
        0x005A6260, 0x005A7C20, 0x005A7E60, 0x005B0BD0, 0x005B0E00, 0x005B2F20, 0x005B4390, 0x005DC380, 0x005DC480,
        0x005DC5C0, 0x005DC640, 0x005DD0B0, 0x005DD280, 0x005DD290, 0x005DD2B0, 0x005DD7F0, 0x005DDC30, 0x005DDE50,
        0x005DDF90, 0x005DDFC0, 0x005DE000, 0x005DE080, 0x005DE0F0, 0x005DE190, 0x005DE200, 0x005DE440, 0x005DE6D0,
        0x005DEAD0, 0x005DEC80, 0x005DECA0, 0x005DED00, 0x005DED20, 0x005DED40, 0x005DED90, 0x005DEDE0, 0x005DEE50,
        0x005DEF80, 0x005DEFB0, 0x005DEFE0, 0x005DF140, 0x005DF400, 0x005DF530, 0x005DF680, 0x005DF7D0, 0x005E17E0,
        0x005E3930, 0x005E3EA0, 0x005E45D0, 0x005E4D30, 0x005E5050, 0x005F2EB0, 0x005F2FC0, 0x005F77C0, 0x005F9E30,
        0x005FD350, 0x005FD470, 0x0061A1B0, 0x0061AB00, 0x0061AD30, 0x0061B130, 0x006201D0, 0x00620BB0, 0x00620C10,
        0x00621DC0, 0x00621E40, 0x00621F20, 0x006221A0, 0x00622AA0, 0x00622C40, 0x00625420, 0x00625480, 0x006256B0,
        0x006259B0, 0x00625B70, 0x00625D10, 0x00625D60, 0x00639DB0, 0x00639DF0, 0x0063A770, 0x0063E7A0, 0x0063E7E0,
        0x0063EA40, 0x0063EC70, 0x0063EFA0, 0x006416D0, 0x006439B0, 0x006439F0, 0x006442A0, 0x00646CA0, 0x006488A0,
        0x00648A20, 0x00648A30, 0x00648AD0, 0x00649070, 0x00649180, 0x0064C040, 0x0064CB30, 0x0064D910, 0x006510C0,
        0x006562F0,
    )
    # return-address windows of a boundary call: the think functions (state row 2 and the AI code 0x005E0000..) and
    # three callees the emulations run on the image (rev 3): MonsterOwner (0x0058F0D0, its GameFindUnit call at
    # 0x0058F0FF), the overseer's stored-unit helper (0x005DE830) and the skill helper 0x005DF850
    THINK_LO = ((0x005B14E0, 0x005B1650), (0x005E0000, 0x00600000), (0x0058F0D0, 0x0058F130),
                (0x005DE830, 0x005DE8C0), (0x005DF850, 0x005DFC00))
    st = {"game": 0, "n": {}, "capped": set(), "line": 0, "stk": [], "plr": 0, "row": {}, "tot": 0, "sst": {},
          "msm": {}, "pp": {}}

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

    def emit(tag, d):
        st["line"] += 1
        d["n"] = st["line"]
        gdb.write("%s %s\n" % (tag, json.dumps(d, separators=(",", ":"))))
        return st["line"]

    def take(kind, cap):
        n = st["n"].get(kind, 0)
        if n >= cap:
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

    def pos(u):
        p = u32(u + 0x2C)
        return (u16(p + 2), u16(p + 6)) if p else None

    def player():
        g, p = st["game"], st["plr"]
        if p:
            try:
                if u32(p) == 0 and u32(p + 0x80) == g:
                    return p
            except gdb.MemoryError:
                pass
        st["plr"] = 0
        for u in struct.unpack("<128I", mem(g + 0x1120, 512)):
            if u:
                st["plr"] = u
                return u
        return 0

    def near(u):
        """The unit is a monster within RADIUS sub-tiles (per axis) of the first player: its position, else None."""
        if not u or u32(u) != 1:
            return None
        pl = player()
        a, b = pos(u), (pos(pl) if pl else None)
        if not a or not b or abs(a[0] - b[0]) > RADIUS or abs(a[1] - b[1]) > RADIUS:
            return None
        return a

    def in_think(ra):
        for lo, hi in THINK_LO:
            if lo <= ra < hi:
                return True
        return False

    bnd_bps = []

    def arm(on):
        for b in bnd_bps:
            b.enabled = on

    def top():
        s = st["stk"]
        return s[-1] if s and s[-1] and s[-1].get("open") else None

    class Bp(gdb.Breakpoint):
        def __init__(self, addr, fn, store=None):
            super().__init__("*0x%08X" % addr, internal=True)
            self.silent = True
            self.fn = fn
            if store is not None:
                store.append(self)

        def stop(self):
            try:
                self.fn()
            except Exception as e:  # never stop the game on a logger error; log it instead
                gdb.write("LOGERR ai %s %r\n" % (getattr(self.fn, "__name__", "?"), e))
            return False

    def on_game():
        st["game"] = reg("edi")
        st["stk"] = []
        st["plr"] = 0
        st["row"], st["tot"], st["n"], st["capped"] = {}, 0, {}, set()   # the caps are per game (a case of a shared process)
        arm(False)
        emit("AGM", {"game": st["game"]})

    # --- the AI event --------------------------------------------------------------------------------------------
    def on_entry():
        st["game"] = reg("ecx")
        u = reg("edx")
        f = None
        try:
            xy = near(u)
            if xy:
                f = {"u": u, "s0": sd(u), "xy": xy, "open": False, "thought": False}
        except gdb.MemoryError:
            f = None
        st["stk"].append(f)

    def unit_ai(u):
        md = u32(u + 0x14)
        ctl = u32(md + 0x28) if md else 0
        cls = s32(u + 4)
        dt = u32(DT_PTR)
        ms = u32(dt + 0xA78) + cls * 0x1A8 if 0 <= cls < s32(dt + 0xA80) else 0
        return md, ctl, cls, ms, (s16(ms + 0x1E) if ms else None)

    def on_think():
        s = st["stk"]
        f = s[-1] if s else None
        if not f or f["thought"]:
            return
        f["thought"] = True
        u = f["u"]
        md, ctl, cls, ms, ai = unit_ai(u)
        row = st["row"].get(ai, 0)
        if row >= CAP_ROW or st["tot"] >= CAP_SESSION:
            if ("row", ai) not in st["capped"]:
                st["capped"].add(("row", ai))
                emit("CAP", {"k": "row", "ai": ai, "n": row, "tot": st["tot"]})
            return
        st["row"][ai] = row + 1
        st["tot"] += 1
        ctx = reg("ebp") - 0x24
        cw = list(struct.unpack("<9I", mem(ctx, 36)))
        tg = cw[2]
        t = None
        if tg:
            tp = u32(tg + 0x2C)
            t = [u32(tg), s32(tg + 4), u32(tg + 0x0C), u32(tg + 0x10)] + (list(pos(tg)) if tp else [None, None])
        head = u32(ctl + 0x20) if ctl else 0
        pl = player()
        d = {"u": u, "id": u32(u + 0x0C), "c": cls, "ai": ai, "st": u32(ctl) if ctl else None,
             "th": u32(ctl + 4) if ctl else None, "md": u32(md + 0x54), "m": u32(u + 0x10), "c4": u32(u + 0xC4),
             "x": f["xy"][0], "y": f["xy"][1], "s0": f["s0"], "s": sd(u), "fr": frame(),
             "cx": ctx, "g": st["game"], "mdp": md, "ctlp": ctl, "hp": head, "diff": u8(st["game"] + 0x6D), "ms": ms, "ms2": s32(u32(DT_PTR) + 0xA80), "ctx": cw,
             "ctl": mem(ctl, 0x40).hex(), "head": mem(head, 0x1C).hex() if head else None,
             "aip": mem(ms + 0x56, 48).hex(), "sk": mem(ms + 0x170, 24).hex(),
             "ad": [u8(ms + 0x4F), u8(ms + 0x52)], "t": t, "pl": list(pos(pl)) if pl else None}
        f["k"] = emit("AID", d)
        f["open"] = True
        f["nb"] = 0
        f["out"] = 0
        arm(True)

    def on_exit():
        s = st["stk"]
        f = s.pop() if s else None
        if f and f["open"]:
            emit("AIX", {"k": f["k"], "s": sd(f["u"]), "nb": f["nb"], "fr": frame()})
        elif f and not f["thought"]:
            ai = None
            try:
                ai = unit_ai(f["u"])[4]
            except gdb.MemoryError:
                pass
            if take("ain", CAP_AIN):
                ctl = u32(u32(f["u"] + 0x14) + 0x28)
                emit("AIN", {"u": f["u"], "id": u32(f["u"] + 0x0C), "c": s32(f["u"] + 4), "ai": ai,
                             "st": u32(ctl) if ctl else None, "s0": f["s0"], "s1": sd(f["u"]), "fr": frame()})
        if not any(x and x["open"] for x in s):
            arm(False)

    # --- boundaries -----------------------------------------------------------------------------------------------
    def on_bnd(fn):
        def f():
            cur = top()
            if not cur:
                return
            esp = reg("esp")
            ra = u32(esp)
            if not in_think(ra):
                cur["out"] += 1
                if cur["out"] > 600:
                    arm(False)
                return
            if cur["nb"] >= BMAX:
                return
            cur["nb"] += 1
            a = list(struct.unpack("<6I", mem(esp + 4, 24)))
            b = {}
            for i, v in enumerate(a):
                if esp - 0x1000 <= v < esp + 0x2000:
                    try:
                        b[str(i)] = list(struct.unpack("<8I", mem(v, 32)))
                    except gdb.MemoryError:
                        pass
            u = cur["u"]
            md = u32(u + 0x14)
            ctl = u32(md + 0x28)
            emit("AIB", {"k": cur["k"], "fn": fn, "ra": ra, "ecx": reg("ecx"), "edx": reg("edx"), "a": a, "b": b,
                         "s": sd(u), "c": list(struct.unpack("<3I", mem(ctl + 0x14, 12))), "c4": u32(u + 0xC4),
                         "fr": frame()})
        return f

    def on_msm0():
        cur = top()
        if not cur:
            return
        esp = reg("esp")
        cmd = u32(esp + 8)
        w = list(struct.unpack("<5I", mem(cmd, 20))) + [u8(cmd + 0x15), s32(cmd + 0x18), u8(cmd + 0x1C)]
        cu = w[1]
        st["msm"][esp] = cur["k"]
        emit("MSM0", {"k": cur["k"], "ra": u32(esp), "flag": u32(esp + 4), "cmd": w, "s": sd(cu) if cu else None,
                      "fr": frame()})

    def on_msm1():
        k = st["msm"].pop(reg("esp"), None)
        if k is None:
            return
        cur = top()
        u = cur["u"] if cur else None
        emit("MSM1", {"k": k, "eax": reg("eax"), "s": sd(u) if u else None})

    def on_pp0():
        cur = top()
        if not cur:
            return
        esp = reg("esp")
        p, u = struct.unpack("<II", mem(esp + 4, 8))
        st["pp"][esp] = cur["k"]
        emit("PP0", {"k": cur["k"], "ra": u32(esp), "ty": s32(p + 0x3C), "b90": u8(p + 0x90), "u": u,
                     "s": sd(u) if u else None})

    def on_pp1():
        k = st["pp"].pop(reg("esp"), None)
        if k is None:
            return
        cur = top()
        u = cur["u"] if cur else None
        emit("PP1", {"k": k, "eax": reg("eax"), "s": sd(u) if u else None})

    def on_sst0():
        u = reg("edx")
        xy = near(u)
        if not xy or not take("sst", CAP_SST):
            return
        esp = reg("esp")
        n = emit("SST0", {"u": u, "id": u32(u + 0x0C), "c": s32(u + 4), "fr": frame(), "a": list(struct.unpack("<3i", mem(esp + 4, 12))),
                          "s": sd(u), "m": u32(u + 0x10)})
        st["sst"][esp] = (n, u)

    def on_sst1():
        v = st["sst"].pop(reg("esp"), None)
        if v:
            emit("SST1", {"k": v[0], "eax": reg("eax"), "s": sd(v[1])})

    Bp(0x0052C312, on_game)
    Bp(0x005B1740, on_entry)
    Bp(0x005B186F, on_think)
    Bp(0x005B1876, on_exit)
    for a in BND:
        Bp(a, on_bnd(a), bnd_bps)
    Bp(0x005A7C20, on_msm0, bnd_bps)
    for a in (0x005A7C3E, 0x005A7CA2, 0x005A7D99, 0x005A7E0A, 0x005A7E51):
        Bp(a, on_msm1, bnd_bps)
    Bp(0x00649970, on_pp0, bnd_bps)
    for a in (0x00649984, 0x006499C2, 0x006499F0, 0x00649C5F, 0x00649C6E, 0x00649C8F):
        Bp(a, on_pp1, bnd_bps)
    Bp(0x0056F640, on_sst0)
    for a in (0x0056F6E8, 0x0056F7D0, 0x0056F7D9):
        Bp(a, on_sst1)
    arm(False)
    gdb.write("AI logger armed rev %d\n" % REV)


_ai_main()
