#!/usr/bin/env python3
"""Checker of plan 0038 batch H1c (run:2026-10-27-sweep-d2s-legacy): the loads of the `leg*` builds
(tools/d2s_recipes/leg*.json) logged by tools/gdb/d2s-h1c.gdb through tools/h1c_sessions.py.

    python3 -I tools/sweep_h1c.py check <excel-dir> <cases-dir> <logs-dir>

For each case (<cases-dir>/<case>/<Name>.d2s, the build) it reads <logs-dir>/h1c-s1-<seed>-<case>.log and the file the
game wrote back (<logs-dir>/h1c-s1-<seed>-<case>-saves/<case>/<Name>.d2s, version 96) and compares, per lane/a72
review ruling 3 of plan 0038: (a) the reader path and its return (LEG, the section calls and their returns, LEGR, RSV,
PLD; for 92 RSTV, RSKC, RSEC, RSV, PLD); (b) the write-back field by field with the build: header, stats, skills,
hotkeys and mouse skills, every item (code, quality, unique or set row, seed, position), the mercenary (seed, name,
Id, experience) and its items; and the per-case lines (mercenary calls, version-71 inserts, the unique builder's
restore branch, NewCharLegacy). Prints one line per comparison group, MISMATCH lines, a total; exits 0 only when
nothing mismatched. A value that the write-back changes on purpose (the new-character case) is checked against the
model of that case, not the build. Stdlib only.
"""
import glob
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import d2s  # noqa: E402

CASES = {  # case: (name, seed)
    "leg87merc": ("Leg87Merc", 27301), "leg87new": ("Leg87New", 27302), "leg71merc": ("Leg71Merc", 27303),
    "leg71uniq": ("Leg71Uniq", 27304), "leg92props": ("Leg92Props", 27305), "leg71sock": ("Leg71Sock", 27306),
    "leg71act2": ("Leg71Act2", 27307),
}


class Ck:
    def __init__(self):
        self.n = 0
        self.bad = 0

    def eq(self, group, what, got, want):
        self.n += 1
        if got != want:
            self.bad += 1
            print("MISMATCH %s: %s: got %r want %r" % (group, what, got, want))
        return got == want


def events(path):
    out = []
    for ln in open(path, errors="replace"):
        tag, _, rest = ln.partition(" ")
        if rest.startswith("{"):
            try:
                out.append((tag, json.loads(rest)))
            except ValueError:
                pass
    return out


def of(ev, tag):
    return [d for t, d in ev if t == tag]


def sections(ev):
    """The legacy reader's section calls in order with their returns: [(name, eax)]."""
    res = []
    for t, d in ev:
        if t == "SEC":
            res.append([d["sec"], None])
        elif t == "SECR" and res:
            for r in reversed(res):
                if r[0] == d["sec"] and r[1] is None:
                    r[1] = d["eax"]
                    break
    return [tuple(r) for r in res]


def items_of(f):
    it = f["items"]
    return it["items"] if isinstance(it, dict) else it


def flat_stats(f):
    return {(sid, par): v for sid, par, v in f["stats"]}


def item_key(it):
    """code or class index, quality, unique/set row, position."""
    return (it.get("quality"), it.get("location"), it.get("x"), it.get("y"))


