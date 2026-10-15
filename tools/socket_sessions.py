#!/usr/bin/env python3
"""Session layouts for plan 0029 Phase 2 (run:2026-10-15-sockets): one test character per session, its recipe and its
insert plan.

    python3 -I tools/socket_sessions.py write [--excel DIR]     # tools/d2s_recipes/sock-<name>.json and
                                                                # tools/gdb/sock-<name>.plan for every session
    python3 -I tools/socket_sessions.py list                    # the sessions and what each holds

Each session is a list of jobs. A job is a socketed base (equipped in a paper-doll slot, or packed into the inventory
or the Horadric Cube) and the socket fillers to insert into it, in order; the base gets exactly that many sockets
unless the job gives "sockets". A job may also be a loose item (a refusal case: an unsocketed base, a potion). The
fillers are packed into the cells left over, inventory first. The plan (tools/d2pilot.py insert tokens) opens the
inventory and the cube, then inserts every filler into its base in job order; "try" entries add the refusal clicks.
The recipes carry the SocketNova character of tools/d2s_recipes/socketnova.json (expansion Sorceress, level 80) and
are built on its base save (smpsor-l50.d2s). Stdlib only.
"""
import argparse
import copy
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import props  # noqa: E402

RECIPES = os.path.join(HERE, "d2s_recipes")
PLANS = os.path.join(HERE, "gdb")
INV_W, INV_H, CUBE_W, CUBE_H = 10, 4, 3, 4
CUBE_AT = (8, 2)          # the cube's own cell in the inventory (2 x 2)

GEMS = ("gcv gfv gsv gzv gpv gcb gfb gsb glb gpb gcg gfg gsg glg gpg gcr gfr gsr glr gpr "
        "gcw gfw gsw glw gpw gcy gfy gsy gly gpy skc skf sku skl skz").split()      # gems rows 0..34
JEWELS = [{"code": "jew", "suffix": 260}, {"code": "jew", "suffix": 307}, {"code": "jew", "suffix": 392},
          {"code": "jew", "quality": "rare"}, {"code": "jew", "suffix": 350}, {"code": "jew", "suffix": 664}]
SFX = 382        # magicsuffix "of Strength" (mele, glov, shld): the magic weapon and shield bases
SFX_HELM = 305   # "of Brilliance" (helm, scep)
R = {n: "r%02d" % (i + 1) for i, n in enumerate(
    "El Eld Tir Nef Eth Ith Tal Ral Ort Thul Amn Sol Shael Dol Hel Io Lum Ko Fal Lem Pul Um Mal Ist Gul Vex Ohm Lo "
    "Sur Ber Jah Cham Zod".split())}


def runes(names):
    return [{"code": R[n]} for n in names.split()]


def gems(codes):
    return [{"code": c} for c in codes]


def J(base, fill, eq=None, **kw):
    d = dict(base=base, fill=fill, **kw)
    if eq:
        d["eq"] = eq
    return d


def gem_sessions():
    """Every gem (7 types x 5 grades) into each item class (gemapplytype 0 weapon, 1 helm/armour, 2 shield), plus the
    jewels: five sessions, each with a helm, a body armour, a weapon and a shield equipped and two bases packed."""
    w, a, s = list(GEMS), list(GEMS), list(GEMS)
    jw = list(JEWELS)
    out = []
    for k in range(5):
        def take(lst, n):
            got = lst[:n]
            del lst[:n]
            return got
        jobs = [J("ghm", gems(take(a, 3)), "head"), J("aar", gems(take(a, 4)), "tors"),
                J("crs", gems(take(w, 6)), "rarm"), J("uit", gems(take(s, 4)), "larm"),
                J("uit", gems(take(s, 4))), J("crs", gems(take(w, 6)) or [])]
        for j in jobs:      # fill short bases with jewels
            if len(j["fill"]) < 1:
                j["fill"] = [jw.pop(0)] if jw else []
        out.append(("gems%d" % (k + 1), [j for j in jobs if j["fill"]]))
    assert not w and not a and not s, (w, a, s)
    return out


SESSIONS = []


