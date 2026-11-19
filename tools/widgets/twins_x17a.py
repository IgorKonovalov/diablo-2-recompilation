"""Python twins of the `calc`, `grid`, `price` and `regen` widgets (ADR-0037), registered by twins.py.

`calc`: tools/calc.py's `evaluate` (the evaluator of docs/specs/data/calc.md section D) over typed toy bytes, with a toy
variable reader and no function table; the twin only reshapes the evaluator's `steps` into rows, and checks the typed
text. `grid`: tools/item_inventory.py's `spot_find` and `InvGrid.score` (items/inventory section B) on a toy page.
`price`: tools/economy.py's `Model.price` over a toy item, with the tables built from the inputs (no game data) and the
`trace` list the checker already prints. `regen`: tools/stats.py's `regen_tick` (stats/states section E) applied once per
frame to the numbers typed.
"""
import os
import re
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import calc  # noqa: E402
import economy  # noqa: E402
import item_inventory as ii  # noqa: E402
import stats  # noqa: E402

I32 = (-0x80000000, 0x7FFFFFFF)


def clamp(v, lo, hi):
    return min(hi, max(lo, int(v)))


def lim(data, name, v):
    return clamp(v, data["inputs"][name]["min"], data["inputs"][name]["max"])


# ---- calc ----------------------------------------------------------------------------------------------------------
OPERAND = {1: 1, 4: 1, 5: 2, 6: 4, 7: 1, 8: 2, 9: 4}


def parse_hex_bytes(text, max_bytes):
    """(bytes, fault): one or two hex digits per token, tokens apart by spaces or commas; fault 1 a bad token, 2 too
    many bytes. The rule of the checksum widget, restated here for the typed toy bytes."""
    toks, bad, cur = [], False, ""
    for ch in str(text).lower():
        if ch in " ,":
            if cur:
                toks.append(cur)
            cur = ""
        elif ch in "0123456789abcdef":
            cur += ch
        else:
            bad, cur = True, ""
    if cur:
        toks.append(cur)
    bad = bad or any(len(t) > 2 for t in toks)
    if bad:
        return [], 1
    out = [int(t, 16) for t in toks]
    return ([], 2) if len(out) > max_bytes else (out, 0)


def cut_operand(code):
    """True when an operand that starts inside the typed bytes runs past the last one, on the path the evaluation takes
    (the walk stops at the first byte that ends it): the game reads past the buffer there, which the page leaves open."""
    p = 0
    while p < len(code):
        op = code[p]
        p += 1
        if op in OPERAND:
            if p < len(code) and p + OPERAND[op] > len(code):
                return True
            p += OPERAND[op]
        elif op == 0 or op == 2 or op == 3 or op > 0x16:
            return False
    return False


class _ToyEnv:
    """The reader of the widget: variables 0, 1, 2 are the three typed numbers, any other index reads 0; no functions."""
    nfuncs = 0

    def __init__(self, vals):
        self.vals = vals

    def argc(self, fn):
        return 0

    def var(self, idx):
        return self.vals.get(idx, 0)

    def call(self, fn, a, b, c, argc):
        return 0


def twin_calc(inputs, data):
    rule = data["rule"]
    code, fault = parse_hex_bytes(inputs["formula"], rule["maxBytes"])
    vals = {0: lim(data, "lvl", inputs["lvl"]), 1: lim(data, "par1", inputs["par1"]), 2: lim(data, "par2", inputs["par2"])}
    out = {"fault": fault, "tally": 0, "rows": [], "how": "empty", "result": 0}
    if fault == 0 and cut_operand(code):
        out["fault"] = 3
        return out
    if fault:
        return out
    out["tally"] = len(code)
    if not code:
        return out
    steps = []
    value = calc.evaluate(bytes(code), _ToyEnv(vals), steps=steps)
    ops = [s for s in steps if s[1] is not None]
    past = steps[-1][1] is None
    rows, end = [], "past"
    for k, (p, op, before) in enumerate(ops):
        size = 1 + OPERAND.get(op, 0)
        arg = None
        if op in OPERAND and p + 1 < len(code):
            fmt = {1: "<B", 4: "<B", 5: "<h", 6: "<i", 7: "<b", 8: "<h", 9: "<i"}[op]
            arg = struct.unpack_from(fmt, bytes(code), p + 1)[0]
        row = {"pos": p, "op": op, "arg": arg, "size": size, "octs": list(code[p:p + size])}
        if op == 0x13 and len(before) >= 2 and before[-1] == -1 and before[-2] == I32[0]:
            row["stack"] = before[:-2]
            rows.append(row)
            end, value = "trap", 0
            break
        if k + 1 < len(ops) or past:
            row["stack"] = steps[k + 1][2]
        elif op in OPERAND and p + 1 >= len(code):
            row["stack"] = []
            end = "cut"
        else:
            row["stack"] = before[:-1]
            end = "end"
        rows.append(row)
    if end in ("cut", "past"):
        assert value == 0
    out.update({"rows": rows, "how": end, "result": value})
    return out


