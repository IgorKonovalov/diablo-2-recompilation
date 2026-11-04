#!/usr/bin/env python3
"""Plan 0054 Phase 2, the architect's review of `lane/p54` (run:2026-11-04-path): what the kept logs say that `tools/path.py check` does not print.

    PATH_IMAGE=<the pinned game.exe> PATH_DEV="<dev logs>" python3 -I tools/path_review.py LOG [LOG ...] > OUT

No game. Sections: the plans after a probe's write; the distinct natural spiral lists; the break control's cap and last hit; controls per path type,
with the model faults a control's exception hid; the type-1 controls on greedy-near's switch; the plans whose output needs the grid (the model on an
empty grid); the model on the tie's grid instead of the live one; the tie's first plans (bits, levels); the head tested backwards; the seed watchpoints;
type 11's client hits. It reads `tools/path.py` (revision in 2026-11-04-path-tools.sha256) and changes nothing it holds.
"""
import collections
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import path as PT  # noqa: E402

P3 = PT.P3


def base(p):
    return os.path.basename(p)[19:-4]


def main(paths):
    games = []
    for p in paths:
        for g in PT.parse(p):
            games.append((base(p), g))
    # ---- evaluate
    rows = []  # (session, game, plan, pred)
    for s, g in games:
        for plan in g.plans:
            if plan.plx is None:
                continue
            kind, pred = PT.evaluate(plan)
            rows.append((s, g, plan, pred if kind == "model" else None))
    types = sorted({r[2].ty for r in rows})

    print("1. PLANS AFTER A PROBE'S WRITE (ADR-0003)")
    first = {}
    for s, g, plan, pred in rows:
        if plan.pln.get("probe") and s not in first:
            first[s] = plan.k
    for s, k in sorted(first.items()):
        print("  %s first write at plan k=%d; plans from there on %d of %d" % (
            s, k, sum(1 for r in rows if r[0] == s and r[2].k >= k), sum(1 for r in rows if r[0] == s)))
    print("  type  all  stock(without the plans from the first write on)  stock-reached  without those two sessions")
    for t in types:
        a = [r for r in rows if r[2].ty == t]
        st = [r for r in a if not (r[0] in first and r[2].k >= first[r[0]])]
        no = [r for r in a if r[0] not in first]
        print("  %4d %5d %5d %5d %5d" % (t, len(a), len(st), sum(1 for r in st if r[3] is not None), len(no)))
    a = [r for r in rows if not (r[0] in first and r[2].k >= first[r[0]])]
    print("  total %d, stock %d, without the two sessions %d" % (len(rows), len(a), sum(1 for r in rows if r[0] not in first)))
    print()

    print("2. NATURAL SPIRAL PLANS")
    rel = collections.Counter()
    fr = collections.Counter()
    bys = collections.Counter()
    for s, g, plan, pred in rows:
        if plan.ty != 14 or plan.pln.get("probe"):
            continue
        rec = plan.pln["rec"]
        fr[(struct.unpack_from("<H", rec, 0)[0], struct.unpack_from("<H", rec, 4)[0])] += 1
        sx, sy = struct.unpack_from("<H", rec, 2)[0], struct.unpack_from("<H", rec, 6)[0]
        pts = struct.unpack_from("<%dI" % plan.plx["eax"], plan.plx["rec"], 0x9C)
        rel[tuple(((p & 0xFFFF) - sx, (p >> 16) - sy) for p in pts)] += 1
        bys[("after a write" if s in first else "stock session", s)] += 1
    print("  start fractions %s; distinct point lists relative to the start: %d; by session %s" % (dict(fr), len(rel), sorted(bys.items())))
    print()

    print("3. BREAK CONTROL (cap 100 per side per game) AND THE WINDOW")
    print("  session  last server control frame, last client control frame, last greedy PLC frame, last S3C frame, last PLN frame")
    for s, g in games:
        srv = [b["fr"] for b in g.brk if b["ctl"] and b["side"] == "srv"]
        cli = [b["fr"] for b in g.brk if b["ctl"] and b["side"] == "cli"]
        gr = [p.plc.get("fr", p.pln["fr"]) for p in g.plans if p.plc and p.plc["pl"] == 0x00679C80]
        print("  %-22s srv %3d@%5d cli %3d@%5d greedyPLC %5d s3c %5d plans-to %5d" % (
            s, len(srv), max(srv or [0]), len(cli), max(cli or [0]), max(gr or [0]), max([x["fr"] for x in g.s3c] or [0]), max(p.pln["fr"] for p in g.plans)))
    srv = sum(max([b["fr"] for b in g.brk if b["ctl"] and b["side"] == "srv"] or [0]) for s, g in games)
    cli = sum(max([b["fr"] for b in g.brk if b["ctl"] and b["side"] == "cli"] or [0]) for s, g in games)
    end = sum(max(p.pln["fr"] for p in g.plans) for s, g in games)
    print("  frames to the last plan, all sessions %d; to the server control's last line %d; to the client control's %d" % (end, srv, cli))
    ra = collections.Counter()
    for s, g in games:
        for b in g.brk:
            if not b["ctl"]:
                ra[(s, "%08x" % b["fn"], b["side"], b["ty"], "%08x" % b["ra"], "%08x" % (b["pra"] or 0))] += 1
    print("  watched hits (session, fn, side, path type, ra, pra): %s" % sorted(ra.items()))
    print()

    print("4. CONTROLS PER PATH TYPE (separating, of which the control's model raised, passed)")
    tab = collections.defaultdict(lambda: [0, 0, 0])
    for s, g, plan, pred in rows:
        if pred is None:
            continue
        fam = PT.control_family(plan)
        names = list(PT.CONTROLS.get(fam, ()))
        for neg in names:
            k = (plan.ty, fam, neg)
            e = tab[k]
            try:
                _, p = PT.evaluate(plan, neg)
            except Exception:
                e[0] += 1
                e[1] += 1
                continue
            if PT.pred_key(p) != PT.pred_key(pred):
                e[0] += 1
                if not PT.compare(plan, p):
                    e[2] += 1
    for k, e in sorted(tab.items()):
        print("  type %2d %-7s %-8s %5d %5d %d" % (k[0], k[1], k[2], e[0], e[1], e[2]))
    print("  type-1 controls on greedy-near's switch (never run by the check: its family is `near`)")
    t1 = [r for r in rows if r[3] is not None and r[3]["label"] == "near:type1"]
    print("  plans through the switch: %d; returns %s" % (len(t1), sorted(collections.Counter(min(r[3]["eax"], 6) for r in t1).items())))
    for neg in PT.CONTROLS["type1"]:
        sep = rais = ps = 0
        for s, g, plan, pred in t1:
            try:
                _, p = PT.evaluate(plan, neg)
            except Exception:
                sep += 1
                rais += 1
                continue
            if PT.pred_key(p) != PT.pred_key(pred):
                sep += 1
                if not PT.compare(plan, p):
                    ps += 1
        print("  near:type1 %-8s %5d %5d %d" % (neg, sep, rais, ps))
    print()

    print("5. PLANS WHOSE OUTPUT NEEDS THE GRID (the model on the same rooms with every cell 0)")
    orig_world = PT.mk_world

    def empty(plan):
        R = orig_world(plan)
        for r in R.values():
            r.c = [0] * len(r.c)
        return R
    PT.mk_world = empty
    ng = collections.Counter()
    nt = collections.Counter()
    for s, g, plan, pred in rows:
        if pred is None or not plan.plc:
            continue
        nt[plan.ty] += 1
        try:
            p = PT.predict_planner(plan)
            if PT.pred_key(p) != PT.pred_key(pred):
                ng[plan.ty] += 1
        except PT.Unmodelled:
            ng[plan.ty] += 1
    PT.mk_world = orig_world
    for t in sorted(nt):
        print("  type %2d planner plans %5d, output differs on an empty grid %5d" % (t, nt[t], ng[t]))
    print("  types 4, 10, 14: straight, the model reads no grid")
    print()

    print("6. THE MODEL ON THE TIE'S GRID (built map + marks) INSTEAD OF THE LIVE CELLS: plans whose return, points or seed then differ from the game's")
    for corpse in (False, True):
        c = collections.Counter()
        d = collections.Counter()
        win = comp = clean = 0
        for s, g, plan, pred in rows:
            if pred is None or not plan.plc:
                continue
            t = PT.tie_of(plan, True, corpse)
            c[plan.ty] += 1
            win += len(plan.rooms)
            if not t or not t.get("compared"):
                continue
            comp += t["compared"]
            R = orig_world(plan)
            flips = []
            for a, x, y, pv, lv in t["diff"]:
                r = R[a]
                flips.append((a, (y - r.y0) * r.w + (x - r.x0), pv))
            if not flips:
                clean += 1
                continue
            try:
                p = PT.predict_planner(plan, None, flips)
                if PT.compare(plan, p):
                    d[plan.ty] += 1
            except PT.Unmodelled:
                d[plan.ty] += 1
        print("  [%s] window rooms %d, rooms with a built map %d, plans with no differing cell %d" % ("corpse reading" if corpse else "units' own marks", win, comp, clean))
        for t in sorted(c):
            print("    type %2d plans %5d, wrong on the tie's grid %5d" % (t, c[t], d[t]))
        print("    all: %d of %d" % (sum(d.values()), sum(c.values())))
    print()

    print("7. THE TIE'S FIRST 10 PLANS OF EACH GAME: where, and which bits (not printed by the check)")
    lev = collections.Counter()
    ty = collections.Counter()
    bits = collections.Counter()
    sense = collections.Counter()
    units = collections.Counter()
    for s, g in games:
        k = 0
        for plan in g.plans:
            if not plan.plc:
                continue
            k += 1
            if k > 10:
                break
            lev[plan.pln["ar"]] += 1
            ty[plan.ty] += 1
            for u in plan.plc["u"]:
                units[u[0]] += 1
            t = PT.tie_of(plan, True, False)
            for a, x, y, pv, lv in t["diff"]:
                bits[pv ^ lv] += 1
                sense["model has it, live lacks it" if pv & (pv ^ lv) else "live has it, model lacks it"] += 1
    print("  levels %s; path types %s; unit-list entries by unit type %s" % (sorted(lev.items(), key=str), sorted(ty.items()), sorted(units.items())))
    print("  xor values %s; %s" % (sorted(bits.items()), sorted(sense.items())))
    print()

    print("8. THE HEAD, BACKWARDS: plans that reached a planner, tested with the record-only refusal reasons of path.py")
    rv = collections.Counter()
    ctx = collections.Counter()
    for s, g, plan, pred in rows:
        if not plan.plc:
            continue
        rv[str(PT.refusal_reason(plan))] += 1
        rec = plan.pln["rec"]
        c = plan.plc["ctx"]
        ctx["ctx start = record start" if struct.unpack_from("<HH", c, 0) == (struct.unpack_from("<H", rec, 2)[0], struct.unpack_from("<H", rec, 6)[0]) else "ctx start differs"] += 1
    print("  %s; %s" % (sorted(rv.items()), sorted(ctx.items())))
    print()

    print("9. SEED WATCHPOINTS")
    cl = collections.Counter()
    w = collections.Counter()
    for s, g, plan, pred in rows:
        if plan.ty == 10:
            cl[(plan.pln["u"][1])] += 1
    print("  type-10 plans by missile class: %s" % sorted(cl.items()))
    print("  type-10 plans by session: %s" % sorted(collections.Counter(r[0] for r in rows if r[2].ty == 10).items()))
    A, = (0x6AC690C5,)
    for s, g in games:
        byk = {p.k: p for p in g.plans}
        for e in g.seedw:
            lo, hi = PT.seed_of(e["from"])
            l2, h2 = PT.seed_of(e["to"])
            full = lo * A + hi
            pl = byk.get(e["k"])
            step = l2 == full & 0xFFFFFFFF
            w[(s, "ctl" if e.get("ctl") else "ty10", "lcg" if step else "other", "hi same" if h2 == hi else "hi moved", "lo 0" if l2 == 0 else "lo not 0")] += 1
            if e.get("ctl"):
                print("  ctl k=%d class=%s fr %d->%d from %s to %s pc %08x lcg=%d hi-after-step=%d st0=%08x" % (
                    e["k"], pl.pln["u"][1] if pl else "?", pl.pln["fr"] if pl else -1, e["fr"], e["from"], e["to"], e["pc"], step, h2 == (full >> 32) & 0xFFFFFFFF, e["st"][0]))
    for k, n in sorted(w.items()):
        print("  %s: %d" % (k, n))
    pcs = collections.Counter("%08x" % e["pc"] for s, g in games for e in g.seedw if not e.get("ctl"))
    print("  type-10 pcs: %s" % sorted(pcs.items()))
    print()

    print("10. RETURN 0 AFTER A PLANNER: the planner's own 0, or the tail's refusal")
    z = collections.Counter()
    for s, g, plan, pred in rows:
        if pred is not None and pred["eax"] == 0:
            z[(plan.ty, "planner 0" if pred.get("n") == 0 else "tail")] += 1
    print("  %s" % sorted(z.items()))
    print()
    print("11. THE UNIT LIST: keys of PLC %s; entries at the cap (120): %d; a field for the marked state: none named by tools/gdb/path.py" % (
        sorted(k for k in rows[0][2].plc) if rows[0][2].plc else [], sum(1 for r in rows if r[2].plc and len(r[2].plc["u"]) >= 120)))

    print("12. THE WRONG PLANS OF SECTION 6, BY THE BIT THAT MAKES THEM WRONG (each bit's differences alone on the live grid; corpse reading on)")
    bit = collections.Counter()
    wrong = 0
    for s, g, plan, pred in rows:
        if pred is None or not plan.plc:
            continue
        t = PT.tie_of(plan, True, True)
        if not t or not t.get("compared") or not t["diff"]:
            continue
        R = orig_world(plan)
        fl = [(a, (y - R[a].y0) * R[a].w + (x - R[a].x0), pv, lv) for a, x, y, pv, lv in t["diff"]]

        def bad(fs):
            try:
                return bool(PT.compare(plan, PT.predict_planner(plan, None, fs)))
            except PT.Unmodelled:
                return True
        if not bad([(a, i, pv) for a, i, pv, lv in fl]):
            continue
        wrong += 1
        hit = []
        for b in (0x2, 0x4, 0x40, 0x80, 0x100, 0x200, 0x400, 0x800, 0x1000, 0x2000, 0x8000):
            fs = [(a, i, (lv & ~b) | (pv & b)) for a, i, pv, lv in fl if (pv ^ lv) & b]
            if fs and bad(fs):
                hit.append(b)
        bit[tuple("0x%04x" % b for b in hit) or ("only together",)] += 1
    print("  wrong plans %d; alone-sufficient bits: %s" % (wrong, sorted(bit.items(), key=lambda kv: -kv[1])))
    print()

    print("13. CORPSES IN THE LIVE CELLS: each distinct mode-12 monster (id, x, y) of the unit lists, the 0x8000 cells of its 3 x 3")
    corpses("kept logs", games)
    dev = [(base(p), g) for p in os.environ.get("PATH_DEV", "").split() for g in PT.parse(p)]
    if dev:
        corpses("development logs dev2..dev5", dev)
    print()

    print("14. THE TIE'S FIRST-PLAN 0x400 CELLS BY OBJECT: objects of the unit list whose rectangle holds a differing cell (class, door, +0x167, +0x1B6)")
    ob = collections.Counter()
    for s, g in games:
        k = 0
        for plan in g.plans:
            if not plan.plc:
                continue
            k += 1
            if k > 10:
                break
            t = PT.tie_of(plan, True, False)
            cells = {(x, y) for a, x, y, pv, lv in t["diff"]}
            for u in plan.plc["u"]:
                if u[0] == 2 and len(u) >= 13:
                    x, y, sx, sy = u[3], u[4], u[7], u[8]
                    l, tp = x - (sx >> 1), y - (sy >> 1)
                    if any((xx, yy) in cells for yy in range(tp, tp + sy) for xx in range(l, l + sx)):
                        ob[(u[2], u[9], "0x%02x" % u[11], u[12])] += 1
    print("  %s" % sorted(ob.items()))
    print()

    print("15. WHICH CLASSES THE SEED WATCHPOINTS COVERED, AND THE FRAMES TO THE WRITE")
    wc = collections.Counter()
    for s, g in games:
        byk = {p.k: p for p in g.plans}
        for e in g.seedw:
            if not e.get("ctl"):
                wc[byk[e["k"]].pln["u"][1]] += 1
    print("  watched type-10 classes: %s" % sorted(wc.items()))
    print()

    print("16. THE SPIRAL'S PRODUCTS: iterations of a natural plan whose stored FISTP integer differs under truncation and rounding (image table, r += 0x2580, angle += 16)")
    print("  %s (env PATH_IMAGE: the pinned image)" % spiral_products())


