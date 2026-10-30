"""Count the table rows no stock path reaches (plan 0062 Phase 2).

Usage:
  python3 -I tools/unreached.py <excel-dir> [--table levels|monstats|skills|states|items] [--list] [--rows N]

<excel-dir> is a data/global/excel directory (e.g. workspace/merged/data/global/excel). Per table the tool
prints a `SURVEY table=...` line (rows, reached per reader bucket, unreached) and, with --list, the unreached rows
(--rows N caps the listing, default 12). Read-only, stdlib only.

"Reached" is defined per table by the readers the specs already name; a row is unreached when none of those
readers names it. The definitions are in docs/findings/archaeology/0002-unreached-rows.md; each is an upper bound
on reach where the reader is code that passes an id as an immediate (the tool cannot see those): such rows are
listed as "unreached by table readers" and the finding says which have a code reader.

  levels    Vis0..7 of any level; the act link lists' seams and border ranges (drlg/warps A1); Waypoint column;
            permanent portals (quests/travel G5).
  monstats  Levels mon/nmon/umon/cmon slots; SuperUniques.Class; MonPreset.Place; MonStats minion1/minion2/spawn;
            Skills.summon; PetType.mclass1..4; Hireling.Class; closure over NextInClass (monsters/pool chain).
  skills    class tree (charclass set and SkillDesc.SkillPage 1..3); MonStats Skill1..8; Hireling Skill1..6;
            CharStats StartSkill and Skill 1..10; item properties that take a skill (skill, oskill, aura, charged,
            att/hit/gethit/kill/death/levelup-skill, skill-rand) in Uniques, Sets, Magic/Rare affixes, Runes, Gems,
            CubeMain; Skills.sumskill1..5 of a reached skill.
  states    Skills aurastate/auratargetstate/passivestate/State1..3/nocostinstate; Misc state/cstate1/cstate2.
  items     auto item-type TCs (items/tc I1); TreasureClassEx item cells; vendor lists (items/vendors B1);
            CubeMain output; CharStats item1..10; MonEquip item1..3. Quest items (quest = 1) are counted apart.
"""
import argparse
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from excel_bin import find_file, read_txt  # noqa: E402

PROP_SKILL_FUNCS = {"11", "12", "19", "22"}


class X:
    def __init__(self, d):
        self.d = d
        self.c = {}

    def t(self, name):
        if name not in self.c:
            p = find_file(self.d, name, ".txt")
            if not p:
                self.c[name] = ([], [])
            else:
                h, rows = read_txt(p)
                self.c[name] = (h, [dict(zip(h, r)) for r in rows])
        return self.c[name]

    def rows(self, name):
        return self.t(name)[1]


def ci(s):
    return s.strip().lower()


def num(s):
    try:
        return int(s)
    except (TypeError, ValueError):
        return None


def line(table, total, buckets, un, extra=""):
    b = " ".join("%s=%d" % (k, v) for k, v in buckets)
    print("SURVEY table=%s rows=%d %s unreached=%d%s" % (table, total, b, len(un), extra))


def show(label, items, args):
    if args.list:
        for it in items[: args.rows]:
            print("  %s %s" % (label, it))
        if len(items) > args.rows:
            print("  ... %d more" % (len(items) - args.rows))


# ------------------------------------------------------------------ levels

# drlg/warps A1: ActLinkInit's border and seam ranges name these levels in the link lists.
LINK_RANGES = [(1, 17), (40, 46), (75, 83), (103, 106), (109, 112)]
# quests/travel G5: permanent portal pairs, both ends and the tomb.
PORTAL_LEVELS = {1, 39, 4, 38, 46, 74, 109, 121, 111, 125, 112, 126, 117, 127, 73}


