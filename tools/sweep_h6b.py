#!/usr/bin/env python3
"""Checker for plan 0038 batch H6b (sockets): the lines of tools/gdb/h6b.py against the readings of
docs/findings/items/0007-sockets-runewords.md. tools/sockets.py check reproduces the inserts, transfers, matches,
runewords and client verdicts of the same logs (the plan 0029 model); this checker adds what it does not read.

Usage:
  python3 -I tools/sweep_h6b.py logs [--excel DIR] <log> [<log> ...]
  python3 -I tools/sweep_h6b.py static <game.exe> [--excel DIR]   objdump call sites and the data checks

logs, per insert (INS0 ... INSX of tools/gdb/sockets.py, HI0 ... HIX of h6b.py, the same thread):
  xy       XY: the pushed x equals the inventory count at the call and the parent's children before the insert
           (PA kids); XYY y = 0; XYB body location = -1
  cursor   CUR: p5 equals INS0's fifth word; the player word; the cursor slot (inventory +0x20) at the p5 test and
           after it (CURX)
  link     SLO/SLB: the owner is the parent, the child is the inserted child, the branch taken
  timers   RPE/RPV/RPS inside an insert: the 252 and 253 timers run after RUNEWORD_Apply exactly when the match gave a
           row the gate lets through (MX row, the Runes server column, the ladder word); RPV = the parent's stat
           (base list plus every list; 252 and 253); an RPS frame = the game frame + trunc(2500 / v) + 1
  reader   RDS: the 16 bits the reader stores at ItemData+0x38; at a later reader insert into that item, PA's rw
           field holds it
  client   UIS: the steps in the code's order, the first failing step ends the test (its return site), the result;
           ItemBaseHasInv = the base's hasinv, ItemMaxSockets = min(gemsockets, MaxSock1/25/40 by ilvl), the count and
           socket steps = UIC's inventory count and stat 194 (low byte);
           UIR: the client copy's rw field beside the server's (RDS) for the same class
  copy     CPY (ItemCopy) with its return site and second argument; the inserts it makes (INS0 return 0x0055A421)
           and their option words
Exit 0 only when every check holds. Stdlib only. Read-only.
"""
import argparse
import collections
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import props  # noqa: E402
import sockets  # noqa: E402
import tbl  # noqa: E402

STR = tbl.Strings(os.path.join(os.path.dirname(HERE), "workspace", "merged", "data", "local", "lng", "eng"))

UIS_ORDER = ["ui", "filler", "socketed", "hasinv", "maxsockets", "identified", "broken", "inventory", "count",
             "sockets"]
RET_INSERT_COPY = 0x0055A421       # after ItemCopy's insert call 0x0055A41C
RET_READER = 0x0053135A            # after ITEMS_ReadInventoryList's socketed-child reader call 0x00531355
RET_PACKET = 0x0054B6E0            # after SOCK_PacketInsert's call 0x0054B6DB
COPY_RETS = {0x0057A538: "NPC_MenuAction 0x0057A533", 0x0057A329: "NPC_MenuAction 0x0057A324",
             0x0057974C: "NPC_SellItem 0x00579747", 0x00577C7F: "NPC_BuyItem 0x00577C7A"}


class Bad(Exception):
    pass


def jl(line):
    tag, _, rest = line.rstrip("\n").partition(" ")
    if not rest.startswith("{"):
        return tag, None
    try:
        return tag, json.loads(rest)
    except ValueError:
        return tag, None


def statsum(u, stat):
    """UnitGetStat(u, stat, 0) from a logged UNIT: the base list plus every sub list (props.py's lists)."""
    v = 0
    for s, p, x in (u.get("b") or []):
        if s == stat and p == 0:
            v += x
    for st, fl, ent, _ in (u.get("sub") or []):
        for s, p, x in ent:
            if s == stat and p == 0:
                v += x
    return v


