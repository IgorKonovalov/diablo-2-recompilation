"""Survey the maze and level-link data: LvlMaze, LvlPrest maze presets, Levels Vis/Warp, LvlWarp (plan 0022 Phase 0).

Usage:
  python3 -I tools/maze_survey.py <excel-dir> [--quiet]

<excel-dir> is a data/global/excel directory (e.g. workspace/merged/data/global/excel). Records are
decoded from the .bin files with the layouts in tools/excel_layouts.py (what the game loads); the
levels.txt / lvlprest.txt / lvltypes.txt / lvlwarp.txt `Name` columns are read only to label rows.
A "maze level" is a Levels row whose leveldefs `DrlgType` is 1 (drlg/0003).

Sections (--quiet drops the per-row listings, keeping counts and exceptions):

1. LvlMaze rows. Per row (file order): its Level, that level's Act, DrlgType and LevelType, and the
   row's values. Then the maze levels without a row, the rows whose level is not a maze level, and
   the maze levels listed with their LvlMaze values.
2. Maze presets per maze level type:
   - the rotation range base+1..base+15, base from MAZE_DEF_BASE (tools/drlg.py, read from the switch
     in sub_006738C0_MazePresetFile, drlg/0003); "none" for a type absent from that table;
   - whether record base+m carries the exit letters of m (N=8, S=4, E=2, W=1, written in N S E W
     order) as its Name suffix and in its File1 basename;
   - the records, Files sum, named-file count, SizeX/SizeY and, per file slot, the DS1 name pattern
     (the exit letters replaced by {m}) of the range;
   - the "block": the records with LevelId 0 whose Dt1Mask is non-zero and names only non-"0" files of
     the type's LvlTypes row, and whose File1 lies in a directory of one of those files. This is a
     sorting rule of the survey, not a claim about the generator.
3. Links. Vis0..7 resolution, duplicates, self links and cross-act links; Vis symmetry (A names B and
   B names A) with every exception; the Vis/Warp slot pairing (set/unset in each combination); the
   pairing table A slot -> B, Warp id and LvlWarp Directions, B's slot back to A and its Warp id.
4. LvlWarp Direction per Id, and the levels naming the Ids that have 'l'/'r' records.

The last line is `SURVEY maze key=value ...` (integer counts). Stdlib only. Read-only.
"""
import collections
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from excel_bin import decode_field, find_file, read_bin, read_txt  # noqa: E402
from excel_layouts import LAYOUTS  # noqa: E402

# sub_006738C0_MazePresetFile: rotation base per level type (drlg/0003); same table as tools/drlg.py
# and tools/ds1.py (not imported: drlg.py pulls in the DS1/DT1 parsers)
MAZE_DEF_BASE = {3: 0x34, 4: 0x6C, 7: 0xA7, 8: 0xCD, 10: 0x101, 13: 0x12D, 17: 0x19D, 18: 0x1E1, 22: 0x2F1,
                 24: 0x298, 25: 0x2C0, 28: 0x344, 33: 0x3EA, 34: 0x422, 35: 0x41C}
EXITS = (("N", 8), ("S", 4), ("E", 2), ("W", 1))


def decode(excel_dir, table):
    lay = LAYOUTS[table]
    recs, size = read_bin(find_file(excel_dir, table, ".bin"))
    assert size == lay["size"], (table, size)
    return [{f.get("name") or f["col"]: decode_field(r, f) for f in lay["fields"]} for r in recs]


def txt_col(excel_dir, table, col):
    header, rows = read_txt(find_file(excel_dir, table, ".txt"))
    i = header.index(col)
    return [r[i] for r in rows]


def letters(m):
    return "".join(c for c, b in EXITS if m & b)


def nfile(s):
    return (s or "").replace("\\", "/")


def named(s):
    return s not in ("", "0", None)


def runs(xs):
    out = []
    for x in sorted(xs):
        if out and out[-1][1] == x - 1:
            out[-1][1] = x
        else:
            out.append([x, x])
    return ", ".join("%d" % a if a == b else "%d-%d" % (a, b) for a, b in out) or "-"


