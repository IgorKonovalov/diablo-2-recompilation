"""Plan 0066 batches S6a (anim/timing) and S6b (anim/movement, anim/README): new tallies over the kept anim logs of
run:2026-10-27-anim, -anim-p2, -anim-p3 and -anim-p3b (the 131 logs of `2026-10-30-anim-p3b-all4.lst`), and a small
static section. No game run, no Ghidra.

Usage:
  python3 -I tools/sweep2_s6ab.py logs [--list <lst>]     # one pass per log: tools/anim.py's Checker (the control)
                                                           # and the S6 observers; heavy: run it alone under
                                                           # `systemd-run --user --scope -p MemoryMax=4G`
  python3 -I tools/sweep2_s6ab.py logs2 [--list <lst>]    # part 2 (S6b, timing 105): the control again and the
                                                           # Obs2 observers; written to check-part2.txt
  python3 -I tools/sweep2_s6ab.py ai78                     # timing row 78 over the plan 0052 ai logs
  python3 -I tools/sweep2_s6ab.py static                   # objdump / r2 / raw-byte facts the log checks lean on

Each check prints `S6 <check> key=value ...` and detail lines; `bad=` counts an observation that contradicts the
statement the check tests (the inventory rows it serves are in each observer's docstring). A statement with no stock
case shows as a zero count, never as a failure. The control is the Checker's own `CHECK anim ...` line, which must
equal the kept `2026-10-30-anim-p3b-check.txt`'s.

Record: findings/anim/experiments.md, the "plan 0066 batches S6a and S6b" addendum to run:2026-10-30-anim-p3b.
Stdlib only, plus tools/anim.py (and its imports), objdump (through tools/sweep_s4b.py) and r2. Read-only.
"""
import bisect
import collections
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import anim as A          # noqa: E402
import anim_rates as AR   # noqa: E402
import rng as RNG         # noqa: E402

ROOT = A.ROOT
EXE = os.path.join(ROOT, "workspace", "install", "app", "game.exe")
DATA = os.path.join(ROOT, "workspace", "merged")
LST = os.path.join(ROOT, "workspace", "logs", "anim", "2026-10-30-anim-p3b-all4.lst")

UI = (0x00624390, 0x00624690)              # UNIT_AnimInit's body (re/symbols.csv: next func UNIT_SetMode 0x00624690)
SUI_SEQ, SUI_PATH = 0x0055343A, 0x00553460  # SUNIT_AnimInit's two UNIT_AnimSetRate returns (static section)
CAN_SUNIT = (0x0055399F, 0x005539AC)       # SUNIT_CancelModeEvents' two UNIT_CancelEvents returns (kinds 0, 1)
MSET_MEG = 0x005A8281                      # UNIT_SetMode(1) in MonModeEndGeneric (WL, RN arrival)
TOWNS = A.TOWNS
PSCHED = {0, 4, 9, 7, 8, 10, 11, 12, 13, 14, 15, 16, 18}
PMOVE = {2, 3, 6, 19}
CHEST_OQ = 0x005863B7


def cdiv(a, b):
    return A.cdiv(a, b)


