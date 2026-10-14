#!/usr/bin/env python3
"""Harness slots: several game copies side by side under wine, one per slot.

    python3 -I tools/slots.py status
    python3 -I tools/slots.py create <N>        # N >= 1: clone the base prefix to workspace/wineprefix-N
    python3 -I tools/slots.py stop   <N>        # kill slot N's driver (pidfile), then wineserver -k on its prefix

Slot convention:
  slot 0      display :7       prefix workspace/wineprefix     driver pidfile workspace/runtime/d2run-driver.pid
                                                               saves asides workspace/runtime/saves-aside-<tag>
  slot N >= 1 display :(7+N)   prefix workspace/wineprefix-N   driver pidfile workspace/runtime/d2run-driver-slotN.pid
                                                               saves asides workspace/runtime/slot-N/saves-aside-<tag>
Slots run 0..MAX_SLOT. The game itself is never in a prefix: every slot starts game.exe in the shared
workspace/runtime/game (d2run.py --game-dir; the prefix's registry InstallPath points there), and a prefix holds only
wine's own files, the Blizzard registry keys and the saves directory. Two copies in one wine session are refused by the
game ("Only one copy of Diablo II may run at a time"); in separate prefixes on separate displays they run side by side
(plan 0011).

workspace/wineprefix2 is plan 0011's second client (ADR-0008). It is not a slot and is left as it is; it used display
:8, which is now slot 1's display, so it cannot run beside slot 1. `status` lists a game in it under "other".

`create` copies the base prefix file by file with reflinks where the filesystem allows (btrfs: nearly free), symlinks
kept as symlinks, and skips everything under each user's "Saved Games" (the clone gets an empty
"Saved Games/Diablo II"); it only reads the base prefix, so it is safe while slot 0 runs. `stop` never touches another
slot's prefix and never matches processes by pattern: the driver comes from the slot's pidfile and is killed only if its
cmdline still names d2run.py; the game dies with its wineserver. `stop 0` is allowed (it is the old cleanup) but kills the
slot 0 game.

The other harness tools take --slot N: d2run.py, d2pilot.py, xdrive.py, d2hunt.py and saves.py (see their docstrings).
Stdlib only.
"""
import fcntl
import getpass
import os
import shutil
import signal
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WS = os.path.join(ROOT, "workspace")
BASE_DISPLAY = 7
MAX_SLOT = 8
FICLONE = 0x40049409


class SlotError(ValueError):
    pass


def check(n):
    if not isinstance(n, int) or n < 0 or n > MAX_SLOT:
        raise SlotError("slot must be an integer 0..%d, not %r" % (MAX_SLOT, n))
    return n


def display(n):
    return ":%d" % (BASE_DISPLAY + check(n))


def prefix(n, ws=None):
    ws = ws or WS
    return os.path.join(ws, "wineprefix" if check(n) == 0 else "wineprefix-%d" % n)


def runtime(n, ws=None):
    """Where slot n keeps its saves asides (slot 0: the historical workspace/runtime itself)."""
    ws = ws or WS
    base = os.path.join(ws, "runtime")
    return base if check(n) == 0 else os.path.join(base, "slot-%d" % n)


def pidfile(n, ws=None):
    ws = ws or WS
    name = "d2run-driver.pid" if check(n) == 0 else "d2run-driver-slot%d.pid" % n
    return os.path.join(ws, "runtime", name)


def saves_dir(n, ws=None, user=None):
    return os.path.join(prefix(n, ws), "drive_c", "users", user or getpass.getuser(), "Saved Games", "Diablo II")


def suffix(n):
    """File-name tag for screenshots and logs: empty for slot 0 (historical names), '-sN' otherwise."""
    return "" if check(n) == 0 else "-s%d" % n


def slot_of_display(d):
    """The slot that owns display d (':8' -> 1), or None outside the slot range."""
    try:
        k = int(str(d).lstrip(":").split(".")[0]) - BASE_DISPLAY
    except ValueError:
        return None
    return k if 0 <= k <= MAX_SLOT else None


