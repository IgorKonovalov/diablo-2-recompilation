"""Build the quest and travel save set of plan 0042 Phase 0, and check each save against the state it is meant to hold.

Usage:
  python3 -I tools/quest_saves.py build <excel-dir> <out-dir> [recipe ...]
  python3 -I tools/quest_saves.py check <excel-dir> [recipe ...]

build  builds each recipe of SET (default: all) from tools/d2s_recipes/<recipe>.json on its base save into
       <out-dir>/<Name>/<Name>.d2s (Name = the recipe's "name": letters only, as the character-name rule wants;
       one character per directory, as a slot's saves directory takes one) and prints one line per save:
       recipe, name, base, sha256.
check  builds each recipe into a temporary directory and compares the built save with EXPECT, written
       independently of the recipe from the state table of docs/formats/d2s.md § Quest and travel saves: per
       difficulty the quest words whose bit 0 is set, the other set bits, the waypoint bits, the header act byte
       (0x80 | act, all three difficulties) and the codes of the items added to the inventory. Exit 1 on any
       difference. `SURVEY quest_saves ...` ends the output.

SET holds the 14 recipes plan 0042 Phase 0 adds, the 9 plan 0032 quest recipes the plan reuses (questfresh,
questfreshv, questfreshvh, questb6, questdurielk, questrewards, questrewardsh, questservices, questcows), and the 3
saves plan 0042 Phase 1 (c) asks for (quest-w9lost, quest-w9book, quest-w39summit), and the 16 recipes of plan 0042
Phase 2 (quest-tpc; part 2's quest-talk1..5, quest-talk1c..4c, quest-orbwill, quest-death; part 3's quest-p3entry,
quest-p3anya, quest-p3meshif, quest-p3wpact), registered by plan 0049 Phase 0. EXPECT covers the plan 0042 recipes;
the plan 0032 ones are checked by tools/test_d2s.py (QuestBitsTest, pinned hashes). The classic recipes' `quests:
all` sets no Act V word (ALL_C).

Bases: workspace/samples/d2s-owner/smpsor-l50.d2s (expansion Sorceress) and
workspace/runtime/monspawn-chars/cls/smpsor.d2s (classic Sorceress), both with every quest word 0.
Stdlib only; writes only under <out-dir> (build) or a temporary directory (check).
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
         "c": os.path.join(ROOT, "workspace", "runtime", "monspawn-chars", "cls", "smpsor.d2s")}

# recipe -> base key; plan 0042 Phase 0 first, then the plan 0032 quest recipes the plan reuses
SET = {
    "travel-wp1": "x", "travel-wp2": "x", "travel-wp3": "x", "travel-wp4": "x", "travel-wp5": "x",
    "travel-wpnone": "x", "travel-tab2": "x", "travel-tab5d": "x", "travel-arcane": "x",
    "travel-act2": "x", "travel-act3": "x", "travel-act4": "x", "travel-act5": "x", "questfreshc": "c",
    "questfresh": "x", "questfreshv": "x", "questfreshvh": "x", "questb6": "x", "questdurielk": "x",
    "questrewards": "x", "questrewardsh": "x", "questservices": "x", "questcows": "x",
    "quest-w9lost": "x", "quest-w9book": "x", "quest-w39summit": "x",
    # plan 0042 Phase 2: the classic town-portal save (part 1), the talk, orb and death saves (part 2, 2026-10-18)
    # and the part 3 saves (2026-10-19); registered by plan 0049 Phase 0
    "quest-tpc": "c",
    "quest-talk1": "x", "quest-talk2": "x", "quest-talk3": "x", "quest-talk4": "x", "quest-talk5": "x",
    "quest-talk1c": "c", "quest-talk2c": "c", "quest-talk3c": "c", "quest-talk4c": "c",
    "quest-orbwill": "x", "quest-death": "x",
    "quest-p3entry": "x", "quest-p3anya": "x", "quest-p3meshif": "x", "quest-p3wpact": "x",
}

# Waypoint indices per act: levels.txt Waypoint 0..38 in act order (docs/tables/Levels.md § Travel)
ACT_WP = {1: set(range(0, 9)), 2: set(range(9, 18)), 3: set(range(18, 27)), 4: set(range(27, 30)),
          5: set(range(30, 39))}
TOWN_WP = {0, 9, 18, 27, 30}
ALL_WP = set(range(39))
ACT1 = set(range(1, 7))            # quest words of the act fields of g_QuestDescs (save/0002), bit 0 = done
ACT2 = set(range(9, 15))
ACT3 = set(range(17, 23))
ACT4 = set(range(25, 28))
ACT5 = set(range(35, 41))
TRAVEL_X = {7, 15, 23, 26, 28}     # acts_open in an expansion save
ALL_X = ACT1 | ACT2 | ACT3 | ACT4 | ACT5 | TRAVEL_X
ALL_C = ACT1 | ACT2 | ACT3 | ACT4 | {7, 15, 23}   # `quests: all` in a classic save: no Act V words

# recipe -> (words with bit 0 set, waypoint bits, act of the header byte, added item codes[, {word: other bits}]); the
# same in every difficulty; no other quest bit is set than the optional fifth element names
EXPECT = {
    "travel-wp1": (ALL_X, TOWN_WP | ACT_WP[1], 0, []),
    "travel-wp2": (ALL_X, TOWN_WP | ACT_WP[2], 0, []),
    "travel-wp3": (ALL_X, TOWN_WP | ACT_WP[3], 0, []),
    "travel-wp4": (ALL_X, TOWN_WP | ACT_WP[4], 0, []),
    "travel-wp5": (ALL_X, TOWN_WP | ACT_WP[5], 0, []),
    "travel-wpnone": (ALL_X, set(), 0, []),
    "travel-tab2": ({7}, ALL_WP, 0, []),
    "travel-tab5d": ({7, 15, 23, 26}, ALL_WP, 0, []),
    "travel-arcane": (ACT1 | {7}, ACT_WP[1] | ACT_WP[2], 1, []),
    "travel-act2": (ACT1, ACT_WP[1], 0, []),
    "travel-act3": (ACT1 | {7} | (ACT2 - {10}), ACT_WP[1] | ACT_WP[2], 1, ["msf", "vip"]),
    "travel-act4": (ACT1 | {7} | ACT2 | {15} | (ACT3 - {18}), ACT_WP[1] | ACT_WP[2] | ACT_WP[3], 2,
                    ["qf1", "qey", "qhr", "qbr"]),
    "travel-act5": (ACT1 | ACT2 | ACT3 | ACT4 | {7, 15, 23, 26}, ALL_WP - ACT_WP[5], 3, []),
    "questfreshc": ({7, 15, 23}, set(range(30)), 0, []),
    # plan 0042 Phase 1 (c): the word-9 first-join clear (bits 0 and 5, no `ass`; counter case with `ass`) and the
    # summit with the Ancients not done (quests/0001 § 8 word 9, § 10 word 39)
    "quest-w9lost": (ALL_X, ALL_WP, 1, ["tbk"], {9: 1 << 5}),
    "quest-w9book": (ALL_X, ALL_WP, 1, ["tbk", "ass"], {9: 1 << 5}),
    "quest-w39summit": (ALL_X - {39, 40}, ALL_WP, 4, ["tbk"]),
    # plan 0042 Phase 2 part 1: the classic Act I-IV town-portal save (questfreshc with a tome)
    "quest-tpc": ({7, 15, 23}, set(range(30)), 0, ["tbk"]),
    # part 2 (run:2026-10-18-quests2): every quest done but the talk steps' words, bit 0 clear and only the step's
    # bit set (1, 2, 4, 6, 9, 20, 25, 27, 35 bit 1; 14 bit 3; 19 bit 6; 21 bit 4); start act I..V
    "quest-talk1": (ALL_X - {1, 2, 4, 6}, TOWN_WP | ACT_WP[1], 0, [], {1: 2, 2: 2, 4: 2, 6: 2}),
    "quest-talk2": (ALL_X - {9, 14}, TOWN_WP | ACT_WP[1], 1, [], {9: 2, 14: 1 << 3}),
    "quest-talk3": (ALL_X - {19, 20, 21}, TOWN_WP | ACT_WP[1], 2, [], {19: 1 << 6, 20: 2, 21: 1 << 4}),
    "quest-talk4": (ALL_X - {25, 27}, TOWN_WP | ACT_WP[1], 3, [], {25: 2, 27: 2}),
    "quest-talk5": (ALL_X - {35}, TOWN_WP | ACT_WP[1], 4, [], {35: 2}),
    "quest-talk1c": (ALL_C - {1, 2, 4, 6}, set(range(30)), 0, [], {1: 2, 2: 2, 4: 2, 6: 2}),
    "quest-talk2c": (ALL_C - {9, 14}, set(range(30)), 1, [], {9: 2, 14: 1 << 3}),
    "quest-talk3c": (ALL_C - {19, 20, 21}, set(range(30)), 2, [], {19: 1 << 6, 20: 2, 21: 1 << 4}),
    "quest-talk4c": (ALL_C - {25, 27}, set(range(30)), 3, [], {25: 2, 27: 2}),
    # travel-act4's state with qf2 wielded instead of qf1 (the eye, heart and brain in the inventory)
    "quest-orbwill": (ACT1 | {7} | ACT2 | {15} | (ACT3 - {18}), ACT_WP[1] | ACT_WP[2] | ACT_WP[3], 2,
                      ["qey", "qhr", "qbr"]),
    "quest-death": (ALL_X, TOWN_WP | ACT_WP[1], 0, []),
    # part 3 (run:2026-10-19-quests3)
    "quest-p3entry": (ALL_X - {4, 11, 12, 37}, ALL_WP, 0, ["tbk", "bkd"]),
    "quest-p3anya": (ALL_X - {37}, ALL_WP, 4, ["tbk", "tr2"], {37: (1 << 1) | (1 << 8) | (1 << 15)}),
    "quest-p3meshif": (ALL_X, ALL_WP, 2, []),
    "quest-p3wpact": (ALL_X, TOWN_WP, 0, ["tbk"]),
}


def build_one(excel, name, out_path):
    with contextlib.redirect_stdout(io.StringIO()):
        d2s.build(excel, os.path.join(RECIPES, name + ".json"), BASES[SET[name]], out_path)
    with open(out_path, "rb") as fh:
        return fh.read()


def check_one(name, b):
    """[difference, ...] between a built save image and EXPECT[name]."""
    words, wps, act, codes = EXPECT[name][:4]
    extra = EXPECT[name][4] if len(EXPECT[name]) > 4 else {}
    errs = []
    qw = d2s.quest_words(b)
    wpb = d2s.parse_waypoints(b)
    for d in range(3):
        got = {q for q in range(d2s.QUEST_WORD_COUNT) if qw[d][q] & 1}
        other = [(q, qw[d][q] & ~1) for q in range(d2s.QUEST_WORD_COUNT) if qw[d][q] & ~1 != extra.get(q, 0)]
        if got != words:
            errs.append("%s: bit-0 words +%s -%s" % (d2s.DIFFICULTIES[d], sorted(got - words), sorted(words - got)))
        if other:
            errs.append("%s: other quest bits %s" % (d2s.DIFFICULTIES[d], other))
        if set(wpb[d]["bits"]) != wps:
            errs.append("%s: waypoints +%s -%s" % (d2s.DIFFICULTIES[d], sorted(set(wpb[d]["bits"]) - wps),
                                                   sorted(wps - set(wpb[d]["bits"]))))
    if list(b[0xA8:0xAB]) != [0x80 | act] * 3:
        errs.append("act bytes %s, want %s" % (list(b[0xA8:0xAB]), [0x80 | act] * 3))
    return errs


def added_codes(excel, name, b):
    t = d2s.Tables(excel)
    f = d2s.parse(b, t.isc, t.kinds)
    with open(os.path.join(RECIPES, name + ".json")) as fh:
        rc = json.load(fh)
    keep = set(rc.get("keep_items", []))
    new = [i["code"].strip() for i in f["items"]["items"] if i.get("location") == 0 and i.get("store") == 1
           and i["code"].strip() not in keep]
    return new


def main(argv):
    if len(argv) < 2 or argv[0] not in ("build", "check") or (argv[0] == "build" and len(argv) < 3):
        print(__doc__)
        return 2
    cmd, excel = argv[0], argv[1]
    names = argv[3:] if cmd == "build" else argv[2:]
    names = names or (list(SET) if cmd == "build" else list(EXPECT))
    for n in names:
        if n not in SET or (cmd == "check" and n not in EXPECT):
            print("unknown recipe %r" % n)
            return 2
    if cmd == "build":
        out = argv[2]
        for n in names:
            with open(os.path.join(RECIPES, n + ".json")) as fh:
                cname = json.load(fh)["name"]
            dst = os.path.join(out, cname)
            os.makedirs(dst, exist_ok=True)
            b = build_one(excel, n, os.path.join(dst, cname + ".d2s"))
            print("%-14s %-15s %s  %s" % (n, cname, os.path.basename(BASES[SET[n]]), hashlib.sha256(b).hexdigest()))
        return 0
    tmp = tempfile.mkdtemp(prefix="quest-saves-")
    bad = 0
    try:
        for n in names:
            b = build_one(excel, n, os.path.join(tmp, n + ".d2s"))
            errs = check_one(n, b)
            codes = added_codes(excel, n, b)
            if codes != EXPECT[n][3]:
                errs.append("added items %s, want %s" % (codes, EXPECT[n][3]))
            bad += bool(errs)
            print("%-14s %s" % (n, "ok" if not errs else "; ".join(errs)))
    finally:
        shutil.rmtree(tmp)
    print("SURVEY quest_saves recipes=%d bad=%d" % (len(names), bad))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