def ceil_div(a, b):
    return -((-a) // b)


class Rep:
    def __init__(self, name):
        self.name = name
        self.c = collections.Counter()
        self.ex = []
        self.notes = []

    def add(self, k, n=1):
        self.c[k] += n

    def note(self, msg):
        if len(self.notes) < 4:
            self.notes.append(msg)

    def bad(self, msg):
        self.c["bad"] += 1
        if len(self.ex) < 6:
            self.ex.append(msg)

    def done(self, keys_max=60):
        if "bad" not in self.c:
            self.c["bad"] += 0
        ks = sorted(self.c)
        print("S6 %s %s" % (self.name, " ".join("%s=%d" % (k, self.c[k]) for k in ks if self.c[k] or k == "bad")))
        for e in self.ex:
            print("  ex %s" % (e,))
        for e in self.notes:
            print("  note %s" % (e,))
        return self.c["bad"]


R = collections.OrderedDict()


def rep(name):
    if name not in R:
        R[name] = Rep(name)
    return R[name]


def uid(tag, x):
    if tag in ("SR", "MSET", "SCH", "RSC", "CQ", "PL0", "PA0", "WIN"):
        return x["u"]["u"]
    if tag in ("CAN", "PDS", "MDS", "EF", "FREE", "AD0", "PS0", "DR0", "WINX"):
        return x["u"]
    if tag in ("OA0", "OEV", "OQ"):
        return x["o"]["u"]
    if tag == "OA1":
        return x["o"]
    return None


def sr_kind(ra):
    if UI[0] <= ra < UI[1]:
        return "ui"
    if ra in (SUI_SEQ, SUI_PATH):
        return "sui"
    return "o"


def mon_every_frame(d, cls, mode):
    """g_MonModePerFrame (0x006E23D0: always, never, by the MonStats2 +0x104 bit = the `*mv` columns)."""
    a = 0x006E23D0 + 12 * mode
    if d.pe.dw(a):
        return True
    if d.pe.dw(a + 4):
        return False
    ex = d.mon[cls]["MonStatsEx"]
    m2 = d.mon2[ex] if ex is not None and 0 <= ex < len(d.mon2) else {}
    return bool(m2.get(A.MMODES[mode] + "mv"))


def mon_sched_flag(d, mode):
    return d.pe.dw(0x006E2260 + 16 * mode + 12)


def k1_model(T, S, r, F, ev):
    """K1 (derived): kind-0 (t, a) list and the end, from the closed forms; ev(f) the event byte."""
    n = max(2, ceil_div(256 * (F - S), r))
    N = n - 1
    out = []
    for f in range(S, min(F, 0x90)):
        e = ev(f)
        if e in (1, 2, 3, 4):
            k = max(1, ceil_div(256 * (f - S), r))
            if k <= N:
                out.append((T + k, e))
    return out, T + n


def e3_model(T, p, r, L, ev):
    """E3 (findings anim/0001 § 7.1): steps 256 p + k r < L, the scan from frame p - 1, codes 1-4 with b = 0, no 0x90
    bound, the end as E1."""
    out = []
    t = T
    f = max(p - 1, 0)
    acc = (p << 8) + r
    while acc < L:
        t += 1
        while f <= (acc >> 8):
            e = ev(f)
            if e in (1, 2, 3, 4):
                out.append([0, t, e, 0])
            f += 1
        acc += r
    if t == T:
        t += 1
    out.append([1, t + 1, 0, 0])
    return out


def ghr(tot, poi, hp, D, lo, hi, frozen, mon_gh):
    if frozen or (poi and poi == tot) or tot < 0x100:
        return 1, lo, hi
    if tot < cdiv(hp, D):
        return 1, lo, hi
    if tot < cdiv(hp, cdiv(D, 2)):
        v, lo, hi = RNG.rng_pow2(lo, hi, 2)
        if v == 0:
            return 1, lo, hi
    if tot < cdiv(hp, cdiv(D, 4)):
        v, lo, hi = RNG.rng_pow2(lo, hi, 4)
        if v == 0:
            return 1, lo, hi
    return (0 if mon_gh else 1), lo, hi


def adv_alt(a, L, r, ev):
    """UNIT_AnimAdvance with the first frame always (+0x44 >> 8) + 1 (the reading the rescan rule excludes)."""
    e = 0
    f = (a >> 8) + 1
    a = AR.s32(a + AR.s16(r))

    def take(x):
        nonlocal e
        if ev is not None and x < 0x90 and ev[x] in (1, 2, 3, 4):
            e = ev[x]
    if a >= L:
        while True:
            while f < (L >> 8):
                take(f)
                f += 1
            a -= L
            f = 0
            if not a >= L:
                break
    while f <= (a >> 8):
        take(f)
        f += 1
    return a, e


def factor(d, line):
    """(branch, X, stat id, base) of an SR line for the K checks: the factor the rate multiplies the record speed by;
    None for a branch the K forms do not cover (moving, knockback, fixed, a transformed player)."""
    if line["c8"] & 8:
        return None
    res = A.rate_model(d, line)
    br = res[4]
    st = {int(k): v for k, v in line["st"].items()}
    g = lambda s: st.get(s, 0)  # noqa: E731
    if br == "cast":
        return br, min(100 + AR.bonus(2, g(105)), 175), 105, 100
    if br == "gethit":
        return br, AR.bonus(1, g(99)) + 50, 99, 50
    if br == "block":
        base = 100 if 101 in line["ss"] else 50
        return br, AR.bonus(3, g(102)) + base, 102, base
    if br == "attack" and "_x" in line:
        x = line["_x"]
        return br, max(15, min(175, x)), 93, x - AR.bonus(0, g(93))
    if br == "default":
        return br, max(15, min(175, g(69))), 69, 0
    return None


BONUS_IDX = {93: 0, 99: 1, 105: 2, 102: 3, 96: 4}


def s_min(stat, y):
    """K3: the least stat s with a bonus >= y, from the closed form ceil(k y / (k - y)); None for y >= k."""
    t, k, _ = AR.BONUS[BONUS_IDX[stat]]
    if y <= 0:
        return 0
    if y >= k:
        return None
    return ceil_div(k * y, k - y)


# ================================================================================================== the observers
class Obs:
    def __init__(self, d, chk):
        self.d = d
        self.chk = chk

    def run(self, path, lines, rev):
        self.lines, self.rev, self.path = lines, rev, os.path.basename(path)
        ev = collections.defaultdict(list)
        lid = None
        self.town = []       # per line index: the player's last PLR level in a town; None when unknown or when the
        plr = []             # next PLR line names another level (a level change between the two pilot lines)
        for i, (tag, x) in enumerate(lines):
            if tag == "PLR":
                lid = x.get("lid")
                plr.append(i)
            self.town.append(lid in TOWNS if lid is not None else None)
        nxt_lid = None
        for i in range(len(lines) - 1, -1, -1):
            tag, x = lines[i]
            if tag == "PLR":
                nxt_lid = x.get("lid")
            elif self.town[i] is not None and nxt_lid is not None and (nxt_lid in TOWNS) != self.town[i]:
                self.town[i] = None
        for i, (tag, x) in enumerate(lines):
            u = uid(tag, x)
            if u is not None:
                ev[u].append(i)
        self.ev = ev
        for fn in (self.o_mset_init, self.o_starts, self.o_pds_end, self.o_town_modes, self.o_pl, self.o_ghr,
                   self.o_gh, self.o_mds, self.o_kbe, self.o_obj, self.o_sched_forms, self.o_rsc, self.o_adv,
                   self.o_sr_mid, self.o_terms, self.o_gh_left):
            fn()

    def unit_lines(self, u, j0, stop_tags=("MSET",), same_frame=True):
        """The unit's lines after index j0 (an index into self.lines) up to the next stop tag of the unit."""
        out = []
        lst = self.ev.get(u, [])
        fr0 = self.lines[j0][1].get("fr")
        k = bisect.bisect_right(lst, j0)
        for i in lst[k:]:
            tag, x = self.lines[i]
            if tag in stop_tags:
                break
            if same_frame and x.get("fr") is not None and x["fr"] != fr0:
                break
            out.append((i, tag, x))
        return out

    # --- rows timing 1, 22, 23, 25, README 1: UNIT_SetMode -> UNIT_AnimInit
    def o_mset_init(self):
        r = rep("mset-animinit")
        rb = rep("animinit-branch")
        for i, (tag, x) in enumerate(self.lines):
            if tag != "MSET":
                continue
            u = x["u"]
            t, same = u["t"], x["to"] == u["m"]
            nxt = self.unit_lines(u["u"], i)
            if t in (0, 1):
                ui = [y for _, tg, y in nxt if tg == "SR" and sr_kind(y["ra"]) == "ui"]
                pre = []
                for _, tg, y in nxt:
                    if tg == "SR" and sr_kind(y["ra"]) == "ui":
                        break
                    if tg == "SR":
                        pre.append(y["ra"])
                key = "t%d-%s" % (t, "same" if same else "new")
                r.add(key)
                if same and ui:
                    r.bad(("same-mode-animinit", self.path, x["n"]))
                if not same and len(ui) != 1:
                    if not nxt and i == max(self.ev[u["u"]]):
                        r.add("new-unit-no-later-line")
                    else:
                        r.bad(("new-mode-animinit-count", self.path, x["n"], len(ui)))
                if not same and ui:
                    if ui[0]["u"]["m"] != x["to"]:
                        r.bad(("animinit-mode", self.path, x["n"], ui[0]["u"]["m"], x["to"]))
                    for ra in pre:
                        r.add("new-sr-before-animinit-ra=%08X" % ra)
                    y = ui[0]
                    disp0 = (y["u"]["t"] == 0 and not y["c8"] & 8) or (
                        y["u"]["t"] == 1 and y["rec"] and y["rec"][0][:2] in A.PLR_TOKEN)
                    m = y["u"]["m"]
                    if y["c8"] & 8:
                        m = A.plr_to_mon_mode(self.d, [A.FORM_STATES[s] for s in y["ss"] if s in A.FORM_STATES][0], m) \
                            if any(s in A.FORM_STATES for s in y["ss"]) else None
                    if m is None:
                        rb.add("transformed-unknown-form")
                        continue
                    want = (0x00624444 if m == 18 else 0x00624469) if disp0 else (0x006244C5 if m == 14 else 0x006244E3)
                    k2 = "disp%d-%s-ra=%08X" % (0 if disp0 else 1, "seq" if m in (14, 18) else "plain", y["ra"])
                    rb.add(k2)
                    if y["ra"] != want:
                        rb.bad(("branch", self.path, y["n"], k2, hex(want)))
                    # +0x30 at the rate call: SeqInit sets it before the sequence branches' call; the player branch
                    # clears it before its call; the monster branch clears it after (C2), so no test there
                    if y["ra"] in (0x00624444, 0x006244C5) and not y["seq"]:
                        rb.bad(("seqflag-seq", self.path, y["n"], y["seq"]))
                    if y["ra"] == 0x00624469 and y["seq"]:
                        rb.bad(("seqflag-plain0", self.path, y["n"], y["seq"]))
                    if y["ra"] == 0x006244E3:
                        rb.add("disp1-plain-seq-at-call=%d" % y["seq"])
            elif t == 2:
                oa = [y for _, tg, y in nxt if tg == "OA0"]
                key = "t2-%s" % ("same" if same else "new")
                r.add(key)
                if same and oa:
                    r.bad(("obj-same-oa", self.path, x["n"]))
                if not same and len(oa) != 1:
                    r.bad(("obj-new-oa-count", self.path, x["n"], len(oa)))

    # --- rows timing 2, 5, 13, 24, 29, 39, 58-60, 63, 73, 128; README 9: the server starts
    def o_starts(self):
        rs = rep("start-sequence")
        rc = rep("two-clocks")
        rr = rep("two-rate-calls")
        rq = rep("sui-branch")
        for i, (tag, x) in enumerate(self.lines):
            if tag != "MSET" or x["u"]["t"] not in (0, 1):
                continue
            u = x["u"]
            nxt = self.unit_lines(u["u"], i)
            toks = []
            srs = []
            sch = ef = None
            for _, tg, y in nxt:
                if tg == "SR":
                    k = sr_kind(y["ra"])
                    toks.append("SR" + k)
                    srs.append((k, y))
                elif tg == "CAN":
                    toks.append("CAN%d" % y["k"] if y["ra"] in CAN_SUNIT else "CANx")
                elif tg in ("SCH", "EF", "RSC"):
                    toks.append(tg)
                    if tg == "SCH" and sch is None:
                        sch = y
                    if tg == "EF" and ef is None:
                        ef = y
            mode = x["to"]
            t = u["t"]
            sig = ">".join(toks)
            # the start kind: what the unit queued after its mode set
            got = "sch" if sch else ("ef" if ef else "none")
            if t == 0:
                want = "sch" if mode in PSCHED else ("ef" if mode in PMOVE else "none")
                fam = "p-m%d" % mode
            else:
                # by the resulting mode: the mode at the SUNIT_AnimInit rate call
                sm = [y for k, y in srs if k == "sui"]
                rm = sm[-1]["u"]["m"] if sm else mode
                cls = u["c"]
                if not sm:
                    want = None
                elif not mon_sched_flag(self.d, rm):
                    want = "none"
                else:
                    want = "ef" if mon_every_frame(self.d, cls, rm) else "sch"
                fam = "m-m%d" % rm
            if want is None:
                rc.add("%s-nostart" % fam)      # a monster mode set outside MonSetMode (no SUNIT_AnimInit)
            else:
                rc.add("%s-%s" % (fam, got))
                if got != want:
                    if not nxt or (got == "none" and want != "none" and nxt[-1][0] == max(self.ev[u["u"]])):
                        rc.add("%s-log-end" % fam)
                    else:
                        rc.bad(("clock", self.path, x["n"], fam, want, got, sig))
            if sch or (ef and t == 1):
                rs.add("%s-%s:%s" % ("p" if t == 0 else "m", "sch" if sch else "ef", sig[:80]))
                # the order: SUNIT_AnimInit's rate, then the cancel of kinds 0 and 1, then the schedule
                if t == 1 or mode in PSCHED:
                    try:
                        a = toks.index("SRsui")
                        c0, c1 = toks.index("CAN0"), toks.index("CAN1")
                        s = toks.index("SCH" if sch else "EF")
                        good = a < c0 < c1 < s or a < c1 < c0 < s
                    except ValueError:
                        good = False
                    rs.add("order-%s" % ("ok" if good else "other"))
                    if not good:
                        rs.bad(("order", self.path, x["n"], sig))
            # the two rate calls (row 128) and the schedule's rate (row 29)
            uis = [y for k, y in srs if k == "ui"]
            suis = [y for k, y in srs if k == "sui"]
            if suis:
                y = suis[-1]
                seqb = (y["u"]["t"] == 1 and y["u"]["m"] == 14) or (y["u"]["t"] == 0 and y["u"]["m"] == 18)
                kq = "ra=%08X-%s-seq%d" % (y["ra"], "seqmode" if seqb else "other", y["seq"])
                rq.add(kq)
                if (y["ra"] == SUI_SEQ) != (seqb and bool(y["seq"])):
                    rq.bad(("sui", self.path, y["n"], kq))
                if sch:
                    rr.add("sch-after-sui")
                    rsch = sch["sr"] if sch["seq"] else sch["r"]
                    rsui = y["sr"] if y["seq"] else y["r"]
                    if rsch != rsui:
                        rr.bad(("sch-rate", self.path, sch["n"], rsch, rsui))
                    if uis:
                        rui = uis[-1]["sr"] if uis[-1]["seq"] else uis[-1]["r"]
                        rr.add("both-calls")
                        if rui != rsui:
                            rr.add("separating-ui-ne-sui")
                            if rsch == rsui:
                                rr.add("separating-sch-takes-second")
                    if uis and srs.index(("ui", uis[-1])) > srs.index(("sui", y)):
                        rr.bad(("ui-after-sui", self.path, x["n"]))
            elif sch:
                rr.add("sch-without-sui")
                rr.bad(("sch-without-sui", self.path, sch["n"]))

    # --- rows timing 4, 54, 61, 124: the kind-1 player dispatch, the frame function's 2
    def o_pds_end(self):
        r = rep("player-mode-end")
        for i, (tag, x) in enumerate(self.lines):
            if tag != "PDS":
                continue
            nxt = self.unit_lines(x["u"], i, stop_tags=("PDS",))
            ms = [y for _, tg, y in nxt if tg == "MSET"]
            m = x["m"]
            if x["k"] == 1:
                to = ms[0]["to"] if ms else None
                town = self.town[i]
                r.add("k1-m%d-to=%s" % (m, to))
                if m == 0:
                    good = to == 17
                elif m == 19:
                    good = to == 4
                else:
                    good = to in (1, 5) and (to == 5) == bool(town)
                if not good:
                    if not nxt and i == max(self.ev[x["u"]]):
                        r.add("k1-log-end")
                    else:
                        r.bad(("k1", self.path, x["n"], m, to, town))
            else:
                r.add("k0-%s" % ("mset-same-frame" if ms else "no-mset"))
                if ms:
                    r.add("k0-m%d-to=%d" % (m, ms[0]["to"]))

    # --- rows timing 56, 62 (and movement 27 later): neutral and walk by town
    def o_town_modes(self):
        r = rep("town-modes")
        for i, (tag, x) in enumerate(self.lines):
            if tag == "MSET" and x["u"]["t"] == 0 and x["to"] in (1, 5, 2, 6, 3):
                town = self.town[i]
                if town is None:
                    r.add("to%d-room-unknown" % x["to"])
                    continue
                r.add("to%d-%s" % (x["to"], "town" if town else "field"))
                if x["to"] in (1, 2) and town or x["to"] in (5, 6) and not town:
                    r.bad(("town", self.path, x["n"], x["u"]["m"], x["to"], town))

    # --- rows timing 7, 12, 106, 114, 115, 117: PlrModeLeaveOk and PlrModeEndPending
    def o_pl(self):
        r = rep("leave-ok")
        open_ = {}
        ple = {}
        cur = None
        for i, (tag, x) in enumerate(self.lines):
            if tag == "PL0":
                open_[x["n"]] = x
                cur = x["n"]
            elif tag == "PLE":
                ple[cur] = x["E"]
            elif tag == "PL1":
                p = open_.pop(x["k"], None)
                if not p:
                    continue
                m, req, c = p["u"]["m"], p["req"], p["u"]["c"]
                E = ple.get(x["k"])
                fr = p["fr"]
                def model(slack):
                    pend = E is not None and E > 0 and fr <= E + slack
                    if req in (0, 1, 5, 17):
                        return 1
                    if m in (0, 4, 9, 17):
                        return 0
                    if m in (7, 8, 10, 11):
                        return 1 if pend or req in (4, 9) else 0
                    if m == 12:
                        return 1 if pend else 0
                    if (m == 13 and c == 0) or (m == 15 and c == 5):
                        return 0
                    if m == 18:
                        return None
                    return 1
                want, alt = model(5), model(0)
                key = "m%d-req%s-r%d" % (m, "pass" if req in (0, 1, 5, 17) else ("gb" if req in (4, 9) else "x"), x["r"])
                r.add(key)
                if want is None:
                    r.add("sq-not-modelled")
                    continue
                if want != x["r"]:
                    r.bad(("pl", self.path, p["n"], m, req, fr, E, x["r"]))
                if E is not None and E > 0 and E < fr <= E + 5:
                    r.add("slack-window")
                    if alt != want:
                        r.add("slack-separating-%s" % ("matched" if want == x["r"] else "missed"))
                if x["r"] == 0:
                    r.add("refused-m%d-req%d" % (m, req))

    # --- rows timing 108, 109, 112, 119: GetHitRoll divisors and the monster GH test
    def o_ghr(self):
        r = rep("ghr-divisor")
        opened, hp = {}, {}
        for tag, x in self.lines:
            if tag == "GR0":
                opened[x["n"]] = x
            elif tag == "GRH":
                hp[x["k"]] = x["hp"]
            elif tag == "GR1":
                g = opened.pop(x["k"], None)
                h = hp.get(x["k"])
                if not g or h is None:
                    continue
                lo, hi = A.seed_of(g["s"])
                hc = g["hc"]
                D = {2: 8, 6: 8, 10: 8, 11: 8, 4: 32, 8: 32, 5: 64}.get(hc, 16)
                frozen = 1 in g["ss"]
                mon_gh = True
                if g["d"]["t"] == 1:
                    m2 = self.d.mon2[self.d.mon[g["d"]["c"]]["MonStatsEx"]]
                    mon_gh = bool(m2.get("mGH"))
                got = (x["r"], x["s"])
                want = ghr(g["tot"], g["poi"], h, D, lo, hi, frozen, mon_gh)
                want = (want[0], "%08x:%08x" % want[1:])
                if want != got:
                    r.bad(("ghr", self.path, g["n"], want, got))
                if D in (32, 64):
                    alt = ghr(g["tot"], g["poi"], h, 16, lo, hi, frozen, mon_gh)
                    alt = (alt[0], "%08x:%08x" % alt[1:])
                    r.add("D%d-calls" % D)
                    if alt != want:
                        r.add("D%d-separating-%s" % (D, "matched" if want == got else "missed"))
                if not mon_gh:
                    alt = ghr(g["tot"], g["poi"], h, D, lo, hi, frozen, True)
                    alt = (alt[0], "%08x:%08x" % alt[1:])
                    r.add("noGH-calls")
                    if alt != want:
                        r.add("noGH-separating-%s" % ("matched" if want == got else "missed"))

    # --- rows timing 6, 75, 104, 107, 110, 119, 120, 122: the hit and the defender
    def o_gh(self):
        r = rep("gethit")
        rs = rep("stun-skips-roll")
        rb = rep("stat95")
        rh = rep("hitclass")
        rd = rep("delivery-frame")
        last95 = {}
        L = self.lines
        for i, (tag, x) in enumerate(L):
            if tag != "GH":
                continue
            de, at, res = x["d"], x["a"], x["res"]
            # the lines of this GH call: up to the next GH
            seg = []
            for tg, y in L[i + 1:i + 80]:
                if tg == "GH":
                    break
                seg.append((tg, y))
            gr = [y for tg, y in seg if tg == "GR0" and y["d"]["u"] == de["u"]]
            ms = [y for tg, y in seg if tg == "MSET" and y["u"]["u"] == de["u"] and y["fr"] == x["fr"]]
            pl = [y for tg, y in seg if tg == "PL0" and y["u"]["u"] == de["u"]]
            stunned = 21 in x["ss"]
            if res & 4 and not res & (0x2 | 0x8 | 0x10 | 0x8000 | 0x380) and 54 not in x["ss"]:
                k = "%s-%s" % ("p" if de["t"] == 0 else "m", "stunned" if stunned else "free")
                rs.add(k + ("-gr" if gr else "-nogr"))
                if stunned and gr:
                    rs.bad(("stun-gr", self.path, x["n"]))
                if not stunned and not gr and de["m"] not in ((0, 17) if de["t"] == 0 else (0, 12)):
                    rs.add(k + "-nogr-unexplained")
                    rs.note(("nogr", self.path, x["n"], de["m"], res, x["ss"]))
            # the defender's command by result bit (M1), first set bit in the spec's order
            if 54 in x["ss"]:
                cls = "state54"
            elif de["t"] == 0:
                cls = next((n for b, n in ((0x80, "dodge"), (0x100, "avoid"), (0x200, "evade"), (0x8010, "block"),
                                           (0x2, "kill"), (0x8, "kb"), (0x4, "gethit")) if res & b), "none")
            else:
                cls = next((n for b, n in ((0x2, "kill"), (0x8, "kb"), (0x10, "block"), (0x4, "gethit")) if res & b),
                           "none")
            req = [y["req"] for y in pl]
            kbe = [y for tg, y in seg if tg == "KBE" and de["u"] in (y["ecx"], y["edx"])]
            if kbe:
                ms = [y for y in ms if y["n"] < kbe[0]["n"]]     # a command after MonKnockbackEnd is its own (I2)
                r.add("kbe-inside")
            to = [y["to"] for y in ms]
            r.add("%s-%s-req=%s-to=%s" % ("p" if de["t"] == 0 else "m", cls, req[:1], to[:1]))
            grr = None
            if gr:
                g1 = [y for tg, y in seg if tg == "GR1" and y["k"] == gr[0]["n"]]
                grr = g1[0]["r"] if g1 else None
            cmd = {4, 9, 19} & set(req)
            if de["t"] == 0:
                # the player's mode commands this hit issued: PL0 with request 4, 9 or 19 (M1's order)
                if cls in ("dodge", "avoid", "evade", "none", "state54") and cmd:
                    r.bad(("p-unexpected-cmd", self.path, x["n"], cls, req))
                if cls == "kb" and cmd - {19}:
                    r.bad(("p-kb-cmd", self.path, x["n"], req))
                if cls == "gethit":
                    want4 = stunned or grr == 0
                    r.add("p-gethit-%s-cmd4=%d" % ("stunned" if stunned else "roll%s" % grr, 4 in cmd))
                    if want4 != (4 in cmd) or cmd - {4}:
                        r.bad(("p-gh-cmd", self.path, x["n"], stunned, grr, req))
                if cls == "kill" and to[:1] not in ([0], []):
                    r.bad(("p-kill", self.path, x["n"], to))
            else:
                if cls == "kb" and to[:1] not in ([13], []):
                    r.bad(("m-kb", self.path, x["n"], to))
                if cls == "gethit":
                    want3 = stunned or grr == 0
                    r.add("m-gethit-%s-to3=%d" % ("stunned" if stunned else "roll%s" % grr, to[:1] == [3]))
                    if to[:1] == [3] and not want3:
                        r.note(("m-gh-roll1-to3", self.path, x["n"], res))
                    if to[:1] == [3] and not want3:
                        r.bad(("m-gh", self.path, x["n"], stunned, grr, to))
                if cls == "block" and to[:1] not in ([6], []):
                    r.bad(("m-bl", self.path, x["n"], to))
                if cls in ("none", "state54") and to and to[0] in (3, 6, 13):
                    r.bad(("m-none", self.path, x["n"], res, to))
            # stat 95 (row 110): the gate and the next GH's stat 95
            if de["t"] == 0 and x.get("st") is not None:
                st = x["st"]
                prev = last95.pop(de["u"], None)
                if prev is not None:
                    want95 = prev[0] if prev[1] else prev[2]
                    k = "next95-after-%s%s" % ("open" if prev[1] else "shut", "-refused" if prev[1] and not prev[3] else "")
                    rb.add(k)
                    if st.get("95", 0) != want95:
                        rb.bad(("st95", self.path, x["n"], prev, st.get("95", 0)))
                if res & 0x8010 and not res & 0x4000 and not res & 0x380 and 54 not in x["ss"]:
                    gate = x["fr"] - st.get("95", 0) > cdiv(st.get("102", 0), 8) + 15
                    started = any(tg == "SCH" and y["u"]["u"] == de["u"] and y["u"]["m"] == 9 for tg, y in seg)
                    last95[de["u"]] = (x["fr"], gate, st.get("95", 0), started)
                elif de["u"] in last95:
                    pass
                else:
                    last95[de["u"]] = (None, False, st.get("95", 0), False)
            # the hit class nibble (row 120): a monster attacker's MonStats2 HitClass
            if res & 1 and at["t"] == 1:
                ex = self.d.mon[at["c"]]["MonStatsEx"]
                hcm = (self.d.mon2[ex].get("HitClass") or 0) if ex is not None else 0
                rh.add("m-attacker-%s" % ("eq" if (x["hc60"] & 0xF) == hcm else "ne"))
            if res & 1 and at["t"] == 0:
                rh.add("p-attacker-nibble=%d" % (x["hc60"] & 0xF))
            # delivery on the do frame (row 104): the attacker's kind-0 dispatch in this frame before the GH
            if at["t"] == 0:
                back = [y for tg, y in L[max(0, i - 400):i] if tg == "PDS" and y["u"] == at["u"] and y["fr"] == x["fr"]
                        and y["k"] == 0]
                rd.add("p-attacker-m%d-%s" % (at["m"], "do-dispatch" if back else "no-dispatch"))
            elif at["t"] == 1:
                back = [y for tg, y in L[max(0, i - 400):i] if tg == "MDS" and y["u"] == at["u"] and y["fr"] == x["fr"]
                        and y["k"] == 0]
                rd.add("m-attacker-m%d-%s" % (at["m"], "dispatch" if back else "no-dispatch"))

    # --- rows timing 54, 75, 76, 133: monster dispatches
    def o_mds(self):
        r = rep("monster-dispatch")
        rf = rep("frozen-drop")
        ra = rep("mon-attack-frame")
        last_sk = {}
        L = self.lines
        for i, (tag, x) in enumerate(L):
            if tag == "SCH" and x["u"]["t"] == 1:
                last_sk[x["u"]["u"]] = x.get("sk")
            if tag == "MSET" and x["u"]["t"] == 1 and x["ra"] == MSET_MEG:
                r.add("meg-setmode1-from-m%d-to%d" % (x["u"]["m"], x["to"]))
                if x["u"]["m"] not in (2, 15) or x["to"] != 1:
                    r.bad(("meg", self.path, x["n"], x["u"]["m"], x["to"]))
            if tag != "MDS":
                continue
            nxt = self.unit_lines(x["u"], i, stop_tags=("MDS",))
            ms = [y for _, tg, y in nxt if tg == "MSET"]
            if x["fz"]:
                rf.add("fz-k%d-%s" % (x["k"], "mset" if ms else "no-mset"))
                if ms:
                    rf.bad(("frozen-mset", self.path, x["n"], x["k"], ms[0]["to"]))
                continue
            if x["k"] == 1:
                to = ms[0]["to"] if ms else None
                r.add("k1-m%d-to=%s" % (x["m"], to))
            elif x["k"] == 0 and x["m"] in (4, 5, 7, 8, 9):
                sk = last_sk.get(x["u"])
                gh = [y for tg, y in L[i + 1:i + 120] if tg == "GH" and y["a"]["u"] == x["u"] and y["fr"] == x["fr"]]
                ra.add("m%d-a%d-%s-%s" % (x["m"], x["a"], "skill" if sk else "noskill", "gh" if gh else "nogh"))

    # --- row timing 77: MonKnockbackEnd and the next command
    def o_kbe(self):
        r = rep("kb-end-next")
        L = self.lines
        for i, (tag, x) in enumerate(L):
            if tag != "KBE":
                continue
            u = None
            for cand in (x["edx"], x["ecx"]):
                if cand in self.ev:
                    u = cand
                    break
            if u is None:
                r.add("unit-unknown")
                continue
            ms = [y for j, tg, y in self.unit_lines(u, i, stop_tags=("KBE",)) if tg == "MSET"]
            cls = next((y["u"]["c"] for _, tg, y in self.unit_lines(u, i, stop_tags=(), same_frame=False)[:3]
                        if tg in ("MSET", "SR", "SCH")), None)
            r.add("to=%s%s" % (ms[0]["to"] if ms else None, "-base78" if cls is not None and
                               self.d.mon[cls]["BaseId"] == 78 else ""))

    # --- rows timing 26, 79, 132: objects
    def o_obj(self):
        r = rep("chest-queue")
        L = self.lines
        oqs = {}
        for i, (tag, x) in enumerate(L):
            if tag == "OQ":
                oqs[(x["o"]["u"], x["q"][1])] = x
        for i, (tag, x) in enumerate(L):
            if tag == "OQ" and x["site"] == CHEST_OQ:
                row = self.d.obj[x["o"]["c"]]
                want = x["fr"] + (row["FrameCnt1"] or 0) + 1
                kind, qf = x["q"][0], x["q"][1]
                r.add("oq-kind%d" % kind)
                if qf != want:
                    r.bad(("oq-frame", self.path, x["n"], qf, want))
            if tag == "OEV":
                after = [tg for j, tg, y in self.unit_lines(x["o"]["u"], i, stop_tags=(), same_frame=True)
                         if tg in ("MSET", "OA0")]
                r.add("oev-%s" % ("mset-or-oa" if after else "no-start"))
                if after:
                    r.bad(("oev-start", self.path, x["n"], after))
                oq = oqs.get((x["o"]["u"], x["fr"]))
                r.add("oev-%s" % ("queued-by-oq-site=%08X" % oq["site"] if oq else "no-oq-line"))

    # --- rows timing 21, 36, 95-98, 100, 101, 125-127: the closed forms on every schedule
    def o_sched_forms(self):
        r = rep("k-forms")
        rw = rep("worked")
        last = {}
        for tag, x in self.lines:
            if tag == "SR":
                last[x["u"]["u"]] = x
                continue
            if tag != "SCH" or x["seq"] or not x["rec"]:
                continue
            nm, F, spd, evb, found = self.d.record(x["rec"][0])
            if not found:
                r.add("fallback-record")
                continue
            S = x.get("s0", 0)
            T, rr, L = x["T"], x["r"], x["L"]
            r.add("sch")
            if L != F << 8:
                r.bad(("B4-len", self.path, x["n"], L, F))
            if rr <= 0 or F <= S:
                r.add("r0-or-F<=S")
                continue
            got0 = sorted((q[1], q[2]) for q in x["q"] if q[0] == 0)
            end = [q[1] for q in x["q"] if q[0] == 1]
            want0, wend = k1_model(T, S, rr, F, lambda f: evb[f] if f < 144 else 0)
            if sorted(want0) != got0 or end != [wend]:
                r.bad(("K1", self.path, x["n"], want0, got0, wend, end))
            else:
                r.add("K1-match")
            dropped = [f for f in range(S, min(F, 0x90)) if evb[f] in (1, 2, 3, 4)
                       and max(1, ceil_div(256 * (f - S), rr)) > wend - T - 1]
            if dropped:
                r.add("K1-separating-dropped-event")
            if rr >= 256 * (F - S):
                r.add("no-step")
            n = wend - T
            sr = last.get(x["u"]["u"])
            fx = factor(self.d, sr) if sr and sr.get("rec") == x["rec"] and sr["r"] == rr else None
            if fx and spd > 0:
                br, X, sid, base = fx
                r.add("K2-%s" % br)
                Rm = ceil_div(256 * (F - S), n)
                Xm = ceil_div(100 * Rm, spd)
                ok = X >= Xm
                if n > 2:
                    Rm1 = ceil_div(256 * (F - S), n - 1)
                    Xm1 = ceil_div(100 * Rm1, spd)
                    ok = ok and X < Xm1
                if (spd * X) % (1 << 32) != spd * X or AR.rate_u(spd, X) != rr:
                    r.add("K2-skip-rate-not-plain")      # a floor, cap or wrap: outside K2's domain
                elif not ok:
                    r.bad(("K2", self.path, x["n"], br, X, n, Xm))
                else:
                    r.add("K2-match")
                    if X == Xm:
                        r.add("K2-at-breakpoint")
                    # K3 (the stat for the bonus): only where the bonus term is the stat's alone
                    st = {int(k): v for k, v in sr["st"].items()}
                    s = st.get(sid, 0)
                    if br in ("cast", "gethit", "block") and X < 175 and s >= 0:
                        y0 = Xm - base
                        smin = s_min(sid, y0)
                        ok3 = smin is not None and s >= smin
                        if n > 2:
                            y1 = ceil_div(100 * ceil_div(256 * (F - S), n - 1), spd) - base
                            smin1 = s_min(sid, y1)
                            ok3 = ok3 and (smin1 is None or s < smin1)
                        r.add("K3-%s-%s" % (br, "match" if ok3 else "bad"))
                        if not ok3:
                            r.bad(("K3", self.path, x["n"], br, s, n, smin))
                        elif smin == s and s > 0:
                            r.add("K3-at-breakpoint")
            # worked examples and illustrations (rows 101, 125-127)
            if nm[:4] in ("SOSC", "PAGH") or nm[:5] == "AMA11":
                st = {int(k): v for k, v in sr["st"].items()} if sr else {}
                do = [q[1] - T for q in x["q"] if q[0] == 0 and q[2] in (1, 2)]
                fxx = fx[1] if fx else None
                e1 = next((f for f in range(F) if evb[f] in (1, 2)), None)
                rw.add("%s(F%d,spd%d,S%d,ev%s)-s105=%d-s99=%d-X=%s-r=%d-n=%d-do=%s" % (
                    nm, F, spd, S, e1, st.get(105, 0), st.get(99, 0), fxx, rr, n, do[:1]))

    # --- rows timing 8, 35, 38, 52: the catalogue reschedules and queue
    def o_rsc(self):
        r = rep("reschedule-e3")
        rq = rep("catalogue-queue-kinds")
        last44 = {}
        lastsr = {}
        for tag, x in self.lines:
            if tag == "SR":
                lastsr[x["u"]["u"]] = x
            if tag == "SCH":
                last44[x["u"]["u"]] = x["a44"]
            elif tag == "CQ":
                rq.add("kind%d" % x["q"][0])
            elif tag == "RSC":
                u = x["u"]["u"]
                T = x["fr"]
                rr = x["sr"] if x["seq"] else x["r"]
                L = x["sl"] if x["seq"] else x["L"]
                a0 = last44.get(u)
                f, arg = x["f"], x["arg"]
                if f == "at":
                    p = arg
                elif a0 is None:
                    r.add("%s-no-prior-a44" % f)
                    last44[u] = x["a44"]
                    continue
                elif f == "pct":
                    p = int((T - (a0 >> 8)) * (100 - arg) / 100)
                else:
                    p = T - (a0 >> 8) - arg
                if x["seq"]:
                    rows = None
                    sk = x.get("sk")
                    if x["u"]["t"] == 0 and sk:
                        skr = A.skill_rec(self.d, sk[0])
                        sr = None
                        wc = self.d.plr_wclass(x["u"]["c"], 7, (lastsr.get(u) or {}).get("eq", []))
                        ps = A.plr_seq(self.d, skr["seqnum"], wc) if skr else None
                        rows = [fr[3] for fr in ps[0]] if ps else None
                        del sr
                    if rows is None:
                        r.add("%s-seq-norows" % f)
                        last44[u] = x["a44"]
                        continue
                    evf = lambda g, rows=rows: rows[g] if g < len(rows) else 0  # noqa: E731
                else:
                    nm, F, spd, evb, found = self.d.record(x["rec"][0]) if x["rec"] else ("", 0, 0, bytes(144), False)
                    evf = lambda g, evb=evb: evb[g] if g < 144 else 0  # noqa: E731
                want = e3_model(T, p, rr, L, evf)
                k = "%s-%s" % (f, "match" if want == x["q"] else "bad")
                r.add(k)
                if want != x["q"]:
                    r.bad(("E3", self.path, x["n"], f, arg, p, want, x["q"]))
                if f in ("at", "pct"):
                    w44 = (T - p) << 8
                    r.add("%s-a44-%s" % (f, "match" if w44 == x["a44"] else "ne"))
                else:
                    r.add("skip-a44-%s" % ("unchanged" if x["a44"] == a0 else
                                           ("(T-p)<<8" if x["a44"] == (T - p) << 8 else "changed-other")))
                last44[u] = x["a44"]

    # --- rows timing 21, 42, 43, 44, 46, 49: the advance
    def o_adv(self):
        r = rep("advance")
        prev = None
        restarted = False
        cls_now = {}
        win_first = {}
        L = self.lines
        for i, (tag, x) in enumerate(L):
            if tag in ("SR", "MSET", "SCH") and x["u"]["t"] == 1:
                cls_now[x["u"]["u"]] = x["u"]["c"]
            if tag == "MSET" and x["u"]["t"] == 1:
                win_first[x["u"]["u"]] = (x["to"] == x["u"]["m"], i)
            if tag == "SR" and prev is not None and x["u"]["u"] == prev["u"]:
                restarted = True
            if tag != "AD0":
                continue
            u = x["u"]
            wf = win_first.pop(u, None)
            if wf is not None:
                # the first advance after a mode set of this unit (rows 21, 42, 46)
                same, j = wf
                srs = [y for jj, tg, y in self.unit_lines(u, j, stop_tags=("AD0",), same_frame=False) if tg == "SR"]
                kinds = [sr_kind(y["ra"]) for y in srs]
                if same:
                    r.add("restart-first-a44=%s-%s" % ("0" if x["a44"] == 0 else "ne0", "+".join(kinds) or "nosr"))
                    if x["a44"] != 0 or "ui" in kinds:
                        r.bad(("restart", self.path, x["n"], x["a44"], kinds))
                if not x["seq"] and x["rec"]:
                    r.add("first-L-%s" % ("frames<<8" if x["L"] == x["rec"][1] << 8 else "other"))
                    if x["L"] != x["rec"][1] << 8:
                        r.bad(("B4-first-L", self.path, x["n"], x["L"], x["rec"]))
                if x["seq"]:
                    rows = self.chk.mon_seq(cls_now.get(u), x["sk"][0]) if x.get("sk") and cls_now.get(u) is not None \
                        else None
                    good = rows is not None and x["sp"] == 0 and x["sl"] == len(rows) << 8 and x["L"] == len(rows) << 8
                    r.add("seq-first-%s" % ("init" if good else "other"))
                    if not good:
                        r.bad(("G2", self.path, x["n"], x["sp"], x["sl"], x["L"], len(rows) if rows else None))
            pair = prev is not None and prev["u"] == u and x["fr"] == prev["fr"] + 1 and x["m"] == prev["m"] \
                and not restarted
            restarted = False
            if pair and not prev["seq"] and not x["seq"]:
                if prev["L"] != x["L"]:
                    r.bad(("F2-L-changed", self.path, x["n"], prev["L"], x["L"]))
                else:
                    r.add("pair-L-kept")
                    if prev["r"] != x["r"] or (prev["rec"] and x["rec"] and prev["rec"] != x["rec"]):
                        r.add("pair-L-kept-across-rate-change")
                ev = None
                if prev["rec"]:
                    _, _, _, evb, found = self.d.record(prev["rec"][0])
                    ev = evb if found else None
                a, e = AR.adv_model(prev["a44"], prev["L"], prev["r"], ev)
                if A.s16(prev["r"]) < 0x100:
                    a2, e2 = adv_alt(prev["a44"], prev["L"], prev["r"], ev)
                    r.add("r-lt-256-pairs")
                    if (a2, e2) != (a, e):
                        r.add("rescan-separating-%s" % ("matched" if (a, e) == (x["a44"], x["e4e"]) else "missed"))
            elif pair and prev["seq"] and x["seq"] and prev.get("sk"):
                rows = self.chk.mon_seq(cls_now.get(u), prev["sk"][0]) if cls_now.get(u) is not None else None
                if rows and prev["rec"]:
                    f = x["sp"] >> 8
                    if f < len(rows):
                        rf = rows[f]["frame"] or 0
                        if rf >= prev["rec"][1]:
                            r.add("seq-step-past-record-%s" % ("event" if (rows[f]["event"] or 0) else "noevent"))
                            res = self.chk.seq_adv(prev, rows)
                            if res is None or res[3] != x["e4e"]:
                                r.add("seq-step-past-record-e4e-differs")
            prev = x

    # --- rows timing 44, 88: mid-mode rate calls
    def o_sr_mid(self):
        r = rep("sr-midmode")
        laststart = {}
        for i, (tag, x) in enumerate(self.lines):
            if tag != "SR":
                continue
            u = x["u"]["u"]
            k = sr_kind(x["ra"])
            if k in ("ui", "sui"):
                laststart[u] = x
                continue
            p = laststart.get(u)
            if p is None or p["u"]["m"] != x["u"]["m"]:
                r.add("no-start-in-this-mode")
                continue
            ch = p["rec"] != x["rec"]
            r.add("%s-ra=%08X-rec-%s" % ("p" if x["u"]["t"] == 0 else "m", x["ra"], "changed" if ch else "same"))
            if ch and p["rec"] and x["rec"] and p["rec"][1] != x["rec"][1]:
                r.add("frames-changed-midmode")
            laststart[u] = x

    # --- rows timing 85, 92: the rate's terms
    def o_terms(self):
        r = rep("rate-terms")
        seen = set()
        for tag, x in self.lines:
            if tag != "SR":
                continue
            u = x["u"]
            st = {int(k): v for k, v in x["st"].items()}
            if u["t"] == 0 and x.get("eq") is not None and not x["ss"] and not x.get("sk"):
                s93 = sum(e[4] for e in x["eq"] if e[0] in (4, 5))
                r.add("p-s93-%s" % ("eq-items" if st.get(93, 0) == s93 else "ne-items"))
            if u["t"] == 1 and u["u"] not in seen and st:
                seen.add(u["u"])
                if not x["ss"] and not x.get("mf"):
                    r.add("m-first-plain-67_68_69=%d_%d_%d" % (st.get(67, 0), st.get(68, 0), st.get(69, 0)))

    # --- rows timing 106: get-hit and block are not left before T + n
    def o_gh_left(self):
        r = rep("gh-bl-left")
        for i, (tag, x) in enumerate(self.lines):
            if tag != "SCH" or x["u"]["t"] != 0 or x["u"]["m"] not in (4, 9):
                continue
            end = [q[1] for q in x["q"] if q[0] == 1]
            if not end:
                continue
            nxt = [y for j, tg, y in self.unit_lines(x["u"]["u"], i, stop_tags=(), same_frame=False)
                   if tg == "MSET"]
            if not nxt:
                r.add("log-end")
                continue
            y = nxt[0]
            k = "m%d-next-to%d-%s" % (x["u"]["m"], y["to"], "before-end" if y["fr"] < end[0] else
                                     ("at-end" if y["fr"] == end[0] else "after-end"))
            r.add(k)
            if y["fr"] < end[0] and y["to"] not in (0, 17):
                r.bad(("left-early", self.path, x["n"], y["n"], y["to"], y["fr"], end[0]))


def parse(path):
    lines, rev = [], 0
    with open(path, errors="replace") as f:
        for raw in f:
            tag, _, rest = raw.partition(" ")
            if not rest.startswith("{"):
                if raw.startswith("ANIM logger armed rev "):
                    rev = int(raw.split()[4])
                continue
            try:
                lines.append((tag, json.loads(rest)))
            except ValueError:
                continue
    return lines, rev


def run_checker(chk, path, lines, rev):
    """tools/anim.py Checker.run's body on lines already parsed (the control)."""
    chk.rev = rev
    chk.mon_cls = {}
    chk.cat_cancel = {}
    for tag, d in lines:
        if tag in ("SR", "MSET", "SCH") and d["u"]["t"] == 1:
            chk.mon_cls[d["u"]["u"]] = d["u"]["c"]
    chk.fast_ids = set()
    for tag, d in lines:
        if tag == "MON":
            for m in d.get("m") or ():
                if 6 in (m.get("mods") or ()):
                    chk.fast_ids.add(m["id"])
    for fn in (chk.check_rates, chk.check_sched, chk.check_steps, chk.check_adv, chk.check_drain, chk.check_ghr,
               chk.check_pma, chk.check_obj, chk.check_actions, chk.check_chain, chk.check_block_gate,
               chk.check_delay, chk.check_plr_kb):
        fn(lines)


def sec_logs(lst):
    d = A.Data(DATA, EXE)
    chk = A.Checker(d, review=True)
    obs = Obs(d, chk)
    paths = [ln.strip() for ln in open(lst) if ln.strip()]
    revs = collections.Counter()
    caps = 0
    for p in paths:
        path = p if os.path.isabs(p) else os.path.join(ROOT, p)
        lines, rev = parse(path)
        revs[rev] += 1
        caps += sum(1 for t, _ in lines if t == "CAP")
        run_checker(chk, path, lines, rev)
        obs.run(path, lines, rev)
        del lines
    print("S6 logs n=%d revs=%s cap_lines=%d" % (len(paths), dict(sorted(revs.items())), caps))
    nbad = 0
    for k in R:
        nbad += R[k].done()
    for k in sorted(chk.tally):
        if k.startswith(("chain-", "obj-chained", "ef-first-run-turn", "plr-kb", "block-gate", "endpending")):
            print("CTALLY %s %d" % (k, chk.tally[k]))
    print("CHECK anim %s" % " ".join("%s=%d/%d" % (k, chk.n[k], chk.bad[k]) for k in sorted(chk.n)))
    print("S6 total bad=%d control_bad=%d" % (nbad, sum(chk.bad.values())))


# ================================================================================================== part 2 (S6b)
PMOVE_END = {0: (2, 3, 6), 1: (2, 15)}     # the modes that end on arrival (movement C2): player WL RN TW, monster WL RN
VEL_RA = 0x005A63E3                        # MonModeVelocity's UNIT_AnimSetRate return (part 1's sr-midmode)
ST_SLOWED, ST_COLD = 24, 11                # States rows: slowed (Slows Target), cold


def centre(w):
    return (w << 16) + 0x8000


class Obs2:
    """Part 2 observers: anim/movement rows 1-3, 7, 9-11, 15, 21, 23, 26, 27, 29-32, 34-36, 38-42, 44 and timing row
    105 (the rv-req restarts of the modes P1b-1 did not tally). Each runs after tools/anim.py's Checker on the same
    parsed lines, so an SR line carries the Checker's branch (`_br`) and factor (`_x`)."""

    def __init__(self, d):
        self.d = d

    def run(self, path, lines, rev):
        self.lines, self.rev, self.path = lines, rev, os.path.basename(path)
        ev = collections.defaultdict(list)
        for i, (tag, x) in enumerate(lines):
            u = uid(tag, x)
            if u is not None:
                ev[u].append(i)
        self.ev = ev
        self.lid = []
        lid = None
        for tag, x in lines:
            if tag == "PLR":
                lid = x.get("lid")
            self.lid.append(lid)
        for fn in (self.o_run67, self.o_vbase, self.o_mon67, self.o_v0s1, self.o_steps, self.o_arrive,
                   self.o_town_drain, self.o_turn, self.o_turn_ef, self.o_kb_gh, self.o_kb_plan, self.o_kb_len, self.o_slow,
                   self.o_velcmd, self.o_rvreq):
            fn()

    # --- movement rows 1, 7, 10, 40: RunVelocityStat's +50 at a run start, dropped at the next mode
    def o_run67(self):
        r = rep("run-stat67")
        last = {}
        for tag, x in self.lines:
            if tag != "SR" or x["u"]["t"] != 0:
                continue
            u, m = x["u"]["u"], x["u"]["m"]
            s67, ss = x["st"].get("67"), tuple(sorted(x["ss"]))
            form = [FS for FS in ss if FS in A.FORM_STATES] if x.get("c8", 0) & 8 else []
            p = last.get(u)
            last[u] = (m, s67, ss)
            if p is None or s67 is None or p[1] is None:
                continue
            pm, p67, pss = p
            run, prun = m in (3, 19), pm in (3, 19)
            if run == prun:
                continue
            cs = self.d.cs[x["u"]["c"]]
            want = (cs["RunVelocity"] * 100) // cs["WalkVelocity"] - 100 if cs["WalkVelocity"] else 0
            dl = (s67 - p67) if run else (p67 - s67)
            key = "%s-m%d-%s%s" % ("start" if run else "end", m if run else pm,
                                   "form%s-" % form[0] if form else "", "same-states" if ss == pss else "states-changed")
            if ss == pss:
                r.add("%s-delta=%d" % (key, dl))
                if dl != want:
                    r.bad(("delta", self.path, x["n"], key, dl, want))
            else:
                r.add("%s-delta=%d" % (key, dl))
        for c in range(len(self.d.cs)):
            cs = self.d.cs[c]
            if cs.get("WalkVelocity"):
                r.c["charstats-c%d-ratio=%d" % (c, (cs["RunVelocity"] * 100) // cs["WalkVelocity"] - 100)] = 1

    # --- movement rows 9, 41, 39: the animation base and the shared factor on the Checker's matched moving calls
    def o_vbase(self):
        r = rep("move-bases")
        for tag, x in self.lines:
            if tag != "SR" or x.get("_br") != "move" or x.get("pv") is None:
                continue
            t, c, m = x["u"]["t"], x["u"]["c"], x["u"]["m"]
            if x.get("c8", 0) & 8:
                r.add("transformed")
                continue
            xx = max(x.get("_x", 100), 25)
            if t == 0:
                r.add("p-m%d-vbase=%s" % (m, "0x65" if m == 3 else "0xD5"))
                if xx == 100:
                    r.add("p-m%d-x100-pv=%d-r=%d" % (m, x["pv"], x["r"]))
            else:
                w, rn = self.d.speeds(c)
                r.add("m-m%d-%s" % (m, ("rn-ne-walk" if rn != w else "rn-eq-walk") if m == 15 else "walk-base"))
            r.add("%s-x%s100" % ("p" if t == 0 else "m", "eq" if xx == 100 else "ne"))

    # --- movement row 11: a monster's stat 67 at neutral against 75 and the mods (monsters/stats § G)
    def o_mon67(self):
        r = rep("mon-stat67")
        mods = {}
        for tag, x in self.lines:
            if tag == "MON":
                for m in x.get("m") or ():
                    mods[(m["id"], m.get("cls"))] = tuple(sorted(m.get("mods") or ()))
        first, vals = {}, collections.defaultdict(set)
        for tag, x in self.lines:      # the unit's neutral SRs with no state, after the frame of its first SR (the
            if tag != "SR" or x["u"]["t"] != 1:          # creation's SRs come before the mods are applied)
                continue
            u = x["u"]["u"]
            if u not in first:
                first[u] = x
                continue
            if x["fr"] > first[u]["fr"] and x["u"]["m"] == 1 and not x["ss"] and "67" in x["st"] and \
                    x.get("ra") != VEL_RA:      # after the creation frame
                vals[u].add(x["st"]["67"])
        for u, vs in vals.items():
            x = first[u]
            c, i = x["u"]["c"], x["u"]["id"]
            md = mods.get((i, c))
            if md is None:
                r.add("mods-unknown")
                continue
            v = self.d.mon[c]["Velocity"] or 0
            sp = [k for k in md if k in (6, 16, 37, 38)]
            ch = any(k in (16, 38) for k in md)      # champion, possessed: + 20 (fanatic: dev run 3 met 175 =
            #                                          75 + clamp only, not 195; the + 20 here is not fanatic's)
            fa = any(k in (6, 37) for k in md)
            want = 75
            if v > 0:
                want += (20 if ch else 0) + (max(10, min(100, 2048 // v - 128)) if fa else 0)
            want_b = want + (20 if 38 in md and v > 0 else 0)      # possessed adding a second 20
            got = sorted(vs)
            key = "mods=%s-v%s" % ("+".join(map(str, sp)) or "none", "0" if v == 0 else "+")
            if len(vs) > 1:
                r.add("%s-values-%d" % (key, len(vs)))
            if want in vs:
                r.add("%s-match" % key)
            elif want_b in vs:
                r.add("%s-match-possessed-40" % key)
            else:
                r.add("%s-mismatch" % key)
                r.bad(("s67", self.path, x["n"], c, md, v, got, want))

    # --- movement row 15: a Velocity-0 classic class in S1
    def o_v0s1(self):
        r = rep("v0-s1")
        for tag, x in self.lines:
            if tag != "SR" or x["u"]["t"] != 1 or not 8 <= x["u"]["m"] <= 11:
                continue
            c = x["u"]["c"]
            if c >= 410 or (self.d.mon[c]["Velocity"] or 0) != 0:
                continue
            r.add("m%d-br=%s-pv=%s-r=%d-x=%s" % (x["u"]["m"], x.get("_br"), x.get("pv"), x["r"], x.get("_x")))

    # --- movement rows 21, 42, 39: the snap lands on the centre; frames per point against ceil(65536 d / step)
    def o_steps(self):
        r = rep("snap")
        rf = rep("frames-per-point")
        prev = {}
        seg = {}
        for tag, q in self.lines:
            if tag != "PS0":
                continue
            u = q["u"]
            p = prev.get(u)
            prev[u] = q
            if p is None or q["fr"] != p["fr"] + 1 or q["m"] != p["m"] or q["pts"][:1] != p["pts"][:1] and \
                    q["i"] <= p["i"]:
                seg.pop(u, None)
                p = None
            if p is not None and q["i"] == p["i"] + 1 and q["pts"] == p["pts"]:
                cx, cy = centre(p["pt"][0]), centre(p["pt"][1])
                ok = (q["x"], q["y"]) == (cx, cy)
                k = "%s-m%d-ty%d" % ("p" if q["t"] == 0 else "m", q["m"], q["ty"])
                r.add("%s-reach-%s" % (k, "centre" if ok else "off"))
                if not ok:
                    r.bad(("off", self.path, q["n"], k))
                s = seg.pop(u, None)
                if s is not None and s["ok"]:
                    nf = q["fr"] - s["fr"]
                    want = ceil_div(s["rem"], s["m"])
                    rf.add("%s-%s" % (k, "match" if nf == want else "mismatch"))
                    if nf != want:
                        rf.bad(("frames", self.path, q["n"], k, nf, want, s["rem"], s["m"]))
                    ax = s["axis"]
                    if ax and s["rem"] % 65536 == 0:
                        rf.add("%s-axis-v%d-d%d-frames=%d" % (k, s["v"], s["rem"] >> 16, nf))
            elif p is not None and q["i"] == p["i"]:
                s = seg.get(u)
                if s is not None and (q["v"] != s["v"] or q["d"] != s["d"] or (q["x"], q["y"]) == (p["x"], p["y"])):
                    s["ok"] = False             # a speed or direction change, or a step that did not move
            # a segment starts at a centre with a point ahead
            if q["i"] < q["np"] and (q["x"] & 0xFFFF, q["y"] & 0xFFFF) == (0x8000, 0x8000) and u not in seg:
                sx, sy = A.path_step(q["v"], q["d"])
                m = max(abs(sx), abs(sy))
                if m:
                    rx, ry = abs(centre(q["pt"][0]) - q["x"]), abs(centre(q["pt"][1]) - q["y"])
                    seg[u] = {"fr": q["fr"], "rem": max(rx, ry), "m": m, "v": q["v"], "d": q["d"], "ok": True,
                              "axis": rx == 0 or ry == 0}

    # --- movement rows 26, 38, 23: the mode end on arrival
    def o_arrive(self):
        r = rep("arrive-end")
        L = self.lines
        for i, (tag, p) in enumerate(L):
            if tag != "PS0" or p["m"] not in PMOVE_END[p["t"]]:
                continue
            if p["i"] != p["np"] - 1:
                continue
            sx, sy = A.path_step(p["v"], p["d"])
            m = max(abs(sx), abs(sy))
            rx, ry = abs(centre(p["pt"][0]) - p["x"]), abs(centre(p["pt"][1]) - p["y"])
            if not m or rx > m or ry > m:
                continue
            # this step reaches the last point: the unit's next line in this frame
            nxt = None
            for j, tg, y in Obs.unit_lines(self, p["u"], i, stop_tags=(), same_frame=True):
                if tg in ("MSET", "PS0"):
                    nxt = (tg, y)
                    break
            who = "p" if p["t"] == 0 else "m"
            if nxt and nxt[0] == "MSET":
                r.add("%s-m%d-last-step-then-mset-to=%d" % (who, p["m"], nxt[1]["to"]))
                if nxt[1]["to"] != 1:
                    r.note(("to", self.path, p["n"], nxt[1]["to"]))
            else:
                r.add("%s-m%d-last-step-then-%s" % (who, p["m"], nxt[0] if nxt else "nothing-this-frame"))
        # every set out of a moving mode to neutral: was it preceded in its frame by a last-point step?
        for i, (tag, x) in enumerate(L):
            if tag != "MSET" or x["to"] != 1 or x["u"]["m"] not in PMOVE_END.get(x["u"]["t"], ()):
                continue
            u = x["u"]["u"]
            lst = self.ev.get(u, [])
            k = bisect.bisect_left(lst, i) - 1
            ps = None
            while k >= 0:
                tg, y = L[lst[k]]
                if y.get("fr") != x["fr"]:
                    break
                if tg == "PS0":
                    ps = y
                    break
                k -= 1
            who = "p" if x["u"]["t"] == 0 else "m"
            win = any(L[j][0] == "PS0" and L[j][1]["fr"] == x["fr"] - 1 for j in lst[max(0, k - 12):k + 1])
            r.add("%s-set-m%d-to-1-after-%s" % (who, x["u"]["m"], "step-same-frame" if ps else
                                                ("no-step-windowed" if win else "no-step-unwindowed")))
            if win and not ps:
                r.note((self.path, x["n"], x["fr"]))

    # --- movement rows 27, 29: the drain's town return (stamina above 0, so the field rule would subtract)
    def o_town_drain(self):
        r = rep("town-drain")
        open_ = {}
        for i, (tag, x) in enumerate(self.lines):
            if tag == "DR0":
                open_[x["n"]] = (x, self.lid[i])
            elif tag == "DR1":
                v = open_.pop(x["k"], None)
                if not v:
                    continue
                x0, lv = v
                s0, s1 = x0["st"].get("10", 0), x["st"].get("10", 0)
                where = "town" if lv in TOWNS else "field"
                r.add("%s-r=%d-%s%s" % (where, x["r"], "unchanged" if s0 == s1 else "drained",
                                        "-s10>0" if s0 > 0 else "-s10=0"))
                if where == "town" and (x["r"] != 1 or s0 != s1):
                    r.bad(("town", self.path, x0["n"]))

    # --- movement rows 30, 44: the run's turn to a walk
    def o_turn(self):
        r = rep("run-turn")
        L = self.lines
        for i, (tag, x) in enumerate(L):
            if tag != "MSET" or x["u"]["t"] != 0 or x["u"]["m"] != 3 or x["to"] != 2:
                continue
            u = x["u"]["u"]
            lst = self.ev.get(u, [])
            k = bisect.bisect_left(lst, i)
            # the frame's lines of the unit before the set
            before = [L[j][0] for j in lst[:k] if L[j][1].get("fr") == x["fr"]]
            dr = [j for j in range(max(0, i - 40), i) if L[j][0] == "DR1" and L[j][1].get("r") == 0]
            ef = ps = None
            for j in lst[k + 1:]:
                tg, y = L[j]
                if tg == "EF" and ef is None and y["m"] == 2:
                    ef = (j, y)
                elif tg == "PS0" and y["m"] == 2:
                    ps = (j, y)
                    break
            if not ef or not ps:
                r.add("no-ef-or-ps")
                continue
            off = ps[1]["fr"] - ef[1]["fr"]
            drain0 = bool(dr) and any(L[j][1]["k"] in [L[jj][1]["n"] for jj in range(max(0, i - 40), i)
                                                     if L[jj][0] == "DR0" and L[jj][1]["u"] == u] for j in dr)
            r.add("off=%d-drain0-before=%s-ef-ph=%s-before=%s" % (off, drain0, ef[1].get("ph"),
                                                                  ">".join(t for t in before[-3:])))
            if off != 0:
                r.note((self.path, x["n"], x["fr"], ef[1]["n"], ef[1].get("ph"), ps[1]["n"], ps[1]["fr"],
                        [L[j][0] + "@" + str(L[j][1].get("fr")) for j in lst[max(0, k - 4):k + 4]]))

    def o_turn_ef(self):
        """The control's ef-first-run-turn cases: a player EF of mode 2 in a frame with the unit's DR0 before it; the
        unit's set just before the EF (from, to), the drain's result in the frame, the offset of the next walk step."""
        r = rep("run-turn-ef")
        L = self.lines
        drfr = {}
        for i, (tag, x) in enumerate(L):
            if tag == "DR0":
                drfr[x["u"]] = (x["fr"], x["n"])
            elif tag == "DR1":
                for u, v in list(drfr.items()):
                    if v[1] == x["k"]:
                        drfr[u] = (v[0], v[1], x["r"])
            elif tag == "EF" and x["m"] == 2 and drfr.get(x["u"], (None,))[0] == x["fr"]:
                u = x["u"]
                lst = self.ev.get(u, [])
                k = bisect.bisect_left(lst, i) - 1
                ms = None
                while k >= 0:
                    if L[lst[k]][0] == "MSET":
                        ms = L[lst[k]][1]
                        break
                    k -= 1
                ps = None
                for j in lst[bisect.bisect_right(lst, i):]:
                    if L[j][0] == "PS0":
                        ps = L[j][1]
                        break
                    if L[j][0] == "EF":
                        break
                v = drfr[u]
                r.add("set=%s-drain-r=%s-ef-ph=%s-off=%s" % (
                    "%d>%d" % (ms["u"]["m"], ms["to"]) if ms and ms["fr"] == x["fr"] else "none-this-frame",
                    v[2] if len(v) > 2 else None, x.get("ph"), ps["fr"] - x["fr"] if ps and ps["m"] == 2 else None))

    # --- movement row 32: a monster's knockback bit against the next mode, by MonStats2 mKB
    def o_kb_gh(self):
        r = rep("gh-kb-bit")
        L = self.lines
        for i, (tag, x) in enumerate(L):
            if tag != "GH" or x["d"]["t"] != 1:
                continue
            c = x["d"]["c"]
            mon = self.d.mon[c]
            m2 = self.d.mon2[mon["MonStatsEx"]] if isinstance(mon["MonStatsEx"], int) else None
            kb = m2.get("mKB") if m2 else None
            b78 = mon["BaseId"] == 78
            if b78:
                r.add("base78-res8=%d" % (1 if x["res"] & 8 else 0))
            if not x["res"] & 8:
                continue
            ms = [y for j, tg, y in Obs.unit_lines(self, x["d"]["u"], i, stop_tags=(), same_frame=True) if tg == "MSET"]
            r.add("res8-mKB=%s%s-next=%s" % (kb, "-base78" if b78 else "", ms[0]["to"] if ms else None))

    # --- movement rows 2, 31: the knockback plan's one point against E1
    def o_kb_plan(self):
        r = rep("kb-plan")
        L = self.lines
        last_gh = {}
        plr = None
        for i, (tag, x) in enumerate(L):
            if tag == "PLR":
                plr = (x["x"], x["y"])
            elif tag == "GH" and x["res"] & 8:
                last_gh[x["d"]["u"]] = (x, plr)
            elif tag == "MSET" and x["to"] in (13, 19) and (x["u"]["t"], x["to"]) in ((1, 13), (0, 19)):
                u = x["u"]["u"]
                ps = None
                for j, tg, y in Obs.unit_lines(self, u, i, stop_tags=("MSET",), same_frame=False):
                    if tg == "PS0":
                        ps = y
                        break
                who = "p" if x["u"]["t"] == 0 else "m"
                if ps is None:
                    r.add("%s-no-step" % who)
                    continue
                n = (ps["b90"] >> 1) + 1
                st = (ps["x"] >> 16, ps["y"] >> 16)
                D = (ps["pt"][0] - st[0], ps["pt"][1] - st[1])
                M = max(abs(D[0]), abs(D[1]))
                r.add("%s-ty=%d-np=%d-b90=%d-%s" % (who, ps["ty"], ps["np"], ps["b90"], "full" if M == n else
                                                    ("short" if M < n else "long")))
                if M > n:
                    r.bad(("long", self.path, ps["n"], n, D))
                g = last_gh.get(u)
                if g and g[0]["a"]["t"] == 0 and g[1] is not None and g[0]["fr"] == x["fr"]:
                    ax, ay = g[1]
                    dx, dy = st[0] - ax, st[1] - ay
                    mm = max(abs(dx), abs(dy))
                    if mm == 0:
                        r.add("%s-attacker-on-unit" % who)
                        continue
                    want = (st[0] + int(n * dx / mm), st[1] + int(n * dy / mm))
                    sep = (int(n * dx / mm), int(n * dy / mm)) not in ((n * (dx > 0) - n * (dx < 0), 0),
                                                                        (0, n * (dy > 0) - n * (dy < 0)))
                    res = "match" if tuple(ps["pt"]) == want else ("short" if M < n else "mismatch")
                    r.add("%s-attacker-player-%s%s" % (who, res, "-offaxis" if sep else ""))
                    if res == "mismatch":
                        r.note((self.path, ps["n"], st, (ax, ay), n, tuple(ps["pt"]), want))

    # --- movement row 34: a monster knockback's advances from +0x44 = 0 to its end
    def o_kb_len(self):
        r = rep("kb-advances")
        L = self.lines
        self.kbe = collections.defaultdict(list)
        for k, (tg, y) in enumerate(L):
            if tg == "KBE":
                self.kbe[y["edx"]].append(k)
                if y["ecx"] != y["edx"]:
                    self.kbe[y["ecx"]].append(k)
        for i, (tag, x) in enumerate(L):
            if tag != "MSET" or x["u"]["t"] != 1 or x["to"] != 13:
                continue
            u = x["u"]["u"]
            ads = []
            end = None
            for j in self.ev.get(u, [])[bisect.bisect_right(self.ev.get(u, []), i):]:
                tg, y = L[j]
                if tg == "MSET":
                    end = ("mset", y["fr"])
                    break
                if tg == "AD0" and y["m"] == 13:
                    ads.append(y)
            kl = self.kbe.get(u, [])
            kbe = [k for k in kl[bisect.bisect_right(kl, i):] if end is None or L[k][1]["fr"] <= end[1]][:1]
            if not ads:
                r.add("no-advance-lines")
                continue
            a0 = ads[0]
            if a0["a44"] != 0:
                r.add("first-a44-ne-0")
                continue
            want = max(1, ceil_div(a0["L"], a0["r"]) - 1)
            if not kbe:
                r.add("no-kbe-%s" % (end[0] if end else "log-end"))
                continue
            kfr = L[kbe[0]][1]["fr"]
            n = sum(1 for y in ads if y["fr"] <= kfr)
            # separating: max(1, ceil(L / r) - 1) against ceil(L / r), the count without the end-frame step
            r.add("%s-%s" % ("match" if n == want else "mismatch",
                             "sep" if ceil_div(a0["L"], a0["r"]) >= 2 else "nosep"))
            if n != want:
                r.bad(("adv", self.path, a0["n"], n, want, a0["L"], a0["r"]))

    # --- movement rows 35, 36: a mid-window speed change; Slows Target's stats
    def o_slow(self):
        r = rep("slow")
        L = self.lines
        lastv = {}
        pend = {}
        for tag, x in L:
            if tag == "PS0":
                u = x["u"]
                if u in pend:
                    nv, src = pend.pop(u)
                    r.add("midwindow-change-%s-%s" % (src, "taken-next-step" if x["v"] == nv else "not-taken"))
                    if x["v"] != nv:
                        r.bad(("v", self.path, x["n"], x["v"], nv))
                lastv[u] = (x["v"], x["fr"], x["m"])
            elif tag == "SR" and x.get("_br") == "move" and x.get("pv") is not None and sr_kind(x["ra"]) == "o":
                u = x["u"]["u"]
                lv = lastv.get(u)
                if lv and x["fr"] - lv[1] <= 1 and lv[2] == x["u"]["m"]:
                    if lv[0] != x["pv"]:
                        src = "cold" if ST_COLD in x["ss"] else ("slowed" if ST_SLOWED in x["ss"] else "other")
                        pend[u] = (x["pv"], src)
                    else:
                        pend.pop(u, None)
            elif tag == "MSET":
                pend.pop(x["u"]["u"], None)       # a mode set before the next step: a new window, not this one
            if tag == "SR" and x["u"]["t"] == 1 and ST_COLD not in x["ss"] and \
                    (x["st"].get("68", 100) < 100 or x["st"].get("69", 100) < 100):
                # a monster's lowered attack or default rate with no cold state (the logger's "ss" lists states 11,
                # 139, 140 only, so Slows Target's state 24 is not visible): 67, 68, 69 together
                r.add("m-lowered-68-69-not-cold-s67=%s-s68=%s-s69=%s" % (x["st"].get("67"), x["st"].get("68"),
                                                                          x["st"].get("69")))

    # --- movement row 3: MonModeVelocity's stat 67 and rate re-run
    def o_velcmd(self):
        r = rep("vel-cmd")
        for tag, x in self.lines:
            if tag == "SR" and x["u"]["t"] == 1 and x.get("ra") == VEL_RA:
                r.add("m%d-br=%s-s67=%s" % (x["u"]["m"], x.get("_br"), x["st"].get("67")))

    # --- timing row 105: the first request after T and the next start, for the modes P1b-1 left out
    def o_rvreq(self):
        r = rep("rv-req-other")
        L = self.lines
        acts = []
        cur = {}
        for tag, x in L:
            if tag == "SCH" and x["u"]["t"] == 0:
                e1 = [q[1] for q in x["q"] if q[0] == 1]
                a = {"T": x["T"], "m": x["u"]["m"], "e1": e1[0] if e1 else None, "u": x["u"]["u"], "req": None,
                     "seq": x["seq"]}
                acts.append(a)
                cur[a["u"]] = a
            elif tag == "PL0" and x["u"]["u"] in cur:
                a = cur[x["u"]["u"]]
                if a["req"] is None and x["fr"] >= a["T"]:
                    a["req"] = (x["fr"], x["req"])
        for a, b in zip(acts, acts[1:] + [None]):
            if a["m"] not in (4, 8, 9, 13, 14, 15, 16) or a["e1"] is None:
                continue
            if not a["req"]:
                r.add("m%d-no-request" % a["m"])
                continue
            rq = a["req"][0] - a["e1"]
            nb = b["T"] - a["req"][0] if (b is not None and b["u"] == a["u"]) else None
            r.add("m%d-req-minus-e1=%s-next-start-minus-req=%s" % (a["m"], max(-5, min(3, rq)),
                                                                    nb if nb is None or abs(nb) <= 5 else ">5"))


def sec_ai78():
    """Timing row 78 (MonModeStartNeutral's re-queue at T + aidel): the plan 0052 ai logs have no mode-set line, so the
    one neutral start a log dates is an AI command to mode 1 (MSM0 cmd[0] = 1, inside a decision); the unit's next
    AID or AIN frame against the decision's frame + aidel (AID "ad"[0])."""
    import glob
    r = rep("ai78-neutral-cmd")
    for p in sorted(glob.glob(os.path.join(ROOT, "workspace", "logs", "ai", "*.log"))):
        aid, pend = {}, {}
        with open(p, errors="replace") as f:
            for raw in f:
                tag, _, rest = raw.partition(" ")
                if tag not in ("AID", "AIN", "MSM0"):
                    continue
                try:
                    x = json.loads(rest)
                except ValueError:
                    continue
                if tag == "AID":
                    aid[x["n"]] = x
                if tag in ("AID", "AIN") and x["u"] in pend:
                    F, ad, m0 = pend.pop(x["u"])
                    r.add("next-%s-delta-%s" % (tag, "eq-aidel" if x["fr"] - F == ad else "ne-aidel"))
                    r.note((os.path.basename(p), F, x["fr"] - F, ad, m0))
                if tag == "MSM0" and x["cmd"][0] == 1 and x["k"] in aid:
                    a = aid[x["k"]]
                    pend[a["u"]] = (x["fr"], a["ad"][0], a["m"])
                    r.add("neutral-cmd-from-m%s" % a["m"])
    return r.done()


def sec_logs2(lst):
    d = A.Data(DATA, EXE)
    chk = A.Checker(d, review=True)
    obs = Obs2(d)
    paths = [ln.strip() for ln in open(lst) if ln.strip()]
    revs = collections.Counter()
    for p in paths:
        path = p if os.path.isabs(p) else os.path.join(ROOT, p)
        lines, rev = parse(path)
        revs[rev] += 1
        run_checker(chk, path, lines, rev)
        obs.run(path, lines, rev)
        del lines
    print("S6b logs n=%d revs=%s" % (len(paths), dict(sorted(revs.items()))))
    nbad = 0
    for k in R:
        nbad += R[k].done()
    for k in sorted(chk.tally):
        if k.startswith(("ps-p-m18-v", "ef-first-run-turn", "plr-kb", "win-", "sr-m-fastmod", "drain-")):
            print("CTALLY %s %d" % (k, chk.tally[k]))
    print("CHECK anim %s" % " ".join("%s=%d/%d" % (k, chk.n[k], chk.bad[k]) for k in sorted(chk.n)))
    print("S6b total bad=%d control_bad=%d" % (nbad, sum(chk.bad.values())))


# ================================================================================================== static
def sec_static():
    import sweep2_s4cd as S4
    rp = rep("static")
    # the return addresses the log checks classify, each with its owner by re/symbols.csv and by the int3 padding
    for ra in (0x00624444, 0x00624469, 0x006244C5, 0x006244E3, SUI_SEQ, SUI_PATH) + CAN_SUNIT + (MSET_MEG,):
        o = S4.owner(ra)
        pe = S4.pad_entry(ra)
        ins = S4.r2_range(ra - 5, ra)
        call = ins[-1] if ins else None
        rp.add("ra-checked")
        print("  ra %08X owner %08X %s pad_entry %s r2_call_before %s" % (ra, o[0], o[1], hex(pe) if pe else None,
                                                                        call))
        if pe != o[0]:
            rp.bad(("owner", hex(ra)))
    # UNIT_AnimInit's extent: the next entry after 0x00624390 by symbols and by padding
    nxt = [a for a, _ in S4.funcs() if a > UI[0]][0]
    rp.add("animinit-end-%s" % ("ok" if nxt == UI[1] else "other"))
    print("  UNIT_AnimInit [0x%08X, 0x%08X); the next symbol 0x%08X; pad_entry(UI_end - 1) %s" % (
        UI[0], UI[1], nxt, hex(S4.pad_entry(UI[1] - 1))))
    # GetHitRoll's callers (timing row 112): raw bytes and r2
    rel, calls, ab = S4.raw(0x0057CB00)
    own = sorted({S4.owner(c)[1] for c in calls})
    r2x = [S4.r2_range(c, c + 5) for c in calls]
    print("  GetHitRoll 0x0057CB00 raw call sites %s owners %s abs32 %d; r2 at the sites %s" % (
        [hex(c) for c in calls], own, len(ab), [x[0][1:] if x else None for x in r2x]))
    if any(not x or "0x57cb00" not in x[0][2] for x in r2x):
        rp.bad(("r2-ghr-site",))
    rp.add("ghr-callers=%d" % len(calls))
    if own != ["COMBAT_GetHit"]:
        rp.bad(("ghr-callers", own))
    # UNIT_AnimInit's rate calls (the four returns above) and SUNIT_AnimInit's two: every call of 0x00623F50 in them
    for lo, hi, name in ((UI[0], UI[1], "UNIT_AnimInit"), (0x005533D0, 0x005534B0, "SUNIT_AnimInit")):
        cs = [va for va, mn, ops in S4.r2_range(lo, hi) if mn == "call" and "0x623f50" in ops]
        print("  %s calls of UNIT_AnimSetRate (r2): %s" % (name, [hex(c) for c in cs]))
    d = A.Data(DATA, EXE)
    for nm in ("SOSCHTH", "SOSC1HS", "SOSCSTF", "PAGHHTH", "PAGH1HS", "AMA11HS"):
        name, F, spd, ev, found = d.record(nm)
        print("  record %s found=%s frames=%d speed=%d events=%s" % (nm, found, F, spd,
                                                                     [(f, ev[f]) for f in range(F) if ev[f]]))
    return rp.done()


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    if sys.argv[1] == "logs":
        lst = LST
        if "--list" in sys.argv:
            lst = sys.argv[sys.argv.index("--list") + 1]
        sec_logs(lst)
    elif sys.argv[1] == "logs2":
        lst = LST
        if "--list" in sys.argv:
            lst = sys.argv[sys.argv.index("--list") + 1]
        sec_logs2(lst)
    elif sys.argv[1] == "ai78":
        sec_ai78()
    elif sys.argv[1] == "static":
        sec_static()
    else:
        print(__doc__)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
