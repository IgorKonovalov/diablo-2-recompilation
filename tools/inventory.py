"""Emit a Markdown inventory table for every file under a directory.

Usage: python3 -I tools/inventory.py <root> [--origin LABEL] [--class NAME GLOB ...] ...

Columns: relative path, size in bytes, sha256, file(1) type, origin, class.
`--class NAME GLOB...` may repeat; a path gets the first class whose glob matches
(case-insensitive fnmatch on the relative path), else `game`.
Stdlib only; calls /usr/bin/file for the type column. Read-only.
"""
import fnmatch
import hashlib
import os
import subprocess
import sys


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def ftype(path):
    r = subprocess.run(["file", "-b", path], capture_output=True, text=True, check=True)
    return r.stdout.strip().replace("|", "/")


def main(argv):
    if not argv or argv[0].startswith("-"):
        print(__doc__)
        return 2
    root, origin, classes = argv[0], "installer", []
    i = 1
    while i < len(argv):
        if argv[i] == "--origin":
            origin = argv[i + 1]
            i += 2
        elif argv[i] == "--class":
            name, globs = argv[i + 1], []
            i += 2
            while i < len(argv) and not argv[i].startswith("--"):
                globs.append(argv[i].lower())
                i += 1
            classes.append((name, globs))
        else:
            raise SystemExit("unknown arg " + argv[i])
    paths = []
    for d, _, fs in os.walk(root):
        for f in fs:
            paths.append(os.path.relpath(os.path.join(d, f), root))
    paths.sort(key=str.lower)
    print("| path | size | sha256 | type | origin | class |")
    print("|---|---:|---|---|---|---|")
    for rel in paths:
        full = os.path.join(root, rel)
        cls = next((n for n, gs in classes if any(fnmatch.fnmatch(rel.lower(), g) for g in gs)), "game")
        print("| `%s` | %d | `%s` | %s | %s | %s |"
              % (rel, os.path.getsize(full), sha256(full), ftype(full), origin, cls))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
