#!/usr/bin/env python3
"""Plan 0038 batch H6a (cube): the checks over the batch's tools/gdb/cube.gdb (logger r4) logs.

    python3 -I tools/sweep_h6a.py check LOG [LOG ...]      # every check below; exit 0 when no mismatch
    python3 -I tools/sweep_h6a.py static                   # the pinned game.exe reads (objdump and the PE's bytes)

check runs tools/cube.py's transmute model on every transmute (CUB0 .. CUBX), then adds, per inventory row of
docs/plans/0038-inventory/items-cube.md:
  cube 1   the call chain of every transmute: PK4F (packet 0x4F, 7 bytes, button 0x18; the return into
           sub_0054D750_SrvPacketDispatch), PIB (sub_00554100_PlayerGetInteract's type 4), CBTN (button 0x18, return
           into sub_00568060_PktInteractButton), CUB0's return into sub_00566AE0_CubeButton
  cube 7   SEV: UnitSetEvent(player, 4) after the destroy of every produced transmute (0x00566439), (player, 20) at every
           refused cow portal (inside CUBE_CowPortalOpen), and no SEV in a transmute that produced nothing otherwise
  cube 15  `upg` inputs of a higher tier matched (the item's code its base's ubercode or ultracode)
  cube 17  the `exc` input test decided: the item passes every other test of the row's input 1 and fails `exc`
  cube 25  the `eli` slot branch: a matched row whose output A has `eli`, its slots the ultracode record
  cube 32  the copy's children: kept (useitem/mod without uns) or not copied (uns), counted per copy
  cube 36  uns on a runeword: bit 26, prefix 0 and the state-171 list removed (tools/cube.py check_strip)
  cube 38  mod lines on an ethereal item (MakeEthereal again) and ItemInitStats on an ethereal copy
  cube 39  rep (damaged, broken), rch (charges refilled)
  cube 40  qty= without sock on a stackable base (rep and qty=)
  cube 43  QSM / QKW: the quest hooks called for a placed hst / qf2 and for no other output; word 10 bit 11
  cube 49  CNULL: the crafted builder's duplicate test reading the record of id 0 (EAX 0) with a filled slot, and the
           transmute's end (no CUBX, the game gone)
  cube 51  row 19's random item of a type: whether the skipped record start - 1 was a candidate (separating case)
  cube 53/54  the cow portal tests (tools/cube.py check_cow): outside level 1, classic word 26
  cube 58  a forced affix above the item's alvl (the forced row skips the level window)
Stdlib only; reads the logs and workspace/merged tables.
"""
import collections
import io
import json
import os
import struct
import subprocess
import sys
import contextlib

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import cube  # noqa: E402
import affixes  # noqa: E402
import items_chain  # noqa: E402
import rng  # noqa: E402
import quality  # noqa: E402

GAME = os.path.join(ROOT, "workspace", "install", "app", "game.exe")
DISPATCH = (0x0054D750, 0x0054D9FF)          # sub_0054D750_SrvPacketDispatch (checked by `static`)
PKTIB = (0x00568060, 0x005685FF)             # sub_00568060_PktInteractButton
COWFN = (0x00594140, 0x0059426F)             # CUBE_CowPortalOpen


class Rep:
    def __init__(self):
        self.n = collections.Counter()
        self.bad = []
        self.notes = collections.defaultdict(list)

    def ok(self, k, v=1):
        self.n[k] += v

    def fail(self, msg):
        self.bad.append(msg)

    def note(self, k, s):
        self.notes[k].append(s)


def lines(path):
    out = []
    for ln in open(path, errors="replace"):
        tag, _, rest = ln.rstrip("\n").partition(" ")
        if rest.startswith("{"):
            try:
                out.append((tag, json.loads(rest)))
            except ValueError:
                pass
    return out


def transmutes(ev):
    """Each CUB0 with the r4 lines before it (back to the previous CUBX) and up to its CUBX (None if the log ends)."""
    out, pre, cur = [], [], None
    for tag, d in ev:
        if tag == "CUB0":
            cur = dict(c=d, pre=pre, ev=[], x=None)
            pre = []
            continue
        if cur is None:
            pre.append((tag, d))
            continue
        if tag == "CUBX":
            cur["x"] = d
            out.append(cur)
            cur = None
            continue
        cur["ev"].append((tag, d))
    if cur is not None:
        out.append(cur)
    return out


