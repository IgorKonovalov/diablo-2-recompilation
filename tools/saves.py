"""Set the harness saves directory aside, install test characters, and restore it with a sha256 check.

Usage:
  python3 -I tools/saves.py [--slot N] status
  python3 -I tools/saves.py [--slot N] aside   <tag>
  python3 -I tools/saves.py [--slot N] install <tag> <file.d2s>...
  python3 -I tools/saves.py [--slot N] restore <tag>

--slot N (default 0, anywhere on the line) picks the harness slot (tools/slots.py). Slot 0's saves directory is
workspace/wineprefix/drive_c/users/$USER/Saved Games/Diablo II and its asides live in workspace/runtime/, as they
always have; slot N >= 1 uses workspace/wineprefix-N/... and workspace/runtime/slot-N/. Each slot has its own aside
copies and manifests, and a tag is only ever restored into the slot it was set aside from. `aside` copies every file there to workspace/runtime/saves-aside-<tag>/, writes a
sha256 manifest next to it, verifies the copy, then empties the saves directory. `install` copies test
.d2s files into the emptied directory (only while that tag is aside). `restore` empties the directory,
copies the aside files back, verifies every sha256 against the manifest, and only then deletes the aside
copy; on a mismatch it stops and keeps the aside copy. `aside`, `install` and `restore` refuse to run
while the slot is busy (the game rewrites saves on exit): a game.exe in the slot's prefix, or a tools/d2run.py running
on the slot or on a slot that cannot be told from its command line.

Exit 0 on success, 1 on any refusal or mismatch. Stdlib only.
"""
import getpass
import hashlib
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import slots  # noqa: E402

ROOT = os.path.dirname(HERE)
WS = os.path.join(ROOT, "workspace")
SLOT = 0
SAVES = os.path.join(WS, "wineprefix", "drive_c", "users", getpass.getuser(), "Saved Games", "Diablo II")
RUNTIME = os.path.join(WS, "runtime")


def configure(slot, ws=None):
    """Point SAVES and RUNTIME at slot `slot` (ws: a stand-in workspace, for tests)."""
    global SLOT, SAVES, RUNTIME
    SLOT = slots.check(slot)
    SAVES = slots.saves_dir(slot, ws or WS)
    RUNTIME = slots.runtime(slot, ws or WS)
    return SAVES, RUNTIME


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
    return [str(p) for p in slots.busy(SLOT, WS)]


def need_idle():
    busy = harness_busy()
    if busy:
        die("slot %d is busy: tools/d2run.py or game.exe running (pids %s); stop the harness first"
            % (SLOT, " ".join(busy)))


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
    names = files(SAVES)        # may be empty: a new slot's saves directory (restore then empties it again)
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


def take_slot(argv):
    argv = list(argv)
    slot = 0
    for i, a in enumerate(argv):
        if a == "--slot" or a.startswith("--slot="):
            v = argv[i + 1] if a == "--slot" and i + 1 < len(argv) else a.partition("=")[2]
            del argv[i:i + (2 if a == "--slot" else 1)]
            try:
                slot = slots.check(int(v))
            except (ValueError, slots.SlotError):
                die("--slot must be an integer 0..%d" % slots.MAX_SLOT)
            break
    return slot, argv


def main(argv):
    slot, argv = take_slot(argv)
    configure(slot)
    if not os.path.isdir(SAVES):
        die("saves directory not found: %s%s" % (SAVES, "" if slot == 0 else
                                                 " (create the slot: python3 -I tools/slots.py create %d)" % slot))
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