def main(argv):
    if len(argv) < 1:
        print(__doc__)
        return 2
    E, quiet = argv[0], "--quiet" in argv[1:]
    S = collections.OrderedDict()
    lv, ld = decode(E, "levels"), decode(E, "leveldefs")
    lname = txt_col(E, "levels", "Name")
    assert all(r["Id"] == i for i, r in enumerate(lv)), "levels Id != row index"
    mz, pr, lt, lw = decode(E, "lvlmaze"), decode(E, "lvlprest"), decode(E, "lvltypes"), decode(E, "lvlwarp")
    pname, tname, wname = txt_col(E, "lvlprest", "Name"), txt_col(E, "lvltypes", "Name"), txt_col(E, "lvlwarp", "Name")
    nlev = len(lv)
    act = [r["Act"] for r in lv]
    maze = [i for i in range(nlev) if ld[i]["DrlgType"] == 1]
    S["levels"] = nlev
    S["maze_levels"] = len(maze)
    S["maze_level_types"] = len({ld[i]["LevelType"] for i in maze})
    for a in range(5):
        S["maze_levels_act%d" % (a + 1)] = sum(1 for i in maze if act[i] == a)

    # ---------------------------------------------------------------- 1. LvlMaze
    print("== 1. LvlMaze rows (%d), file order" % len(mz))
    print("row  Level  name                        act drlg ltype  Rooms  (N)  (H) SizeX SizeY Merge  maze?")
    by_level = collections.defaultdict(list)
    for k, r in enumerate(mz):
        L = r["Level"]
        by_level[L].append(k)
        ok = 0 <= L < nlev
        d = ld[L] if ok else None
        if not quiet:
            print("%3d  %5d  %-26s  %3s %4s %5s  %5d %4d %4d %5d %5d %5d  %s"
                  % (k, L, lname[L][:26] if ok else "?", act[L] + 1 if ok else "?", d["DrlgType"] if ok else "?",
                     d["LevelType"] if ok else "?", r["Rooms"], r["Rooms(N)"], r["Rooms(H)"], r["SizeX"],
                     r["SizeY"], r["Merge"], "yes" if ok and d["DrlgType"] == 1 else "NO"))
    S["lvlmaze_rows"] = len(mz)
    S["lvlmaze_level_unresolved"] = sum(1 for r in mz if not 0 <= r["Level"] < nlev)
    S["lvlmaze_level_dup"] = sum(1 for v in by_level.values() if len(v) > 1)
    nonmaze = [k for k, r in enumerate(mz) if ld[r["Level"]]["DrlgType"] != 1]
    S["lvlmaze_rows_maze"] = len(mz) - len(nonmaze)
    S["lvlmaze_rows_not_maze"] = len(nonmaze)
    for dt in (0, 2, 3):
        S["lvlmaze_rows_drlg%d" % dt] = sum(1 for k in nonmaze if ld[mz[k]["Level"]]["DrlgType"] == dt)
    missing = [i for i in maze if i not in by_level]
    S["maze_levels_without_row"] = len(missing)
    print("maze levels without a LvlMaze row: %s" % (missing or "none"))
    print("rows whose level is not a maze level (row: level name DrlgType LevelType):")
    for k in nonmaze:
        L = mz[k]["Level"]
        print("  row %d: level %d %s, DrlgType %d, LevelType %d" % (k, L, lname[L], ld[L]["DrlgType"], ld[L]["LevelType"]))
    print("\nmaze levels (%d) with their LvlMaze values (Rooms N H, SizeX SizeY, Merge):" % len(maze))
    for i in maze:
        r = mz[by_level[i][0]] if i in by_level else None
        if not quiet:
            print("  %3d act %d ltype %2d %-28s %s" % (i, act[i] + 1, ld[i]["LevelType"], lname[i],
                  "%d %d %d, %dx%d, %d" % (r["Rooms"], r["Rooms(N)"], r["Rooms(H)"], r["SizeX"], r["SizeY"], r["Merge"])
                  if r else "no row"))

    # ---------------------------------------------------------------- 2. maze presets
    print("\n== 2. Maze presets per maze level type")
    types = sorted({ld[i]["LevelType"] for i in maze})
    block_of = collections.defaultdict(list)
    S["maze_types_with_base"] = S["maze_types_without_base"] = 0
    S["range_records"] = S["range_files_sum"] = S["range_named_files"] = S["range_files_ne_named"] = 0
    S["range_name_mismatch"] = S["range_file1_mismatch"] = S["range_size_vs_lvlmaze_mismatch"] = 0
    S["range_ranges_overlapping"] = 0
    bases = {t: b for t, b in MAZE_DEF_BASE.items()}
    for t in types:
        lvls = [i for i in maze if ld[i]["LevelType"] == t]
        files = [nfile(lt[t]["File %d" % (b + 1)]) for b in range(32)]
        dirs = {os.path.dirname(f.lower()) for f in files if named(f)}
        print("\n-- type %d %s: maze levels %s" % (t, tname[t], ", ".join(str(i) for i in lvls)))
        mz_sizes = sorted({(mz[by_level[i][0]]["SizeX"], mz[by_level[i][0]]["SizeY"]) for i in lvls if i in by_level})
        print("   LvlMaze SizeX x SizeY of these levels: %s" % ", ".join("%dx%d" % s for s in mz_sizes))
        b = bases.get(t)
        if b is None:
            S["maze_types_without_base"] += 1
            print("   rotation range: none (type not in MAZE_DEF_BASE)")
        else:
            S["maze_types_with_base"] += 1
            rng = list(range(b + 1, b + 16))
            others = [u for u, ob in bases.items() if u != t and ob < b + 16 and b < ob + 16]
            if others:
                S["range_ranges_overlapping"] += 1
            print("   rotation range: Def %d-%d (base %d = 0x%X, record %d is %r)%s"
                  % (b + 1, b + 15, b, b, b, pname[b],
                     "; overlaps the range of type(s) %s" % ", ".join(str(u) for u in others) if others else ""))
            fsum = sum(pr[d]["Files"] for d in rng)
            nn = sum(sum(1 for s in range(1, 7) if named(pr[d]["File%d" % s])) for d in rng)
            ne = sum(1 for d in rng if pr[d]["Files"] != sum(1 for s in range(1, 7) if named(pr[d]["File%d" % s])))
            S["range_records"] += 15
            S["range_files_sum"] += fsum
            S["range_named_files"] += nn
            S["range_files_ne_named"] += ne
            sizes = collections.Counter((pr[d]["SizeX"], pr[d]["SizeY"]) for d in rng)
            if set(sizes) != set(mz_sizes):
                S["range_size_vs_lvlmaze_mismatch"] += 1
            print("   15 records, Files sum %d, named files %d, Files != named in %d; LvlPrest SizeX x SizeY %s"
                  % (fsum, nn, ne, ", ".join("%dx%d (%d)" % (k[0], k[1], v) for k, v in sorted(sizes.items()))))
            bad_name, bad_file = [], []
            for m in range(1, 16):
                d = b + m
                if not pname[d].rstrip().endswith(" " + letters(m)):
                    bad_name.append("%d=%r" % (d, pname[d]))
                base1 = os.path.splitext(os.path.basename(nfile(pr[d]["File1"])))[0]
                if letters(m).lower() not in base1.lower():
                    bad_file.append("%d=%s" % (d, base1))
            S["range_name_mismatch"] += len(bad_name)
            S["range_file1_mismatch"] += len(bad_file)
            print("   Name suffix = exit letters of m: %s" % ("all 15" if not bad_name else
                  "%d mismatches: %s" % (len(bad_name), "; ".join(bad_name))))
            print("   File1 basename holds the exit letters of m: %s" % ("all 15" if not bad_file else
                  "%d mismatches: %s" % (len(bad_file), "; ".join(bad_file))))
            for s in range(1, 7):
                pats = collections.Counter()
                for m in range(1, 16):
                    f = nfile(pr[b + m]["File%d" % s])
                    if not named(f):
                        pats["(none)"] += 1
                        continue
                    dn, bn = os.path.split(f)
                    stem, ext = os.path.splitext(bn)
                    key = letters(m)
                    k = stem.upper().rfind(key)
                    # the last occurrence: a stem may itself hold exit letters (e.g. "Sewer" has E)
                    for cand in range(len(stem) - len(key), -1, -1):
                        if stem[cand:cand + len(key)].upper() == key and not stem[cand + len(key):cand + len(key) + 1].isupper():
                            k = cand
                            break
                    pats["%s/%s{m}%s%s" % (dn, stem[:k], stem[k + len(key):], ext) if k >= 0 else f] += 1
                if set(pats) == {"(none)"}:
                    continue
                print("   File%d: %s" % (s, "; ".join("%s x%d" % kv for kv in sorted(pats.items()))))
        blk = []
        for r in pr:
            if r["LevelId"] or not named(r["File1"]):
                continue
            bits = [x for x in range(32) if r["Dt1Mask"] >> x & 1]
            if not bits or any(not named(files[x]) for x in bits):
                continue
            if os.path.dirname(nfile(r["File1"]).lower()) in dirs:
                blk.append(r["Def"])
                block_of[r["Def"]].append(t)
        fsum = sum(pr[d]["Files"] for d in blk)
        nn = sum(sum(1 for s in range(1, 7) if named(pr[d]["File%d" % s])) for d in blk)
        S["block_records_type%d" % t] = len(blk)
        print("   block (survey rule): Def %s: %d records, Files sum %d, named files %d"
              % (runs(blk), len(blk), fsum, nn))
        if b is None:
            ordered = [d for d in blk if all(d + m - 1 < len(pr) and
                       pname[d + m - 1].rstrip().endswith(" " + letters(m)) for m in range(1, 16))]
            S["maskrun_type%d" % t] = len(ordered)
            print("   15-record runs in the block named in exit-mask order (W, E, EW, S ... NSEW): %s"
                  % (", ".join("Def %d-%d (as base %d)" % (d, d + 14, d - 1) for d in ordered) or "none"))
            for d in ([] if quiet else blk):
                r = pr[d]
                print("     %4d %-34s Files %d  %dx%d  %s" % (d, pname[d].rstrip(), r["Files"], r["SizeX"], r["SizeY"],
                      " ".join(os.path.basename(nfile(r["File%d" % s_])) for s_ in range(1, 7) if named(r["File%d" % s_]))))
        if b is not None:
            run = [b + 1] if b + 1 in blk else []
            while run and run[-1] + 1 in blk:
                run.append(run[-1] + 1)
            print("   block run from Def %d: %s" % (b + 1, runs(run)))
            outside = [d for d in range(b + 1, b + 16) if d not in blk]
            print("   rotation-range records outside the block: %s" % (outside or "none"))
    shared = {d: ts for d, ts in block_of.items() if len(ts) > 1}
    S["block_records_shared"] = len(shared)
    by_set = collections.defaultdict(list)
    for d, ts in shared.items():
        by_set[tuple(ts)].append(d)
    print("\nrecords in more than one type's block: %d" % len(shared))
    for ts, ds in sorted(by_set.items()):
        print("  types %s: Def %s" % ("+".join(map(str, ts)), runs(ds)))

    # ---------------------------------------------------------------- 3. links
    print("\n== 3. Links: Levels Vis0..7 / Warp0..7 (leveldefs +0x48 / +0x68)")
    vis = [[ld[i]["Vis%d" % k] for k in range(8)] for i in range(nlev)]
    warp = [[ld[i]["Warp%d" % k] for k in range(8)] for i in range(nlev)]
    S["vis_cells_set"] = sum(1 for i in range(nlev) for v in vis[i] if v != 0)
    S["vis_unresolved"] = sum(1 for i in range(nlev) for v in vis[i] if v != 0 and not 0 < v < nlev)
    S["vis_negative"] = sum(1 for i in range(nlev) for v in vis[i] if v < 0)
    S["vis_self"] = sum(1 for i in range(nlev) for v in vis[i] if v == i and v != 0)
    S["vis_dup_levels"] = sum(1 for i in range(nlev) if len([v for v in vis[i] if v]) != len({v for v in vis[i] if v}))
    gaps = [i for i in range(nlev) if any(vis[i][k] == 0 and any(vis[i][k + 1:]) for k in range(8))]
    S["vis_gaps"] = len(gaps)
    S["vis_gaps_maze"] = sum(1 for i in gaps if i in maze)
    S["levels_with_vis"] = sum(1 for i in range(nlev) if any(vis[i]))
    print("cells set (non-zero) %d; unresolved %d; negative %d; self links %d; levels repeating a level %d; "
          "levels with a 0 slot before a set one %d; levels with any Vis %d"
          % (S["vis_cells_set"], S["vis_unresolved"], S["vis_negative"], S["vis_self"], S["vis_dup_levels"],
             S["vis_gaps"], S["levels_with_vis"]))
    print("levels with a 0 slot before a set one: %s" % ", ".join("%d%s" % (i, "*" if i in maze else "") for i in gaps)
          + " (* maze)")
    print("per slot, cells set: %s" % ", ".join("Vis%d=%d" % (k, sum(1 for i in range(nlev) if vis[i][k])) for k in range(8)))
    xact = [(i, v) for i in range(nlev) for v in vis[i] if v and act[i] != act[v]]
    S["vis_cross_act"] = len(xact)
    print("cross-act links (A act != B act): %d%s" % (len(xact), ": " + ", ".join("%d->%d" % p for p in xact) if xact else ""))
    # symmetry
    asym = [(i, k, v) for i in range(nlev) for k, v in enumerate(vis[i]) if v and 0 < v < nlev and i not in vis[v]]
    S["vis_links"] = sum(1 for i in range(nlev) for v in vis[i] if v and 0 < v < nlev)
    S["vis_asymmetric"] = len(asym)
    print("\nVis symmetry: %d links, %d with no link back (A names B, B does not name A):"
          % (S["vis_links"], len(asym)))
    for i, k, v in asym:
        print("  %3d %-26s Vis%d -> %3d %-26s (Warp%d %d; B's Vis: %s)"
              % (i, lname[i], k, v, lname[v], k, warp[i][k], [x for x in vis[v] if x]))
    # Vis / Warp per slot
    comb = collections.Counter()
    odd = []
    S["null_vis_set"] = sum(1 for v in vis[0] if v)
    S["null_warp_not_m1"] = sum(1 for w in warp[0] if w != -1)
    print("\nlevel 0 (%s): Vis %s, Warp %s (left out of the slot counts below)" % (lname[0], vis[0], warp[0]))
    for i in range(1, nlev):
        for k in range(8):
            c = (vis[i][k] != 0, warp[i][k] != -1)
            comb[c] += 1
            if c[0] != c[1]:
                odd.append((i, k))
    S["slot_vis_warp"] = comb[(True, True)]
    S["slot_vis_nowarp"] = comb[(True, False)]
    S["slot_novis_warp"] = comb[(False, True)]
    S["slot_none"] = comb[(False, False)]
    print("Vis/Warp per slot (%d slots, levels 1..): Vis set + Warp set %d; Vis set + Warp -1 %d; Vis 0 + Warp set %d; neither %d"
          % (8 * (nlev - 1), comb[(True, True)], comb[(True, False)], comb[(False, True)], comb[(False, False)]))
    for i, k in odd:
        print("  %3d %-26s slot %d: Vis %d%s, Warp %d" % (i, lname[i], k, vis[i][k],
              " (%s, DrlgType %d)" % (lname[vis[i][k]], ld[vis[i][k]]["DrlgType"]) if vis[i][k] else "", warp[i][k]))
    # pairing table
    wdirs = collections.defaultdict(list)
    for r in lw:
        wdirs[r["Id"]].append(r["Direction"])
    S["pair_same_warp"] = S["pair_diff_warp"] = S["pair_both_nowarp"] = S["pair_one_nowarp"] = S["pair_slot_same"] = 0
    print("\npairing table: A slot -> B | Warp | LvlWarp Directions | B slot back -> A | B's Warp")
    for i in range(nlev):
        for k, v in enumerate(vis[i]):
            if not v:
                continue
            back = [j for j, x in enumerate(vis[v]) if x == i] if 0 < v < nlev else []
            bw = warp[v][back[0]] if back else None
            if back:
                if bw == -1 or warp[i][k] == -1:
                    S["pair_both_nowarp" if bw == warp[i][k] else "pair_one_nowarp"] += 1
                else:
                    S["pair_same_warp" if bw == warp[i][k] else "pair_diff_warp"] += 1
                S["pair_slot_same"] += back[0] == k
            if not quiet:
                print("  %3d %-24s Vis%d -> %3d %-24s | %3d | %-4s | %s | %s"
                      % (i, lname[i][:24], k, v, lname[v][:24], warp[i][k],
                         "".join(wdirs.get(warp[i][k], [])) or "-",
                         "Vis%d" % back[0] if back else "none", "-" if bw is None else bw))
    print("over the links with a link back: both Warps set: same Warp id both ways %d, different %d; "
          "Warp -1 both ways %d, one way %d; same slot index both ways %d"
          % (S["pair_same_warp"], S["pair_diff_warp"], S["pair_both_nowarp"], S["pair_one_nowarp"], S["pair_slot_same"]))
    # maze levels: links
    S["maze_vis_links"] = sum(1 for i in maze for v in vis[i] if v)
    S["maze_vis_nowarp"] = sum(1 for i in maze for k in range(8) if vis[i][k] and warp[i][k] == -1)
    print("maze levels: %d Vis links, %d of them with Warp -1" % (S["maze_vis_links"], S["maze_vis_nowarp"]))

    # ---------------------------------------------------------------- 4. LvlWarp Direction
    print("\n== 4. LvlWarp Direction per Id (%d records)" % len(lw))
    named_by = collections.defaultdict(list)
    for i in range(nlev):
        for k in range(8):
            if warp[i][k] != -1:
                named_by[warp[i][k]].append((i, k))
    S["lvlwarp_records"] = len(lw)
    S["lvlwarp_ids"] = len(wdirs)
    S["lvlwarp_ids_b"] = sum(1 for d in wdirs.values() if d == ["b"])
    S["lvlwarp_ids_lr"] = sum(1 for d in wdirs.values() if sorted(d) == ["l", "r"])
    S["lvlwarp_ids_other"] = len(wdirs) - S["lvlwarp_ids_b"] - S["lvlwarp_ids_lr"]
    S["warp_cells"] = sum(len(v) for v in named_by.values())
    S["warp_cells_level0"] = sum(1 for i, k in named_by.get(0, []) if i == 0)
    S["warp_unresolved"] = sum(len(v) for w, v in named_by.items() if w not in wdirs)
    S["lvlwarp_ids_unnamed"] = sum(1 for w in wdirs if w not in named_by)
    print("Ids %d: 'b' only %d, 'l'+'r' %d, other %d; Warp cells %d, unresolved %d; Ids named by no level %d"
          % (S["lvlwarp_ids"], S["lvlwarp_ids_b"], S["lvlwarp_ids_lr"], S["lvlwarp_ids_other"], S["warp_cells"],
             S["warp_unresolved"], S["lvlwarp_ids_unnamed"]))
    first_name = {}
    for r, n in zip(lw, wname):
        first_name.setdefault(r["Id"], n)
    for w in sorted(wdirs):
        users = named_by.get(w, [])
        if quiet and wdirs[w] == ["b"]:
            continue
        print("  Id %2d %-32s %-3s named by %s" % (w, first_name[w][:32], "".join(wdirs[w]),
              ", ".join("%d/Warp%d(Vis %d)" % (i, k, vis[i][k]) for i, k in users) or "-"))
    S["lr_warp_cells"] = sum(len(named_by[w]) for w in wdirs if sorted(wdirs[w]) == ["l", "r"])
    print("Warp cells naming an 'l'+'r' Id: %d" % S["lr_warp_cells"])

    print("SURVEY maze " + " ".join("%s=%d" % kv for kv in S.items()))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