def check_chain(R, t, name):
    pre = t["pre"]
    pk = [d for tg, d in pre if tg == "PK4F"]
    pib = [d for tg, d in pre if tg == "PIB"]
    cb = [d for tg, d in pre if tg == "CBTN"]
    if not (pk and pib and cb):
        R.fail("%s: transmute without PK4F/PIB/CBTN before it" % name)
        return
    p, i, b = pk[-1], pib[-1], cb[-1]
    pkt = bytes.fromhex(p["pkt"] or "")
    good = (p["len"] == 7 and pkt[:1] == b"\x4f" and struct.unpack("<H", pkt[1:3])[0] == 0x18
            and DISPATCH[0] <= p["ret"] <= DISPATCH[1] and i["r"] != 0 and i["type"] == 4 and i["btn"] == 0x18
            and b["btn"] == 0x18 and PKTIB[0] <= b["ret"] <= PKTIB[1] and t["c"].get("ret") == 0x00566AFC)
    if good:
        R.ok("cube 1: PK4F 0x4F/0x18 -> PIB type 4 -> CBTN 0x18 -> CUBE_Transmute (ret 0x00566AFC)")
        R.note("cube 1: return addresses (PK4F, CBTN, CUB0)", "%08x %08x %08x" % (p["ret"], b["ret"], t["c"]["ret"]))
    else:
        R.fail("%s: call chain %r %r %r ret %r" % (name, p, i, b, t["c"].get("ret")))


def check_events(R, t, name, res):
    sev = [d for tg, d in t["ev"] if tg == "SEV"]
    player = t["c"]["player"]
    produced = bool(res and res.get("produced"))
    cow_refused = [o for o in (res or {}).get("outs", []) if o.get("kind") == "cow portal" and o.get("result") == 0]
    want = []
    if cow_refused:
        want.append(20)
    if produced:
        want.append(4)
    got = [d["ev"] for d in sev]
    if got != want or any(d["unit"] != player for d in sev):
        R.fail("%s: UnitSetEvent %s, model %s" % (name, [(d["ev"], hex(d["ret"])) for d in sev], want))
        return
    for d in sev:
        if d["ev"] == 4:
            if d["ret"] != 0x0056643E:
                R.fail("%s: event 4 from %08x" % (name, d["ret"]))
            R.ok("cube 7: UnitSetEvent(player, 4) after the destroy (ret 0x0056643E)")
        else:
            if not COWFN[0] <= d["ret"] <= COWFN[1]:
                R.fail("%s: event 20 from %08x" % (name, d["ret"]))
            R.ok("cube 7: UnitSetEvent(player, 20) at a refused cow portal (ret %08x)" % d["ret"])
    if not got:
        R.ok("cube 7: no UnitSetEvent (nothing produced, no cow refusal)")