CALC_BASE = {"formula": "04 00 07 05 0A 04 00 04 00 07 03 12 04 01 11 16 00", "lvl": 3, "par1": 4, "par2": 0}


def ccase(**kw):
    return dict(CALC_BASE, **kw)


CALC_CASES = [
    ccase(),
    ccase(lvl=7),
    ccase(lvl=5),
    ccase(formula="04 01 04 02 10 07 02 12 00", par1=6, par2=-9),
    ccase(formula="04 00 07 03 13 07 02 10 00", lvl=100),
    ccase(formula="04 00 07 03 13 07 02 10 00", lvl=-100),
    ccase(formula="07 05 07 03 01 00 00"),
    ccase(formula="07 02 04 00 14 00", lvl=10),
    ccase(formula="07 02 04 00 14 00", lvl=0),
    ccase(formula="07 02 07 00 14 00"),
    ccase(formula="07 03 07 04 16 00"),
    ccase(formula="07 03 16 00"),
    ccase(formula="16"),
    ccase(formula="00"),
    ccase(formula="02 07 05"),
    ccase(formula="07 05 03 07 06"),
    ccase(formula="07 05 17 07 06"),
    ccase(formula="07 05 07 03 0A 07 05 07 03 0B 07 05 07 05 0C 07 05 07 05 0D 07 05 07 05 0E 07 05 07 05 0F"),
    ccase(formula="07 07 07 02 13 07 07 07 00 13 15 00"),
    ccase(formula="08 FF 7F 08 02 00 12 08 00 80 12 00"),
    ccase(formula="09 00 00 00 80 07 FF 13 00"),
    ccase(formula="08 00 80 09 00 00 01 00 12 07 FF 13 00"),
    ccase(formula="08 00 80 09 00 00 01 00 12 07 FF 12 07 FF 13 00"),
    ccase(formula="09 FF FF FF 7F 07 02 12 00"),
    ccase(formula="05 01 00 06 02 00 00 00 04 09 10 10 00", lvl=1, par1=2, par2=3),
    ccase(formula="08 01 00 05 05 00 10 00", lvl=1),
    ccase(formula="07 07 07 02 15 14 00"),
    ccase(formula="07 02 08 70 11 14 00"),
    ccase(formula="08 70 11 08 01 00 14 00"),
    ccase(formula="07 01 07 02 07 03 07 04 07 05 07 06 07 07 07 08 07 09 07 0A 07 0B 07 0C 07 0D 07 0E 07 0F 07 10 07 11 07 12 07 13 07 14"),
    ccase(formula="08"),
    ccase(formula="09 01 02"),
    ccase(formula="07 05 08 01"),
    ccase(formula="04"),
    ccase(formula="01"),
    ccase(formula=""),
    ccase(formula="zz"),
    ccase(formula="123"),
    ccase(formula="07\t05"),
    ccase(formula="07 05, 07 06,,10 00"),
    ccase(formula="07 05 " * 20 + "10 00"),
    ccase(formula="07 " * 41),
    ccase(lvl=99999999999, par1=-99999999999, par2=3000000000, code="04 00 04 01 12 04 02 10 00"),
]


# ---- grid ----------------------------------------------------------------------------------------------------------
GRID_LIMITS = {"gw": (1, 10), "gh": (1, 8), "owner": (0, 1)}


