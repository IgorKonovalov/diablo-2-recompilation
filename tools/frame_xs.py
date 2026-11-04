"""Plan 0055 Phase 2b, reader rev 2: the chain with the LCG applied at every logged step (ruling 2 of the `lane/p55b` review).

The logger (tools/gdb/frame.py rev 2) writes an `XS {fr, site, low, ra}` line for every execution of an LCG multiplier site in a
window. This module keeps each chained seed's exact value (the game seed `Game+0xD0`, a unit's seed by (type, guid), a room's
seed by its pointer) from its first reading in the window, applies the LCG (rng/0001) at every `XS` whose low word matches it,
and asserts, each failing the window:

  arith   every logged reading equals the value the applied steps give, exactly: a seed that moves with no XS, an XS too many
          or a write fails. A low word two seeds share (a new unit's Init of the game seed's low) keeps both alternatives
          until each one's next reading; a reading that matches neither fails.
  class   every step on a chained seed is `own` (that unit's event, or the player's message, is open), `game` (the game seed,
          inside an open pair) or `touch` (another unit's event is open). With no pair open a step passes only at a site of
          the pass-draw table (PASSDRAW). A touch passes only at a site (or return address, for the six sites inside rng/0001's
          primitives) of the touch table (TOUCH) and only under the row's trigger (kill, defender, owner). "Located" is gone.
  even    a game-seed step count that is odd inside an event with a KD (items/tc H7: 2 per item).
  first   a missile's first reading, if its high word is 0x29A (an untouched Init), must be the low of a game-seed step of the
          window (skills/missiles C3), except in the window's first frame (created before it).
  free    no `own` step in a kind 11 or kind 6 event (their draw-free reading, frame/0002 §§ 6-7).
  rank    within a frame the top-level walks run in rank order; slot events in QE order; an every-frame walk newest QF first.

and counts what the record states: steps per class and per site, touches per trigger, entries whose seed had moved against
those it had not (ADR-0028 item 7), the KD events, the order pairs, the cross-type every-frame runs per receiving type.
`selftest2` builds consistent synthetic logs and the nine controls of the ruling (plus the draw-free control): each fails the
test it is for and nothing else. Stdlib only; no game.
"""
import collections
import json
import random

import frame_window as fw

M32 = fw.M32
INIT_HI = 0x29A
PAIRS = ("UE0", "MSG0", "RU0", "TQ0", "SV0")


def _step(t):
    return fw.step(t)


