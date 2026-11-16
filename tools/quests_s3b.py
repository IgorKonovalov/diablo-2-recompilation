"""Plan 0066 Phase 1, batch S3b: kill-step and service-step rules (per quest word: the write sites' returns, the
player record, the game record) over the kept quests.gdb-family logs, no game.

Usage:
  python3 -I tools/quests_s3b.py check LOG [LOG ...]   # every rule below; "KEY value" lines, MISMATCH lines, SUMMARY
  python3 -I tools/quests_s3b.py static                 # the image reads the rules attribute sites with (objdump, r2)

The logs: run:2026-10-16-quest-drops (quests-run.lst and quests-owner-run.lst), run:2026-10-17-sweep-quest-b6
(h6d/quest-b6-run.lst, the kept ones), run:2026-10-27-sweep-quest-items (h6e2/quest-items-*.log, the kept ones),
run:2026-10-27-sweep-quest-npc (h6e1/quest-npc-*.log) and run:2026-10-20-two-clients (the four den host logs, the
host process's own lines only). Their loggers (tools/gdb/quests.py and the files sourcing it) write QS/QC/QK at the
entries of QUESTRECORD_SetState / ClearState / ClearSteps with the return address, the record, the word, the bit and
the word before the call; QI1 gives the game record ("G" below), every other record is a player's ("P").

A write's site is its return address - 5 (every caller uses the 5-byte `call rel32`; `static` decodes each logged
site with objdump and r2). A game-record write goes through sub_00544720_GameQuestSet (ECX game, EDX word, one
stacked bit), so its logged return is 0x0054475C for every caller: `static` lists the 40 callers with their EDX
and pushed bit (r2), and the rules attribute a game-record write to a caller by the (word, bit) pair when one caller
holds it, else by the event it sits in.

Rules (P = docs/plans/0066-inventory/quests-progression.md rows):
  sites   all     every logged site: op, word, bit, record kind, count, logs; the site's function (re/symbols.csv)
  gq      all     the game-record writes by return address; no GameQuestSet return on a player record
  leave   P3      QL0 .. QL1 brackets: QE9 lines, then QE10, per leave
  operate P5      QOW slot -> the next quest line's return inside g_ObjOperateFns[slot]; QOE event 7 and its QOT target
  pend    P15     QUESTS_ListSetPending's pair (0x0054565C b13, 0x00545665 b1) on one record and word, back to back
  step    P50 P73 P120 P127 P166 P220 P252 P296  writes at the StepBits sites: the old word's b0 and b1 clear
  svc     P59 P89 P259 P284  each service line (IMB0 / LZ0 / PZ) and the word's b0 set then b1 clear after it
  lohi    P64     Baal's gold: BGR amount = lo + Range(qs, hi - lo) on BG0's quest seed (and the hi - lo + 1 reading)
  qseed   P66     the quest seed between consecutive observations moves only after a QGS
  den     P69 P72 the Den of Evil completion: G w1 b13, then ListSetPending from 0x00590387 on the host's record
  cow     P101 P320  the cow portal: G w4 b11 (one GameQuestSet caller holds (4, 11)) after the opener's w40 b0
  kill    P117 P128 P167 P221 P294  boss-kill credit writes against B60/QME and the killer's old word
  report  P119    G w6 b13 at Warriv's report (one caller holds (6, 13)) after the player's w6 b13 with b0 clear
  gjoin   P131 P224  game-record (word, b13) writes: at a join (before the first PLR line of the game) or after a kill
  staff   P138    the orifice: OSP / the b0 and b13 writes on the placer's word 10
  chest   P142    QOW slots 39-41: one QGS per operate, no QS/QC/QK until the last gold pile
  forge   P250    the forge's third strike: FOP mode 2 strike 2, then w27 b13, b1; any QK and the next word-27 old
  give    P273    w37 b8 at 0x005896F1: old b1 set, b0 clear; the QGV (QUESTS_GiveItem) just before it
  chamber P303 P309  object 563/569 operates and Baal's mode-0 record line against the moves into level 132
  b6      P315    B60 .. B6X before the boss's credit writes; the B6G results against the old word of the credit
Stdlib only, plus objdump and r2 through tools/sweep2_s7a.py for `static`. Read-only.
"""
import collections
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

