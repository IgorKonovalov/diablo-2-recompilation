"""Compare two extracted directory trees by sha256, matching paths case-insensitively.

Usage: python3 -I tools/tree_diff.py <treeA> <treeB> [--prefix data/global/excel] [--list]

Prints counts of identical / differing / only-in-A / only-in-B files, broken down by top-level
directory (two path levels). With --list, prints every non-identical path. --prefix restricts the
comparison to paths under that prefix. Names like File00001234.xxx (no listfile entry) are
counted separately because they cannot be matched across archives. Stdlib only. Read-only.
"""
import collections
import hashlib
import os
import re
import sys

UNNAMED = re.compile(r"^file\d{8}\.", re.I)


def scan(root, prefix):
    out = {}
    for d, _, fs in os.walk(root):
        for f in fs:
            full = os.path.join(d, f)
            rel = os.path.relpath(full, root).replace("\\", "/").lower()
            if prefix and not rel.startswith(prefix):
                continue
            with open(full, "rb") as fh:
                out[rel] = hashlib.sha256(fh.read()).hexdigest()
    return out


def bucket(p):
    return "/".join(p.split("/")[:3]) if "/" in p else "(root)"


def main(argv):
    args = [a for a in argv if not a.startswith("--")]
    if len(args) < 2:
        print(__doc__)
        return 2
    prefix = ""
    if "--prefix" in argv:
        prefix = argv[argv.index("--prefix") + 1].lower().rstrip("/") + "/"
        args = [a for a in args if a != argv[argv.index("--prefix") + 1]]
    a, b = scan(args[0], prefix), scan(args[1], prefix)
    ua = {p for p in a if UNNAMED.match(os.path.basename(p))}
    ub = {p for p in b if UNNAMED.match(os.path.basename(p))}
    na, nb = set(a) - ua, set(b) - ub
    stats = collections.defaultdict(collections.Counter)
    rows = []
    for p in sorted(na | nb):
        if p in na and p in nb:
            k = "same" if a[p] == b[p] else "DIFF"
        else:
            k = "onlyA" if p in na else "onlyB"
        stats[bucket(p)][k] += 1
        if k != "same":
            rows.append((k, p))
    tot = collections.Counter()
    print("%-40s %7s %7s %7s %7s" % ("dir", "same", "DIFF", "onlyA", "onlyB"))
    for d in sorted(stats):
        s = stats[d]
        tot.update(s)
        print("%-40s %7d %7d %7d %7d" % (d, s["same"], s["DIFF"], s["onlyA"], s["onlyB"]))
    print("%-40s %7d %7d %7d %7d" % ("TOTAL", tot["same"], tot["DIFF"], tot["onlyA"], tot["onlyB"]))
    print("unnamed (no listfile name): A=%d B=%d" % (len(ua), len(ub)))
    if "--list" in argv:
        for k, p in rows:
            print("%s %s" % (k, p))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
