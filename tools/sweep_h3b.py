#!/usr/bin/env python3
"""Plan 0038 batch H3b (data-load): the checks over the session logs of tools/gdb/excel.gdb (tools/h3b_sessions.py).

Usage:
  python3 -I tools/sweep_h3b.py check [--written HASHES] LOG [LOG ...]   # every check, per log, then the totals

The loose and written files are read from each log's game directory, which tools/h3b_sessions.py stage --slot 2
recreates byte for byte (the loose ones); the .bin files a -direct -txt run wrote are gone after unstage, so --written
gives their sha256sum list (check/txt-written-bins-h3b-dtxt.txt), used where the file is absent.
  python3 -I tools/sweep_h3b.py txtfiles DIR                 # the .bin files a -txt session wrote into DIR against
                                                             # the archive copies the game loads instead

A log's session kind comes from its d2run header: "-txt" in args -> txt, "-direct" -> direct, a game directory named
game-loose -> loose, else stock. Models, each written from the findings (data/0001-0004) and the tables, not from the
log:
  archives  A1: core (d2data 1000, d2sfx 1000, d2speech 1000, d2delta 1000, d2kfixup 1000, patch_d2 5000, d2exp 3000),
            then game (d2char 1000, d2music 1000; expansion installed: d2Xmusic, d2Xtalk, d2Xvideo 3000); a call
            returns a handle iff the file exists in the game directory. A2: a new archive goes in front of the first
            node whose priority is <= its own (signed), the list is walked by Storm handle (XARC "storm"); every XLST
            must equal the model list after the same events, an archive no longer in a logged list (closed) leaves the
            model too.
  lookup    A3: a FindFile that returns 1 names the first archive of the current list whose extracted tree
            (workspace/mpq/<archive>/, case-insensitive) holds the path; under -direct a path that exists in the game
            directory returns 2 before any archive; without -direct nothing returns 2.
  bytes     every XFLW buffer's sha256 equals the file the lookup model picks (the archive's extracted copy, or the
            loose file for a return of 2).
  language  I1: the first LNG_GetLanguageIndex call reads data\\local\\use through FILE_LoadWhole and returns its first
            byte (> 13 -> 0); every later call returns the same; the string tables load from lng\\<code>\\ with code 0
            = ENG.
  strings   A1 of data/strings: a STRTABLE_LoadAll with reference count 0 loads, by FILE_LoadWhole in this order, the
            font map, string.tbl, patchstring.tbl and, when the expansion argument is non-zero, expansionstring.tbl,
            then holds count 1 and the three buffers; STRTABLE_Unload takes the count down by one and, at 0, clears
            the buffers.
  excel     every DATATBLS_LoadTable call is followed, on its thread, by one FILE_LoadWhole of
            DATA\\GLOBAL\\EXCEL\\<name>.bin; the 15 code-list tables of DATATBLS_LoadCodeLists and the 2-byte monstats /
            skilldesc calls appear only under -txt; the name sequence of one LoadAll is the same in every session
            (txt: the stock sequence plus those calls).
  lookups   ITEMS_GetByCode: index = the code's first position in weapons + armor + misc (tools/tc.py Tables), return =
            g_pItems + 0x1A8 * index, or 0 and index 0 for an unknown code. EXCEL_FindName on g_TCLink: the TC index of
            the name (tools/tc.py Tables, case-insensitive; the empty name is TC 0), -1 when it has none (load-time callers may also return -1
            for a name defined later in the file: counted apart). TC_GetByName: no hit.
  records   the XDMP dumps (H3B_DUMP) against the archive .bin records: the bytes that differ, per table and offset;
            the filled fields modelled (items +0x0F0 s32 by GEMS_Load: -1 on the first nGems records, then the gem
            row on its item's record; monstats +0x02A s16 by MONEQUIP_Load: the first monequip row of the class, else
            -1; charstats +0x000 the UTF-16 text of STRTABLE_GetStringByKey(class at +0x20), at most 16 units, zero
            padded; levels +0x16E / +0x1BE the UTF-16 text of the LevelName / LevelWarp key, 40 units with the 40th
            forced 0; +0x033..+0x035 the counts of the leading non-negative mon / nmon / umon slots, 25 u16 each
            at +0x036 / +0x068 / +0x09A, which data/0004 § 3 and tables/Levels name but the spec's J4 list does not);
            the padding bytes the spec names (items +0x123, +0x12E; monstats +0x00A..+0x00B, +0x00F bits
            5-7; levels +0x00A..+0x00B) equal to the file in every dump; load and unload dumps compared.
Prints one CHECK line per check with its counts and "bad"; the last line is the total. Stdlib only. Read-only.
"""
import hashlib
import json
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import excel_bin  # noqa: E402
import tc as tcmod  # noqa: E402
import tbl  # noqa: E402

ROOT = os.path.dirname(HERE)
MPQ = os.path.join(ROOT, "workspace", "mpq")
EXCEL = os.path.join(ROOT, "workspace", "merged", "data", "global", "excel")
LNG = os.path.join(ROOT, "workspace", "merged", "data", "local", "lng", "eng")
CORE = [("d2data", 1000), ("d2sfx", 1000), ("d2speech", 1000), ("d2delta", 1000), ("d2kfixup", 1000),
        ("patch_d2", 5000), ("d2exp", 3000)]
