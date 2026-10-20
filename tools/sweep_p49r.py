#!/usr/bin/env python3
"""Plan 0049 Phase 1 (`lane/p49r`): the static readings of the backlog sweep, over the pinned Game.exe and the
stock excel tables. No game, no slot.

    python3 -I tools/sweep_p49r.py tables     image tables read by the readings (P1c (a), (b), (c), (e))
    python3 -I tools/sweep_p49r.py excel      the stock rows those tables are indexed by
    python3 -I tools/sweep_p49r.py qsites     the 45 QUESTRECORD_SetState/ClearState sites with a register word or bit,
                                              and the callers of the steps clear 0x0065C3E0 (S2c static leftovers)

`tables` prints, each block headed by a `#` line:
  - `g_StatEventFuncs` (0x007325B0, bound 0x31 at 0x0056E746): `E <index> <handler>`;
  - the missile server do-function table (0x0073C768, indexed by the record's `pSrvDoFunc`, `movsx eax, WORD PTR [ebx+0xc]` at
    0x005ADC97) and the Missiles field descriptor entries for pCltDoFunc..pSrvDmgFunc (name, record offset);
  - the bone-prison formation descriptor 0x0073D4F0 ({count, ?, flags} then {dx, dy, kind} entries) and the
    FormationSpawn kind table 0x005B34A4;
  - every `mov DWORD PTR ds:0x7795ec, <value>` in .text, with its function, and the front-end button records whose
    callback writes it (string id, callback).
`excel` prints the ItemStatCost rows with itemeventfunc 31, the Missiles rows with pSrvDoFunc 13 and 36, the Skills rows
that name `bonewallmaker`, and the stock carriers of the property whose stat is item_reanimate.
`qsites` prints, per site, `Q <site> <set|clear> word=<operand> bit=<operand> fn=<entry>` and the quest objects whose
init-stored callbacks reach the site's function by direct calls (`objects=<id:word ...>`, the word being what that
object's init stores at Quest+0xE0); the range-clear callers as `R <site> word=<operand> fn=<entry> objects=...`.
A register operand is printed as the instruction text that last loaded it in the window before the call.

Stdlib only, plus the objdump binary (through tools/sweep_s4b.py and tools/sweep_s2c.py). Read-only.
"""
import argparse
import csv
import os
import re
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import sweep_s4b as S4  # noqa: E402
import sweep_s2c as S2C  # noqa: E402

ROOT = os.path.dirname(HERE)
EXCEL = os.path.join(ROOT, "workspace", "merged", "data", "global", "excel")


def dword(va):
    return S4.dword(va)


def sdword(va):
    v = dword(va)
    return v - (1 << 32) if v & 0x80000000 else v


def cmd_tables():
    print("# g_StatEventFuncs 0x007325B0, entries 0..0x31")
    for i in range(0x32):
        print("E %d 0x%08X" % (i, dword(0x007325B0 + 4 * i)))
    print("# missile server do-function table 0x0073C768, entries 0..52")
    for i in range(53):
        print("M %d 0x%08X" % (i, dword(0x0073C768 + 4 * i)))
    print("# Missiles field descriptor, from the loader's stores 0x00661D97..0x00661E31 (name ptr, offset)")
    for ins_va, name_va in ((0x00661D97, 0x006EE368), (0x00661DB7, 0x006EE35C), (0x00661DD7, 0x006EE350),
                            (0x00661DF7, 0x006EE344), (0x00661E17, 0x006EE338)):
        mn, ops = S2C.ins_at(ins_va)
        nxt = S2C.window(ins_va, ins_va + 0x20)
        off = [o for va, m, o in nxt if m == "mov" and va > ins_va and re.search(r",0x[0-9a-f]+$", o)][0]
        data, _, _ = S4.image()
        o = S4.va_off(name_va)
        nm = data[o:data.index(b"\0", o)].decode()
        print("F %s %s | %s" % (nm, ops, off))
    print("# formation descriptor 0x0073D4F0 (FormationSpawn from 0x005B3559, class 0x154)")
    n = sdword(0x0073D4F0)
    print("D head %d %d %d" % (n, sdword(0x0073D4F4), sdword(0x0073D4F8)))
    for i in range(n):
        b = 0x0073D4FC + 12 * i
        print("D %d dx=%d dy=%d kind=%d" % (i, sdword(b), sdword(b + 4), sdword(b + 8)))
    print("# FormationSpawn kind table 0x005B34A4")
    for i in range(6):
        print("K %d 0x%08X" % (i, dword(0x005B34A4 + 4 * i)))
    print("# writes of the front-end mode word 0x007795EC")
    A = S4.asm()
    sites = []
    for va in sorted(A.ins):
        mn, ops = A.ins[va]
        if mn == "mov" and ops.startswith("DWORD PTR ds:0x7795ec,"):
            sites.append(va)
            print("W 0x%08X %s" % (va, ops.split(",", 1)[1]))
    print("N writes %d" % len(sites))
    print("# button records whose callback writes the mode word (record: ... strId at cb-8, cb)")
    data, _, _ = S4.image()
    for cb in (0x00435CD0, 0x00435D30, 0x00435D10, 0x00431A40, 0x00435D80):
        for ref in S4.raw_abs(cb):
            print("B cb=0x%08X ref=0x%08X strid=%d" % (cb, ref, dword(ref - 8)))


