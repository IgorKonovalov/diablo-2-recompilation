"""Animate the runeword match (docs/specs/items/sockets-runewords.md section D): an item's sockets filled one rune at a
time, the match that runs after every insert (it stops until the item is full), the scan of the Runes rows from record 0 and
the first row whose runes, in socket order, and item type fit. Schematic only (ADR-0036): boxes and text in our own palette.

Usage:
  python3 -I tools/runeword_anim.py <root> [--base CODE] [--runes a,b,c] [--quality N] [--theme dark|light]
        [--out DIR] [--schematic]

<root> is the data tree (workspace/merged): the excel tables Runes, Misc, Armor, Weapons and ItemTypes are read from
<root>/data/global/excel. --base: the parent's base code (default lrg, a large shield). --runes: the runes in socket order,
by name, ko,ko,mal by default (Sanctuary in a large shield, the page's worked example); the parent has as many sockets as
runes. --quality: 1 low, 2 normal (default), 3 superior, 4 to 9 never match. --theme: dark or light palette values.
--schematic is accepted for the export builder and changes nothing. DIR defaults to workspace/render/anim/runeword-<base>-
schematic/ and must stay under workspace/. Outputs: frame-NNN.png, runeword.gif, index.html, steps.json, schematic.json.

Steps: the item and its runes; one step per insert (the match runs and stops until the last socket is filled); the checks that
pass on the full item; the scan of the Runes rows from record 0 (a count of the complete rows ahead of the hit by where each
differs); the hit row compared rune by rune; the item type test; the outcome. The match is the model of tools/sockets.py
(match, over the real Runes, Misc/Armor/Weapons and ItemTypes rows); the scan's counts are recomputed from the same rows and
asserted to agree with its result. Not shown: the server's refusal list, what a rune brings, the runeword's property lines and
rolls, the one-rune-more case with its stale stack word (D2). Stdlib only.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import anim_common  # noqa: E402
import props  # noqa: E402
import schematic_kit as K  # noqa: E402
import sockets  # noqa: E402

W, H = 960, 500
CAP_Y = 420
RUNES = ("EL ELD TIR NEF ETH ITH TAL RAL ORT THUL AMN SOL SHAEL DOL HEL IO LUM KO FAL LEM PUL UM MAL IST GUL VEX OHM LO SUR BER "
         "JAH CHAM ZOD").split()
QNAME = {1: "LOW", 2: "NORMAL", 3: "SUPERIOR", 4: "MAGIC", 5: "SET", 6: "RARE", 7: "UNIQUE", 8: "CRAFTED", 9: "QUALITY 9"}
BASE_NAMES = {"lrg": "LARGE SHIELD", "lsd": "LONG SWORD", "buc": "BUCKLER", "ful": "FULL PLATE MAIL", "cap": "CAP"}
HELP = """<li>Top: the parent item with its sockets and the runes in the order they are inserted. The match runs after every insert but only a full item can match.</li>
<li>Scan: the Runes rows are tried from record 0; a row is skipped at the first rune that differs from the children in socket order.</li>
<li>The hit row must also allow the item's type; item type equivalences count.</li>
<li>Every value is computed by our model from the game's tables for the item given, not observed in the game.</li>"""


def class_of(T, code):
    for i in range(len(T.items)):
        if T.base(i)["code"] == code:
            return i
    raise KeyError(code)


def rune_name(T, cls):
    c = T.base(cls)["code"]
    return RUNES[int(c[1:]) - 1] if c[:1] == "r" and c[1:].isdigit() and 1 <= int(c[1:]) <= 33 else c.upper()


def type_code(T, t):
    return T.itypes[t][:4].split(b"\0")[0].decode("latin1").upper()


def type_chain(T, cls, want):
    """The item's type and the equivalences from it up to `want` (ITEMS_IsType's walk), as type codes; [] when none."""
    def up(x, seen, path):
        if x <= 0 or x in seen or x >= len(T.itypes):
            return None
        path = path + [x]
        if x == want:
            return path
        seen.add(x)
        return up(props.u16(T.itypes[x], 4), seen, path) or up(props.u16(T.itypes[x], 6), seen, path)
    b = T.base(cls)
    r = up(b["type"], set(), []) or up(b["type2"], set(), [])
    return [type_code(T, x) for x in r] if r else []


