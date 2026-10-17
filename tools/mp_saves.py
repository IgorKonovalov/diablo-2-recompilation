"""Build the two-client character pairs of plan 0044 Phase 2, and check each pair against the case it serves.

Usage:
  python3 -I tools/mp_saves.py build <excel-dir> <out-dir> [recipe ...]
  python3 -I tools/mp_saves.py check <excel-dir>
  python3 -I tools/mp_saves.py pairs

build  builds each recipe of SET (default: all) from tools/d2s_recipes/<recipe>.json on its base save into
       <out-dir>/<Name>/<Name>.d2s (one character per directory, as a slot's saves directory takes one) and prints
       one line per save: recipe, name, base, sha256.
check  builds every recipe of SET into a temporary directory and tests, for each pair of PAIRS, the conditions
       of the cases it serves (multiplayer/0001 § 2), written apart from the recipes: the two header names differ,
       both are letters only and the game types match; the levels the case needs (hostility: both >= 9, so
       character level 9 or more on both sides, multiplayer/0001 § 4); the quest bits, waypoints, start act and
       held items each case names; magic find (stat 80) on the host's items only (MP19); a mercenary (MP04); a
       Paladin joiner whose right skill is an aura (MP25); for the MP23 bulk pair, both sides with
       Nova on the right button, no Lightning Mastery, no item with a property, and max life at least 200 times the
       other side's largest Nova hit at 17 % (an upper bound from skills.txt EMax + (level - 1) * the largest
       EMaxLev*, rounded up), so either survives 200 attack events with no potion. Exit 1 on any failure. `SURVEY mp_saves ...` ends
       the output.
pairs  prints PAIRS: case ids, host recipe, joiner recipe, what the pair is for.

The recipes are made with tools/d2s.py build keys only (no new key). Bases: workspace/samples/d2s-owner/smpsor-l50.d2s
(expansion Sorceress) for every recipe but mp-pal-join, which is built on workspace/samples/d2s/smppal.d2s
(expansion Paladin); the clones (mp-mf-host, mp-merc-host, mp-forge-host, mp-cow-host) are uniqnova, mercnova,
questrewardsh and questcows under another name. Stdlib only; writes only under <out-dir> (build) or a temporary
directory (check).
"""
import contextlib
import hashlib
import io
import json
import os
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import d2s  # noqa: E402

ROOT = os.path.dirname(HERE)
RECIPES = os.path.join(HERE, "d2s_recipes")
BASES = {"x": os.path.join(ROOT, "workspace", "samples", "d2s-owner", "smpsor-l50.d2s"),
         "pal": os.path.join(ROOT, "workspace", "samples", "d2s", "smppal.d2s")}

SET = {n: "x" for n in (
    "mp-nova-host", "mp-nova-weak", "mp-nova-low", "mp-tank-join", "mp-mf-host", "mp-merc-host",
    "mp-forge-host", "mp-forge-join", "mp-forge-done", "mp-andy-open", "mp-andy-done", "mp-andy-weak",
    "mp-den-host", "mp-den-join", "mp-dur-host", "mp-dur-closed", "mp-dur-open", "quest-w39summit",
    "mp-anc-join", "mp-anc-low", "mp-scroll-join", "mp-quest-host", "mp-quest-join", "mp-cow-host",
    "mp-pvp-host", "mp-pvp-join")}
SET["mp-pal-join"] = "pal"

# (cases, host, joiner, purpose): the backlog request's items (a)-(f)
PAIRS = [
    ("MP01 MP23 MP24", "mp-nova-host", "mp-nova-weak", "(a) Nova pair, both level >= 9; the joiner weak enough to die"),
    ("MP23", "mp-pvp-host", "mp-pvp-join", "(a) the bulk of MP23: both level 80, life 8000, Nova 1 and no gear, so both survive 200 attack events"),
    ("MP24 counter", "mp-nova-host", "mp-nova-low", "(a) joiner below level 9: the declaration is refused"),
    ("MP19", "mp-mf-host", "mp-tank-join", "(b) MF host (uniqnova's gear), joiner with no MF item"),
    ("MP04", "mp-merc-host", "mp-tank-join", "(c) host with a mercenary (mercnova's Rogue)"),
    ("MP12", "mp-forge-host", "mp-forge-join", "(d) forge: word 27 bits 0, 1 clear on both"),
    ("MP12 counter", "mp-forge-host", "mp-forge-done", "(d) forge: joiner with word 27 bit 0 set"),
    ("MP13 MP14a", "mp-andy-open", "mp-andy-done", "(d) Andariel: opposite word-6 states (swap: host and joiner exchange)"),
    ("MP14b", "mp-andy-done", "mp-andy-weak", "(d) Andariel: joiner weak enough to die in level 37, word 6 open"),
    ("MP28", "mp-den-host", "mp-den-join", "(d) Den of Evil open on both"),
    ("MP27a", "mp-dur-host", "mp-dur-closed", "(d) Durance: joiner word 21 bit 0 clear"),
    ("MP27b", "mp-dur-host", "mp-dur-open", "(d) Durance: joiner word 21 bit 0 set"),
    ("MP17", "quest-w39summit", "mp-anc-join", "(d) Ancients: joiner word 39 bit 0 clear, base level 60 (>= 20(d + 1) in every difficulty)"),
    ("MP17 counter", "quest-w39summit", "mp-anc-low", "(d) Ancients: joiner word 39 bit 0 clear, base level 19 (< 20)"),
    ("MP30", "mp-nova-host", "mp-scroll-join", "(d) joiner holding bks (the Bark Scroll)"),
    ("MP29", "mp-quest-host", "mp-quest-join", "(d) different finished quests: host words 1-3, joiner 4-6"),
    ("MP25", "mp-nova-host", "mp-pal-join", "(e) Paladin joiner with an aura (Might) on the right button"),
    ("MP24 cow", "mp-cow-host", "mp-tank-join", "(f) cubeportal-type host: cube with Wirt's Leg and a tome, word 4 bit 10 clear"),
]

