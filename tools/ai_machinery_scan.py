#!/usr/bin/env python3
"""Static reads of the monster AI machinery (plan 0052 phase 1.1, `lane/r52`) from the pinned Game.exe and the
shipped excel text files.

    python3 -I tools/ai_machinery_scan.py tables [--exe PATH]
    python3 -I tools/ai_machinery_scan.py rows [--exe PATH] [--excel DIR]
    python3 -I tools/ai_machinery_scan.py entries [--exe PATH] [--excel DIR]
    python3 -I tools/ai_machinery_scan.py pool [--excel DIR]

- `tables`: the dispatch tables the machinery reads, as dwords from the image: the monster event functions
  (`g_MonEventFuncs`, 0x006E2490, 16 kinds), the AI unit-search kinds (0x006E3300, 13 pairs {walker, callback}), the
  path planner functions (`g_PathPlanFuncs`, 0x006EB6D8, 17 types) and the path type flags (0x006EB690, 17 dwords).
  Lines `EV <kind> <fn>`, `SK <kind> <walker> <callback>`, `PF <type> <fn>`, `PT <type> <flags>`.
- `rows`: every row of the AI table (`g_MonAiTable`, 0x0073CA18, 148 rows of 16 bytes) and of the 18 state rows that
  follow it (0x0073D358, indexed by the AI control's state word): `ROW <i> kind=<+0> init=<+4> think=<+8> alt=<+C>
  name=<monai name> mon=<MonStats rows naming it>`, `ST <i> ...` for the state rows, then count lines:
  `KIND <k> <rows>`, `FN distinct think functions`, `SHARED <fn> <rows...>` for a think function on several rows,
  `UNUSED <i> <name>` for a table row no MonStats row names.
- `entries`: where hirelings and summons enter the table: per Hireling row (`Class`) and per summon class (Skills
  `summon`, PetType `mclass1..4`), the MonStats row's `AI` index and that row's think function.
  Lines `HIRE <hireling> <class id> <monstats Id> ai=<i> <name> think=<fn>`, `SUMMON <src> <class> ...`.

- `pool`: per AI index, the Levels pool slots (`mon1..10`, `nmon1..10`, `umon1..10`, every level row) whose MonStats
  `Id` uses it, and the number of distinct levels: `POOL <ai> <name> slots=<n> levels=<n>`, sorted by slots, then
  `SURVEY pool slots=<total> ais=<AIs with a slot>`.

The AI index of a MonStats row is its `AI` column name looked up in `monai.txt` by row order (the table's rows are
in `monai.txt` order: 148 data rows, the table holds 148). Stdlib only. Read-only.
"""
import argparse
import collections
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import pe_info  # noqa: E402

ROOT = os.path.dirname(HERE)
EXE = os.path.join(ROOT, "workspace", "install", "app", "game.exe")
EXCEL = os.path.join(ROOT, "workspace", "merged", "data", "global", "excel")

AI_TABLE = 0x0073CA18
AI_ROWS = 148
AI_STATES = 0x0073D358
AI_STATE_ROWS = 18
EVENT_FUNCS = 0x006E2490
SEARCH_KINDS = 0x006E3300
PLAN_FUNCS = 0x006EB6D8
PLAN_FLAGS = 0x006EB690


class Image:
    def __init__(self, path):
        self.p = pe_info.parse(path)
        self.data = open(path, "rb").read()
        self.base = self.p["image_base"]

    def read(self, va, n):
        for s in self.p["sections"]:
            a = self.base + s["va"]
            if a <= va < a + max(s["vsize"], s["rsize"]):
                off = s["raw"] + va - a
                return self.data[off:off + n]
        raise ValueError("%#x outside the image" % va)

    def dwords(self, va, n):
        return struct.unpack("<%dI" % n, self.read(va, 4 * n))


def txt_rows(path):
    with open(path, encoding="latin-1") as f:
        lines = f.read().split("\n")
    head = lines[0].rstrip("\r").split("\t")
    out = []
    for ln in lines[1:]:
        ln = ln.rstrip("\r")
        if not ln:
            continue
        cells = ln.split("\t")
        out.append(dict(zip(head, cells + [""] * (len(head) - len(cells)))))
    return out


def ai_names(excel):
    return [r["AI"] for r in txt_rows(os.path.join(excel, "monai.txt"))]


def monstats(excel):
    return txt_rows(os.path.join(excel, "monstats.txt"))


def ai_index(names, name):
    return names.index(name) if name in names else -1


def row(img, base, i):
    return img.dwords(base + 16 * i, 4)


def cmd_tables(img):
    for k, f in enumerate(img.dwords(EVENT_FUNCS, 16)):
        print("EV %d 0x%08X" % (k, f))
    for k in range(13):
        w, cb = img.dwords(SEARCH_KINDS + 8 * k, 2)
        print("SK %d %d 0x%08X" % (k, w, cb))
    for t, f in enumerate(img.dwords(PLAN_FUNCS, 17)):
        print("PF %d 0x%08X" % (t, f))
    for t, f in enumerate(img.dwords(PLAN_FLAGS, 17)):
        print("PT %d 0x%08X" % (t, f))