def scan(T, kids, s, upto):
    """The rows before `upto` (or all when None) that are complete, by where each differs from the children: {k: count} for
    a first differing rune k (0 based) and 'short' for a row that matched its runes but had fewer than the sockets."""
    out, ncomplete = {}, 0
    n = len(kids)
    for i in range(len(T.runes) if upto is None else upto):
        R = T.rune(i)
        if not R["complete"]:
            continue
        ncomplete += 1
        k = 0
        bad = None
        while k < 6 and R["rune"][k] >= 1:
            if n < k or kids[k] != R["rune"][k]:
                bad = k
                break
            k += 1
        if bad is None and k < s:
            bad = "short"
        if bad is not None:
            out[bad] = out.get(bad, 0) + 1
        else:
            out["type"] = out.get("type", 0) + 1       # a row whose runes fit: only its item types decided
    return out, ncomplete


def build(T, base, runes, quality, theme):
    k = K.Kit(W, H, theme)
    frames, caps = [], []
    cls = class_of(T, base)
    kids = [class_of(T, "r%02d" % (RUNES.index(r) + 1)) for r in runes]
    n = len(kids)
    row, why = sockets.match(T, cls, quality, kids, n, [0] * 6)
    bname = BASE_NAMES.get(base, base.upper())
    qn = QNAME[quality]

    def header(s):
        k.text(20, 12, s, "acc", 2, True)

    def sockets_row(filled, cur=None, y=60):
        k.text(20, y - 4, "%s, %s, %d SOCKETS" % (qn, bname, n), "dim", 2)
        vals = [runes[i] if i < filled else None for i in range(n)]
        cw = min(150, 880 // max(n, 1))
        k.tape(20, y + 22, vals, cw, 52, cur=cur, sc=2, empty="")

    def rows(items, y0=170, dy=26, x=20):
        for i, r in enumerate(items):
            s, col = r if isinstance(r, tuple) else (r, "txt")
            k.text(x, y0 + i * dy, s, col, 2)

    def put(cap, text, calc):
        k.caption(cap, CAP_Y, 76)
        frames.append(k.done())
        caps.append(dict(text=text, calc=calc))

    # ---- the item and its runes
    header("RUNEWORD MATCH: %s" % " ".join(runes))
    sockets_row(0)
    rows([("THE RUNES, IN THE ORDER THEY ARE INSERTED:", "dim"), ("  " + ", ".join(runes), "txt"), "",
          ("AFTER EVERY INSERT THE GAME RUNS THE MATCH.", "dim"), ("UNTIL THE LAST SOCKET IS FILLED IT STOPS AT ONCE.", "dim")], y0=170)
    put("A %s of %s quality with %d sockets takes the runes %s, in that order. The match runs after every insert; only a full "
        "item can match (sockets D1)." % (bname.lower(), qn.lower(), n, ", ".join(r.title() for r in runes)),
        "An item with %d sockets and the runes to insert in order." % n,
        ["sockets D1: kids[] = the children's class ids in socket order; s = stat 194 & 0xFF = the item's sockets = %d." % n])
    # ---- the inserts before the last
    for i in range(1, n):
        header("INSERT %d OF %d: %s" % (i, n, runes[i - 1]))
        sockets_row(i, cur=i - 1)
        rows([("CHILDREN N = %d, SOCKETS S = %d" % (i, n), "txt"), ("N IS NOT S: NO MATCH", "bad"),
              "", ("THE SCAN OF THE RUNES ROWS DOES NOT RUN.", "dim")], y0=170)
        put("Insert %d of %d, %s: the item holds %d of %d runes, so the count of children differs from the sockets and the match "
            "returns at once (sockets D1)." % (i, n, runes[i - 1].title(), i, n),
            "Insert %d: %d of %d sockets filled, no match." % (i, i, n),
            ["sockets D1: s = %d, n = %d; s != n, return none." % (n, i)])
    # ---- the full item: the first tests
    header("INSERT %d OF %d: THE ITEM IS FULL" % (n, n))
    sockets_row(n, cur=n - 1)
    qok = not (4 <= quality <= 9)
    rows([("QUALITY %s (%d): %s" % (qn, quality, "PASSES" if qok else "NEVER MATCHES"), "good" if qok else "bad"),
          ("BASE QUEST FLAG %d: %s" % (T.base(cls)["quest"], "PASSES" if not T.base(cls)["quest"] else "NEVER MATCHES"),
           "good" if not T.base(cls)["quest"] else "bad"),
          ("CHILDREN N = %d = SOCKETS S" % n, "good"), "", ("NEXT: THE SCAN OF THE RUNES ROWS", "dim") if qok else
          ("NO SCAN: THE MATCH RETURNS NO ROW", "bad")], y0=170)
    put("The last rune fills the item: %s quality %s, the base is no quest item, and the children equal the sockets, so the scan "
        "can run (sockets D1)." % (qn.lower(), "passes" if qok else "stops the match"),
        "The full item passes the quality, quest and count tests." if qok else "The item's quality stops the match.",
        ["sockets D1: quality %d %s 4..9 (u32 (quality - 4) < 6 returns none)." % (quality, "is outside" if qok else "is in"),
         "sockets D1: ItemRecord quest = %d; n = %d = s." % (T.base(cls)["quest"], n)])
    if not qok or T.base(cls)["quest"]:
        assert row is None
        return frames, caps, k.pal, (row, why)
    # ---- the scan
    ahead, ncomp = scan(T, kids, n, row)
    header("THE SCAN: RUNES ROWS FROM RECORD 0")
    sockets_row(n)
    lines = [("%d COMPLETE ROWS BEFORE THE %s" % (sum(ahead.values()), "HIT" if row is not None else "END"), "txt"),
             ("EACH IS SKIPPED AT THE FIRST RUNE THAT DIFFERS:", "dim")]
    for key in sorted((a for a in ahead if isinstance(a, int))):
        lines.append(("  RUNE %d DIFFERS: %d %s" % (key + 1, ahead[key], "ROW" if ahead[key] == 1 else "ROWS"), "txt"))
    if ahead.get("short"):
        lines.append(("  FEWER RUNES THAN SOCKETS: %d %s" % (ahead["short"], "ROW" if ahead["short"] == 1 else "ROWS"), "txt"))
    if ahead.get("type"):
        lines.append(("  RUNES FIT, THE ITEM TYPE DOES NOT: %d %s" % (ahead["type"], "ROW" if ahead["type"] == 1 else "ROWS"), "txt"))
    rows(lines, y0=170, dy=24)
    put("The scan tries the Runes rows from record 0 and skips each complete row whose runes differ from the children in socket "
        "order%s (sockets D2)." % (
            ": %d complete rows are skipped before the hit" % sum(ahead.values()) if row is not None else ""),
        "The scan skips %d complete %s." % (sum(ahead.values()), "row" if sum(ahead.values()) == 1 else "rows"),
        ["sockets D2: for r in 0 ..< RunesCount: skip rows with complete = 0; while k < 6 and R.rune[k] >= 1, goto next on "
         "n < k or kids[k] != R.rune[k].",
         "skipped before the hit, by the first differing rune: %s." % (
             ", ".join("%s: %d" % (("rune %d" % (a + 1)) if isinstance(a, int) else a, c) for a, c in sorted(ahead.items(), key=str)) or "none")])
    if row is None:
        header("NO ROW FITS")
        sockets_row(n)
        rows([("NO COMPLETE ROW HAS THESE RUNES IN THIS ORDER", "bad"), ("AND AN ITEM TYPE THAT FITS: NO RUNEWORD.", "bad")], y0=170)
        put("No complete Runes row matches these runes in this order for this item, so the match returns none and the item gets no "
            "runeword (sockets D2).", "No row matches: no runeword.", ["sockets D2: the scan ends without a row; Match returns none."])
        return frames, caps, k.pal, (row, why)
    R = T.rune(row)
    # ---- the hit row compared rune by rune
    header("RECORD %d: %s" % (row, R["ename"].upper()))
    sockets_row(n)
    k.text(20, 160, "THE ROW'S RUNES", "dim", 2)
    cw = min(150, 880 // max(n, 1))
    rr = [rune_name(T, c) for c in R["rune"] if c >= 1]
    k.tape(20, 182, rr, cw, 52, cur=None, sc=2)
    for i in range(n):
        k.text_c(20 + i * cw + cw // 2, 240, "=", "good", 2, True)
    k.text(20, 262, "THE CHILDREN, IN SOCKET ORDER", "dim", 2)
    k.tape(20, 284, runes, cw, 52, cur=None, sc=2)
    rows([("EACH ROW RUNE EQUALS THE CHILD AT ITS SOCKET.", "txt"),
          ("THE ROW HAS %d RUNES, THE ITEM %d SOCKETS: NOT FEWER." % (len(rr), n), "txt")], y0=350)
    put("Record %d, %s, lists %s: every rune equals the child at the same socket, and the row has no fewer runes than the item has "
        "sockets (sockets D2)." % (row, R["ename"], ", ".join(r.title() for r in rr)),
        "Record %d, %s: its runes equal the children in socket order." % (row, R["ename"]),
        ["sockets D2: R.rune = %s; kids = %s; k reaches %d >= s = %d." % (rr, [r for r in runes], len(rr), n)])
    # ---- the item type
    it = [type_code(T, t) for t in R["itype"] if t]
    chain = [(t, type_chain(T, cls, t)) for t in R["itype"] if t]
    hit = [c for t, c in chain if c]
    header("THE ITEM TYPE")
    sockets_row(n)
    rows([("THE ROW'S ITEM TYPES: %s" % ", ".join(it), "txt"), ("EXCLUDED TYPES: NONE", "dim") if not any(R["etype"]) else
          ("EXCLUDED TYPES: %d" % sum(1 for e in R["etype"] if e), "dim"),
          ("%s IS %s" % (bname, " WHICH IS ".join(x for x in hit[0])) if hit else "THE ITEM IS NOT OF THE ROW'S TYPES",
           "good" if hit else "bad"),
          "", ("ANY OF THE ROW'S TYPES THE ITEM IS OF RETURNS THE ROW.", "dim"), ("EQUIVALENT TYPES COUNT.", "dim")], y0=170)
    put("The row accepts %s; %s%s, so the row is returned (sockets D3, D4)." % (
        ", ".join(it), bname.lower(), (" is of type %s" % " which is a ".join(x.lower() for x in hit[0])) if hit else " is not"),
        "The item type fits the row.",
        ["sockets D3: no excluded type of the row is the item's type.",
         "sockets D4: ITEMS_UnitIsType(parent, itype) is true through %s, so the row is returned." % " -> ".join(hit[0])])
    # ---- the outcome
    header("THE MATCH RETURNS %s" % R["ename"].upper())
    sockets_row(n, cur=None)
    k.box(20, 160, 440, 70, [("RUNES ROW %d" % row, "dim"), (R["ename"].upper(), "good")], "qd_set", "good", sc=3)
    rows([("THE RUNEWORD'S PROPERTY LINES ARE APPLIED NEXT.", "dim"), ("NOT SHOWN HERE.", "dim")], y0=260)
    put("The match returns record %d, %s. Its property lines are applied next (sockets D, E)." % (row, R["ename"]),
        "The match returns %s." % R["ename"], ["sockets D2: return R (record %d, %s)." % (row, R["ename"])])
    return frames, caps, k.pal, (row, why)


def main(argv):
    argv = list(argv)
    if "--schematic" in argv:
        argv.remove("--schematic")
    targs = list(argv[1:])
    if "--out" in targs:
        del targs[targs.index("--out"):targs.index("--out") + 2]
    opts = {"--base": "lrg", "--runes": "ko,ko,mal", "--quality": "2", "--theme": "dark", "--out": None}
    for o in opts:
        if o in argv:
            i = argv.index(o)
            if i + 1 >= len(argv):
                print(__doc__.strip(), file=sys.stderr)
                return 2
            opts[o] = argv[i + 1]
            del argv[i:i + 2]
    if len(argv) != 1 or opts["--theme"] not in K.THEMES:
        print(__doc__.strip(), file=sys.stderr)
        return 2
    runes = [r.strip().upper() for r in opts["--runes"].split(",")]
    try:
        quality = int(opts["--quality"])
    except ValueError:
        print(__doc__.strip(), file=sys.stderr)
        return 2
    if not (1 <= len(runes) <= 6 and all(r in RUNES for r in runes) and 1 <= quality <= 9):
        print(__doc__.strip(), file=sys.stderr)
        return 2
    excel = os.path.join(argv[0], "data", "global", "excel")
    if not os.path.isdir(excel):
        print("no excel tables under %s" % excel, file=sys.stderr)
        return 2
    T = sockets.Tables(excel)
    try:
        class_of(T, opts["--base"])
    except KeyError:
        print("no base with code %s" % opts["--base"], file=sys.stderr)
        return 2
    out = opts["--out"] or os.path.join(HERE, "..", "workspace", "render", "anim", "runeword-%s-schematic" % opts["--base"])
    out = anim_common.safe_out(out)
    os.makedirs(out, exist_ok=True)
    frames, caps, _pal, _i = build(T, opts["--base"], runes, quality, opts["--theme"])
    K.write_illustration(out, "runeword", frames, caps, W, H, K.palette(opts["--theme"])[1],
                         "runeword match animation", HELP, targs)
    print("%d frames -> %s" % (len(frames), out))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
