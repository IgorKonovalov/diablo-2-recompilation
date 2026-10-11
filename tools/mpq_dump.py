"""Dump the reference MPQs and build the merged game-data tree (Plan 0001 phase 3).

Usage:
  python3 -I tools/mpq_dump.py names   <out-listfile> [--excel <excel-dir>] <archive.mpq>...
  python3 -I tools/mpq_dump.py extract <listfile> <out-root> <ref-root> [archive-name...]
  python3 -I tools/mpq_dump.py merge   <mpq-root> <out-merged> <log-dir>

names    Builds a candidate listfile (backslash separators, which smpq's -L requires) from the
         internal listfiles of every archive given, plus derived sets: each
         data/global/excel name with both .txt and .bin extensions, each data/local/<kind>/<xxx>/
         name with every known language code, and (with --excel) data/global/items/<x>.dc6 for every
         invfile, uniqueinvfile, setinvfile and flippyfile cell of weapons, armor, misc,
         uniqueitems and setitems .txt in <excel-dir>. Archives without a listfile (both
         patch_d2.mpq) are named from these candidates.
extract  Extracts every archive in ARCHIVES (below), or only the named ones, from <ref-root> into
         <out-root>/<name>/ with `smpq -x -L <listfile>`, refuses archives whose names contain '..'
         or a drive or root prefix, and prints total/named/unnamed counts per archive (also
         written to <out-root>/counts.tsv; with a subset, only those rows are replaced).
merge    Copies MERGE_ORDER archives in ascending precedence into <out-merged>. Paths are
         lowercased (MPQ name lookup is case-insensitive). Unnamed entries and (listfile),
         (attributes), (signature) are skipped. Writes <log-dir>/merged-manifest.tsv
         (path, origin archive, original name, size, sha256) and <log-dir>/overrides.txt (every path
         that a later archive overwrote, with both hashes).

Stdlib only. Shells out to smpq (StormLib). Never runs anything from the archives.
"""
import hashlib
import os
import re
import shutil
import subprocess
import sys

# name -> path relative to the reference extraction root (workspace/reference/extracted)
ARCHIVES = {
    "d2data": "1.14b-d2/Common/d2data.mpq",
    "d2char": "1.14b-d2/Common/d2char.mpq",
    "d2music": "1.14b-d2/Common/d2music.mpq",
    "d2sfx": "1.14b-d2/Common/d2sfx.mpq",
    "d2speech": "1.14b-d2/Common/d2speech.mpq",
    "d2video": "1.14b-d2/Common/d2video.mpq",
    "patch_d2-classic": "1.14b-d2/Common/patch_d2.mpq",
    "d2exp": "1.14b-d2lod/Common/d2exp.mpq",
    "d2xmusic": "1.14b-d2lod/Common/d2xmusic.mpq",
    "d2xtalk": "1.14b-d2lod/Common/d2xtalk.mpq",
    "d2xvideo": "1.14b-d2lod/Common/d2xvideo.mpq",
    "patch_d2": "1.14b-d2lod/Common/patch_d2.mpq",
}

# Ascending precedence (later overwrites earlier), mirroring the game's search order
# (docs/findings/data/0002-mpq-precedence.md): patch_d2 5000 > d2exp 3000 > the 1000 band. Within
# the 1000 band a later-opened archive is searched first; d2char is opened after d2data, so it
# comes after d2data here (d2char and d2data share no path, so the tie order changes no file).
# Audio/video archives hold no data the tools read and are not merged.
# patch_d2-classic is not merged: installing LoD replaces patch_d2.mpq with the LoD one.
MERGE_ORDER = ["d2data", "d2char", "d2exp", "patch_d2"]

LANGS = ["eng", "deu", "fra", "ita", "esp", "kor", "chi", "jpn", "pol", "por", "rus", "cyr"]
UNNAMED = re.compile(r"^file\d{8}\.", re.I)
SPECIAL = {"(listfile)", "(attributes)", "(signature)"}


def smpq_list(archive, listfile=None):
    cmd = ["smpq", "-l"] + (["-L", listfile] if listfile else []) + [archive]
    out = subprocess.run(cmd, check=True, capture_output=True, text=True).stdout
    # lines: "<size> <date> <time> <name>"; names contain no spaces in D2 archives
    return [ln.split(None, 3)[3] for ln in out.splitlines() if len(ln.split(None, 3)) == 4]


ITEM_ART_TABLES = ["weapons", "armor", "misc", "uniqueitems", "setitems"]
ITEM_ART_COLUMNS = {"invfile", "uniqueinvfile", "setinvfile", "flippyfile"}


def item_art_names(excel_dir):
    """data\\global\\items\\<x>.dc6 for every item-art cell of the item tables."""
    out = set()
    for t in ITEM_ART_TABLES:
        with open(os.path.join(excel_dir, t + ".txt"), encoding="latin-1") as fh:
            rows = [ln.rstrip("\r\n").split("\t") for ln in fh]
        cols = [i for i, h in enumerate(rows[0]) if h.strip().lower() in ITEM_ART_COLUMNS]
        for r in rows[1:]:
            for i in cols:
                v = r[i].strip() if i < len(r) else ""
                if v and re.fullmatch(r"[A-Za-z0-9_]+", v):
                    out.add("data\\global\\items\\" + v + ".dc6")
    return out


