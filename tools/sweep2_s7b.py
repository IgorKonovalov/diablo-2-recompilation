#!/usr/bin/env python3
"""Plan 0066 Phase 1, batch S7b (`lane/n66o`): new checks over the kept frame-window logs of run:2026-11-04-frame (the two
pilot logs), run:2026-11-04-frame2 (five logs) and run:2026-11-04-frame3 (three logs), for the 41 sim/frame rows and the 5
drlg/lifecycle rows of the batch (docs/plans/0066-inventory/README.md § 4).

    python3 -I tools/sweep2_s7b.py check [--out F]

One pass per log. `tools/frame_window.py`'s `parse_log` (the reader's own parser, unchanged) splits each log into windows;
nothing else of the reader is used, so every count below is this tool's own. The windows: every window of the ten kept
logs (13; the dev logs are not read). "counted" is the set of plan 0055's counted windows (frame_p55c_counts.COUNTED plus
the three town windows).

Sections (row ids are the inventory's: fN sim-frame, lN drlg-lifecycle):

  tick     f4, l1: FT0/FT1 alternate; FT0.fr = pre + 1 = the previous FT0's fr + 1; FT1.fr = FT0.fr; one game pointer
  drain    f1, f2, f22, f28, f120: MSG0/MSG1/SYS lines inside a tick (FT0..FT1) and between ticks; a MSG0's stamp against
           the last FT1's and the next FT0's
  sysmsg   f25: drain gaps holding both SYS and MSG0, the order of the two kinds
  player   f26: a MSG0's `pl` and `id` against the type-0 unit of the window's UE0 lines
  ranks    f5, f21, f116, l5: the rank of every depth-0 line in a tick (ACL 1, RU0 3, UE0 4-13 by type and list, SV0 14,
           TM T20 17, D12 18, U11 19, S1500 20), inversions and the adjacent rank pairs that separate the order
  rr       l5: RR lines (ActiveRoomFree) by place: after a D12 line in a frame = 0 mod 12, or elsewhere
  tm       f77, l8: TM pairs in one frame; S1500 at every in-window frame = 0 mod 1500 and at no other; the T20/D12/U11
           lines at their due frames
  slot     f31: slot UE0 rf = fr, every-frame UE0 rf = -1
  k11      f14, f48: kind-11 runs: the QE inside each (kind 11, the player, asked = fr + 30), the next run at fr + 30
  e5       f41, f42, f32: timed records (a slot run matched to its QE): queued frame < run frame; QE asked <= fr (raised);
           every-frame records (QF, QE asked -1): the first run's frame against the walk-order prediction
  rooms    f59, f60, f61, f62, f123, l6, l15: the act room lists modelled from RC (prepend) and RR (unlink); each walk's RU0
           order against the model; walk frames against the act flag (set by RC, cleared after the walk); old rooms' seed
           one step from RU0 to RU1; new rooms' flags; RC places and their room's first walk; RC flags by act
  sv       f66: SV0/SV1 lines: frame, return address
  acl      f52: ACL lines, their place, the WEND ACL stop count against the frames
  quiet    f91: XS lines at depth 0 before the first rank >= 3 line of a tick (ranks 1-2) and between the last rank 4-13
           line and the first TM or FT1 in frames with no RC, RR or SV0 (ranks 14-16); game seed at FT0 against the next
  gsites   f92: the sites of the XS lines that step the game seed (its low word at the step), by function
  ai       f124: XS lines at AI-function sites by the open UE0's (type, kind)
  recount  f95-f110: this tool's own recount of the counted windows' K3a (UE0 moved neither/own/game), K3e (KD segments),
           K4 trigger sites, K5 pairs, compared with the stated numbers

Stdlib only. Read-only. Output ends with `S7b total bad=N`.
"""
import argparse
import bisect
import collections
import csv
import glob
import io
import os
import re
import sys
from contextlib import redirect_stdout

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import frame_window as fw  # noqa: E402

LOGDIR = os.path.join(ROOT, "workspace", "logs", "frame")
LOGS = ["2026-11-04-frame-s1-5501-town", "2026-11-04-frame-s1-5501-pack",
        "2026-11-04-frame2-s1-5501-pack1", "2026-11-04-frame2-s1-5503-maze1", "2026-11-04-frame2-s1-5505-maze1",
        "2026-11-04-frame2-s1-5507-mazeh", "2026-11-04-frame2-s1-5509-mazeh",
        "2026-11-04-frame3-s1-5511-packd", "2026-11-04-frame3-s1-5513-den", "2026-11-04-frame3-s1-5515-den"]
# plan 0055's counted windows: frame_p55c_counts.COUNTED (the seven with XS) and the three town windows (K1)
COUNTED_XS = {("5501-pack1", 3486), ("5503-maze1", 1897), ("5503-maze1", 7942), ("5505-maze1", 7942), ("5507-mazeh", 2094),
              ("5511-packd", 1539), ("5511-packd", 2063)}
DEV_GLOB = "dev-2026-11-04-frame2-*.log"     # frame_p55c_counts' dev set for run:2026-11-04-frame2 (frame3 has none)
COUNTED_TOWN = {("5501-town", 501), ("5501-town", 752), ("5501-town", 1375)}
OPENS = {"UE0": "UE1", "MSG0": "MSG1", "RU0": "RU1", "TQ0": "TQ1", "SV0": "SV1"}
CLOSES = {v: k for k, v in OPENS.items()}
RANK = {3: (4, 5), 0: (6, 7), 1: (8, 9), 2: (10, 11), 4: (12, 13)}     # tools/gdb/frame.py RANK: type -> (ef, slot)
TM_RANK = {"T20": 17, "D12": 18, "U11": 19, "S1500": 20}
TM_PERIOD = {"T20": 20, "D12": 12, "U11": 11, "S1500": 1500}
SV_CALL_RA = 0x0052D4C2            # the return address of ClientsRoomSync's SaveGameClients call 0x0052D4BD
CRS = (0x0052D440, 0x0052D4D7)     # fn:sub_0052D440_ClientsRoomSync, its last instruction read (0x0052D453-0x0052D4D7)
UNIT_SEED_SITE, ITEM_SEED_SITE = 0x00552E31, 0x00552E9F
NEG1 = 0xFFFFFFFF