def sessions():
    if SESSIONS:
        return SESSIONS
    S = gem_sessions()
    # the jewels into one more shield and weapon of the last gem session's class mix
    S.append(("jewels", [J("crs", copy.deepcopy(JEWELS[:4]), "rarm"), J("uit", copy.deepcopy(JEWELS[4:]), "larm"),
                         J("ghm", [{"code": "jew", "suffix": 307}, {"code": "gpw"}], "head")]))
    # runewords
    S.append(("rw1", [J("cap", runes("Ort Sol"), "head"), J("qui", runes("Tal Eth"), "tors"),
                      J("ssd", runes("Tir El"), "rarm"), J("sml", runes("Eth Lum"), "larm"),
                      J("sml", runes("Shael Eth")), J("lrg", runes("Ko Ko Mal")), J("cap", runes("Nef Tir"))]))
    S.append(("rw2", [J("skp", runes("Ort Sol"), "head"), J("lea", runes("Tal Eth"), "tors"),
                      J("ssd", runes("Amn Tir"), "rarm"), J("sml", runes("Shael Eth"), "larm"),
                      J("sml", runes("Eth Lum")), J("kit", runes("Ko Ko Mal")), J("mst", runes("Thul Io Nef"))]))
    S.append(("rw3", [J("ghm", runes("Nef Sol Ith"), "head"), J("brs", runes("Fal Um Pul"), "tors"),
                      J("ssd", runes("Tir El"), "rarm"), J("sml", runes("Eth Lum"), "larm"),
                      J("tow", runes("Ko Ko Mal")), J("mst", runes("Ith El Eth")), J("bwn", runes("Dol Io"))]))
    S.append(("rw4", [J("cap", runes("Nef Tir"), "head"), J("aar", runes("Ral Ohm Sur Eth"), "tors"),
                      J("mst", runes("Thul Io Nef"), "rarm"), J("sml", runes("Eth Lum"), "larm"),
                      J("brs", runes("Jah Ith Ber")), J("sbw", runes("Ort Eth"))]))
    S.append(("rw5", [J("crn", runes("Lem Ist Io"), "head"), J("gth", runes("Shael Um Pul Lum"), "tors"),
                      J("wsp", runes("Eth Ral Ort Tal"), "rarm"), J("pa1", runes("Vex Ohm Ist Dol")),
                      J("lax", runes("Fal Ohm Ort Jah")), J("lea", runes("Nef Lum"))]))
    S.append(("rw6", [J("ghm", runes("Nef Sol Ith"), "head"), J("ful", runes("Ral Ohm Sur Eth"), "tors"),
                      J("fla", runes("Ko Vex Pul Thul"), "rarm"), J("2ax", runes("Amn Ral Mal Ist Ohm")),
                      J("rng", runes("Shael Um Thul")), J("cst", runes("Tir Ral"))]))
    S.append(("rw7", [J("cap", runes("Ort Sol"), "head"), J("ltp", runes("Hel Lum Fal"), "tors"),
                      J("crs", runes("Sur Cham Amn Lo"), "rarm"), J("sml", runes("Shael Eth"), "larm"),
                      J("brs", runes("Sol Um Um")), J("lrg", runes("Ko Ko Mal"))]))
    # special cases and refusals
    S.append(("cases1", [
        J("sml", runes("Eth Lum"), "larm", quality="low"),               # low quality: matches (Phase 1b case)
        J("sml", runes("Shael Eth"), quality="superior"),                # superior: matches
        J("cap", runes("Eth Lum")),                                      # Splendor's runes in a helm: wrong type
        J("sml", runes("Lum Eth")),                                      # Splendor's runes reversed: wrong order
        J("sml", runes("Eth Lum"), suffix=SFX),                          # a magic base
    ]))
    S.append(("cases2", [
        J("bsh", runes("Eth Lum"), quality="rare"),                      # a rare base
        J("spk", runes("Eth Lum"), quality="crafted"),                   # a crafted base
        J("aar", runes("Ral Ohm Sur"), "tors"),                          # the first 3 of Bramble in 3 sockets
        J("crs", runes("Tal Thul Ort Amn"), "rarm"),                     # Spirit: a server (ladder) row
        J("leg", runes("Thul Io Nef")),                                  # Black in Wirt's Leg: a quest base
    ]))
    S.append(("forced", [
        J("crs", gems("gcv gcy gcb gcg gcr gcw".split()), "rarm", suffix=SFX),   # magic, 6 sockets (built state)
        J("uit", gems("gpv gpy gpb gpg".split()), "larm", suffix=SFX),           # magic, 4 sockets
        J("crs", gems("gsv gsy gsb gsg gsr".split()), quality="rare"),           # rare, 5 sockets (built state)
        J("lsd", gems("gzv gly glb glg".split()), quality="crafted"),            # crafted, 4 sockets (built state)
        J("ghm", gems("gfv gfy gfb".split()), "head", quality="low"),            # low quality, 3 sockets
    ]))
    S.append(("refuse", [
        J("ssd", runes("Tir El"), "rarm"),                               # Steel, then a gem onto the full sword
        J("sml", [{"code": "gcv"}], "larm"),
        J("cap", [{"code": "gcy"}], "head", identified=False, suffix=SFX_HELM, sockets=2),   # unidentified parent
        J("lrg", [{"code": "jew", "suffix": 260, "identified": False}, {"code": "gcb"}]),  # unidentified jewel first
        J("buc", [], loose=True),                                        # no sockets
        J("hp1", [], loose=True),                                        # a potion: not a socket filler
    ], [("gfv", "ssd"), ("gfv", "buc"), ("hp1", "lrg")]))
    # classic (game "classic", tools/d2s_recipes/socketclassic.json's character on its classic base save)
    S.append(("classic1", [J("ghm", gems("gsv gzv gpv".split()), "head"), J("qui", gems("gcb gfb".split()), "tors"),
                           J("crs", gems("gsb glb gpb gcg gfg gsg".split()), "rarm"),
                           J("sml", gems("glg gpg".split()), "larm"), J("lrg", gems("gcr gfr gsr".split())),
                           J("ssd", gems("glr gpr".split())), J("cap", gems("gcw skc".split()))], (), "classic"))
    S.append(("classic2", [J("cap", [], sockets=2), J("sml", [{"code": "gcv"}], sockets=2)],
              [("r01", "cap")], "classic"))
    # a rune made in the session: the cube's 3 Tir -> Nef (stock CubeMain), then Black (Thul Io Nef) completed by it (the output lands in the cube's last cell)
    S.append(("cubenef", [J("mst", runes("Thul Io"), sockets=3)], (), "expansion",
              {"stock": runes("Tir Tir Tir"),
               "tokens": ["click:{0}", "click:cube:0,0", "click:{1}", "click:cube:1,0", "click:{2}", "click:cube:2,0",
                          "xy:240,340", "sleep:1", "shot:workspace/logs/sock-cubenef-cube.png", "cube:2,3>{mst}"]}))
    SESSIONS.extend(S)
    return SESSIONS


