"""Plan 0066 Phase 1, batch S3a: new checks over the kept quest-state logs of plan 0042 (run:2026-10-17-quests,
run:2026-10-18-quests2, run:2026-10-19-quests3) and plan 0047 (the p47h / p47b travel sessions), no game.

Usage:
  python3 -I tools/quests_s3a.py check LOG [LOG ...]    # every rule below; "KEY value" lines, MISMATCH lines, SUMMARY
  python3 -I tools/quests_s3a.py static                  # the image reads: callers of QUESTS_TimersRun, g_ItemUseFns[2]

A separate tool, so that tools/quests.py, the hashed checker behind the three runs' kept outputs, stays unchanged; it
imports that checker's model (free_near, Window, Data, the seed steps) and its walk-free free-cell rule is reused here
with the walk of quests/travel § B1 added (the field-end searches the checker counted "not modelled").
Each rule names its inventory rows (docs/plans/0066-inventory/quests-*.md: P = progression, T = travel, R = README).

  timers  P4 P8   TMA/TMR: the control tick equals frame // 20 at every add and run, and a run is on a frame with
                  frame mod 20 = 0 (a pass that skipped a 20-frame boundary would leave the tick behind)
  qobj    P7 P34  the first quest-object list of each game (the join's entry): 41 objects, ids 0..40, list order
                  40, 39, 38, 37 then the main table's rows from the last to row 0 (g_QuestDescs read from the image),
                  +0x09 / +0x0A at the entry, the word +0xE0 against the descriptor's word
  desites P39 P42 every quest dispatch by its call site (the entry's return address): event, force, act filter;
                  the e10 dispatch's unit and its place after the leave's e9 dispatches
  words   P13 P16 R1  QS/QC/QK "old" (the u16 word w of the record, read at the call): each write's next observation
                  of that record word is the old word with bit b set (QS), cleared (QC) or bits 2-11 cleared (QK)
  w9      P18 P130 P132  word 9 at each first join: QC of b0, b1, b15, b5 at 0x0059927F/89/93/9D iff the joiner has
                  b0 and b5 and no `ass `; the game record's w9 b13 iff b0
  gb13    P98 P125 P184 P190 P210 P304  per first join: game-record (word, b13) writes inside the join against the
                  joiner's b0 of that word; player word 40 b10 against its b0; per e11 (npc, msg): the game-record
                  writes and the player's b13 before
  firstjoin P49   the join's exit quest objects (+0x0B, and +0x0C in revision E) against the joiner's step bits
  chain   P54     revision E: quest-state (+0x0C) changes between consecutive object lists, with the event between
  talks   P58     the e0 / e11 / e2 dispatches of one NPC unit: e0 first, then its e11s, then e2
  seeds   P63 P65 P322 R2  per dispatch event: the quest, player and game seed steps; the quest seed between
                  consecutive observations (chained, or moved inside a logged drawing bracket); QGS sites
  intros  P182 P231 P305  the callbacks of quest objects 37-40: record writes between their QCB and the next one
  stat5   P75 P237  the in/out saves' stats 4 and 5 and level around the Akara / Tyrael rewards
  orb     P196 P217 P313 P307  the x-orb / x-orbno saves' quest items; the orb's completing write and the gate
  w36 w10 P262 P141  the per-join clears of w36 b4 and w10 b9
  prog    P301    the in/out saves' progression byte against word 40 b0 per difficulty
  larzuk  P260    distinct units of class 511 per log (NPCQ)
  warps   T5 T69 T70 T71 P308  warp brackets: caller, player-to-warp distance, the gate call by destination
  brackets T2 T3 T4 T6 T7 T8 T37 T38 T34 T35 T58 T63 T67 T83 T85 T86  bracket nesting and arguments
  ff      T9 T10 T11 T12 T19 T20 T22 T60  COLL_FindFreeNear arguments by caller; the walk-extended search
  stale   T48     NPCSTORE_ActStale calls from TownLevelLeave (0x00537402) against the act changes
Stdlib only; read-only.
"""
import collections
import json
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import quests as Q  # noqa: E402

ROOT = Q.ROOT
EXCEL = Q.EXCEL
EXE = Q.EXE
FIELD = os.path.join(ROOT, "workspace", "merged", "data", "global", "expfield.d2")
DX = (0, 1, 1, 1, 0, -1, -1, -1, 0)
DY = (-1, -1, 0, 1, 1, 1, 0, -1, 0)
TOWNS = {1, 40, 75, 103, 109}


def parse(path):
    out = []
    with open(path, errors="replace") as f:
        for ln, s in enumerate(f, 1):
            tag, _, rest = s.rstrip("\n").partition(" ")
            if not rest.startswith("{"):
                continue
            try:
                out.append((ln, tag, json.loads(rest)))
            except ValueError:
                continue
    return out


class Br:
    __slots__ = ("k", "e", "x", "i0", "i1", "parent", "kids")

    def __init__(self, k, e, i0, parent):
        self.k, self.e, self.x, self.i0, self.i1, self.parent, self.kids = k, e, None, i0, None, parent, []


def brackets(lines):
    """EV entries and exits matched innermost-first by kind; -> list of closed brackets (with parent links)."""
    stack, out = [], []
    for i, (ln, tag, d) in enumerate(lines):
        if tag != "EV" or "k" not in d:
            continue
        if d["ph"] == 0:
            b = Br(d["k"], d, i, stack[-1] if stack else None)
            if stack:
                stack[-1].kids.append(b)
            stack.append(b)
        else:
            for j in range(len(stack) - 1, -1, -1):
                if stack[j].k == d["k"]:
                    b = stack.pop(j)
                    b.x, b.i1 = d, i
                    out.append(b)
                    break
    return out