def tag_of(name):
    return name.split("-s1-", 1)[1]


def symbols():
    rows = []
    with open(os.path.join(ROOT, "re", "symbols.csv")) as f:
        for r in csv.DictReader(f):
            if r["kind"] == "func":
                rows.append((int(r["address"], 16), r["name"]))
    rows.sort()
    return rows


SYMS = symbols()
SADDR = [a for a, _ in SYMS]


def fname(a):
    i = bisect.bisect_right(SADDR, a) - 1
    return SYMS[i][1] if i >= 0 else "?"


def loc_of(o):
    return o.get("ra") or o["site"]


def s32(v):
    return v - (1 << 32) if v >= 1 << 31 else v


class S7b:
    def __init__(self):
        self.c = collections.defaultdict(collections.Counter)    # section -> counters
        self.bad = collections.Counter()
        self.ex = collections.defaultdict(list)                  # section -> examples

    def note(self, sec, key, n=1):
        self.c[sec][key] += n

    def fail(self, sec, why, ex):
        self.bad[sec] += 1
        if len(self.ex[sec]) < 8:
            self.ex[sec].append("%s: %s" % (why, ex))

    # ------------------------------------------------------------------------------------------------ per window
    def window(self, tag, w):
        key = (tag, w["start"])
        counted = key in COUNTED_XS or key in COUNTED_TOWN
        L = [(n, t, o) for n, t, o in w["lines"] if t not in ("WIN", "WEND")]
        wid = "%s#%s" % (tag, w["wid"])
        self.note("windows", "all")
        self.note("windows", "counted" if counted else "uncounted")
        frames = self.tick(wid, L, w)
        self.drain(wid, L)
        self.player(wid, L)
        self.ranks(wid, L)
        self.tm(wid, L, frames)
        self.slot(wid, L)
        self.k11(wid, L)
        self.e5(wid, L)
        self.rooms(wid, L)
        self.sv(wid, L)
        self.acl(wid, L, w, frames)
        self.quiet(wid, L)
        self.gsites(wid, L)
        self.ai(wid, L)
        if key in COUNTED_XS:
            self.recount(wid, L)
            self.pairs("counted", wid, L)
            self.touches(wid, L)
        if any(t == "XS" for _n, t, _o in L):
            self.note("windows", "with_xs")
            self.touches(wid, L, "all_xs_windows")
        self.pairs("all_kept", wid, L)

    # f4, l1 ---------------------------------------------------------------------------------------------------
    def tick(self, wid, L, w):
        S = "tick"
        open_fr, last_fr, games, frames = None, None, set(), []
        for n, t, o in L:
            if t == "FT0":
                if open_fr is not None:
                    self.fail(S, "FT0 inside a tick", (wid, n))
                if o["fr"] != o["pre"] + 1:
                    self.fail(S, "fr != pre + 1", (wid, n))
                if last_fr is not None and o["fr"] != last_fr + 1:
                    self.fail(S, "FT0 not consecutive", (wid, n, last_fr, o["fr"]))
                games.add(o.get("game"))
                open_fr = last_fr = o["fr"]
                frames.append(o["fr"])
                self.note(S, "FT0")
            elif t == "FT1":
                if open_fr is None or o["fr"] != open_fr:
                    self.fail(S, "FT1 without its FT0", (wid, n))
                open_fr = None
                self.note(S, "FT1")
        if open_fr is not None:
            self.fail(S, "window ends inside a tick", wid)
        if len(games) != 1:
            self.fail(S, "games", (wid, games))
        wf = (w.get("wend") or {}).get("frames")
        if wf != len(frames):
            self.fail(S, "WEND frames", (wid, wf, len(frames)))
        self.note(S, "windows")
        return frames

    # f1, f2, f22, f28, f120 ------------------------------------------------------------------------------------
    def drain(self, wid, L):
        S = "drain"
        tick, last_ft1, ops = False, None, collections.Counter()
        pend = []          # MSG0 lines since the last FT1, checked at the next FT0
        for n, t, o in L:
            if t == "FT0":
                tick = True
                for (pn, pfr) in pend:
                    if pfr != o["fr"] - 1:
                        self.fail(S, "MSG0 stamp != next FT0 - 1", (wid, pn))
                    else:
                        self.note(S, "msg0_before_next_ft0")
                pend = []
            elif t == "FT1":
                tick = False
                last_ft1 = o["fr"]
            elif t in ("MSG0", "MSG1", "SYS"):
                if tick:
                    self.fail(S, "%s inside a tick" % t, (wid, n))
                else:
                    self.note(S, t + "_between")
                if t == "MSG0":
                    ops[o.get("op")] += 1
                    if last_ft1 is None:
                        self.note(S, "msg0_before_first_ft1")
                    elif o["fr"] != last_ft1:
                        self.fail(S, "MSG0 stamp != last FT1", (wid, n, o["fr"], last_ft1))
                    else:
                        self.note(S, "msg0_stamp_eq_last_ft1")
                    pend.append((n, o["fr"]))
                if t == "SYS":
                    self.note(S, "sys_ty_%d" % o["ty"])
        self.note(S, "msg0_after_last_ft0", len(pend))
        for op, k in ops.items():
            self.note(S, "op_0x%02x" % (op if op is not None else 0), k)

    # f25: drain gaps with both SYS and MSG0 --------------------------------------------------------------------
    def sysmsg(self, wid, L):
        pass

    # f26 ------------------------------------------------------------------------------------------------------
    def player(self, wid, L):
        S = "player"
        pu = collections.defaultdict(set)
        for n, t, o in L:
            if t == "UE0" and o["ty"] == 0:
                pu[o["u"]].add(o["id"])
        gap = []
        for n, t, o in L:
            if t == "MSG0":
                if o["pl"] in pu and o["id"] in pu[o["pl"]]:
                    self.note(S, "msg0_pl_is_type0_unit")
                elif not pu:
                    self.note(S, "msg0_no_type0_ue0")
                else:
                    self.fail(S, "MSG0 pl not a type-0 unit of the window", (wid, n))
            # f25: SYS and MSG0 in one gap
            if t == "FT0":
                self._gap(wid, gap)
                gap = []
            elif t in ("SYS", "MSG0"):
                gap.append((n, t))
        self._gap(wid, gap)
        self.note(S, "type0_units_%d" % len(pu))

    def _gap(self, wid, gap):
        S = "sysmsg"
        kinds = [t for _n, t in gap]
        if "SYS" in kinds and "MSG0" in kinds:
            self.note(S, "gaps_both")
            first_msg = kinds.index("MSG0")
            last_sys = len(kinds) - 1 - kinds[::-1].index("SYS")
            self.note(S, "sys_all_before_msg0" if last_sys < first_msg else "sys_after_a_msg0")
        elif "SYS" in kinds:
            self.note(S, "gaps_sys_only")
        elif "MSG0" in kinds:
            self.note(S, "gaps_msg0_only")

    # f5, f21, f116, l5 ----------------------------------------------------------------------------------------
    def ranks(self, wid, L):
        S = "ranks"
        tick, depth, last, fr = False, [], None, None
        seen_kinds = collections.Counter()
        for n, t, o in L:
            if t == "FT0":
                tick, depth, last, fr = True, [], None, o["fr"]
                continue
            if t == "FT1":
                tick = False
                continue
            if not tick:
                continue
            r = None
            if not depth:
                if t == "ACL":
                    r = 1
                elif t == "RU0":
                    r = 3 if "ai" in o else None
                    if r is None:
                        self.note(S, "ru0_one")
                elif t == "UE0":
                    r = RANK[o["ty"]][0 if o["lst"] == "ef" else 1]
                elif t == "SV0":
                    r = 14
                elif t == "TM":
                    r = TM_RANK[o["which"]]
            if t in OPENS:
                depth.append(t)
            elif t in CLOSES:
                if depth and depth[-1] == CLOSES[t]:
                    depth.pop()
                else:
                    self.fail(S, "unbalanced close", (wid, n))
            if r is None:
                continue
            seen_kinds[r] += 1
            if r in (5, 6, 10, 11, 12, 13):
                self.note(S, "rank_%02d_in %s" % (r, wid))
            if last is not None:
                if r < last:
                    self.fail(S, "rank inversion", (wid, n, last, r))
                elif r > last:
                    self.note(S, "pair_%d_%d" % (last, r))
            last = r
        for r, k in sorted(seen_kinds.items()):
            self.note(S, "rank_%02d_lines" % r, k)

    # rr (l5) and tm (f77, l8) ------------------------------------------------------------------------------------
    def tm(self, wid, L, frames):
        S = "tm"
        byfr = collections.defaultdict(list)
        tick, fr, after_d12 = False, None, False
        for n, t, o in L:
            if t == "FT0":
                tick, fr, after_d12 = True, o["fr"], False
            elif t == "FT1":
                tick = False
            elif t == "TM" and tick:
                byfr[fr].append(o["which"])
                if o["which"] == "D12":
                    after_d12 = True
                elif o["which"] in ("U11", "S1500"):
                    after_d12 = False if o["which"] == "S1500" else after_d12
                if o["which"] == "U11" and o.get("act") is not None:
                    self.note(S, "u11_act_%s" % o["act"])
            elif t == "TM":
                self.fail(S, "TM outside a tick", (wid, n))
            elif t == "RR":
                if tick and after_d12 and fr % 12 == 0:
                    self.note("rr", "after_D12_in_mod12_frame")
                else:
                    self.note("rr", "elsewhere_%s" % ("tick" if tick else "between"))
                    self.ex["rr"].append("RR elsewhere %s n=%d fr=%s" % (wid, n, o["fr"])) if len(self.ex["rr"]) < 6 else None
        for f in frames:
            ws = byfr.get(f, [])
            for which, p in TM_PERIOD.items():
                due = f % p == 0
                has = which in ws
                if due and has:
                    self.note(S, "%s_due_present" % which)
                elif due and not has:
                    self.fail(S, "%s due, absent" % which, (wid, f))
                elif has:
                    self.fail(S, "%s present, not due" % which, (wid, f))
                else:
                    self.note(S, "%s_not_due_absent" % which)
            if f % 750 == 0 and f % 1500 != 0:
                self.note(S, "frame_750_mod_1500_no_S1500" if "S1500" not in ws else "frame_750_with_S1500")
            order = [TM_RANK[x] for x in ws]
            if len(ws) >= 2:
                self.note(S, "frames_2plus_tm")
                self.note(S, "set_" + "+".join(ws))
                if order != sorted(order) or len(set(order)) != len(order):
                    self.fail(S, "TM order", (wid, f, ws))

    # f31 ------------------------------------------------------------------------------------------------------
    def slot(self, wid, L):
        S = "slot"
        for n, t, o in L:
            if t != "UE0":
                continue
            if o["lst"] == "slot":
                if o["rf"] == o["fr"]:
                    self.note(S, "slot_rf_eq_fr")
                else:
                    self.fail(S, "slot rf != fr", (wid, n))
            else:
                if o["rf"] == NEG1:
                    self.note(S, "ef_rf_neg1")
                else:
                    self.fail(S, "ef rf != -1", (wid, n))
            self.note(S, "ue0_ty%d_%s" % (o["ty"], o["lst"]))

    # f14, f48 -------------------------------------------------------------------------------------------------
    def k11(self, wid, L):
        S = "k11"
        runs = []
        cur = None
        for n, t, o in L:
            if t == "UE0":
                cur = (n, o, []) if (o["ty"] == 0 and o["kind"] == 11) else None
                if cur:
                    runs.append(cur)
            elif t == "UE1":
                cur = None
            elif t == "QE" and cur is not None:
                cur[2].append(o)
            elif t == "XS" and cur is not None:
                self.fail(S, "XS inside a kind-11 run", (wid, n))
        frs = collections.defaultdict(list)
        for n, o, qs in runs:
            self.note(S, "runs")
            frs[o["id"]].append(o["fr"])
            q11 = [q for q in qs if q["kind"] == 11]
            if len(q11) == 1 and q11[0]["ut"] == 0 and q11[0]["id"] == o["id"] and s32(q11[0]["asked"]) == o["fr"] + 30:
                self.note(S, "requeue_fr_plus_30")
            else:
                self.fail(S, "kind-11 run without its QE at fr + 30", (wid, n, qs))
            if len(qs) != len(q11):
                self.fail(S, "other QE inside a kind-11 run", (wid, n))
        for pid, fs in frs.items():
            for a, b in zip(fs, fs[1:]):
                if b - a == 30:
                    self.note(S, "next_run_at_plus_30")
                else:
                    self.fail(S, "kind-11 interval", (wid, pid, a, b))

    # f41, f42, f32 ------------------------------------------------------------------------------------------------
    def e5(self, wid, L):
        S = "e5"
        # the place of every line: (frame stamp, in tick?, rank of the open walk or depth-0 context)
        tick, fr, ctx, depth = False, None, 0, []
        qe = collections.defaultdict(list)       # (ut, id, kind, effective frame) -> [(queued fr, n, asked)]
        ef_q = []                                 # (n, ut, id, kind, fr, tick, ctx)
        first_ef = {}                             # (ty, id, kind) -> list of (n, fr) of ef UE0
        ef_runs = collections.defaultdict(list)
        slot_runs = []
        for n, t, o in L:
            if t == "FT0":
                tick, fr, ctx, depth = True, o["fr"], 0, []
                continue
            if t == "FT1":
                tick, fr, ctx = False, o["fr"], 21
                continue
            if t in ("MSG0", "SYS"):
                fr = o["fr"]
            if t == "UE0":
                r = RANK[o["ty"]][0 if o["lst"] == "ef" else 1]
                if not depth:
                    ctx = r
                if o["lst"] == "ef":
                    ef_runs[(o["ty"], o["id"], o["kind"])].append((n, o["fr"]))
                else:
                    slot_runs.append((n, o))
            elif t == "RU0" and not depth and tick:
                ctx = 3
            elif t == "SV0" and not depth:
                ctx = 14
            elif t == "TM" and not depth:
                ctx = TM_RANK[o["which"]]
            if t in OPENS:
                depth.append(t)
            elif t in CLOSES and depth:
                depth.pop()
                if not depth and t == "UE1":
                    pass
            if t == "QE":
                a = s32(o["asked"])
                if a != -1 and (a - o["fr"]) % 64 == 0:
                    self.note(S, "qe_into_current_slot_asked_fr_plus_%d" % (a - o["fr"]))
                if a == -1:
                    ef_q.append((n, o["ut"], o["id"], o["kind"], o["fr"], tick, ctx, "QE-1"))
                    continue
                eff = a if a > o["fr"] else o["fr"] + 1
                qe[(o["ut"], o["id"], o["kind"], eff)].append((o["fr"], n, a))
                if a <= o["fr"]:
                    self.note(S, "qe_asked_le_fr_raised")
            elif t == "QF":
                ef_q.append((n, o["ut"], o["id"], o["kind"], o["fr"], tick, ctx, "QF"))
        # timed half
        for n, o in slot_runs:
            k = (o["ty"], o["id"], o["kind"], o["fr"])
            cands = [q for q in qe.get(k, []) if q[1] < n]
            if not cands:
                self.note(S, "slot_run_queued_before_window")
                continue
            qfr, qn, a = cands[-1]
            if qfr >= o["fr"]:
                self.fail(S, "timed record ran in its queue frame", (wid, n))
            else:
                self.note(S, "slot_run_matched_queued_earlier_frame")
                if a <= qfr:
                    self.note(S, "slot_run_from_raised_qe")
                if o["fr"] == qfr + 1:
                    self.note(S, "slot_run_at_queue_frame_plus_1")
        # every-frame half
        for n, ut, uid, kind, qfr, tk, cx, how in ef_q:
            runs = [r for r in ef_runs.get((ut, uid, kind), []) if r[0] > n]
            target = RANK[ut][0]
            if tk:
                pred = qfr if cx < target else qfr + 1
                where = "tick_ctx%d_target%d" % (cx, target)
            else:
                pred = qfr + 1
                where = "between_target%d" % target
            if not runs:
                self.note(S, "ef_q_no_run_in_window_ut%d" % ut)
                continue
            got = runs[0][1]
            if got == pred:
                self.note(S, "ef_ok_ut%d_%s_%s_%s" % (ut, "same" if pred == qfr else "next", how, where))
                if tk and cx < target and cx >= 4:
                    self.note(S, "ef_same_frame_later_walk_ut%d_from_rank%d" % (ut, cx))
            else:
                self.fail(S, "ef first run frame", (wid, n, ut, uid, kind, qfr, where, got))

    # f59, f60, f61, f62, f123, l6, l15 -------------------------------------------------------------------------
    def rooms(self, wid, L):
        S = "rooms"
        acts_walked = {o["act"] for _n, t, o in L if t == "RU0" and "ai" in o}
        model = {}                      # act -> list newest first, or None until the first walk
        created = collections.defaultdict(list)    # act -> rooms created in the window before the first walk, oldest first
        flag = collections.defaultdict(bool)
        walk = None                     # (act, frame, [rooms]) being read
        tick, fr, depth, ctx = False, None, [], 0
        due, walked = set(), set()
        rc_place = []                   # (room, frame, place, line) of every server RC
        rc_frame_seen = set()
        walk_frames = collections.defaultdict(list)
        ru0 = {}
        inwalk = collections.defaultdict(list)

        def end_walk():
            nonlocal walk
            if walk is None:
                return
            act, wf, rooms = walk
            walk = None
            during = inwalk.pop(act, [])           # created inside this walk: linked at the head, not visited (H2c)
            m = model.get(act)
            if m is not None:
                m = [r for r in m if r not in during]
            if m is None:
                pre = list(reversed(created[act]))
                live = [r for r in pre if r in rooms]
                if rooms[:len(live)] == live:
                    self.note(S, "first_walk_prefix_ok_rooms_%d" % len(live) if live else "first_walk_no_prefix")
                    if len(live) >= 2:
                        self.note(S, "first_walk_prefix_2plus")
                else:
                    self.fail(S, "first walk prefix", (wid, wf, live, rooms[:len(live)]))
                model[act] = list(reversed(during)) + list(rooms)
            else:
                if rooms == m:
                    self.note(S, "walk_eq_model")
                    self.note(S, "walk_rooms", len(rooms))
                else:
                    self.fail(S, "walk != model", (wid, wf, len(rooms), len(m), [r for r in m if r not in rooms],
                                                   [r for r in rooms if r not in m]))
                model[act] = list(reversed(during)) + list(rooms)
            if not flag[act]:
                self.fail(S, "walk without the act flag", (wid, wf))
            else:
                self.note(S, "walk_with_flag")
            flag[act] = False
            walk_frames[act].append(wf)

        for n, t, o in L:
            if t == "FT0":
                tick, fr, depth, ctx = True, o["fr"], [], 0
                due = {act for act in acts_walked if flag[act]}
                walked = set()
                continue
            if t == "FT1":
                end_walk()
                tick = False
                for act in due:
                    if act in walked:
                        self.note(S, "flag_set_at_ft0_walked")
                    else:
                        self.fail(S, "flag set at FT0, no walk", (wid, fr))
                for act in walked - due:
                    self.fail(S, "walk with no flag at FT0", (wid, fr))
                continue
            if not depth and tick and t in ("UE0", "SV0", "TM", "ACL"):
                ctx = TM_RANK[o["which"]] if t == "TM" else {"UE0": 4, "SV0": 14, "ACL": 1}[t]
            if t == "RU0" and "ai" in o:
                act = o["act"]
                if walk is None or walk[0] != act or walk[1] != fr:
                    end_walk()
                    walk = (act, fr, [])
                    walked.add(act)
                    # the flag decides the walk at rank 3: predict walks
                walk[2].append(o["room"])
                ru0[o["room"]] = o
            elif t == "RU1" and "ai" in o:
                a = ru0.get(o["room"])
                if a is not None:
                    f0 = a["f"]
                    if f0 & 3 == 3:
                        s0, s1 = fw.sd(a["rs"]), fw.sd(o["rs"])
                        if fw.step(s0) == s1:
                            self.note(S, "old_room_one_step")
                        else:
                            k = fw.steps(s0, s1, 64)
                            self.fail(S, "old room seed not one step", (wid, o["fr"], k))
                    elif f0 & 1 == 0:
                        if o["f"] & 3 == 3:
                            self.note(S, "new_room_populated_flags_3")
                        else:
                            self.fail(S, "new room flags after", (wid, o["fr"], f0, o["f"]))
                        k = fw.steps(fw.sd(a["rs"]), fw.sd(o["rs"]), 100000)
                        self.note(S, "new_room_steps_known" if k is not None else "new_room_steps_unknown")
                    else:
                        self.note(S, "restore_room_f%d_to_f%d" % (f0, o["f"]))
            elif t != "RU1" and t not in ("XS",) and walk is not None and not (t in ("RC", "RR", "QE", "QF", "KD", "UE0", "UE1") and depth):
                if t not in ("RC", "RR", "QE", "QF", "KD"):
                    end_walk()
            if t in OPENS:
                depth.append(t)
            elif t in CLOSES and depth:
                depth.pop()
            if t == "RC":
                act = o["act"]
                if act not in acts_walked:
                    self.note(S, "rc_act_never_walked_f%d" % o["f"])
                    continue
                self.note(S, "rc_server_f%d" % o["f"])
                if walk is not None and walk[0] == act:
                    inwalk[act].append(o["room"])
                elif model.get(act) is None:
                    created[act].append(o["room"])
                else:
                    model[act].insert(0, o["room"])
                if walk is not None and walk[0] == act:
                    place = "in_walk"
                elif not tick:
                    place = "between"
                elif depth:
                    place = "in_event"
                else:
                    place = "depth0"
                rc_place.append((o["room"], fr, place, n))
                self.note(S, "rc_place_" + place + ("_after_rank%d" % ctx if place == "depth0" else ""))
                flag[act] = True
                if place == "in_walk":
                    # set during the walk; the walk's end clears it (H2c)
                    self._inwalk = getattr(self, "_inwalk", []) + [(wid, o["room"], fr)]
            elif t == "RR":
                act = o["act"]
                self.note(S, "rr_%s_act_%s" % ("walked" if act in acts_walked else "never_walked", "tick" if tick else "between"))
                if act in acts_walked and tick:
                    self.note(S, "rr_walked_tick_after_rank%d_fr_mod12_%s" % (ctx, fr % 12 == 0))
                if model.get(act) is not None and o["room"] in model[act]:
                    model[act].remove(o["room"])
                    self.note(S, "rr_unlinked_from_model")
                elif act in acts_walked:
                    if o["room"] in created[act]:
                        created[act].remove(o["room"])
                    self.note(S, "rr_room_not_in_model")
        end_walk()
        # H2c: a room created inside its act's walk is cleared with the walk's flag; its first RU0 comes at the next walk
        # l6: a room's first RU0 frame against its RC frame and place
        ru0s = collections.defaultdict(list)
        last_fr = None
        for n, t, o in L:
            if t == "RU0" and "ai" in o:
                ru0s[o["room"]].append((o["fr"], n))
            if t == "FT0":
                last_fr = o["fr"]
        for room, rf, place, n in rc_place:
            got = next((x for x in ru0s.get(room, []) if x[1] > n), None)
            if got is None:
                self.note(S, "rc_%s_no_walk_after%s" % (place, "_last_frame" if rf == last_fr else ""))
                if place != "in_walk" and rf != last_fr:
                    self.fail(S, "RC with no walk after, not at the window's last frame", (wid, room, rf))
                continue
            if place == "in_walk":
                self.note(S, "rc_in_walk_first_ru0_after_%d" % (got[0] - rf))
            elif got[0] == rf + 1:
                self.note(S, "rc_%s_first_ru0_next_frame" % place)
            else:
                self.fail(S, "first RU0 not frame + 1", (wid, room, rf, place, got[0]))
        # walk frames predicted: a walk at frame F iff an RC of the act came after its last walk (checked above per walk);
        # a frame with an RC at rank <= 14 of frame N and no walk at N + 1 would fail rc_*_first_ru0_next_frame
        for act, fs in walk_frames.items():
            self.note(S, "walks", len(fs))

    # f66 ------------------------------------------------------------------------------------------------------
    def sv(self, wid, L):
        S = "sv"
        for n, t, o in L:
            if t == "SV0":
                ok = o["fr"] % 8192 == 0 and o["ra"] == SV_CALL_RA
                if ok:
                    self.note(S, "sv0_at_mod8192_from_ClientsRoomSync")
                else:
                    self.fail(S, "SV0 elsewhere", (wid, n, o["fr"], hex(o["ra"])))
            elif t == "SV1":
                self.note(S, "sv1")
            elif t == "FT0" and o["fr"] % 8192 == 0:
                self.note(S, "frames_mod8192")

    # f52 ------------------------------------------------------------------------------------------------------
    def acl(self, wid, L, w, frames):
        S = "acl"
        hits = ((w.get("wend") or {}).get("hits") or {}).get("ACL")
        if hits is not None:
            if hits == len(frames):
                self.note(S, "acl_stops_eq_frames")
                self.note(S, "acl_stops", hits)
            else:
                self.fail(S, "ACL stops != frames", (wid, hits, len(frames)))
        else:
            self.note(S, "no_acl_stop_count")
        for n, t, o in L:
            if t == "U11" or (t == "TM" and o["which"] == "U11"):
                self.note(S, "u11_act_%s" % o.get("act"))
            if t == "ACL":
                self.note(S, "acl_line_act%d_r%d" % (o["act"], o["r"]))

    # f91 ------------------------------------------------------------------------------------------------------
    def quiet(self, wid, L):
        S = "quiet"
        tick, depth, phase, fr = False, [], 0, None
        frame_lines = []
        for n, t, o in L:
            if t == "FT0":
                tick, depth, frame_lines, fr = True, [], [(n, t, o)], o["fr"]
                continue
            if tick:
                frame_lines.append((n, t, o))
            if t == "FT1" and tick:
                tick = False
                self._quiet_frame(wid, frame_lines)

    def _quiet_frame(self, wid, F):
        S = "quiet"
        has_xs = any(t == "XS" for _n, t, _o in F)
        # ranks 1-2: XS before the first RU0/UE0/RC/SV0/TM/RR line (ACL is rank 1)
        first = None
        for i, (n, t, o) in enumerate(F[1:], 1):
            if t in ("RU0", "UE0", "RC", "SV0", "TM", "RR", "FT1", "QE", "QF"):
                first = i
                break
        pre = [x for x in F[1:first] if x[1] == "XS"]
        self.note(S, "frames")
        self.note(S, "frames_with_xs" if has_xs else "frames_no_xs")
        if has_xs:
            self.note(S, "xs_frames_ranks12_xs_%s" % ("0" if not pre else "some"))
            if pre:
                self.fail(S, "XS at ranks 1-2", (wid, F[0][2]["fr"], [hex(loc_of(x[2])) for x in pre][:4]))
        # game seed at FT0 against the first later line with a gs
        g0 = F[0][2].get("gs")
        nxt = next(((t, o) for _n, t, o in F[1:] if isinstance(o, dict) and o.get("gs")), None)
        if nxt is not None:
            acl = any(t == "ACL" for _n, t, _o in F[1:first])
            if nxt[1]["gs"] == g0:
                self.note(S, "gs_ft0_eq_next")
            elif acl:
                self.note(S, "gs_moved_with_acl")
            else:
                self.fail(S, "game seed moved at ranks 1-3 with no ACL", (wid, F[0][2]["fr"], nxt[0]))
        # ranks 14-16: after the last depth-0 close of an event (UE1, RU1) and before the first TM or FT1
        types = {t for _n, t, _o in F}
        if not has_xs:
            return
        if types & {"RC", "RR", "SV0"}:
            self.note(S, "xs_frames_with_rc_rr_sv")
            return
        last_close = 0
        depth = 0
        for i, (n, t, o) in enumerate(F):
            if t in OPENS:
                depth += 1
            elif t in CLOSES:
                depth -= 1
                if depth == 0:
                    last_close = i
        end = next((i for i, (n, t, o) in enumerate(F) if t in ("TM", "FT1") and i > last_close), len(F) - 1)
        mid = [x for x in F[last_close + 1:end] if x[1] == "XS"]
        self.note(S, "quiet_frames_r14_16_xs_%s" % ("0" if not mid else "some"))
        if mid:
            self.fail(S, "XS at ranks 14-16 in a frame with no RC, RR or SV0",
                      (wid, F[0][2]["fr"], [fname(loc_of(x[2])) for x in mid][:4]))

    # f92 ------------------------------------------------------------------------------------------------------
    def gsites(self, wid, L):
        """J2's kind (1): the game-seed steps by place. Sites, not low words: UnitSeedInit+0x41 (every unit SUnitCreate
        makes), ItemSeedInit+0xF (items), and RoomPopulate's own loop at 0x0054ED96 (it loads [game+0xD0] at 0x0054ED90).
        For each, the XS lines whose low word equals the last logged game seed's low (a step on the game seed) or not."""
        S = "gsites"
        sites = {UNIT_SEED_SITE: "UnitSeedInit", ITEM_SEED_SITE: "ItemSeedInit", 0x0054ED96: "RoomPopulate"}
        stack, tick, cur = [], False, None
        for n, t, o in L:
            if t == "FT0":
                tick = True
            elif t == "FT1":
                tick = False
            g = o.get("gs") if isinstance(o, dict) else None
            if g:
                cur = fw.sd(g)
            if t in OPENS:
                stack.append((t, o))
            elif t in CLOSES and stack:
                stack.pop()
            elif t == "XS" and loc_of(o) in sites:
                top = stack[0] if stack else None
                place = ("between" if not tick else "tick_nopair") if top is None else (
                    "UE0_ty%d" % top[1]["ty"] if top[0] == "UE0" else top[0])
                on_game = cur is not None and o["low"] == cur[0]
                self.note(S, "%s in %s %s" % (sites[loc_of(o)], place, "game_low" if on_game else "other_low"))
                if on_game:
                    cur = fw.step(cur)

    # f124 -----------------------------------------------------------------------------------------------------
    def ai(self, wid, L):
        S = "ai"
        stack = []
        for n, t, o in L:
            if t in OPENS:
                stack.append((t, o))
            elif t in CLOSES and stack:
                stack.pop()
            elif t == "XS":
                fn = fname(loc_of(o))
                if not (fn.startswith("Ai") or "_Ai" in fn or fn.startswith("MonAi") or "_MonAi" in fn):
                    continue
                top = next((x for x in reversed(stack) if x[0] == "UE0"), None)
                if top is None:
                    self.note(S, "ai_xs_no_ue0 %s" % fn)
                    continue
                u = top[1]
                self.note(S, "ty%d kind%d %s" % (u["ty"], u["kind"], "cb" if u.get("cb") else "dispatch"))
                self.note("ai_fn", "kind%d %s" % (u["kind"], fn))

    # f95-f110 -------------------------------------------------------------------------------------------------
    def recount(self, wid, L):
        S = "recount"
        stack = []
        kd_seg = None
        frame_movers = collections.defaultdict(list)
        for n, t, o in L:
            if t == "FT0":
                if kd_seg is not None:
                    self._kd_close(kd_seg)
                    kd_seg = None
            if t in OPENS:
                stack.append((t, o, not stack))
            elif t in CLOSES and stack:
                tg, a, top = stack.pop()
                if tg == "UE0":
                    self.note(S, "ue0")
                    gm = a.get("gs") != o.get("gs")
                    um = bool(a.get("us") and o.get("us") and a["us"] != o["us"])
                    self.note(S, "ue0_" + ("both" if gm and um else "game" if gm else "own" if um else "neither"))
                    if gm:
                        self.note(S, "ue0_game_ty%d_kind%d_%s" % (a["ty"], a["kind"], a["lst"]))
                        if top:
                            frame_movers[a["fr"]].append((a["ty"], a["id"]))
                    if gm or um:
                        self.note(S, "ue0_either")
            elif t == "KD":
                if kd_seg is not None:
                    self._kd_close(kd_seg)
                kd_seg = {"unit": 0, "item": 0}
                self.note(S, "kd")
            elif t == "XS":
                loc = loc_of(o)
                if kd_seg is not None:
                    if loc == UNIT_SEED_SITE:
                        kd_seg["unit"] += 1
                    elif loc == ITEM_SEED_SITE:
                        kd_seg["item"] += 1
            if t == "UE1" and kd_seg is not None and not stack:
                self._kd_close(kd_seg)
                kd_seg = None
        if kd_seg is not None:
            self._kd_close(kd_seg)
        self.note(S, "game_movers_top %s" % wid, sum(len(v) for v in frame_movers.values()))

    # K5 over every window of a log set: top-level UE0 that moved the game seed, consecutive ones of different units in a
    # frame; handed (the second's entry gs = the first's exit gs) and in rank order
    def pairs(self, label, wid, L):
        S = "pairs_" + label
        stack, fr = [], collections.defaultdict(list)
        for n, t, o in L:
            if t in OPENS:
                stack.append((t, o, not stack))
            elif t in CLOSES and stack:
                tg, a, top = stack.pop()
                if tg == "UE0" and top and a.get("gs") != o.get("gs"):
                    fr[a["fr"]].append((a, o))
        for f, v in sorted(fr.items()):
            for (a0, a1), (b0, b1) in zip(v, v[1:]):
                if (a0["ty"], a0["id"]) == (b0["ty"], b0["id"]):
                    continue
                ra = RANK[a0["ty"]][0 if a0["lst"] == "ef" else 1]
                rb = RANK[b0["ty"]][0 if b0["lst"] == "ef" else 1]
                handed = a1["gs"] == b0["gs"]
                self.note(S, "pairs")
                self.note(S, "pair_ty%d_then_ty%d" % (a0["ty"], b0["ty"]))
                self.note(S, "handed" if handed else "not_handed")
                if rb < ra:
                    self.fail(S, "pair against rank order", (wid, f))
                self.ex[S].append("%s fr=%d (%d,%d)->(%d,%d) handed=%s" % (wid, f, a0["ty"], a0["id"], b0["ty"], b0["id"], handed))

    # K3b's place split and K4's trigger rows, counted by place and site alone (no seed chaining): every XS of a counted
    # window by place, and the XS at each TOUCH row's locations under the row's trigger
    def touches(self, wid, L, label="counted"):
        S = "touch" if label == "counted" else "touch_" + label
        tick, stack = False, []
        kd_in = set()
        cur_ue = None
        # events holding a KD line (kill trigger)
        st2 = []
        for n, t, o in L:
            if t in OPENS:
                st2.append(n)
            elif t in CLOSES and st2:
                st2.pop()
            elif t == "KD" and st2:
                kd_in.add(st2[0])
        for n, t, o in L:
            if t == "FT0":
                tick = True
            elif t == "FT1":
                tick = False
            if t in OPENS:
                stack.append((n, t, o))
            elif t in CLOSES and stack:
                stack.pop()
            elif t == "XS":
                self.note(S, "xs")
                self.note(S, "xs_" + ("between" if not tick else "tick_pair" if stack else "tick_nopair"))
                loc = loc_of(o)
                for r in fw.TOUCH:
                    if not fw.row_has(r, loc):
                        continue
                    trig = r["trigger"]
                    self.note(S, "any_place %s %s" % (trig, r["fn"].split("@")[0][3:]))
                    top = stack[0] if stack else None
                    ok = False
                    if top is None:
                        pass
                    elif trig == "room":
                        ok = any(x[1] == "RU0" for x in stack)
                    elif trig == "kill":
                        ok = top[0] in kd_in
                    elif trig in ("owner", "defender"):
                        ok = top[1] == "UE0"
                    if ok:
                        self.note(S, "row_%s %s 0x%08X" % (trig, r["fn"].split("@")[0][3:], loc))
                        if trig == "defender":
                            self.note(S, "row_defender_window %s" % wid)
                        if trig in ("owner", "defender"):
                            self.note(S, "row_%s %s 0x%08X in ty%d kind%d" % (trig, r["fn"].split("@")[0][3:], loc,
                                                                             top[2]["ty"], top[2]["kind"]))
                        self.note(S, "row_%s_total" % trig)

    def _kd_close(self, seg):
        self.note("recount", "kd_item%d_unit%d" % (seg["item"], seg["unit"]))
        if seg["item"] > seg["unit"]:
            self.fail("recount", "KD item steps above unit steps", seg)

    # ------------------------------------------------------------------------------------------------- report
    def report(self):
        tot = 0
        for sec in sorted(set(self.c) | set(self.bad)):
            print("== %s bad=%d" % (sec, self.bad[sec]))
            for k, v in sorted(self.c[sec].items()):
                print("  %-60s %d" % (k, v))
            for e in self.ex.get(sec, []):
                print("  ex %s" % (e,))
            tot += self.bad[sec]
        for e in getattr(self, "_inwalk", []):
            print("  rc_in_walk %s" % (e,))
        print("S7b total bad=%d" % tot)
        return tot


