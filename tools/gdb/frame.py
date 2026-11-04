# gdb Python logger for plan 0055 Phase 2b (frame windows). Sourced by tools/gdb/frame.gdb after tools/gdb/pilot.py
# (the PLR/RL/CB lines tools/d2pilot.py steers by). Addresses refer to the pinned game.exe (image base 0x400000, sha256
# 631066c1...). One line per record, "TAG {json}"; seeds are "low:high" hex. Every line carries "fr" (the frame stamp,
# Game+0xA8) and "n" (this logger's own line count). The design is docs/findings/frame/0001 § 7 (the P1.1 lines),
# 0002 § 8 (UE0/UE1), 0003 § 9 (the closed design); the reader and checker are `python3 -I tools/frame.py window`.
#
# THIS LOGGER NEVER WRITES GAME MEMORY OR REGISTERS (review-fixes 17, ADR-0003). It reads memory (inf.read_memory) and
# registers ($name) and writes its own lines; the only things it changes are gdb's own breakpoint enable flags (a window
# opens by enabling the window breakpoints and closes by disabling them) and, for nothing the game sees, its host
# counters. No breakpoint here has a condition, a command list or an expression with side effects; every site stops,
# logs or not by Python, and returns False from stop() (the game resumes). `grep -nE 'write_memory|set var|\$[a-z]+ *=|
# execute\(' tools/gdb/frame.py` finds nothing (tools/test_frame_window.py asserts it).
#
# Lines (site; fields beyond fr, n):
#   WIN   a window opens (before its first FT0): id, scene, len, start, wall (unix s), mono (monotonic s), cover
#   WEND  a window closes (after its last FT1): id, ok, why, frames, lines, hits {name: count} (this logger's own stops
#         in the window), ghits {name: gdb hit_count delta}, wall0, wall1, mono0, mono1
#   HB    outside a window, every 250th frame: wall, mono (liveness for the runner; the only line outside windows)
#   FT0   GameTick entry 0x0052D870 (ECX game): fr = Game+0xA8 + 1 (the increment is the entry's third instruction,
#         0x0052D87B; FT1 reads the real value), pre = Game+0xA8, gs (Game+0xD0), hc (g_HitClassCounter, 0x0088CAD0)
#   FT1   GameTick return 0x0052D974: fr (read), gs
#   FP    the seven pass calls 0x0052D8DF, 0x0052D8E6, 0x0052D8EB, 0x0052D8F2, 0x0052D8F9, 0x0052D900, 0x0052D907 and the
#         sweep call 0x0052D96C: site, gs; written only when gs differs from the game seed of the last line written
#         (any line with a "gs", or "gs1" when it has one)
#   ACL   after ActClockTick, 0x0052D7D7 (EBX act, EAX the return); non-zero returns only: act, r
#   UE0   the 20 unit-event dispatch sites (frame/0002 § 8): ty (unit type), id (guid), lst (ef | slot), kind, rf (record
#         frame), a, b (record +0x14, +0x18), cb (1: the record's callback, 0: the type's dispatch), site, u (unit
#         pointer), us (unit seed), gs
#   UE1   the instruction after the call: same u, id, site, us (after; null when the unit memory cannot be read), gs, gone
#   MSG0  SrvPacketDispatch entry 0x0054D750 (ECX game, EDX player, [esp+4] packet, [esp+8] length): pl, id, op, len,
#         hex (first 24 bytes), ps (player seed), gs
#   MSG1  its four rets 0x0054D785, 0x0054D81E, 0x0054D827, 0x0054D832: r (EAX), ps, gs
#   SYS   SrvClientMsgDispatch 0x0053F100 (ECX message): ty (byte at +4)
#   RU0   NewRoomsUpdate's per-room call 0x0052D1C4, and RoomUpdateOne's entry 0x0052D0F0 (one: 1): act, room, f (room+0x34),
#         rs (room seed +0x6C), gs, ra (one only)
#   RU1   the next-room load 0x0052D211 and RoomUpdateOne's rets 0x0052D133, 0x0052D151 (one: 1): same fields
#   TM    0x0052D920 (which T20), 0x0052D938 (D12), 0x0052D95F (U11, act), 0x0052D322 (S1500, inside the sweep's branch): gs
#   TQ0   QUESTS_TimersRun's callback call 0x00543E85: cb (EAX), q (EDX), due ([timer+8]), tick (control +0x14), gs
#   TQ1   its return 0x00543E87: r (AL), gs
#   RC    DUNGEON_RoomCreate's return 0x0061995E (EAX room): act, room, drlg (room +0x10), lv (DRLG room +0x58), rs, f
#   RR    ActiveRoomFree entry 0x0061A910 ([esp+4] act, [esp+8] room): act, room, f
#   QE    EventQueueAt entry 0x005416B0 (ECX kind, EAX frame asked, EDX game, [esp+4] unit): kind and asked (signed), ut,
#         id (the unit), ra
#   QF    EventQueueEveryFrame entry 0x005415E0 (EBX kind, EAX unit) unless [esp] = 0x005416DC: kind (signed), ut, id, ra
#   SV0   SaveGameClients entry 0x0052CA10 (a boundary oracle: frame/0003 § 3): ra, gs
#   SV1   its three returns 0x0052D430, 0x0052D4C2, 0x00530446: gs
#   XS    (rev 2) every execution of an LCG multiplier site (tools/gdb/lcg-sites.txt, 852 `mov ecx|edx, 0x6ac690c5`, rng/0001)
#         inside a window, only from the thread that hit FT0 (other threads are counted in WEND.hits as XS_other, not
#         written): site, low (the seed's low word, which the step multiplies: EAX at all but two sites, ESI at 0x004F2959
#         and [ESI] at 0x005F7C17; tools/test_frame_xs.py recounts that with objdump), ra (the caller, only for the six
#         sites inside rng/0001's primitives, by each one's stack offset)
#   KD    (rev 2) sub_005A6830_MonDeathDrop entry 0x005A6830 (EDX event, [EDX+4] the dying monster): ty, id
#   CAP   once, when WIN_MAX_LINES (env FRAME_MAX_LINES, default 400000) lines are written in one window
#   LOGERR a handler raised; the game resumes (the logger never stops it)
#
# FRAME_HOOKS=1 (rev 2): the universal hooks of frame/0005 (tools/gdb/frame-hooks.txt) as count-only breakpoints; WEND carries
# "hk": {address: {open-event rank | "msg" | "ru" | "none": count}} and no line is written for them.
# Windows (env): FRAME_WINDOWS = "SPEC,SPEC" with SPEC = START:LEN:SCENE[:COVER]; START is an absolute frame, or "r"+N
# (N frames after the first FT0 seen), or "now" (the next FT0); COVER M places the window so that the frame = 0 (mod M)
# lies in its middle (START ignored). FRAME_CTL = a control file the runner appends to; each new line
# "open LEN SCENE [cover=M] [at=N]" opens a window at the next FT0 (or at frame N, or around the next multiple of M).
# Outside a window only FT0 and FT1 stop (2 stops a frame; the control poll runs inside FT0); the window breakpoints
# are disabled. "ghits" (gdb's own hit_count) is expected to stay 0: gdb counts a hit only when stop() answers True, and
# these breakpoints answer False (gdb's bpstat_stop_status, a reading, [I]); the first smoke session shows it, and
# "hits" (this logger's own count of stops, by name) is the hit count per breakpoint the record states.
import json
import os
import struct
import time