def check_quest(R, T, t, name):
    ev = t["ev"]
    placed = [d["it"]["cls"] for tg, d in ev if tg == "CPL"]
    codes = [T.code(c).decode().strip() for c in placed]
    qsm = [d for tg, d in ev if tg == "QSM"]
    qkw = [d for tg, d in ev if tg == "QKW"]
    if [d["it"]["cls"] for d in qsm] != [c for c, k in zip(placed, codes) if k == "hst"]:
        R.fail("%s: QSM %s for placed %s" % (name, qsm, codes))
    if [d["it"]["cls"] for d in qkw] != [c for c, k in zip(placed, codes) if k == "qf2"]:
        R.fail("%s: QKW %s for placed %s" % (name, qkw, codes))
    for d in qsm:
        s = [x for tg, x in ev if tg == "QSMS"]
        x = [x for tg, x in ev if tg == "QSMX"]
        if not (s and x and s[0]["q"] == 10 and s[0]["s"] == 11 and not s[0]["w10"] & 0x800 and x[0]["w10"] & 0x800
                and x[0]["w10"] == s[0]["w10"] | 0x800):
            R.fail("%s: QuestStaffMade word 10 %s -> %s" % (name, s, x))
        else:
            R.ok("cube 43: hst placed -> QuestStaffMade, the player's word 10 bit 11 set (0x%04x -> 0x%04x)" % (
                s[0]["w10"], x[0]["w10"]))
        a = [x for tg, x in ev if tg == "QSD0"]
        b = [x for tg, x in ev if tg == "QSD1"]
        if a and b:
            R.note("cube 43: the game's quest 9 data +0x18..+0x2C before / after, byte +0x2A",
                   "%s -> %s, %s" % (a[0]["w"], b[0]["w"], b[0]["b2a"]))
    for d in qkw:
        q = [x for tg, x in ev if tg == "QKW18"]
        a = [x for tg, x in ev if tg == "QKD0"]
        b = [x for tg, x in ev if tg == "QKD1"]
        R.ok("cube 43: qf2 placed -> QuestKhalimWillMade")
        R.note("cube 43: QuestKhalimWillMade word 18, GetState(18, 0), quest 16 data +0x10..+0x20 before / after",
               "%s, %s, %s -> %s" % (q[0]["w18"] if q else None, q[0]["r"] if q else None, a[0]["w"] if a else None,
                                    b[0]["w"] if b else None))
    if placed and not qsm and not qkw:
        R.ok("cube 43: no quest hook for the other outputs placed (%s)" % ",".join(sorted(set(codes))))


def item_other_tests(T, r, it, game, drop):
    """The row's input 1 test with flag bits `drop` cleared (the test decides when this passes and the real one
    does not)."""
    r2 = json.loads(json.dumps(r, default=lambda o: None))
    r2["ins"][0]["flags"] &= ~drop
    return cube.item_test(T, r2, 0, it, game)


def check_tiers(R, T, t, name, res):
    c = t["c"]
    rows = T.rows
    for it in c["items"]:
        for ri in (131, 132, 135, 136):
            r = rows[ri]
            if r["ins"][0]["flags"] & 0x200 and len(c["items"]) == r["n"]:
                real = cube.item_test(T, r, 0, it, c)
                other = item_other_tests(T, r, it, c, 0x200)
                tier = tier_of(T, it["cls"])
                if other and not real:
                    R.ok("cube 17: exc decided: row %d refuses a %s-tier item (%s)" % (ri, tier, code(T, it)))
                elif other and real:
                    R.ok("cube 17: exc passed: row %d input 1 an exceptional item (%s)" % (ri, code(T, it)))
    row = res.get("row") if res else None
    if row is None:
        return
    r = rows[row]
    a = r["outs"][0]
    if r["ins"][0]["flags"] & 0x80:
        for it in c["items"]:
            if cube.item_test(T, r, 0, it, c):
                tier = tier_of(T, it["cls"])
                if tier != "normal":
                    R.ok("cube 15: upg matched a higher tier: row %d input %s, item %s (%s)" % (
                        row, T.code(r["ins"][0]["index"]).decode().strip(), code(T, it), tier))
    if a["kind"] in (0xFE, 0xFF) and a["flags"] & 0x100:
        sl = res.get("slots") or []
        R.ok("cube 25: eli slot branch: row %d" % row)
    for o in res.get("outs", []):
        if o.get("strip"):
            s = o["strip"]
            R.ok("cube 32: uns copy: %d children on the input, %d on the copy" % (s["kids_src"], s["kids_copy"]))
            if s["runeword"]:
                R.ok("cube 36: uns removed the runeword")
        if o.get("kids_kept") is not None:
            R.ok("cube 32: copy kept its %d children" % o["kids_kept"])
        for k in ("rep dur", "rep broken", "rep qty", "qty", "rch"):
            if k in o:
                R.ok("cube %s: %s %s" % ("40" if "qty" in k else "39", k, o[k]))


def tier_of(T, cls):
    n, u, e = T.tiers(cls)
    c = T.raw(cls)[0x80:0x84]
    return "normal" if c == n else "exceptional" if c == u else "elite" if c == e else "?"


def code(T, it):
    return T.code(it["cls"]).decode().strip()