GQS = 0x00544720          # sub_00544720_GameQuestSet
GQS_RET = 0x0054475C
PEND = (0x0054565C, 0x00545665)
STEP_SITES = {  # spec site -> (row, word, bit)
    0x0058FCDD: ("P73", 1, 2), 0x0058FCF9: ("P73", 1, 3), 0x0058FD0A: ("P73", 1, 4),
    0x00595C1D: ("P120", 6, 2), 0x00595C39: ("P120", 6, 3), 0x00595C4A: ("P120", 6, 4),
    0x00598A2D: ("P127", 9, 2), 0x00598A49: ("P127", 9, 3), 0x00598A5A: ("P127", 9, 4),
    0x0059C6FC: ("P166", 14, 2),
    0x005B6027: ("P252", 27, 5), 0x005B6016: ("P252", 27, 2), 0x005B603D: ("P252", 27, 3),
    0x0058D91D: ("P296", 40, 2), 0x0058D933: ("P296", 40, 3),
}
P220_LO, P220_HI = 0x005BC088, 0x005BC11D   # A3Q6 SetProgressBits b2..b9
SVC = {  # service tag -> (row, word, b0 site, b1 site)
    "IMB0": ("P89", 3, 0x005917A7, 0x005917B1),
    "LZ0": ("P259", 35, 0x005877D7, 0x005877E1),
    "PZ": ("P284", 38, 0x0058BC16, 0x0058BC20),
}
KILLS = {  # monster class -> (row, word, [(site, bit)] in order)
    156: ("P117", 6, [(0x00596218, 13), (0x00596222, 1)]),
    229: ("P128", 9, [(0x00598F10, 13), (0x00598F1F, 1), (0x00598F29, 5)]),
    211: ("P167", 14, [(0x0059D0F0, 5)]),
    242: ("P221", 22, [(0x005BC148, 13), (0x005BC152, 0), (0x005BC15C, 11)]),
    544: ("P294", 40, [(0x0058DD38, 13), (0x0058DD42, 0)]),
}


def parse(path):
    out = []
    with open(path, errors="replace") as f:
        for ln, s in enumerate(f, 1):
            tag, _, rest = s.rstrip("\n").partition(" ")
            d = None
            if rest[:1] == "{":
                try:
                    d = json.loads(rest)
                except ValueError:
                    d = None
            elif rest and tag.isupper() and "=" in rest:
                d = dict(kv.split("=", 1) for kv in rest.split() if "=" in kv)
            out.append((ln, tag, d))
    return out


class Log:
    def __init__(self, path):
        self.path = path
        self.name = os.path.basename(path)
        self.L = parse(path)
        self.grec = None
        self.w = []          # (index, ln, op, site, rec, kind, word, bit, old)
        for i, (ln, tag, d) in enumerate(self.L):
            if tag == "QI1" and d:
                self.grec = d.get("grec")
            if tag in ("QS", "QC", "QK") and d and "ret" in d:
                kind = "G" if d["rec"] == self.grec else "P"
                self.w.append((i, ln, tag, int(d["ret"], 16) - 5, d["rec"], kind, d["w"], d.get("b"), d["old"]))

    def tags(self, *tags):
        return [(i, ln, d) for i, (ln, t, d) in enumerate(self.L) if t in tags]

    def writes_after(self, i):
        return [x for x in self.w if x[0] > i]


class Out:
    def __init__(self):
        self.mis = 0
        self.checks = 0

    def p(self, *a):
        print(" ".join(str(x) for x in a))

    def test(self, ok, key, *a):
        self.checks += 1
        if not ok:
            self.mis += 1
            self.p("MISMATCH", key, *a)