GAMEA = [("d2char", 1000), ("d2music", 1000)]
GAMEX = [("d2xmusic", 3000), ("d2xtalk", 3000), ("d2xvideo", 3000)]
CODELISTS = ["playerclass", "bodylocs", "storepage", "elemtypes", "hitclass", "colors", "hiredesc", "monmode",
             "plrmode", "monai", "monplace", "skillcalc", "misscalc", "skills", "events"]
TXT_SMALL = {("monmode", 4), ("plrmode", 4), ("skills", 2), ("monstats", 2), ("skilldesc", 2)}
STRLOAD_RA = 0x0052593C          # FILE_LoadWhole's return in STRTABLE_LoadFile
FONT_RA = 0x005277AF             # FILE_LoadWhole's return in UNICODE_LoadFontMap
PLAY_FROM = "PLR "


def parse(path):
    hdr, ev = {}, []
    with open(path, encoding="utf-8", errors="replace") as fh:
        for n, ln in enumerate(fh, 1):
            if ln.startswith("# d2run "):
                for tok in ("args=", "dir="):
                    i = ln.find(tok)
                    v = ln[i + len(tok):]
                    if v.startswith("'"):
                        v = v[1:v.index("'", 1)]
                    else:
                        v = v.split(" ")[0]
                    hdr[tok[:-1]] = v
            elif ln.startswith("# early:"):
                hdr["early"] = ln.strip()
            elif ln.startswith("LOGERR"):
                ev.append(("LOGERR", n, {"text": ln.strip()}))
            elif ln[:1].isupper() and " {" in ln[:12]:
                tag, _, js = ln.partition(" ")
                try:
                    ev.append((tag, n, json.loads(js)))
                except ValueError:
                    pass
            elif ln.startswith("[Inferior "):
                ev.append(("INFERIOR", n, {"text": ln.strip()}))
    args = hdr.get("args", "")
    gd = hdr.get("dir", "")
    base = os.path.basename(gd.rstrip("/"))
    kind = "rus" if base == "game-rus" else "clamp" if base == "game-clamp" else "txt" if "-txt" in args else \
        "direct" if "-direct" in args else "loose" if base == "game-loose" else "stock"
    return {"path": path, "hdr": hdr, "ev": ev, "kind": kind, "dir": gd, "direct": "-direct" in args,
            "txt": "-txt" in args}


class Arcs:
    """The extracted archive trees: lower-cased relative path -> file, per archive."""

    def __init__(self):
        self.trees = {}

    def tree(self, name):
        if name not in self.trees:
            t = {}
            base = os.path.join(MPQ, name)
            for dp, _, fs in os.walk(base):
                for f in fs:
                    full = os.path.join(dp, f)
                    t.setdefault(os.path.relpath(full, base).replace(os.sep, "\\").lower(), full)
            self.trees[name] = t
        return self.trees[name]

    def find(self, name, path):
        return self.tree(name).get(path.lower().replace("/", "\\"))


def ci_exists(base, rel):
    """Case-insensitive lookup of rel (backslashes) under base, as wine resolves it; the path or None."""
    cur = base
    for part in rel.replace("/", "\\").split("\\"):
        if not part:
            continue
        try:
            names = os.listdir(cur)
        except OSError:
            return None
        hit = [n for n in names if n.lower() == part.lower()]
        if not hit:
            return None
        cur = os.path.join(cur, hit[0])
    return cur if os.path.isfile(cur) else None


