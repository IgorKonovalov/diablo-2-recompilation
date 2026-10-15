"""Build the level-up save set of plan 0034 Phase 0: each class one experience point below a level threshold.

Usage:
  python3 -I tools/levelup_saves.py <excel-dir> <out-dir> [level ...]

For every class and game, and every target level N (default 2, 10, 50, 98), one save of a level N - 1 character
with experience = threshold(N) - 1, threshold(N) = experience.bin record N in the class's column (record 0 is the
MaxLvl row; record N is the .txt row labelled N - 1; docs/tables/Experience.md). One more experience point should
take the character to level N; that, and what the level-up changes, is for plan 0034 Phase 2.

Bases: the fresh level-1 expansion samples workspace/samples/d2s/smp<cls>.d2s (all seven classes); the classic
bases (Amazon, Sorceress, Necromancer, Paladin, Barbarian) are the same files made classic by `d2s.py classic`
(status bit 5 cleared, jf/kf trailer dropped), written to <out-dir>/_bases/. Each recipe keeps the base's whole
stat list, skills, mouse and hot keys and every top-level item, and changes only stat 12 (level, and so header
0x2B) and stat 13 (experience). The new characters are therefore level N - 1 with level-1 attributes, life and
mana: the save reader does not recompute max life or mana (save/0001), so the level-up adds to the level-1 values.

Out: <out-dir>/<Name>/<Name>.d2s and the recipe <out-dir>/<Name>/<Name>.json (rebuild one with
`d2s.py build <excel-dir> <Name>.json <base> <Name>.d2s`), one character per directory (a slot's saves directory
takes one). Name = Xp<Ama|Sor|Nec|Pal|Bar|Dru|Asn><A|B|C|D...><x|c>: the letter is the target level's position
in the level list (A = 2, B = 10, C = 50, D = 98 by default), x expansion, c classic; letters only, as the
character-name rule wants. Prints one line per save: name, base, level, experience, sha256. Stdlib only; writes
only under <out-dir>.
"""
import contextlib
import hashlib
import io
import json
import os
import string
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import d2s  # noqa: E402
import excel_bin as eb  # noqa: E402
import excel_layouts as L  # noqa: E402

ROOT = os.path.dirname(HERE)
SAMPLES = os.path.join(ROOT, "workspace", "samples", "d2s")
# class name (d2s.CLASSES order), sample file stem, name tag, classic?
KINDS = [("Amazon", "smpama", "Ama", True), ("Sorceress", "smpsor", "Sor", True),
         ("Necromancer", "smpnec", "Nec", True), ("Paladin", "smppal", "Pal", True),
         ("Barbarian", "smpbar", "Bar", True), ("Druid", "smpdru", "Dru", False),
         ("Assassin", "smpasn", "Asn", False)]
LEVELS = [2, 10, 50, 98]
SEED = 34000


def thresholds(excel_dir):
    """class name -> [threshold of level N for N = 0..100]: experience.bin record N, in the class's column."""
    _, _, recs, _ = eb.load_table(excel_dir, "experience")
    fields = {f["col"]: f for f in L.LAYOUTS["experience"]["fields"]}
    return {c: [eb.decode_field(r, fields[c]) for r in recs] for c, _, _, _ in KINDS}


def base_recipe(path, isc, kinds, cls, game):
    with open(path, "rb") as fh:
        b = fh.read()
    f = d2s.parse(b, isc, kinds)
    if d2s.CLASSES[f["header"]["cls"]] != cls:
        raise d2s.D2sError("%s is not a %s" % (path, cls))
    stats = {}
    for sid, param, v in f["stats"]:
        if param is not None:
            raise d2s.D2sError("%s: param stat %d" % (path, sid))
        if 6 <= sid <= 11:
            if v & 0xFF:
                raise d2s.D2sError("%s: stat %d has a fraction (%d)" % (path, sid, v))
            v >>= 8
        stats[str(sid)] = v
    keep = sorted({it["code"].strip() for it in f["items"]["items"] if "parent" not in it})
    return dict(game=game, **{"class": cls}), stats, keep


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 2
    excel, out = argv[0], argv[1]
    levels = [int(a) for a in argv[2:]] or LEVELS
    if any(not 2 <= n <= 99 for n in levels) or len(levels) > 26:
        print("levels must be 2..99, at most 26")
        return 2
    isc, kinds = d2s.load_isc(excel), d2s.load_kinds(excel)
    thr = thresholds(excel)
    os.makedirs(os.path.join(out, "_bases"), exist_ok=True)
    k = 0
    for game in ("expansion", "classic"):
        for cls, stem, tag, has_classic in KINDS:
            if game == "classic" and not has_classic:
                continue
            base = os.path.join(SAMPLES, stem + ".d2s")
            if game == "classic":
                with open(base, "rb") as fh:
                    img = d2s.to_classic(fh.read(), isc, kinds)
                base = os.path.join(out, "_bases", stem + "-classic.d2s")
                with open(base, "wb") as fh:
                    fh.write(img)
            head, stats, keep = base_recipe(base, isc, kinds, cls, game)
            for li, n in enumerate(levels):
                name = "Xp%s%s%s" % (tag, string.ascii_uppercase[li], "x" if game == "expansion" else "c")
                exp = thr[cls][n] - 1
                rc = dict(head, seed=SEED + k, name=name, stats=dict(stats, **{"12": n - 1, "13": exp}),
                          keep_items=keep)
                k += 1
                d = os.path.join(out, name)
                os.makedirs(d, exist_ok=True)
                rp, dst = os.path.join(d, name + ".json"), os.path.join(d, name + ".d2s")
                with open(rp, "w") as fh:
                    json.dump(rc, fh, indent=2)
                    fh.write("\n")
                with contextlib.redirect_stdout(io.StringIO()):
                    d2s.build(excel, rp, base, dst)
                with open(dst, "rb") as fh:
                    sha = hashlib.sha256(fh.read()).hexdigest()
                print("%-8s %-20s level %2d exp %10d  %s" % (name, os.path.basename(base), n - 1, exp, sha))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except d2s.D2sError as e:
        print("error:", e, file=sys.stderr)
        sys.exit(1)