def sym_owner(va):
    import sweep2_s4cd as T
    e, n = T.owner(va)
    return n if e == va else "%s+0x%X" % (n, va - e)


def range_(low, high, n):
    import rng
    return rng.rng_range(low, high, n)


def seed(s):
    lo, hi = s.split(":")
    return int(lo, 16), int(hi, 16)


# ------------------------------------------------------------------------------------------------------- rules
def r_sites(O, logs):
    agg = collections.defaultdict(lambda: [0, set(), set()])
    for g in logs:
        for (i, ln, op, site, rec, kind, w, b, old) in g.w:
            a = agg[(site, op, kind, w, b)]
            a[0] += 1
            a[1].add(g.name)
            a[2].add(old)
    for (site, op, kind, w, b), (n, names, olds) in sorted(agg.items()):
        O.p("SITE 0x%08X %s %s w%s b%s n=%d logs=%d olds=%s %s" % (site, op, kind, w, b, n, len(names),
            ",".join("0x%X" % o for o in sorted(olds)[:6]) + ("…" if len(olds) > 6 else ""), sym_owner(site)))


def r_gq(O, logs):
    c = collections.Counter()
    for g in logs:
        for (i, ln, op, site, rec, kind, w, b, old) in g.w:
            if kind == "G" or site + 5 == GQS_RET:
                c[(kind, "0x%08X" % (site + 5), op)] += 1
    for k, n in sorted(c.items()):
        O.p("GQ record=%s ret=%s %s n=%d" % (k + (n,)))
        O.test(not (k[1] == "0x%08X" % GQS_RET and k[0] != "G"), "GQ GameQuestSet on a player record", k)
    O.p("GQ total game-record writes=%d" % sum(n for k, n in c.items() if k[0] == "G"))


def r_leave(O, logs):
    n = e9 = e10 = 0
    for g in logs:
        open_ = None
        for i, (ln, tag, d) in enumerate(g.L):
            if tag == "QL0":
                open_ = {"ln": ln, "e9": 0, "e10": 0, "e10_after_e9": True}
            elif open_ is not None and tag == "QE9":
                open_["e9"] += 1
                if open_["e10"]:
                    open_["e10_after_e9"] = False
            elif open_ is not None and tag == "QE10":
                open_["e10"] += 1
            elif open_ is not None and tag == "QL1":
                n += 1
                e9 += open_["e9"]
                e10 += open_["e10"]
                O.p("P3 leave %s:%d e9=%d e10=%d" % (g.name, open_["ln"], open_["e9"], open_["e10"]))
                O.test(open_["e10"] == 1 and open_["e10_after_e9"], "P3", g.name, open_["ln"])
                open_ = None
    O.p("P3 total leaves=%d e9=%d e10=%d" % (n, e9, e10))


def operate_table():
    import sweep_s4b as S
    return S.dwords(0x00732D18, 80)


