"""Plan 0042 Phase 2: the quests-and-travel model and its checker, over the lines tools/gdb/quest-state.gdb writes
(tools/gdb/questev.py: EV, LPL, GT, QCB, PU, FF0/FFX; tools/gdb/quests.py: QI1, QS, QC).

Usage:
  python3 -I tools/quests.py check LOG [LOG ...]       # predict every checked line; exit 1 on a mismatch
  python3 -I tools/quests.py test                       # the model's self-test (also tools/test_quests.py)

What is predicted (docs/findings/quests/0001-progression.md, 0002-travel.md; every rule names its claim):
  dispatch    the callbacks of one QUESTS_DispatchEvent, in order: the quest objects in list order (object 40 down to
              row 0) whose slot for the event is set, whose +0x0A is 1 unless the event is forced, and whose act is
              the player's act when the act filter is on (0001 § 2)
  join        the first join with rejoin 0 and byte 0x0073150C set: every g_QuestDescs row with flag +0x0C = 0 whose
              word has bit 0 or 15 in the joiner's record is deactivated (+0x09 = +0x0A = +0x0B = 0) and its word's
              bit 15 is set in the game record, in descriptor order; no other quest is switched off by the pass (0001 § 3)
  deactivated a deactivated quest's (+0x09 = 0) callbacks of a forced event write no bit of that quest's word, but for
              the handlers that do not test +0x09 (deactivated_writes: quest 11's NPC 331 messages)
  seeds       per event kind, the steps of the game seed (gs), the quest seed (qs) and the player's unit seed (ps)
              between the entry and the exit: NPC 331 talk with the palace open (quest 11's +0x0E) one qs step;
              NPC 266 and 377 talks one ps step; town portal open two gs steps; every other kind none (0001 § 11,
              0002 § 10)
  level seed  LevelPointFind on a Levels.Position level steps the level seed once for point types 0, 5, 11 (when a
              point is found) and not for 13; a level without Position: no step (0002 § 4)
  portal pair the field end's seed is Init(gs.low) after one gs step at SUnitCreate; the partner's after the second
              gs step; the SetMode(1)/(2) that follows draws (Objects.Sync 0) only if the mode changes, and the run
              finds both ends already in that mode at creation, so no object-seed draw (corrects 0002 § 6's five)
  gates       packet 0x49 and the portal use pass iff GetTickCount() >= stamp + 10000 / 5000 (0002 § 3, § 9)
  packet 0x58 the word's bit 12 is set, nothing else (0001 § 4)
  warp gate   QUESTS_WarpGate(120, 118 or 128) = quest 35 active and its private "done" byte 0; a refused warp
              leaves the player where he was (0002 § 7)
  orb         the Compelling Orb's counter (quest 19 +0x18 -> +0x38) grows by one iff the object is in mode 0 and
              the operator's weapon code is 'qf2' (0001 § 9)
  free cell   COLL_FindFreeNear from the logged cells (pos +/- 12): the first free footprint by the ring order of
              0002 § 4 (counted "beyond" when the answer lies outside the logged square)
  spot        ActLevelSpot: the search starts at the tile's sub-tile (5 tx + 3, 5 ty + 3); the result is the search's
  chaining    per seed, consecutive events of one kind whose exit seed is the next one's entry seed (nothing drew
              between): counted as chained pairs per kind
Seeds are "low:high" hex; one step is low * 0x6AC690C5 + high (tools/rng.py). Stdlib only.
"""
import json
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
if HERE not in sys.path:
    sys.path.insert(0, HERE)
EXCEL = os.path.join(ROOT, "workspace", "merged", "data", "global", "excel")
EXE = os.path.join(ROOT, "workspace", "runtime", "game", "game.exe")
MULT = 0x6AC690C5
M32 = 0xFFFFFFFF


def pseed(s):
    lo, hi = s.split(":")
    return int(lo, 16), int(hi, 16)


def step(s, n=1):
    lo, hi = s
    for _ in range(n):
        v = lo * MULT + hi
        lo, hi = v & M32, (v >> 32) & M32
    return lo, hi


def nsteps(a, b, limit=8):
    """Steps from seed a to seed b (0..limit), or None."""
    s = a
    for k in range(limit + 1):
        if s == b:
            return k
        s = step(s)
    return None


def tsv(name):
    path = os.path.join(EXCEL, name)
    with open(path, errors="replace") as f:
        rows = [ln.rstrip("\r\n").split("\t") for ln in f]
    head = rows[0]
    return [dict(zip(head, r)) for r in rows[1:] if r and r[0] and r[0] != "Expansion"]


