#!/usr/bin/env python3
"""Socket insert and runeword model (plan 0029 Phase 2), checked against tools/gdb/sockets.gdb logs.

    python3 -I tools/sockets.py check <log> [<log> ...] [--excel DIR] [-v]

Model of docs/findings/items/0007-sockets-runewords.md, chained after tools/props.py (its tables, its Item and Roller,
the func handlers of items/0006):
  - ITEMS_InsertSocket (section 1): the tests in order, from the logged child (CH) and parent (PA) and the four option
    flags (INS0); compared with the tests the log passed (IST), the return value and the not-found word (INSX).
  - ITEMS_AttachToOwner (section 3): a gem or rune applies the gems row that names its item, the 3-block group of the
    parent's gemapplytype, in mode 2 (gem) or 5 (rune), with the child as the item and the target, through
    props.Roller; compared slot by slot, roll by roll and write by write with the log (APE ... APX) and with the
    child's lists at APX. A jewel applies nothing (no APE).
  - The link: the parent's lists after the insert are its lists before plus the child's own stat list
    (state 0, flags 0x80000000, the child's base entries).
  - RUNEWORD_Match (section 4): quality 4..9, base quest, the children's classes in insert order against Stat 194, the
    Runes scan from record 0 (complete, Rune1..6 with the k == n stale-word rule, etype, itype through
    ITEMS_UnitIsType); compared with MK (n, the children) and MX (the row). The stale stack word kids[n] is read from
    MK: it is whatever the stack held (not modelled; an input).
  - The server/ladder gate and RUNEWORD_Apply (section 5): the T1Code1..7 lines in order through props.Roller with
    the parent's lists as the target (state 171, flags 0x40) and the child (the completing rune) as the item: its seed,
    its type for the weapon/armour tests, its flags and durability for func 23, its ilvl for funcs 11/19. The child's
    seed is the one input: the seed it had at INS0 (CH), which the model carries through the transfer (no draws) to
    RWA and through the rolls to RWX and INSX. Compared slot by slot with the log and with the parent's lists at RWX.
  - sub_0055FE80_ItemRefillCharges (p7): every stat 204 entry with current < max gets max; compared at RFX.
  - INSX: the parent's and the child's lists, flags, mode, children, every seed (game seed, the child's and the
    parent's item and unit seeds) against the model.
  - The client test sub_004843E0_UiCanInsertSocket (UIC lines): the model's verdict from the logged inputs.
Exit 0 only when every insert and every client test reproduces. Stdlib only. Read-only.
"""
import argparse
import collections
import copy
import json
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import props  # noqa: E402

EXCEL = props.EXCEL
Mismatch = props.Mismatch
eq = props.eq
GEM, SOCK, RUNE = 20, 53, 74
QUAL = {1: "low", 2: "normal", 3: "superior", 4: "magic", 5: "set", 6: "rare", 7: "unique", 8: "crafted"}


class Tables(props.Tables):
    def __init__(self, excel):
        super().__init__(excel)
        self.gems = props.recs(excel, "gems")
        self.runes = props.recs(excel, "runes")
        self.gem_of = {props.s32(r, 0x28): i for i, r in enumerate(self.gems)}

    def raw(self, cls):
        return self.items[cls]

    def gemapplytype(self, cls):
        return self.raw(cls)[0x13E]

    def rune(self, i):
        r = self.runes[i]
        return dict(name=r[0:64].split(b"\0")[0].decode("latin1"), ename=r[64:128].split(b"\0")[0].decode("latin1"),
                    complete=r[0x80], server=r[0x81], itype=[props.u16(r, 0x86 + 2 * k) for k in range(6)],
                    etype=[props.u16(r, 0x92 + 2 * k) for k in range(3)],
                    rune=[props.s32(r, 0x98 + 4 * k) for k in range(6)], t1=props.blocks(r, 0xB0, 7))

    def max_sockets(self, cls, ilvl):
        return props.Tables.max_sockets(self, cls, ilvl)


def lists_of(u):
    """(base entries, [(state, flags, entries)]) of a logged unit (the owner field dropped)."""
    base = {(s, p): v for s, p, v in (u.get("b") or [])}
    subs = [[st, fl, {(s, p): v for s, p, v in ent}] for st, fl, ent, *_ in u.get("sub", [])]
    return base, subs


def norm(subs):
    return sorted((st, fl, tuple(sorted(e.items()))) for st, fl, e in subs)