def r_operate(O, logs):
    import sweep2_s4cd as T
    tab = operate_table()
    c = collections.Counter()
    for g in logs:
        for k, (ln, tag, d) in enumerate(g.L):
            if tag != "QOW" or not d:
                continue
            slot = d["fn"]
            fn = tab[slot]
            res = "none"
            for (ln2, t2, d2) in g.L[k + 1:k + 1500]:
                if t2 == "QOW":
                    break
                if t2 == "FOP":
                    res = "entry"          # FOP is the breakpoint at sub_005B5C10_A4Q3_ForgeOperate's entry
                    O.test(fn == 0x005B5C10, "P5 FOP slot", slot, g.name, ln)
                    break
                if d2 and isinstance(d2, dict) and "ret" in d2 and t2 in ("QS", "QC", "QK", "QGS", "QDC", "QDI",
                                                                          "QGV", "PFI", "OCD"):
                    if T.pad_entry(int(d2["ret"], 16) - 5) == fn:
                        res = "in"
                        break
            c[(slot, "0x%08X" % fn, res)] += 1
    for (slot, fn, res), n in sorted(c.items()):
        O.p("P5 operate slot=%d fn=%s %s=%d" % (slot, fn, res, n))
    O.checks += 1
    ev = collections.Counter()
    for g in logs:
        for k, (ln, tag, d) in enumerate(g.L):
            if tag == "QOE" and d:
                tgt = None
                for (ln2, t2, d2) in g.L[k + 1:k + 4]:
                    if t2 == "QOT":
                        tgt = d2["fn"]
                        break
                ev[(d["cls"], d["ev"], d["ret"], tgt)] += 1
    for k, n in sorted(ev.items()):
        O.p("P5 objectevent cls=%s ev=%s ret=%s target=%s n=%d" % (k + (n,)))
        O.test(k[1] == 7 and k[3] is not None, "P5 event", k)


def r_pend(O, logs):
    n = 0
    for g in logs:
        for a, b in zip(g.w, g.w[1:]):
            if a[3] == PEND[0]:
                ok = (b[3] == PEND[1] and a[4] == b[4] and a[6] == b[6] and a[7] == 13 and b[7] == 1
                      and b[8] == a[8] | (1 << 13) and b[0] == a[0] + 1)
                n += 1
                O.p("P15 pend %s:%d w%d old=0x%X then 0x%X" % (g.name, a[1], a[6], a[8], b[8]))
                O.test(ok, "P15", g.name, a[1])
    O.p("P15 total pairs=%d" % n)


def r_step(O, logs):
    c = collections.Counter()
    for g in logs:
        for (i, ln, op, site, rec, kind, w, b, old) in g.w:
            row = None
            if site in STEP_SITES:
                row, ww, bb = STEP_SITES[site]
                O.test(op == "QS" and kind == "P" and (w, b) == (ww, bb), row, "site", hex(site), w, b)
            elif P220_LO <= site <= P220_HI and op == "QS":
                row = "P220"
                O.test(w == 22 and 2 <= b <= 9, row, hex(site), w, b)
            if row:
                c[(row, w, b, hex(site))] += 1
                O.test(old & 3 == 0, "P50 b0/b1 clear", row, g.name, ln, "old=0x%X" % old)
    for k, n in sorted(c.items()):
        O.p("P50 step %s w%d b%d site %s n=%d (old b0 and b1 clear in each)" % (k + (n,)))
    O.p("P50 total writes=%d" % sum(c.values()))


def r_svc(O, logs):
    c = collections.Counter()
    for g in logs:
        idx = g.tags(*SVC)
        for (i, ln, d) in idx:
            tag = g.L[i][1]
            row, word, s0, s1 = SVC[tag]
            later = [x for x in g.writes_after(i) if x[6] == word and x[5] == "P"][:2]
            ok = (len(later) == 2 and later[0][3] == s0 and later[0][2] == "QS" and later[0][7] == 0
                  and later[1][3] == s1 and later[1][2] == "QC" and later[1][7] == 1)
            pend = bool(later) and bool(later[0][8] & 2) and not later[0][8] & 1
            c[(row, tag, ok, pend)] += 1
            O.test(ok, row, g.name, ln, later[:2])
    for k, n in sorted(c.items()):
        O.p("%s svc %s b0-then-b1-clear=%s old(b1 set, b0 clear)=%s n=%d" % (k + (n,)))