def levels(x, args):
    L = x.rows("levels")
    ids = [num(r["Id"]) for r in L]
    vis = set()
    for r in L:
        for k in range(8):
            v = num(r["Vis%d" % k])
            if v:
                vis.add(v)
    link = {i for a, b in LINK_RANGES for i in range(a, b + 1)}
    wp = {num(r["Id"]) for r in L if r["Waypoint"] not in ("", "255")}
    got = [(r["Id"], r["Name"]) for r in L]
    un = []
    for r, i in zip(L, ids):
        if i in vis or i in link or i in wp or i in PORTAL_LEVELS:
            continue
        un.append((i, r["Name"]))
    line("levels", len(L), [("vis", len({i for i in ids if i in vis})),
                            ("link_ranges", len({i for i in ids if i in link})),
                            ("waypoint", len({i for i in ids if i in wp})),
                            ("portals", len({i for i in ids if i in PORTAL_LEVELS}))], un)
    show("level", un, args)
    return un


# ------------------------------------------------------------------ monstats

def monstats(x, args):
    M = x.rows("monstats")
    ids = [r["Id"] for r in M]
    low = {}
    for i, n in enumerate(ids):
        low.setdefault(ci(n), i)
    B = {}

    def add(b, name):
        n = ci(name)
        if n in low:
            B.setdefault(b, set()).add(low[n])

    for r in x.rows("levels"):
        for k in range(1, 11):
            for p in ("mon", "nmon", "umon"):
                add("pool", r.get("%s%d" % (p, k), ""))
        for k in range(1, 5):
            add("cmon", r.get("cmon%d" % k, ""))
    for r in x.rows("superuniques"):
        add("superunique", r["Class"])
    for r in x.rows("monpreset"):
        add("monpreset", r["Place"])
    for r in M:
        for c in ("minion1", "minion2", "spawn"):
            add("minion_spawn", r[c])
    for r in x.rows("skills"):
        add("summon", r["summon"])
    for r in x.rows("pettype"):
        for k in range(1, 5):
            add("pettype", r.get("mclass%d" % k, ""))
    for r in x.rows("hireling"):
        v = num(r["Class"])
        if v is not None and 0 <= v < len(M):
            B.setdefault("hireling", set()).add(v)
    base = set().union(*B.values())
    reached = set(base)
    grew = True
    while grew:
        grew = False
        for i in list(reached):
            j = low.get(ci(M[i]["NextInClass"]))
            if j is not None and j not in reached:
                reached.add(j)
                grew = True
    B["nextinclass_closure"] = reached - base
    un = [i for i in range(len(M)) if i not in reached]
    order = ["pool", "cmon", "superunique", "monpreset", "minion_spawn", "summon", "pettype", "hireling",
             "nextinclass_closure"]
    line("monstats", len(M), [(k, len(B.get(k, ()))) for k in order], un,
         " reached=%d enabled_unreached=%d npc_unreached=%d" % (
             len(reached), sum(1 for i in un if M[i]["enabled"] == "1"), sum(1 for i in un if M[i]["npc"] == "1")))
    nopool = [i for i in range(len(M)) if i not in B.get("pool", set()) and i not in B.get("cmon", set())]
    print("SURVEY table=monstats.levels_only rows=%d named_by_levels_slots=%d not_named_by_levels_slots=%d" % (
        len(M), len(M) - len(nopool), len(nopool)))
    show("monstats", ["%d %s enabled=%s isSpawn=%s npc=%s" % (i, ids[i], M[i]["enabled"], M[i]["isSpawn"], M[i]["npc"])
                      for i in un], args)
    return un


# ------------------------------------------------------------------ skills

def skill_param_columns(h):
    """(code column, param column) pairs of an item-property table, by header convention."""
    pairs = []
    s = set(h)
    for c in h:
        m = re.fullmatch(r"(prop|aprop)(\d+[ab]?)", c)
        if m:
            p = ("par" if m.group(1) == "prop" else "apar") + m.group(2)
            if p in s:
                pairs.append((c, p))
        m = re.fullmatch(r"mod(\d)code", c)
        if m and "mod%sparam" % m.group(1) in s:
            pairs.append((c, "mod%sparam" % m.group(1)))
        m = re.fullmatch(r"T(\d)Code(\d)", c)
        if m and "T%sParam%s" % m.groups() in s:
            pairs.append((c, "T%sParam%s" % m.groups()))
        m = re.fullmatch(r"(\w+Mod\d)Code", c)
        if m and m.group(1) + "Param" in s:
            pairs.append((c, m.group(1) + "Param"))
        m = re.fullmatch(r"mod (\d)", c)
        if m and "mod %s param" % m.group(1) in s:
            pairs.append((c, "mod %s param" % m.group(1)))
        m = re.fullmatch(r"b?\s*mod (\d)", c)
    return pairs