def cmd_logs(ns):
    T = sockets.Tables(ns.excel)
    S = collections.Counter()
    notes = collections.defaultdict(list)
    bad = []
    rds_by_item = {}
    rds_list = []
    server_units = collections.defaultdict(set)
    for path in ns.logs:
        name = os.path.basename(path)
        cur = {}            # thread -> the open insert
        last_uic = None
        for ln, line in enumerate(open(path, errors="replace"), 1):
            tag, d = jl(line)
            if tag == "LOGERR" or line.startswith("LOGERR"):
                bad.append("%s:%d %s" % (name, ln, line.strip()))
                continue
            if d is None:
                continue
            th = d.get("th", 0)
            try:
                if tag == "INS0":
                    cur[th] = {"ins": d, "ev": []}
                    continue
                if tag == "RDS":
                    rds_by_item[(name, d["item"])] = d["v"]
                    rows_ = [R["ename"] for R in (T.rune(i) for i in range(len(T.runes)))
                             if R["complete"] and STR.index(R["name"]) == d["v"]]
                    if not rows_:
                        raise Bad("RDS 0x%04X is the Name index of no complete runes row" % d["v"])
                    rds_list.append((name, d, rows_))
                    continue
                if tag == "CPY":
                    site = COPY_RETS.get(d["ret"], "0x%08X" % d["ret"])
                    S["ItemCopy calls, second argument %d" % d["a2"]] += 1
                    notes["ItemCopy"].append("%s: from %s, class %s, a2 %d, children %s" % (
                        name, site, d["cls"], d["a2"], d["kids"]))
                    continue
                if tag == "UIC":
                    last_uic = d
                    continue
                if tag == "UIS":
                    # sockets.py's UIC breakpoint at the same return fires first; an unchanged UIC tuple is not
                    # written again, so the latest UIC holds the same inputs
                    if last_uic is None:
                        raise Bad("a UIS line before any UIC line")
                    check_uis(T, d, last_uic, S, notes, name)
                    continue
                if tag == "UIR":
                    S["client copies seen (UIR)"] += 1
                    if d["rw"]:
                        notes["UIR (client copy with a runeword field)"].append(
                            "%s: target class %d, flags %08X, rw 0x%04X, children %s" % (
                                name, d["tgt"], d["fl"], d["rw"], d["kids"]))
                        S["client copy rw field non-zero"] += 1
                    continue
                if tag == "RPE" and not d["ins"]:
                    S["timers outside an insert (RPE): %s" % ("at the load, frame 1" if d["frame"] == 1 else
                                                                "later")] += 1
                if th not in cur:
                    continue
                c = cur[th]
                c["ev"].append((tag, d))
                if tag in ("CH", "PA") and d:
                    server_units[name].add(d["u"])
                if tag == "INSX":
                    del cur[th]
                    check_insert(T, c["ins"], c["ev"], d, S, notes, name, rds_by_item)
            except (Bad, KeyError, TypeError) as e:
                bad.append("%s:%d %s: %s" % (name, ln, tag, e))
    for name, d, rows_ in rds_list:
        who = "a server insert's parent" if d["item"] in server_units[name] else "no server insert unit (client copy)"
        S["reader runeword store: the Name index of the row (%s)" % who] += 1
        notes["RDS"].append("%s: unit %d class %d (%s), ItemData+0x38 <- 0x%04X = Name index of %s" % (
            name, d["item"], d["cls"], who, d["v"], "/".join(rows_)))
    for k in sorted(S):
        print("%-72s %6d" % (k, S[k]))
    for k in sorted(notes):
        print("-- %s (%d)" % (k, len(notes[k])))
        for n in notes[k]:
            print("   " + n)
    for b in bad:
        print("BAD " + b)
    print("SUMMARY logs=%d checks=%d bad=%d" % (len(ns.logs), sum(S.values()), len(bad)))
    return 1 if bad else 0


def path_of(ins):
    return {RET_PACKET: "packet", RET_READER: "reader", RET_INSERT_COPY: "copier"}.get(ins["ret"],
                                                                                       "0x%08X" % ins["ret"])