def check_pole(R, T, t, name):
    ev = t["ev"]
    c = t["c"]
    for i, (tg, d) in enumerate(ev):
        if tg != "CPT0":
            continue
        gs = cube.seedpair(d["gs"])
        n = len(T.P.items)
        start, _ = quality.range_b(gs, n)
        cand = lambda j: (T.A.is_type(j, d["type"]) and T.raw(j)[0x133] and
                          (cube.u16(T.raw(j), 0xF6) < 100 or c["iver"] >= 100) and T.raw(j)[0xFD] <= d["ilvl"])
        skipped = (start - 1) % n
        R.ok("cube 51: row 19 transmutes")
        R.note("cube 51: start, skipped record start-1 a candidate?", "%s %d %d %s" % (
            name, start, skipped, bool(cand(skipped))))
        if cand(skipped):
            R.ok("cube 51: separating: the skipped record start - 1 is a candidate")


def check_forced(R, T, t, name, res):
    row = res.get("row") if res else None
    if row != 17:
        return
    for tg, d in t["ev"]:
        if tg == "CPL":
            it = d["it"]
            st = affixes.Item(T.A, {"cls": it["cls"], "ilvl": it["ilvl"], "ver": it["ver"]})
            st.q = it["q"]
            alvl = affixes.alvl_of(st)
            sid = it["s"][0]
            lvl = T.A.magic[sid - 1]["level"] if sid else None
            R.note("cube 58: row 17 output base, ilvl, alvl, suffix id, its level", "%s %d %d %d %s" % (
                code(T, it), it["ilvl"], alvl, sid, lvl))
            if sid and lvl > alvl:
                R.ok("cube 58: forced suffix above the alvl (level %d > alvl %d) taken" % (lvl, alvl))


def check_crash(R, T, t, name, log_end):
    cn = [d for tg, d in t["ev"] if tg == "CNULL"]
    zero = [d for d in cn if d["rec"] == 0]
    if not zero:
        R.fail("%s: transmute without CUBX and no CNULL record 0" % name)
        return
    d = zero[-1]
    if d["id"] == 0 and d["slot"] != 0 and d["srec"] != 0 and d is cn[-1]:
        recs = [x for tg, x in t["ev"] if tg == "CREC"]
        base = code(T, {"cls": recs[-1]["idx"]}) if recs else "?"
        R.ok("cube 49: (b) the crafted pick of 0 with a filled slot: record 0 read at +0x5C (side %s, slot %d id %d), "
             "the transmute never ended" % (d["side"], d["k"], d["slot"]))
        R.note("cube 49: the faulting transmute", "%s base %s ilvl %s, last line %s" % (
            name, base, recs[-1]["ilvl"] if recs else "?", log_end))
    else:
        R.fail("%s: CNULL %r" % (name, d))


def cmd_check(ns):
    T = cube.Tables(cube.EXCEL)
    affixes.PROPS_HOOK = items_chain.make_hook(T.P)
    R = Rep()
    S = collections.Counter()
    notes = collections.defaultdict(list)
    ntx = 0
    for path in ns.logs:
        name = os.path.basename(path)
        ev = lines(path)
        pdt = (0, 0)
        for tg, d in ev:
            if tg == "PDT":
                pdt = (d["c6c"], d["c70"])
                break
        model = list(cube.read_log(path))
        made = set()
        txs = transmutes(ev)
        mi = 0
        for k, t in enumerate(txs, 1):
            tn = "%s #%d" % (name, k)
            check_chain(R, t, tn)
            if t["x"] is None:
                last = ev[-1][0] if ev else None
                check_crash(R, T, t, tn, last)
                continue
            mt = model[mi]
            mi += 1
            try:
                res = cube.check_tx(T, mt, S, notes, pdt, made)
            except (cube.Mismatch, affixes.Mismatch, KeyError, IndexError, TypeError, ValueError) as e:
                R.fail("%s: model: %s" % (tn, e))
                continue
            ntx += 1
            R.ok("transmutes reproduced by tools/cube.py")
            R.note("transmutes", "%s: row %s %s" % (tn, res.get("row"), json.dumps(res.get("outs", []))[:300]))
            check_events(R, t, tn, res)
            check_quest(R, T, t, tn)
            check_tiers(R, T, t, tn, res)
            check_pole(R, T, t, tn)
            check_forced(R, T, t, tn, res)
            for o in res.get("outs", []):
                if o.get("cow"):
                    R.ok("cube 53/54: cow portal: %s (%s)" % (o["cow"], "exp" if t["c"]["exp"] else "classic"))
    for k in sorted(S):
        R.note("tools/cube.py counters", "%-66s %d" % (k, S[k]))
    for k in sorted(R.n):
        print("  %-100s %d" % (k, R.n[k]))
    for k in sorted(R.notes):
        print("-- %s:" % k)
        for v, n in sorted(collections.Counter(R.notes[k]).items()):
            print("     %s%s" % (v, " (x%d)" % n if n > 1 else ""))
    for b in R.bad:
        print("MISMATCH " + b)
    print("%d logs, %d transmutes checked, %d mismatches" % (len(ns.logs), ntx, len(R.bad)))
    return 0 if not R.bad else 1