def parse_shapes(text, max_items):
    """([(w, h)], fault): tokens apart by spaces or commas, each one digit 1 to 4, an `x` or `X`, one digit 1 to 4;
    fault 1 a bad token, 2 too many items."""
    toks, cur = [], ""
    for ch in str(text):
        if ch in " ,":
            if cur:
                toks.append(cur)
            cur = ""
        else:
            cur += ch
    if cur:
        toks.append(cur)
    out = []
    for t in toks:
        if len(t) != 3 or t[0] not in "1234" or t[1] not in "xX" or t[2] not in "1234":
            return [], 1
        out.append((int(t[0]), int(t[2])))
    return ([], 2) if len(out) > max_items else (out, 0)


def twin_grid(inputs, data):
    gw, gh = clamp(inputs["gw"], *GRID_LIMITS["gw"]), clamp(inputs["gh"], *GRID_LIMITS["gh"])
    owner = clamp(inputs["owner"], *GRID_LIMITS["owner"])
    sizes, fault = parse_shapes(inputs["shapes"], data["rule"]["maxItems"])
    g = ii.InvGrid(gw, gh)
    letters = [["."] * gw for _ in range(gh)]
    rows = []
    for k, (w, h) in enumerate(sizes):
        spot = ii.spot_find(g, w, h, owner == 0)
        row = {"num": k + 1, "wd": w, "ht": h, "placed": spot is not None, "col": -1, "row": -1, "score": -1}
        if spot is not None:
            col, rw = spot
            row.update({"col": col, "row": rw, "score": g.score(col, rw, w, h) if owner == 0 else -1})
            for r in range(rw, rw + h):
                for c in range(col, col + w):
                    g.cell[r][c] = 1
                    letters[r][c] = chr(ord("A") + k)
        rows.append(row)
    return {"fault": fault, "gw": gw, "gh": gh, "owner": owner, "rows": rows, "grid": ["".join(r) for r in letters]}


GRID_BASE = {"gw": 10, "gh": 4, "owner": 0, "shapes": "1x1 1x1 1x1 1x1 1x1"}


def gcase(**kw):
    return dict(GRID_BASE, **kw)


GRID_CASES = [
    gcase(),
    gcase(owner=1),
    gcase(shapes="2x2 1x1 1x3 2x1 1x2 3x1"),
    gcase(shapes="2x2 1x1 1x3 2x1 1x2 3x1", owner=1),
    gcase(gw=6, gh=4, shapes="2x2 2x2 2x2 2x2 2x2 2x2 1x1"),
    gcase(gw=6, gh=4, shapes="2x2 2x2 2x2 2x2 2x2 2x2 1x1", owner=1),
    gcase(gw=3, gh=3, shapes="1x1 1x1 1x1 1x1 1x1 1x1 1x1 1x1 1x1 1x1 1x1"),
    gcase(gw=3, gh=3, shapes="4x1 1x4 3x3 1x1"),
    gcase(gw=1, gh=1, shapes="1x1 1x1"),
    gcase(gw=1, gh=8, shapes="1x3 1x3 1x3"),
    gcase(gw=10, gh=1, shapes="2x1 2x1 4x4 1x1"),
    gcase(gw=4, gh=4, shapes="2x4 1X2 2x1,1x1 3x1"),
    gcase(gw=5, gh=5, shapes="3x2 2x3 2x2 1x1 1x1 1x1 1x1"),
    gcase(gw=5, gh=5, shapes="3x2 2x3 2x2 1x1 1x1 1x1 1x1", owner=1),
    gcase(shapes=""),
    gcase(shapes="1x1 1x1 1x1 1x1 1x1 1x1 1x1 1x1 1x1 1x1 1x1 1x1"),
    gcase(shapes="1x1 1x1 1x1 1x1 1x1 1x1 1x1 1x1 1x1 1x1 1x1 1x1 1x1"),
    gcase(shapes="1x1 5x1"),
    gcase(shapes="1x1 0x1"),
    gcase(shapes="1 x 1"),
    gcase(shapes="11x1"),
    gcase(shapes="1x1\t1x1"),
    gcase(shapes="1x1;1x1"),
    gcase(shapes="1y1"),
    gcase(shapes=" 1x1 ,, 2x2 "),
    gcase(gw=99, gh=-4, owner=7, shapes="1x1 2x2"),
]


# ---- price ---------------------------------------------------------------------------------------------------------
PRICE_QUALITY = {1: "low", 2: "normal", 5: "set", 7: "unique"}