def check_insert(T, ins, ev, x, S, notes, name, rds_by_item):
    get = collections.defaultdict(list)
    for t, d in ev:
        get[t].append(d)
    path = path_of(ins)
    pa = get["PA"][0] if get["PA"] else None
    ch = get["CH"][0] if get["CH"] else None
    ok = x["ret"] == 1
    if not ok:
        for t in ("XY", "CUR", "SLO", "RPE"):
            if get[t]:
                raise Bad("a refused insert logged %s" % t)
        S["refused inserts (no XY, CUR, SLO, RPE)"] += 1
        return
    # xy
    if len(get["XY"]) != 1 or len(get["XYY"]) != 1 or len(get["XYB"]) != 1:
        raise Bad("XY/XYY/XYB count %d/%d/%d" % (len(get["XY"]), len(get["XYY"]), len(get["XYB"])))
    xy, yy, bb = get["XY"][0], get["XYY"][0], get["XYB"][0]
    nk = len(pa["kids"] or [])
    if xy["item"] != ch["u"] or yy["item"] != ch["u"] or bb["item"] != ch["u"]:
        raise Bad("x/y/body item is not the child")
    if xy["x"] != xy["count"] or xy["x"] != nk:
        raise Bad("x %d, count %d, children before %d" % (xy["x"], xy["count"], nk))
    if yy["y"] != 0 or bb["body"] != -1:
        raise Bad("y %d, body %d" % (yy["y"], bb["body"]))
    S["xy: x = count before = children before; y 0; body -1 (%s)" % path] += 1
    S["xy: x values %s" % ("> 0" if xy["x"] > 0 else "0")] += 1
    # cursor
    if len(get["CUR"]) != 1 or len(get["CURX"]) != 1:
        raise Bad("CUR/CURX count")
    cu, cx = get["CUR"][0], get["CURX"][0]
    if cu["p5"] != ins["p"][1]:
        raise Bad("p5 %d, INS0 %r" % (cu["p5"], ins["p"]))
    if cu["player"] != ins["player"]:
        raise Bad("CUR player %d, INS0 %d" % (cu["player"], ins["player"]))
    who = "player" if ins["player"] and ins["player"] != pa["u"] else "the parent" if ins["player"] == pa["u"] else "none"
    S["cursor: %s, p5 %d, %s; cursor at the p5 test %s, after %s" % (
        path, cu["p5"], who, "empty" if not cu["cursor"] else "the child" if cu["cursor"] == ch["u"] else "other",
        "empty" if not cx["cursor"] else "the child" if cx["cursor"] == ch["u"] else "other")] += 1
    # link
    if len(get["SLO"]) != 1 or len(get["SLB"]) != 1:
        raise Bad("SLO/SLB count %d/%d" % (len(get["SLO"]), len(get["SLB"])))
    so, sb = get["SLO"][0], get["SLB"][0]
    if so["owner"] != pa["u"] or so["child"] != ch["u"]:
        raise Bad("SLO owner/child")
    S["link: %s parent mode %d, list owner %s before, branch %s" % (
        path, pa["mode"], "the parent" if so["lowner"] == pa["u"] else "0" if not so["lowner"] else "other",
        sb["b"])] += 1
    if ch["fl"] & 0x100:
        S["link: child with flag 0x100"] += 1
    # the gate and the timers
    mx = get["MX"][0]["row"] if get["MX"] else -1
    gate = mx >= 0 and not (T.rune(mx)["server"] and not ins["ladder"])
    rpe = [d for d in get["RPE"] if d["ins"]]
    if gate != bool(rpe):
        raise Bad("timers: gate %s, RPE lines %d (row %d)" % (gate, len(rpe), mx))
    if gate:
        if [d["stat"] for d in rpe] != [252, 253]:
            raise Bad("timer order %r" % [d["stat"] for d in rpe])
        rwx = get["RWX"][-1] if get["RWX"] else None
        if rwx is None:
            raise Bad("a gated row without RWX")
        rpv = get["RPV"]
        rps = get["RPS"]
        for stat in (252, 253):
            v = [d["v"] for d in rpv if d["stat"] == stat]
            want = statsum(rwx, stat)
            if v != [want]:
                raise Bad("RPV %d: %r, the parent's stat at RWX %d" % (stat, v, want))
            sched = [d for d in rps if d["stat"] == stat]
            fr = [d["frame"] for d in rpe if d["stat"] == stat][0]
            if want:
                if len(sched) != 1:
                    raise Bad("stat %d = %d but %d schedules" % (stat, want, len(sched)))
                at = fr + int(2500 / want) + 1
                if sched[0]["at"] != at or sched[0]["type"] != 3 or sched[0]["v"] != want:
                    raise Bad("stat %d schedule %r, model at %d type 3" % (stat, sched[0], at))
                S["timers: stat %d = %d, scheduled at frame + 2500/v + 1 (%s)" % (stat, want, T.rune(mx)["ename"])] += 1
                notes["timer schedules"].append("%s: %s stat %d v %d frame %d -> event type 3 at %d" % (
                    name, T.rune(mx)["ename"], stat, want, fr, at))
            else:
                if sched:
                    raise Bad("stat %d = 0 but scheduled" % stat)
                S["timers: stat %d = 0, nothing scheduled" % stat] += 1
    S["timers: called iff the gate passed (%s, %s)" % (path, "gate" if gate else "no gate")] += 1
    # the reader's runeword field
    if path == "reader" and pa["fl"] & 0x4000000:
        v = rds_by_item.get((name, pa["u"]))
        if v is None or v != pa["rw"]:
            raise Bad("reader insert into a runeword parent: RDS %r, PA rw %r" % (v, pa["rw"]))
        S["reader: PA rw = the RDS store (runeword parent)"] += 1
    if path == "copier":
        S["copier inserts, options %s" % ins["p"]] += 1
        S["copier: parent mode %d (p6 %d)" % (pa["mode"], ins["p"][2])] += 1
    S["inserts checked (%s)" % path] += 1