def check_case(ck, case, name, seed, cases, logs, isc, kinds):
    stem = os.path.join(logs, "h1c-s1-%d-%s" % (seed, case))
    ev = events(stem + ".log")
    b = open(os.path.join(cases, case, name + ".d2s"), "rb").read()
    w = open(os.path.join(stem + "-saves", case, name + ".d2s"), "rb").read()
    ver = d2s.u32(b, 4)
    g = d2s.parse(w, isc, kinds, extended=True)
    gh = g["header"]
    f = d2s.parse_legacy(b, isc, kinds) if ver in (71, 87) else d2s.parse(b, isc, kinds, extended=True)
    fh = f["header"]
    G = case
    ck.eq(G, "no LOGERR line", sum(1 for ln in open(stem + ".log", errors="replace") if ln.startswith("LOGERR")), 0)
    ck.eq(G, "build version", ver, {"leg87merc": 87, "leg87new": 87, "leg92props": 92}.get(case, 71))
    ck.eq(G, "written version", gh["version"], 96)
    ck.eq(G, "PLD code", [d["code"] for d in of(ev, "PLD")], [0])
    ck.eq(G, "RSV code and bytes read", [(d["code"], d["nread"]) for d in of(ev, "RSV")], [(0, len(b))])
    if ver < 92:
        ck.eq(G, "LEG (version, length)", [(d["version"], d["len"]) for d in of(ev, "LEG")], [(ver, len(b))])
        ck.eq(G, "LEGR", [d["code"] for d in of(ev, "LEGR")], [0])
        ck.eq(G, "no RHDR (the 96 header reader did not run)", len(of(ev, "RHDR")), 0)
    else:
        ck.eq(G, "no LEG (version 92 goes to D2S_ReadSaveV92)", len(of(ev, "LEG")), 0)
        ck.eq(G, "RHRET code", [d["code"] for d in of(ev, "RHRET")], [0])
        ck.eq(G, "RSTV (version, slots)", [(d["version"], d["count"]) for d in of(ev, "RSTV")], [(92, 16)])
        ck.eq(G, "RSKC (version, count)", [(d["version"], d["count"]) for d in of(ev, "RSKC")], [(92, 30)])
    secs = sections(ev)
    full = ["header", "quests", "waypoints", "npcs", "stats", "skills", "items", "corpses"]
    if case == "leg87new":
        ck.eq(G, "sections: the header only, new-character flag", secs, [("header", 0)])
        ncl = of(ev, "NCL")
        ck.eq(G, "NewCharLegacy called once, returned 0", (len(ncl), [d["eax"] for d in of(ev, "NCLR")]), (1, [0]))
        ck.eq(G, "no mercenary call", (len(of(ev, "MOS")), len(of(ev, "MCR"))), (0, 0))
        # the written character is the new one, not the build
        ck.eq(G, "build header status bit 0", fh["status"] & 1, 1)
        ck.eq(G, "written status (bit 0 clear, expansion)", gh["status"], 0x20)
        ck.eq(G, "written level 1 (build 30)", gh["level"], 1)
        ck.eq(G, "written hotkeys all none", gh["hotkeys"], [0xFFFF] * 16)
        st = flat_stats(g)
        ck.eq(G, "written stats 0..3 = the Sorceress start (10, 35, 25, 10)", [st.get((i, None)) for i in range(4)],
              [10, 35, 25, 10])
        ck.eq(G, "written stat 12 (level) 1, experience absent", (st.get((12, None)), st.get((13, None))), (1, None))
        bst = flat_stats(f)
        ck.eq(G, "the build's stats 0 and 12 are not the written ones", (bst[(0, None)], bst[(12, None)]), (60, 30))
        codes = [i["code"].strip() for i in items_of(g)]
        ck.eq(G, "written items: 4 healing potions, 2 scrolls, a staff (the new character's)",
              sorted(codes), sorted(["hp1"] * 4 + ["tsc", "isc", "sst"]))
        ck.eq(G, "the build has no item", f["items"]["count"], 0)
        ck.eq(G, "written skills all 0 (build had skills)", (sum(g["skills"]), sum(f["skills"])), (0, sum(f["skills"])))
        return
    ck.eq(G, "sections in order, all return 0",
          secs if ver < 92 else [], [(s, 0) for s in full] + ([("items", 0)] if case == "leg87merc" else []) + [("tail", 0)]
          if ver < 92 else [])
    # header, stats, skills, hotkeys, mouse
    ck.eq(G, "name", gh["name"], fh["name"])
    ck.eq(G, "class", gh["cls"], fh["cls"])
    ck.eq(G, "level", gh["level"], fh["level"])
    ck.eq(G, "stats (all of 0..15 the build holds)", flat_stats(g), flat_stats(f))
    ck.eq(G, "skills", g["skills"][:30], list(f["skills"])[:30])
    if ver == 92:
        ck.eq(G, "hotkey slots 0..15", gh["hotkeys"], fh["hotkeys"])
        ck.eq(G, "mouse skills L R swapL swapR", gh["mouse"], fh["mouse"])
        ck.eq(G, "difficulty bytes", gh["difficulty"], fh["difficulty"])
    else:
        hk = [h[0] for h in fh["hotkeys"]]
        want = hk + ([0xFFFF] * 8 if ver == 71 else [44, 42, 0xFFFF, 0xFFFF, 0xFFFF, 0xFFFF, 0xFFFF, 0xFFFF])
        ck.eq(G, "hotkey slots 0..7 (the header) %s" % ("; 8..15 none" if ver == 71 else "; 8, 9 from the tail"),
              gh["hotkeys"][:8] if ver == 71 else gh["hotkeys"][:10], hk if ver == 71 else hk + [44, 42])
        ck.eq(G, "hotkey slots %s none" % ("8..15" if ver == 71 else "10..15"),
              gh["hotkeys"][8:] if ver == 71 else gh["hotkeys"][10:], [0xFFFF] * (8 if ver == 71 else 6))
        ck.eq(G, "left and right skills", gh["mouse"][:2], [fh["left"], fh["right"]])
        ck.eq(G, "swap skills A and B: %s" % ("the tail's (48, 42)" if ver == 87 else "none (no tail)"),
              gh["mouse"][2:], [48, 42] if ver == 87 else [0, 0])
        ck.eq(G, "difficulty byte 0 = 0x80 | act", gh["difficulty"][0], 0x80 | fh["act"])
    # items
    bi, wi = items_of(f), items_of(g)
    ck.eq(G, "item count (top level + socketed)", len(wi), len(bi))
    for k, (x, y) in enumerate(zip(bi, wi)):
        gg = "%s item %d" % (G, k)
        code = x.get("code") or None
        if code is not None:
            ck.eq(gg, "code", y["code"], code)
        if x.get("code") == "jew " or "quality" not in y:
            # a jewel is rolled by the game (the build's quality 2 is not kept); a belt potion has no quality field
            ck.eq(gg, "quality of a jewel (rolled magic by the game) or none for a potion",
                  y.get("quality"), 4 if x.get("code") == "jew " else None)
        else:
            ck.eq(gg, "quality", y.get("quality"), x.get("quality"))
        ck.eq(gg, "location, x, y", (y["location"], y["x"], y["y"]), (x["location"], x["x"], x["y"]))
        seed_b = x.get("unit_seed", x.get("seed"))
        if seed_b:
            ck.eq(gg, "seed", y.get("seed"), seed_b)
        if x.get("quality") in (5, 7) or x.get("qid") is not None:
            row = x.get("file_index", x.get("qid"))
            ck.eq(gg, "unique or set row", y.get("qid"), row)
        if "n_filled" in x and "quality" in y:
            ck.eq(gg, "children", y.get("n_filled"), x["n_filled"])
    if ver == 87:
        for k, (x, y) in enumerate(zip(bi, wi)):
            ck.eq("%s item %d" % (G, k), "property list, defense, durability, version-87 widths",
                  (y.get("props"), y.get("defense"), y.get("maxdur"), y.get("dur")),
                  (x.get("props"), x.get("defense"), x.get("maxdur"), x.get("dur")))
    if ver == 92:
        for k, (x, y) in enumerate(zip(bi, wi)):
            ck.eq("%s item %d" % (G, k), "property list", y.get("props"), x.get("props"))
            ck.eq("%s item %d" % (G, k), "defense, durability, set lists",
                  (y.get("defense"), y.get("maxdur"), y.get("dur"), y.get("set_lists")),
                  (x.get("defense"), x.get("maxdur"), x.get("dur"), x.get("set_lists")))
        rist = {d["unit"]: d for d in of(ev, "RIST")}
        full_stats = [sorted(map(tuple, d["full"])) for d in rist.values()]
        want = sorted((sid, par, val) for sid, par, vals in bi[0]["props"] for val in vals[:1])
        ck.eq(G, "read stat 83/107/188/195/126 values on the cap (RIST, unshifted)",
              sorted(t for t in full_stats[0] if t[0] in (83, 107, 126, 188, 195)),
              sorted(t for t in want if t[0] in (83, 107, 126, 188, 195)))
        return
    # mercenary
    if case in ("leg87merc", "leg71merc", "leg71act2"):
        mos, mosr, mcr, mxo = of(ev, "MOS"), of(ev, "MOSR"), of(ev, "MCR"), of(ev, "MXO")
        ck.eq(G, "ReadMercOldSave called once with the save's version", [d["st"][2] for d in mos], [ver])
        ck.eq(G, "ReadMercOldSave returned 0", [d["eax"] for d in mosr], [0])
        if ver == 71:
            m = f["merc"]
            ck.eq(G, "the JM record read: tag, seed, name", (bytes.fromhex(mos[0]["bytes"])[:2], int.from_bytes(
                bytes.fromhex(mos[0]["bytes"])[2:6], "little"), int.from_bytes(bytes.fromhex(mos[0]["bytes"])[6:8],
                                                                                "little")), (b"JM", m["seed"], m["name"]))
            ck.eq(G, "length 8, no experience conversion", ([d["len"] for d in mosr], len(mxo)), ([8], 0))
            ck.eq(G, "MERC_Create (name, seed, id 0xFFFF, +0x08, dead)", mcr[0]["st"][:5],
                  [m["name"], m["seed"], 0xFFFF, 0, 0])
            ck.eq(G, "written mercenary seed", gh["merc_seed"], m["seed"])
            ck.eq(G, "written mercenary Id (the first row, 1)", gh["merc_type"], 1)
            ck.eq(G, "written mercenary experience (not converted: 0 in the file)", gh["merc_exp"], 2649150)
            ck.eq(G, "written mercenary dead flag", gh["merc_dead"], 0)
            ck.eq(G, "written mercenary item list empty", len(g.get("merc_items", {"items": []})["items"]), 0)
        else:
            m = f["merc"]
            ck.eq(G, "the 0x12-byte record: seed, name word, id, experience as built (sans the +0x114 base)",
                  [m["seed"], m["id"], m["exp"]], [12345, 1, 100000])
            rec = bytes.fromhex(mos[0]["bytes"])
            ck.eq(G, "record bytes +0x06 seed, +0x0C id, +0x0E start of experience",
                  (int.from_bytes(rec[6:10], "little"), int.from_bytes(rec[12:14], "little"),
                   int.from_bytes(rec[14:18], "little")), (m["seed"], m["id"], m["exp"]))
            ck.eq(G, "MercExpFromOldSave called once (version <= 89) with (id, experience)",
                  [(d["edx"] & 0xFFFF, d["st"][0]) for d in mxo], [(m["id"], m["exp"])])
            conv = of(ev, "MXOR")[0]["eax"]
            ck.eq(G, "converted experience differs from the file's", conv != m["exp"], True)
            ck.eq(G, "written mercenary experience = the converted", gh["merc_exp"], conv)
            ck.eq(G, "MERC_Create seed and id", (mcr[0]["st"][1], mcr[0]["st"][2]), (m["seed"], m["id"]))
            ck.eq(G, "written mercenary seed, Id, name (name word minus the record's +0x114 base)",
                  (gh["merc_seed"], gh["merc_type"], gh["merc_name"]), (m["seed"], m["id"], m["name"]))
            ck.eq(G, "written mercenary dead flag", gh["merc_dead"], 0)
            ck.eq(G, "MOSR length = 0x12 + the item list", [d["len"] for d in mosr], [46])
            mi = g.get("merc_items", {"items": []})["items"]
            ck.eq(G, "written mercenary items = the built list (cap, equipped head)",
                  [(i["code"], i["location"], i["body"]) for i in mi], [("cap ", 1, 1)])
    # the version-71 lists
    if ver == 71:
        ck.eq(G, "V71 list reader called once, returned 0", (len(of(ev, "V71")), [d["eax"] for d in of(ev, "V71R")]),
              (1, [0]))
        ck.eq(G, "item records created = the built records", len(of(ev, "OIC")), f["items"]["count"] + sum(
            1 for i in bi if i["location"] == 6))
    if case == "leg71sock":
        ins = of(ev, "INS")
        ck.eq(G, "InsertSocket from the version-71 site 0x005311B5 (return 0x005311BA) twice, child then parent ids",
              [(d["ret"], d["child"] - d["parent"]) for d in ins], [(0x5311BA, 1)] * 2)
        ck.eq(G, "no call from the other site (0x005313F5)", sum(1 for d in ins if d["ret"] == 0x5313F5), 0)
        ck.eq(G, "InsertSocket returned 1 each time", [d["eax"] for d in of(ev, "INSR")], [1, 1])
        ck.eq(G, "children in the written list: location 6 right after each parent",
              [i["location"] for i in wi], [0, 6, 0, 6])
    if case == "leg71uniq":
        ub = of(ev, "UB0")
        ubr = of(ev, "UBR")
        ck.eq(G, "unique builder entered for the two uniques, rec+0x2C = 1 (restore) both", [d["r2c"] for d in ub], [1, 1])
        ck.eq(G, "rec+0x40 = the row itself (0, 1)", [d["r40"] for d in ubr], [0, 1])
        ck.eq(G, "restore branch taken both times", len(ubr), 2)
        ck.eq(G, "written unique rows 0 and 1; set rows 0 and 1",
              [i.get("qid") for i in wi if i.get("quality") in (5, 7)], [0, 0, 1, 1])
        ck.eq(G, "item version the builder saw (not 0: the version-0 half is not reached)", [d["version"] for d in ub],
              [ub[0]["version"]] * 2)
        ck.eq(G, "...and it is not 0", ub[0]["version"] != 0, True)
        ck.eq(G, "seeds distinct on the set item: unit 1234567 written", wi[1]["seed"], 1234567)


def main(argv):
    if len(argv) != 4 or argv[0] != "check":
        print(__doc__)
        return 2
    excel, cases, logs = argv[1:]
    isc, kinds = d2s.load_isc(excel), d2s.load_kinds(excel)
    ck = Ck()
    for case, (name, seed) in CASES.items():
        n0, b0 = ck.n, ck.bad
        check_case(ck, case, name, seed, cases, logs, isc, kinds)
        print("%-10s %3d comparisons, %d mismatch" % (case, ck.n - n0, ck.bad - b0))
    print("H1C %d comparisons, %d failing" % (ck.n, ck.bad))
    return 1 if ck.bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