def check_chain2(w, touch=None, passdraw=None):
    """-> dict(fails [dict(line, tag, kind, msg, key, ...)], counts ...) for one window of fw.parse_log."""
    touch = fw.TOUCH if touch is None else touch
    passdraw = fw.PASSDRAW if passdraw is None else passdraw
    tmap = {}
    for row in touch:
        for a in row["at"]:
            tmap.setdefault(a, []).append(row)
    legacy = not any(t == "XS" for _n, t, _o in w["lines"])    # a log of logger rev 1: no step is logged, so no draw inside an open pair
    fails = []                                                   # is visible: exits and nested entries are set, not compared
    alts = {}                     # key -> set of possible current (lo, hi)
    moved = set()                 # keys stepped by an XS since their last reading
    stack = []                    # open pairs
    gpost = {}                    # low word after a game-seed step -> line
    cls_n = collections.Counter()           # class -> steps
    site_n = collections.Counter()          # (class, trigger or "", loc) -> steps
    untracked = collections.Counter()
    ambig = []
    ent = collections.Counter()             # entry readings by "moved" / "unmoved"
    reads = collections.Counter()
    firsts = collections.Counter()          # missile firsts: predicted / init_unmatched_first_frame / other
    kds = []
    ev_info = {}                            # open record line -> dict(game steps)
    free_runs = collections.Counter()
    rank_n = collections.Counter()
    last_rank = -1
    cur_frame = None
    frame_start = w["start"]
    slots = collections.defaultdict(list)   # (type, due) -> [(id, kind)] queue order
    slot_pos = collections.Counter()
    qf_line = {}                            # (ut, id, kind) -> line of the latest QF
    ef_seen = collections.defaultdict(list)  # (frame, ty) -> [(line of the QF or None, id, kind)]
    cross = collections.Counter()           # receiving type -> every-frame runs of a record queued by another type's event in that frame
    qf_by_frame = collections.defaultdict(dict)   # frame -> {(ut, id, kind): queuing event type}

    def fail(no, tag, kind, msg, **kw):
        fails.append(dict(line=no, tag=tag, kind=kind, msg=msg, **kw))

    def own_of(key):
        for r in stack:
            if r["tag"] == "UE0" and key == ("U", r["ty"], r["id"]):
                return True
            if r["tag"] == "MSG0" and key == ("U", 0, r["id"]):
                return True
            if r["tag"] == "RU0" and key == ("R", r["room"]):
                return True
        return False

    def reading(key, seed_s, role, no, tag, o):
        if not seed_s:
            return
        seed = fw.sd(seed_s)
        reads[role] += 1
        a = alts.get(key)
        if a is None:
            alts[key] = {seed}
            moved.discard(key)
            firsts["named"] += 1
            if key[0] == "U" and key[1] == 3 and role == "entry":
                if legacy:
                    firsts["missile_legacy"] += 1
                elif seed[1] == INIT_HI:
                    if seed[0] in gpost:
                        firsts["missile_predicted"] += 1
                    elif o.get("fr") <= frame_start:
                        firsts["missile_before_window"] += 1
                    else:
                        firsts["missile_unmatched"] += 1
                        fail(no, tag, "first", "missile %s: first reading %s is an Init seed whose low word is no game-seed step of the window" % (key[2], seed_s), key=key)
                else:
                    firsts["missile_not_init"] += 1
            return
        if role == "entry":
            ent["moved" if key in moved else "unmoved"] += 1
        skip = legacy and (role == "exit" or (role == "entry" and (
            bool(stack) if key == "G" else any(key == ("U", r["ty"], r["id"]) or key == ("U", 0, r["id"]) if r["tag"] in ("UE0", "MSG0")
                                               else (r["tag"] == "RU0" and key == ("R", r["room"])) for r in stack))))
        if seed not in a and not skip:
            exp = sorted(a)[0]
            rel = fw.relation(fw.fmt(exp), seed_s)
            fail(no, tag, "arith", "%s read %s, the applied steps give %s (%s%s)" % (
                key, seed_s, fw.fmt(exp), rel[0], (" %d" % rel[1]) if rel[1] is not None else ""), key=key, rel=rel[0], k=rel[1])
        alts[key] = {seed}
        moved.discard(key)

    def xs(no, o):
        low = o["low"]
        loc = o.get("ra") or o["site"]
        cands = [k for k, a in alts.items() if any(v[0] == low for v in a)]
        if not cands:
            untracked[(loc, bool(stack))] += 1
            return
        for k in cands:
            a = alts[k]
            if len(cands) > 1 or len(a) > 1:
                alts[k] = a | {_step(v) for v in a if v[0] == low}
            else:
                alts[k] = {_step(next(iter(a)))}
            moved.add(k)
        if len(cands) > 1:
            ambig.append((no, cands))
        key = "G" if "G" in cands else cands[0]
        if key == "G":
            for v in alts["G"]:
                gpost[v[0]] = no
            if stack:
                cls = "game"
                for r in stack:
                    if r["tag"] == "UE0":
                        r["g"] += 1
            else:
                cls = "pass"
                if loc not in passdraw:
                    fail(no, "XS", "nopair", "game-seed step at %#x with no pair open, not a pass-draw site" % loc, key=key, loc=loc)
        elif not stack:
            cls = "pass"
            if loc not in passdraw:
                fail(no, "XS", "nopair", "%s stepped at %#x with no pair open, not a pass-draw site" % (key, loc), key=key, loc=loc)
        elif own_of(key):
            cls = "own"
            top = next((r for r in reversed(stack) if r["tag"] == "UE0"), None)
            if top is not None and key == ("U", top["ty"], top["id"]) and top["kind"] in (6, 11):
                fail(no, "XS", "free", "own step of unit %s in a kind %d event (draw-free)" % (key[2], top["kind"]), key=key, loc=loc)
            if top is not None:
                top["own"] += 1
        else:
            cls = "touch"
            ok_row = None
            for row in tmap.get(loc, ()):
                if trigger_holds(row["trigger"], key):
                    ok_row = row
                    break
            if not tmap.get(loc):
                fail(no, "XS", "class", "touch on %s at %#x: not a site of the touch table" % (key, loc), key=key, loc=loc)
            elif ok_row is None:
                fail(no, "XS", "trigger", "touch on %s at %#x: the site is listed, its trigger (%s) does not hold" % (
                    key, loc, "/".join(r["trigger"] for r in tmap[loc])), key=key, loc=loc)
            else:
                site_n[("touch", ok_row["trigger"], loc)] += 1
                cls_n["touch:" + ok_row["trigger"]] += 1
        cls_n[cls] += 1
        if cls != "touch":
            site_n[(cls, "", loc)] += 1

    def trigger_holds(trig, key):
        if trig == "kill":
            return any(key in r.get("kills", ()) for r in stack)
        if key[0] != "U":
            return False
        for r in stack:
            if r["tag"] != "UE0":
                continue
            if trig in ("defender", "owner"):
                if r["ty"] == 3 and key[1] in (0, 1):
                    return True
                if trig == "defender" and r["ty"] in (0, 1) and r["kind"] in fw.ATTACK_KINDS and key[1] in (0, 1) and key != ("U", r["ty"], r["id"]):
                    return True
        return False

    for no, tag, o in w["lines"]:
        if tag in fw.BOOKKEEPING:
            continue
        if tag == "FT0":
            cur_frame = o["fr"]
            last_rank = -1
            reading("G", o.get("gs"), "point", no, tag, o)
        elif tag == "FT1":
            reading("G", o.get("gs"), "point", no, tag, o)
            ef_seen.clear()
        elif tag in ("FP", "TM", "ACL"):
            if o.get("gs"):
                reading("G", o["gs"], "point", no, tag, o)
        elif tag == "XS":
            xs(no, o)
        elif tag == "KD":
            key = ("U", o["ty"], o["id"])
            r = next((r for r in reversed(stack) if r["tag"] == "UE0"), stack[-1] if stack else None)
            if r is not None:
                r.setdefault("kills", set()).add(key)
                r["kd"] = True
                kds.append(dict(line=no, key=key, rec=r["line"], fr=o["fr"]))
            else:
                kds.append(dict(line=no, key=key, rec=None, fr=o["fr"]))
        elif tag in fw.ENTRIES:
            rec = dict(tag=tag, line=no, g=0, own=0, kind=o.get("kind"), ty=o.get("ty"), id=o.get("id"), room=o.get("room"), o=o)
            if tag == "UE0":
                reading("G", o.get("gs"), "entry", no, tag, o)
                if o.get("us"):
                    reading(("U", o["ty"], o["id"]), o["us"], "entry", no, tag, o)
                if not stack:
                    r = fw.RANK.get(o["ty"], (0, 0))[0 if o["lst"] == "ef" else 1]
                    rank_n["ue0"] += 1
                    if r < last_rank:
                        fail(no, tag, "rank", "frame %s: a walk of rank %d after rank %d" % (o["fr"], r, last_rank))
                    last_rank = max(last_rank, r)
                    if o["lst"] == "slot":
                        k = (o["ty"], o["fr"])
                        q = slots.get(k, [])
                        e = (o["id"], o["kind"])
                        if e in q[slot_pos[k]:]:
                            slot_pos[k] = q.index(e, slot_pos[k]) + 1
                            rank_n["slot_placed"] += 1
                        elif e in q:
                            rank_n["slot_inverted"] += 1
                            fail(no, tag, "slot", "frame %s: slot event %s ran before an earlier-queued one" % (o["fr"], e))
                    else:
                        seq = ef_seen[(o["fr"], o["ty"])]
                        ql = qf_line.get((o["ty"], o["id"], o["kind"]))
                        if ql is not None:
                            for pl, _i, _k in seq:
                                if pl is not None and pl < ql:
                                    rank_n["ef_inverted"] += 1
                                    fail(no, tag, "ef", "frame %s: every-frame event %s ran after one queued earlier (newest first expected)" % (
                                        o["fr"], (o["id"], o["kind"])))
                                    break
                            rank_n["ef_placed"] += 1
                        seq.append((ql, o["id"], o["kind"]))
                        qq = qf_by_frame[o["fr"]].get((o["ty"], o["id"], o["kind"]))
                        if qq is not None and qq != o["ty"]:
                            cross[o["ty"]] += 1
            elif tag == "MSG0":
                reading("G", o.get("gs"), "entry", no, tag, o)
                if o.get("ps") and o.get("id") is not None:
                    reading(("U", 0, o["id"]), o["ps"], "entry", no, tag, o)
            elif tag == "RU0":
                reading("G", o.get("gs"), "entry", no, tag, o)
                if o.get("rs"):
                    reading(("R", o["room"]), o["rs"], "entry", no, tag, o)
            else:
                reading("G", o.get("gs"), "entry", no, tag, o)
            stack.append(rec)
        elif tag in fw.CLOSE:
            if not stack:
                continue
            rec = stack.pop()
            reading("G", o.get("gs"), "exit", no, tag, o)
            if tag == "UE1":
                if o.get("us"):
                    reading(("U", rec["ty"], rec["id"]), o["us"], "exit", no, tag, o)
                else:
                    alts.pop(("U", rec["ty"], rec["id"]), None)
                if rec["kind"] in (6, 11):
                    free_runs[(rec["ty"], rec["kind"], "runs")] += 1
                    if not rec["own"]:
                        free_runs[(rec["ty"], rec["kind"], "no_own")] += 1
                if rec.get("kd"):
                    if rec["g"] % 2:
                        fail(no, tag, "even", "event at line %d holds a KD and %d game-seed steps (odd)" % (rec["line"], rec["g"]))
                    for kd in kds:
                        if kd["rec"] == rec["line"]:
                            kd["g"] = rec["g"]
            elif tag == "MSG1" and o.get("ps") and rec.get("id") is not None:
                reading(("U", 0, rec["id"]), o["ps"], "exit", no, tag, o)
            elif tag == "RU1" and o.get("rs"):
                reading(("R", rec["room"]), o["rs"], "exit", no, tag, o)
        elif tag == "RC":
            if o.get("rs"):
                alts[("R", o["room"])] = {fw.sd(o["rs"])}
                moved.discard(("R", o["room"]))
        elif tag == "RR":
            alts.pop(("R", o["room"]), None)
        elif tag == "QE":
            if o.get("ut") is not None:
                slots[(o["ut"], o["asked"])].append((o["id"], o["kind"]))
        elif tag == "QF":
            if o.get("ut") is not None:
                qf_line[(o["ut"], o["id"], o["kind"])] = no
                top = next((r for r in reversed(stack) if r["tag"] == "UE0"), None)
                if top is not None:
                    qf_by_frame[o["fr"]][(o["ut"], o["id"], o["kind"])] = top["ty"]
    return dict(fails=fails, cls=cls_n, sites=site_n, untracked=untracked, ambig=ambig, entries=ent, reads=reads, firsts=firsts,
                kds=kds, free=free_runs, order=rank_n, cross=cross, has_xs=any(t == "XS" for _n, t, _o in w["lines"]))