class RuneItem(props.Item):
    """RUNEWORD_Apply's view: the parent's lists are the target, the child (the completing rune) is the item."""

    def __init__(self, T, parent, child):
        super().__init__(T, parent["cls"], parent["q"], child["ilvl"], parent["ver"], child["fl"], {}, [], "0:0")
        self.child_cls = child["cls"]
        self.child_b = T.base(child["cls"])

    def weapon(self):
        return self.T.is_type(self.child_cls, props.WEAP)

    def armor(self):
        return self.T.is_type(self.child_cls, props.ARMO)

    def has_dur(self, evd=None):
        b = self.child_b
        return bool(not b["nodur"] and b["dur"])          # a rune: nodurability 1, so never reached further


def client_test(T, d):
    """sub_004843E0_UiCanInsertSocket from the logged inputs: (verdict, the first failing test)."""
    cur, tgt = d["cur"], d["tgt"]
    if d["ui"] in (10, 11):
        return 0, "ui state %d" % d["ui"]
    if not T.is_type(cur["cls"], SOCK):
        return 0, "cursor item not a socket filler"
    if not tgt["fl"] & 0x800:
        return 0, "target not socketed"
    if not T.base(tgt["cls"])["hasinv"]:
        return 0, "target base hasinv 0"
    if not T.max_sockets(tgt["cls"], tgt["ilvl"]):
        return 0, "target ItemMaxSockets 0"
    if not tgt["fl"] & 0x10:
        return 0, "target not identified"
    if tgt["fl"] & 0x100:
        return 0, "target flag 0x100"
    if tgt["ninv"] is None:
        return 0, "target has no inventory"
    if tgt["ninv"] >= tgt["s194"] & 0xFF:
        return 0, "target full"
    return 1, "ok"


STAGES = ["child_item", "child_cursor", "parent_item", "parent_ident", "parent_mode", "child_sock", "child_ident",
          "parent_socketed", "parent_hasinv", "inventory", "free"]


def insert_tests(T, ins, ch, pa):
    """The tests of ITEMS_InsertSocket in order: (stages passed, ret, notFound, reason)."""
    passed = []
    if ch is None:
        return passed, 0, 1, "child not found"
    if ch["type"] != 4:
        return passed, 0, 0, "child not an item"
    passed.append("child_item")
    if ch["mode"] != 4:
        return passed, 0, 1, "child not on the cursor"
    passed.append("child_cursor")
    if pa is None:
        return passed, 0, 1, "parent not found"
    if pa["type"] != 4:
        return passed, 0, 0, "parent not an item"
    passed.append("parent_item")
    if not pa["fl"] & 0x10:
        return passed, 0, 0, "parent not identified"
    passed.append("parent_ident")
    if ins["p"][2] and pa["mode"] not in (0, 1):
        return passed, 0, 0, "parent not stored or equipped"
    passed.append("parent_mode")
    if not T.is_type(ch["cls"], SOCK):
        return passed, 0, 0, "child not a socket filler"
    passed.append("child_sock")
    if not ch["fl"] & 0x10:
        return passed, 0, 0, "child not identified"
    passed.append("child_ident")
    if not pa["fl"] & 0x800:
        return passed, 0, 0, "parent not socketed"
    passed.append("parent_socketed")
    if not T.base(pa["cls"])["hasinv"]:
        return passed, 0, 0, "parent base hasinv 0"
    passed.append("parent_hasinv")
    passed.append("inventory")
    s194 = {(s, p): v for s, p, v in (pa.get("b") or [])}.get((194, 0), 0)
    if (pa["ninv"] or 0) >= s194 & 0xFF:
        return passed, 0, 0, "parent full"
    passed.append("free")
    return passed, 1, 0, "inserted"


def match(T, parent_cls, q, kid_classes, s194, stale):
    """RUNEWORD_Match: (row or None, why)."""
    if 4 <= q <= 9:
        return None, "quality %d" % q
    if T.base(parent_cls)["quest"]:
        return None, "quest base"
    n = len(kid_classes)
    s = s194 & 0xFF
    if s != n:
        return None, "%d of %d sockets filled" % (n, s)
    kids = list(kid_classes) + list(stale[n:])
    for i in range(len(T.runes)):
        R = T.rune(i)
        if not R["complete"]:
            continue
        k = 0
        ok = True
        while k < 6 and R["rune"][k] >= 1:
            if n < k or kids[k] != R["rune"][k]:
                ok = False
                break
            k += 1
        if not ok or k < s:
            continue
        if any(e and T.is_type(parent_cls, e) for e in R["etype"][:3] if e):
            continue
        for t in R["itype"]:
            if not t:
                break
            if T.is_type(parent_cls, t):
                return i, "row %d %s" % (i, R["ename"])
    return None, "no row"