def cmd_rows(img, excel):
    names = ai_names(excel)
    users = collections.defaultdict(list)
    for r in monstats(excel):
        if r.get("Id") and r.get("AI"):
            users[ai_index(names, r["AI"])].append(r["Id"])
    kinds = collections.Counter()
    by_fn = collections.defaultdict(list)
    for i in range(AI_ROWS):
        k, init, think, alt = row(img, AI_TABLE, i)
        kinds[k] += 1
        by_fn[think].append(i)
        name = names[i] if i < len(names) else "?"
        print("ROW %d kind=%d init=0x%08X think=0x%08X alt=0x%08X name=%s mon=%d" % (
            i, k, init, think, alt, name, len(users.get(i, []))))
    for i in range(AI_STATE_ROWS):
        k, init, think, alt = row(img, AI_STATES, i)
        print("ST %d kind=%d init=0x%08X think=0x%08X alt=0x%08X" % (i, k, init, think, alt))
    for k in sorted(kinds):
        print("KIND %d %d" % (k, kinds[k]))
    print("FN %d distinct think functions over %d rows" % (len(by_fn), AI_ROWS))
    for fn, rs in sorted(by_fn.items()):
        if len(rs) > 1:
            print("SHARED 0x%08X %s" % (fn, " ".join(str(x) for x in rs)))
    unused = [i for i in range(AI_ROWS) if i not in users]
    for i in unused:
        print("UNUSED %d %s" % (i, names[i]))
    bad = sorted(set(users) - set(range(AI_ROWS)))
    print("SURVEY rows=%d states=%d used=%d unused=%d unknown_names=%d monstats_rows=%d" % (
        AI_ROWS, AI_STATE_ROWS, AI_ROWS - len(unused), len(unused), len(bad),
        sum(len(v) for v in users.values())))


def cmd_entries(img, excel):
    names = ai_names(excel)
    ms = monstats(excel)
    by_hc = {}
    by_id = {}
    for r in ms:
        if r.get("Id"):
            by_id[r["Id"]] = r
            if r.get("hcIdx", "") != "":
                by_hc[int(r["hcIdx"])] = r

    def show(tag, src, r):
        i = ai_index(names, r["AI"])
        think = row(img, AI_TABLE, i)[2] if 0 <= i < AI_ROWS else 0
        print("%s %s %s %s ai=%d %s think=0x%08X" % (tag, src, r.get("hcIdx"), r["Id"], i, r["AI"], think))

    seen = set()
    for h in txt_rows(os.path.join(excel, "hireling.txt")):
        c = h.get("Class", "")
        if c == "" or (h.get("Hireling"), c) in seen:
            continue
        seen.add((h.get("Hireling"), c))
        r = by_hc.get(int(c))
        if r:
            show("HIRE", h.get("Hireling", "?").replace(" ", "_"), r)
    seen = set()
    for s in txt_rows(os.path.join(excel, "skills.txt")):
        m = s.get("summon", "")
        if m and m in by_id and m not in seen:
            seen.add(m)
            show("SUMMON", "skill:" + s.get("skill", "?").replace(" ", "_"), by_id[m])
    for p in txt_rows(os.path.join(excel, "pettype.txt")):
        for k in range(1, 5):
            c = p.get("mclass%d" % k, "")
            if c != "" and int(c) in by_hc and by_hc[int(c)]["Id"] not in seen:
                seen.add(by_hc[int(c)]["Id"])
                show("SUMMON", "pettype:" + p.get("pet type", "?"), by_hc[int(c)])


def cmd_pool(excel):
    names = ai_names(excel)
    ai_of = {r["Id"]: ai_index(names, r["AI"]) for r in monstats(excel) if r.get("Id") and r.get("AI")}
    slots = collections.Counter()
    levels = collections.defaultdict(set)
    cols = ["%s%d" % (c, k) for c in ("mon", "nmon", "umon") for k in range(1, 11)]
    for lv in txt_rows(os.path.join(excel, "levels.txt")):
        for c in cols:
            m = lv.get(c, "")
            if m and m in ai_of:
                slots[ai_of[m]] += 1
                levels[ai_of[m]].add(lv.get("Id", lv.get("Name", "?")))
    for i, n in sorted(slots.items(), key=lambda kv: (-kv[1], kv[0])):
        print("POOL %d %s slots=%d levels=%d" % (i, names[i], n, len(levels[i])))
    print("SURVEY pool slots=%d ais=%d" % (sum(slots.values()), len(slots)))


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["tables", "rows", "entries", "pool"])
    ap.add_argument("--exe", default=EXE)
    ap.add_argument("--excel", default=EXCEL)
    a = ap.parse_args(argv)
    if a.cmd == "pool":
        cmd_pool(a.excel)
        return
    img = Image(a.exe)
    if a.cmd == "tables":
        cmd_tables(img)
    elif a.cmd == "rows":
        cmd_rows(img, a.excel)
    else:
        cmd_entries(img, a.excel)


if __name__ == "__main__":
    main(sys.argv[1:])