def kd_report(x):
    """-> list of (frame, key, game-seed steps) of the KD events."""
    return [(k["fr"], k["key"], k.get("g")) for k in x["kds"]]


# ------------------------------------------------------------------------------------------------------ synthetic logs
SITE_PASS, SITE_OWN, SITE_GAME, SITE_KILL, SITE_DEF, SITE_UNLISTED = 0x500010, 0x500020, 0x500030, 0x500040, 0x500050, 0x5000F0
SYN_PASS = {SITE_PASS: ("fn:synthetic", "synthetic")}
SYN_TOUCH = [dict(trigger="kill", at={SITE_KILL}, fn="fn:synthetic", spec="synthetic"),
             dict(trigger="defender", at={SITE_DEF}, fn="fn:synthetic", spec="synthetic")]


class Gen:
    """A consistent synthetic window (6 frames) with one fault switch per control. Every step is an XS line and every reading
    follows the applied steps, so the clean log passes and a switch breaks exactly one test."""

    def __init__(self, **sw):
        self.sw = sw
        self.L = []
        self.n = 0
        self.g = (0x2A, INIT_HI)
        self.s = {("U", 0, 1): (0x1111, INIT_HI), ("U", 1, 10): (0x2222, INIT_HI), ("U", 1, 11): (0x3333, INIT_HI),
                  ("U", 3, 500): (0x4444, 0x1234)}
        self.fr = 0

    def emit(self, tag, d):
        self.n += 1
        d["n"] = self.n
        self.L.append("%s %s" % (tag, json.dumps(d, separators=(",", ":"))))

    def draw(self, key, k, site, ra=None, log=True):
        for _ in range(k):
            t = self.g if key == "G" else self.s[key]
            if log:
                d = dict(fr=self.fr, site=site, low=t[0])
                if ra is not None:
                    d["ra"] = ra
                self.emit("XS", d)
            t = fw.step(t)
            if key == "G":
                self.g = t
            else:
                self.s[key] = t

    def gs(self):
        return fw.fmt(self.g)

    def ue0(self, ty, i, kind, lst, key):
        self.emit("UE0", dict(fr=self.fr, ty=ty, id=i, lst=lst, kind=kind, rf=self.fr, a=0, b=0, cb=1, site=0x540FB2,
                              u=0x1000 + i, us=fw.fmt(self.s[key]), gs=self.gs()))

    def ue1(self, ty, i, key):
        self.emit("UE1", dict(fr=self.fr, id=i, site=0x540FB2, u=0x1000 + i, us=fw.fmt(self.s[key]), gs=self.gs(), gone=0))

    def build(self, frames=6, start=100):
        sw = self.sw
        self.emit("WIN", dict(id=1, scene="pack", len=frames, start=start, fr=start, wall=1.0, mono=1.0, cover=0, rev=2))
        new_missile = None
        for f in range(start, start + frames):
            self.fr = f
            self.emit("FT0", dict(fr=f, pre=f - 1, gs=self.gs(), hc=0, game=4096))
            # the pass draws (listed site), or an unlisted one
            if f == start + 1:
                self.draw("G", 1, SITE_UNLISTED if sw.get("pass_unlisted") else SITE_PASS)
                self.emit("FP", dict(fr=f, site=0x52D8EB, gs=self.gs()))
            # the queue: two monster slot events queued in the order 10 then 11, for frame start+3
            if f == start:
                self.emit("QE", dict(fr=f, kind=0, asked=start + 3, ut=1, id=10, ra=1))
                self.emit("QE", dict(fr=f, kind=0, asked=start + 3, ut=1, id=11, ra=1))
            # missile 500 (slot): a kill
            if f == start + 2:
                self.ue0(3, 500, 1, "slot", ("U", 3, 500))
                if not sw.get("no_kd"):
                    self.emit("KD", dict(fr=f, ty=1, id=11))
                self.draw("G", sw.get("kill_game", 2), SITE_GAME)
                tsite = SITE_UNLISTED if sw.get("touch_unlisted") else SITE_KILL
                self.draw(("U", 1, 11), 3, tsite)
                self.ue1(3, 500, ("U", 3, 500))
            # the new missile's first event, the next frame: Init(post.low), possibly off by one
            if f == start + 4 and new_missile:
                lo = new_missile[0] + (1 if sw.get("first_off") else 0)
                self.s[("U", 3, 501)] = (lo & M32, INIT_HI)
                self.ue0(3, 501, 1, "ef", ("U", 3, 501))
                self.ue1(3, 501, ("U", 3, 501))
            # the player's kind 11 (draw-free), and its optional own step
            ue_player = (6, 7)
            self.ue0(0, 1, 11, "ef", ("U", 0, 1))
            if sw.get("free_draw"):
                self.draw(("U", 0, 1), 1, SITE_OWN)
            self.ue1(0, 1, ("U", 0, 1))
            # the monsters' slot events at start+3 (queue order 10, 11; inverted when asked)
            if f == start + 3:
                order = [11, 10] if sw.get("slot_inverted") else [10, 11]
                for i in order:
                    self.ue0(1, i, 0, "slot", ("U", 1, i))
                    if i == 10:
                        self.draw(("U", 1, 10), 2, SITE_OWN)
                        self.draw("G", 1, SITE_GAME)        # a missile is created: SUnitCreate steps the game seed once
                        new_missile = (self.g[0], INIT_HI)
                    if i == 11 and sw.get("extra_xs"):     # an XS whose step the seed did not take
                        self.emit("XS", dict(fr=f, site=SITE_GAME, low=self.g[0]))
                    self.ue1(1, i, ("U", 1, i))
            # a defender touch inside a monster attack event (the trigger of the DEF site)
            if f == start + 5:
                if sw.get("def_no_trigger"):          # the same site with a kind 6 event open: not an attack event
                    self.ue0(0, 1, 6, "ef", ("U", 0, 1))
                    self.draw(("U", 1, 10), 1, SITE_DEF)
                    self.ue1(0, 1, ("U", 0, 1))
                self.ue0(1, 10, 0, "ef", ("U", 1, 10))
                if not sw.get("def_no_trigger"):
                    self.draw(("U", 0, 1), 2, SITE_DEF)
                    self.draw(("U", 1, 10), 1, SITE_OWN)
                self.ue1(1, 10, ("U", 1, 10))
            if f == start + 1:           # monster 11 and the player's seed are chained before the kill
                self.ue0(1, 11, 0, "ef", ("U", 1, 11))
                self.ue1(1, 11, ("U", 1, 11))
            # the rank-inverted control: a missile (rank 4) after the player's walk (rank 6) in the frame start+1
            if f == start + 1 and sw.get("rank_inverted"):
                self.ue0(3, 500, 2, "ef", ("U", 3, 500))
                self.ue1(3, 500, ("U", 3, 500))
            self.emit("FT1", dict(fr=f, gs=self.gs()))
        self.emit("WEND", dict(id=1, ok=1, why="", frames=frames, lines=self.n, hits={}, ghits={}, wall0=1.0, wall1=2.0, mono0=1.0,
                               mono1=2.0, fr=start + frames - 1))
        return self.L


