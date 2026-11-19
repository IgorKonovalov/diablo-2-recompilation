#!/usr/bin/env python3
"""Self-tests of the scripted widgets (ADR-0037, plan 0070 Phase 11; gate rule E21).

Usage: python3 -I tools/test_widgets.py

For each folder tools/widgets/<name>/ (widget.js, widget.json, fixture.json): the fixture is what the Python twin
(tools/widgets/twins.py) computes now; and, when node is on PATH, widget.js's `compute` gives, for every fixture
case, exactly the fixture's outputs. Without node the second part is skipped with one line `SKIP node ...` and the
gate warns (like E17). The rng widget's first case is also compared with the randomness page's worked example
(Init 12345, Range 100: 87, low 015B2E77, high 0000141D). Prints `TEST widgets: N checks, M failed`.
"""
import atexit
import json
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
WIDGETS = os.path.join(HERE, "widgets")
sys.path.insert(0, WIDGETS)
import twins  # noqa: E402
sys.path.insert(0, HERE)
import export_check as ec  # noqa: E402

checks, failed = 0, []


def node_cmd(*reads):
    """node under its permission model: it may read the widgets folder and the given scratch folders, nothing else
    (no writes, no child process, no network module use, no code from strings). A widget runs here only after its
    sources pass X13 (main), so the gate never runs a script the publish check would refuse."""
    dirs = dict.fromkeys(os.path.join(os.path.dirname(r) if os.path.isfile(r) else r, "") for r in (WIDGETS,) + reads)
    return [shutil.which("node"), "--permission"] + [f"--allow-fs-read={d}" for d in dirs] + [
        "--disallow-code-generation-from-strings"]


# one change per widget that gives another answer: the harness must see it (a mutation of the pure part)
MUTATIONS = {
    "rng": ("low % n", "(low + 1) % n"),
    "monstat": ("Math.trunc(Math.imul(a, b) / c)", "Math.trunc(Math.imul(a, b) / c) + 1"),
    "merc": ("Math.max(10, r.st + tdiv(i32(r.stl * dlt), 8))", "Math.max(10, r.st + tdiv(i32(r.stl * dlt), 4))"),
    "quality": ("tdiv(Math.imul(word, c), rule.ratioScale)", "tdiv(Math.imul(word, c), rule.ratioScale + 1)"),
    "checksum": ("((sum << 1) | (sum >>> 31)) >>> 0", "(sum << 1) >>> 0"),
}


# strings the mounted widget shows for its default inputs (the first fixture case): a value of the twin's output
MOUNT_SHOWS = {"monstat": ["268"], "merc": ["4305280", "68864"], "quality": ["28594", "1792"], "checksum": ["0007FCB4"]}


def bump_first_number(v):
    """Adds 1 to the first integer leaf of a fixture output (a wrong expected value); True when one was found."""
    items = v.items() if isinstance(v, dict) else enumerate(v) if isinstance(v, list) else ()
    for k, x in items:
        if isinstance(x, int) and not isinstance(x, bool):
            v[k] = x + 1
            return True
        if bump_first_number(x):
            return True
    return False


def ok(cond, what):
    global checks
    checks += 1
    if not cond:
        failed.append(what)
        print(f"FAIL {what}")


def node_run(folder, fixture_path=None, js_path=None):
    """-> (outputs list, error). widget.js is copied to a scratch .mjs so node reads it as a module."""
    tmp = tempfile.mkdtemp(prefix="widget-test-")
    try:
        mod = os.path.join(tmp, "widget.mjs")
        shutil.copyfile(js_path or os.path.join(folder, "widget.js"), mod)
        cmd = node_cmd(tmp, folder, fixture_path or folder) + [os.path.join(WIDGETS, "run_fixture.mjs"), mod, os.path.join(folder, "widget.json"),
               fixture_path or os.path.join(folder, "fixture.json")]
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if p.returncode:
            return None, (p.stderr.strip().splitlines() or ["node failed"])[-1][:200]
        return json.loads(p.stdout), ""
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def copy_mjs(folder):
    """widget.js copied to a scratch .mjs (a module for node); the file is removed with the interpreter's temp dir."""
    d = tempfile.mkdtemp(prefix="widget-smoke-")
    atexit.register(shutil.rmtree, d, True)
    dst = os.path.join(d, "widget.mjs")
    shutil.copyfile(os.path.join(folder, "widget.js"), dst)
    return dst