def r_lohi(O, logs):
    for g in logs:
        for k, (ln, tag, d) in enumerate(g.L):
            if tag != "BG0":
                continue
            r = next(d2 for (l2, t2, d2) in g.L[k + 1:] if t2 == "BGR")
            lo, hi = d["lo"], d["hi"]
            s = seed(d["qs"])
            v, l2, h2 = range_(s[0], s[1], hi - lo)
            v1, _, _ = range_(s[0], s[1], hi - lo + 1)
            after = "%08x:%08x" % (l2, h2)
            O.p("P64 lohi %s:%d lo=%d hi=%d qs=%s amt=%d model=%d (hi-lo+1: %d) seed after %s logged %s"
                % (g.name, ln, lo, hi, d["qs"], r["amt"], lo + v, lo + v1, after, r["qs"]))
            O.test(r["amt"] == lo + v and after == r["qs"], "P64", g.name, ln)


def r_qseed(O, logs):
    obs = moved = moved_qgs = 0
    for g in logs:
        last = None
        pending = False
        for (ln, tag, d) in g.L:
            if tag not in ("QI1", "QGS", "QDI", "QDX", "BG0", "BGR") or not isinstance(d, dict) or "qs" not in d:
                continue
            q = d["qs"]
            obs += 1
            if tag == "QI1":
                last, pending = q, False
                continue
            if tag == "QGS":
                O.test(last is None or q == last, "P66 qs moved before a QGS", g.name, ln)
                last, pending = q, True
                continue
            if last is not None and q != last:
                if pending:
                    moved_qgs += 1
                    pending = False
                else:
                    moved += 1
                    O.test(False, "P66 qs moved without a QGS", g.name, ln, last, q)
            last = q
    O.p("P66 qseed observations=%d moved-after-QGS=%d moved-otherwise=%d" % (obs, moved_qgs, moved))
    O.checks += 1


def first_plr(g):
    for i, (ln, tag, d) in enumerate(g.L):
        if tag == "PLR":
            return i
    return len(g.L)


def r_den(O, logs):
    for g in logs:
        for a, b, c_ in zip(g.w, g.w[1:], g.w[2:]):
            if a[5] == "G" and a[6] == 1 and a[7] == 13 and b[3] == PEND[0] and b[6] == 1:
                O.p("P72 den G w1 b13 %s:%d (old 0x%X), next ListSetPending on the host record w1 old=0x%X then b1"
                    % (g.name, a[1], a[8], b[8]))
                O.test(c_[3] == PEND[1] and b[8] & 3 == 0, "P69", g.name, a[1])


def r_cow(O, logs):
    for g in logs:
        for (i, ln, op, site, rec, kind, w, b, old) in g.w:
            if kind == "G" and (w, b) == (4, 11):
                # the player's word 40 as the last earlier write on a player record shows it (old | the bit set)
                w40 = [x for x in g.w if x[0] < i and x[5] == "P" and x[6] == 40 and x[2] == "QS"]
                v = (w40[-1][8] | (1 << w40[-1][7])) if w40 else None
                O.p("P101/P320 cow G w4 b11 %s:%d old=0x%X player w40=%s" % (g.name, ln, old,
                    None if v is None else "0x%X" % v))
                O.test(v is not None and v & 1, "P320 w40 b0", g.name, ln)


def r_kill(O, logs):
    for g in logs:
        seen = set()
        marks = [(k, d) for k, (ln, tag, d) in enumerate(g.L) if tag in ("B60", "QME") and d and d["mon"][1] in KILLS]
        for j, (k, d) in enumerate(marks):
            mon = tuple(d["mon"])
            if mon in seen:
                continue
            seen.add(mon)
            row, word, sites = KILLS[mon[1]]
            nxt_mark = next((kk for kk, dd in marks[j + 1:] if tuple(dd["mon"]) != mon), len(g.L))
            ws = [x for x in g.w if k < x[0] < min(nxt_mark, k + 2500) and x[5] == "P" and x[6] == word
                  and x[3] in {s_ for s_, _ in sites}]
            first = [(x[3], x[7]) for x in ws[:len(sites)]]
            O.p("%s kill cls=%d %s:%d credit=%s writes=%s" % (
                row, mon[1], g.name, g.L[k][0], first == sites,
                [("0x%08X" % x[3], x[7], "0x%X" % x[8], x[4] & 0xFFFF) for x in ws]))
            O.test(not ws or (first == sites and ws[0][8] & 3 == 0), row, g.name, g.L[k][0])