def rows(name):
    path = os.path.join(EXCEL, name)
    with open(path, encoding="latin-1", newline="") as f:
        r = list(csv.reader(f, delimiter="\t"))
    return r[0], r[1:]


def cmd_excel():
    h, rs = rows("itemstatcost.txt")
    ix = {c: i for i, c in enumerate(h)}
    print("# itemstatcost: itemeventfunc 31")
    for row in rs:
        for k in ("itemeventfunc1", "itemeventfunc2"):
            if row[ix[k]] == "31":
                print("I %s %s %s event=%s" % (row[ix["ID"]], row[0], k, row[ix["itemevent1"]]))
    h, rs = rows("missiles.txt")
    ix = {c: i for i, c in enumerate(h)}
    print("# missiles: pSrvDoFunc 13 and 36")
    for n, row in enumerate(rs):
        if row[ix["pSrvDoFunc"]] in ("13", "36"):
            print("M %d %s pSrvDoFunc=%s" % (n, row[0], row[ix["pSrvDoFunc"]]))
    h, rs = rows("skills.txt")
    print("# skills naming bonewallmaker")
    for n, row in enumerate(rs):
        for i, c in enumerate(row):
            if c == "bonewallmaker":
                print("S %s %s %s=%s srvdofunc=%s summon=%s" % (row[1], row[0], h[i], c, row[h.index("srvdofunc")],
                                                               row[h.index("summon")]))
    h, rs = rows("properties.txt")
    props = {row[0] for row in rs if "item_reanimate" in row}
    print("# properties with stat item_reanimate: %s" % sorted(props))
    for t in ("uniqueitems.txt", "runes.txt", "setitems.txt", "sets.txt", "magicprefix.txt", "magicsuffix.txt",
              "cubemain.txt", "automagic.txt", "qualityitems.txt", "rareprefix.txt", "raresuffix.txt"):
        if not os.path.exists(os.path.join(EXCEL, t)):
            continue
        h, rs = rows(t)
        for row in rs:
            for i, c in enumerate(row):
                if c in props and i < len(h):
                    print("P %s %s %s=%s next=%s" % (t, row[0], h[i], c, row[i + 1:i + 4]))


def operand_source(site, op):
    """The instruction that last loaded register op in the window before site (or the operand itself)."""
    if op is None:
        return "?"
    if op.strip().startswith("0x"):
        return op.strip()
    w = [x for x in S2C.window(site - 0x40, site + 5) if x[0] < site]
    src = op
    for va, mn, o in w:
        a = [x.strip() for x in o.split(",")]
        if a and a[0] == op.strip() and mn in ("mov", "movzx", "lea", "xor", "pop"):
            src = "%s(%s %s @0x%08X)" % (op, mn, o, va)
    return src


def site_pushes(site):
    w = [x for x in S2C.window(site - 0x40, site + 5) if x[0] < site]
    return [o for va, mn, o in w if mn == "push"]


def cmd_qsites():
    descs = S2C.quest_descs()
    owner = {}  # function entry -> set of (object id, stored word)
    for d in descs:
        stored = S2C.init_stores(d["init"]).get(0xE0, [])
        cbs = sorted(S2C.quest_callbacks([d]) | {d["init"]})
        G = S4.graph(cbs)
        for e, v in G.items():
            owner.setdefault(e, set()).add((d["id"], tuple(stored)))
    A = S4.asm()
    # map each instruction va to the walked function entries that contain it
    contain = {}
    for e in owner:
        vas, _, _ = S4.body(A, e)[:3]
        for va in vas:
            contain.setdefault(va, set()).add(e)
    sites = S2C.setstate_sites()
    n = 0
    for site, fname, word, bit, kind in sites:
        if word is not None and bit is not None:
            continue
        n += 1
        pu = site_pushes(site)
        wop = pu[-2] if len(pu) >= 2 else None
        bop = pu[-3] if len(pu) >= 3 else None
        es = sorted(contain.get(site, ()))
        objs = sorted({o for e in es for o in owner[e]})
        print("Q 0x%08X %s word=%s bit=%s fn=%s %s objects=%s" % (
            site, kind, word if word is not None else operand_source(site, wop),
            bit if bit is not None else operand_source(site, bop),
            ",".join("0x%08X" % e for e in es) or "-", fname,
            " ".join("%d:%s" % (i, "/".join(str(x) for x in w)) for i, w in objs) or "-"))
    print("N nonconstant %d" % n)
    rc = S4.raw_callers(0x0065C3E0)
    for site in rc:
        pu = site_pushes(site)
        wop = pu[-2] if len(pu) >= 2 else None
        es = sorted(contain.get(site, ()))
        objs = sorted({o for e in es for o in owner[e]})
        tp = S2C.traced_pushes(site, 0x30)
        word = tp[-2] if len(tp) >= 2 else None
        print("R 0x%08X word=%s fn=%s objects=%s" % (
            site, word if word is not None else operand_source(site, wop), ",".join("0x%08X" % e for e in es) or "-",
            " ".join("%d:%s" % (i, "/".join(str(x) for x in w)) for i, w in objs) or "-"))
    print("N rangeclear %d" % len(rc))


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("cmd", choices=("tables", "excel", "qsites"))
    ns = ap.parse_args(argv)
    {"tables": cmd_tables, "excel": cmd_excel, "qsites": cmd_qsites}[ns.cmd]()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