def _toy_tables(inp):
    """economy.Tables with no game data: two item rows (an ordinary item and a class item), one child row for the
    gems, the three item types the model tests by code, one automagic affix, one set record, one unique record and one
    Npc row, packed at the offsets the model reads."""
    T = object.__new__(economy.Tables)
    types = []
    for cls in (7, 7, 0, 7, 7, 7):
        b = bytearray(228)
        b[0x1F] = 255
        b[0x21] = cls
        types.append(bytes(b))
    T.types = types
    T.tcode = {"body": 3, "book": 4, "armo": 5}
    T._clos = {}

    def item(cost, typ):
        b = bytearray(424)
        struct.pack_into("<i", b, 0xE0, cost)
        struct.pack_into("<h", b, 0x11E, typ)
        return bytes(b)

    T.items = [item(inp["cost"], 1), item(inp["cost"], 2), item(inp["gem"], 1)]
    aff = bytearray(144)
    struct.pack_into("<ii", aff, 0x88, inp["autoMult"], inp["autoAdd"])
    T.affixes = [bytes(aff)]
    rec = bytearray(440)
    struct.pack_into("<ii", rec, 0x38, inp["recMult"], inp["recAdd"])
    T.sets = [bytes(rec)]
    uq = bytearray(332)
    struct.pack_into("<ii", uq, 0x7C, inp["recMult"], inp["recAdd"])
    T.uniques = [bytes(uq)]
    npc = bytearray(76)
    struct.pack_into("<iiii", npc, 0, 1, inp["sell"], inp["buy"], 1024)
    struct.pack_into("<i", npc, 0x40, inp["maxbuy"])
    T.npcs = {1: bytes(npc)}
    T.books, T.monstats, T.skills, T.isc, T.sets_ = [], [], [], [], []
    T.by_code = {}
    return T


def _find(trace, tag):
    return next((t for t in trace if t[0] == tag), None)


def twin_price(inputs, data):
    inp = {k: lim(data, k, inputs[k]) for k in data["inputs"]}
    if inp["grade"] not in PRICE_QUALITY:
        inp["grade"] = 2          # a number the widget does not offer reads as normal
    T = _toy_tables(inp)
    model = economy.Model(T)
    item = {"t": 4, "c": 1 if inp["kind"] else 0, "q": inp["grade"], "fl": (0x10 if inp["ident"] else 0) | (0x400000 if inp["eth"] else 0),
            "fi": 0, "own": [[70 << 16, 1]], "aa": 1 if inp["auto"] else 0, "pre": [0, 0, 0], "suf": [0, 0, 0],
            "ch": [2] * inp["sockets"], "v": 0}
    base = {"m": 1, "d": 0, "npc": 1, "it": item, "plv": 1, "prp": inp["reduce"], "qb": None}
    trace = []
    sell = model.price(base, trace)
    buy = model.price(dict(base, m=0))
    b, v, n = _find(trace, "base"), _find(trace, "value"), _find(trace, "npc")
    aff = _find(trace, "affix") or ("affix", 0, 0, 0)
    add = _find(trace, "added") or ("added", b[1], b[2], b[3])
    sock, eth = _find(trace, "sockets"), _find(trace, "ethereal")
    fin = _find(trace, "final")
    return {"cost": inp["cost"],
            "first": [b[1], b[2]], "terms": [aff[1], aff[2]], "added": [add[1], add[2]], "sockets": [sock[1], sock[2]],
            "ethereal": [eth[1], eth[2]], "value": [v[1], v[2]], "npc": [n[1], n[2]], "ceiling": fin[4],
            "buy": buy, "sell": sell}


PRICE_BASE = {"cost": 1000, "grade": 2, "ident": 1, "recMult": 0, "recAdd": 0, "auto": 0, "autoMult": 0, "autoAdd": 0,
              "sockets": 0, "gem": 0, "eth": 0, "kind": 0, "sell": 1024, "buy": 512, "maxbuy": 100000, "reduce": 0}


def pcase(**kw):
    return dict(PRICE_BASE, **kw)