def ival(v, d=0):
    try:
        return int(v)
    except (TypeError, ValueError):
        return d


class Data:
    def __init__(self, excel=EXCEL, exe=EXE):
        global EXCEL
        EXCEL = excel
        self.position, self.wpidx = {}, {}
        for r in tsv("levels.txt"):
            i = ival(r.get("Id"), -1)
            if i < 0:
                continue
            self.position[i] = ival(r.get("Position"))
            w = ival(r.get("Waypoint"), 255)
            if w != 255:
                self.wpidx[i] = w
        self.sync = {}
        for k, r in enumerate(tsv("objects.txt")):
            self.sync[k] = ival(r.get("Sync"))
        self.groups = []
        self.descs = []
        if os.path.exists(exe):
            from collision import exe_read
            b = exe_read(exe, 0x00731510, 37 * 0x18)
            for i in range(37):
                init, act, _, flag, qid, word = struct.unpack_from("<6I", b, 0x18 * i)
                self.descs.append({"row": i, "act": act, "flag": flag, "id": qid, "word": word})
            g = exe_read(exe, 0x006EED88, 8 * 16)     # the point-type groups LevelPointPick reads: {has, group}
            self.groups = [struct.unpack_from("<2I", g, 8 * i) for i in range(16)]

    def point_match(self, want, typ):
        """LevelPointPick's test (0x0066AC60-0x0066AC83): the same type, or both in one group when the wanted
        type has one."""
        if typ == want:
            return True
        if want >= len(self.groups) or typ >= len(self.groups) or not self.groups[want][0]:
            return False
        return self.groups[want][1] == self.groups[typ][1]


def act_of(lid):
    if lid is None:
        return None
    return 0 if lid < 40 else 1 if lid < 75 else 2 if lid < 103 else 3 if lid < 109 else 4


# ---------------------------------------------------------------- the free-cell search (0002 § 4)
def footprint(x, y, size):
    if size in (0, 1):
        return [(x, y)]
    if size == 2:
        return [(x, y), (x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)]
    if size == 3:
        return [(x + dx, y + dy) for dy in (-1, 0, 1) for dx in (-1, 0, 1)]
    return None


class Window:
    def __init__(self, x0, y0, w, cells):
        self.x0, self.y0, self.w, self.c = x0, y0, w, cells
        self.n = 2 * w + 1

    def get(self, x, y):
        i, j = x - (self.x0 - self.w), y - (self.y0 - self.w)
        if not (0 <= i < self.n and 0 <= j < self.n):
            raise KeyError((x, y))
        return self.c[j * self.n + i]

    def blocked(self, x, y, size, mask):
        fp = footprint(x, y, size)
        if fp is None:
            return True
        v = 0
        for cx, cy in fp:
            c = self.get(cx, cy)
            if c is None:
                return True          # no map holds the cell: 0x27, unmasked
            v |= c & mask
        return v != 0


def free_near(win, x0, y0, size, mask, radius, stp):
    """The search of 0x0064DEA0 (0002 § 4); raises KeyError when it reads outside the logged square."""
    if not win.blocked(x0, y0, size, mask):
        return x0, y0, 0
    best, pos = -1, None
    xl = xh = x0
    yl, yh, w = y0 - 1, y0 + 1, 2
    while (xh - x0 + 1) < radius:
        for y in range(yl, yh + 1, stp):
            for x in range(xl - 1, xh + 2, w):
                if not win.blocked(x, y, size, mask):
                    d = abs(x - x0) + abs(y - y0)
                    if best == -1 or d < best:
                        best, pos = d, (x, y)
        for x in range(xl, xh + 1, stp):
            for y in range(yl, yh + 1, w):
                if not win.blocked(x, y, size, mask):
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


def deactivated_writes(qid, ev, e):
    """The bits a deactivated quest's callback still writes (0001 § 3: what keeps it inert is each handler's own
    test). Quest 11's e11 handler 0x0059AF50 tests only the NPC class (0x14B = 331) and the message: 0xBA sets word
    12 bit 7, 0xBB-0xBD bit 8, with no +0x09 test (0x0059AF84-0x0059AFC3; run:2026-10-17-quests). Every other
    handler the run reached writes nothing while its quest is off."""
    if qid == 11 and ev == 11 and e.get("p14") == 331:
        m = e.get("p18")
        if m == 0xBA:
            return [(12, 7)]
        if 0xBB <= m <= 0xBD:
            return [(12, 8)]
    return []


