"""Set the harness saves directory aside, install test characters, and restore it with a sha256 check.

Usage:
  python3 -I tools/saves.py status
  python3 -I tools/saves.py aside   <tag>
  python3 -I tools/saves.py install <tag> <file.d2s>...
  python3 -I tools/saves.py restore <tag>

The saves directory is workspace/wineprefix/drive_c/users/$USER/Saved Games/Diablo II (the only one the
harness game reads). `aside` copies every file there to workspace/runtime/saves-aside-<tag>/, writes a
sha256 manifest next to it, verifies the copy, then empties the saves directory. `install` copies test
.d2s files into the emptied directory (only while that tag is aside). `restore` empties the directory,
copies the aside files back, verifies every sha256 against the manifest, and only then deletes the aside
copy; on a mismatch it stops and keeps the aside copy. `aside`, `install` and `restore` refuse to run
while a tools/d2run.py process is alive (the game rewrites saves on exit).

Exit 0 on success, 1 on any refusal or mismatch. Stdlib only.
"""
import getpass
import hashlib
import os
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WS = os.path.join(ROOT, "workspace")
SAVES = os.path.join(WS, "wineprefix", "drive_c", "users", getpass.getuser(), "Saved Games", "Diablo II")
RUNTIME = os.path.join(WS, "runtime")


def die(msg):
    print("saves: " + msg, file=sys.stderr)
    sys.exit(1)


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def files(d):
    return sorted(n for n in os.listdir(d) if os.path.isfile(os.path.join(d, n)))


def aside_paths(tag):
    if not tag or not all(c.isalnum() or c in "-_" for c in tag):
        die("tag must be letters, digits, '-' or '_'")
    base = os.path.join(RUNTIME, "saves-aside-" + tag)
    return base, base + ".sha256"


def harness_busy():
    r = subprocess.run(["pgrep", "-f", "tools/d2run.py"], capture_output=True, text=True)
    return [p for p in r.stdout.split() if p and int(p) != os.getpid()]


def need_idle():
    busy = harness_busy()
    if busy:
        die("tools/d2run.py is running (pids %s); stop the harness first" % " ".join(busy))


def read_manifest(path):
    out = {}
    with open(path) as f:
        for ln in f:
            h, n = ln.rstrip("\n").split("  ", 1)
            out[n] = h
    return out


def clear_saves():
    for n in files(SAVES):
        os.remove(os.path.join(SAVES, n))


def cmd_status():
    print("saves dir: %s" % SAVES)
    for n in files(SAVES):
        print("  %s  %s" % (sha(os.path.join(SAVES, n))[:16], n))
    asides = sorted(n for n in os.listdir(RUNTIME) if n.startswith("saves-aside-") and not n.endswith(".sha256"))
    print("aside: %s" % (", ".join(asides) if asides else "none"))
    busy = harness_busy()
    print("harness: %s" % ("running " + " ".join(busy) if busy else "idle"))


def cmd_aside(tag):
    need_idle()
    base, man = aside_paths(tag)
    if os.path.exists(base) or os.path.exists(man):
        die("%s already exists; restore it first" % base)
    names = files(SAVES)
    if not names:
        die("saves directory is empty; nothing to set aside")
    os.makedirs(base)
    lines = []
    for n in names:
        src = os.path.join(SAVES, n)
        shutil.copy2(src, os.path.join(base, n))
        lines.append("%s  %s\n" % (sha(src), n))
    with open(man, "w") as f:
        f.writelines(lines)
    for n, h in read_manifest(man).items():
        if sha(os.path.join(base, n)) != h:
            die("copy of %s does not match; saves directory left untouched" % n)
    clear_saves()
    print("set aside %d file(s) to %s; saves directory emptied" % (len(names), base))


def cmd_install(tag, paths):
    need_idle()
    base, _ = aside_paths(tag)
    if not os.path.isdir(base):
        die("tag %s is not aside; run `aside %s` first" % (tag, tag))
    for p in paths:
        if not p.lower().endswith(".d2s") or not os.path.isfile(p):
            die("not a .d2s file: %s" % p)
    for p in paths:
        shutil.copy2(p, os.path.join(SAVES, os.path.basename(p)))
        print("installed %s" % os.path.basename(p))


def cmd_restore(tag):
    need_idle()
    base, man = aside_paths(tag)
    if not os.path.isdir(base) or not os.path.isfile(man):
        die("no aside copy for tag %s" % tag)
    want = read_manifest(man)
    for n, h in want.items():
        if sha(os.path.join(base, n)) != h:
            die("aside copy of %s does not match its manifest; nothing changed" % n)
    clear_saves()
    for n in want:
        shutil.copy2(os.path.join(base, n), os.path.join(SAVES, n))
    bad = [n for n, h in want.items() if sha(os.path.join(SAVES, n)) != h]
    extra = [n for n in files(SAVES) if n not in want]
    if bad or extra:
        die("restore mismatch (bad %s, extra %s); aside copy kept at %s" % (bad, extra, base))
    shutil.rmtree(base)
    os.remove(man)
    print("restored %d file(s), all sha256 match; aside copy removed" % len(want))


def main(argv):
    if not os.path.isdir(SAVES):
        die("saves directory not found: %s" % SAVES)
    os.makedirs(RUNTIME, exist_ok=True)
    if argv[:1] == ["status"] and len(argv) == 1:
        cmd_status()
    elif argv[:1] == ["aside"] and len(argv) == 2:
        cmd_aside(argv[1])
    elif argv[:1] == ["install"] and len(argv) >= 3:
        cmd_install(argv[1], argv[2:])
    elif argv[:1] == ["restore"] and len(argv) == 2:
        cmd_restore(argv[1])
    else:
        print(__doc__.strip())
        sys.exit(2)


if __name__ == "__main__":
    main(sys.argv[1:])