def inside(b, lines, tags=None):
    for i in range(b.i0 + 1, b.i1):
        ln, tag, d = lines[i]
        if tags is None or tag in tags:
            yield i, tag, d


def B(w, b):
    return (w >> b) & 1


def field():
    return open(FIELD, "rb").read()[10:]


def walk_cells(fld, ox, oy, x, y):
    out = [(x, y)]
    while True:
        d = fld[(y - oy + 128) * 256 + (x - ox) + 128]
        x, y = x + DX[d], y + DY[d]
        if fld[(y - oy + 128) * 256 + (x - ox) + 128] == 8:
            return out
        out.append((x, y))


def free_near_walk(win, fld, x0, y0, size, ma, mb, origin, radius, stp):
    """quests.free_near with the walk of quests/travel § B1 (Walk(r, cell, origin, maskB), one cell per step)."""
    def ok(x, y):
        if win.blocked(x, y, size, ma):
            return False
        for cx, cy in walk_cells(fld, origin[0], origin[1], x, y):
            c = win.get(cx, cy)
            if c is None or c & mb:
                return False
        return True
    if ok(x0, y0):
        return x0, y0, 0
    best, pos = -1, None
    xl = xh = x0
    yl, yh, w = y0 - 1, y0 + 1, 2
    while (xh - x0 + 1) < radius:
        for y in range(yl, yh + 1, stp):
            for x in range(xl - 1, xh + 2, w):
                if ok(x, y):
                    d = abs(x - x0) + abs(y - y0)
                    if best == -1 or d < best:
                        best, pos = d, (x, y)
        for x in range(xl, xh + 1, stp):
            for y in range(yl, yh + 1, w):
                if ok(x, y):
                    d = abs(x - x0) + abs(y - y0)
                    if best == -1 or d < best:
                        best, pos = d, (x, y)
        if best != -1:
            break
        xl -= stp
        xh += stp
        yl -= stp
        yh += stp
        w += 2 * stp
    if pos is None:
        return x0, y0, -1
    return pos[0], pos[1], best