class Packer:
    def __init__(self):
        self.used = {"inv": set(), "cube": set()}
        for x in range(2):
            for y in range(2):
                self.used["inv"].add((CUBE_AT[0] + x, CUBE_AT[1] + y))

    def place(self, w, h):
        for page, (W, H) in (("inv", (INV_W, INV_H)), ("cube", (CUBE_W, CUBE_H))):
            for y in range(H - h + 1):
                for x in range(W - w + 1):
                    cells = {(x + i, y + j) for i in range(w) for j in range(h)}
                    if not cells & self.used[page]:
                        self.used[page] |= cells
                        return page, x, y
        raise ValueError("no room for a %dx%d item" % (w, h))


def layout(T, name, jobs, tries=(), extra=None):
    codes = {r[0x80:0x84].decode("latin1").strip(): i for i, r in enumerate(T.items)}

    def size(code):
        b = T.base(codes[code])
        return b["invw"], b["invh"]

    P = Packer()
    items, plan, where = [{"code": "box", "store": "inventory", "x": CUBE_AT[0], "y": CUBE_AT[1]}], \
        ["key:i", "rclick:inv:%d,%d,2,2" % CUBE_AT], {}
    placed = []
    order = sorted(range(len(jobs)), key=lambda k: -(size(jobs[k]["base"])[0] * size(jobs[k]["base"])[1]))
    for k in order:
        j = jobs[k]
        spec = {"code": j["base"]}
        for key in ("quality", "suffix", "identified"):
            if key in j:
                spec[key] = j[key]
        if not j.get("loose"):
            spec["sockets"] = j.get("sockets", len(j["fill"]))
        w, h = size(j["base"])
        if "eq" in j:
            spec["equip"] = j["eq"]
            cell = "eq:%s" % j["eq"]
        else:
            page, x, y = P.place(w, h)
            spec.update(store="inventory" if page == "inv" else "cube", x=x, y=y)
            cell = "%s:%d,%d,%d,%d" % (page, x, y, w, h)
        where.setdefault(j["base"], cell)
        placed.append((k, spec, cell))
    placed.sort()
    fills = []
    for k, spec, cell in placed:
        items.append(spec)
        for c in jobs[k]["fill"]:
            page, x, y = P.place(1, 1)
            cs = dict(c, store="inventory" if page == "inv" else "cube", x=x, y=y)
            items.append(cs)
            fills.append(("%s:%d,%d" % (page, x, y), cell, c["code"]))
    tcells = {}
    for child, _ in tries:
        if child not in tcells and not any(i.get("code") == child and "sockets" not in i for i in items
                                           if i.get("store")):
            page, x, y = P.place(1, 1)
            items.append({"code": child, "store": "inventory" if page == "inv" else "cube", "x": x, "y": y})
            tcells[child] = "%s:%d,%d" % (page, x, y)
    for k, spec, cell in placed:
        if jobs[k].get("loose"):
            if spec["code"] not in tcells:
                tcells[spec["code"]] = cell
    # inserts in job order; the refusal tries after the inserts they need
    for src, dst, _ in fills:
        plan.append("%s>%s" % (src, dst))
    for child, parent in tries:
        src = tcells.get(child)
        if src is None:
            src = [s for s, d, c in fills if c == child][0]
        plan.append("%s>%s" % (src, where[parent]))
    if extra:
        cells = []
        for c in extra.get("stock", []):
            page, x, y = P.place(1, 1)
            items.append(dict(c, store="inventory" if page == "inv" else "cube", x=x, y=y))
            cells.append("%s:%d,%d" % (page, x, y))
        for t in extra.get("tokens", []):
            plan.append(t.format(*cells, **{k: v for k, v in where.items()}))
    plan.append("shot:workspace/logs/sock-%s-end.png" % name)
    return items, plan


