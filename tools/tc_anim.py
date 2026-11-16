"""Animate one treasure-class drop (docs/specs/items/tc.md, quality.md, uniques-sets.md, affixes.md) step by step,
ending with the dropped items' inventory icons.

Usage:
  python3 -I tools/tc_anim.py <root> <monster|superunique|TC name> <seed> [--difficulty 0|1|2|normal|nightmare|hell]
        [--players N] [--mf N] [--mlvl N] [--kind normal|champion|unique|minion] [--max N] [--out DIR]
  python3 -I tools/tc_anim.py selftest <root> <log> [<log> ...]      (instrumented run against kept game logs)

<root> is the merged data tree (workspace/merged). The first argument names a MonStats Id (--kind picks the
monster's type flag: the drop column TreasureClass1/2/3 of the difficulty, tc.md B), a Superuniques name (column
TC / TC(N) / TC(H)), or a TreasureClassEx name (the resolver starts there; no level upgrade). <seed> is an
illustrative input: the source unit's seed is {seed, 666} and the game-seed stream that seeds each created
item is derived from it too; neither is a seed the game derives (rng/seeds). Defaults: difficulty 0 (Normal),
expansion game, one player alone (party 1, PlayerCount N), magic find 0 (--mf N: the killer's stat 80),
--mlvl the MonStats Level column of the difficulty (the game takes Levels.MonLvl*Ex for non-boss monsters in
expansion Nightmare/Hell, so pass --mlvl for those; not modelled here), --max 0 = the monster drop's 6.
Outputs, all regenerable and never committed, only under workspace/ (anim_common.safe_out), default DIR
workspace/render/anim/tc-<name>-d<difficulty>-<seed hex>/:
  frame-NNN.png  one frame per step: the resolver's frame stack and log, the current item's quality chain and
                 builder lines, the items dropped so far (inventory icons once an item is complete), caption
  tc.gif         the frames as an animated GIF (global palette: UI colours then the icons' colours)
  index.html     local step-through page (prev/next/play, slider, arrow keys, calculations, how to read this)
  steps.json     {text, calc} per step

Every caption and calculation line restates a spec section; it claims nothing of its own. Models used, all
reading of the specs, none re-derived here: tools/tc.py (Tables, nodrop_scaled; the resolver loop is the
expansion branch of tc.replay_call run on its own seed instead of a log), tools/quality.py (roll, with its
trace), tools/uniques.py (overrides, unique_cands, set_cands and the draws of check_block), tools/affixes.py
(Walk with free=True, the builders magic, rare, superior, low, normal; tools/props.py through
tools/items_chain.make_hook for the item seed), tools/item_art.py and tools/palette.py (icons, items/0003),
tools/tbl.py (Strings: the shown names of uniques, sets and affixes, data/strings.md D and C).
Not modelled here, shown as such: the Levels monster level, the quest TC (TreasureClass4), classic games,
gold amounts and gold find, ItemInitStats (quantity, durability, defense), the ethereal and socket rolls and the
automagic pick after them, the durability fix after a failed unique or set, the unit seed and the unidentified
view of an item, the properties' values (ItemApplyProps draws are applied to the item seed only).
selftest runs this tool's resolver and creation chain on the logged inputs of tools/gdb logs and compares
count, final seed, created items and quality, and the creation's join seed with the log. Stdlib only.
"""
import copy
import json
import os
import struct
import sys
import tempfile
from fractions import Fraction  # noqa: F401

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import affixes  # noqa: E402
import anim_common  # noqa: E402
import dc6  # noqa: E402
import excel_bin  # noqa: E402
import item_art  # noqa: E402
import items_chain  # noqa: E402
import palette as pal  # noqa: E402
import png  # noqa: E402
import props  # noqa: E402
import tbl  # noqa: E402
import quality  # noqa: E402
import rng  # noqa: E402
import tc  # noqa: E402
import uniques  # noqa: E402

M32 = 0xFFFFFFFF
QNAME = {1: "low", 2: "normal", 3: "superior", 4: "magic", 5: "set", 6: "rare", 7: "unique"}
DIFFN = ("Normal", "Nightmare", "Hell")
CHAIN6 = ("unique", "set", "rare", "magic", "superior", "normal")     # quality.md "Test order"


# ---------------------------------------------------------------- the models, wired together

class Models:
    def add_display_names(self, root):
        """Give each unique, set, magic and rare-affix record a "disp" text: its name key resolved through the string
        tables (data/strings.md D1: key -> index by the patchstring, expansionstring, string order; C1: index -> text).
        The key stays in "name". A key found nowhere shows the key itself: our display choice, not the game's text
        for a miss (D2's placeholder, F1's index 5382 for an excel cell, a rare name's raw key in parentheses)."""
        lng = os.path.join(root, "data", "local", "lng", "eng")
        S = tbl.Strings(lng) if os.path.isdir(lng) else None

        def disp(key):
            if S is None or not key:
                return key
            i = S.index(key)
            t = None if i == tbl.NOT_FOUND else S.text(i)
            return t if t else key
        for lst in (self.AT.uniq, self.AT.setit, self.AT.magic, self.AT.rare):
            for r in lst:
                r["disp"] = disp(r["name"])

    def __init__(self, root):
        self.root = root
        self.excel = os.path.join(root, "data", "global", "excel")
        self.T = tc.Tables(self.excel)
        self.QT = quality.Tables(self.excel)
        affixes.STAFF_MODEL = True
        affixes.PROPS_HOOK = items_chain.make_hook(props.Tables(self.excel))
        self.AT = affixes.Tables(self.excel)
        self.add_display_names(root)
        # affix colour byte (+0x56) in the order of AT.magic: magicsuffix, magicprefix, automagic (items/0003 [I])
        self.acol = []
        for t in ("magicsuffix", "magicprefix", "automagic"):
            self.acol += [r[0x56] for r in tc.recs(self.excel, t)]
        self.mon_ids, self.su = [], []
        h, rows = excel_bin.read_txt(excel_bin.find_file(self.excel, "monstats", ".txt"))
        self.mon_ids = [r[0] for r in rows]
        h, rows = excel_bin.read_txt(excel_bin.find_file(self.excel, "superuniques", ".txt"))
        k = h.index("Superunique")
        c = h.index("Class")
        self.su = [(r[k], r[c]) for r in rows if r and r[0] and r[0] != "Expansion"]

    def item_name(self, idx):
        return self.T.items[idx]["code"].strip()


# ---------------------------------------------------------------- one item's creation (uniques.py + affixes.py)

class RecWalk(affixes.Walk):
    """affixes.Walk that also keeps every pick it makes (the model's own return values), for display."""

    def __init__(self, *a, **k):
        super().__init__(*a, **k)
        self.picks = []

    def pick(self, kind, spawn, must, apply, pre, forced=0, auto=0):
        aid, rec = super().pick(kind, spawn, must, apply, pre, forced, auto)
        self.picks.append((kind, pre, must, dict(rec), aid))
        return aid, rec


def run_builder(AT, ic, kind, q, seed, stats):
    """One builder of tools/affixes.py with no log lines (as tools/items_chain.free_builder). -> dict."""
    import collections
    it = affixes.Item(AT, ic)
    it.q = q
    W = RecWalk(AT, [], it, stats, collections.defaultdict(list), "chain", free=True)
    W.seed = seed
    W.rare_info = None
    before = dict(stats)
    ok = bool(getattr(W, affixes.BUILDERS[kind])())
    low = [k for k in stats if k.startswith("low row") and stats[k] != before.get(k, 0)]
    return dict(ok=ok, it=it, seed=W.seed, picks=W.picks, apr=W.apr, rare=W.rare_info, low=low)