import gdb

REV = 2
HOOKS_ON = bool(os.environ.get("FRAME_HOOKS"))
# The six LCG sites inside rng/0001's primitives and the caller's return address relative to ESP at the site (the pushes of
# each primitive before its multiplier load; objdump of 0x0045C370, 0x0045C390, 0x0045C3E0, 0x00472210, 0x00472240, 0x00472280)
PRIM_RA = {0x0045C372: 0, 0x0045C39F: 12, 0x0045C3F9: 12, 0x00472217: 12, 0x0047224A: 16, 0x004722A4: 16}
LOW_ESI, LOW_MEM_ESI = 0x004F2959, 0x005F7C17
# pass rank of a unit-event list (tools/frame.py PASS_NAMES): type -> (every-frame walk, slot walk)
RANK = {3: (4, 5), 0: (6, 7), 1: (8, 9), 2: (10, 11), 4: (12, 13)}
MAX_LINES = int(os.environ.get("FRAME_MAX_LINES", "400000"))
HC_ADDR = 0x0088CAD0
UE_SITES = (   # callback call, dispatch call, unit type, list
    (0x00540FB2, 0x00540FC4, 0, "slot"), (0x00541016, 0x0054102B, 0, "ef"),
    (0x005410B2, 0x005410C4, 1, "slot"), (0x00541116, 0x0054112B, 1, "ef"),
    (0x005411B2, 0x005411BF, 2, "slot"), (0x00541209, 0x00541216, 2, "ef"),
    (0x00541292, 0x0054129F, 3, "slot"), (0x005412E9, 0x005412F6, 3, "ef"),
    (0x00541372, 0x0054137F, 4, "slot"), (0x005413C9, 0x005413D6, 4, "ef"),
)
UE_NEXT = {0x00540FB2: 0x00540FB4, 0x00540FC4: 0x00540FC9, 0x00541016: 0x00541018, 0x0054102B: 0x00541030,
           0x005410B2: 0x005410B4, 0x005410C4: 0x005410C9, 0x00541116: 0x00541118, 0x0054112B: 0x00541130,
           0x005411B2: 0x005411B4, 0x005411BF: 0x005411C4, 0x00541209: 0x0054120B, 0x00541216: 0x0054121B,
           0x00541292: 0x00541294, 0x0054129F: 0x005412A4, 0x005412E9: 0x005412EB, 0x005412F6: 0x005412FB,
           0x00541372: 0x00541374, 0x0054137F: 0x00541384, 0x005413C9: 0x005413CB, 0x005413D6: 0x005413DB}
