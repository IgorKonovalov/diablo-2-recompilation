#!/usr/bin/env python3
"""Plan 0038 batch H5d (collision): the static and kept-log checks next to tools/collision.py check.

Usage:
  python3 -I tools/sweep_h5d.py static [--excel DIR] [--exe GAME.EXE]
  python3 -I tools/sweep_h5d.py masks LOG [LOG ...]
  python3 -I tools/sweep_h5d.py patterns LOG [LOG ...]

static: (a) every stock creation source of the suckernest classes 334-337 (BaseId 334, collision 45): a cell naming one
  of them by Id or by number in the class columns of Levels (mon/nmon/umon 1-25), MonStats (minion1/2, spawn), MonPreset
  (Place), SuperUniques (Class) and Skills (summon); (b) every instruction of .text with an immediate 334-337 that is not
  a displacement, listed by radare2's `/ai 0x14e 0x151` (r2 must be on PATH), each with the next two instructions, for
  the reader to classify (the finding lists the classification per site).
masks: sub_005B2A00_MonSpawnTry's CollisionTest mask (the MK0 line at 0x005B2DA8) paired with the class of the open
  request (MT0 .. MTX, nested by "d"), counted by the class's MonStats2 spawnCol and the class (collision 5: spawnCol 1
  -> 0x01C0, 3 -> 0). A class with spawnCol 1 outside 153 and 258-263 takes SpawnPosOnTile (MTT) and makes no MK0.
patterns: the creation mark of every MonSpawnTry request (MT0 .. MU0, then the first CM "PM" line at the created cell)
  against PATH_PatternFromSize (0x00648580): g_CollPatternBySize[SizeX] (0x006EB3DC, sizes 0-3; above 3 pattern 1 with no
  NPC test); 1 -> 3 and 2 -> 4 when MonIsNpc (0x0063E860) holds and MonStats flag 9 (`interact`, +0x0D bit 1) is clear.
  MonIsNpc is read as `npc` (+0x0D bit 0) or `inTown` (+0x0D bit 2), else the unit's +0xC4 bit 31 (not logged: a
  creation where it would decide is counted apart). The older reading (`npc` only) is scored beside it.
"""
import csv
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
EXCEL = os.path.join(ROOT, "workspace", "merged", "data", "global", "excel")
EXE = os.path.join(ROOT, "workspace", "install", "app", "game.exe")
NEST = range(334, 338)


def rows(excel, name):
    with open(os.path.join(excel, name), encoding="latin-1", newline="") as fh:
        return list(csv.DictReader(fh, delimiter="\t"))


def monstats(excel):
    """MonStats rows in hcIdx order (the Expansion separator row dropped)."""
    out = {}
    for r in rows(excel, "monstats.txt"):
        if r.get("Id") and r["Id"] != "Expansion" and r.get("hcIdx", "").strip().lstrip("-").isdigit():
            out[int(r["hcIdx"])] = r
    return out