def create_item(M, ic, start, made, emit=None):
    """ItemCreateByQuality's switch and fallback chain (uniques-sets.md B-F; tools/uniques.check_block for the
    unique and set builders, tools/items_chain.check_creation for the affix builders). ic: cls, ilvl, ver, rq (the
    quality the drop roll gave), rrow (the unique or set row + 1, else 0), rfl, g6a, ladder. start: item.start.
    emit(kind, **info) is called for every stage. Returns dict(q, row, it, seed, steps)."""
    import collections
    AT = M.AT
    S = start
    cur = (S, 666)
    stats = collections.Counter()
    b = AT.base(ic["cls"])
    q, fired = uniques.overrides(AT, ic["cls"], ic["rq"])
    emit and emit("override", rq=ic["rq"], q=q, fired=fired, seed=cur)
    out = dict(q=q, row=-1, it=None, seed=None, steps=[], tried=[])
    ok = None
    if q == 7:
        cands, total = uniques.unique_cands(AT, b, ic)
        forced = ic["rrow"] - 1 if ic["rrow"] and any(c[0] == ic["rrow"] - 1 for c in cands) else -1
        info = dict(kind="unique", n=len(cands), total=total, forced=forced, cands=cands, seed_in=cur, r=None, seed_out=cur)
        if not cands:
            ok, row = bool(b["unique"]), -1
            info.update(exit="no-candidate", row=row)
        else:
            r = None
            if forced < 0:
                lo, hi = rng.step(*cur)
                r = lo % total
                cur = (lo, hi)
                c = 1
                while c < len(cands) and r >= cands[c][1]:
                    c += 1
                row = cands[c - 1][0]
            else:
                row = forced
            info.update(r=r, row=row, seed_out=cur)
            if not b["quest"] and (row > 0x1000 or row in made):
                ok = False
                info["exit"] = "made"
            else:
                ok = True
                if not AT.uniq[row]["flags"] & 2:
                    made.add(row)
                info["exit"] = "row"
        out["row"] = row if ok else -1
        emit and emit("pick7", ok=ok, **info)
        if ok:
            out.update(it=None, seed=cur)
            return out
        chain = ["rare", "magic", "superior", "normal"]
    elif q == 5:
        cands, total = uniques.set_cands(AT, b, ic)
        forced = ic["rrow"] - 1 if ic["rrow"] and any(c[0] == ic["rrow"] - 1 for c in cands) else -1
        info = dict(kind="set", n=len(cands), total=total, forced=forced, cands=cands, seed_in=cur)
        row, r = -1, None
        if forced >= 0:
            row = forced
        elif total == 0:
            info["exit"] = "no-candidate"
        else:
            r, cur = uniques.rng_range_b(cur, total)
            rr = r
            for c in cands:
                if rr < c[1]:
                    row = c[0]
                    break
                rr -= c[1]
            if row < 0:
                info["exit"] = "walk-off"
        ok = row >= 0
        if ok:
            info["exit"] = "row"
        info.update(r=r, row=row, seed_out=cur)
        out["row"] = row if ok else -1
        emit and emit("pick5", ok=ok, **info)
        if ok:
            out.update(it=None, seed=cur)
            return out
        chain = ["magic", "superior", "normal"]
    else:
        first = uniques.FIRST[q]
        chain = list(uniques.CHAIN.get(q, []))
        if first == "normalcase":
            first = "normal"
        res = run_builder(AT, ic, first, q, cur, stats)
        out["tried"].append((first, q, res))
        emit and emit("build", kind=first, q=q, res=res, seed_in=cur)
        if res["ok"] or first == "normal":
            out.update(it=res["it"], seed=res["seed"], q=q)
            return out
    # the fallback chain: every step reseeds {S, 666}
    for k in chain:
        cur = (S, 666)
        qq = uniques.STEPQ[k]
        res = run_builder(AT, ic, k, qq, cur, stats)
        out["tried"].append((k, qq, res))
        emit and emit("build", kind=k, q=qq, res=res, seed_in=cur, fallback=True)
        out["steps"].append(k)
        if res["ok"] or k == "normal":
            out.update(it=res["it"], seed=res["seed"], q=qq)
            return out
    raise RuntimeError("fallback chain ended without a result")


# ---------------------------------------------------------------- the resolver (tc.replay_call, expansion branch, no log)