def skills(x, args):
    K = x.rows("skills")
    names = [r["skill"] for r in K]
    low = {}
    for i, n in enumerate(names):
        low.setdefault(ci(n), i)
    B = {}

    def add(b, v):
        n = ci(v)
        if n in low:
            B.setdefault(b, set()).add(low[n])
            return
        k = num(v)
        if k is not None and "Id" in K[0] and k in idx:
            B.setdefault(b, set()).add(idx[k])

    idx = {num(r["Id"]): i for i, r in enumerate(K)}
    desc = {ci(r["skilldesc"]): r for r in x.rows("skilldesc")}
    for i, r in enumerate(K):
        if r["charclass"]:
            d = desc.get(ci(r["skilldesc"]))
            if d and d.get("SkillPage") in ("1", "2", "3"):
                B.setdefault("class_tree", set()).add(i)
    for r in x.rows("monstats"):
        for k in range(1, 9):
            add("monster", r.get("Skill%d" % k, ""))
    for r in x.rows("hireling"):
        for k in range(1, 7):
            add("hireling", r.get("Skill%d" % k, ""))
    for r in x.rows("charstats"):
        add("charstats", r.get("StartSkill", ""))
        for k in range(1, 11):
            add("charstats", r.get("Skill %d" % k, ""))
    props = {r["code"] for r in x.rows("properties") if r["func1"] in PROP_SKILL_FUNCS}
    for tname in ("uniqueitems", "setitems", "magicprefix", "magicsuffix", "rareprefix", "raresuffix", "runes",
                  "gems", "cubemain", "automagic"):
        h, rows = x.t(tname)
        for cc, pc in skill_param_columns(h):
            for r in rows:
                if r[cc] in props:
                    add("item_property", r[pc])
    # sumskill of a reached skill
    reached = set().union(*B.values()) if B else set()
    for i in list(reached):
        for k in range(1, 6):
            add("sumskill", K[i].get("sumskill%d" % k, ""))
    reached = set().union(*B.values())
    un = [i for i in range(len(K)) if i not in reached]
    order = ["class_tree", "monster", "hireling", "charstats", "item_property", "sumskill"]
    line("skills", len(K), [(k, len(B.get(k, ()))) for k in order], un,
         " reached=%d" % len(reached))
    show("skill", ["%d %s charclass=%s" % (i, names[i], K[i]["charclass"] or "-") for i in un], args)
    return un


# ------------------------------------------------------------------ states

def states(x, args):
    S = x.rows("states")
    names = [r["state"] for r in S]
    ref = {}
    for t, cols in (("skills", ["aurastate", "auratargetstate", "passivestate", "State1", "State2", "State3",
                                "nocostinstate"]),
                    ("misc", ["state", "cstate1", "cstate2"])):
        for r in x.rows(t):
            for c in cols:
                if r.get(c):
                    ref.setdefault(ci(r[c]), set()).add(t)
    un = [i for i, n in enumerate(names) if ci(n) not in ref]
    line("states", len(S), [("skills", sum(1 for n in names if "skills" in ref.get(ci(n), ()))),
                            ("misc", sum(1 for n in names if "misc" in ref.get(ci(n), ())))], un)
    show("state", ["%d %s" % (i, names[i]) for i in un], args)
    print("SURVEY table=states.ids unreached_ids=%s" % ",".join(str(i) for i in un))
    return un


# ------------------------------------------------------------------ items