def r_report(O, logs):
    for g in logs:
        for a, b, c_ in zip(g.w, g.w[1:], g.w[2:]):
            if a[5] == "G" and (a[6], a[7]) == (6, 13):
                O.p("P119 report G w6 b13 %s:%d old=0x%X; next %s 0x%08X w%d b%d old=0x%X; %s 0x%08X w%d b%d" % (
                    g.name, a[1], a[8], b[2], b[3], b[6], b[7], b[8], c_[2], c_[3], c_[6], c_[7]))
                O.test(b[8] & (1 << 13) and not b[8] & 1, "P119", g.name, a[1])


def r_gjoin(O, logs):
    c = collections.Counter()
    for g in logs:
        fp = first_plr(g)
        kills = [i for i, (ln, t, d) in enumerate(g.L) if t in ("QME", "B6X")]
        for (i, ln, op, site, rec, kind, w, b, old) in g.w:
            if kind != "G" or b != 13 or w not in (9, 22):
                continue
            where = "join" if i < fp else ("kill" if any(0 < i - j < 60 for j in kills) else "other")
            c[(w, where)] += 1
            if where != "join":
                O.p("P131/P224 G w%d b13 %s:%d at %s old=0x%X" % (w, g.name, ln, where, old))
    for k, n in sorted(c.items()):
        O.p("P131/P224 G w%d b13 where=%s n=%d" % (k + (n,)))
    O.checks += 1


def r_staff(O, logs):
    for g in logs:
        for k, (ln, tag, d) in enumerate(g.L):
            if tag == "OSP":
                O.p("P138 OSP %s:%d %s" % (g.name, ln, d))
        for a, b in zip(g.w, g.w[1:]):
            if a[3] == 0x0059DD9C:
                O.p("P138 staff %s:%d w%d b%d old=0x%X then 0x%08X w%d b%d old=0x%X" % (
                    g.name, a[1], a[6], a[7], a[8], b[3], b[6], b[7], b[8]))
                O.test(b[3] == 0x0059DDB4 and (a[6], a[7], b[6], b[7]) == (10, 0, 10, 13) and a[4] == b[4], "P138")


def r_chest(O, logs):
    for g in logs:
        for k, (ln, tag, d) in enumerate(g.L):
            if tag != "QOW" or not d or d["fn"] not in (39, 40, 41):
                continue
            end = next((j for j in range(k + 1, len(g.L)) if g.L[j][1] in ("QOW", "QI0")), len(g.L))
            body = g.L[k + 1:end]
            qgs = [x for x in body if x[1] == "QGS"]
            gold = [x for x in body if x[1] == "QDC" and x[2] and x[2].get("code") == "gld "]
            last_gold = max((x[0] for x in gold), default=ln)
            wr = [x for x in g.w if ln < x[1] <= last_gold]
            O.p("P142 chest slot=%d cls=%d %s:%d qgs=%d gold=%d writes=%d" % (d["fn"], d["cls"], g.name, ln, len(qgs),
                len(gold), len(wr)))
            O.test(len(qgs) == 1 and not wr and 5 <= len(gold) <= 9, "P142", g.name, ln)