class Run:
    def __init__(self):
        self.n = collections.Counter()
        self.bad = []
        self.D = Q.Data()
        self.fld = field()
        self.notes = collections.defaultdict(collections.Counter)

    def hit(self, k, v=1):
        self.n[k] += v

    def ok(self, cond, k, msg):
        self.hit(k + " checks")
        if not cond:
            self.hit(k + " MISMATCH")
            self.bad.append("%s:%s %s: %s" % (self.name, self.ln, k, msg))
        return cond

    def note(self, k, v):
        self.notes[k][v] += 1

    # ------------------------------------------------------------------ per log
    def log(self, path):
        self.name = os.path.basename(path)
        self.ln = 0
        L = parse(path)
        self.L = L
        brs = brackets(L)
        self.brs = brs
        self.timers(L)
        self.qobj(L)
        self.words(L)
        self.desites(L, brs)
        self.joins(L, brs)
        self.talks(L, brs)
        self.seeds(L, brs)
        self.intros(L, brs)
        self.e11s(L, brs, next((d.get("grec") for ln, t, d in L if t == "QI1"), None))
        self.levelchanges(L, brs)
        self.larzuk(L)
        self.warps(L, brs)
        self.travel(L, brs)
        self.ff(L, brs)
        self.stale(L, brs)
        self.chain(L, brs)

    # ---- P4 P8
    def timers(self, L):
        for ln, tag, d in L:
            self.ln = ln
            if tag == "TMA":
                self.ok(d["tick"] == d["f"] // 20, "P4/P8 timer add tick = frame // 20", str(d))
            elif tag == "TMR":
                self.ok(d["f"] % 20 == 0 and d["tick"] == d["f"] // 20, "P4/P8 timer run on frame mod 20 = 0, tick = "
                        "frame / 20", str(d))
                self.ok(d["tick"] == d["due"] + 1, "P4/P8 timer runs at tick = due + 1", str(d))

    # ---- P7 P34
    def qobj(self, L):
        for ln, tag, d in L:
            if tag == "EV" and d.get("k") == "join" and d["ph"] == 0 and d.get("qobj") and d.get("rejoin") == 0:
                self.ln = ln
                q = d["qobj"]
                ids = [r[0] for r in q]
                main = [self.D.descs[r]["id"] for r in range(36, -1, -1)]
                self.ok(len(q) == 41 and sorted(ids) == list(range(41)), "P7 41 quest objects, ids 0..40", str(ids))
                self.ok(ids == [40, 39, 38, 37] + main, "P34 list order 40..37 then the main rows last to first",
                        "%s vs %s" % (ids, [40, 39, 38, 37] + main))
                info = {r[0]: r for r in q}
                self.ok([info[i][5] for i in (37, 38, 39, 40)] == [42] * 4 and
                        [info[i][1] for i in (37, 38, 39, 40)] == [0, 1, 2, 4], "P7 second table: word 42, acts I II "
                        "III V", str([info[i] for i in (37, 38, 39, 40)]))
                self.ok(all(info[i][2] == 0 and info[i][3] == 1 for i in (37, 38, 39, 40)) and
                        all(info[r["id"]][2] == 1 and info[r["id"]][3] == 1 for r in self.D.descs),
                        "P34 at the join's entry: main +0x09 = +0x0A = 1, second +0x09 = 0, +0x0A = 1", str(q))
                diff = sorted((r["row"], r["id"], r["word"], info[r["id"]][5]) for r in self.D.descs
                              if info[r["id"]][5] != r["word"])
                self.note("P34 rows whose +0xE0 differs from the descriptor word (row, id, desc word, +0xE0)", str(diff))
                self.note("P34 +0xE0 of rows 7, 24, 29 (id, +0xE0)", str([(self.D.descs[r]["id"],
                                                                           info[self.D.descs[r]["id"]][5])
                                                                          for r in (7, 24, 29)]))
                self.hit("P7/P34 games")

    # ---- P13 P16 R1
    def words(self, L):
        last = {}
        for ln, tag, d in L:
            if tag not in ("QS", "QC", "QK") or d.get("old") is None:
                continue
            self.ln = ln
            key = (d["rec"], d["w"])
            if key in last:
                exp, ptag, pb, pold = last[key]
                changed = exp != pold
                if self.ok(d["old"] == exp, "P13 %s then the next write's old word" % ptag,
                           "after %s b%s old %04x want %04x got %04x" % (ptag, pb, pold, exp, d["old"])):
                    if changed:
                        self.hit("P13 %s pairs whose write changed the word" % ptag)
            o = d["old"]
            if tag == "QS":
                new = o | (1 << d["b"])
            elif tag == "QC":
                new = o & ~(1 << d["b"]) & 0xFFFF
            else:
                new = o & ~0x0FFC
                self.hit("P16 QK calls")
                if o & 0x0FFC:
                    self.hit("P16 QK with bits 2-11 set before")
                if o & ~0x0FFC & 0xFFFF:
                    self.hit("P16 QK with bits outside 2-11 set before")
                self.note("P16 QK (ret, word, old)", "%s w%d %04x" % (d["ret"], d["w"], o))
            last[key] = (new, tag, d.get("b"), o)

    # ---- P39 P42
    def desites(self, L, brs):
        for b in brs:
            if b.k != "de":
                continue
            e = b.e
            self.note("P39/P42 dispatch sites (ret, ev, force, actf)", "%s e%s f%s a%s" % (e.get("ret"), e.get("ev"),
                                                                                         e.get("force"), e.get("actf")))
            self.ln = L[b.i0][0]
            if e.get("ret") == "00543ca7":
                self.ok(e["ev"] == 10 and e["force"] == 1 and e["actf"] == 0, "P39/P42 e10 from 0x00543CA2 (push 1 at 0x00543C96): force 1, "
                        "act filter 0", str(e.get("ev")))
                self.note("P39 e10 (unit, plr) fields", "%s %s" % (e.get("unit"), e.get("plr")))
                info = {q[0]: q for q in e["qobj"]}
                want = [i for i in e["slots"] if i in info]
                got = [d["id"] for i, t, d in inside(b, L, ("QCB",)) if d.get("unit") == "de" and d.get("ev") == 10]
                self.ok(got == want, "P39 e10 runs every object with its slot set, in list order, any act, forced",
                        "%s %s" % (want, got))
                later = [bb for bb in brs if bb.k == "de" and bb.e.get("ev") == 9 and bb.i0 > b.i1 and
                         bb.e.get("f") == e.get("f")]
                self.ok(not later, "P39 no e9 after the e10 in the same frame", str(len(later)))
                n9 = sum(1 for bb in brs if bb.k == "de" and bb.e.get("ev") == 9 and bb.i1 < b.i0 and
                         bb.e.get("f") == e.get("f"))
                self.hit("P39 e10 dispatches after %d e9 in the frame" % n9)
            if e.get("ev") == 0 and e.get("ret") not in ("00543d44",):
                self.note("P42 other e0 dispatch sites (ret, force)", "%s %s" % (e.get("ret"), e.get("force")))

    # ---- P18 P49 P98 P125 P130 P132 P141 P184 P190 P262 P304
    def joins(self, L, brs):
        grecp = next((d.get("grec") for ln, t, d in L if t == "QI1"), None)
        js = [b for b in brs if b.k == "join"]
        for b in js:
            e, x = b.e, b.x
            self.ln = L[b.i0][0]
            first = e.get("rejoin") == 0 and e.get("b150c") == 1
            writes = [(t, d) for i, t, d in inside(b, L, ("QS", "QC"))]
            # P262 P141: per join
            w36 = [d for t, d in writes if t == "QC" and d["w"] == 36 and d["b"] == 4]
            w10 = [d for t, d in writes if t == "QC" and d["w"] == 10 and d["b"] == 9]
            self.note("P262 QC w36 b4 per join (rejoin, rets)", "%s %s" % (e.get("rejoin"), [d["ret"] for d in w36]))
            self.note("P141 QC w10 b9 per join (rejoin, rets)", "%s %s" % (e.get("rejoin"), [d["ret"] for d in w10]))
            self.hit("joins (rejoin %s)" % e.get("rejoin"))
            rec = e.get("rec")
            if not first or rec is None:
                continue
            self.hit("first joins with the joiner's record")
            # P18 P130 P132
            w9 = rec[9]
            qc9 = [(d["ret"], d["b"]) for t, d in writes if t == "QC" and d["w"] == 9 and d.get("rec") != grecp]
            g9 = [d for t, d in writes if t == "QS" and d["w"] == 9 and d["b"] == 13 and d.get("rec") == grecp]
            ass = self.ass
            if B(w9, 0) and B(w9, 5) and ass is not None:
                want = [] if ass else [("00599284", 0), ("0059928e", 1), ("00599298", 15), ("005992a2", 5)]
                self.ok(qc9 == want, "P18/P130 w9 b0 b5 at the join: the four clears iff no ass", "ass %s %s" % (ass,
                                                                                                                qc9))
                self.hit("P130 w9 b0 b5 join, ass %s" % ass)
            elif B(w9, 0) and not B(w9, 5):
                self.ok(qc9 == [], "P130 w9 b0 without b5: no clear", str(qc9))
                self.hit("P130 w9 b0 without b5")
            elif not B(w9, 0):
                self.ok(qc9 == [], "P130 w9 b0 clear: no clear", str(qc9))
                self.hit("P130 w9 b0 clear")
            if B(w9, 0):
                self.ok(len(g9) == 1, "P130 w9 b0: G w9 b13 written in the join", str(len(g9)))
            # P98 P125 P184 P190 P304: per word, b0 of the joiner against a game-record b13 write in the join
            gw = collections.Counter(d["w"] for t, d in writes if t == "QS" and d["b"] == 13 and d.get("rec") == grecp)
            for w in range(42):
                self.note("gb13 join (word, joiner b0, G b13 writes)", "w%02d b0=%d g=%d" % (w, B(rec[w], 0), gw[w]))
            p40 = [d for t, d in writes if t == "QS" and d["w"] == 40 and d["b"] == 10 and d.get("rec") != grecp]
            self.note("P304 join (w40 b0, QS w40 b10 rets)", "b0=%d %s" % (B(rec[40], 0), [d["ret"] for d in p40]))
            # P49: the join's exit objects against the step bits
            if x and x.get("qobj") and e.get("qobj"):
                pre = {q[0]: q for q in e["qobj"]}
                post = {q[0]: q for q in x["qobj"]}
                for q in self.D.descs:
                    qid, w = q["id"], post[q["id"]][5]
                    if w >= 42:
                        continue
                    r = rec[w]
                    if B(r, 0) or B(r, 15):
                        continue
                    want = (2, 3) if B(r, 4) else (1, 3) if B(r, 3) else (1, 2) if B(r, 2) else None
                    got = (post[qid][4], post[qid][6] if len(post[qid]) > 6 else None)
                    if want is None:
                        self.note("P49 no step bit: (+0x0B, +0x0C) entry -> exit", "%s -> %s" % (
                            (pre[qid][4], pre[qid][6] if len(pre[qid]) > 6 else None), got))
                        continue
                    if got[1] is None:
                        self.ok(got[0] == want[0], "P49 step bit -> +0x0B (revision D)", "q%d w%d %04x %s" % (
                            qid, w, r, got))
                    else:
                        self.ok(got == want, "P49 step bit -> (+0x0B, +0x0C) (revision E)", "q%d w%d %04x want %s got "
                                "%s" % (qid, w, r, want, got))
                    self.note("P49 restored (quest, word, bit)", "q%d w%d b%d" % (qid, w, 4 if B(r, 4) else 3 if B(r, 3)
                                                                                  else 2))

    # ---- P58
    def talks(self, L, brs):
        open_ = {}
        for b in sorted((b for b in brs if b.k == "de"), key=lambda b: b.i0):
            e = b.e
            u = e.get("unit")
            if not u or u[0] != 1 or e["ev"] not in (0, 2, 11):
                continue
            self.ln = L[b.i0][0]
            uid = (u[1], u[2])
            if e["ev"] == 0 and e.get("ret") == "005457d9":
                self.ok(uid in open_ and len(open_) == 1, "P58 re-dispatched e0 (0x005457D4) inside the open talk of "
                        "its unit", str(uid))
                self.hit("P58 re-dispatched e0 after an e11 %s" % (L[b.i0 - 1][1] != "x"))
                continue
            if e["ev"] == 0:
                self.ok(uid not in open_, "P58 e0 opens a talk (no open talk with that unit)", str(uid))
                open_[uid] = 0
                self.hit("P58 talks opened")
            elif e["ev"] == 11:
                self.ok(uid in open_ and len(open_) == 1, "P58 e11 inside the open talk of its unit", str(uid))
                if uid in open_:
                    open_[uid] += 1
                self.hit("P58 e11")
            else:
                self.ok(uid in open_, "P58 e2 closes the talk of its unit", str(uid))
                if uid in open_:
                    self.hit("P58 talks closed with %s e11" % ("no" if open_[uid] == 0 else "some"))
                    del open_[uid]
        if open_:
            self.hit("P58 talks open at the log's end", len(open_))

    # ---- P63 P65 P322 R2
    def seeds(self, L, brs):
        for b in brs:
            if b.k != "de":
                continue
            e, x = b.e, b.x
            k = "e%d" % e["ev"]
            for s in ("qs", "ps", "gs"):
                if e.get(s) and x.get(s):
                    n = Q.nsteps(Q.pseed(e[s]), Q.pseed(x[s]), 16)
                    self.note("P63 dispatch %s steps by event (event ucls)" % s, "%s %s: %s" % (
                        k, e.get("ucls") if e["ev"] in (0, 2, 11) else "-", n))
        # the quest seed between consecutive observations
        obs = []
        for i, (ln, tag, d) in enumerate(L):
            if "qs" in d and isinstance(d["qs"], str) and ":" in d["qs"]:
                obs.append((i, tag, d))
        drawing = [b for b in brs if b.e.get("qs") and b.x.get("qs") and b.e["qs"] != b.x["qs"]]
        tm = [(i, j) for i, (ln, t, d) in enumerate(L) if t in ("TMR", "CRN0")
              for j in [next((k for k in range(i + 1, len(L)) if L[k][1] == {"TMR": "TMX", "CRN0": "CRN"}[t]), None)]
              if j]
        for (i, t, d), (j, t2, d2) in zip(obs, obs[1:]):
            if d["qs"] == d2["qs"]:
                self.hit("P65 consecutive quest-seed observations equal")
                continue
            n = Q.nsteps(Q.pseed(d["qs"]), Q.pseed(d2["qs"]), 64)
            inb = [b.k for b in drawing if b.i0 <= i and j <= b.i1] + [L[a][1] for a, c in tm if a <= i and j <= c]
            if t == "QGS" and n == 1:
                self.hit("P65 quest seed moved one step after a QGS draw")
                continue
            if inb:
                self.hit("P65 quest seed moved inside a drawing bracket")
                self.note("P65 moved inside (bracket kinds, steps)", "%s %s" % (sorted(set(inb)), n))
            else:
                self.ok(False, "P65 quest seed moved outside every drawing bracket", "%s %s -> %s %s steps %s" % (
                    t, d["qs"], t2, d2["qs"], n))
        for i, (ln, tag, d) in enumerate(L):
            if tag == "QGS":
                kinds = sorted({b.k + ("e%d" % b.e["ev"] if b.k == "de" else "") for b in brs if b.i0 < i < b.i1})
                tmr = any(a < i < c for a, c in tm)
                self.note("P322 QGS (ret, inside)", "%s %s%s" % (d["ret"], kinds, " timer" if tmr else ""))

    # ---- P125 P184 P190 P210: the record writes of each e11
    def e11s(self, L, brs, grecp):
        for b in brs:
            if b.k != "de" or b.e.get("ev") != 11:
                continue
            g = [(d["w"], d["b"]) for i, t, d in inside(b, L, ("QS",)) if d.get("rec") == grecp]
            p = ["%s w%d b%d old %04x" % (t, d["w"], d["b"], d["old"]) for i, t, d in inside(b, L, ("QS", "QC"))
                 if d.get("rec") != grecp and d.get("old") is not None]
            if g or b.e.get("p18") in (0xFD, 0x1D1, 0x1D2, 0x21A, 0x234, 0x272):
                self.note("P125/P184/P190/P210 e11 (npc, msg): game-record writes; player writes", "%s 0x%X: G %s; %s" % (
                    b.e.get("ucls"), b.e.get("p18") or 0, g, p))

    # ---- P182 P231 P305
    def intros(self, L, brs):
        for b in brs:
            if b.k != "de":
                continue
            sub = [(i, t, d) for i, t, d in inside(b, L, ("QCB", "QS", "QC", "QK"))]
            for n, (i, t, d) in enumerate(sub):
                if t == "QCB" and d.get("id") in (37, 38, 39, 40) and d.get("unit") == "de":
                    nxt = [tt for ii, tt, dd in sub[n + 1:]]
                    w = []
                    for tt in nxt:
                        if tt == "QCB":
                            break
                        w.append(tt)
                    self.ln = L[i][0]
                    self.ok(not w, "P182/P231/P305 object %d's callback writes no record bit" % d["id"], str(w))
                    self.hit("P182/P231/P305 object %d e%d callbacks" % (d["id"], b.e["ev"]))
                    seeds = all(b.e.get(s) == b.x.get(s) for s in ("qs", "ps"))
                    self.hit("P182/P231/P305 object %d e%d callbacks in a dispatch with qs, ps unchanged %s" % (
                        d["id"], b.e["ev"], seeds))
            if b.e["ev"] == 11 and 0x4E45 <= (b.e.get("p18") or 0) <= 0x4E47:
                q0 = {q[0]: q for q in b.e.get("qobj") or []}.get(31)
                nxt = next((d for ln, t, d in L[b.i1 + 1:] if t == "EV" and d.get("qobj")), None)
                q1 = {q[0]: q for q in (nxt or {}).get("qobj") or []}.get(31)
                self.note("P305 e11 0x4E45-0x4E47: quest 31 (+0x09, +0x0C) entry -> next list", "0x%X %s -> %s" % (
                    b.e["p18"], q0 and (q0[2], q0[6] if len(q0) > 6 else None), q1 and (q1[2], q1[6] if len(q1) > 6
                                                                                        else None)))

    # ---- P260
    def larzuk(self, L):
        ids = set()
        for ln, tag, d in L:
            if tag == "NPCQ":
                for r in d.get("n") or []:
                    if r[0] == 511:
                        ids.add(r[1])
        if ids:
            self.note("P260 class-511 unit ids per log", "%s %s" % (self.name[:40], sorted(ids)))

    # ---- T5 T69 T70 T71 P307 P308
    def warps(self, L, brs):
        for b in brs:
            if b.k != "warp":
                continue
            e, x = b.e, b.x
            self.note("T5/T69 warp caller (ret)", e.get("ret"))
            if e.get("pos") and e.get("wpos"):
                dx, dy = e["pos"][0] - e["wpos"][0], e["pos"][1] - e["wpos"][1]
                self.note("T69 player-to-warp (caller, max |d|, euclid)", "%s %d %.1f" % (
                    e.get("ret"), max(abs(dx), abs(dy)), (dx * dx + dy * dy) ** 0.5))
            gates = [k for k in b.kids if k.k == "warpgate"]
            dst = x.get("lid")
            self.note("T70 warp (src, exit lid, gate calls)", "%s -> %s gate %s" % (e.get("lid"), dst,
                                                                                [(g.e["src"], g.e["dst"], g.x.get("eax"))
                                                                                 for g in gates]))
            if dst is not None and e.get("lid") != dst:
                self.ok((dst in (73, 100, 118, 128, 132)) == bool(gates), "T70 gate called iff the destination is 73, "
                        "100, 118, 128 or 132", "%s -> %s %d" % (e.get("lid"), dst, len(gates)))

    # ---- the travel brackets
    def travel(self, L, brs):
        for b in brs:
            e, x = b.e, b.x
            k = b.k
            par = b.parent.k if b.parent else None
            self.ln = L[b.i0][0]
            if k == "p49":
                kids = [c.k for c in b.kids if c.k == "wptr"]
                self.note("T2/T34 p49 (lvl 0?, wptr inside, eax)", "lvl0=%s wptr=%d eax=%s" % (e.get("lvl") == 0,
                                                                                              len(kids), x.get("eax")))
            if k == "wptr":
                self.ok(par == "p49" and e.get("ret") == "0054c684", "T2 wptr inside a p49, from 0x0054C67F",
                        "%s %s" % (par, e.get("ret")))
                cl = [c for c in b.kids if c.k == "chlevel"]
                pk = b.parent.e.get("lvl") if b.parent else None
                self.note("T34 wptr (packet level 0?, chlevel inside, wptr's own eax 0?)", "%s %d %s" % (
                    pk == 0, len(cl), x.get("eax") == 0))
                for c in cl:
                    lv, ty = c.e.get("lvl"), c.e.get("type")
                    want = 13 if (lv in TOWNS or lv in (46, 74, 133, 134, 135, 136)) else 0
                    self.ok(ty == want, "T35 waypoint arrival type 13 for towns and 46, 74, 133-136, else 0",
                            "%s %s" % (lv, ty))
                    self.note("T35 arrival (class, type)", "%s %s" % ("town" if lv in TOWNS else lv if lv in (
                        46, 74, 133, 134, 135, 136) else "field", ty))
            if k == "npcmove":
                cl = [(c.k, c.e.get("lvl"), c.e.get("type")) for c in b.kids if c.k in ("chlevel", "pocreate")]
                self.note("T3/T38 npcmove (caller ret, lvl, type, inner)", "%s %s %s %s" % (e.get("ret"), e.get("lvl"),
                                                                                         e.get("type"), cl))
                if e.get("lvl"):
                    self.ok(cl == [("chlevel", e["lvl"], e["type"])] and Q.act_of(e["lvl"]) != Q.act_of(e.get("lid")),
                            "T38 another act: PlayerChangeLevel(level, type)", "%s %s" % (e, cl))
            if k == "npcact":
                prev = [c for c in brs if c.k == "npcmove" and c.i1 < b.i0 and c.e.get("f") == e.get("f")]
                self.note("T37 NPC class -> (npcmove lvl, type) before the npcact in the frame",
                          "%s %s" % (e["npc"][1], [(c.e.get("lvl"), c.e.get("type")) for c in prev]))
                rec = e.get("rec")
                if rec:
                    w = {155: 6, 210: 14, 367: 26}.get(e["npc"][1])
                    if w is not None:
                        self.note("P312 npcact (class, the gate word's b0)", "%s w%d b0=%d" % (e["npc"][1], w,
                                                                                             B(rec[w], 0)))
            if k == "tp":
                pcs = [c for c in b.kids if c.k == "pocreate"]
                self.note("T58 tp (town?, pocreate count, own entry -> exit)", "%s %d %s" % (
                    e.get("lid") in TOWNS, len(pcs), "same" if e.get("own") == x.get("own") else "changed"))
                if pcs and pcs[0].x and pcs[0].x.get("field"):
                    self.ok(x.get("own") == pcs[0].x["field"][2], "T58/T85 player data +0x48 = the new field end's id",
                            "%s %s" % (x.get("own"), pcs[0].x["field"]))
                    self.ok(pcs[0].x["field"][1] == 59, "T58 class 59", str(pcs[0].x["field"]))
                self.note("T4 tp caller (ret)", e.get("ret"))
            if k == "portal":
                ins = [c for c in b.kids if c.k == "de" and c.e.get("ev") == 3]
                town = e.get("lid") in TOWNS
                moved = x.get("lid") != e.get("lid")
                if moved:
                    self.ok(bool(ins) == town, "T63/T86 portal use: e3 raised iff the operator is in a town",
                            "town %s e3 %d" % (town, len(ins)))
                self.note("T63 portal (class, from town, moved, e3 inside, own entry -> exit)", "%s %s %s %d %s" % (
                    e["obj"][1], town, moved, len(ins), "kept" if e.get("own") == x.get("own") else "%s->%s" % (
                        e.get("own"), x.get("own"))))
                if e["obj"][1] != 59:
                    self.note("T68 non-59 portal (class, lid, odest, exit lid)", "%s %s %s %s" % (
                        e["obj"][1], e.get("lid"), e.get("odest"), x.get("lid")))
            if k == "place":
                self.note("T7 place caller (ret)", e.get("ret"))
            if k in ("p41", "p48"):
                self.note("T6/T8 %s (caller, eax)" % k, "%s %s" % (e.get("ret"), x.get("eax")))
            if k == "chlevel":
                self.note("T83 chlevel exit lid = the asked level", str(x.get("lid") == e.get("lvl")))

    # ---- T86: each level change, then the e3 that names it
    def levelchanges(self, L, brs):
        kinds = ("chlevel", "warp", "portal", "p41", "npcmove", "wptr")
        ch = sorted((b for b in brs if b.k in kinds and b.x and b.e.get("lid") is not None and
                     b.x.get("lid") is not None and b.e["lid"] != b.x["lid"] and not (b.parent and b.parent.k in kinds)),
                    key=lambda b: b.i0)
        e3 = [b for b in brs if b.k == "de" and b.e.get("ev") == 3]
        for k, b in enumerate(ch):
            end = ch[k + 1].i0 if k + 1 < len(ch) else len(L)
            win = [c for c in e3 if b.i0 < c.i0 < end]
            m = [c for c in win if c.e.get("p14") == b.e["lid"] and c.e.get("p18") == b.x["lid"]]
            inner = [c for c in win if c.i0 < b.i1]
            act = Q.act_of(b.e["lid"]) != Q.act_of(b.x["lid"])
            self.ln = L[b.i0][0]
            if act:
                self.note("T86 act change by %s: e3s before the next change (p14, p18, old, new)" % b.k, str(sorted(set(
                    (c.e.get("p14"), c.e.get("p18"), b.e["lid"], b.x["lid"]) for c in win))))
                continue
            town = b.k == "portal" and b.e["lid"] in TOWNS
            self.ok(len(m) == 1 + town and len(inner) == town, "T86 a level change in one act is followed by one e3 "
                    "(0x00543BB7) naming the old and new level; a portal used in a town raises one more inside",
                    "%s %s -> %s: %d, %d inside" % (b.k, b.e["lid"], b.x["lid"], len(m), len(inner)))
            self.hit("T86 level changes in one act by %s%s" % (b.k, " from a town" if town else ""))

    # ---- T9 T10 T11 T12 T19 T20 T22 T60
    def ff(self, L, brs):
        ff0 = None
        for i, (ln, tag, d) in enumerate(L):
            if tag == "FF0":
                ff0 = (i, d)
                continue
            if tag != "FFX" or ff0 is None:
                continue
            j, e = ff0
            ff0 = None
            self.ln = ln
            encl = [b for b in brs if b.i0 < j < b.i1]
            encl.sort(key=lambda b: b.i0)
            inner = encl[-1].k if encl else None
            ctx = inner
            if inner == "pocreate":
                pc = encl[-1]
                spots = [c for c in pc.kids if c.k == "spot" and c.i1 < j]
                ctx = "pocreate-partner" if spots else "pocreate-field"
            args = "size %s ma %04x mb %04x fb %s rad %s step %s other %s" % (
                e["size"], e["ma"], e["mb"], e["fb"], e["rad"], e["step"], "pos" if e.get("other") == [e["x"], e["y"]]
                else e.get("other"))
            self.note("T9-T12 COLL_FindFreeNear args by caller", "%s: %s" % (ctx, args))
            win = Q.Window(e["x"], e["y"], e["w"], e["cells"])
            try:
                if e.get("other"):
                    x, y, best = free_near_walk(win, self.fld, e["x"], e["y"], e["size"], e["ma"], e["mb"], e["other"],
                                                e["rad"], e["step"])
                else:
                    x, y, best = Q.free_near(win, e["x"], e["y"], e["size"], e["ma"], e["rad"], e["step"])
            except KeyError:
                self.hit("T20 search beyond the logged square (%s)" % ctx)
                continue
            key = "T20/T22/T60 search %s size %s step %s%s" % (ctx, e["size"], e["step"], " walk" if e.get("other")
                                                               else "")
            if best == -1 and not e["fb"]:
                self.ok(d["room"] == 0, key, "none found, room %s" % d["room"])
                self.hit(key + " none found")
                continue
            self.ok((x, y) == (d["x"], d["y"]), key, "predicted (%d, %d) got (%d, %d) from (%d, %d)" % (
                x, y, d["x"], d["y"], e["x"], e["y"]))
            self.hit(key + (" moved" if best else " in place"))
            if best and e.get("other"):
                # a control: the same search without the walk
                x2, y2, b2 = Q.free_near(win, e["x"], e["y"], e["size"], e["ma"], e["rad"], e["step"])
                self.hit("T60 control: the walk-free search %s" % ("agrees" if (x2, y2) == (x, y) else "differs"))
            if inner == "chact":
                sp = [b for b in encl[-1].kids if b.k == "spot"]
                if sp and sp[0].x:
                    dd = max(abs(d["x"] - sp[0].x["x"]), abs(d["y"] - sp[0].x["y"]))
                    self.note("T19 chact: landing cell's distance from the spot's cell (Chebyshev)", str(dd))

    # ---- T48
    def stale(self, L, brs):
        """Each level change dispatches e3 (p14 the old level, p18 the new) from 0x00538182 and then calls
        TownLevelLeave(…) at 0x00538191; NPCSTORE_ActStale's calls from it return to 0x00537402."""
        e3s = [b for b in brs if b.k == "de" and b.e.get("ev") == 3]
        st = [(i, d) for i, (ln, t, d) in enumerate(L) if t == "STALE" and d.get("ret") == 0x00537402]
        for k, b in enumerate(e3s):
            end = e3s[k + 1].i0 if k + 1 < len(e3s) else len(L)
            mine = [d for i, d in st if b.i1 < i < end]
            old, new = b.e.get("p14"), b.e.get("p18")
            self.ln = L[b.i0][0]
            if old == new:
                continue
            for d in mine:
                self.hit("T48 an ActStale after an e3 (not a check): the old level is a town of that act %s" % (
                    old in TOWNS and d["act"] == Q.act_of(old)))
            if len(mine) <= 1 and (mine or old in TOWNS):
                self.hit("T48 e3 %s -> %s (%s act): ActStale %s" % (
                    "town" if old in TOWNS else "field", "town" if new in TOWNS else "field",
                    "same" if Q.act_of(old) == Q.act_of(new) else "another", "once" if mine else "none"))
            elif len(mine) > 1:
                self.hit("T48 e3 followed by %d ActStale (a save and exit)" % len(mine))
        for i, d in st:
            if not any(b.i1 < i for b in e3s):
                self.hit("T48 ActStale before the first e3 (the game's start)")

    # ---- P54
    def chain(self, L, brs):
        prev = None
        for i, (ln, tag, d) in enumerate(L):
            if tag != "EV" or not d.get("qobj") or len(d["qobj"][0]) < 7:
                continue
            cur = {q[0]: q[6] for q in d["qobj"]}
            if prev is not None:
                for qid in cur:
                    if cur[qid] != prev[1].get(qid):
                        evs = sorted({"%s%s" % (b.k, "e%d" % b.e["ev"] if b.k == "de" else "") for b in self.brs
                                      if prev[0] <= b.i0 <= i})
                        self.note("P54 +0x0C changes (quest, old -> new, events between)", "q%d %s -> %s %s" % (
                            qid, prev[1].get(qid), cur[qid], evs[:4]))
            prev = (i, cur)

    # ------------------------------------------------------------------ the saves
    def saves(self, paths):
        try:
            import d2s
        except ImportError:
            return
        isc, kinds = d2s.load_isc(EXCEL), d2s.load_kinds(EXCEL)

        def load(p):
            if not os.path.exists(p):
                return None
            b = open(p, "rb").read()
            f = d2s.parse(b, isc, kinds)
            st = {sid: v for sid, prm, v in f["stats"]}
            codes = [it.get("code") for it in d2s.all_items(f)]
            q = f["sections"]["quests"]
            words = [[d2s.u16(b, q["off"] + 10 + 96 * dd + 2 * w) for w in range(48)] for dd in range(3)]
            return f["header"], st, codes, words
        for p in paths:
            base = p[:-4]
            a, z = load(base + ".in.d2s"), load(base + ".out.d2s")
            nm = os.path.basename(base)
            if a is None or z is None:
                continue
            (ha, sa, ca, wa), (hz, sz, cz, wz) = a, z
            self.note("P75/P237 in -> out (session: level, stat 4, stat 5)", "%s: %s %s %s -> %s %s %s" % (
                nm[-12:], ha["level"], sa.get(4, 0), sa.get(5, 0), hz["level"], sz.get(4, 0), sz.get(5, 0)))
            gone = sorted(set(c for c in ca if c in ("qey ", "qhr ", "qbr ", "qf1 ", "qf2 ")) -
                          set(c for c in cz if c in ("qey ", "qhr ", "qbr ", "qf1 ", "qf2 ")))
            kept = sorted(set(c for c in cz if c in ("qey ", "qhr ", "qbr ", "qf1 ", "qf2 ")))
            if gone or kept:
                self.note("P196 Khalim items (session: removed, kept)", "%s: %s %s" % (nm[-12:], gone, kept))
            self.note("P301 progression (session: in -> out; w40 b0 per difficulty in, out)", "%s: %d -> %d; %s %s" % (
                nm[-12:], ha["progression"], hz["progression"], [B(wa[dd][40], 0) for dd in range(3)],
                [B(wz[dd][40], 0) for dd in range(3)]))

    def ass_of(self, path):
        p = path[:-4] + ".in.d2s"
        if not os.path.exists(p):
            # part 1 kept no installed save; x-lut and nm-lut ran QuestBookLost (tools/d2s_recipes/quest-w9lost.json,
            # run:2026-10-17-quests' session table): its recipe lists no `ass `
            if os.path.basename(path) in ("2026-10-17-quests-x-lut.log", "2026-10-17-quests-nm-lut.log"):
                return '"ass' in open(os.path.join(HERE, "d2s_recipes", "quest-w9lost.json")).read()
            return None
        import d2s
        isc, kinds = d2s.load_isc(EXCEL), d2s.load_kinds(EXCEL)
        f = d2s.parse(open(p, "rb").read(), isc, kinds)
        return any(it.get("code") == "ass " for it in d2s.all_items(f))


def cmd_check(paths):
    R = Run()
    for p in paths:
        R.ass = R.ass_of(p)
        R.log(p)
    R.saves(paths)
    for k in sorted(R.n):
        print("%-100s %d" % (k, R.n[k]))
    for k in sorted(R.notes):
        print("NOTE %s" % k)
        for v, c in sorted(R.notes[k].items()):
            print("    %-96s %d" % (v, c))
    for b in R.bad[:200]:
        print("MISMATCH " + b)
    nchk = sum(v for k, v in R.n.items() if k.endswith(" checks"))
    print("SUMMARY mismatches=%d checks=%d logs=%d" % (len(R.bad), nchk, len(paths)))
    return 1 if R.bad else 0


def cmd_static():
    from collision import exe_read
    data = open(EXE, "rb").read()
    pe = struct.unpack_from("<I", data, 0x3C)[0]
    n = struct.unpack_from("<H", data, pe + 6)[0]
    o = struct.unpack_from("<H", data, pe + 20)[0]
    calls = []
    for i in range(n):
        name = data[pe + 24 + o + 40 * i: pe + 24 + o + 40 * i + 8].rstrip(b"\0")
        vs, ra, sz, ptr = struct.unpack_from("<IIII", data, pe + 24 + o + 40 * i + 8)
        if name != b".text":
            continue
        sec = data[ptr:ptr + sz]
        for j in range(len(sec) - 5):
            if sec[j] == 0xE8:
                va = 0x400000 + ra + j
                tgt = (va + 5 + struct.unpack_from("<i", sec, j + 1)[0]) & 0xFFFFFFFF
                if tgt == 0x00543E10:
                    calls.append(va)
    print("E8 calls to QUESTS_TimersRun 0x00543E10: %s" % ", ".join("0x%08X" % c for c in calls))
    b = exe_read(EXE, 0x00741790, 3 * 8)
    print("g_ItemUseFns rows 0..2 (u32 pairs): %s" % ", ".join("0x%08X" % v for v in struct.unpack("<6I", b)))
    return 0


def main(argv):
    if len(argv) >= 2 and argv[0] == "check":
        return cmd_check(argv[1:])
    if argv and argv[0] == "static":
        return cmd_static()
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