def items(x, args):
    allr = []
    for t in ("weapons", "armor", "misc"):
        for r in x.rows(t):
            if r.get("code"):
                allr.append((t, r))
    T = x.rows("itemtypes")
    tcode = {ci(r["Code"]): i for i, r in enumerate(T)}

    def of_type(tc, want):
        """tc is of type want (equiv chain), by code."""
        seen = set()
        todo = [tc]
        while todo:
            c = ci(todo.pop())
            if c == want:
                return True
            if c in seen or c not in tcode:
                continue
            seen.add(c)
            r = T[tcode[c]]
            todo += [r["Equiv1"], r["Equiv2"]]
        return False

    B = {}
    # auto TCs (items/tc I1): per item type with TreasureClass != 0
    auto_types = [r["Code"].strip() for r in T if num(r["TreasureClass"])]
    for n, (t, r) in enumerate(allr):
        if r.get("quest") not in ("", "0", None):
            continue
        if num(r.get("spawnable")) in (None, 0):
            continue
        lv = num(r.get("level")) or 0
        if not (0 < lv <= 96):  # the windows L-3 < level <= L for L = 3, 6, ..., 96
            continue
        for tc in auto_types:
            if of_type(r["type"], ci(tc)) and (ci(tc) == "tpot" or not of_type(r["type"], "tpot")):
                B.setdefault("auto_tc", set()).add(n)
                break
    codes = {ci(r["code"]): n for n, (t, r) in enumerate(allr)}
    for r in x.rows("treasureclassex"):
        for k in range(1, 11):
            c = ci(r.get("Item%d" % k, ""))
            if c in codes:
                B.setdefault("tc_explicit", set()).add(codes[c])
    h, W = x.t("weapons")
    vend = [c[:-8] for c in h if c.endswith("MagicMax")]
    for n, (t, r) in enumerate(allr):
        if num(r.get("spawnable")) in (None, 0):
            continue
        for v in vend:
            if num(r.get(v + "Max")) or num(r.get(v + "MagicMax")):
                B.setdefault("vendor", set()).add(n)
    for r in x.rows("cubemain"):
        for col in ("output", "output b"):
            tok = ci(re.split(r"[,\[\]\"]", r.get(col, ""))[0])
            if tok in codes:
                B.setdefault("cube_output", set()).add(codes[tok])
    for r in x.rows("charstats"):
        for k in range(1, 11):
            c = ci(r.get("item%d" % k, ""))
            if c in codes:
                B.setdefault("charstats", set()).add(codes[c])
    for r in x.rows("monequip"):
        for k in range(1, 4):
            c = ci(r.get("item%d" % k, ""))
            if c in codes:
                B.setdefault("monequip", set()).add(codes[c])
    reached = set().union(*B.values())
    quest = {n for n, (t, r) in enumerate(allr) if r.get("quest") not in ("", "0", None)}
    un = [n for n in range(len(allr)) if n not in reached and n not in quest]
    order = ["auto_tc", "tc_explicit", "vendor", "cube_output", "charstats", "monequip"]
    line("items", len(allr), [(k, len(B.get(k, ()))) for k in order], un,
         " reached=%d quest_apart=%d" % (len(reached), len(quest - reached)))
    for t in ("weapons", "armor", "misc"):
        idxs = [n for n, (tt, r) in enumerate(allr) if tt == t]
        print("SURVEY table=%s rows=%d reached=%d quest_apart=%d unreached=%d" % (
            t, len(idxs), sum(1 for n in idxs if n in reached), sum(1 for n in idxs if n in quest and n not in reached),
            sum(1 for n in idxs if n in un)))
    show("item", ["%s %s %s spawnable=%s level=%s" % (allr[n][0], allr[n][1]["code"], allr[n][1]["name"],
                                                      allr[n][1].get("spawnable"), allr[n][1].get("level"))
                  for n in un], args)
    return un


TABLES = {"levels": levels, "monstats": monstats, "skills": skills, "states": states, "items": items}


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("excel_dir")
    ap.add_argument("--table", choices=sorted(TABLES))
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--rows", type=int, default=12)
    args = ap.parse_args()
    x = X(args.excel_dir)
    for name in ([args.table] if args.table else list(TABLES)):
        TABLES[name](x, args)


if __name__ == "__main__":
    main()
