#!/usr/bin/env python3
"""The lane run ledger, docs/plans/metrics.md, without reading it into an agent's context.

    python3 -I tools/metrics.py append --date YYYY-MM-DD --lane LANE --plan "NNNN Px" --kind KIND
                                       --tokens N --tools N --wall N [--slot S] [--verdict V] [--fixes F]
    python3 -I tools/metrics.py summary [--since YYYY-MM-DD] [--by kind|date|lane]

`append` adds one row at the end of the Runs table. `--lane` is written as given, so pass the
backticked form the table uses (`` `lane/p51a` `` or `` `lane/p51a` review ``). Missing cells are
written as an em dash. `summary` prints runs, total and mean agent tokens per group.

Every command takes --root DIR (default: this checkout).
"""
import argparse
import collections
import os
import re
import sys

LEDGER = "docs/plans/metrics.md"
ROW = re.compile(r"^\| \d{4}-\d{2}-\d{2} \|")
DASH = "—"


def thousands(n):
    return f"{n:,}".replace(",", " ")


def parse_int(cell):
    digits = re.sub(r"[\s  ]", "", cell)
    return int(digits) if digits.isdigit() else None


def rows(lines):
    for line in lines:
        if ROW.match(line):
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if len(cells) >= 10:
                yield cells


def cmd_append(args, path):
    with open(path, encoding="utf-8") as f:
        lines = f.readlines()
    last = max((i for i, line in enumerate(lines) if ROW.match(line)), default=None)
    if last is None:
        sys.exit(f"{LEDGER}: no Runs table rows found")
    cells = [args.date, args.lane, args.plan, args.kind, thousands(args.tokens), str(args.tools),
             str(args.wall), args.slot or DASH, args.verdict or DASH, args.fixes or DASH]
    if any("|" in c for c in cells):
        sys.exit("a cell may not contain '|'")
    lines.insert(last + 1, "| " + " | ".join(cells) + " |\n")
    with open(path, "w", encoding="utf-8") as f:
        f.writelines(lines)
    print(f"appended after line {last + 1}")


def cmd_summary(args, path):
    with open(path, encoding="utf-8") as f:
        lines = f.readlines()
    key = {"date": 0, "lane": 1, "kind": 3}[args.by]
    groups = collections.defaultdict(lambda: [0, 0])
    for cells in rows(lines):
        tokens = parse_int(cells[4])
        if tokens is None or (args.since and cells[0] < args.since):
            continue
        g = groups[cells[key]]
        g[0] += 1
        g[1] += tokens
    order = sorted(groups.items(), key=(lambda kv: kv[0]) if args.by == "date" else (lambda kv: -kv[1][1]))
    total = sum(v[1] for v in groups.values())
    for name, (n, t) in order:
        print(f"{name:40} {n:4} runs {thousands(t):>12} tokens  mean {thousands(t // n):>9}  {100 * t / total:5.1f}%")
    print(f"{'total':40} {sum(v[0] for v in groups.values()):4} runs {thousands(total):>12} tokens")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--root", default=os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    sub = p.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("append")
    a.add_argument("--date", required=True)
    a.add_argument("--lane", required=True)
    a.add_argument("--plan", required=True)
    a.add_argument("--kind", required=True)
    a.add_argument("--tokens", type=int, required=True)
    a.add_argument("--tools", type=int, required=True)
    a.add_argument("--wall", type=int, required=True)
    a.add_argument("--slot")
    a.add_argument("--verdict")
    a.add_argument("--fixes")
    s = sub.add_parser("summary")
    s.add_argument("--since")
    s.add_argument("--by", choices=["kind", "date", "lane"], default="kind")
    args = p.parse_args()
    path = os.path.join(args.root, LEDGER)
    {"append": cmd_append, "summary": cmd_summary}[args.cmd](args, path)


if __name__ == "__main__":
    main()