def uis_verdict(steps):
    """The client test from its logged steps: the result and the name of the first failing test (or ok)."""
    names = [s[0] for s in steps]
    expect = UIS_ORDER[:len(names)]
    if names != expect:
        raise Bad("UIS steps %r not in the code's order" % names)
    vals = dict((s[0], s[1]) for s in steps)
    for n in names:
        v = vals[n]
        if n == "ui" and v in (10, 11):
            return 0, n
        if n in ("filler", "socketed", "hasinv", "maxsockets", "identified", "inventory") and not v:
            return 0, n
        if n == "broken" and v:
            return 0, n
    if "sockets" in vals:
        return (1 if vals["count"] < vals["sockets"] else 0), "count < sockets"
    raise Bad("UIS ended early with every step passing: %r" % steps)


def check_uis(T, u, uic, S, notes, name):
    r, why = uis_verdict(u["steps"])
    if r != u["r"]:
        raise Bad("UIS result %d, steps give %d (%s)" % (u["r"], r, why))
    last = u["steps"][-1][0]
    if why not in (last, "count < sockets"):
        raise Bad("UIS: failing step %s is not the last step %s" % (why, last))
    m_r, m_why = sockets.client_test(T, uic)
    if m_r != r:
        raise Bad("UIS %d, the UIC model %d" % (r, m_r))
    vals = dict((a, b) for a, b in u["steps"])
    tc = uic["tgt"]["cls"]
    S["client steps: UI word %d" % vals["ui"]] += 1
    if "inventory" in vals:
        S["client steps: inventory step reached, %s" % ("non-zero" if vals["inventory"] else "0")] += 1
    if "hasinv" in vals:
        if bool(vals["hasinv"]) != bool(T.base(tc)["hasinv"]):
            raise Bad("ItemBaseHasInv %r, table hasinv %r" % (vals["hasinv"], T.base(tc)["hasinv"]))
        S["client steps: ItemBaseHasInv = the base's hasinv (%d)" % T.base(tc)["hasinv"]] += 1
    if "maxsockets" in vals:
        m = T.max_sockets(tc, uic["tgt"]["ilvl"])
        if vals["maxsockets"] != m:
            raise Bad("ItemMaxSockets %r, F5 model %r" % (vals["maxsockets"], m))
        S["client steps: ItemMaxSockets = min(gemsockets, MaxSock by ilvl)"] += 1
    if "sockets" in vals and vals["sockets"] != uic["tgt"]["s194"] & 0xFF:
        raise Bad("sockets step %r, stat 194 %r" % (vals["sockets"], uic["tgt"]["s194"]))
    if "count" in vals and vals["count"] != uic["tgt"]["ninv"]:
        raise Bad("count step %r, inventory count %r" % (vals["count"], uic["tgt"]["ninv"]))
    code = T.base(uic["tgt"]["cls"])["code"] if uic.get("tgt") else "?"
    S["client steps: %s at %s (r %d)" % (why, "0x%08X" % u["ret"], r)] += 1
    notes["client steps"].append("%s: target %s flags %08X: %s -> %d (%s; UIC model: %s)" % (
        name, code, uic["tgt"]["fl"], " ".join("%s=%s" % (a, b) for a, b in u["steps"]), r, why, m_why))