def sha(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


class Check:
    def __init__(self):
        self.lines = []
        self.total_bad = 0

    def out(self, name, log, bad, **counts):
        self.total_bad += bad
        print("CHECK %s %s %s bad=%d" % (name, os.path.basename(log), " ".join("%s=%s" % kv for kv in counts.items()),
                                         bad))

    def note(self, s):
        print("  " + s)


def arc_name(n):
    return n.lower().replace(".mpq", "")


def check_archives(S, C, A):
    ev = S["ev"]
    bad = 0
    xarc = [(n, d) for t, n, d in ev if t == "XARC"]
    first_tbl = next((n for t, n, d in ev if t == "XTBL"), None)
    first_sla = next((n for t, n, d in ev if t == "XSLA"), None)
    startup = [(n, d) for n, d in xarc if first_sla is None or n < first_sla]
    want = CORE + GAMEA + GAMEX
    got = [(arc_name(d["name"]), d["prio"]) for n, d in startup]
    if got != want:
        bad += 1
        C.note("startup opens %r != model %r" % (got, want))
    for n, d in startup:
        exists = ci_exists(S["dir"], d["name"]) is not None
        if bool(d["ret"]) != exists:
            bad += 1
            C.note("line %d: %s ret %x, file exists %s" % (n, d["name"], d["ret"], exists))
    if first_tbl is not None and startup and startup[-1][0] > first_tbl:
        bad += 1
    # A2 over every open, every list snapshot
    model, names, nlist, closed_seen = [], {}, 0, 0
    for t, n, d in ev:
        if t == "XARC" and d["ret"]:
            names[d["storm"]] = arc_name(d["name"])
            model = [x for x in model if x[0] != d["storm"]]   # a closed archive's handle, reused
            k = next((i for i, (h, p) in enumerate(model) if p <= d["prio"]), len(model))
            model.insert(k, (d["storm"], d["prio"]))
        elif t == "XLST":
            nlist += 1
            logged = [(int(h, 16), p) for h, p, _, _ in d["list"]]
            live = {h for h, _ in logged}
            gone = [x for x in model if x[0] not in live]
            if gone:     # archives closed since (the game archives around a cinematic): out of the model too
                closed_seen += len(gone)
                model = [x for x in model if x[0] in live]
            if logged != model:
                bad += 1
                C.note("line %d: list %r != model %r" % (n, logged, model))
    S["arcnames"] = names
    vid = [(n, d) for t, n, d in ev if t == "XARC" and arc_name(d["name"]) == "d2video"]
    vopn = [(n, d) for t, n, d in ev if t == "XOPN" and d["fn"] == "video"]
    C.out("archives", S["path"], bad, startup_opens=len(startup), opened=sum(1 for _, d in startup if d["ret"]),
          lists=nlist, closed=closed_seen, video_opens=len(vid), video_calls=len([1 for _, d in vopn
                                                                                   if "ret" in d]),
          video_prio=",".join(str(d["prio"]) for _, d in vid), before_first_table=first_tbl is None or
          (bool(startup) and startup[-1][0] < first_tbl))


def current_list(ev, upto):
    """The archive list (handles, front first) of the last XLST before line upto."""
    last = None
    for t, n, d in ev:
        if n >= upto:
            break
        if t == "XLST":
            last = [int(h, 16) for h, _, _, _ in d["list"]]
    return last or []


def check_files(S, C, A):
    """FindFile inside FILE_LoadWhole, its source, the buffer bytes."""
    ev, bad, n_ff, n_flw, n_bytes, n_disk, n_excel, n_skip = S["ev"], 0, 0, 0, 0, 0, 0, 0
    names, cur, disk_paths = {}, [], []
    # Under -direct -txt the run itself writes DATA\GLOBAL\EXCEL\*.bin into the game directory (B1b), so such a path
    # is on disk only from its write on: it may return 1 (an archive, as the model) before and 2 after, never 1
    # after a 2. A .bin written twice (a code-list call, then the full table) is compared by bytes at its last read
    # only; an earlier read must have the size its LoadTable gives (4 + count x record).
    written = set()
    if S["direct"] and S["txt"]:
        staged = set()
        for dp, _, fs in os.walk(os.path.join(S["dir"], "data")):
            for f in fs:
                staged.add(os.path.relpath(os.path.join(dp, f), S["dir"]).replace(os.sep, "\\").lower())
        for t, n, d in ev:
            if t == "XFLW" and d["ff"] and d["ff"][0]["ret"] == 2:
                written.add(d["path"].lower())
    last_read = {}
    for t, n, d in ev:
        if t == "XFLW":
            last_read[d["path"].lower()] = n
    tbl_after = {}
    nxt = None
    for t, n, d in reversed(ev):
        if t == "XTBL":
            nxt = d
        elif t == "XFLW":
            tbl_after[n] = nxt
    went_disk, n_before_write = set(), 0
    for t, n, d in ev:
        if t == "XARC" and d["ret"]:
            names[d["storm"]] = arc_name(d["name"])     # in log order: a reused handle names its new archive
            continue
        if t == "XLST":
            cur = [int(h, 16) for h, _, _, _ in d["list"]]
            continue
        if t not in ("XFLW", "XFF"):
            continue
        recs = d["ff"] if t == "XFLW" else [d]
        if t == "XFF":
            continue     # the XFF lines repeat the records an XFLW carries; the counts are in XSTAT
        n_flw += 1
        for r in recs:
            n_ff += 1
            path = r["name"]
            loose = ci_exists(S["dir"], path)
            if loose is None and WRITTEN and path.lower() in written and r["ret"] == 2:
                loose = "(written by the run)"   # the directory is gone: the kept hash list stands for it
            if path.lower() in written and path.lower() not in went_disk and r["ret"] == 1:
                loose = None           # not written yet: the archive model applies
                n_before_write += 1
            if path.lower() in written and r["ret"] == 2:
                went_disk.add(path.lower())
            if S["direct"] and loose:
                want, src = 2, loose
            else:
                want, src = 0, None
                for h in cur:
                    f = A.find(names.get(h, "?"), path)
                    if f:
                        want, src = 1, (h, f)
                        break
            if r["ret"] != want or (want == 1 and int(r["arc"], 16) != src[0]):
                bad += 1
                C.note("line %d: FindFile %s ret %d arc %s, model %d %s" % (n, path, r["ret"], r["arc"], want,
                                                                          src if want != 1 else "%x" % src[0]))
                continue
            if r["ret"] == 2:
                n_disk += 1
                disk_paths.append(path)
            if t == "XFLW" and d.get("sha256") and len(d["ff"]) == 1 and want == 2 and path.lower() in written \
                    and last_read[path.lower()] != n:
                tb = tbl_after.get(n)
                if tb is None or tb["name"].lower() != path.split("\\")[-1][:-4].lower() or \
                        d["size"] != 4 + (tb["count"] or 0) * tb["rec"]:
                    bad += 1
                    C.note("line %d: %s, an earlier write, size %d against its LoadTable %r" % (n, path, d["size"], tb))
                else:
                    n_bytes += 1
            elif t == "XFLW" and d.get("sha256") and len(d["ff"]) == 1 and want == 2 and path.lower() in written \
                    and WRITTEN:
                # a file the run wrote, checked against the hash list kept after the run (--written)
                if d["sha256"] != WRITTEN.get(path.split("\\")[-1].lower()):
                    bad += 1
                    C.note("line %d: %s bytes differ from the kept hash" % (n, path))
                else:
                    n_bytes += 1
                    n_excel += 1
            elif t == "XFLW" and d.get("sha256") and len(d["ff"]) == 1:
                fpath = src if want == 2 else src[1]
                if d["size"] != os.path.getsize(fpath) or d["sha256"] != sha(fpath):
                    bad += 1
                    C.note("line %d: %s bytes differ from %s" % (n, path, fpath))
                else:
                    n_bytes += 1
                    if path.lower().startswith("data\\global\\excel"):
                        n_excel += 1
            elif t == "XFLW" and len(d["ff"]) != 1:
                n_skip += 1
    st = [d for t, n, d in ev if t == "XSTAT"]
    ff_disk = st[-1]["ff_disk"] if st else None
    ff_calls = st[-1]["ff_calls"] if st else None
    if not S["direct"] and ff_disk:
        bad += 1
    C.out("files", S["path"], bad, flw=n_flw, findfile_in_flw=n_ff, bytes_equal=n_bytes, excel_bytes_equal=n_excel,
          disk=n_disk, written_by_run=len(written), archive_reads_before_write=n_before_write,
          flw_not_one_findfile=n_skip, all_findfile_calls=ff_calls, all_findfile_disk=ff_disk,
          disk_paths=("|".join(disk_paths) if len(disk_paths) <= 8 else "%d paths" % len(disk_paths)) or "-")


def check_language(S, C):
    ev, bad = S["ev"], 0
    lng = [(n, d) for t, n, d in ev if t == "XLNG"]
    first = lng[0] if lng else None
    use = [(n, d) for t, n, d in ev if t == "XFLW" and d["path"].lower() == "data\\local\\use"]
    if not first or first[1]["flag_in"] != 0 or not use:
        C.out("language", S["path"], 1, xlng=len(lng), use_loads=len(use))
        return
    un, ud = use[0]
    byte = int(ud["head"][:2], 16) if ud.get("head") else None
    want = byte if byte is not None and byte <= 13 else 0
    prev = max((n for t, n, d in ev if t == "XLNG" and n < un), default=0)
    if not (prev < un < first[0]):
        bad += 1
        C.note("the use load (line %d) is not inside the first XLNG (line %d)" % (un, first[0]))
    for n, d in lng:
        if d["ret"] != want:
            bad += 1
            C.note("line %d: language %d, model %d" % (n, d["ret"], want))
    if len(use) != 1:
        bad += 1
    st = [d for t, n, d in ev if t == "XSTAT"]
    if any(d["lng_byte"] != want for t, n, d in ev if t == "XSTAT" and n > first[0]):
        bad += 1
    tbls = [d["path"] for t, n, d in ev if t == "XFLW" and d["path"].lower().startswith("data\\local\\lng\\")]
    codes = sorted({p.split("\\")[3] for p in tbls})
    if codes != ["ENG"] and want == 0:
        bad += 1
    C.out("language", S["path"], bad, use_byte=byte, use_size=ud["size"], ret=want, xlng=len(lng),
          later_calls=st[-1]["lng_calls"] - 1 if st else None, use_loads=len(use), tbl_dirs=",".join(codes))


def check_strings(S, C):
    ev, bad = S["ev"], 0
    n_load = n_unload = n_inc = n_free = 0
    flw = []
    for t, n, d in ev:
        if t == "XFLW" and d["ra"] in (STRLOAD_RA, FONT_RA):
            flw.append((n, d))
        if t == "XSLA":
            b, a = d["before"], d["after"]
            if b["s"]:
                n_inc += 1
                if a["ref"] != b["ref"] + 1 or (a["s"], a["p"], a["x"]) != (b["s"], b["p"], b["x"]):
                    bad += 1
                continue
            n_load += 1
            mine = [x for x in flw if x[0] < n][-4:] if d["exp"] else [x for x in flw if x[0] < n][-3:]
            want = ["default.map", "string.tbl", "patchstring.tbl"] + (["expansionstring.tbl"] if d["exp"] else [])
            got = [x[1]["path"].split("\\")[-1].lower() for x in mine]
            bufs = [x[1]["buf"] for x in mine[1:]]
            if got != want or a["ref"] != 1 or b["ref"] != 0 or [a["s"], a["p"]] + ([a["x"]] if d["exp"] else []) \
                    != bufs or d["ret"] != 1:
                bad += 1
                C.note("line %d: LoadAll files %r bufs %r after %r" % (n, got, bufs, a))
            flw = []
        if t == "XSUL":
            n_unload += 1
            b, a = d["before"], d["after"]
            if not b["s"]:
                if a != b:
                    bad += 1
                continue
            if a["ref"] != b["ref"] - 1:
                bad += 1
            if a["ref"] == 0:
                n_free += 1
                if (a["s"], a["p"], a["x"]) != (0, 0, 0):
                    bad += 1
            elif (a["s"], a["p"], a["x"]) != (b["s"], b["p"], b["x"]):
                bad += 1
    C.out("strings", S["path"], bad, loads_ref0=n_load, loads_inc=n_inc, unloads=n_unload, unloads_to0=n_free,
          unload_ras=",".join("%x" % d["ra"] for t, n, d in ev if t == "XSUL"),
          load_ras=",".join("%x" % d["ra"] for t, n, d in ev if t == "XSLA"))


def check_excel(S, C):
    ev, bad = S["ev"], 0
    tbls = [(n, d) for t, n, d in ev if t == "XTBL"]
    flws = [(n, d) for t, n, d in ev if t == "XFLW"]
    matched = 0
    for (n, d), nxt in zip(tbls, [x[0] for x in tbls[1:]] + [10 ** 9]):
        want = "data\\global\\excel\\%s.bin" % d["name"].lower()
        hit = [x for x in flws if n > x[0] > max([m for m, _ in tbls if m < n], default=0)
               and x[1]["path"].lower() == want]
        if len(hit) == 1:
            matched += 1
        else:
            bad += 1
            C.note("line %d: LoadTable %s has %d FILE_LoadWhole of its .bin" % (n, d["name"], len(hit)))
    seq = [(d["name"].lower(), d["rec"]) for n, d in tbls]
    small = [x for x in seq if x in TXT_SMALL or (x[0] in CODELISTS and x[0] not in ("monmode", "plrmode", "skills"))]
    if S["txt"]:
        got_names = {x[0] for x in small}
        if not set(CODELISTS) <= got_names | {"monmode", "plrmode", "skills"} or not TXT_SMALL <= set(seq):
            bad += 1
            C.note("txt: code-list calls %r" % small)
    elif small:
        bad += 1
        C.note("stock-mode code-list calls %r" % small)
    # the excel files read whole outside a LoadTable call: name, caller
    outside = {}
    tbl_lines = [n for n, _ in tbls]
    for n, d in flws:
        p = d["path"].lower()
        if not p.startswith("data\\global\\excel"):
            continue
        if any(abs(n - m) < 1 for m in tbl_lines):
            continue
        prev = max([m for m in tbl_lines if m < n], default=None)
        nextl = min([m for m in tbl_lines if m > n], default=None)
        owned = nextl is not None and any(x[1]["name"].lower() == p.split("\\")[-1][:-4] and x[0] == nextl
                                          for x in tbls)
        if not owned:
            outside.setdefault("%s@%x" % (p.split("\\")[-1], d["ra"]), 0)
            outside["%s@%x" % (p.split("\\")[-1], d["ra"])] += 1
    dta = [d for t, n, d in ev if t == "XDTA" and d["phase"] == "return"]
    txt = [d for t, n, d in ev if t == "XTXT"]
    if len(txt) != 1 or txt[0]["cfg_txt"] != (1 if S["txt"] else 0) or txt[0]["after"] != (1 if S["txt"] else 0):
        bad += 1
        C.note("XTXT %r" % txt)
    C.out("excel", S["path"], bad, loadall=len(dta), tables=len(tbls), bin_loads_matched=matched,
          codelist_calls=len(small), txt_flag=txt[0]["after"] if txt else None,
          txt_ra=",".join("%x" % d["ra"] for d in txt),
          excel_reads_outside_loadtable=";".join("%s=%d" % kv for kv in sorted(outside.items())) or "-")
    return seq


def check_lookups(S, C, T):
    ev, bad = S["ev"], 0
    play = next((n for t, n, d in ev if t == "PLR"), None)
    n_igc = n_igc_play = n_unknown = 0
    igc_ras = {}
    for t, n, d in ev:
        if t != "XIGC":
            continue
        n_igc += 1
        igc_ras["%x" % d["ra"]] = igc_ras.get("%x" % d["ra"], 0) + 1
        if play and n > play:
            n_igc_play += 1
        i = T.code2item.get(d["text"])
        if i is None:
            n_unknown += 1
            ok = d["ret"] == 0 and d["idx"] == 0
        else:
            ok = d["idx"] == i and d["ret"] == (d["items"] + 0x1A8 * i) & 0xFFFFFFFF
        if not ok:
            bad += 1
            C.note("line %d: ITEMS_GetByCode %r -> %r idx %r, model %r" % (n, d["text"], d["ret"], d["idx"], i))
    n_tcn = n_tcn_play = n_fwd = n_none = 0
    tcn_ras = {}
    for t, n, d in ev:
        if t != "XTCN":
            continue
        n_tcn += 1
        tcn_ras["%x" % d["ra"]] = tcn_ras.get("%x" % d["ra"], 0) + 1
        if play and n > play:
            n_tcn_play += 1
        # TC 0 is the empty name (data/0001 § 7: TC_LoadAll registers it first)
        want = (0 if d["name"] == "" else T.names.get(d["name"].lower())) if d["name"] is not None else None
        r = d["ret"] if d["ret"] < 0x80000000 else d["ret"] - (1 << 32)
        if want is None:
            n_none += 1
            ok = r == -1
        elif r == -1 and d["ra"] == 0x0065450B:
            n_fwd += 1
            ok = True
        else:
            ok = r == want
        if not ok:
            bad += 1
            C.note("line %d: FindName(g_TCLink, %r) = %d, model %r" % (n, d["name"], r, want))
    tcg = sum(1 for t, n, d in ev if t == "XTCG")
    st = [d for t, n, d in ev if t == "XSTAT"]
    if tcg:
        bad += 1
    C.out("lookups", S["path"], bad, igc_lines=n_igc, igc_lines_in_play=n_igc_play, igc_unknown=n_unknown,
          igc_calls=st[-1]["igc_calls"] if st else None, igc_ras=",".join("%s:%d" % kv for kv in sorted(igc_ras.items())),
          tcn_lines=n_tcn, tcn_lines_in_play=n_tcn_play, tcn_not_a_tc=n_none, tcn_forward=n_fwd,
          tcn_calls=st[-1]["tcn_calls"] if st else None,
          tcn_ras=",".join("%s:%d" % kv for kv in sorted(tcn_ras.items())), tc_getbyname_hits=tcg)


def u16s(b):
    return [b[i] | b[i + 1] << 8 for i in range(0, len(b), 2)]


def check_records(S, C, G):
    ev, bad = S["ev"], 0
    ddir = os.path.splitext(S["path"])[0] + "-dump"
    dumps = [d for t, n, d in ev if t == "XDMP"]
    if not dumps or not os.path.isdir(ddir):
        C.out("records", S["path"], 1, dumps=len(dumps))
        return
    src = {"items": b"".join(excel_bin.read_bin(excel_bin.find_file(EXCEL, t, ".bin"))[0] and
                             open(excel_bin.find_file(EXCEL, t, ".bin"), "rb").read()[4:]
                             for t in ("weapons", "armor", "misc")),
           "monstats": open(excel_bin.find_file(EXCEL, "monstats", ".bin"), "rb").read()[4:],
           "levels": open(excel_bin.find_file(EXCEL, "levels", ".bin"), "rb").read()[4:],
           "charstats": open(excel_bin.find_file(EXCEL, "charstats", ".bin"), "rb").read()[4:],
           "gems": open(excel_bin.find_file(EXCEL, "gems", ".bin"), "rb").read()[4:]}
    gems = [struct.unpack_from("<i", src["gems"], 0xC0 * g + 0x28)[0] for g in range(len(src["gems"]) // 0xC0)]
    monequip = open(excel_bin.find_file(EXCEL, "monequip", ".bin"), "rb").read()[4:]
    me_first = {}
    for r in range(len(monequip) // 28):
        cls = struct.unpack_from("<h", monequip, 28 * r)[0]
        if cls >= 0:
            me_first.setdefault(cls, r)
    PAD = {"items": [0x123, 0x12E], "monstats": [0x00A, 0x00B], "levels": [0x00A, 0x00B]}
    FILLED = {"items": set(range(0xF0, 0xF4)), "monstats": {0x2A, 0x2B, 0x36, 0x37, 0x38, 0x39, 0x4A, 0x4B},
              "levels": set(range(0x16E, 0x20E)) | {0x33, 0x34, 0x35}, "charstats": set(range(0x00, 0x20)), "gems": {0x2C, 0x2D}}
    counts = {}
    loaded = {}
    for d in dumps:
        name, rs = d["table"], d["rec"]
        data = open(os.path.join(ddir, d["file"]), "rb").read()
        if hashlib.sha256(data).hexdigest() != d["sha256"]:
            bad += 1
        f = src[name]
        if len(f) != len(data):
            bad += 1
            C.note("%s %s: %d bytes, file %d" % (d["phase"], name, len(data), len(f)))
            continue
        diff = {}
        for r in range(d["count"]):
            a, b = data[rs * r: rs * r + rs], f[rs * r: rs * r + rs]
            if a == b:
                continue
            for o in range(rs):
                if a[o] != b[o]:
                    diff[o] = diff.get(o, 0) + 1
        outside = {o: c for o, c in diff.items() if o not in FILLED.get(name, set())}
        key = (d["phase"], name)
        counts[key] = (len(diff), sorted(outside.items()))
        for o in PAD.get(name, []):
            if diff.get(o):
                bad += 1
                C.note("%s %s: padding +0x%03X differs in %d records" % (d["phase"], name, o, diff[o]))
        if name == "monstats":
            for r in range(d["count"]):
                if (data[rs * r + 0xF] ^ f[rs * r + 0xF]) & 0xE0:
                    bad += 1
        # value models
        mm = 0
        if name == "items":
            want = [struct.unpack_from("<i", f, rs * r + 0xF0)[0] for r in range(d["count"])]
            for g in range(len(gems)):
                want[g] = -1
            for g, it in enumerate(gems):
                if it >= 0:
                    want[it] = g
            mm = sum(struct.unpack_from("<i", data, rs * r + 0xF0)[0] != want[r] for r in range(d["count"]))
        elif name == "monstats":
            mm = sum(struct.unpack_from("<h", data, rs * r + 0x2A)[0] != me_first.get(r, -1) for r in range(d["count"]))
        elif name == "charstats":
            for r in range(d["count"]):
                key_ = f[rs * r + 0x20: rs * r + 0x30].split(b"\0")[0]
                _, _, text = G.by_key(key_)
                u = [ord(c) for c in text][:16] if isinstance(text, str) else text[:16]
                got = u16s(data[rs * r: rs * r + 0x20])
                if got != (u + [0] * 16)[:16]:
                    mm += 1
                    C.note("charstats %d: %r != %r" % (r, got, u))
        elif name == "levels":
            for r in range(d["count"]):
                for k, base in enumerate((0x36, 0x68, 0x9A)):    # +0x033..+0x035: leading non-negative slots
                    slots = struct.unpack_from("<25h", f, rs * r + base)
                    cnt = next((i for i, v in enumerate(slots) if v < 0), 25)
                    if data[rs * r + 0x33 + k] != cnt:
                        mm += 1
                for ko, do in ((0xF5, 0x16E), (0x11D, 0x1BE)):
                    key_ = f[rs * r + ko: rs * r + ko + 40].split(b"\0")[0]
                    _, _, text = G.by_key(key_)
                    u = ([ord(c) for c in text] if isinstance(text, str) else list(text))[:40]
                    u = (u + [0] * 40)[:40]
                    u[39] = 0
                    if u16s(data[rs * r + do: rs * r + do + 80]) != u:
                        mm += 1
        if mm:
            bad += 1
            C.note("%s %s: %d records off the value model" % (d["phase"], name, mm))
        counts[key] = counts[key] + (mm,)
        if d["phase"] == "load":
            loaded[name] = data
        elif name in loaded and loaded[name] != data:
            ch = sum(1 for i in range(len(data)) if data[i] != loaded[name][i])
            C.note("unload %s: %d bytes changed since the load dump" % (name, ch))
            counts[("changed", name)] = ch
    for (ph, name), v in sorted(counts.items()):
        if ph == "changed":
            C.note("changed between load and unload: %s %d bytes" % (name, v))
            continue
        C.note("%s %s: %d offsets differ from the file; outside the listed fields: %s; value-model misses %d" % (
            ph, name, v[0], v[1] or "none", v[2]))
    C.out("records", S["path"], bad, dumps=len(dumps), tables=len({d["table"] for d in dumps}),
          phases=",".join(sorted({d["phase"] for d in dumps})))


def check_hover(S, C, G):
    """The client's rare-name lines (data/strings § D, 0x0048C5C1-0x0048C726): the SIDX lines of the two name calls
    (return addresses 0x0048C5FD for name 1, 0x0048C6E0 for name 2) against the merged rare-name records (raresuffix
    then rareprefix, id = merged index + 1) of the hovered items (the H3bRare recipe): the index shown is the record's
    +0x0C, which LoadRareAffixes fills with STRTABLE_GetByKey(name); an id past the 201 records has no record and
    no line. A logged index the logger already wrote from an earlier call (one line per distinct index) counts as
    seen."""
    ev = S["ev"]
    if S["kind"] != "stock":
        return
    recipe = json.load(open(os.path.join(HERE, "d2s_recipes", "h3brare.json")))
    merged = [r[0x26:0x48].split(b"\0")[0] for t in ("raresuffix", "rareprefix")
              for r in excel_bin.read_bin(excel_bin.find_file(EXCEL, t, ".bin"))[0]]
    want = {0x0048C5FD: {}, 0x0048C6E0: {}}
    missing = 0
    for it in recipe["items"]:
        for ra, nid in zip((0x0048C5FD, 0x0048C6E0), it["rare"]):
            if 1 <= nid <= len(merged):
                want[ra][G.by_key(merged[nid - 1])[0]] = merged[nid - 1].decode("latin-1")
            else:
                missing += 1
    sidx = [(n, d) for t, n, d in ev if t == "SIDX"]
    bad, seen_at, seen_before = 0, 0, 0
    for ra, idxs in want.items():
        got = {d["idx"] for n, d in sidx if d["ra"] == ra}
        for i in idxs:
            if i in got:
                seen_at += 1
            elif any(d["idx"] == i for n, d in sidx):
                seen_before += 1
            else:
                bad += 1
                C.note("rare name index %d (%s) not shown" % (i, idxs[i]))
        for i in got - set(idxs):
            bad += 1
            C.note("unexpected rare name index %d at %x" % (i, ra))
    fmt = sum(1 for n, d in sidx if d["idx"] == 1718)
    C.out("hover", S["path"], bad, names_expected=sum(len(v) for v in want.values()), shown_at_ra=seen_at,
          shown_earlier=seen_before, ids_without_record=missing, rareformat_lines=fmt)


def check_rus(S, C):
    """The RUS session: the language byte 11 (checked by "language") selects the RUS code and the CYR font charset
    (data/0002 § 4); the install has neither, so the first load under them returns 0 (its FindFile 0), no
    STRTABLE_LoadAll returns, and the program ends before any game."""
    ev = S["ev"]
    fails = [(n, d) for t, n, d in ev if t == "XFLW" and d["ret"] == 0]
    sla = [d for t, n, d in ev if t == "XSLA"]
    plr = any(t == "PLR" for t, n, d in ev)
    first = fails[0][1] if fails else None
    p = first["path"].lower() if first else ""
    ok = first is not None and ("\\cyr\\" in p or "\\rus\\" in p) and [r["ret"] for r in first["ff"]] == [0] \
        and not sla and not plr
    C.out("rus", S["path"], 0 if ok else 1, first_failed_load=first["path"].replace("\\", "/") if first else "-",
          failed_loads=len(fails), failed_paths=",".join(d["path"].split("\\")[-2] + "/" + d["path"].split("\\")[-1]
                                                         for n, d in fails), loadall_returned=len(sla), in_game=plr,
          exit=next((d["text"].replace(" ", "_") for t, n, d in ev if t == "INFERIOR"), "-"))


def check_early(S, C):
    ev = S["ev"]
    att = [d for t, n, d in ev if t == "XATT"]
    first = [t for t, n, d in ev if t.startswith("X")][:3]
    bad = 0 if att and att[0]["early"] and first[:2] == ["XATT", "XIFI"] else 1
    ifi = [d for t, n, d in ev if t == "XIFI"]
    want = 1 if S["direct"] else 0
    if len(ifi) != 1 or ifi[0]["ecx"] != want or ifi[0]["storm_direct"] != want or ifi[0]["direct"] != want:
        bad += 1
    errs = sum(1 for t, n, d in ev if t == "LOGERR")
    bad += errs
    ingame = any(t == "PLR" for t, n, d in ev)
    C.out("early", S["path"], bad, header=S["hdr"].get("early", "-").replace(" ", "_"), xatt_early=bool(att and
          att[0]["early"]), initfileio_ecx=ifi[0]["ecx"] if ifi else None, direct_after=ifi[0]["direct"] if ifi
          else None, logerr=errs, in_game=ingame,
          exit=next((d["text"].replace(" ", "_") for t, n, d in ev if t == "INFERIOR"), "-"))


def cmd_check(logs):
    C, A = Check(), Arcs()
    T = tcmod.Tables(EXCEL)
    G = tbl.GameStrings(LNG, "spx")
    sessions = [parse(p) for p in logs]
    ref = None
    for S in sessions:
        print("== %s (%s)" % (S["path"], S["kind"]))
        check_early(S, C)
        check_archives(S, C, A)
        check_files(S, C, A)
        check_language(S, C)
        if S["kind"] == "rus":
            check_rus(S, C)
            S["seq"] = None
            continue
        check_strings(S, C)
        seq = check_excel(S, C)
        if S["kind"] == "stock" and ref is None:
            ref = seq
        S["seq"] = seq
        check_lookups(S, C, T)
        check_records(S, C, G)
        check_hover(S, C, G)
    print("== LoadAll sequence against the first stock session")
    for S in sessions:
        if ref is None:
            break
        seq = S["seq"]
        if seq is None:
            continue
        if S["txt"]:     # the stock sequence must be a subsequence; the calls added are listed
            it = iter(seq)
            same = all(x in it for x in ref)
            rest = list(seq)
            for x in ref:
                rest.remove(x)
            extra = rest
        else:
            same, extra = seq == ref, []
        C.out("order", S["path"], 0 if same else 1, tables=len(seq), same_as_stock=same, extra=len(extra),
              extra_calls=",".join("%s/%d" % x for x in extra) or "-")
    print("TOTAL bad=%d" % C.total_bad)
    return 1 if C.total_bad else 0


def cmd_txtfiles(d):
    A = Arcs()
    same = diff = 0
    for f in sorted(os.listdir(d)):
        if not f.lower().endswith(".bin"):
            continue
        p = os.path.join(d, f)
        arc = None
        for name in ("patch_d2", "d2exp", "d2data"):
            arc = A.find(name, "data\\global\\excel\\" + f)
            if arc:
                break
        if arc is None:
            print("TXTBIN %s %d no archive copy" % (f, os.path.getsize(p)))
            continue
        if sha(p) == sha(arc):
            same += 1
        else:
            diff += 1
            print("TXTBIN %s written %d bytes sha %s; archive copy (%s) %d bytes sha %s" % (
                f, os.path.getsize(p), sha(p)[:16], os.path.relpath(arc, MPQ), os.path.getsize(arc), sha(arc)[:16]))
    print("CHECK txtfiles written=%d identical=%d different=%d" % (same + diff, same, diff))
    return 0


WRITTEN = {}


def main(argv):
    if len(argv) >= 3 and argv[0] == "check" and argv[1] == "--written":
        # sha256sum lines of the .bin files a -direct -txt run wrote (check/txt-written-bins-h3b-dtxt.txt)
        for ln in open(argv[2]):
            h, _, name = ln.strip().partition("  ")
            WRITTEN[name.lower()] = h
        argv = ["check"] + argv[3:]
    if len(argv) >= 2 and argv[0] == "check":
        return cmd_check(argv[1:])
    if len(argv) == 2 and argv[0] == "txtfiles":
        return cmd_txtfiles(argv[1])
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