def slot_of_prefix(p, ws=None):
    rp = os.path.realpath(p)
    for n in range(MAX_SLOT + 1):
        if os.path.realpath(prefix(n, ws)) == rp:
            return n
    return None


def resolve(slot=None, disp=None, pfx=None, ws=None):
    """(slot, display, prefix) from the --slot/--display/--prefix a tool was given.

    --slot fixes both; an explicit --display or --prefix that names another slot's is an error. Without --slot the
    display picks the slot (default :7, slot 0) and the prefix defaults to that slot's; an explicit --prefix outside
    the slot scheme (workspace/wineprefix2) is kept as given, with the slot of its display.
    """
    if slot is not None:
        check(slot)
        if disp is not None and disp != display(slot):
            raise SlotError("--display %s contradicts --slot %d (display %s)" % (disp, slot, display(slot)))
        if pfx is not None and os.path.realpath(pfx) != os.path.realpath(prefix(slot, ws)):
            raise SlotError("--prefix %s contradicts --slot %d (prefix %s)" % (pfx, slot, prefix(slot, ws)))
        return slot, display(slot), prefix(slot, ws)
    disp = disp or display(0)
    n = slot_of_display(disp)
    if pfx is None:
        if n is None:
            raise SlotError("display %s is outside the slots (:%d..:%d); pass --prefix too"
                            % (disp, BASE_DISPLAY, BASE_DISPLAY + MAX_SLOT))
        return n, disp, prefix(n, ws)
    pn = slot_of_prefix(pfx, ws)
    if pn is not None and n is not None and pn != n:
        raise SlotError("--prefix %s is slot %d's but --display %s is slot %d's" % (pfx, pn, disp, n))
    return n, disp, os.path.abspath(pfx)


def pick_display(slot=None, disp=None):
    """(slot, display) for the tools that only drive a display (xdrive.py, d2pilot.py, d2hunt.py): --slot sets the
    display, a contradicting --display is an error, neither means slot 0 (:7). A display outside the slots is
    allowed, with slot None."""
    if slot is not None:
        check(slot)
        if disp is not None and disp != display(slot):
            raise SlotError("--display %s contradicts --slot %d (display %s)" % (disp, slot, display(slot)))
        return slot, display(slot)
    disp = disp or display(0)
    return slot_of_display(disp), disp


def argv_slot(argv, cwd=None, ws=None):
    """The slot a d2run.py command line runs on: from its --slot/--display/--prefix. None if it cannot be told
    (a prefix outside the slots, or a malformed line)."""
    vals = {}
    for i, a in enumerate(argv):
        for k in ("--slot", "--display", "--prefix"):
            if a == k and i + 1 < len(argv):
                vals[k] = argv[i + 1]
            elif a.startswith(k + "="):
                vals[k] = a.split("=", 1)[1]
    try:
        pfx = vals.get("--prefix")
        if pfx is not None and cwd and not os.path.isabs(pfx):
            pfx = os.path.join(cwd, pfx)
        slot = int(vals["--slot"]) if "--slot" in vals else None
        n, _, p = resolve(slot, vals.get("--display"), pfx, ws)
    except (SlotError, ValueError):
        return None
    if slot_of_prefix(p, ws) != n:
        return None
    return n


# ---- processes -----------------------------------------------------------------------------------------------

def _read(path, binary=False):
    with open(path, "rb" if binary else "r") as f:
        return f.read()


def procs():
    """[(pid, ppid, state, argv, env)] for every process we may read."""
    out = []
    for d in os.listdir("/proc"):
        if not d.isdigit():
            continue
        try:
            stat = _read("/proc/%s/stat" % d).rsplit(")", 1)[1].split()
            argv = [a.decode("latin1") for a in _read("/proc/%s/cmdline" % d, True).split(b"\0")[:-1]]
        except OSError:
            continue
        try:
            env = dict(kv.decode("latin1").split("=", 1) for kv in _read("/proc/%s/environ" % d, True).split(b"\0")
                       if b"=" in kv)
        except OSError:
            env = {}
        out.append((int(d), int(stat[1]), stat[0], argv, env))
    return out