def _verdict(lines, touch=None, passdraw=None):
    import os
    import tempfile
    d = tempfile.mkdtemp()
    p = os.path.join(d, "t.log")
    with open(p, "w") as f:
        f.write("# d2run seed=1\n" + "\n".join(lines) + "\n")
    ws, _o = fw.parse_log(p)
    w = ws[0]
    return fw.check_whole(w), check_chain2(w, SYN_TOUCH if touch is None else touch, SYN_PASS if passdraw is None else passdraw)


def drop_line(lines, pred, which=0):
    idx = [i for i, ln in enumerate(lines) if pred(ln)]
    return lines[:idx[which]] + lines[idx[which] + 1:]


def selftest2():
    """-> exit code. The clean log passes; each control fails exactly the test it is for."""
    out = []
    clean = Gen().build()
    whole, x = _verdict(clean)
    out.append(("clean: whole, 0 failures", not whole and not x["fails"], x["fails"][:2] or whole[:2]))

    def kinds(lines, **kw):
        whole, x = _verdict(lines, **kw)
        return whole, {f["kind"] for f in x["fails"]}

    def want(name, lines, kind, **kw):
        whole, ks = kinds(lines, **kw)
        out.append((name, not whole and ks == {kind}, "failures %s, whole %s" % (sorted(ks), whole[:1])))

    # 1 a step with no XS: one own draw of unit 10 lost its XS line
    base = Gen().build()
    j = [i for i, ln in enumerate(base) if ln.startswith("XS ") and json.loads(ln[3:])["site"] == SITE_OWN][0]
    want("1 a step with no XS fails arith", base[:j] + base[j + 1:], "arith")
    # 2 an extra XS: an XS whose step the seed did not take
    want("2 an extra XS fails arith", Gen(extra_xs=1).build(), "arith")
    # 3 a touch at an unlisted site (consistent chain)
    want("3 a touch at an unlisted site fails class", Gen(touch_unlisted=1).build(), "class")
    # 4 a listed site with no trigger (no KD)
    want("4 a listed site with no trigger fails trigger", Gen(no_kd=1).build(), "trigger")
    # 5 a kill's odd game-seed steps
    want("5 a kill's odd game-seed steps fail even", Gen(kill_game=3).build(), "even")
    # 6 a missile's first reading off by one
    want("6 a missile's first reading off by one fails first", Gen(first_off=1).build(), "first")
    # 7 an inverted rank
    want("7 an inverted rank fails rank", Gen(rank_inverted=1).build(), "rank")
    # 8 an inverted slot order
    want("8 an inverted slot order fails slot", Gen(slot_inverted=1).build(), "slot")
    # 9 a step with no pair open at an unlisted site
    want("9 a step with no pair open at an unlisted site fails nopair", Gen(pass_unlisted=1).build(), "nopair")
    # 10 a draw-free kind with an own step
    want("10 an own step in a kind 11 event fails free", Gen(free_draw=1).build(), "free")
    # 11 the defender trigger: the same listed site with no attack event open
    want("11 a defender site with no attack or missile event open fails trigger", Gen(def_no_trigger=1).build(), "trigger")
    # 12 a log with no XS: no touch is allowed and an own draw between readings is an exit, not a failure of the entries
    nox = [ln for ln in clean if not ln.startswith("XS ")]
    whole, x = _verdict(nox)
    out.append(("12 a log with no XS reads as rev 1 (no step logged)", not whole and x["has_xs"] is False, x["fails"][:2]))
    ok = True
    for name, passed, why in out:
        print("%s %s%s" % ("PASS" if passed else "FAIL", name, "" if passed else "  <- %s" % (why,)))
        ok &= bool(passed)
    return 0 if ok else 1