# pairs whose case declares hostility (multiplayer/0001 § 4: both players at character level 9 or more)
HOSTILE = {"MP01 MP23 MP24", "MP23", "MP25", "MP24 cow"}
# MP23 bulk (multiplayer/0001 § 2: at least 200 events, P = 17 % on every scaled field)
MP23_EVENTS, MP23_PCT = 200, 17


def bit(qw, d, word, b):
    return (qw[d][word] >> b) & 1


def every(pred):
    return all(pred(d) for d in range(3))


def held(f, code):
    """The player holds an item of that code: stored (inventory, cube, stash) or equipped."""
    return any(i["code"].strip() == code and i.get("location") in (0, 1) for i in f["items"]["items"])


def mf_items(f):
    """Top-level items (stored or equipped) carrying stat 80 (item_magicbonus)."""
    return [i["code"].strip() for i in f["items"]["items"] if any(p[0] == 80 for p in i.get("props") or [])]


def aura_skills(excel):
    rows = []
    with open(os.path.join(excel, "skills.txt"), newline="") as fh:
        lines = [ln.rstrip("\r\n").split("\t") for ln in fh.read().split("\n") if ln]
    head = [h.lower() for h in lines[0]]
    ia, iid = head.index("aura"), head.index("id")
    for r in lines[1:]:
        if len(r) > ia and r[ia] == "1":
            rows.append(int(r[iid]))
    return set(rows)


def nova_bound(excel, level):
    """An upper bound on one Nova hit at that skill level, whole points: EMax + (level - 1) * max(EMaxLev1..5)
    (skills.txt, HitShift 8), with no mastery and no item bonus."""
    with open(os.path.join(excel, "skills.txt"), newline="") as fh:
        lines = [ln.rstrip("\r\n").split("\t") for ln in fh.read().split("\n") if ln]
    head = lines[0]
    r = next(x for x in lines[1:] if x[0] == "Nova")
    assert r[head.index("HitShift")] == "8"
    step = max(int(r[head.index("EMaxLev%d" % k)]) for k in range(1, 6))
    return int(r[head.index("EMax")]) + max(level - 1, 0) * step


def stat(f, sid):
    return next((v for s, _p, v in f["stats"] if s == sid), 0)