# ---------------------------------------------------------------- static

def pe_read(va, n):
    b = open(GAME, "rb").read()
    pe = struct.unpack_from("<I", b, 0x3C)[0]
    nsec = struct.unpack_from("<H", b, pe + 6)[0]
    opt = struct.unpack_from("<H", b, pe + 20)[0]
    base = struct.unpack_from("<I", b, pe + 24 + 28)[0]
    sec = pe + 24 + opt
    rva = va - base
    for i in range(nsec):
        s = sec + 40 * i
        vsz, vaddr, rsz, raw = struct.unpack_from("<IIII", b, s + 8)
        if vaddr <= rva < vaddr + max(vsz, rsz):
            off = rva - vaddr
            return b[raw + off: raw + off + n] if off < rsz else b"\0" * n
    raise ValueError("va %08x not mapped" % va)


def objdump(lo, hi):
    out = subprocess.run(["objdump", "-d", "-M", "intel", "--start-address=0x%x" % lo, "--stop-address=0x%x" % hi,
                          GAME], capture_output=True, text=True).stdout
    return [ln for ln in out.splitlines() if ln[:2] == "  " and ":" in ln]


def cmd_static(ns):
    h, flag = struct.unpack("<II", pe_read(0x006E0D18 + 0x4F * 8, 8))
    print("g_SrvPacketTable[0x4F] = {handler %08x, flag %08x}" % (h, flag))
    bad = h != 0x0054C7C0
    for lo, hi, what in ((0x0054C7C0, 0x0054C7FB, "Pkt4FButton"), (0x00566AE0, 0x00566B2D, "CubeButton"),
                         (0x00566400, 0x0056657C, "RecipeOutputCreate: destroy, event 4, placement, quest hooks"),
                         (0x0059E5C0, 0x0059E623, "QuestStaffMade"), (0x005B86E0, 0x005B8733, "QuestKhalimWillMade"),
                         (0x00558C50, 0x00558CA4, "ItemRemoveRuneword"),
                         (0x0055F900, 0x0055F9B5, "ItemRepairBroken")):
        print("== %s %08x..%08x" % (what, lo, hi))
        for ln in objdump(lo, hi):
            if "int3" not in ln:
                print(ln)
    # the dispatcher's indirect call: the PK4F return address lies in it
    calls = [ln for ln in objdump(*DISPATCH) if "call" in ln]
    print("== sub_0054D750_SrvPacketDispatch calls")
    for ln in calls:
        print(ln)
    return 1 if bad else 0