def r_forge(O, logs):
    n = 0
    for g in logs:
        fops = [k for k, (ln, tag, d) in enumerate(g.L) if tag == "FOP" and d]
        for j, k in enumerate(fops):
            d = g.L[k][2]
            end = fops[j + 1] if j + 1 < len(fops) else len(g.L)
            nxt = [x for x in g.w if k < x[0] < end and x[6] == 27]
            if d.get("mode") == 2 and d.get("strikes") == 2:
                n += 1
                O.p("P250 forge third strike %s:%d fop=%s writes=%s qk-logged=%s" % (
                    g.name, g.L[k][0], json.dumps(d, sort_keys=True),
                    [("%s 0x%08X" % (x[2], x[3]), x[7], "0x%X" % x[8]) for x in nxt], "QK" in {t for _, t, _ in g.L}))
                O.test(len(nxt) >= 2 and nxt[0][3] == 0x005B5D3C and nxt[1][3] == 0x005B5D49 and nxt[0][7] == 13
                       and nxt[1][7] == 1 and nxt[0][8] & 3 == 0, "P250", g.name, g.L[k][0])
            else:
                O.test(not nxt, "P250 write before the third strike", g.name, g.L[k][0])
    # the run's first sessions (no FOP line): the pair by site alone
    for g in logs:
        if any(t == "FOP" for _, t, _ in g.L):
            continue
        for a, b in zip(g.w, g.w[1:]):
            if a[3] == 0x005B5D3C:
                n += 1
                O.p("P250 forge (no FOP line) %s:%d w%d b%d old=0x%X then 0x%08X b%d" % (g.name, a[1], a[6], a[7],
                    a[8], b[3], b[7]))
                O.test(b[3] == 0x005B5D49 and a[8] & 3 == 0, "P250", g.name, a[1])
    O.p("P250 total third strikes=%d" % n)


def r_give(O, logs):
    for g in logs:
        for (i, ln, op, site, rec, kind, w, b, old) in g.w:
            if site != 0x005896F1:
                continue
            qgv = [d for (_, t, d) in g.L[max(0, i - 60):i] if t == "QGV" and d]
            code = qgv[-1].get("code") if qgv else None
            O.p("P273 give %s:%d w%d b%d old=0x%X the QGV before it: %s" % (g.name, ln, w, b, old, code))
            O.test((w, b) == (37, 8) and old & 2 and not old & 1, "P273", g.name, ln)


def r_chamber(O, logs):
    for g in logs:
        ops = [(ln, d["cls"]) for (ln, t, d) in g.L if t == "OOP" and d and d.get("cls") in (563, 569)]
        mmr = [ln for (ln, t, d) in g.L if t == "MMR" and d and d["mon"][1] == 544 and d.get("mode") == 0]
        lv = []
        last = None
        for (ln, t, d) in g.L:
            if t == "PLR" and isinstance(d, dict):
                L = d.get("lid")
                if L is not None and L != last:
                    lv.append((ln, L))
                    last = L
        if ops or mmr:
            O.p("P303 chamber %s ops=%s baal_mode0=%s levels=%s" % (g.name, ops, mmr,
                [x for x in lv if x[1] in (128, 129, 130, 131, 132)][:12]))
            O.checks += 1


def r_b6(O, logs):
    n = 0
    for g in logs:
        for k, (ln, tag, d) in enumerate(g.L):
            if tag != "B60" or not d:
                continue
            word = d["qid"]
            gs = []
            x_ln = None
            for (l2, t2, d2) in g.L[k + 1:k + 40]:
                if t2 == "B6G":
                    gs.append((d2["k"], d2["r"]))
                if t2 == "B6X":
                    x_ln = l2
                    break
            pre = [x for x in g.w if x[6] == word and x[5] == "P" and ln - 400 < x[1] < ln and x[3] != 0x0054633E]
            post = [x for x in g.w if x[6] == word and x[5] == "P" and x[1] > (x_ln or ln)][:1]
            n += 1
            O.p("P315 b6 %s:%d cls=%d qid=%d B6G=%s B6X=%s first-credit-after=%s" % (
                g.name, ln, d["mon"][1], word, gs, x_ln,
                [("0x%08X" % x[3], x[7], "0x%X" % x[8]) for x in post]))
            if post:
                # the reads saw the word before the script's write: b1's read is 0 when the old word had b1 clear
                g1 = dict(gs).get(1)
                O.test(g1 is None or g1 == (1 if post[0][8] & 2 else 0), "P315", g.name, ln)
    O.p("P315 total B60 groups=%d" % n)