class Block:
    def __init__(self, ins):
        self.ins, self.ev = ins, []


def read_log(path):
    """Yield ("PDT", d), ("UIC", d), ("INS", Block) in log order."""
    open_ = {}
    for line in open(path, errors="replace"):
        tag, _, rest = line.rstrip("\n").partition(" ")
        if not rest.startswith("{"):
            continue
        try:
            d = json.loads(rest)
        except ValueError:
            continue
        th = d.get("th", 0)
        if tag in ("PDT", "UIC"):
            yield tag, d
            continue
        if tag == "INS0":
            open_[th] = Block(d)
            continue
        if th not in open_:
            continue
        b = open_[th]
        b.ev.append((tag, d))
        if tag == "INSX":
            yield "INS", b
            del open_[th]


def split(ev, start, end):
    """The events between a start tag and its end tag (first occurrence), and the rest."""
    out, rest, inside, got = [], [], False, None
    for t, d in ev:
        if not inside and got is None and t == start:
            inside, got = True, (d, None)
            continue
        if inside and t == end:
            inside = False
            got = (got[0], d)
            continue
        (out if inside else rest).append((t, d))
    return got, out, rest


ROLLTAGS = ("SLOT", "SLOTR", "ROLL", "ROLLR", "WR", "EVD")


def check_insert(T, blk, pdt, S, notes):
    ins = blk.ins
    get = collections.defaultdict(list)
    for t, d in blk.ev:
        get[t].append(d)
    ch = get["CH"][0] if get["CH"] else None
    pa = get["PA"][0] if get["PA"] else None
    x = get["INSX"][0]
    path = "packet" if ins["p"] == [1, 1, 1, 1] else "reader" if ins["p"] == [0, 0, 0, 0] else "p%s" % ins["p"]
    passed, ret, nf, why = insert_tests(T, ins, ch, pa)
    eq("tests passed", passed, [d["s"] for d in get["IST"]])
    eq("return value", ret, x["ret"])
    eq("not-found word", nf, x["nf"])
    eq("game seed unchanged", ins["gseed"], x["gseed"])
    res = dict(path=path, why=why, ret=ret)
    if ch:
        res["child"] = ch
    if pa:
        res["parent"] = pa
    if not ret:
        for who, a in (("child", ch), ("parent", pa)):
            if a is not None:
                b = x[who]
                for k in ("seed", "useed", "fl", "mode", "kids"):
                    eq("%s %s unchanged by a refused insert" % (who, k), a.get(k), b.get(k))
                eq("%s lists unchanged" % who, norm(lists_of(a)[1]), norm(lists_of(b)[1]))
        if get["APE"] or get["M0"]:
            raise Mismatch("a refused insert reached the transfer or the match")
        return res
    # ---- the transfer
    cseed = props.Seed(ch["seed"])
    cb, csubs = lists_of(ch)
    child = props.Item(T, ch["cls"], ch["q"], ch["ilvl"], ch["ver"], ch["fl"], cb, csubs, ch["seed"])
    grp = T.gemapplytype(pa["cls"])
    is_gem, is_rune = T.is_type(ch["cls"], GEM), T.is_type(ch["cls"], RUNE)
    ape, ap_ev, rest = split(blk.ev, "APE", "APX")
    if is_gem or is_rune:
        if ape is None:
            raise Mismatch("a gem or rune insert without ItemApplyProps")
        a, apx = ape
        row = T.gem_of.get(ch["cls"])
        mode = 2 if is_gem else 5
        eq("ItemApplyProps mode", mode, a["mode"])
        eq("ItemApplyProps a2 (the parent for a rune, 0 for a gem)", pa["u"] if is_rune else 0, a["a2"])
        eq("ItemApplyProps item is the child", True, a["same"])
        eq("gems row (the row naming the child's item)", row, a["row"])
        eq("group (the parent's gemapplytype)", grp, a["grp"])
        bl = [(b, 0, 0x40, False) for b in props.blocks(T.gems[row], 0x30 + 0x30 * grp, 3)]
        R = props.Roller(T, child, mode, [d["v"] for t, d in ap_ev if t == "EVD"], pdt)
        R.run(bl)
        props.compare_events(R.ev, [(t, d) for t, d in ap_ev if t in ROLLTAGS], "transfer %s" % T.base(ch["cls"])["code"])
        eq("child seed after the transfer (no draw)", ch["seed"], str(child.seed))
        eq("child seed at APX", str(child.seed), apx["seed"])
        eq("child lists at APX", norm(child.subs), norm(lists_of(apx)[1]))
        S["transfer %s group %d" % ("gem" if is_gem else "rune", grp)] += 1
        res["transfer"] = (row, grp, sum(1 for t, _ in ap_ev if t == "SLOT"))
    elif ape is not None:
        raise Mismatch("a jewel insert called ItemApplyProps")
    else:
        S["transfer jewel (none)"] += 1
        res["transfer"] = None
    # ---- the link
    pb, psubs = lists_of(pa)
    psubs = copy.deepcopy(psubs)
    psubs.append([0, 0x80000000, dict(child.base)])
    kid_classes = [c for _, c in (pa["kids"] or [])] + [ch["cls"]]
    pfl = pa["fl"]
    # ---- the match
    m0 = [(t, d) for t, d in rest if t in ("M0", "MK", "MX")]
    if not m0 or m0[0][0] != "M0":
        raise Mismatch("no RUNEWORD_Match after the insert")
    mk = [d for t, d in m0[:3] if t == "MK"]
    mx = [d for t, d in m0[:3] if t == "MX"]
    s194 = pb.get((194, 0), 0)
    stale = mk[0]["kids"] if mk else [0] * 7
    rw, mwhy = match(T, pa["cls"], pa["q"], kid_classes, s194, stale)
    if mk:
        eq("children in the match (n)", len(kid_classes), mk[0]["n"])
        eq("children's classes in insert order", kid_classes, mk[0]["kids"][:len(kid_classes)])
    eq("RUNEWORD_Match row (%s)" % mwhy, -1 if rw is None else rw, mx[0]["row"])
    res["match"] = (rw, mwhy)
    if len(kid_classes) == s194 & 0xFF and len(kid_classes) < 6:
        # a row with one rune more than the sockets compares the stale word kids[n]
        for i in range(len(T.runes)):
            R = T.rune(i)
            seq = [r for r in R["rune"] if r >= 1]
            if R["complete"] and len(seq) == len(kid_classes) + 1 and seq[:-1] == kid_classes:
                notes["one rune more than the sockets (stale kids[n])"].append(
                    "%s: %s row %d %s needs %d, stale word %d -> %s" % (
                        T.base(pa["cls"])["code"], [T.base(c)["code"] for c in kid_classes], i, R["ename"], seq[-1],
                        stale[len(kid_classes)], "match" if stale[len(kid_classes)] == seq[-1] else "no match"))
    rwa, rw_ev, rest2 = split(rest, "RWA", "RWX")
    apply_ = rw is not None and not (T.rune(rw)["server"] and not ins["ladder"])
    if rw is not None and not apply_:
        notes["server row in a non-ladder game: inserted, no runeword"].append("%s %s" % (
            T.base(pa["cls"])["code"], T.rune(rw)["ename"]))
    eq("RUNEWORD_Apply called", apply_, rwa is not None)
    if apply_:
        a, rwx = rwa
        eq("RUNEWORD_Apply child is the inserted child", True, a["same"])
        eq("child seed at RUNEWORD_Apply (the seed it had at the insert, no draw since)", str(child.seed), a["seed"])
        eq("parent lists at RUNEWORD_Apply", norm(psubs), norm(lists_of(a)[1]))
        it = RuneItem(T, pa, ch)
        it.base, it.subs, it.seed = dict(pb), copy.deepcopy(psubs), child.seed
        R = props.Roller(T, it, 6, [d["v"] for t, d in rw_ev if t == "EVD"], pdt)
        Rr = T.rune(rw)
        R.run([(b, 171, 0x40, False) for b in Rr["t1"]])
        props.compare_events(R.ev, [(t, d) for t, d in rw_ev if t in ROLLTAGS], "runeword %s" % Rr["ename"])
        eq("child seed at RWX", str(it.seed), rwx["seed"])
        eq("parent lists at RWX", norm(it.subs), norm(lists_of(rwx)[1]))
        eq("RUNEWORD_Apply return", 1, rwx["eax"])
        psubs = it.subs
        pfl |= 0x4000000
        draws = sum(1 for t, d in R.ev if t == "ROLL" and d["min"] != d["max"]) + sum(1 for t, _ in R.ev if t == "F19")
        res["rw"] = dict(row=rw, name=Rr["ename"], seed0=a["seed"], seed1=str(it.seed), draws=draws,
                         rolls=[(d["min"], d["max"]) for t, d in R.ev if t == "ROLL" and d["min"] != d["max"]],
                         vals=[d["v"] for t, d in R.ev if t == "ROLLR"], f19=[d for t, d in R.ev if t == "F19"],
                         loaded_seed=a["seed"] == "%08x:0000029a" % a["start"],
                         slots=[d["func"] for t, d in R.ev if t == "SLOT"])
        # ---- the refill
        rf0, _, rest2 = split(rest2, "RF0", "RFX")
        eq("charges refilled (option p7)", bool(ins["p"][3]), rf0 is not None)
        if rf0 is not None:
            refilled = 0
            for st, fl, e in psubs:
                for (stat, par), v in list(e.items()):
                    if stat == 204 and (v & 0xFF) < (v >> 8):
                        e[(stat, par)] = (v & ~0xFF) | (v >> 8)
                        refilled += 1
            eq("parent lists after the refill", norm(psubs), norm(lists_of(rf0[1])[1]))
            res["refilled"] = refilled
    elif ins["p"][0] == 0:
        pass
    child_seed = str(child.seed) if rwa is None else str(it.seed)
    # ---- the result
    if apply_ or ins["p"][0]:
        pfl |= 1
        pfl &= ~0x4000
    xp, xc = x["parent"], x["child"]
    eq("parent flags after", pfl, xp["fl"])
    eq("parent lists after", norm(psubs), norm(lists_of(xp)[1]))
    eq("parent base entries after", sorted(pb.items()), sorted(lists_of(xp)[0].items()))
    eq("parent children after", [c for _, c in (pa["kids"] or [])] + [ch["cls"]], [c for _, c in xp["kids"]])
    eq("parent item seed unchanged", pa["seed"], xp["seed"])
    eq("parent unit seed unchanged", pa["useed"], xp["useed"])
    eq("child mode 6", 6, xc["mode"])
    eq("child item seed after", child_seed, xc["seed"])
    eq("child unit seed unchanged", ch["useed"], xc["useed"])
    eq("child lists after", norm(child.subs), norm(lists_of(xc)[1]))
    return res


