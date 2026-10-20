"""Recount the `oracle` mentions of the core and enabler specs against the ledger of chain/0001 (plan 0048 Phase 0).

Usage: python3 -I tools/oracle_ledger.py [--root DIR]

Lists every line of docs/specs/{items,monsters,drlg,objects,rng,data}/ that matches `oracle` (case-insensitive),
the same set as the kept grep of docs/findings/chain/0001-oracles.md § 1, and compares it with the table of that
finding's § 6 ("lines -> oracle, S or N"). Prints the per-file totals, the lines missing from or extra in the
ledger, the S and N counts and the § 2 oracles that no line names. Exit 1 when the ledger and the specs differ.
Reads only docs/. Stdlib only.
"""
import argparse
import hashlib
import os
import re
import sys

DIRS = ("items", "monsters", "drlg", "objects", "rng", "data")
FINDING = "docs/findings/chain/0001-oracles.md"
N_ORACLES = 31


def spec_lines(root):
    out = []
    for d in DIRS:
        base = os.path.join(root, "docs/specs", d)
        for dirpath, _dirs, files in os.walk(base):
            for f in files:
                p = os.path.join(dirpath, f)
                rel = os.path.relpath(p, os.path.join(root, "docs/specs"))
                with open(p, encoding="utf-8") as fh:
                    for n, line in enumerate(fh, 1):
                        if "oracle" in line.lower():
                            out.append((rel, n))
    return sorted(out)


def ledger(root):
    with open(os.path.join(root, FINDING), encoding="utf-8") as fh:
        text = fh.read()
    sec = text.split("## 6. Every mention, assigned")[1].split("## Data touched")[0]
    got, ids, s_n = {}, set(), {"S": 0, "N": 0}
    for row in sec.splitlines():
        m = re.match(r"\| (\S+\.md) \| (\d+) \| (.*) \|$", row)
        if not m:
            continue
        rel, total, body = m.group(1), int(m.group(2)), m.group(3)
        count = 0
        for seg in body.split(";"):
            lines, cls = seg.split("→")
            nums = [int(x) for x in re.findall(r"\d+", lines)]
            count += len(nums)
            cls = cls.strip()
            if cls in s_n:
                s_n[cls] += len(nums)
            else:
                for r in cls.split(","):
                    r = r.strip()
                    if "–" in r:
                        a, b = map(int, r.split("–"))
                        ids |= set(range(a, b + 1))
                    else:
                        ids.add(int(r))
            for x in nums:
                got[(rel, x)] = cls
        if count != total:
            print("ledger row %s: %d lines listed, total says %d" % (rel, count, total))
    return got, ids, s_n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    a = ap.parse_args()
    found = spec_lines(a.root)
    got, ids, s_n = ledger(a.root)
    listing = "".join("docs/specs/%s:%d\n" % x for x in found)
    per = {}
    for rel, _n in found:
        per[rel] = per.get(rel, 0) + 1
    for rel in sorted(per):
        print("%-28s %3d" % (rel, per[rel]))
    missing = [x for x in found if x not in got]
    extra = [x for x in got if x not in set(found)]
    print("lines %d in %d files, sha256 %s" % (len(found), len(per),
                                               hashlib.sha256(listing.encode()).hexdigest()))
    print("ledger: %d lines, S %d, N %d, naming an oracle %d" % (len(got), s_n["S"], s_n["N"],
                                                                 len(got) - s_n["S"] - s_n["N"]))
    print("oracles named by no line: %s" % (sorted(set(range(1, N_ORACLES + 1)) - ids) or "none"))
    for x in missing:
        print("missing from the ledger: docs/specs/%s:%d" % x)
    for x in sorted(extra):
        print("in the ledger, no match: docs/specs/%s:%d" % x)
    return 1 if missing or extra else 0


if __name__ == "__main__":
    sys.exit(main())