def cmd_tables(ns):
    """cube 49 case (a) and cube 51 from the stock tables: (a) needs a side whose FIRST crafted pick has no candidate
    (the side holds no filled slot yet). The pick skips the groups already on the item, and the prefix and suffix
    groups share one group; so (a) needs a base and ilvl where one side's candidates are all of that shared group,
    taken by the other side. Printed for every crafted row's spawnable bases at every output ilvl 1..99: the sides
    whose candidates span <= 2 groups, with those groups, and the count of (row, base, ilvl, side) whose candidates
    are all in the shared group (case (a) reachable). cube 51: the candidates of row 19 at its output lvl and the
    item count, in an expansion and in a classic game."""
    import sweep_s2c as S2
    with contextlib.redirect_stdout(io.StringIO()):
        R2 = S2.Report("h6a-tables")
        T = S2.tbl_cube(R2)
    A = T.A
    pg = {A.magic[i]["group"] for i in range(*A.blk_p)}
    sg = {A.magic[i]["group"] for i in range(*A.blk_s)}
    shared = pg & sg
    print("prefix groups %d, suffix groups %d, shared %s" % (len(pg), len(sg), sorted(shared)))
    rows = [(i, r) for i, r in enumerate(T.rows) if r["enabled"] and any(o["kind"] and o["q"] == 8 for o in r["outs"])]
    reach_a = 0
    cases = 0
    for i, r in rows:
        x = r["ins"][0]
        cls_ = [c for c in range(len(T.P.items))
                if (x["flags"] & 2 and T.A.is_type(c, x["index"]) or x["flags"] & 1 and c == x["index"])
                and T.P.items[c][0x133]]
        for c in cls_:
            for ilvl in range(1, 100):
                for side in ("p", "s"):
                    cand = S2.crafted_candidates(T, c, ilvl, side)
                    g = sorted(set(y[1] for y in cand))
                    cases += 1
                    if not cand or set(g) <= shared:
                        reach_a += 1
                        print("case (a) reachable: row %d base %s ilvl %d side %s groups %s" % (
                            i, T.code(c).decode().strip(), ilvl, side, g))
                    elif len(g) <= 2:
                        print("row %d base %s ilvl %d side %s: %d candidates, groups %s" % (
                            i, T.code(c).decode().strip(), ilvl, side, len(cand), g))
    print("crafted (row, base, ilvl, side) cases %d; case (a) reachable in %d" % (cases, reach_a))
    # cube 16, 44, 25: the compiled inputs with `eth` (0x010), the outputs with `rem` (0x020) or `uns` (0x010), and
    # the rows whose output A has `exc`/`eli` (0x080/0x100) with their version
    ins = [(i, k) for i, r in enumerate(T.rows) for k, x in enumerate(r["ins"]) if x["flags"] & 3]
    print("compiled inputs %d; with eth %d; with noe %d" % (
        len(ins), sum(1 for i, k in ins if T.rows[i]["ins"][k]["flags"] & 0x10),
        sum(1 for i, k in ins if T.rows[i]["ins"][k]["flags"] & 0x20)))
    outs = [(i, s_) for i, r in enumerate(T.rows) for s_, o in enumerate(r["outs"]) if o["kind"]]
    print("outputs %d; with rem %s; with uns %s" % (
        len(outs), [i for i, s_ in outs if T.rows[i]["outs"][s_]["flags"] & 0x20],
        [i for i, s_ in outs if T.rows[i]["outs"][s_]["flags"] & 0x10]))
    print("rows with output A exc/eli (row, flags, version, enabled): %s" % [
        (i, hex(r["outs"][0]["flags"] & 0x180), r["ver"], r["enabled"]) for i, r in enumerate(T.rows)
        if r["outs"][0]["kind"] in (0xFE, 0xFF) and r["outs"][0]["flags"] & 0x180])
    n = len(T.P.items)
    for iver, game in ((101, "expansion"), (1, "classic")):
        cand = [j for j in range(n) if T.A.is_type(j, T.rows[19]["outs"][0]["index"]) and T.raw(j)[0x133]
                and (cube.u16(T.raw(j), 0xF6) < 100 or iver >= 100) and T.raw(j)[0xFD] <= 50]
        print("row 19, %s game: %d items, %d candidates at lvl 50 %s; P(start - 1 a candidate) = %d/%d" % (
            game, n, len(cand), [T.code(j).decode().strip() for j in cand], len(cand), n))
    return 0


def main(argv):
    import argparse
    ap = argparse.ArgumentParser(prog="sweep_h6a.py")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("check")
    p.add_argument("logs", nargs="+")
    sub.add_parser("static")
    sub.add_parser("tables")
    ns = ap.parse_args(argv[1:])
    return {"check": cmd_check, "static": cmd_static, "tables": cmd_tables}[ns.cmd](ns)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