def is_game(argv):
    return bool(argv) and argv[0].lower().endswith("\\game.exe")


def games(ps=None):
    """{pid: (prefix realpath, display, state, ppid)} for every live game.exe."""
    out = {}
    for pid, ppid, st, argv, env in ps if ps is not None else procs():
        if st != "Z" and is_game(argv):
            out[pid] = (os.path.realpath(env.get("WINEPREFIX", "")), env.get("DISPLAY", "?"), st, ppid)
    return out


def d2runs(ps=None):
    """{pid: argv} of every live tools/d2run.py process (launchers and their driver children)."""
    out = {}
    for pid, ppid, st, argv, env in ps if ps is not None else procs():
        if st != "Z" and pid != os.getpid() and any(a.endswith("d2run.py") for a in argv[:3]):
            out[pid] = argv
    return out


def cwd_of(pid):
    try:
        return os.readlink("/proc/%d/cwd" % pid)
    except OSError:
        return None


def busy(n, ws=None, ps=None):
    """PIDs that make slot n busy: its game.exe (by WINEPREFIX) and every d2run.py that runs on slot n or whose slot
    cannot be told (counted against every slot, to be safe)."""
    ps = procs() if ps is None else ps
    want = os.path.realpath(prefix(n, ws))
    hit = [pid for pid, g in games(ps).items() if g[0] == want]
    for pid, argv in d2runs(ps).items():
        s = argv_slot(argv, cwd_of(pid), ws)
        if s is None or s == n:
            hit.append(pid)
    return sorted(set(hit))


def driver(n, ws=None):
    """(pid, alive) from slot n's driver pidfile, or (None, False)."""
    try:
        pid = int(_read(pidfile(n, ws)).split()[0])
    except (OSError, ValueError, IndexError):
        return None, False
    try:
        st = _read("/proc/%d/stat" % pid).rsplit(")", 1)[1].split()[0]
        ok = st != "Z" and b"d2run.py" in _read("/proc/%d/cmdline" % pid, True)
    except OSError:
        ok = False
    return pid, ok


# ---- commands ------------------------------------------------------------------------------------------------

def _clone_file(src, dst):
    """Copy one file, as a reflink when the filesystem can (FICLONE), else a plain copy; metadata as copy2."""
    with open(src, "rb") as fi, open(dst, "wb") as fo:
        try:
            fcntl.ioctl(fo.fileno(), FICLONE, fi.fileno())
        except OSError:
            fo.truncate(0)
            shutil.copyfileobj(fi, fo, 1 << 20)
    shutil.copystat(src, dst)
    return dst


def _ignore_saves(d, names):
    return list(names) if os.path.basename(d) == "Saved Games" else []


def create(n, ws=None):
    if check(n) == 0:
        raise SlotError("slot 0 is the base prefix itself; create takes N >= 1")
    src, dst = prefix(0, ws), prefix(n, ws)
    if os.path.lexists(dst):
        raise SlotError("%s already exists" % dst)
    if not os.path.isfile(os.path.join(src, "system.reg")):
        raise SlotError("no base prefix at %s" % src)
    tmp = dst + ".partial"
    if os.path.lexists(tmp):
        shutil.rmtree(tmp)
    shutil.copytree(src, tmp, symlinks=True, ignore=_ignore_saves, copy_function=_clone_file)
    users = os.path.join(tmp, "drive_c", "users")
    for u in os.listdir(users):
        if os.path.isdir(os.path.join(users, u, "Saved Games")):
            os.makedirs(os.path.join(users, u, "Saved Games", "Diablo II"), exist_ok=True)
    for reg in ("system.reg", "user.reg", "userdef.reg"):
        p = os.path.join(tmp, reg)
        if os.path.exists(p) and not _read(p, True).startswith(b"WINE REGISTRY"):
            raise SlotError("%s copied torn (no WINE REGISTRY header); left at %s" % (reg, tmp))
    os.makedirs(os.path.join(tmp, os.path.relpath(saves_dir(n, ws), dst)), exist_ok=True)
    os.rename(tmp, dst)
    os.makedirs(runtime(n, ws), exist_ok=True)
    return dst