# ------------------------------------------------------------------------------------------------ static

def objdump(exe, start, stop):
    out = subprocess.run(["objdump", "-d", "-M", "intel", "--start-address=0x%x" % start, "--stop-address=0x%x" % stop,
                          exe], capture_output=True, text=True, check=True).stdout
    rows = []
    for ln in out.splitlines():
        m = re.match(r"\s+([0-9a-f]+):\t([0-9a-f ]+)\t(.*)", ln)
        if m:
            rows.append((int(m.group(1), 16), m.group(3).strip()))
    return rows


def cmd_static(ns):
    T = sockets.Tables(ns.excel)
    rows = objdump(ns.exe, 0x401000, 0x6B0000)
    print("== ItemCopy 0x0055A2A0 direct calls, with the two pushes before each (arg1, arg2)")
    n = 0
    for i, (a, ins) in enumerate(rows):
        if ins in ("call   0x55a2a0",):
            pushes = [x for _, x in rows[max(0, i - 6):i] if x.startswith("push")]
            print("  0x%08X  %s" % (a, " | ".join(pushes[-2:])))
            n += 1
    print("  %d calls" % n)
    for tgt, what in ((0x563350, "0x00563350 (re-inserting copies of a parent's children)"),
                      (0x489360, "0x00489360 (writes UI word 10 or 11)"), (0x562660, "ITEMS_InsertSocket")):
        sites = [(a, ins) for a, ins in rows if ins in ("call   0x%x" % tgt, "jmp    0x%x" % tgt)]
        print("== %s: %d direct calls or jumps" % (what, len(sites)))
        for a, ins in sites:
            print("  0x%08X  %s" % (a, ins))
    w = [(a, ins) for a, ins in rows if re.match(r"mov\s+(DWORD PTR )?ds:0x7bcbf0,", ins)]
    print("== stores to the UI word 0x007BCBF0: %d" % len(w))
    for a, ins in w:
        print("  0x%08X  %s" % (a, ins))
    print("== data: socket fillers (ItemTypes 53 sock) and durability")
    nf = nd = 0
    for c in range(len(T.items)):
        if T.is_type(c, sockets.SOCK):
            nf += 1
            b = T.base(c)
            if b["dur"] and not b["nodur"]:
                nd += 1
                print("  durability: %s" % b["code"])
    print("  %d socket-filler rows, %d with durability" % (nf, nd))
    print("== data: misc.txt levelreq of the runes (r01..r33)")
    import csv
    with open(os.path.join(ns.excel, "misc.txt"), newline="", encoding="latin-1") as fh:
        lv = {r["code"]: r["levelreq"] for r in csv.DictReader(fh, delimiter="\t")}
    print("  " + " ".join("%s:%s" % ("r%02d" % k, lv.get("r%02d" % k)) for k in range(1, 34)))
    print("== data: complete runes rows whose lines reach funcs 17 (par 0, min != max), 20, 24; their server column")
    for i in range(len(T.runes)):
        R = T.rune(i)
        if not R["complete"]:
            continue
        hits = []
        for b in R["t1"]:
            code, par, mn, mx = b
            if code < 0 or code >= len(T.props):
                continue
            fs = T.props[code]["func"]
            if 20 in fs:
                hits.append("20")
            if 24 in fs:
                hits.append("24")
            if 17 in fs and par == 0:
                hits.append("17 par 0%s" % (" ranged" if mn != mx else " min = max"))
        if hits:
            print("  row %3d %-12s server %d: %s" % (i, R["ename"], R["server"], ", ".join(sorted(set(hits)))))
    return 0


def main(argv):
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("logs")
    a.add_argument("logs", nargs="+")
    a.add_argument("--excel", default=props.EXCEL)
    b = sub.add_parser("static")
    b.add_argument("exe")
    b.add_argument("--excel", default=props.EXCEL)
    ns = ap.parse_args(argv)
    return cmd_logs(ns) if ns.cmd == "logs" else cmd_static(ns)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