def cmd_static(argv):
    excel, exe = EXCEL, EXE
    it = iter(argv)
    for a in it:
        if a == "--excel":
            excel = next(it)
        elif a == "--exe":
            exe = next(it)
    ms = monstats(excel)
    ids = {ms[i]["Id"] for i in NEST if i in ms}
    print("suckernest classes: %s" % ", ".join("%d %s (BaseId %s)" % (i, ms[i]["Id"], ms[i]["BaseId"]) for i in NEST))
    names = ids | {str(i) for i in NEST}
    hits = []
    lv = rows(excel, "levels.txt")
    cols = [c for c in lv[0] if c[:4] in ("mon1", "mon2") or c.rstrip("0123456789") in ("mon", "nmon", "umon")]
    for r in lv:
        for c in cols:
            if r[c] in ids:
                hits.append(("levels.txt", r.get("Name"), c, r[c]))
    for i, r in sorted(ms.items()):
        for c in ("minion1", "minion2", "spawn"):
            if r.get(c) in ids and i not in NEST:
                hits.append(("monstats.txt", r["Id"], c, r[c]))
    for r in rows(excel, "monpreset.txt"):
        if r.get("Place") in names:
            hits.append(("monpreset.txt", r.get("Act"), "Place", r["Place"]))
    for r in rows(excel, "superuniques.txt"):
        if r.get("Class") in names:
            hits.append(("superuniques.txt", r.get("Superunique"), "Class", r["Class"]))
    for r in rows(excel, "skills.txt"):
        if r.get("summon") in names:
            hits.append(("skills.txt", r.get("skill"), "summon", r["summon"]))
    print("table creation sources (levels %d class columns, monstats minion1/minion2/spawn, monpreset Place, "
          "superuniques Class, skills summon): %d" % (len(cols), len(hits)))
    for h in hits:
        print("  %s %s %s = %s" % h)
    spawners = [(ms[i]["Id"], ms[i]["spawn"]) for i in NEST]
    print("the suckernests' own spawn column (what they make): %s" % spawners)
    out = subprocess.run(["r2", "-q", "-e", "scr.color=0", "-e", "search.in=section", "-c",
                          "s 0x401000; /ai 0x14e 0x151", exe], capture_output=True, text=True, timeout=1800).stdout
    sites = []
    for ln in out.splitlines():
        p = ln.split(None, 2)
        if len(p) < 3 or not p[0].startswith("0x"):
            continue
        a = int(p[0], 16)
        if not 0x401000 <= a < 0x401000 + 0x2CA5A1:
            continue
        asm = p[2]
        if any(("%s 0x%x]" % (s, v)) in asm for s in ("+", "-") for v in NEST) or any(
                "[0x%x]" % v in asm for v in NEST):
            continue
        sites.append((a, p[1], asm))
    print("immediates 334-337 in .text (r2 /ai, displacements dropped): %d sites" % len(sites))
    for a, hx, asm in sites:
        nxt = subprocess.run(["r2", "-q", "-e", "scr.color=0", "-c", "s 0x%x; pi 3" % a, exe], capture_output=True,
                             text=True, timeout=120).stdout.strip().split("\n")
        print("  0x%08X  %-24s %s" % (a, hx, " | ".join(nxt)))
    return 0


def cmd_masks(paths):
    excel = EXCEL
    ms = monstats(excel)
    m2 = {r["Id"]: r for r in rows(excel, "monstats2.txt")}

    def spawncol(cls):
        r = ms.get(cls)
        if r is None:
            return None
        v = m2.get(r.get("MonStatsEx"), {}).get("spawnCol", "")
        return int(v) if v.strip() else 0
    tally, ontile = {}, {}
    nfiles = 0
    for p in paths:
        nfiles += 1
        stack = []
        for ln in open(p, errors="replace"):
            tag = ln.split(" ", 1)[0]
            if tag not in ("MT0", "MTX", "MK0", "MTT"):
                continue
            try:
                d = json.loads(ln[len(tag) + 1:])
            except ValueError:
                continue
            if tag == "MT0":
                del stack[d["d"] - 1:]
                stack.append(d["cls"])
            elif tag == "MTX":
                del stack[d["d"] - 1:]
            elif stack:
                cls = stack[-1]
                sc = spawncol(cls)
                if tag == "MK0":
                    k = (sc, d["mask"], cls)
                    tally[k] = tally.get(k, 0) + 1
                else:
                    ontile[(sc, cls)] = ontile.get((sc, cls), 0) + 1
    print("logs %d" % nfiles)
    for (sc, mask, cls), n in sorted(tally.items(), key=lambda kv: (kv[0][0] if kv[0][0] is not None else -1, kv[0][1], kv[0][2])):
        if sc in (1, 2, 3):
            print("  MK0 spawnCol %s mask 0x%04x class %d %s: %d" % (sc, mask, cls, ms[cls]["Id"], n))
    by = {}
    for (sc, mask, cls), n in tally.items():
        by[(sc, mask)] = by.get((sc, mask), 0) + n
    for (sc, mask), n in sorted(by.items(), key=lambda kv: (kv[0][0] if kv[0][0] is not None else -1, kv[0][1])):
        print("MK0 by (spawnCol, mask): (%s, 0x%04x) %d" % (sc, mask, n))
    for (sc, cls), n in sorted(ontile.items()):
        print("MTT (SpawnPosOnTile) spawnCol %s class %d %s: %d" % (sc, cls, ms[cls]["Id"], n))
    return 0