def resolve(M, root_tc, ilvl, seed, mx=0, nonodrop=False, party=1, players=1, cap=None, mf=0, bits=53, fq=0,
            hook=None):
    """The expansion branch of tc.replay_call (tc.md D-H) on its own seed. hook(kind, **info) is called at every stage
    (None: plain run). Returns dict(count, seed, picks, items) with items = [(index, quality, uidx, up)]."""
    T, QT = M.T, M.QT
    lo, hi = seed
    h = hook or (lambda *a, **k: None)
    mx = 6 if mx < 1 else mx
    t0 = T.tcs[root_tc]
    frames = [dict(tc=root_tc, left=max(1, abs(t0["picks"])), ratio=list(t0["ratio"]))]
    cur = 0
    count = picks = 0
    items = []
    h("start", frames=frames, cur=cur)
    while True:
        f = frames[cur]
        t = T.tcs[f["tc"]] if f["tc"] else None
        if t and t["texp"]:
            while frames[cur]["left"]:
                f = frames[cur]
                t = T.tcs[f["tc"]]
                total = t["texp"]
                if not total:
                    break
                info = dict(tc=f["tc"], total=total, nd0=t["nodrop"], nd=t["nodrop"], n=1, picks=t["picks"],
                            left=f["left"])
                if t["picks"] < 0:
                    roll = abs(t["picks"]) - f["left"]
                    info.update(neg=True, roll=roll)
                    if roll >= total:
                        h("negstop", frames=frames, cur=cur, **info)
                        break
                else:
                    nd = t["nodrop"]
                    if nd:
                        if isinstance(party, list):       # selftest: the logged PARTY / PLAYERS of each scaled pick
                            pty, ply = party.pop(0), players.pop(0)
                        else:
                            pty, ply = party, players
                        d = ply - pty
                        n = pty + (abs(d) // 2) * (1 if d >= 0 else -1)
                        if cap is not None:
                            n = min(n, cap)
                        info["n"] = n
                        if n > 1:
                            nd = tc.nodrop_scaled(nd, total, n, bits)
                        info["nd"] = nd
                    rng_n = total if nonodrop else total + nd
                    roll, lo, hi = rng.rng_range(lo, hi, rng_n & M32)
                    picks += 1
                    info.update(neg=False, roll=roll, range=rng_n, seed=(lo, hi))
                    if not nonodrop and roll < nd:
                        f["left"] -= 1
                        h("nodrop", frames=frames, cur=cur, **info)
                        continue
                    if not nonodrop:
                        roll -= nd
                    info["eroll"] = roll
                f["left"] -= 1
                ents = t["entries"]
                i = next((k for k in range(len(ents)) if ents[k]["cume"] <= roll < ents[k]["cume"] + ents[k]["prob"]), 0)
                info["i"] = i
                if i >= len(ents):
                    h("miss", frames=frames, cur=cur, **info)
                    continue
                e = ents[i]
                info["e"] = e
                if e["flags"] & tc.F_TC:
                    sub = e["index"]
                    parent = cur
                    if f["left"] > 0:
                        cur += 1
                    stc = T.tcs[sub]
                    pr = frames[parent]["ratio"]
                    nr = [stc["ratio"][k] if (pr[k] == 0 or stc["ratio"][k] > pr[k]) else pr[k] for k in range(6)]
                    fr = dict(tc=sub, left=max(1, abs(stc["picks"])), ratio=nr)
                    if cur < len(frames):
                        frames[cur] = fr
                    else:
                        frames.append(fr)
                    h("push", frames=frames, cur=cur, sub=sub, tail=(cur == parent), **info)
                    continue
                if e["index"] == 0xFFFF:
                    h("ffff", frames=frames, cur=cur, **info)
                    continue
                h("pick", frames=frames, cur=cur, **info)
                if e["flags"] & tc.F_UNIQUE:
                    q, uidx = 7, e["aux"] + 1
                    h("qforced", q=q, uidx=uidx, what="unique entry", item=e["index"])
                elif e["flags"] & tc.F_SET:
                    q, uidx = 5, e["aux"] + 1
                    h("qforced", q=q, uidx=uidx, what="set entry", item=e["index"])
                else:
                    uidx = 0
                    if fq:
                        q = fq
                        h("qforced", q=q, uidx=0, what="forced quality", item=e["index"])
                    else:
                        pre = []
                        tr = []
                        mfi = mf.pop(0) if isinstance(mf, list) else mf      # selftest: the logged QMF of each roll
                        q, (lo2, hi2), why, ndraw, ri = quality.roll(QT, e["index"], ilvl, f["ratio"], (lo, hi), mfi,
                                                                    False, trace=tr, cf={"pre": pre})
                        h("quality", item=e["index"], ilvl=ilvl, ratio=list(f["ratio"]), seed_in=(lo, hi),
                          seed_out=(lo2, hi2), mf=mfi, q=q, why=why, ndraw=ndraw, ri=ri, trace=tr, pre=pre)
                        lo, hi = lo2, hi2
                up = 0
                for k, bit in ((4, 0x04), (5, 0x10)):
                    if f["ratio"][k]:
                        lo, hi = rng.step(lo, hi)
                        h("upgrade", k=k, low=lo, ratio=f["ratio"][k], seed=(lo, hi))
                        if (lo & 0x3FF) < f["ratio"][k]:
                            up |= bit
                items.append((e["index"], q, uidx, up))
                h("create", index=e["index"], q=q, uidx=uidx, up=up, seed=(lo, hi), n=len(items), e=e)
                count += 1
                if count >= mx:
                    h("max", count=count, mx=mx)
                    break
            if count >= mx:
                break
        if cur == 0:
            break
        cur -= 1
        h("pop", frames=frames, cur=cur)
    return dict(count=count, seed=(lo, hi), picks=picks, items=items)


# ---------------------------------------------------------------- source: monster / superunique / TC

def find_source(M, name, diff, kind, mlvl):
    """-> dict(label, root, base, lvl_gate, ilvl, notes, mflags) per tc.md B-C."""
    T = M.T
    low = name.lower()
    notes = []
    if low in (i.lower() for i in M.mon_ids) or any(s[0].lower() == low for s in M.su):
        su = next((k for k, s in enumerate(M.su) if s[0].lower() == low), None)
        if su is not None and low not in (i.lower() for i in M.mon_ids):
            cls = [i.lower() for i in M.mon_ids].index(M.su[su][1].lower())
            kind = "superunique"
        else:
            cls = [i.lower() for i in M.mon_ids].index(low)
            su = None
        rec = T.monstats(cls)
        col = lambda k: struct.unpack_from("<H", rec, 0x86 + 8 * diff + 2 * k)[0]  # noqa: E731
        if kind == "superunique":
            base, why = T.superunique_tc(su, diff) or col(2), "Superuniques TC column of the difficulty (tc.md B2)"
        elif kind == "champion":
            base, why = col(1), "MonStats TreasureClass2 of the difficulty (tc.md B3)"
        elif kind == "unique":
            base, why = col(2), "MonStats TreasureClass3 of the difficulty (tc.md B4)"
        else:
            base, why = col(0), "MonStats TreasureClass1 of the difficulty (tc.md B5)"
        gate = diff > 0 and not rec[0x0C] & 0x04 and not rec[0x0C] & 0x40
        lvl_default = struct.unpack_from("<H", rec, 0xAA + 2 * diff)[0]
        if mlvl is None:
            mlvl = max(1, lvl_default)
            notes.append("monster level %d = MonStats Level column of the difficulty (tc.md B1: ilvl = the monster's "
                         "stat 12); the game takes Levels.MonLvl*Ex for non-boss monsters in expansion Nightmare/Hell: "
                         "not modelled here (--mlvl overrides)" % mlvl)
        if rec[0x9E] and col(3):
            notes.append("quest TC (TreasureClass4, tc.md B6) needs the killer's quest state: not modelled here")
        return dict(label="%s%s" % (M.su[su][0] if su is not None else M.mon_ids[cls],
                                    "" if kind == "normal" or su is not None else " (%s)" % kind),
                    base=base, why=why, gate=gate, ilvl=mlvl, notes=notes, rec=rec,
                    boss=bool(rec[0x0C] & 0x40), noratio=bool(rec[0x0C] & 4), kind=kind, monster=True)
    idx = T.names.get(low)
    if idx is None:
        raise SystemExit("no MonStats Id, Superuniques name or TreasureClassEx name %r" % name)
    if mlvl is None:
        mlvl = 50
        notes.append("item level 50: input default (--mlvl); a TC named directly has no source monster")
    return dict(label=T.tcs[idx]["name"], base=idx, why="named directly, no monster (tc.md Entry points)", gate=False,
                ilvl=mlvl, notes=notes, kind="tc", monster=False)


# ---------------------------------------------------------------- icons (items/0003)

class Icons:
    def __init__(self, M):
        self.M = M
        root = M.root
        self.units = pal.load(root, "units")
        self.codes = pal.colour_codes(root)
        self.maps = {n: pal.item_shift_maps(root, n) for n in pal.ITEM_SHIFT_FILES}
        tmp = os.path.join(anim_common.safe_out(os.path.join(HERE, "..", "workspace", "render", "anim")), "_tmp")
        os.makedirs(tmp, exist_ok=True)
        d = tempfile.mkdtemp(dir=tmp)
        path = os.path.join(d, "index.tsv")
        import contextlib
        import io
        with contextlib.redirect_stdout(io.StringIO()):
            item_art.cmd_index(root, path)
        with open(path, encoding="latin-1") as fh:
            head = fh.readline().rstrip("\n").split("\t")
            rows = [dict(zip(head, ln.rstrip("\n").split("\t"))) for ln in fh]
        for f in os.listdir(d):
            os.unlink(os.path.join(d, f))
        os.rmdir(d)
        self.base, self.uniq, self.setit = {}, {}, {}
        for r in rows:
            if r["kind"] in ("weapons", "armor", "misc"):
                self.base.setdefault(r["id"].strip(), r)
            elif r["kind"] == "uniqueitems":
                self.uniq[int(r["row"])] = r
            elif r["kind"] == "setitems":
                self.setit[int(r["row"])] = r

    def line(self, code, q, row):
        if q == 7 and row in self.uniq:
            return self.uniq[row]
        if q == 5 and row in self.setit:
            return self.setit[row]
        return self.base.get(code.strip())

    def colour_of(self, q, it):
        """The affix colour code of a magic or rare item (items/0003 [I]): the first suffix slot, then prefix slot,
        whose affix record byte +0x56 is not 0xFF; None otherwise."""
        if it is None or q not in (4, 6):
            return None
        for lst in (it.s, it.p):
            for a in lst:
                if a and self.M.acol[a - 1] != 0xFF:
                    return self.M.acol[a - 1]
        return None

    def render(self, code, q, row, it):
        """-> (w, h, rgb pixel list or None, note)."""
        r = self.line(code, q, row)
        if r is None or r["inv_status"] != "ok":
            return None, "no inventory art"
        d = dc6.parse(open(os.path.join(self.M.root, r["inv_dc6"]), "rb").read())
        f = d["frames"][0]
        px = dc6.frame_pixels(f)
        note = "base InvTrans %s" % (r["base_invtrans"] or "-")
        rgb = self.units
        cc = None
        if q in (5, 7):
            cc = r["invtransform"] or None
        else:
            c = self.colour_of(q, it)
            if c is not None and c < len(self.codes):
                cc = self.codes[c]
        if cc:
            what, remap = item_art.shift_map(r["base_invtrans"], cc, self.codes, self.maps)
            if remap is not None:
                rgb = pal.shift_rgb(self.units, remap)
                note = "shift %s, colour %s" % (what, cc)
            else:
                note = "no shift (%s)" % what
        return (f["width"], f["height"], px, rgb), note


# ---------------------------------------------------------------- canvas with a growing palette

class Canvas:
    UI = dict(bg=(16, 16, 22), panel=(30, 30, 40), txt=(225, 225, 225), dim=(130, 130, 145), acc=(240, 210, 80),
              good=(70, 200, 90), bad=(215, 70, 70), blue=(90, 140, 255), cur=(60, 60, 95), grey=(70, 70, 80),
              q_low=(150, 150, 150), q_normal=(235, 235, 235), q_superior=(200, 200, 200), q_magic=(110, 130, 255),
              q_set=(60, 220, 60), q_rare=(255, 240, 80), q_unique=(205, 160, 90), black=(0, 0, 0))

    def __init__(self, W, H):
        self.W, self.H = W, H
        self.pal = []
        self.near = {}
        self.C = {k: self.alloc(v) for k, v in self.UI.items()}
        self.frozen = False

    def alloc(self, rgb):
        rgb = tuple(rgb)
        if rgb in self.near:
            return self.near[rgb]
        if len(self.pal) < 256:
            self.pal.append(rgb)
            i = len(self.pal) - 1
        else:
            i = min(range(len(self.pal)), key=lambda j: sum((self.pal[j][c] - rgb[c]) ** 2 for c in range(3)))
        self.near[rgb] = i
        return i

    def new(self):
        self.cv = bytearray([self.C["bg"]]) * (self.W * self.H)
        return self.cv

    def rect(self, x, y, w, h, col):
        for yy in range(max(0, y), min(self.H, y + h)):
            a, b = max(0, x), min(self.W, x + w)
            if a < b:
                self.cv[yy * self.W + a:yy * self.W + b] = bytes([col]) * (b - a)

    def frame_rect(self, x, y, w, h, col, t=1):
        self.rect(x, y, w, t, col)
        self.rect(x, y + h - t, w, t, col)
        self.rect(x, y, t, h, col)
        self.rect(x + w - t, y, t, h, col)

    def text(self, x, y, s, col, sc=2, bold=False):
        anim_common.text(self.cv, self.W, self.H, x, y, s, col, sc)
        if bold:
            anim_common.text(self.cv, self.W, self.H, x + 1, y, s, col, sc)

    def icon(self, x, y, ic, scale):
        w, h, px, rgb = ic
        for yy in range(h):
            for xx in range(w):
                v = px[yy * w + xx]
                if not v:
                    continue
                i = self.alloc(rgb[3 * v:3 * v + 3])
                self.rect(x + xx * scale, y + yy * scale, scale, scale, i)

    def prealloc(self, ic):
        w, h, px, rgb = ic
        for v in sorted(set(px)):
            if v:
                self.alloc(rgb[3 * v:3 * v + 3])

    def palette(self):
        p = bytearray()
        for c in self.pal:
            p += bytes(c)
        return bytes(p) + bytes(768 - len(p))


# ---------------------------------------------------------------- building the steps

def fseed(s):
    return "%08x:%08x" % s


class Anim:
    def __init__(self, M, src, seed, diff, players, mf, mx):
        self.M, self.src, self.seed, self.diff = M, src, seed, diff
        self.players, self.mf, self.mx = players, mf, mx
        self.steps = []
        self.view = dict(stack=[], cur=-1, log=[], dropped=[], item=None, items_done=0)
        self.made = set()
        self.gseed = ((seed * 0x9E3779B1 + 1) & M32, 666)
        if not hasattr(M, "_icons"):
            M._icons = Icons(M)
        self.icons = M._icons
        self.pending_icons = []

    # state ------------------------------------------------------
    def S(self, text, calc, **upd):
        self.view.update(upd)
        self.steps.append(dict(text=text, calc=list(calc), view=copy.deepcopy(self.view)))

    def tcname(self, i):
        return self.M.T.tcs[i]["name"]

    def stack_view(self, frames, cur):
        T = self.M.T
        out = []
        for k in range(cur + 1):
            f = frames[k]
            t = T.tcs[f["tc"]]
            out.append(dict(name=t["name"], left=f["left"], picks=abs(t["picks"]), neg=t["picks"] < 0,
                            nd=t["nodrop"], total=t["texp"]))
        return out

    def logline(self, s):
        self.view["log"].append(s)
        del self.view["log"][:-8]

    def iname(self, idx):
        c = self.M.T.items[idx]["code"].strip()
        r = self.icons.base.get(c)
        return (r["name"] if r else c), c

    # hook of resolve() ------------------------------------------
    def hook(self, kind, **k):
        T = self.M.T
        if kind == "start":
            t0 = T.tcs[k["frames"][0]["tc"]]
            self.S("The resolver starts at '%s': %d pick%s, NoDrop %d, expansion total %d."
                   % (t0["name"], abs(t0["picks"]), "" if abs(t0["picks"]) == 1 else "s", t0["nodrop"], t0["texp"]),
                   ["tc.md D1: frame 0 = {TC, picksLeft = max(1, |Picks|), the TC's ratio words}; max = 6 for a monster "
                    "drop (max 0 becomes 6).",
                    "'%s': Picks %d (a negative Picks takes every entry in order with no draw, tc.md D3), NoDrop %d, "
                    "%d entries, total %d (tc.md A)." % (t0["name"], t0["picks"], t0["nodrop"], len(t0["entries"]), t0["texp"]),
                    "All draws below are on the source unit's seed {%s}, one Step per draw (tc.md D4)."
                    % fseed(self.src_seed)],
                   stack=self.stack_view(k["frames"], 0), cur=0)
            return
        if kind in ("nodrop", "pick", "push", "negstop", "miss", "ffff"):
            self.pick_step(kind, k)
            return
        if kind == "pop":
            self.view.update(stack=self.stack_view(k["frames"], k["cur"]), cur=k["cur"])
            return
        if kind == "max":
            self.S("%d items dropped: the Resolve call ends (max %d)." % (k["count"], k["mx"]),
                   ["tc.md H8: count = count + 1; count >= max ends the whole Resolve call (every frame)."])
            return
        self.item_hook(kind, k)

    def pick_step(self, kind, k):
        T = self.M.T
        t = T.tcs[k["tc"]]
        nm = t["name"]
        calc = []
        if k.get("neg"):
            calc.append("tc.md D3: Picks < 0: roll = |Picks| - picksLeft = %d - %d = %d, no draw." % (
                abs(t["picks"]), k["left"], k["roll"]))
            if kind == "negstop":
                calc.append("tc.md D3: roll >= total (%d >= %d) abandons this frame." % (k["roll"], k["total"]))
                self.S("Negative picks of '%s': roll %d >= total %d, the frame is abandoned." % (nm, k["roll"], k["total"]),
                       calc)
                return
            calc.append("tc.md E1: entry i with cumExp_i <= roll < cumExp_i + Prob_i; total %d." % k["total"])
            head = "Pick %d of '%s' (fixed, no draw): roll %d" % (abs(t["picks"]) - k["left"] + 1, nm, k["roll"])
        else:
            if t["nodrop"]:
                if k["n"] > 1:
                    calc.append("tc.md F2: n = party + (PlayerCount - party) / 2 = %d; n > 1 so NoDrop is scaled "
                                "(x87, 53-bit; tc.md F4): NoDrop %d, total %d -> NoDrop' %d."
                                % (k["n"], k["nd0"], k["total"], k["nd"]))
                else:
                    calc.append("tc.md F2: n = party + (PlayerCount - party) / 2 = %d; n <= 1: NoDrop stays %d."
                                % (k["n"], k["nd"]))
            else:
                calc.append("tc.md D4: NoDrop 0: the range is the total %d." % k["total"])
            calc.append("tc.md D4: roll = Range(src.seed, total + NoDrop' = %d) = %d; seed after {%s}."
                        % (k["range"], k["roll"], fseed(k["seed"])))
            if kind == "nodrop":
                calc.append("tc.md D4: roll %d < NoDrop' %d: a NoDrop, the pick is consumed, nothing drops."
                            % (k["roll"], k["nd"]))
                self.logline("%s: roll %d < NoDrop' %d -> NoDrop" % (nm, k["roll"], k["nd"]))
                self.S("NoDrop: roll %d of %d is below NoDrop' %d in '%s'." % (k["roll"], k["range"], k["nd"], nm),
                       calc, stack=self.stack_view(k["frames"], k["cur"]), cur=k["cur"])
                return
            calc.append("tc.md D4: roll - NoDrop' = %d - %d = %d, in 0..%d." % (k["roll"], k["nd"], k["eroll"], k["total"] - 1))
            calc.append("tc.md E1: entry i with cumExp_i <= roll < cumExp_i + Prob_i.")
            head = "Pick in '%s': roll %d of %d" % (nm, k["roll"], k["range"])
        if kind == "miss":
            self.S(head + " selects no entry.", calc)
            return
        e = k["e"]
        sel = T.tcs[e["index"]]["name"] if e["flags"] & tc.F_TC else self.iname(e["index"])[0]
        calc.append("Entry %d: %s, Prob %d, cumExp %d (tc.md E1)." % (k["i"], sel, e["prob"], e["cume"]))
        self.logline("%s: roll %s -> %s" % (nm, k["roll"], sel))
        if kind == "push":
            stc = T.tcs[k["sub"]]
            calc.append("tc.md G: the entry is a TC (flag 0x04): the pick is consumed and the resolver %s the sub-TC '%s' "
                        "(%d picks, NoDrop %d); its ratio words become the max of the two frames."
                        % ("tail-continues into" if k["tail"] else "pushes a frame for", stc["name"],
                           abs(stc["picks"]), stc["nodrop"]))
            self.S(head + " -> sub-TC '%s'." % stc["name"], calc, stack=self.stack_view(k["frames"], k["cur"]),
                   cur=k["cur"])
            return
        if kind == "ffff":
            self.S(head + " -> an empty entry (index 0xFFFF).", calc)
            return
        calc.append("tc.md H1: an item entry: quality roll, creation (H4-H7).")
        self.S(head + " -> item '%s'." % sel, calc, stack=self.stack_view(k["frames"], k["cur"]), cur=k["cur"])

    # items ------------------------------------------------------
    def item_hook(self, kind, k):
        T = self.M.T
        v = self.view
        if kind == "qforced":
            nm, code = self.iname(k["item"])
            v["item"] = dict(name=nm, code=code, ilvl=self.src_ilvl, chain=[[n, None, None, "skip"] for n in CHAIN6],
                             build=[], q=k["q"], title="")
            self.S("Quality %d (%s) is fixed by a %s: no quality roll." % (k["q"], QNAME.get(k["q"], k["q"]), k["what"]),
                   ["tc.md H4: a unique entry (flag 0x01) takes quality 7 and uidx = aux + 1, a set entry (0x02) "
                    "quality 5, with no draw; forcedQ takes quality forcedQ."])
            return
        if kind == "quality":
            self.quality_steps(k)
            return
        if kind == "upgrade":
            self.S("Upgrade draw %d: low word %#x & 0x3FF %s ratio word %d." % (
                k["k"], k["low"], "<" if (k["low"] & 0x3FF) < k["ratio"] else ">=", k["ratio"]),
                ["tc.md H5: a non-zero ratio word 4 or 5 draws one Step on src.seed; (low & 0x3FF) < ratio sets flag "
                 "0x04 (forced ethereal) or 0x10 (forced sockets)."])
            return
        if kind == "create":
            self.create_steps(k)

    def quality_steps(self, k):
        T, QT = self.M.T, self.M.QT
        nm, code = self.iname(k["item"])
        v = self.view
        chain = [[n, None, None, "untested"] for n in CHAIN6]
        v["item"] = dict(name=nm, code=code, ilvl=self.src_ilvl, chain=chain, build=[], q=None, title="")
        r = QT.items[k["item"]]
        qlvl = r[0xFD]
        head = ["quality.md Inputs: item '%s' (qlvl %d), ilvl %d, TC frame ratio words %s, magic find %d, source seed {%s}."
                % (code, qlvl, k["ilvl"], k["ratio"], k["mf"], fseed(k["seed_in"]))]
        if not k["trace"] and k["ri"] is None:
            why = k["why"]
            expl = {"normal-type": "the item type's Normal flag is set: quality 2",
                    "unique-flag": "the base has the unique flag: quality 7",
                    "magic-type-quest": "type Magic and a quest base: quality 7"}.get(why, why)
            chain[-1][3] = "skip"
            v["item"]["q"] = k["q"]
            self.S("Quality roll for '%s': early return, %s (quality %d)." % (nm, expl, k["q"]),
                   head + ["quality.md A: early returns draw nothing and read no itemratio row (%s)." % why])
            return
        calc0 = head + ["quality.md B: ITEMRATIO_Select picks itemratio row %d (version argument 100); "
                        "d = ilvl - qlvl = %d - %d = %d (quality.md C)." % (k["ri"], k["ilvl"], qlvl, k["ilvl"] - qlvl)]
        pre = {p[0]: p for p in k["pre"]}
        last_name = None
        for (name, c, x, won) in k["trace"]:
            idx = CHAIN6.index(name)
            for j in range(idx):
                if chain[j][3] == "untested":
                    chain[j][3] = "skip"
            chain[idx][1], chain[idx][2], chain[idx][3] = c, x, "won" if won else "lost"
            p = pre.get(name)
            calc = list(calc0)
            if p:
                calc.append("quality.md D4-D7: the chance after the base term and magic find (%d) is raised to the row "
                            "minimum %d when not above it (D6), then c - ratio word %d x c / 1024 (D7) = %d."
                            % (p[1], p[2], p[3], c))
            if x is None:
                calc.append("quality.md D: chance %d < 1: the test is won with no draw." % c)
            else:
                calc.append("quality.md D: draw RangeB(src.seed, chance %d) = %d; the test is won when the draw < 128: %s."
                            % (c, x, "won" if won else "lost"))
            last_name = name
            self.S("%s test for '%s': chance %d%s -> %s." % (
                name.capitalize(), nm, c, "" if x is None else ", draw %d" % x, "won" if won else "lost"), calc,
                   item=v["item"])
        if k["q"] == 4 and not any(t[0] == "magic" and t[3] for t in k["trace"]):
            for j, n in enumerate(CHAIN6):
                if chain[j][3] == "untested":
                    chain[j][3] = "skip"
        v["item"]["q"] = k["q"]
        for j in range(6):
            if chain[j][3] == "untested":
                chain[j][3] = "skip"
        self.S("Quality %d (%s) for '%s' after %d draw%s; source seed now {%s}." % (
            k["q"], QNAME[k["q"]], nm, k["ndraw"], "" if k["ndraw"] == 1 else "s", fseed(k["seed_out"])),
            calc0 + ["quality.md Test order: unique, set, rare, magic, superior, then normal or low; a won test ends the "
                     "roll (exit label %s)." % k["why"],
                     "quality.md Draw order: %d draw%s on src.seed, seed after {%s}." % (
                         k["ndraw"], "" if k["ndraw"] == 1 else "s", fseed(k["seed_out"]))], item=v["item"])

    def create_steps(self, k):
        M = self.M
        AT = M.AT
        v = self.view
        itm = v["item"]
        nm, code = self.iname(k["index"])
        # the item seed: two game-seed steps, unit seed then item start (uniques-sets.md A1-A2)
        g = rng.step(*self.gseed)
        g = rng.step(*g)
        self.gseed = g
        start = g[0]
        ic = dict(cls=k["index"], ilvl=self.src_ilvl, ver=101, rq=k["q"], rrow=k["uidx"], rfl=0, g6a=3, ladder=0)
        gcalc = ["uniques-sets.md A1-A2: DropCreateItem draws two Steps on the game seed (unit seed, then item.start); "
                 "item.seed = {start, 666} = {%08x, 666}. The game seed here is derived from the illustrative input." % start,
                 "tc.md H7: creation does not touch src.seed (seed stays {%s})." % fseed(k["seed"]),
                 "Creation record as logged for drops: item version 101, Game+0x6A 3, ladder 0, record quality %d, "
                 "record row %d (uniques-sets.md A, B)." % (k["q"], k["uidx"])]
        itm["build"] = []
        self.S("Item creation for '%s' (quality %d, %s): item seed {%08x:%08x}." % (nm, k["q"], QNAME[k["q"]], start, 666),
               gcalc, item=itm)
        events = []
        res = create_item(M, ic, start, self.made, emit=lambda ev_, **i: events.append((ev_, i)))
        for kind, i in events:
            self.build_step(kind, i, nm, ic, itm)
        # the finished item
        q = res["q"]
        row = res["row"]
        it = res["it"]
        title, detail = self.describe(nm, q, row, it, res)
        icon, inote = self.icons.render(code, q, row if q in (5, 7) else -1, it)
        if icon:
            self.pending_icons.append(icon)
        entry = dict(name=title, base=nm, q=q, detail=detail, icon=len(self.pending_icons) - 1 if icon else None,
                     note=inote)
        itm["q"] = q
        itm["title"] = title
        v["dropped"].append(entry)
        itm["done"] = True
        self.S("Item complete: %s." % title,
               ["Result of the model: quality %d (%s)%s." % (q, QNAME.get(q, q), "" if not res["steps"] else
                                                          ", reached by the fallback chain %s (uniques-sets.md E)" % " -> ".join(res["steps"])),
                "Inventory icon: %s (items/0003: the identified view; magic and rare items take the first affix colour, "
                "unique and set items their invtransform colour)." % inote,
                "Not modelled here: gold amount and gold find (tc.md H8-H9), ItemInitStats values, the ethereal and socket rolls, the automagic pick after them "
                "(affixes.md J), the durability fix of a failed unique or set, property values."],
               item=itm)

    def describe(self, nm, q, row, it, res):
        AT = self.M.AT
        if q == 7 and row >= 0:
            return AT.uniq[row]["disp"], "unique row %d of %s" % (row, nm)
        if q == 5 and row >= 0:
            return AT.setit[row]["disp"], "set row %d of %s" % (row, nm)
        if it is None:
            return nm, QNAME.get(q, str(q))
        ps = [AT.magic[a - 1]["disp"] for a in it.p if a]
        ss = [AT.magic[a - 1]["disp"] for a in it.s if a]
        if q == 6:
            ri = res["tried"][-1][2]["rare"]
            if ri:
                n1, n2 = AT.rare[ri["n1"] - 1]["disp"], AT.rare[ri["n2"] - 1]["disp"]
                return "%s %s" % (n1, n2), "rare %s: prefixes %s, suffixes %s" % (nm, ps, ss)
        if q == 4:
            return "%s%s%s" % (ps[0] + " " if ps else "", nm, " " + ss[0] if ss else ""), "magic: prefix %s, suffix %s" % (
                ps, ss)
        return ("Superior " if q == 3 else "Low quality " if q == 1 else "") + nm, "%s %s" % (QNAME.get(q, q), nm)

    def build_step(self, kind, i, nm, ic, itm):
        AT = self.M.AT
        if kind == "override":
            if i["fired"] and i["q"] != i["rq"]:
                self.S("Pre-switch override: record quality %d becomes %d (%s)." % (i["rq"], i["q"], ", ".join(i["fired"])),
                       ["uniques-sets.md B: the four overrides in order (ItemTypes Magic, Rare = 0 and 6, the base's unique "
                        "flag, ItemTypes Normal) rewrite the record quality before the switch; fired: %s." % ", ".join(i["fired"])],
                       item=itm)
            return
        if kind in ("pick7", "pick5"):
            sec = "C" if kind == "pick7" else "D"
            what = "unique" if kind == "pick7" else "set"
            filt = ("version, enabled, code '%s', ladder, level <= ilvl %d" if what == "unique" else
                    "version, level <= ilvl %d, code '%s'")
            fa = (AT.base(ic["cls"])["name"], ic["ilvl"]) if what == "unique" else (ic["ilvl"], AT.base(ic["cls"])["name"])
            calc = ["uniques-sets.md %s: candidates in table order (%s); weight = %s; %d candidate%s, total weight %d." % (
                        sec, filt % fa, "max(1, rarity)" if what == "unique" else "rarity, 1 when it is 0",
                        i["n"], "" if i["n"] == 1 else "s", i["total"])]
            if i["n"]:
                calc.append("Candidates (row: weight): " + ", ".join(
                    "%s" % (AT.uniq[c[0]]["disp"] if kind == "pick7" else AT.setit[c[0]]["disp"])
                    for c in i["cands"][:6]) + (" ..." if len(i["cands"]) > 6 else ""))
            if i["forced"] >= 0:
                calc.append("uniques-sets.md F: the record names row %d (a TC-named row), taken with no draw." % i["forced"])
            elif i["r"] is not None:
                calc.append("uniques-sets.md %s: one draw %s(item.seed, total %d) = %d; seed after {%s}." % (
                    sec, "lo %% total" if what == "unique" else "RangeB", i["total"], i["r"], fseed(i["seed_out"])))
            if i["ok"]:
                name = AT.uniq[i["row"]]["disp"] if what == "unique" else AT.setit[i["row"]]["disp"]
                calc.append("The %s builder returns row %d '%s'; its properties are applied to the item seed next "
                            "(not shown)." % (what, i["row"], name))
                itm["build"].append("%s row: %s" % (what, name))
                self.S("%s builder for '%s': row %d, '%s'." % (what.capitalize(), nm, i["row"], name), calc, item=itm)
            else:
                why = {"no-candidate": "no candidate", "made": "the unique was already made in this game",
                       "walk-off": "the draw walked off the candidates"}.get(i.get("exit"), i.get("exit"))
                calc.append("The %s builder fails (%s): the durability fix and the fallback chain follow "
                            "(uniques-sets.md E): %s." % (what, why, "rare, magic, superior, normal" if what == "unique"
                                                          else "magic, superior, normal"))
                itm["build"].append("%s builder failed: %s" % (what, why))
                self.S("%s builder for '%s' fails (%s)." % (what.capitalize(), nm, why), calc, item=itm)
            return
        res, kd, q = i["res"], i["kind"], i["q"]
        fb = i.get("fallback")
        pre = "Fallback step: reseed item seed to {S, 666}; " if fb else ""
        sec = {"magic": "D", "rare": "E", "superior": "F", "low": "G", "normal": "H"}[kd]
        calc = [pre + "affixes.md %s: the %s builder runs on item seed {%s}." % (sec, kd, fseed(i["seed_in"]))]
        if fb:
            calc.append("uniques-sets.md E: every fallback step starts from {S, 666}, S = the item start.")
        if kd == "rare" and res["rare"]:
            ri = res["rare"]
            AT_ = self.M.AT
            calc.append("affixes.md E: rare names first (prefix side, then suffix side): '%s' and '%s' (the RarePrefix / RareSuffix keys "
                        "shown as their string-table text, data/strings.md D and C); count %d "
                        "(table g_RareAffixCountTable[low & 7] after one Step, or 3 + Range(item.seed, 2) for a jewel)." % (
                            AT_.rare[ri["n1"] - 1]["disp"], AT_.rare[ri["n2"] - 1]["disp"], ri["count"]))
        shown = []
        for (kind2, pre2, must, rec, aid) in res["picks"]:
            nm_a = AT.magic[aid - 1]["disp"] if aid else "none"
            if rec.get("exit") == "no-roll":
                line = "%s pick (must %d): draw #1 bit 0 = 0, no affix" % ("prefix" if pre2 else "suffix", must)
                calc.append("affixes.md C: %s." % line)
            elif rec.get("exit") == "no-candidate":
                line = "%s pick: alvl %s, no candidate" % ("prefix" if pre2 else "suffix", rec.get("alvl"))
                calc.append("affixes.md C: %s." % line)
            else:
                line = "%s pick: alvl %s, %d candidates, W %d, draw %s -> %s" % (
                    "prefix" if pre2 else "suffix", rec.get("alvl"), rec.get("n", 0), rec.get("W", 0), rec.get("x"), nm_a)
                calc.append("affixes.md C: %s (alvl from ilvl and qlvl, filter, weights, draw #2 = low %% (W + 1))." % line)
            shown.append(line)
        if kd == "superior" and res["apr"]:
            calc.append("affixes.md F: QualityItems row %s drawn by rejection sampling, type test passed." % res["apr"][0][1])
            shown.append("QualityItems row %s" % res["apr"][0][1])
        if kd == "low":
            calc.append("affixes.md G: %s (RNG_Range(seed, nLow); success only for a weapon or armour)." %
                        (", ".join(res["low"]) or "no row"))
        if kd == "normal":
            calc.append("affixes.md H1: for a base other than a charm, body part, scroll or book the normal builder draws nothing "
                        "of its own on the item seed (a charm takes the forced-affix pair, an inferred path).")
        if kd == "magic" and len(res["picks"]) == 0:
            pass
        calc.append("Result: %s%s." % ("success" if res["ok"] else "failure", "" if not fb or res["ok"] else
                                       ", the next step of the chain follows"))
        calc.append("ItemApplyProps draws (property values) are applied to the seed by tools/props.py; the values are "
                    "not shown.")
        itm["build"] += ["%s%s: %s" % ("fallback " if fb else "", kd, s) for s in shown] or [
            "%s%s builder %s" % ("fallback " if fb else "", kd, "ok" if res["ok"] else "failed")]
        itm["build"] = itm["build"][-6:]
        self.S("%s%s builder for '%s': %s." % ("Fallback to the " if fb else "The ", kd, nm,
                                               "success" if res["ok"] else "fails"), calc, item=itm)

    # run -----------------------------------------------------------
    def run(self):
        src, M = self.src, self.M
        T = M.T
        self.src_ilvl = src["ilvl"]
        self.src_seed = (self.seed & M32, 666)
        notes = list(src["notes"])
        calc = ["Source: %s; difficulty %s; PlayerCount %d, party 1 (killer alone); magic find %d; expansion game."
                % (src["label"], DIFFN[self.diff], self.players, self.mf),
                "Seed %#x is an illustrative input: src.seed = {%s}; the game would derive it (rng/seeds)." %
                (self.seed, fseed(self.src_seed))] + notes
        self.S("Drop of %s in %s, seed %#x (illustrative input)." % (src["label"], DIFFN[self.diff], self.seed), calc)
        base = src["base"]
        lvl = src["ilvl"] if src["gate"] else 0
        if src["monster"]:
            self.S("Base TC: '%s'." % self.tcname(base),
                   ["tc.md B: %s -> TC %d '%s'." % (src["why"], base, self.tcname(base)),
                    "tc.md B1: ilvl = the monster's level (stat 12) = %d." % src["ilvl"]])
            gate = ("tc.md C1: the level upgrade gate is %s (expansion, difficulty > 0, monster source, not noRatio, not "
                    "boss): lvl = %d." % ("open" if src["gate"] else "closed", lvl))
        else:
            gate = "tc.md Entry points: a TC named directly is resolved as given; no level upgrade."
        t = T.get(base, lvl)
        if t is None:
            self.S("TC index 0: no drop.", [gate, "tc.md C2: index 0 returns none; Resolve is not called."])
            return
        calc = [gate]
        b = T.tcs[base]
        calc.append("tc.md C2: GetByIndex(%d '%s', lvl %d): while lvl >= the next TC's level in the same group, move to "
                    "the next TC (the base TC is kept even above lvl)." % (base, b["name"], lvl))
        self.S("Resolving TC '%s'%s." % (T.tcs[t]["name"], "" if t == base else " (walked up from '%s')" % b["name"]), calc)
        self.res = resolve(M, t, src["ilvl"], self.src_seed, mx=self.mx, party=1, players=self.players,
                           cap=self.players if src["monster"] else None, mf=self.mf, hook=self.hook)
        # prepare icons, then final frames
        n = len(self.res["items"])
        self.S("Drop finished: %d item%s after %d random picks." % (n, "" if n == 1 else "s", self.res["picks"]),
               ["tc.md D: the call returns count = %d with src.seed {%s}." % (n, fseed(self.res["seed"])),
                "Items: " + "; ".join(d["name"] for d in self.view["dropped"]) if n else "No item dropped."],
               item=None, final=True)


# ---------------------------------------------------------------- drawing

W, H = 1280, 720
QCOL = {1: "q_low", 2: "q_normal", 3: "q_superior", 4: "q_magic", 5: "q_set", 6: "q_rare", 7: "q_unique"}


def draw(cv, A, st, k, total):
    v = st["view"]
    C = cv.C
    cv.new()
    cv.text(10, 8, "%s  %s  SEED %#X  (ILLUSTRATIVE INPUT)" % (A.src["label"].upper(), DIFFN[A.diff].upper(), A.seed),
            C["dim"])
    # left: frame stack and log
    cv.rect(8, 32, 628, 360, C["panel"])
    cv.text(16, 38, "TREASURE CLASS STACK", C["acc"])
    y = 60
    for d, f in enumerate(v["stack"]):
        col = C["txt"] if d == v["cur"] else C["dim"]
        if d == v["cur"]:
            cv.rect(12, y - 2, 620, 20, C["cur"])
        s = "%s%s  %s%d/%d  ND %d  T %d" % ("  " * d, f["name"][:22].upper(), "FIXED " if f["neg"] else "PICKS ",
                                             f["left"], f["picks"], f["nd"], f["total"])
        cv.text(16, y, s[:50], col)
        y += 20
        if y > 230:
            break
    cv.text(16, 242, "LOG", C["acc"])
    for j, s in enumerate(v["log"]):
        cv.text(16, 262 + 16 * j, s.upper()[:50], C["txt"], 2 if False else 1)
    # right: current item
    cv.rect(646, 32, 626, 360, C["panel"])
    it = v["item"]
    cv.text(654, 38, "CURRENT ITEM", C["acc"])
    if it:
        title = (it["title"] or it["name"]).upper()
        cv.text(654, 60, "%s  ILVL %d" % (title[:34], it["ilvl"]), C[QCOL[it["q"]]] if it["q"] else C["txt"])
        x = 654
        for name, c, xx, state in it["chain"]:
            col = {"won": C["good"], "lost": C["bad"], "untested": C["grey"], "skip": C["panel"]}[state]
            cv.rect(x, 90, 94, 56, col if state != "skip" else C["bg"])
            cv.frame_rect(x, 90, 94, 56, C["dim"])
            cv.text(x + 4, 94, name[:8].upper(), C["txt"] if state != "skip" else C["dim"], 1)
            if c is not None:
                cv.text(x + 4, 108, "CH %d" % c, C["txt"], 1)
                cv.text(x + 4, 120, "ROLL %s" % ("-" if xx is None else xx), C["txt"], 1)
            cv.text(x + 4, 134, {"won": "WON", "lost": "LOST", "untested": "...", "skip": "-"}[state], C["txt"], 1)
            x += 99
        if it["q"]:
            cv.text(654, 156, "QUALITY %d  %s" % (it["q"], QNAME[it["q"]].upper()), C[QCOL[it["q"]]])
        cv.text(654, 186, "CREATION", C["acc"])
        for j, s in enumerate(it["build"]):
            cv.text(654, 206 + 16 * j, s.upper()[:100], C["txt"], 1)
    else:
        cv.text(654, 60, "NONE YET", C["dim"])
    # bottom: dropped items with icons
    cv.rect(8, 400, 1264, 216, C["panel"])
    cv.text(16, 406, "DROPPED (%d)" % len(v["dropped"]), C["acc"])
    x = 16
    for d in v["dropped"]:
        cv.rect(x, 430, 150, 180, C["bg"])
        cv.frame_rect(x, 430, 150, 180, C[QCOL[d["q"]]])
        if d["icon"] is not None:
            w, h, _, _ = A.pending_icons[d["icon"]]
            sc = 2 if h <= 56 else 1
            cv.icon(x + (150 - w * sc) // 2, 434 + (112 - h * sc) // 2, A.pending_icons[d["icon"]], sc)
        else:
            cv.text(x + 8, 470, "NO ICON", C["dim"], 1)
        for j, ln in enumerate(anim_common.wrap(d["name"].upper(), 24)[:3]):
            cv.text(x + 6, 550 + 12 * j, ln, C[QCOL[d["q"]]], 1)
        if d["base"].upper() != d["name"].upper():
            for ln in anim_common.wrap(d["base"].upper(), 24)[:1]:
                cv.text(x + 6, 592, ln, C["dim"], 1)
        x += 156
        if x > 1250:
            break
    # caption
    cv.rect(0, 624, W, H - 624, C["panel"])
    cv.text(10, 630, "STEP %d/%d" % (k + 1, total), C["acc"])
    for j, ln in enumerate(anim_common.wrap(st["text"].upper(), (W - 20) // 12)[:3]):
        cv.text(10, 650 + 22 * j, ln, C["txt"], 2, bold=True)
    return bytes(cv.cv)


TC_HELP = """<li>Left: the resolver's frame stack (tc.md D, G): the TC being picked from, picks left, NoDrop and total.
A NoDrop roll or a pick uses one draw on the source unit's seed; a sub-TC entry pushes a frame.</li>
<li>Right: the item being made. The six boxes are the quality tests in order (unique, set, rare, magic, superior, then
normal or low): chance, the draw (RangeB of the chance, won below 128) and the result. Below: the creation builders on
the item's own seed.</li>
<li>Bottom: items dropped so far; an inventory icon appears once the item is complete.</li>
<li>Each step's calculations name the spec section it restates (tc.md, quality.md, uniques-sets.md, affixes.md).
Stages without a model in tools/ (monster level of an area, quest TC, gold, ItemInitStats, ethereal, sockets, automagic,
property values) are marked "not modelled here".</li>
<li>The seed is an illustrative input; the item seeds come from a game-seed stream derived from it, not from the
game's own derivation.</li>"""


def cmd_render(argv):
    opts = {"--difficulty": "0", "--players": "1", "--mf": "0", "--mlvl": None, "--kind": "normal", "--max": "0",
            "--out": None}
    argv = list(argv)
    for o in opts:
        if o in argv:
            i = argv.index(o)
            opts[o] = argv[i + 1]
            del argv[i:i + 2]
    if len(argv) != 3:
        print(__doc__.strip(), file=sys.stderr)
        return 2
    root, name, seed = argv[0], argv[1], int(argv[2], 0)
    diff = {"normal": 0, "nightmare": 1, "hell": 2}.get(opts["--difficulty"].lower())
    if diff is None:
        diff = int(opts["--difficulty"])
    M = Models(root)
    mlvl = int(opts["--mlvl"]) if opts["--mlvl"] else None
    src = find_source(M, name, diff, opts["--kind"], mlvl)
    slug = "".join(c if c.isalnum() else "_" for c in src["label"].lower()).strip("_")
    out = opts["--out"] or os.path.join(HERE, "..", "workspace", "render", "anim", "tc-%s-d%d-%x" % (slug, diff, seed))
    out = anim_common.safe_out(out)
    os.makedirs(out, exist_ok=True)
    A = Anim(M, src, seed, diff, int(opts["--players"]), int(opts["--mf"]), int(opts["--max"]))
    A.run()
    cv = Canvas(W, H)
    for ic in A.pending_icons:
        cv.prealloc(ic)
    n = len(A.steps)
    frames, caps = [], []
    for k, st in enumerate(A.steps):
        frames.append(draw(cv, A, st, k, n))
        caps.append(dict(text=st["text"], calc=st["calc"]))
    p = cv.palette()
    for i, f in enumerate(frames):
        png.write_indexed(os.path.join(out, "frame-%03d.png" % i), W, H, f, p, transparent=())
    anim_common.write_html(os.path.join(out, "index.html"), caps, W, H, "treasure class drop animation", TC_HELP)
    json.dump(caps, open(os.path.join(out, "steps.json"), "w"), indent=1)
    delays = [120] * n
    delays[-1] = 600
    gw, gh = W // 2, H // 2
    gf = [b"".join(f[y * 2 * W:y * 2 * W + gw * 2:2] for y in range(gh)) for f in frames]
    with open(os.path.join(out, "tc.gif"), "wb") as fh:
        fh.write(anim_common.encode_gif(gf, gw, gh, p, delays))
    print("%d frames -> %s" % (n, out))
    return 0


# ---------------------------------------------------------------- selftest against kept logs

def selftest(argv):
    """selftest <root> --stock | <log> ...  (--stock: the stock log set of tools/tc_sweep.py with the run records' magic
    find, plus workspace/logs/affixes*-*.log for the creation chain; --mf N for explicit logs)."""
    import glob
    root, rest = argv[0], argv[1:]
    mfs = {}
    if rest and rest[0] == "--stock":
        import tc_sweep
        sl = tc_sweep.stock_logs()
        logs = [p for _, p, _, _, _ in sl]
        mfs = {p: m for _, p, m, _, _ in sl}
        clogs = sorted(glob.glob(os.path.join(tc_sweep.LOGS, "affixes*-*.log")))
    else:
        mf0 = 0
        if "--mf" in rest:
            i = rest.index("--mf")
            mf0 = int(rest[i + 1])
            del rest[i:i + 2]
        logs = clogs = rest
        mfs = {p: mf0 for p in rest}
    M = Models(root)
    T = M.T
    ok = bad = items_ok = items_bad = qn = 0
    cjoin = cjoin_bad = 0
    skipped = 0
    for path in logs:
        if mfs.get(path, 0) is None:       # runs the sweep replays with the quality oracle (no magic find known)
            skipped += 1
            continue
        for call0, err in tc.read_calls(path):
            call = list(call0)
            drop = call.pop(1)[1]
            if len(call) > 1 and call[1][0] == "_CTX":
                call.pop(1)
            tcr = call[0][1]
            if err or tcr["exp"] != "1" or int(tcr["fq"]) or tcr["stype"] not in ("1", "2"):
                continue
            ev = call
            party, players = [], []
            bits = 53
            for h_, kv in ev:
                if h_ == "PARTY":
                    party.append(int(kv["party"]))
                elif h_ == "PLAYERS":
                    players.append(int(kv["players"]))
                elif h_ == "NDIN":
                    bits = tc.PC_BITS[(int(kv["fctrl"], 16) >> 8) & 3]
            mf = []
            for j, (h_, kv) in enumerate(ev):
                if h_ == "QIN":
                    extra, k2 = {}, j + 1
                    while k2 < len(ev) and ev[k2][0] in quality.QEXTRA:
                        extra[ev[k2][0]] = ev[k2][1]
                        k2 += 1
                    mf.append(quality.magic_find(extra, tcr, mfs.get(path, 0))[0])
            lo, hi = tc.seedpair(tcr["seed"])
            r = resolve(M, int(tcr["tc"]), int(tcr["ilvl"]), (lo, hi), mx=int(tcr["max"]), nonodrop=bool(int(tcr["nonodrop"])),
                        party=party, players=players, cap=None, mf=mf, bits=bits)
            end = next(kv for h_, kv in ev if h_ == "TCEND")
            cpre = [(int(kv["item"]), int(kv["q"]), int(kv["uidx"]), int(kv["up"])) for h_, kv in ev if h_ == "CPRE"]
            good = r["count"] == int(end["count"]) and r["seed"] == tc.seedpair(end["seed"]) and r["items"] == cpre[:len(r["items"])] \
                and len(cpre) >= len(r["items"])
            ok += good
            bad += not good
            if not good:
                print("FAIL %s tc=%s count %s/%s seed %s/%s items %s vs CPRE %s" % (os.path.basename(path), tcr["tc"], r["count"], end["count"], fseed(r["seed"]), end["seed"], r["items"][-2:], cpre[-2:]))
            qn += len(r["items"])
    print("logs skipped (no magic find known, the sweep uses the oracle): %d" % skipped)
    print("resolver: %d calls identical to the log (count, final seed, created items with quality, uidx and flags), %d "
          "differ; %d items" % (ok, bad, qn))
    # creation chain against IC0 .. ICJ blocks
    for path in clogs:
        blocks, cur_b = [], None
        for ln in open(path, errors="replace"):
            if ln.startswith("IC0 {"):
                cur_b = [("IC0", json.loads(ln[4:]))]
                blocks.append(cur_b)
            elif cur_b is not None and ln.startswith("ICJ {"):
                cur_b.append(("ICJ", json.loads(ln[4:])))
                cur_b = None
        made = set()
        for b in blocks:
            if len(b) != 2:
                continue
            ic0, icj = b[0][1], b[1][1]
            if ic0["rest"] or ic0["ver"] == 0 or ic0["rq"] == 0:
                continue
            ic = dict(cls=ic0["cls"], ilvl=ic0["ilvl"], ver=ic0["ver"], rq=ic0["rq"], rrow=ic0["rrow"], rfl=ic0["rfl"],
                      g6a=ic0["g6a"], ladder=ic0["ladder"])
            res = create_item(M, ic, ic0["start"], made)
            seed_ok = res["it"] is None or res["seed"] is None or fseed(res["seed"]) == icj["seed"]
            qok = res["q"] == icj["q"]
            cjoin += 1
            # the seed at the join is only compared where the model's seed is the builder's (a unique or set build's
            # exit goes through ItemApplyProps, so only its quality is compared)
            if not qok or not seed_ok:
                cjoin_bad += 1
                if cjoin_bad < 5:
                    print("FAIL creation cls %d ilvl %d rq %d: model q %s seed %s, log q %s seed %s" % (
                        ic["cls"], ic["ilvl"], ic["rq"], res["q"], res["seed"] and fseed(res["seed"]), icj["q"], icj["seed"]))
    print("creation: %d IC0..ICJ blocks, %d differ (final quality; join seed for the affix builders)" % (cjoin, cjoin_bad))
    # the instrumented run (Anim: every stage emitted as a step) against the plain model, several sources and seeds
    inst = inst_bad = 0
    for name, diff, kind in (("andariel", 2, "normal"), ("bishibosh", 0, "normal"), ("mephisto", 2, "normal"),
                             ("countess", 1, "normal"), ("baal", 2, "normal"), ("hephasto", 2, "normal"),
                             ("act 3 (h) good", 2, "tc")):
        for sd in range(1, 41):
            src = find_source(M, name, diff, kind, None)
            A = Anim(M, src, sd * 0x9E37, diff, 1, 150, 0)
            A.run()
            lvl = src["ilvl"] if src["gate"] else 0
            t = T.get(src["base"], lvl)
            plain = resolve(M, t, src["ilvl"], (sd * 0x9E37 & M32, 666), mx=0, party=1, players=1,
                            cap=1 if src["monster"] else None, mf=150)
            same = A.res == plain
            # the instrumented creation's quality of every item must also equal a plain create_item on the same inputs
            inst += 1
            inst_bad += not same
    print("instrumented run vs plain model: %d runs (7 sources x 40 seeds), %d differ (count, seed, items)" % (inst, inst_bad))
    return 1 if bad or cjoin_bad or inst_bad else 0


def main(argv):
    if argv and argv[0] == "selftest":
        return selftest(argv[1:])
    return cmd_render(argv)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
