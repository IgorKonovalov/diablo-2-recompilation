#!/usr/bin/env python3
"""Draw Mermaid blocks as GitHub would and report those that do not come out right.

Usage: python3 -I tools/mermaid_lint.py [--no-cache] [PATH ...]

PATH is a markdown file or a directory; the default is every tracked .md except the deliberately
broken gate fixtures. The checks are rule E17 of tools/gate.py (see tools/mermaid_render.mjs); a block
Mermaid cannot parse fails here too. Exit 0 clean, 1 a block failed, 2 the check could not run.
"""
import argparse
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import gate  # noqa: E402

REPO = os.path.dirname(HERE)


def tracked():
    names = subprocess.run(["git", "-C", REPO, "ls-files", "*.md"], capture_output=True, text=True, check=True).stdout.split("\n")
    return [os.path.join(REPO, n) for n in names if n and not n.startswith("tools/gate/fixtures/")]


def expand(paths):
    for p in paths:
        if os.path.isdir(p):
            for d, _, names in os.walk(p):
                yield from (os.path.join(d, n) for n in sorted(names) if n.endswith(".md"))
        else:
            yield p


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--no-cache", action="store_true", help="draw every block, even one already drawn clean")
    ap.add_argument("paths", nargs="*")
    a = ap.parse_args(argv)
    blocks = []
    for path in expand(a.paths) if a.paths else tracked():
        with open(path, encoding="utf-8") as f:
            blocks += [(os.path.relpath(path), n, b) for n, b in gate.mermaid_blocks(f.read())]
    why, failures = gate.render_mermaid(blocks, REPO, redraw=a.no_cache) if blocks else (None, [])
    if why:
        print(f"mermaid lint: could not run: {why}", file=sys.stderr)
        return 2
    for rel, line, message in failures:
        print(f"{rel}:{line}: {message}")
    print(f"mermaid lint: {len(blocks)} blocks, {len(failures)} failed")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