def stop(n, ws=None, run=subprocess.run):
    pid, ok = driver(check(n), ws)
    if ok:
        os.kill(pid, signal.SIGKILL)
        print("slot %d: killed driver %d" % (n, pid))
    if pid is not None:
        try:
            os.unlink(pidfile(n, ws))
        except OSError:
            pass
    p = prefix(n, ws)
    if not os.path.isdir(p):
        raise SlotError("slot %d has no prefix (%s)" % (n, p))
    run(["wineserver", "-k"], env=dict(os.environ, WINEPREFIX=os.path.realpath(p)), stderr=subprocess.DEVNULL)
    print("slot %d: wineserver -k on %s" % (n, p))


def known_slots(ws=None):
    ns = [0]
    for n in range(1, MAX_SLOT + 1):
        if os.path.isdir(prefix(n, ws)) or os.path.exists(pidfile(n, ws)):
            ns.append(n)
    return ns


def status(ws=None):
    ps = procs()
    gs = games(ps)
    comm = {pid: argv for pid, _, _, argv, _ in ps}
    claimed = set()
    for n in known_slots(ws):
        p = prefix(n, ws)
        rp = os.path.realpath(p)
        mine = {pid: g for pid, g in gs.items() if g[0] == rp}
        claimed.update(mine)
        x = os.path.exists("/tmp/.X11-unix/X%d" % (BASE_DISPLAY + n))
        print("slot %d  display %s (%s)  prefix %s%s" % (n, display(n), "up" if x else "down",
                                                         os.path.relpath(p, ROOT), "" if os.path.isdir(p) else " MISSING"))
        for pid, (_, disp, st, ppid) in sorted(mine.items()):
            par = comm.get(ppid, [])
            dbg = "gdb %d" % ppid if par and os.path.basename(par[0]) == "gdb" else "no gdb"
            print("  game %d state %s on %s, %s" % (pid, st, disp, dbg))
        if not mine:
            print("  game: none")
        dpid, ok = driver(n, ws)
        print("  driver: %s" % ("%d alive" % dpid if ok else ("stale pidfile %d" % dpid if dpid else "none")))
        sd = saves_dir(n, ws)
        if os.path.isdir(sd):
            nf = len([f for f in os.listdir(sd) if os.path.isfile(os.path.join(sd, f))])
            rt = runtime(n, ws)
            asides = sorted(f[len("saves-aside-"):] for f in (os.listdir(rt) if os.path.isdir(rt) else [])
                            if f.startswith("saves-aside-") and not f.endswith(".sha256"))
            print("  saves: %d file(s); aside: %s" % (nf, ", ".join(asides) if asides else "none"))
        else:
            print("  saves: no saves directory")
    other = {pid: g for pid, g in gs.items() if pid not in claimed}
    for pid, (rp, disp, st, _) in sorted(other.items()):
        print("other   game %d state %s on %s, prefix %s" % (pid, st, disp, rp))


def main(argv):
    try:
        if argv == ["status"]:
            status()
        elif len(argv) == 2 and argv[0] in ("create", "stop"):
            n = int(argv[1])
            if argv[0] == "create":
                print("created %s" % create(n))
            else:
                stop(n)
        else:
            print(__doc__.strip())
            return 2
    except (SlotError, ValueError) as e:
        print("slots: %s" % e, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