FP_SITES = (0x0052D8DF, 0x0052D8E6, 0x0052D8EB, 0x0052D8F2, 0x0052D8F9, 0x0052D900, 0x0052D907, 0x0052D96C)
MSG_RETS = (0x0054D785, 0x0054D81E, 0x0054D827, 0x0054D832)
SV_RETS = (0x0052D430, 0x0052D4C2, 0x00530446)


def _frame_main():
    inf = gdb.selected_inferior()
    st = {"game": 0, "line": 0, "win": None, "pend": [], "ctl_off": 0, "first": None, "last_gs": None, "wid": 0,
          "thr": None, "ue": [], "msg": [], "one": [], "hk": {}, "wlines": 0, "capped": False, "hits": {}, "gh0": {}, "skip_ctl": 0}
    ctl_path = os.environ.get("FRAME_CTL", "")
    wbps = []          # the window breakpoints: enabled only inside a window
    allbps = {}        # name -> breakpoint, for gdb's own hit counts

    def mem(a, n):
        return bytes(inf.read_memory(a, n))

    def u8(a):
        return mem(a, 1)[0]

    def u32(a):
        return struct.unpack("<I", mem(a, 4))[0]

    def s32(a):
        return struct.unpack("<i", mem(a, 4))[0]

    def reg(n):
        return int(gdb.parse_and_eval("$" + n)) & 0xFFFFFFFF

    def sd(a):
        return "%08x:%08x" % struct.unpack("<II", mem(a, 8)) if a else None

    def sdq(a):
        try:
            return sd(a)
        except gdb.MemoryError:
            return None

    def gs():
        return sd(st["game"] + 0xD0)

    def fr():
        return u32(st["game"] + 0xA8)

    def emit(tag, d):
        st["line"] += 1
        d["n"] = st["line"]
        if st["win"] is not None:
            st["wlines"] += 1
            if st["wlines"] > MAX_LINES:
                if not st["capped"]:
                    st["capped"] = True
                    gdb.write("CAP {\"k\":\"window\",\"n\":%d}\n" % st["wlines"])
                return
        if "gs1" in d:
            st["last_gs"] = d["gs1"]
        elif "gs" in d:
            st["last_gs"] = d["gs"]
        gdb.write("%s %s\n" % (tag, json.dumps(d, separators=(",", ":"))))

    def unit_head(u):
        """(type, guid) of a unit pointer, or (None, None)."""
        if not u:
            return None, None
        try:
            return u32(u), u32(u + 0x0C)
        except gdb.MemoryError:
            return None, None

    def hit(name):
        st["hits"][name] = st["hits"].get(name, 0) + 1

    class Bp(gdb.Breakpoint):
        def __init__(self, addr, name, fn, window=True):
            super().__init__("*0x%08X" % addr, internal=True)
            self.silent = True
            self.name, self.fn = name, fn
            allbps[name + "@%08X" % addr] = self
            if window:
                wbps.append(self)
                self.enabled = False

        def stop(self):
            hit(self.name)
            try:
                self.fn()
            except Exception as e:      # never stop the game on a logger error; log it instead
                gdb.write("LOGERR frame %s %r\n" % (self.name, e))
            return False

    def arm(on):
        for b in wbps:
            b.enabled = on

    # --- windows --------------------------------------------------------------------------------------------------
    def parse_spec(spec):
        p = spec.split(":")
        start = p[0]
        n = int(p[1]) if len(p) > 1 else 250
        scene = p[2] if len(p) > 2 else "scene"
        cover = int(p[3]) if len(p) > 3 and p[3] else 0
        return {"start": start, "len": n, "scene": scene, "cover": cover}

    for spec in [s for s in os.environ.get("FRAME_WINDOWS", "").split(",") if s]:
        try:
            st["pend"].append(parse_spec(spec))
        except ValueError:
            gdb.write("LOGERR frame bad FRAME_WINDOWS %r\n" % spec)

    def poll_ctl():
        if not ctl_path:
            return
        try:
            with open(ctl_path) as f:
                f.seek(st["ctl_off"])
                data = f.read()
                st["ctl_off"] = f.tell()
        except OSError:
            return
        for ln in data.splitlines():
            w = ln.split()
            if len(w) >= 2 and w[0] == "open":
                d = {"start": "now", "len": int(w[1]), "scene": w[2] if len(w) > 2 else "scene", "cover": 0}
                for x in w[3:]:
                    if x.startswith("cover="):
                        d["cover"] = int(x[6:])
                    elif x.startswith("at="):
                        d["start"] = x[3:]
                st["pend"].append(d)

    def resolve(p, f):
        """Absolute start frame of a pending spec given the current frame f (the frame this FT0 runs)."""
        n = p["len"]
        if p["cover"]:
            m, h = p["cover"], n // 2
            return ((f + h + m - 1) // m) * m - h if f + h > 0 else f
        s = p["start"]
        if s == "now":
            return f
        if s.startswith("r"):
            return st["first"] + int(s[1:])
        return int(s)

    def open_window(p, f):
        st["wid"] += 1
        st["wlines"] = 0
        st["capped"] = False
        st["win"] = {"id": st["wid"], "scene": p["scene"], "len": p["len"], "start": f, "end": f + p["len"] - 1,
                     "mono0": time.monotonic(), "wall0": time.time(), "lines0": st["line"], "frames": 0}
        st["hits"] = {"FT0": 1}      # this frame's FT0 stop was counted before the reset
        st["gh0"] = {k: b.hit_count for k, b in allbps.items()}
        st["ue"], st["msg"], st["one"], st["hk"] = [], [], [], {}
        arm(True)
        emit("WIN", {"id": st["wid"], "scene": p["scene"], "len": p["len"], "start": f, "fr": f, "wall": round(time.time(), 3),
                     "mono": round(time.monotonic(), 3), "cover": p["cover"], "rev": REV})

    def close_window(ok, why):
        w = st["win"]
        if w is None:
            return
        arm(False)
        gh = {k: b.hit_count - st["gh0"].get(k, 0) for k, b in allbps.items() if b.hit_count - st["gh0"].get(k, 0)}
        emit("WEND", {"id": w["id"], "ok": ok, "why": why, "frames": w["frames"], "lines": st["line"] - w["lines0"],
                      "hits": st["hits"], "ghits": gh, "hk": st["hk"], "wall0": round(w["wall0"], 3), "wall1": round(time.time(), 3),
                      "mono0": round(w["mono0"], 3), "mono1": round(time.monotonic(), 3), "fr": w["end"]})
        st["win"] = None

    # --- the frame -------------------------------------------------------------------------------------------------
    def on_ft0():
        game = reg("ecx")
        if game != st["game"]:
            if st["win"] is not None:
                st["game"] = game
                close_window(0, "game pointer changed")
            st["game"], st["first"], st["last_gs"] = game, None, None
        pre = u32(game + 0xA8)
        f = (pre + 1) & 0xFFFFFFFF
        if st["first"] is None:
            st["first"] = f
        if st["win"] is not None and f > st["win"]["end"]:
            close_window(0, "missed the end frame")
        if st["win"] is None:
            poll_ctl()
            for p in list(st["pend"]):
                s = resolve(p, f)
                if s < f:
                    st["pend"].remove(p)
                    gdb.write("WSKIP {\"scene\":\"%s\",\"start\":%d,\"fr\":%d}\n" % (p["scene"], s, f))
                elif s == f:
                    st["pend"].remove(p)
                    open_window(p, f)
                    break
        w = st["win"]
        if w is None:
            if f % 250 == 0:
                emit("HB", {"fr": f, "wall": round(time.time(), 3), "mono": round(time.monotonic(), 3)})
            return
        w["frames"] += 1
        st["thr"] = gdb.selected_thread().num
        emit("FT0", {"fr": f, "pre": pre, "gs": gs(), "hc": u8(HC_ADDR), "game": game})

    def on_ft1():
        if st["win"] is None or not st["game"]:
            return
        f = fr()
        emit("FT1", {"fr": f, "gs": gs()})
        if f >= st["win"]["end"]:
            close_window(1, "")

    def on_fp(addr):
        def h():
            g = gs()
            if g != st["last_gs"]:
                emit("FP", {"fr": fr(), "site": addr, "gs": g})
        return h

    def on_acl():
        r = reg("eax")
        if r:
            emit("ACL", {"fr": fr(), "act": reg("ebx"), "r": r})

    # --- unit events -----------------------------------------------------------------------------------------------
    def on_ue0(addr, ty, lst, cb):
        def h():
            rec = reg("esi")
            u = u32(rec + 8)
            d = {"fr": fr(), "ty": ty, "id": u32(rec + 0x0C), "lst": lst, "kind": u8(rec), "rf": u32(rec + 4),
                 "a": u32(rec + 0x14), "b": u32(rec + 0x18), "cb": cb, "site": addr, "u": u,
                 "us": sdq(u + 0x20) if u else None, "gs": gs()}
            st["ue"].append((addr, u, d["id"], ty, lst))
            emit("UE0", d)
        return h

    def on_ue1(site, join=None):
        # The callback path's instruction after the call is `jmp` to the dispatch call's next instruction, so both UE1
        # breakpoints fire for one event (smoke session 1 of the pack: 4 "UE1 with no open UE0"; with an event open
        # outside it, the second would have closed the wrong one). The callback's UE1 names the dispatch site it joins
        # (`join`); that site's UE1 right after it is the same return and logs nothing.
        def h():
            if st.get("join") == site:
                st["join"] = None
                return
            if not st["ue"]:
                emit("LOGERR", {"fr": fr(), "why": "UE1 with no open UE0", "site": site})
                return
            a, u, i, _ty, _lst = st["ue"].pop()
            us = sdq(u + 0x20) if u else None
            emit("UE1", {"fr": fr(), "id": i, "site": a, "u": u, "us": us, "gs": gs(), "gone": 0 if us else 1})
            if join is not None:
                st["join"] = join
        return h

    # --- messages --------------------------------------------------------------------------------------------------
    def on_msg0():
        game, pl, esp = reg("ecx"), reg("edx"), reg("esp")
        pkt, ln = u32(esp + 4), u32(esp + 8)
        try:
            raw = mem(pkt, min(ln, 24, 0x5B4))
        except gdb.MemoryError:
            raw = b""
        st["msg"].append(pl)
        emit("MSG0", {"fr": fr(), "pl": pl, "id": u32(pl + 0x0C) if pl else None, "op": raw[0] if raw else None, "len": ln,
                      "hex": raw.hex(), "ps": sdq(pl + 0x20) if pl else None, "gs": gs()})

    def on_msg1():
        pl = st["msg"].pop() if st["msg"] else 0
        emit("MSG1", {"fr": fr(), "r": reg("eax"), "ps": sdq(pl + 0x20) if pl else None, "gs": gs()})

    def on_sys():
        m = reg("ecx")
        emit("SYS", {"fr": fr(), "ty": u8(m + 4)})

    # --- rooms and timers ------------------------------------------------------------------------------------------
    def room_line(tag, room, extra=None):
        d = {"fr": fr(), "room": room, "f": u32(room + 0x34), "rs": sdq(room + 0x6C), "gs": gs()}
        d["act"] = u32(room + 0x2C)
        if extra:
            d.update(extra)
        emit(tag, d)

    def on_ru0_loop():
        slot = u32(reg("ebp") - 4)
        room = reg("esi")
        room_line("RU0", room, {"ai": (slot - (st["game"] + 0xBC)) // 4})

    def on_ru1_loop():
        slot = u32(reg("ebp") - 4)
        room_line("RU1", reg("esi"), {"ai": (slot - (st["game"] + 0xBC)) // 4})

    def on_ru0_one():
        room = reg("edx")
        st["one"].append(room)
        room_line("RU0", room, {"one": 1, "ra": u32(reg("esp"))})

    def on_ru1_one():
        room = st["one"].pop() if st["one"] else 0
        if room:
            room_line("RU1", room, {"one": 1})

    def on_tm(which, act=False):
        def h():
            d = {"fr": fr(), "which": which, "gs": gs()}
            if act:
                d["act"] = (reg("esi") - (st["game"] + 0xBC)) // 4
            emit("TM", d)
        return h

    def on_tq0():
        esi, edi = reg("esi"), reg("edi")
        emit("TQ0", {"fr": fr(), "cb": reg("eax"), "q": reg("edx"), "due": u32(esi + 8), "tick": u32(edi + 0x14),
                     "gs": gs()})

    def on_tq1():
        emit("TQ1", {"fr": fr(), "r": reg("eax") & 0xFF, "gs": gs()})

    def on_rc():
        room = reg("eax")
        drlg = u32(room + 0x10)
        emit("RC", {"fr": fr(), "act": u32(room + 0x2C), "room": room, "drlg": drlg, "lv": u32(drlg + 0x58) if drlg else None,
                    "rs": sdq(room + 0x6C), "f": u32(room + 0x34)})

    def on_rr():
        esp = reg("esp")
        room = u32(esp + 8)
        emit("RR", {"fr": fr(), "act": u32(esp + 4), "room": room, "f": u32(room + 0x34)})

    # --- the queue --------------------------------------------------------------------------------------------------
    def _s(v):
        return v - (1 << 32) if v & 0x80000000 else v

    def on_qe():
        esp = reg("esp")
        u = u32(esp + 4)
        ut, i = unit_head(u)
        k = reg("ecx")
        emit("QE", {"fr": fr(), "kind": _s(k), "asked": _s(reg("eax")), "ut": ut, "id": i, "ra": u32(esp)})

    def on_qf():
        esp = reg("esp")
        ra = u32(esp)
        if ra == 0x005416DC:
            return
        ut, i = unit_head(reg("eax"))
        emit("QF", {"fr": fr(), "kind": _s(reg("ebx")), "ut": ut, "id": i, "ra": ra})

    sv_open = [False]

    def on_sv0():
        sv_open[0] = True
        emit("SV0", {"fr": fr(), "ra": u32(reg("esp")), "gs": gs()})

    def on_sv1():
        # the three SV_RETS are the instructions after the calls; the branch that skips a call reaches them too
        # (smoke session 1: 2 SV1 per frame, no SV0), so a return counts only after its entry
        if not sv_open[0]:
            return
        sv_open[0] = False
        emit("SV1", {"fr": fr(), "gs": gs()})

    # --- the breakpoints ------------------------------------------------------------------------------------------
    Bp(0x0052D870, "FT0", on_ft0, window=False)
    Bp(0x0052D974, "FT1", on_ft1, window=False)
    for a in FP_SITES:
        Bp(a, "FP", on_fp(a))
    Bp(0x0052D7D7, "ACL", on_acl)
    for cb, dp, ty, lst in UE_SITES:
        Bp(cb, "UE0", on_ue0(cb, ty, lst, 1))
        Bp(dp, "UE0", on_ue0(dp, ty, lst, 0))
        Bp(UE_NEXT[cb], "UE1", on_ue1(cb, dp))
        Bp(UE_NEXT[dp], "UE1", on_ue1(dp))
    # --- rev 2: every LCG step, the kills, the hooks ---------------------------------------------------------------------
    def on_xs(addr):
        def h():
            if gdb.selected_thread().num != st["thr"]:
                hit("XS_other")
                return
            if addr == LOW_ESI:
                low = reg("esi")
            elif addr == LOW_MEM_ESI:
                low = u32(reg("esi"))
            else:
                low = reg("eax")
            d = {"fr": fr(), "site": addr, "low": low}
            if addr in PRIM_RA:
                d["ra"] = u32(reg("esp") + PRIM_RA[addr])
            emit("XS", d)
        return h

    def on_kd():
        ev = reg("edx")
        ty, i = unit_head(u32(ev + 4))
        emit("KD", {"fr": fr(), "ty": ty, "id": i})

    def hook_ctx():
        if st["ue"]:
            _a, _u, _i, ty, lst = st["ue"][-1]
            ef, slot = RANK.get(ty, (0, 0))
            return str(slot if lst == "slot" else ef)
        if st["msg"]:
            return "msg"
        if st["one"]:
            return "ru"
        return "none"

    def on_hook(addr):
        def h():
            k = "%08X" % addr
            d = st["hk"].setdefault(k, {})
            c = hook_ctx()
            d[c] = d.get(c, 0) + 1
        return h

    def gdb_file(name):
        for base in ("tools/gdb", os.path.dirname(os.path.abspath(globals().get("__file__", "tools/gdb/frame.py")))):
            if os.path.exists(os.path.join(base, name)):
                return os.path.join(base, name)
        return os.path.join("tools/gdb", name)

    sites = []
    with open(gdb_file("lcg-sites.txt")) as fh:
        for ln in fh:
            if ln.startswith("0x"):
                sites.append(int(ln.split()[0], 16))
    for a in sites:
        Bp(a, "XS", on_xs(a))
    Bp(0x005A6830, "KD", on_kd)
    if HOOKS_ON:
        with open(gdb_file("frame-hooks.txt")) as fh:
            for ln in fh:
                if ln.startswith("0x"):
                    Bp(int(ln.split()[0], 16), "HK", on_hook(int(ln.split()[0], 16)))
    Bp(0x0054D750, "MSG0", on_msg0)
    for a in MSG_RETS:
        Bp(a, "MSG1", on_msg1)
    Bp(0x0053F100, "SYS", on_sys)
    Bp(0x0052D1C4, "RU0", on_ru0_loop)
    Bp(0x0052D211, "RU1", on_ru1_loop)
    Bp(0x0052D0F0, "RU0", on_ru0_one)
    for a in (0x0052D133, 0x0052D151):
        Bp(a, "RU1", on_ru1_one)
    Bp(0x0052D920, "TM", on_tm("T20"))
    Bp(0x0052D938, "TM", on_tm("D12"))
    Bp(0x0052D95F, "TM", on_tm("U11", act=True))
    Bp(0x0052D322, "TM", on_tm("S1500"))
    Bp(0x00543E85, "TQ0", on_tq0)
    Bp(0x00543E87, "TQ1", on_tq1)
    Bp(0x0061995E, "RC", on_rc)
    Bp(0x0061A910, "RR", on_rr)
    Bp(0x005416B0, "QE", on_qe)
    Bp(0x005415E0, "QF", on_qf)
    Bp(0x0052CA10, "SV0", on_sv0)
    for a in SV_RETS:
        Bp(a, "SV1", on_sv1)
    gdb.write("RDY {\"logger\":\"frame\",\"rev\":%d,\"bps\":%d,\"ctl\":%s}\n" % (REV, len(wbps) + 2, json.dumps(ctl_path)))
    gdb.write("Frame logger armed rev %d\n" % REV)


_frame_main()