def corpses(name, games):
    shape = collections.Counter()
    classes = collections.Counter()
    for s, g in games:
        seen = set()
        for plan in g.plans:
            if not plan.plc:
                continue
            R = PT.mk_world(plan)
            for u in plan.plc["u"]:
                if u[0] != 1 or u[3] != 12 or u[6] not in R:
                    continue
                key = (u[1], u[4], u[5])
                if key in seen:
                    continue
                seen.add(key)
                on = set()
                for dy in (-1, 0, 1):
                    for dx in (-1, 0, 1):
                        r = PT.P2.room_at(R, u[6], u[4] + dx, u[5] + dy)
                        if r is not None and r.cell(u[4] + dx, u[5] + dy) & 0x8000:
                            on.add((dx, dy))
                sh = "3x3" if len(on) == 9 else ("plus" if on == {(0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)} else ("none" if not on else "other %d" % len(on)))
                shape[(sh, "mask 0x%x" % u[9], "pattern %d" % u[8])] += 1
                classes[(sh, u[2])] += 1
    print("  [%s] %s" % (name, sorted(shape.items(), key=lambda kv: -kv[1])))
    print("  [%s] not 3x3, by class: %s; distinct classes 3x3: %d" % (name, [kv for kv in sorted(classes.items()) if kv[0][0] != "3x3"], sum(1 for k in classes if k[0] == "3x3")))


def spiral_products():
    img = os.environ.get("PATH_IMAGE")
    if not img:
        return "PATH_IMAGE not set"
    b = open(img, "rb").read()
    pe = struct.unpack_from("<I", b, 0x3C)[0]
    nsec, opt = struct.unpack_from("<H", b, pe + 6)[0], struct.unpack_from("<H", b, pe + 20)[0]
    va = 0x00707800 - 0x400000
    off = None
    for i in range(nsec):
        o = pe + 24 + opt + 40 * i
        vs, vaddr, rs, rp = struct.unpack_from("<4I", b, o + 8)
        if vaddr <= va < vaddr + rs:
            off = rp + va - vaddr
    tab = struct.unpack_from("<512f", b, off)
    r = ang = 0
    diff = tot = 0
    for it in range(1, 95):
        r += 0x2580
        ang += 16
        f = float(r)
        for v in (tab[(ang + 0x80) & 0x1FF] * f, tab[ang & 0x1FF] * f):
            tot += 1
            if int(round(v)) != int(v):
                diff += 1
    return "%d of %d products in the 94 iterations" % (diff, tot)


if __name__ == "__main__":
    main(sys.argv[1:])