PRICE_CASES = [
    pcase(),
    pcase(grade=1),
    pcase(grade=5, recMult=2048, recAdd=300),
    pcase(grade=7, recMult=3000, recAdd=-250),
    pcase(grade=7, recMult=3000, recAdd=-250, ident=0),
    pcase(auto=1, autoMult=512, autoAdd=40),
    pcase(grade=1, auto=1, autoMult=512, autoAdd=40),
    pcase(grade=7, auto=1, autoMult=-300, autoAdd=15, recMult=1024, recAdd=5),
    pcase(sockets=3, gem=1400),
    pcase(sockets=6, gem=99999, grade=5, recMult=100, recAdd=1),
    pcase(eth=1),
    pcase(kind=1),
    pcase(eth=1, kind=1, sockets=1, gem=3),
    pcase(cost=100000, grade=7, recMult=4096, recAdd=999),
    pcase(cost=100000, grade=7, recMult=4096, recAdd=999, sell=1600, buy=600),
    pcase(cost=2000000, grade=5, recMult=5000, recAdd=0),
    pcase(cost=2000000, grade=7, recMult=100000, recAdd=100000, ident=1, sell=2048, buy=512),
    pcase(cost=70000, grade=7, recMult=70000, recAdd=-70000, auto=1, autoMult=100000, autoAdd=-100000),
    pcase(cost=65535, grade=5, recMult=1024),
    pcase(cost=65536, grade=5, recMult=1024),
    pcase(cost=65536, grade=5, recMult=0, recAdd=7),
    pcase(cost=1, maxbuy=1, sell=0, buy=0),
    pcase(cost=0),
    pcase(cost=3, grade=1),
    pcase(cost=3, grade=1, sockets=2, gem=5),
    pcase(maxbuy=0),
    pcase(maxbuy=-5),
    pcase(reduce=20),
    pcase(reduce=99, cost=500000),
    pcase(reduce=99, grade=1, cost=1),
    pcase(cost=999999, reduce=33, sell=2048),
    pcase(cost=-50, grade=7, recMult=-100, recAdd=-100),
    pcase(sell=-512, buy=-512, grade=5, recMult=-2000, recAdd=-9999),
    pcase(cost=5000000, grade=9, ident=-1, sockets=9, gem=-8, eth=3, kind=-1, sell=99999999, buy=-99999999,
          maxbuy=99999999, reduce=150, recMult=99999999, recAdd=99999999, auto=2, autoMult=99999999, autoAdd=-99999999),
]


# ---- regen ---------------------------------------------------------------------------------------------------------
LIFE_CODE = {"life +74": "up", "life -74": "down", "life capped": "cap", "life floored at 256": "floor", "life no 74": "none"}


def twin_regen(inputs, data):
    v = {k: lim(data, k, inputs[k]) for k in data["inputs"]}
    st = {6: v["life"], 7: v["lifeMax"], 74: v["lifeReg"], 10: v["stam"], 11: v["stamMax"], 28: v["stamBonus"],
          8: v["mana"], 9: v["manaMax"], 27: v["manaBonus"], 26: v["manaFlat"]}
    rows = [{"tick": 0, "life": st[6], "lifeWhy": "start", "stam": st[10], "stamWhy": "start", "mana": st[8], "manaWhy": "start"}]
    for tick in range(1, v["ticks"] + 1):
        out = stats.regen_tick(lambda k: st.get(k, 0), v["mode"], v["noMana"] != 0, lambda: v["manaK"])
        sw = out[10][1]
        rows.append({"tick": tick, "life": out[6][0], "lifeWhy": LIFE_CODE[out[6][1]],
                     "stam": out[10][0], "stamWhy": "gain" if "+" in sw else "full" if sw.endswith("full") else "none",
                     "mana": out[8][0], "manaWhy": "state" if out[8][1] == "mana state 85" else "regen"})
        st[6], st[10], st[8] = out[6][0], out[10][0], out[8][0]
    return {"rows": rows}


REGEN_BASE = {"life": 10000, "lifeMax": 30000, "lifeReg": 400, "stam": 2000, "stamMax": 25600, "stamBonus": 0, "mode": 1,
              "mana": 3000, "manaMax": 10000, "manaK": 1, "manaBonus": 0, "manaFlat": 0, "noMana": 0, "ticks": 10}


def rcase(**kw):
    return dict(REGEN_BASE, **kw)


