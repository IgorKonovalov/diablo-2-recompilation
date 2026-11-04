"""The `lane/p55c` review's check of reader rev 2's controls: reverse one test of tools/frame_xs.py at a time, in a temporary copy,
and list the controls of `selftest2` that turn red. A test no control catches prints `NONE`. Stdlib only; no game; no log read.

    python3 -I tools/frame_xs_mutants.py > OUT
"""
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
MUTANTS = {
    "arith": ('if seed not in a and not skip:', 'if False:'),
    "class": ('if not rows_here:', 'if False:'),
    "trigger": ('def trigger_holds(trig, key):\n', 'def trigger_holds(trig, key):\n        return True\n'),
    "even": ('if n % 2:', 'if False:'),
    "first": ('elif o.get("fr") <= frame_start:', 'elif True:'),
    "free": ('top["kind"] in (6, 11):', 'False:'),
    "rank": ('if r < last_rank:', 'if False:'),
    "slot": ('elif e in q:', 'elif False:'),
    "nopair-game": ('if not any(fw.row_has(r, loc) and not r.get("client") for r in passdraw):\n                    fail(no, "XS", "nopair", "game',
                    'if False:\n                    fail(no, "XS", "nopair", "game'),
    "nopair-unit": ('if not any(fw.row_has(r, loc) and not r.get("client") for r in passdraw):\n                fail(no, "XS", "nopair", "%s',
                    'if False:\n                fail(no, "XS", "nopair", "%s'),
    "every-frame": ('if pl is not None and pl < ql:', 'if False:'),
    "fresh": ('(k == "G" and low in fresh and loc not in fw.FRESH_INIT)', 'False'),
    "room": ('return key[0] == "R" and any(r["tag"] == "RU0" for r in stack)', 'return key[0] == "R"'),
}


def main():
    with open(os.path.join(HERE, "frame_xs.py")) as f:
        src = f.read()
    code = 0
    for name, (a, b) in MUTANTS.items():
        if a not in src:
            print("%s: PATTERN GONE" % name)
            code = 1
            continue
        with tempfile.TemporaryDirectory() as d:
            for f in ("frame_window.py", "frame_volume.py"):
                shutil.copy(os.path.join(HERE, f), d)
            with open(os.path.join(d, "frame_xs.py"), "w") as f:
                f.write(src.replace(a, b, 1))
            r = subprocess.run([sys.executable, "-I", "-c", "import sys;sys.path.insert(0,%r);import frame_xs;sys.exit(frame_xs.selftest2())" % d],
                               capture_output=True, text=True)
        red = [ln[5:].split("  <-")[0][:60] for ln in r.stdout.split("\n") if ln.startswith("FAIL")]
        if r.returncode not in (0, 1) or "Traceback" in r.stderr:
            print("%s: CRASH %s" % (name, r.stderr.strip().split("\n")[-1][:80]))
            code = 1
        else:
            print("%s: %s" % (name, "; ".join(red) if red else "NONE"))
            code |= not red
    return code


if __name__ == "__main__":
    sys.exit(main())