def cmd_names(out, archives, excel_dir=None):
    names = set()
    for a in archives:
        names.update(n.replace("/", "\\") for n in smpq_list(a) if not UNNAMED.match(n))
    derived = set()
    for n in names:
        low = n.lower()
        if low.startswith("data\\global\\excel\\") and low.endswith((".txt", ".bin")):
            derived.add(n[:-4] + ".txt")
            derived.add(n[:-4] + ".bin")
        m = re.match(r"(?i)(data\\local\\[a-z]+\\)[a-z]{3}(\\.*)$", n)
        if m:
            derived.update(m.group(1) + lang + m.group(2) for lang in LANGS)
    if excel_dir:
        derived |= item_art_names(excel_dir)
    seen, final = set(), []
    # (lower, name): when spellings differ only in case, the choice is stable across runs
    for n in sorted(names | derived, key=lambda x: (x.lower(), x)):
        if n.lower() not in seen:
            seen.add(n.lower())
            final.append(n)
    with open(out, "w", newline="\r\n") as fh:
        fh.write("\n".join(final) + "\n")
    print(f"{len(final)} candidate names ({len(names)} from archive listfiles) -> {out}")


def safe(name):
    n = name.replace("\\", "/")
    return not (n.startswith("/") or re.match(r"^[a-z]:", n, re.I) or ".." in n.split("/"))


def cmd_extract(listfile, out_root, ref_root, only=None):
    listfile = os.path.abspath(listfile)
    unknown = [o for o in (only or []) if o not in ARCHIVES]
    if unknown:
        sys.exit(f"unknown archive names {unknown}")
    counts = os.path.join(out_root, "counts.tsv")
    prev = {}
    if only and os.path.exists(counts):
        with open(counts) as fh:
            prev = {ln.split("\t", 1)[0]: ln.rstrip("\n") for ln in list(fh)[1:] if ln.strip()}
    rows = ["archive\ttotal\tnamed\tunnamed"]
    for name, rel in ARCHIVES.items():
        if only and name not in only:
            if name in prev:
                rows.append(prev[name])
            continue
        archive = os.path.abspath(os.path.join(ref_root, rel))
        entries = smpq_list(archive, listfile)
        bad = [e for e in entries if not safe(e)]
        if bad:
            sys.exit(f"{name}: refusing unsafe entry names {bad[:5]}")
        dest = os.path.join(out_root, name)
        if os.path.exists(dest):
            shutil.rmtree(dest)
        os.makedirs(dest)
        subprocess.run(["smpq", "-x", "-q", "-L", listfile, archive], cwd=dest, check=True)
        unnamed = sum(1 for e in entries if UNNAMED.match(e))
        on_disk = sum(len(fs) for _, _, fs in os.walk(dest))
        if on_disk != len(entries):
            sys.exit(f"{name}: listed {len(entries)} entries but extracted {on_disk} files")
        rows.append(f"{name}\t{len(entries)}\t{len(entries) - unnamed}\t{unnamed}")
        print(rows[-1])
    with open(counts, "w") as fh:
        fh.write("\n".join(rows) + "\n")


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def cmd_merge(mpq_root, out, log_dir):
    if os.path.exists(out):
        shutil.rmtree(out)
    os.makedirs(log_dir, exist_ok=True)
    manifest, overrides = {}, []
    for name in MERGE_ORDER:
        root = os.path.join(mpq_root, name)
        for d, _, fs in os.walk(root):
            for f in fs:
                src = os.path.join(d, f)
                orig = os.path.relpath(src, root).replace(os.sep, "/")
                if UNNAMED.match(f) or orig.lower() in SPECIAL:
                    continue
                rel = orig.lower()
                digest = sha256(src)
                if rel in manifest:
                    prev = manifest[rel]
                    same = "same" if prev[3] == digest else "changed"
                    overrides.append(f"{rel}\t{prev[0]}:{prev[3][:16]}\t{name}:{digest[:16]}\t{same}")
                dst = os.path.join(out, rel)
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                shutil.copyfile(src, dst)
                manifest[rel] = (name, orig, os.path.getsize(src), digest)
    with open(os.path.join(log_dir, "merged-manifest.tsv"), "w") as fh:
        fh.write("path\tarchive\toriginal_name\tsize\tsha256\n")
        for rel in sorted(manifest):
            a, orig, size, digest = manifest[rel]
            fh.write(f"{rel}\t{a}\t{orig}\t{size}\t{digest}\n")
    with open(os.path.join(log_dir, "overrides.txt"), "w") as fh:
        fh.write("path\tbefore\tafter\tcontent\n" + "\n".join(overrides) + "\n")
    changed = sum(1 for o in overrides if o.endswith("changed"))
    print(f"{len(manifest)} files merged, {len(overrides)} overrides ({changed} with changed content)")


def main(argv):
    if len(argv) >= 5 and argv[0] == "names" and argv[2] == "--excel":
        cmd_names(argv[1], argv[4:], argv[3])
    elif len(argv) >= 3 and argv[0] == "names":
        cmd_names(argv[1], argv[2:])
    elif len(argv) >= 4 and argv[0] == "extract":
        cmd_extract(argv[1], argv[2], argv[3], argv[4:])
    elif len(argv) == 4 and argv[0] == "merge":
        cmd_merge(*argv[1:])
    else:
        print(__doc__)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