REGEN_CASES = [
    rcase(),
    rcase(ticks=1),
    rcase(ticks=40),
    rcase(lifeReg=-3000, life=9000, ticks=5),
    rcase(lifeReg=-3000, life=1000, ticks=5),
    rcase(lifeReg=0),
    rcase(lifeReg=9000, life=20000, lifeMax=30000, ticks=5),
    rcase(life=300, lifeReg=-100, ticks=4),
    rcase(mode=2),
    rcase(mode=2, stam=255),
    rcase(mode=2, stam=256),
    rcase(mode=6),
    rcase(mode=5, stamBonus=250),
    rcase(mode=1, stamBonus=-50, stam=20000),
    rcase(mode=3),
    rcase(mode=3, stamBonus=1000),
    rcase(mode=3, stamBonus=999),
    rcase(mode=4, stamBonus=5000),
    rcase(mode=0, stamBonus=1000),
    rcase(mode=200),
    rcase(stam=25000, ticks=5),
    rcase(stam=25600),
    rcase(mode=1, stamMax=1000, stam=0, stamBonus=77, ticks=6),
    rcase(manaK=0),
    rcase(manaK=3, manaMax=100000),
    rcase(manaMax=10, manaK=100),
    rcase(manaMax=0, mana=0),
    rcase(manaBonus=100, ticks=4),
    rcase(manaBonus=-100, ticks=4),
    rcase(manaBonus=-250, ticks=4),
    rcase(manaFlat=-900, mana=2000, ticks=6),
    rcase(manaFlat=-900, mana=500, ticks=3),
    rcase(manaFlat=70, mana=9990, ticks=4),
    rcase(noMana=1),
    rcase(noMana=1, manaFlat=-30, mana=50, ticks=4),
    rcase(noMana=1, manaFlat=300, mana=9900, ticks=3),
    rcase(mana=12000, manaMax=10000, ticks=2),
    rcase(manaMax=16777215, manaK=1, manaBonus=1000, mana=0, ticks=3),
    rcase(life=-5, lifeMax=-5, stam=-5, mana=-5, ticks=-3),
    rcase(life=99999999, lifeMax=99999999, lifeReg=99999999, stamBonus=9999999, ticks=99),
]


TWINS = {"calc": twin_calc, "grid": twin_grid, "price": twin_price, "regen": twin_regen}
CASES = {"calc": CALC_CASES, "grid": GRID_CASES, "price": PRICE_CASES, "regen": REGEN_CASES}


# ---- text fallbacks (the first fixture case, in decimal) -------------------------------------------------------------
def fallback_calc(fx):
    c = fx["cases"][0]
    e = c["expect"]
    rows = [[k + 1, " ".join("%02X" % b for b in r["octs"]), " ".join(str(x) for x in r["stack"]) or "-"]
            for k, r in enumerate(e["rows"])]
    note = ("The toy formula with lvl %d, par1 %d and par2 %d, one row per step, computed by our model; the stack is shown "
            "after the step and the value returned is %d." % (c["inputs"]["lvl"], c["inputs"]["par1"], c["inputs"]["par2"], e["result"]))
    return ["Step", "Bytes (hex)", "Stack after"], rows, note


def fallback_grid(fx):
    c = fx["cases"][0]
    e = c["expect"]
    rows = [[r["num"], "%d x %d" % (r["wd"], r["ht"]), "%d, %d" % (r["col"], r["row"]) if r["placed"] else "none",
             r["score"] if r["score"] >= 0 else "-"] for r in e["rows"]]
    note = ("Five one-cell items put in turn on a toy page %d wide and %d high for a player, computed by our model; columns "
            "and rows count from 0." % (e["gw"], e["gh"]))
    return ["Item", "Size", "Spot (column, row)", "Score"], rows, note


def fallback_price(fx):
    c = fx["cases"][0]["expect"]
    rows = [["Base value", c["first"][0], c["first"][1]], ["Value after the terms, the sockets and the quarter steps", c["value"][0], c["value"][1]],
            ["After the Npc step", c["npc"][0], c["npc"][1]], ["Price", c["buy"], c["sell"]]]
    return ["Step", "Buy", "Sell"], rows, ("A toy item of base cost %d, normal quality, at a toy Npc, computed by our model "
                                          "(decimal)." % c["cost"])


def fallback_regen(fx):
    c = fx["cases"][0]
    rows = [[r["tick"], r["life"], r["stam"], r["mana"]] for r in c["expect"]["rows"][:6]]
    return ["Frame", "Life", "Stamina", "Mana"], rows, (
        "The first frames of the toy numbers offered, in unit mode 1, computed by our model (raw stat values).")


FALLBACKS = {"calc": fallback_calc, "grid": fallback_grid, "price": fallback_price, "regen": fallback_regen}