def cmd_patterns(paths):
    import struct
    excel = EXCEL
    ms = monstats(excel)
    m2 = {r["Id"]: r for r in rows(excel, "monstats2.txt")}
    with open(EXE, "rb") as fh:
        raw = fh.read()
    table = struct.unpack_from("<4I", raw, 0x006EB3DC - 0x400000)

    def model(cls, use_town):
        r = ms[cls]
        v = m2.get(r.get("MonStatsEx"), {}).get("SizeX", "")
        size = int(v) if v.strip() else 0
        if size > 3:
            return 1, size
        p = table[size]
        npc = r.get("npc") == "1" or (use_town and r.get("inTown") == "1")
        if p in (1, 2) and npc and r.get("interact") != "1":
            p += 2
        return p, size
    tally, bad, bad_old, p5 = {}, [], 0, {}
    nfiles = 0
    for path in paths:
        nfiles += 1
        stack, pend = [], None
        for ln_no, ln in enumerate(open(path, errors="replace"), 1):
            tag = ln.split(" ", 1)[0]
            if tag not in ("MT0", "MTX", "MU0", "CM"):
                continue
            try:
                d = json.loads(ln[len(tag) + 1:])
            except ValueError:
                continue
            if tag == "MT0":
                del stack[d["d"] - 1:]
                stack.append(d["cls"])
            elif tag == "MTX":
                del stack[d["d"] - 1:]
                pend = None
            elif tag == "MU0":
                pend = (stack[-1], d["x"], d["y"]) if stack else None
            elif pend and d.get("f") == "PM" and (d["x"], d["y"]) == pend[1:]:
                cls = pend[0]
                pend = None
                want, size = model(cls, True)
                old, _ = model(cls, False)
                if d["a"] == 5:
                    # pattern 5 is not PatternFromSize's (it returns 0-4): set by another writer, counted apart
                    p5[cls] = p5.get(cls, 0) + 1
                    continue
                k = (cls, size, d["a"], want)
                tally[k] = tally.get(k, 0) + 1
                if d["a"] != want:
                    bad.append("%s:%d class %d size %d: logged pattern %d, model %d" % (
                        os.path.basename(path), ln_no, cls, size, d["a"], want))
                if d["a"] != old:
                    bad_old += 1
    print("logs %d" % nfiles)
    n = sum(tally.values())
    print("creation marks %d (pattern 5 excluded); model (npc or inTown, interact clear) mismatches %d; older reading (npc only) "
          "mismatches %d" % (n, len(bad), bad_old))
    for b in bad[:40]:
        print("  MISMATCH " + b)
    for (cls, size, a, want), c in sorted(tally.items()):
        r = ms[cls]
        if a in (3, 4) or want in (3, 4) or r.get("inTown") == "1" or r.get("npc") == "1":
            print("  class %d %s (npc %s, inTown %s, interact %s) size %d: pattern %d (model %d) x %d" % (
                cls, r["Id"], r.get("npc") or 0, r.get("inTown") or 0, r.get("interact") or 0, size, a, want, c))
    by = {}
    for (cls, size, a, want), c in tally.items():
        by[a] = by.get(a, 0) + c
    print("creation marks by pattern: %s" % dict(sorted(by.items())))
    print("creation marks with pattern 5 (another writer, not compared): %d, classes %s" % (
        sum(p5.values()), ", ".join("%d %s x %d" % (c, ms[c]["Id"], n) for c, n in sorted(p5.items()))))
    return 1 if bad else 0


def main(argv):
    if len(argv) < 2 or argv[1] not in ("static", "masks", "patterns"):
        print(__doc__)
        return 2
    if argv[1] == "static":
        return cmd_static(argv[2:])
    if argv[1] == "patterns":
        return cmd_patterns(argv[2:])
    return cmd_masks(argv[2:])


if __name__ == "__main__":
    sys.exit(main(sys.argv))