def checks(excel):
    """recipe -> [(label, predicate(f, qw, wp))]: the state each pair's case needs, apart from the recipes."""
    aura = aura_skills(excel)
    lvl = lambda f: f["header"]["level"]  # noqa: E731
    return {
        "mp-nova-host": [("level >= 9", lambda f, q, w: lvl(f) >= 9)],
        "mp-nova-weak": [("level 9", lambda f, q, w: lvl(f) == 9), ("max life <= 60", lambda f, q, w: stat(f, 7) >> 8 <= 60)],
        "mp-nova-low": [("level 8", lambda f, q, w: lvl(f) == 8)],
        "mp-tank-join": [("no MF item", lambda f, q, w: not mf_items(f)), ("level >= 9", lambda f, q, w: lvl(f) >= 9)],
        "mp-mf-host": [("MF items", lambda f, q, w: bool(mf_items(f)))],
        "mp-merc-host": [("mercenary", lambda f, q, w: f["header"]["merc_seed"] != 0)],
        "mp-forge-host": [("word 27 bits 0, 1 clear", lambda f, q, w: every(lambda d: not bit(q, d, 27, 0) and not bit(q, d, 27, 1))),
                          ("hfh, mss held", lambda f, q, w: held(f, "hfh") and held(f, "mss")), ("Act IV", lambda f, q, w: list(f["header"]["difficulty"]) == [131] * 3)],
        "mp-forge-join": [("word 27 bits 0, 1 clear", lambda f, q, w: every(lambda d: not bit(q, d, 27, 0) and not bit(q, d, 27, 1))),
                          ("Act IV", lambda f, q, w: list(f["header"]["difficulty"]) == [131] * 3)],
        "mp-forge-done": [("word 27 bit 0 set", lambda f, q, w: every(lambda d: bit(q, d, 27, 0))),
                          ("Act IV", lambda f, q, w: list(f["header"]["difficulty"]) == [131] * 3)],
        "mp-andy-open": [("word 6 bit 0 clear", lambda f, q, w: every(lambda d: not bit(q, d, 6, 0)))],
        "mp-andy-done": [("word 6 bit 0 set", lambda f, q, w: every(lambda d: bit(q, d, 6, 0)))],
        "mp-andy-weak": [("word 6 bit 0 clear", lambda f, q, w: every(lambda d: not bit(q, d, 6, 0))), ("level 9", lambda f, q, w: lvl(f) == 9)],
        "mp-den-host": [("word 1 bit 0 clear", lambda f, q, w: every(lambda d: not bit(q, d, 1, 0))), ("Act II open", lambda f, q, w: every(lambda d: bit(q, d, 7, 0)))],
        "mp-den-join": [("word 1 bit 0 clear", lambda f, q, w: every(lambda d: not bit(q, d, 1, 0))), ("Act II open", lambda f, q, w: every(lambda d: bit(q, d, 7, 0)))],
        "mp-dur-host": [("waypoint 26 (level 101)", lambda f, q, w: every(lambda d: 26 in w[d]["bits"])), ("Act III", lambda f, q, w: list(f["header"]["difficulty"]) == [130] * 3)],
        "mp-dur-closed": [("word 21 bit 0 clear", lambda f, q, w: every(lambda d: not bit(q, d, 21, 0))), ("Act III", lambda f, q, w: list(f["header"]["difficulty"]) == [130] * 3)],
        "mp-dur-open": [("word 21 bit 0 set", lambda f, q, w: every(lambda d: bit(q, d, 21, 0))), ("Act III", lambda f, q, w: list(f["header"]["difficulty"]) == [130] * 3)],
        "quest-w39summit": [("words 39, 40 bit 0 clear", lambda f, q, w: every(lambda d: not bit(q, d, 39, 0) and not bit(q, d, 40, 0))),
                            ("waypoint 37 (level 118)", lambda f, q, w: every(lambda d: 37 in w[d]["bits"])), ("Act V", lambda f, q, w: list(f["header"]["difficulty"]) == [132] * 3)],
        "mp-anc-join": [("word 39 bit 0 clear", lambda f, q, w: every(lambda d: not bit(q, d, 39, 0))), ("level >= 60", lambda f, q, w: lvl(f) >= 60),
                        ("Act V", lambda f, q, w: list(f["header"]["difficulty"]) == [132] * 3)],
        "mp-anc-low": [("word 39 bit 0 clear", lambda f, q, w: every(lambda d: not bit(q, d, 39, 0))), ("level < 20", lambda f, q, w: lvl(f) < 20),
                       ("Act V", lambda f, q, w: list(f["header"]["difficulty"]) == [132] * 3)],
        "mp-scroll-join": [("bks held", lambda f, q, w: held(f, "bks")), ("word 4 bit 0 clear", lambda f, q, w: every(lambda d: not bit(q, d, 4, 0)))],
        "mp-quest-host": [("words 1-3 done, 4-6 not", lambda f, q, w: every(lambda d: all(bit(q, d, x, 0) for x in (1, 2, 3)) and not any(bit(q, d, x, 0) for x in (4, 5, 6))))],
        "mp-quest-join": [("words 4-6 done, 1-3 not", lambda f, q, w: every(lambda d: all(bit(q, d, x, 0) for x in (4, 5, 6)) and not any(bit(q, d, x, 0) for x in (1, 2, 3))))],
        "mp-pal-join": [("Paladin", lambda f, q, w: f["header"]["cls"] == 3), ("right skill an aura", lambda f, q, w: f["header"]["mouse"][1] in aura),
                        ("level >= 9", lambda f, q, w: lvl(f) >= 9)],
        "mp-pvp-host": [("level >= 9", lambda f, q, w: lvl(f) >= 9), ("no item with a property", lambda f, q, w: not any(i.get("props") for i in f["items"]["items"]))],
        "mp-pvp-join": [("level >= 9", lambda f, q, w: lvl(f) >= 9), ("no item with a property", lambda f, q, w: not any(i.get("props") for i in f["items"]["items"]))],
        "mp-cow-host": [("word 4 bit 10 clear", lambda f, q, w: every(lambda d: not bit(q, d, 4, 10))), ("leg, tbk held", lambda f, q, w: held(f, "leg") and held(f, "tbk")),
                        ("box held", lambda f, q, w: held(f, "box"))],
    }