def base_recipe(game="expansion"):
    with open(os.path.join(RECIPES, "socketnova.json" if game == "expansion" else "socketclassic.json")) as f:
        r = json.load(f)
    r.pop("items")
    return r


def cmd_write(ns):
    T = props.Tables(ns.excel)
    codes = {r[0x80:0x84].decode("latin1").strip(): i for i, r in enumerate(T.items)}
    bad = [c for c in GEMS if not T.is_type(codes[c], 20)]
    if bad:
        raise SystemExit("not gems: %s" % bad)
    for i, s in enumerate(sessions()):
        name, jobs = s[0], s[1]
        tries = s[2] if len(s) > 2 else ()
        game = s[3] if len(s) > 3 else "expansion"
        items, plan = layout(T, name, jobs, tries, s[4] if len(s) > 4 else None)
        r = base_recipe(game)
        r["name"] = "Sock" + name[0].upper() + "".join(ch for ch in name[1:] if ch.isalpha()) + \
            "".join(chr(ord("a") + int(ch)) for ch in name if ch.isdigit())
        r["seed"] = 742902901 + i
        r["items"] = items
        with open(os.path.join(RECIPES, "sock-%s.json" % name), "w") as f:
            json.dump(r, f, indent=1)
            f.write("\n")
        with open(os.path.join(PLANS, "sock-%s.plan" % name), "w") as f:
            f.write("# tools/d2pilot.py insert tokens for tools/d2s_recipes/sock-%s.json (tools/socket_sessions.py)\n"
                    % name)
            f.write("\n".join(plan) + "\n")
        print("%-8s %-12s %2d items, %2d inserts" % (name, r["name"], len(items), sum(">" in t for t in plan)))
    return 0


def cmd_list(ns):
    for s in sessions():
        print(s[0])
        for j in s[1]:
            print("   %-4s %-6s %s %s" % (j["base"], j.get("eq", ""), [c["code"] for c in j["fill"]],
                                       {k: v for k, v in j.items() if k not in ("base", "fill", "eq")}))
        if len(s) > 2:
            print("   tries %s" % (s[2],))
    return 0


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=("write", "list"))
    ap.add_argument("--excel", default=props.EXCEL)
    ns = ap.parse_args(argv)
    return cmd_write(ns) if ns.cmd == "write" else cmd_list(ns)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