def main():
    ec.set_allow(ec.load_allow(os.path.join(HERE, "..", "docs", "export", "allow-hex.txt")))
    have_node = bool(shutil.which("node"))
    if not have_node:
        print("SKIP node: not on PATH, widget.js not run against its fixtures")
    for name in twins.widget_dirs():
        folder = os.path.join(WIDGETS, name)
        data = json.load(open(os.path.join(folder, "widget.json"), encoding="utf-8"))
        fx = os.path.join(folder, "fixture.json")
        ok(os.path.isfile(fx), f"{name}: fixture.json exists")
        if not os.path.isfile(fx):
            continue
        fixture = json.load(open(fx, encoding="utf-8"))
        ok(open(fx, encoding="utf-8").read() == json.dumps(twins.fixture(name, data), indent=1) + "\n",
           f"{name}: fixture.json is what the Python twin computes (python3 -I tools/widgets/twins.py write)")
        ok(len(fixture["cases"]) >= 5, f"{name}: the fixture has edge cases")
        if name == "rng":
            r = fixture["cases"][0]["expect"]["rows"][0]
            ok((r["result"], r["low"], r["high"]) == (87, 0x015B2E77, 0x0000141D),
               "rng: the first case is the randomness page's worked example")
            ok(any(c["inputs"]["n"] < 1 for c in fixture["cases"]), "rng: a case with n below 1 (no draw)")
        # X13 on the sources first: the gate catches a refused script at commit time, and node never runs one
        src = open(os.path.join(folder, "widget.js"), encoding="utf-8").read()
        xp = ec.js_problems(src, ec.git_identity()) + ec.json_problems(
            open(os.path.join(folder, "widget.json"), encoding="utf-8").read(), ec.git_identity())[0]
        ok(not xp, f"{name}: widget.js and widget.json pass X13 ({xp[:2]})")
        if not have_node or xp:
            continue
        outs, err = node_run(folder)
        ok(outs is not None, f"{name}: node ran widget.js ({err})")
        if outs is None:
            continue
        ok(len(outs) == len(fixture["cases"]), f"{name}: one output per case")
        for i, (got, c) in enumerate(zip(outs, fixture["cases"])):
            ok(got == c["expect"], f"{name}: case {i} {c['inputs']}: compute differs from the twin")
        # mount builds its controls with DOM calls only; a stand-in page runs it (no browser) and types into the inputs
        mjs = copy_mjs(folder)
        sm = subprocess.run(node_cmd(mjs) + [os.path.join(WIDGETS, "smoke_mount.mjs"), mjs,
                             os.path.join(folder, "widget.json")], capture_output=True, text=True, timeout=60)
        try:
            res = json.loads(sm.stdout)
        except ValueError:
            res = {}
            print("FAIL " + name + ": mount smoke test: " + ((sm.stderr.strip().splitlines() or ["no output"])[-1][:160]))
        ok(res.get("inputs", 0) >= 1 and len(res.get("rows", [])) >= 2 and bool(res.get("live")),
           f"{name}: mount builds inputs, a table and the live region")
        if name == "rng":
            ok("Init(seed)" in " ".join(res.get("rows", [])) and "00003039" in " ".join(res.get("rows", [])),
               "rng: mount shows Init(seed) and the typed seed in the table")
            ok("87" in " ".join(res.get("rows", [])) and "87" in (res.get("live") or ""),
               "rng: typing seed 12345 and range 100 shows the worked example's first draw, 87")
        for shown in MOUNT_SHOWS.get(name, []):
            ok(shown in " ".join(res.get("rows", [])) + " " + (res.get("live") or ""),
               f"{name}: mount shows {shown}, a value of the twin's first case")
        # the harness itself: a changed fixture is caught
        tmp = tempfile.mkdtemp(prefix="widget-test-")
        try:
            bad = json.loads(json.dumps(fixture))
            bump_first_number(bad["cases"][0]["expect"])
            bp = os.path.join(tmp, "fixture.json")
            json.dump(bad, open(bp, "w"))
            o2, _ = node_run(folder, fixture_path=bp)
            ok(o2 is not None and o2[0] != bad["cases"][0]["expect"], f"{name}: a wrong expected value is a difference")
            # a widget that gives another answer is caught: the multiplier changed
            js = open(os.path.join(folder, "widget.js"), encoding="utf-8").read()
            jp = os.path.join(tmp, "w.js")
            old_text, new_text = MUTATIONS[name]
            ok(old_text in js, f"{name}: the mutation's target text is in widget.js")
            open(jp, "w", encoding="utf-8").write(js.replace(old_text, new_text))
            o3, _ = node_run(folder, js_path=jp)
            open(jp, "w", encoding="utf-8").write(js.replace('return make(document.createElement("td"), text);', "return td(text);"))
            bm = subprocess.run(node_cmd(tmp) + [os.path.join(WIDGETS, "smoke_mount.mjs"), jp, os.path.join(folder, "widget.json")],
                                capture_output=True, text=True, timeout=60)
            ok(name != "rng" or bm.returncode != 0 or '"rows":[]' in bm.stdout, "rng: a mount that recurses forever is caught by the smoke test")
            ok(o3 is not None and o3 != [c["expect"] for c in fixture["cases"]], f"{name}: a changed widget.js differs")
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
    if have_node:
        # the sandbox itself: a script run as the widgets are may not start a process, write, or read outside
        for what, code in (("start a process", 'require("child_process").execSync("true")'),
                           ("write a file", 'require("fs").writeFileSync("x-widget-probe", "x")'),
                           ("read outside its folders", 'require("fs").readFileSync("/etc/hostname")'),
                           ("make code from a string", 'new Function("return 1")()')):
            p = subprocess.run(node_cmd() + ["-e", code], capture_output=True, text=True, timeout=60, cwd=WIDGETS)
            ok(p.returncode != 0, f"node sandbox: a widget run may not {what}")
    print(f"TEST widgets: {checks} checks, {len(failed)} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