def mp23_errors(excel, t, fh, fj):
    """MP23 bulk: each side attacks with Nova and outlives 200 of the other's largest hits at 17 %."""
    order = t.class_skills["sor"]
    nova, mastery = order.index("Nova"), order.index("Lightning Mastery")
    errs = []
    for side, f, other in (("host", fh, fj), ("joiner", fj, fh)):
        if f["header"]["cls"] != 1 or other["header"]["cls"] != 1:
            errs.append("%s: not a Sorceress" % side)
            continue
        if f["skills"][nova] < 1 or f["header"]["mouse"][1] != 48:
            errs.append("%s: Nova not on the right button" % side)
        if other["skills"][mastery]:
            errs.append("%s: the other side has Lightning Mastery" % side)
        hit = -(-nova_bound(excel, other["skills"][nova]) * MP23_PCT // 100)
        if stat(f, 7) >> 8 < MP23_EVENTS * hit:
            errs.append("%s: max life %d < %d x %d" % (side, stat(f, 7) >> 8, MP23_EVENTS, hit))
    return errs


def build_one(excel, name, out_path):
    with contextlib.redirect_stdout(io.StringIO()):
        d2s.build(excel, os.path.join(RECIPES, name + ".json"), BASES[SET[name]], out_path)
    with open(out_path, "rb") as fh:
        return fh.read()


def check_all(excel):
    t = d2s.Tables(excel)
    tmp = tempfile.mkdtemp(prefix="mp-saves-")
    parsed = {}
    try:
        for n in SET:
            b = build_one(excel, n, os.path.join(tmp, n + ".d2s"))
            parsed[n] = (d2s.parse(b, t.isc, t.kinds), d2s.quest_words(b), d2s.parse_waypoints(b))
    finally:
        shutil.rmtree(tmp)
    cond = checks(excel)
    bad = 0
    for n in SET:
        f, q, w = parsed[n]
        errs = [lab for lab, p in cond[n] if not p(f, q, w)]
        if not f["header"]["name"].isalpha():
            errs.append("name not letters only")
        bad += bool(errs)
        print("%-16s %-14s %s" % (n, f["header"]["name"], "ok" if not errs else "FAIL " + "; ".join(errs)))
    pbad = 0
    for cases, h, j, _what in PAIRS:
        fh, fj = parsed[h][0], parsed[j][0]
        errs = []
        if fh["header"]["name"].lower() == fj["header"]["name"].lower():
            errs.append("same name")
        if (fh["header"]["status"] & 0x20) != (fj["header"]["status"] & 0x20):
            errs.append("game types differ")
        lv = min(fh["header"]["level"], fj["header"]["level"])
        if cases in HOSTILE and lv < 9:
            errs.append("hostility needs level >= 9 on both")
        if cases == "MP24 counter" and fj["header"]["level"] >= 9:
            errs.append("the counter joiner must be below level 9")
        if cases == "MP23":
            errs += mp23_errors(excel, t, fh, fj)
        pbad += bool(errs)
        print("pair %-16s %-16s %-16s %s" % (cases, h, j, "ok" if not errs else "FAIL " + "; ".join(errs)))
    print("SURVEY mp_saves recipes=%d bad=%d pairs=%d pairs_bad=%d" % (len(SET), bad, len(PAIRS), pbad))
    return 1 if bad or pbad else 0


def main(argv):
    if not argv or argv[0] not in ("build", "check", "pairs") or (argv[0] == "build" and len(argv) < 3) \
            or (argv[0] == "check" and len(argv) < 2):
        print(__doc__)
        return 2
    if argv[0] == "pairs":
        for cases, h, j, what in PAIRS:
            print("%-16s %-16s %-16s %s" % (cases, h, j, what))
        return 0
    excel = argv[1]
    if argv[0] == "check":
        return check_all(excel)
    out, names = argv[2], argv[3:] or list(SET)
    for n in names:
        if n not in SET:
            print("unknown recipe %r" % n)
            return 2
    for n in names:
        with open(os.path.join(RECIPES, n + ".json")) as fh:
            cname = json.load(fh)["name"]
        dst = os.path.join(out, cname)
        os.makedirs(dst, exist_ok=True)
        b = build_one(excel, n, os.path.join(dst, cname + ".d2s"))
        print("%-16s %-14s %-14s %s" % (n, cname, os.path.basename(BASES[SET[n]]), hashlib.sha256(b).hexdigest()))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