# ---------------------------------------------------------------- the checker
class Checker:
    def __init__(self, data):
        self.D = data
        self.n = {}
        self.bad = []
        self.reset()

    def reset(self):
        self.stack = []                 # open EV entries (kind, entry dict, nested lines)
        self.last_exit = {}             # (seed name, kind) -> exit seed of the last event of that kind
        self.ff = None
        self.grec = None
        self.pu = []
        self.lpl = None
        self.qcb = None
        self.lvlseed = {}               # level id -> the last level seed seen (exit of an lpf)

    def hit(self, k, v=1):
        self.n[k] = self.n.get(k, 0) + v

    def ok(self, cond, k, msg):
        self.hit(k + " checks")
        if not cond:
            self.hit(k + " MISMATCH")
            self.bad.append("%s:%d %s: %s" % (self.path, self.ln, k, msg))
        return cond

    # ---- per-line
    def line(self, tag, d):
        f = getattr(self, "on_" + tag, None)
        if f:
            f(d)

    def on_QI1(self, d):
        self.grec = d.get("grec")

    def note(self, tag, d):
        """A line inside open events: every open frame keeps it with the depth it came at."""
        n = len(self.stack)
        for fr in self.stack:
            fr[2].append((tag, d, n))

    def on_QS(self, d):
        self.note("QS", d)

    def on_QC(self, d):
        self.note("QC", d)

    def on_QCB(self, d):
        self.note("QCB", d)

    def on_LPL(self, d):
        self.lpl = d

    def on_PU(self, d):
        self.pu.append(d)

    def on_GT(self, d):
        lim = 10000 if d["k"] == "p49" else 5000
        self.ok(d["pass"] == int(((d["stamp"] + lim) & M32) <= d["tick"]),          # unsigned, as jbe
                "gate %s" % d["k"], "pass %s at tick %d stamp %d" % (d["pass"], d["tick"], d["stamp"]))
        self.hit("gate %s stamp %d" % (d["k"], d["stamp"]))

    def on_FF0(self, d):
        self.ff = d

    def on_FFX(self, d):
        e, self.ff = self.ff, None
        if not e:
            return
        win = Window(e["x"], e["y"], e["w"], e["cells"])
        if e.get("other"):
            self.hit("free search with a partner footprint (not modelled)")
            return
        try:
            x, y, best = free_near(win, e["x"], e["y"], e["size"], e["ma"], e["rad"], e["step"])
        except KeyError:
            self.hit("free search beyond the logged square")
            return
        if best == -1 and not e["fb"]:
            self.ok(d["room"] == 0, "free search", "no cell found, room %s" % d["room"])
            return
        self.ok((x, y) == (d["x"], d["y"]), "free search",
                "predicted (%d, %d) got (%d, %d) from (%d, %d) size %d mask %x step %d" % (
                    x, y, d["x"], d["y"], e["x"], e["y"], e["size"], e["ma"], e["step"]))
        self.hit("free search moved" if best else "free search in place")

    def on_EV(self, d):
        if d["ph"] == 0:
            self.stack.append((d["k"], d, []))
            if d["k"] == "lpf":
                self.lpl = None
            if d["k"] == "tp":
                self.pu = []
            return
        # an exit: the innermost open entry of that kind
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i][0] == d["k"]:
                k, e, sub = self.stack.pop(i)
                self.depth = i + 1
                self.event(k, e, d, sub)
                self.note("EV", d)
                return
        self.hit("exit without entry")

    # ---- per event
    def seeds_rule(self, k, e, x):
        """Predicted steps (gs, qs, ps), or None for a kind the run does not predict."""
        if k == "de":
            ev, cls = e["ev"], e.get("ucls")
            if ev == 0 and cls == 331:
                return 0, (1 if e.get("q11e") else 0), 0
            if ev == 0 and cls in (266, 377):
                return 0, 0, 1
            return 0, 0, 0
        if k == "tp":
            return None if x.get("own") and x.get("own") != e.get("own") else (0, 0, 0)   # ev_tp checks gs
        if k in ("pocreate", "join", "place", "due"):
            return None
        return 0, 0, 0

    def event(self, k, e, x, sub):
        self.hit("events %s" % k)
        # seeds at the entry and the exit
        rule = self.seeds_rule(k, e, x)
        names = ("gs", "qs", "ps")
        for i, s in enumerate(names):
            if e.get(s) is None or x.get(s) is None:
                continue
            a, b = pseed(e[s]), pseed(x[s])
            got = nsteps(a, b, 16)
            if rule is not None:
                want = rule[i]
                if want == 0 and got != 0 and k in ("chlevel", "chact", "npcmove", "p49", "wptr", "portal", "warp",
                                                     "p41", "lvlportal", "arcane", "durance", "wpop") and s == "gs":
                    # a level or room built inside the event (spawns: a DRLG/population oracle)
                    self.hit("%s gs moved by a build inside (oracle)" % k)
                else:
                    if self.ok(got == want, "seed %s %s" % (k, s), "%s steps %s, want %s (entry %s exit %s)" % (
                            s, got, want, e[s], x[s])) and want == 0:
                        self.hit("seed unchanged %s %s" % (k, s))
            # chaining: the exit of the last event of this kind is this entry
            key = (s, k, e.get("ucls"))
            if rule is not None and rule[i] > 0:
                if key in self.last_exit:
                    if self.last_exit[key] == e[s]:
                        self.hit("chained pairs %s %s %s" % (k, e.get("ucls"), s))
                    else:
                        self.hit("unchained pairs %s %s %s" % (k, e.get("ucls"), s))
                self.last_exit[key] = x[s]
        f = getattr(self, "ev_" + k, None)
        if f:
            f(e, x, sub)

    def ev_de(self, e, x, sub):
        ev, force, actf = e["ev"], e["force"], e["actf"]
        slots = e.get("slots")
        if slots is None:
            return
        info = {q[0]: q for q in e["qobj"]}
        pact = act_of(e.get("lid")) if actf == 1 else None
        want = []
        for qid in slots:
            q = info.get(qid)
            if q is None:
                continue
            if not force and q[3] != 1:
                continue
            if actf == 1 and pact is not None and q[1] != pact:
                continue
            want.append(qid)
        got = [d["id"] for t, d, n in sub if t == "QCB" and n == self.depth and d["unit"] == "de"]
        self.ok(got == want, "dispatch order e%d" % ev, "want %s got %s" % (want, got))
        self.hit("callbacks run e%d" % ev, len(got))
        # deactivated quests: callbacks run, no write to their own word
        off = {q[0]: q[5] for q in e["qobj"] if q[2] == 0 and q[0] < 37}
        ran_off = [i for i in got if i in off]
        if ran_off:
            self.hit("forced e%d callbacks of deactivated quests" % ev, len(ran_off))
            words = {off[i] for i in ran_off}
            writes = [(d["w"], d["b"]) for t, d, n in sub if t in ("QS", "QC") and d["w"] in words]
            want = []
            for i in ran_off:
                want += deactivated_writes(i, ev, e)
            self.ok(writes == want, "deactivated quest writes", "e%d writes %s, want %s" % (ev, writes, want))
            self.hit("deactivated quest writes (word, bit) %s" % (want,) if want else "deactivated quest no write")

    def ev_join(self, e, x, sub):
        rec = e["rec"]
        first = e["ready"] == 0
        if not (first and e["rejoin"] == 0 and e["b150c"]):
            self.hit("join without the pass")
            return
        want = [dd for dd in self.D.descs if dd["flag"] == 0 and rec and rec[dd["word"]] & 0x8001]
        writes = [d for t, d, n in sub if t == "QS" and d["ret"] == "0054633e"]
        self.ok([(d["w"], d["b"]) for d in writes] == [(dd["word"], 15) for dd in want], "join game-record marks",
                "want %s got %s" % ([dd["word"] for dd in want], [d["w"] for d in writes]))
        after = {q[0]: q for q in x["qobj"]}
        wid = {dd["id"] for dd in want}
        for dd in want:
            q = after.get(dd["id"])
            self.ok(q is not None and q[2] == 0 and q[3] == 0, "join deactivation",
                    "quest %d after %s" % (dd["id"], q))
        before = {q[0]: q for q in e["qobj"]}
        others = [qid for qid, q in after.items() if qid < 37 and qid not in wid and q[2] == 0
                  and before.get(qid, [0, 0, 1])[2] == 1]
        self.hit("join quests deactivated", len(want))
        self.hit("join other quests switched off by a first-join callback", len(others))
        g = x.get("grec")
        if g:
            for dd in want:
                self.ok(g[dd["word"]] & 0x8000, "join game record bit 15", "word %d = %x" % (dd["word"], g[dd["word"]]))

    def ev_lpf(self, e, x, sub):
        lid, typ = e["lvl"], e["type"]
        L = self.lpl
        if not L or L["lid"] != lid:
            self.hit("lpf without its level line")
            return
        a, b = pseed(L["ls"]), pseed(x["ls"])
        got = nsteps(a, b, 16)
        pos = self.D.position.get(lid, 0)
        pick = None
        if pos and typ != 13:
            if L.get("pts") is None:
                self.hit("lpf without the level's points (older logger)")
                return
            idx = [i for i, p in enumerate(L["pts"]) if self.D.point_match(typ, p[2])]
            want = 1 if idx else 0
            if idx:                        # LevelPointPick 0x0066AC40: k = r mod n + 1 (n not a power of two) or
                n = len(idx)               # (r & (n - 1)) + 1; the k-th matching point
                r = step(a)[0]
                k = (r % n if n & (n - 1) else r & (n - 1))
                pick = L["pts"][idx[k]]
            else:
                pick = L["pts"][0] if L["pts"] else None
        else:
            want = 0
        if pick is not None:
            self.ok((x["tx"], x["ty"]) == (pick[0], pick[1]), "level point pick type %d" % typ,
                    "level %d: (%d, %d), want (%d, %d)" % (lid, x["tx"], x["ty"], pick[0], pick[1]))
        if self.ok(got == want, "level seed type %d" % typ, "level %d Position %d: %s steps, want %d" % (
                lid, pos, got, want)):
            self.hit("level seed %s type %d step %d" % ("Position" if pos else "plain", typ, want))
        prev = self.lvlseed.get(lid)
        if prev is not None and want:
            self.hit("level seed chained pairs" if prev == L["ls"] else "level seed unchained pairs")
        self.lvlseed[lid] = x["ls"]

    def ev_tp(self, e, x, sub):
        if not x.get("own") or x["own"] == e.get("own"):
            self.hit("town portal refused (lid %s)" % e.get("lid"))
            return
        pu = {d["at"]: d for d in self.pu}
        gs0 = pseed(e["gs"])
        g1 = step(gs0)
        g2 = step(g1)
        ru = pu.get("roomupdate")
        pop = 0
        if ru:                         # the town end's room populated by RoomUpdateOne: its draws are an oracle
            pop = nsteps(g1, pseed(ru["gs"]), 64)
            if pop is None:
                self.ok(False, "portal room update", "gs %s after the field end %08x" % (ru["gs"], g1[0]))
                return
            g2 = step(pseed(ru["gs"]))
        elif pu.get("partner"):        # older logs: find the population draws between the two creations
            pop = nsteps(g1, (int(pu["partner"]["oinit"], 16), pseed(pu["partner"]["gs"])[1]), 64)
            pop = (pop - 1) if pop else 0
            g2 = step(g1, pop + 1)
        if pop:
            self.hit("town portal: gs draws of the town room's population (oracle)", pop)
        f, f1, p, p2 = pu.get("field"), pu.get("field1"), pu.get("partner"), pu.get("partner2")
        if not (f and f1 and p and p2):
            self.hit("town portal without its PU lines")
            return
        self.ok(int(f["oinit"], 16) == g1[0] and pseed(f["os"]) == (g1[0], 666), "portal field seed",
                "field %s %s gs+1 %08x" % (f["oinit"], f["os"], g1[0]))
        # SUnitCreate already leaves the field end in mode 1 and the partner in mode 2 (PU "omode"), so the
        # SetMode that follows changes nothing and draws nothing; a draw is predicted only for a real mode change
        fw = step(pseed(f["os"])) if f.get("omode") != 1 else pseed(f["os"])
        self.ok(pseed(f1["os"]) == fw, "portal field SetMode(1)", "%s -> %s (mode %s)" % (f["os"], f1["os"],
                                                                                         f.get("omode")))
        self.ok(int(p["oinit"], 16) == g2[0] and pseed(p["os"]) == (g2[0], 666), "portal partner seed",
                "partner %s %s gs+2 %08x" % (p["oinit"], p["os"], g2[0]))
        pw = step(pseed(p["os"])) if p.get("omode") != 2 else pseed(p["os"])
        self.ok(pseed(p2["os"]) == pw, "portal partner SetMode(2)", "%s -> %s (mode %s)" % (p["os"], p2["os"],
                                                                                           p.get("omode")))
        self.ok(pseed(x["gs"]) == g2, "town portal gs at exit", "exit %s, want %08x:%08x" % (x["gs"], g2[0], g2[1]))
        self.hit("town portal object draws %d" % ((fw != pseed(f["os"])) + (pw != pseed(p["os"]))))
        self.hit("town portals opened")

    def ev_p58(self, e, x, sub):
        w = e["w"]
        if w >= 42 or e.get("old") is None:
            self.hit("packet 0x58 word %d (no write)" % w)
            return
        self.ok(x.get("new") == e["old"] | 0x1000, "packet 0x58", "word %d %x -> %x" % (w, e["old"], x.get("new")))
        self.hit("packet 0x58 word %d" % w)

    def ev_warpgate(self, e, x, sub):
        src, dst = e["src"], e["dst"]
        if src == 120 and dst in (118, 128):
            q = e.get("q35")
            want = int(bool(q and q[0] and q[2] == 0))
            self.ok(x["eax"] == want, "summit warp gate", "120 -> %d: %s, want %d (q35 %s)" % (dst, x["eax"], want, q))
            self.hit("summit warp %s" % ("refused" if want else "allowed"))
        else:
            self.hit("warp gate %d -> %d = %d" % (src, dst, x["eax"]))

    def ev_warp(self, e, x, sub):
        self.hit("warps")

    def ev_orb(self, e, x, sub):
        self.hit("orb operates")

    def ev_p48(self, e, x, sub):
        if e.get("c4c") == 1:
            self.ok(x.get("c4c") == 0 and x["eax"] == 0, "packet 0x48 clear", "+0x4C %s -> %s" % (e.get("c4c"),
                                                                                                    x.get("c4c")))
        else:
            self.ok(x["eax"] == 2, "packet 0x48 no-op", "eax %s" % x["eax"])

    def ev_wpop(self, e, x, sub):
        lid = e.get("lid")
        idx = self.D.wpidx.get(lid)
        if idx is not None and x.get("wp"):
            b = bytes.fromhex(x["wp"])
            self.ok(b[idx >> 3] >> (idx & 7) & 1, "waypoint record bit", "level %d index %d" % (lid, idx))
        cls = e["obj"][1] if e.get("obj") else None
        m0, m1 = e.get("omode"), x.get("omode")
        if m0 == 0:
            self.ok(m1 == 1, "waypoint mode 0 -> 1", "mode %s" % m1)
        else:
            self.ok(m1 == m0, "waypoint mode kept", "%s -> %s" % (m0, m1))
        want = 1 if (m0 == 0 and self.D.sync.get(cls) == 0) else 0
        got = nsteps(pseed(e["os"]), pseed(x["os"]), 8)
        self.ok(got == want, "waypoint object seed", "class %s Sync %s mode %s: %s steps" % (
            cls, self.D.sync.get(cls), m0, got))

    def run(self, paths):
        for path in paths:
            self.path = path
            self.reset()
            with open(path, errors="replace") as f:
                for self.ln, line in enumerate(f, 1):
                    tag, _, rest = line.partition(" ")
                    if not rest.startswith("{"):
                        continue
                    try:
                        d = json.loads(rest)
                    except ValueError:
                        continue
                    try:
                        self.line(tag, d)
                    except (KeyError, TypeError, ValueError) as ex:
                        self.hit("line errors")
                        self.bad.append("%s:%d %s: checker error %r" % (path, self.ln, tag, ex))
        return self


def cmd_check(paths):
    c = Checker(Data()).run(paths)
    for k in sorted(c.n):
        print("%-70s %d" % (k, c.n[k]))
    for b in c.bad[:50]:
        print("MISMATCH " + b)
    mism = sum(v for k, v in c.n.items() if k.endswith("MISMATCH")) + c.n.get("line errors", 0)
    checks = sum(v for k, v in c.n.items() if k.endswith(" checks"))
    print("SUMMARY mismatches=%d checks=%d logs=%d" % (mism, checks, len(paths)))
    return 1 if mism else 0


def main(argv):
    if not argv or argv[0] not in ("check", "test"):
        print(__doc__)
        return 2
    if argv[0] == "test":
        import unittest
        import test_quests
        r = unittest.TextTestRunner(verbosity=1).run(unittest.defaultTestLoader.loadTestsFromModule(test_quests))
        return 0 if r.wasSuccessful() else 1
    return cmd_check(argv[1:])


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