RULES = [r_sites, r_gq, r_leave, r_operate, r_pend, r_step, r_svc, r_lohi, r_qseed, r_den, r_cow, r_kill, r_report,
         r_gjoin, r_staff, r_chest, r_forge, r_give, r_chamber, r_b6]


def check(paths):
    logs = [Log(p) for p in paths]
    O = Out()
    for r in RULES:
        print("== %s" % r.__name__[2:])
        r(O, logs)
    print("SUMMARY mismatches=%d checks=%d logs=%d" % (O.mis, O.checks, len(logs)))
    return 1 if O.mis else 0


# ------------------------------------------------------------------------------------------------------- static
def static():
    import sweep2_s7a as A
    import sweep_s4b as S
    calls, other, ab = A.calls_of(GQS)
    print("GameQuestSet 0x%08X calls=%d other=%d abs=%d" % (GQS, len(calls), len(other), len(ab)))
    pairs = collections.Counter()
    for s in calls:
        e = A.reg_before(s, "edx")
        a = A.args(s, 1)
        pairs[(e[2] if e else None, a[0] if a else None)] += 1
        print("  GQS 0x%08X %s edx=%s bit=%s" % (s, A.nm(s), e[2] if e else None, a[0] if a else None))
    # the logged write sites: each return - 5 decoded by objdump and r2
    for name, tgt in (("SetState", 0x0065C360), ("ClearState", 0x0065C3A0), ("ClearSteps", 0x0065C3E0)):
        cs, oth, ab2 = A.calls_of(tgt)
        print("%s 0x%08X calls=%d other=%d abs=%d" % (name, tgt, len(cs), len(oth), len(ab2)))
    sites = [PEND[0], PEND[1], 0x00590375, 0x00590387, 0x00590175, 0x0059017F, 0x00598F10, 0x00598F1F, 0x00598F29,
             0x00598D96, 0x00598DA0, 0x00598DAA, 0x0059423A, 0x00595D88, 0x005B5D3C, 0x005B5D49, 0x005B5B72,
             0x005B5B7C] + sorted(STEP_SITES) + [s for _, _, s0, s1 in SVC.values() for s in (s0, s1)]
    A_ = S.asm()
    for s in sites:
        od = A_.ins.get(s)
        mn, ops = A.r2ins(s)
        args = A.args(s, 3)
        print("  SITE 0x%08X %s objdump=%s r2=%s %s args=%s" % (s, A.nm(s), od, mn, ops, args))
    for tgt in (0x005455F0, 0x00596210, 0x005BC190, 0x00598E20, 0x00598D40, 0x005B5B00, 0x0058DD30, 0x0058DC60,
                0x00590150, 0x0059DD80, 0x0058E640):
        cs, oth, ab2 = A.calls_of(tgt)
        print("CALLERS 0x%08X %s: %s other=%d abs=%s" % (tgt, A.nm(tgt), ", ".join("0x%08X %s" % (c, A.nm(c)) for c in cs),
              len(oth), ["0x%08X" % a for a in ab2]))
    for va in (0x005844FD, 0x00584504, 0x0058450E, 0x00586B0E, 0x00586B19):
        print("  DISPATCH 0x%08X objdump=%s r2=%s" % (va, A_.ins.get(va), A.r2ins(va)))
    tab = operate_table()
    for slot in (8, 23, 39, 40, 41, 46, 49, 57, 58, 59, 70):
        print("  g_ObjOperateFns[%d] = 0x%08X %s" % (slot, tab[slot], A.nm(tab[slot])))
    return 0


def main(argv):
    if len(argv) >= 2 and argv[1] == "check":
        return check(argv[2:])
    if len(argv) == 2 and argv[1] == "static":
        return static()
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