def recipe_games():
    """Character name -> "classic" | "exp", from the recipes' "game" key (d2s.py build gives the save that status)."""
    out = {}
    rd = os.path.join(HERE, "d2s_recipes")
    for fn in os.listdir(rd):
        if fn.endswith(".json"):
            with open(os.path.join(rd, fn)) as f:
                r = json.load(f)
            if "name" in r:
                out[r["name"].lower()] = "classic" if r.get("game") == "classic" else "exp"
    return out


def log_game(path, games):
    """The game of a log, from its "# installed NAME.d2s" header line (tools/d2run.py --install)."""
    with open(path, errors="replace") as f:
        for line in f:
            if not line.startswith("#"):
                break
            if line.startswith("# installed "):
                return games.get(line.split()[2][:-4].lower(), "?")
    return "?"


def cmd_check(ns):
    T = Tables(ns.excel)
    S = collections.Counter()
    notes = collections.defaultdict(list)
    ok = bad = 0
    table = collections.Counter()
    rws = collections.Counter()
    ui = collections.Counter()
    reasons = collections.Counter()
    gemcov = set()
    games = recipe_games()
    for path in ns.logs:
        pdt = (0, 0)
        game_of_log = log_game(path, games)
        for kind, x in read_log(path):
            if kind == "PDT":
                pdt = (x["c6c"], x["c70"])
                continue
            if kind == "UIC":
                try:
                    r, why = client_test(T, x)
                    eq("client insert test (%s)" % why, r, x["r"])
                    ui[(r, why)] += 1
                    S["client tests"] += 1
                except (Mismatch, KeyError, TypeError) as e:
                    bad += 1
                    print("FAIL %s UIC %s: %s" % (os.path.basename(path), json.dumps(x)[:300], e))
                continue
            try:
                r = check_insert(T, x, pdt, S, notes)
            except (Mismatch, KeyError, IndexError, TypeError) as e:
                bad += 1
                print("FAIL %s INS0 %s: %s" % (os.path.basename(path), json.dumps(x.ins)[:200], e))
                continue
            ok += 1
            ch, pa = r.get("child"), r.get("parent")
            mode = game_of_log
            reasons[(r["path"], r["why"])] += 1
            if r["ret"]:
                kind_ = ("gem" if T.is_type(ch["cls"], GEM) else "rune" if T.is_type(ch["cls"], RUNE) else
                         "jewel %s" % QUAL.get(ch["q"], ch["q"]))
                cls = ("weapon" if T.gemapplytype(pa["cls"]) == 0 else "helm/armour" if T.gemapplytype(pa["cls"]) == 1
                       else "shield")
                table[(r["path"], mode, kind_, cls)] += 1
                if T.is_type(ch["cls"], GEM):
                    notes["gem codes inserted"].append(T.base(ch["cls"])["code"])
                    gemcov.add((ch["cls"], T.gemapplytype(pa["cls"])))
                if r.get("rw"):
                    w = r["rw"]
                    rws[(w["row"], w["name"])] += 1
                    notes["runewords"].append("%s %s q%d %s: %s seed %s -> %s, %d draws, rolls %s -> %s%s%s" % (
                        r["path"], T.base(pa["cls"])["code"], pa["q"], "eth" if pa["fl"] & 0x400000 else "",
                        w["name"], w["seed0"], w["seed1"], w["draws"], w["rolls"],
                        [v for v in w["vals"]], " f19 %s" % w["f19"] if w["f19"] else "",
                        " (loaded rune: seed = {start, 666})" if w["loaded_seed"] else " (seed != {start, 666})"))
                    if "refilled" in r:
                        notes["charges refilled"].append("%s: %d entries" % (w["name"], r["refilled"]))
                elif r["match"][0] is None and len(pa.get("kids") or []) + 1 == ({(s, p): v for s, p, v in
                                                                                   (pa.get("b") or [])}.get((194, 0), 0) & 0xFF):
                    notes["full item, no runeword"].append("%s %s q%d %s: %s" % (
                        r["path"], T.base(pa["cls"])["code"], pa["q"],
                        [T.base(c)["code"] for _, c in pa["kids"]] + [T.base(ch["cls"])["code"]], r["match"][1]))
    print("%d inserts reproduced, %d failed; %d client tests" % (ok, bad, S["client tests"]))
    print("insert outcomes (path, reason):")
    for k, v in sorted(reasons.items()):
        print("  %-7s %-32s %d" % (k[0], k[1], v))
    print("successful inserts by path, game, child, parent class:")
    for k, v in sorted(table.items()):
        print("  %-7s %-8s %-14s %-12s %d" % (k + (v,)))
    print("runewords made: %d from %d rows" % (sum(rws.values()), len(rws)))
    for k, v in sorted(rws.items()):
        print("  %3d %-22s %d" % (k[0], k[1], v))
    print("client test verdicts:")
    for k, v in sorted(ui.items()):
        print("  %d %-34s %d" % (k[0], k[1], v))
    print("transfers: %s" % ", ".join("%s %d" % kv for kv in sorted(S.items()) if kv[0].startswith("transfer")))
    gems = collections.Counter(notes.pop("gem codes inserted", []))
    print("gem codes inserted (%d kinds): %s" % (len(gems), " ".join("%s:%d" % kv for kv in sorted(gems.items()))))
    allgems = [props.s32(r, 0x28) for r in T.gems if T.is_type(props.s32(r, 0x28), GEM)]
    miss = [(T.base(c)["code"], g) for c in allgems for g in (0, 1, 2) if (c, g) not in gemcov]
    print("gem x group coverage: %d of %d (gems %d x groups 3); missing %s" % (
        len(allgems) * 3 - len(miss), len(allgems) * 3, len(allgems), miss or "none"))
    for k in sorted(notes):
        print("-- %s (%d)" % (k, len(notes[k])))
        for n in notes[k][: (None if ns.verbose else 40)]:
            print("   " + n)
    return 0 if bad == 0 and ok > 0 else 1


def main(argv):
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("check")
    c.add_argument("logs", nargs="+")
    c.add_argument("--excel", default=EXCEL)
    c.add_argument("-v", "--verbose", action="store_true")
    ns = ap.parse_args(argv)
    return cmd_check(ns)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