# f28, f2, f16: the call sites of the message path (raw-byte scan, each site decoded by r2: tools/sweep2_s7a.py's
# `calls_of`) and the calls of the two loops in address order (objdump, through tools/sweep_s4b.py's listing)
STATIC_CALLS = [(0x0054D750, "SrvPacketDispatch", [0x0053F459]), (0x0053F3D0, "SrvProcessClientMessage", [0x0052D03E]),
                (0x0052CFE0, "SrvDrainMessages", None), (0x00619890, "DUNGEON_RoomCreate", [0x00642369])]
LOOPS = [("client main frame, modes 0 and 1", 0x0044F110, 0x0044F170), ("open-server thread", 0x0044CF5A, 0x0044D01E)]


def static(chk):
    import sweep2_s7a as A          # noqa: E402  (r2 and objdump; imported only here)
    S = "static"
    for tgt, name, want in STATIC_CALLS:
        calls, other, ab = A.calls_of(tgt)
        owners = sorted(set(A.T.pad_entry(c) for c in calls))
        chk.note(S, "%s calls=%d jumps=%d abs=%d owners=%d" % (name, len(calls), len(other), len(ab), len(owners)))
        for c in calls:
            chk.note(S, "  %s call 0x%08X in %s" % (name, c, A.nm(c)))
        if want is not None and (sorted(calls) != sorted(want) or other or ab):
            chk.fail(S, "%s call sites" % name, ([hex(c) for c in calls], other, ab))
    for label, lo, hi in LOOPS:
        ins = A.S.parse_listing(A.S.objdump(lo, hi))
        seq = ["0x%08X %s" % (va, A.nm(int(ops, 16)) if re.match(r"^(0x)?[0-9a-f]+$", ops) else ops)
               for va, (mn, ops) in sorted(ins.items()) if mn == "call"]
        chk.note(S, "loop %s: %s" % (label, " ; ".join(seq)))


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["check"])
    ap.add_argument("--out")
    ap.add_argument("--no-static", action="store_true", help="skip the r2/objdump section (development runs)")
    a = ap.parse_args(argv)
    chk = S7b()
    for name in LOGS:
        path = os.path.join(LOGDIR, name + ".log")
        ws, _outside = fw.parse_log(path)
        for w in ws:
            chk.window(tag_of(name), w)
    if not a.no_static:
        static(chk)
    for path in sorted(glob.glob(os.path.join(LOGDIR, DEV_GLOB))):     # K5's "every development log": the pairs only
        name = os.path.basename(path)[:-4]
        ws, _outside = fw.parse_log(path)
        for w in ws:
            L = [(n, t, o) for n, t, o in w["lines"] if t not in ("WIN", "WEND")]
            chk.pairs("dev", "dev:%s#%s" % (tag_of(name), w["wid"]), L)
    buf = io.StringIO()
    with redirect_stdout(buf):
        bad = chk.report()
    text = buf.getvalue()
    if a.out:
        with open(a.out, "w") as f:
            f.write(text)
    sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
