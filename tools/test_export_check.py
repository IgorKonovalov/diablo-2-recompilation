#!/usr/bin/env python3
"""Self-tests of tools/export_check.py (plan 0070 Phase 2; gate rule E20).

Usage: python3 -I tools/test_export_check.py

Runs the check on every fixture under tools/gate/fixtures/export/: `clean` and `pass-*` cuts must have no
failure; `X<n>-*` cuts must fail rule X<n>; `repo/clean` passes and `repo/X<n>-*` fail X<n>. Also: the
text-rule function on single units, the .git directory case (built at run time), and an unredacted copy of
three specs (X1, X2 and X3 must fail). Prints `TEST export_check: N checks, M failed`; exit 1 on a failure.
"""
import os
import re
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import export_check as ec  # noqa: E402

FIX = os.path.join(HERE, "gate", "fixtures", "export")
MANIFEST = os.path.join(FIX, "manifest.txt")
IDENT = ("secret-repo-name",)
checks = 0
failed = []


def ok(cond, what):
    global checks
    checks += 1
    if not cond:
        failed.append(what)
        print(f"FAIL {what}")


def rules_of(fails):
    return {f[0] for f in fails}


def main():
    for name in sorted(os.listdir(FIX)):
        d = os.path.join(FIX, name)
        if not os.path.isdir(d) or name == "repo":
            continue
        fails, _ = ec.check_cut(d, MANIFEST, IDENT)
        if name == "clean" or name.startswith("pass-"):
            ok(not fails, f"{name} passes (got {sorted(rules_of(fails))}: {fails[:2]})")
        else:
            want = name.split("-")[0]
            ok(want in rules_of(fails), f"{name} fails {want} (got {sorted(rules_of(fails))})")
    ok(os.path.isdir(os.path.join(FIX, "clean")), "clean fixture exists")
    _, warns = ec.check_cut(os.path.join(FIX, "pass-x12-warning"), MANIFEST, IDENT)
    ok(any(w[0] == "X12" for w in warns), "X12 warns on a long quoted run")
    for name in sorted(os.listdir(os.path.join(FIX, "repo"))):
        d = os.path.join(FIX, "repo", name)
        fails = ec.check_repo(d, IDENT)
        if name == "clean":
            ok(not fails, f"repo/clean passes (got {fails[:2]})")
        else:
            want = name.split("-")[0]
            ok(want in rules_of(fails), f"repo/{name} fails {want} (got {sorted(rules_of(fails))})")
    # every rule has a bad fixture
    have = {n.split("-")[0] for n in os.listdir(FIX)} | {n.split("-")[0] for n in os.listdir(os.path.join(FIX, "repo"))}
    for r in ("X1", "X2", "X3", "X4", "X5", "X6", "X7", "X8", "X9", "X10", "X11"):
        ok(r in have, f"a bad fixture exists for {r}")
    # the text-rule function on single units
    t = lambda s: ec.text_rules(s, ())
    ok(t("The game is emulated.") == set(), "emulated passes X9")
    ok(t("The attack-speed breakpoint is 9 frames.") == set(), "attack-speed breakpoint passes X9")
    ok(t("Not confirmed by a run:") == set(), "'a run:' passes X2")
    ok(t("# Game data: tables, strings and formulas") == set() and t("The raw data:") == set(),
       "'data:' in ordinary prose passes X2")
    ok("X2" in t("see data:ItemTypes"), "data:<name> anchor fails X2")
    ok("X2" in t("see run:items-0002"), "run id fails X2")
    ok("X9" in t("- Open Battle.net"), "Battle.net menu line fails X9")
    ok("X9" in t("the Warden and the CD key and copy protection"), "banned topics fail X9")
    ok("X9" in t("a logged run with gdb"), "tool names fail X9")
    ok("X1" in t("0x00556F60") and "X1" in t("sub_00556F60") and "X1" in t("Game+0x1B24"), "X1 shapes")
    ok("X3" in t("ADR-0031") and "X3" in t("findings/rng/0001") and "X3" in t("tools/gate.py"), "X3 shapes")
    ok("X4" in t("/home/x/y") and "X4" in ec.text_rules("hi secret-repo-name", IDENT), "X4 shapes")
    ok(t("Igor Konovalov, https-free github.com/IgorKonovalov") == set(), "owner name and account pass X4")
    ok("X5" in t("```\nx = f(y);\n```"), "X5 on a unit that is a fenced block")
    ok(t("```mermaid\nflowchart LR\n  A[\"x;\"] --> B{y}\n```") == set(), "mermaid fence exempt from X5")
    ok(t("```\n1. n: i32 ← tbl.Picks    ; draw#1\n2. m: u32 ← (u64) a × b\n```") == set(),
       "our pseudocode passes X5")
    ok("X5" in t("```\n(int)x\n```") and "X5" in t("```\nuVar1 = 3\n```") and "X5" in t("```\nreturn __thiscall\n```"),
       "casts, decompiler names, calling conventions fail X5")
    # narrowings and widenings of the architect review (2026-11-17)
    ok("X1" in t("DAT_00556F60") and "X1" in t("g_Table_00556F60") and "X1" in t("at 00556860"),
       "an address after `_` or bare in the image range fails X1")
    ok("X3" in t("../../docs/plans/0070-x.md") and "X3" in t("[a](../docs/specs/rng.md)"),
       "a relative docs/ path fails X3")
    ok(t("site/src/content/docs/items.md") == set(), "the export repository's content/docs/ passes X3")
    ok("X4" in t("file:///home/someone/x") and "X4" in t("x:/Users/someone/y"), "home paths fail X4 anywhere")
    ok("X9" in t("Battle-net") and "X9" in t("opened in rizin") and "X9" in t("run under wine"),
       "Battle-net and more tool names fail X9")
    # .git directory, built at run time (git can't hold one)
    tmp = tempfile.mkdtemp(prefix="export_check_")
    try:
        c = os.path.join(tmp, "cut")
        shutil.copytree(os.path.join(FIX, "clean"), c)
        os.makedirs(os.path.join(c, "site", ".git"))
        ok("X11" in rules_of(ec.check_cut(c, MANIFEST, IDENT)[0]), ".git directory fails X11 (cut)")
        r = os.path.join(tmp, "repo")
        shutil.copytree(os.path.join(FIX, "repo", "clean"), r)
        os.makedirs(os.path.join(r, ".git"))
        ok("X11" in rules_of(ec.check_repo(r, IDENT)), ".git directory fails X11 (repo)")
        # architect review 2026-11-17: text inside a schematic folder passes the text rules too
        shutil.rmtree(os.path.join(c, "site", ".git"))
        for fname, body in (("steps.json", '{"marker": "%s", "steps": [{"caption": "at 0x00556F60"}]}' % ec.MARKER),
                            ("schematic.json", None)):
            c2 = os.path.join(tmp, "cut-" + fname)
            shutil.copytree(c, c2)
            m2 = os.path.join(c2, "site", "public", "illustrations", "maze")
            sj = os.path.join(m2, "schematic.json")
            with open(sj, encoding="utf-8") as f:
                meta = ec.json.load(f)
            if body:
                with open(os.path.join(m2, fname), "w", encoding="utf-8") as f:
                    f.write(body)
                meta["files"][fname] = ec._sha(os.path.join(m2, fname))
            else:
                meta["args"] = ["--ds1", "/home/someone/workspace/game/x.ds1"]
            with open(sj, "w", encoding="utf-8") as f:
                ec.json.dump(meta, f)
            ok("X11" in rules_of(ec.check_cut(c2, MANIFEST, IDENT)[0]), f"a leak in {fname} fails X11")
        ok(not ec.check_cut(c, MANIFEST, IDENT)[0], "the clean copy still passes after .git is removed")
        # an unredacted copy of three specs fails X1, X2 and X3
        root = os.path.normpath(os.path.join(HERE, ".."))
        picks = [p for p in ("docs/specs/rng/README.md", "docs/specs/items/README.md", "docs/specs/drlg/README.md")
                 if os.path.isfile(os.path.join(root, p))]
        if len(picks) < 3:
            specs = os.path.join(root, "docs", "specs")
            for sub in sorted(os.listdir(specs)) if os.path.isdir(specs) else []:
                sd = os.path.join(specs, sub)
                for f in sorted(os.listdir(sd)) if os.path.isdir(sd) else []:
                    p = f"docs/specs/{sub}/{f}"
                    if f.endswith(".md") and p not in picks and len(picks) < 3:
                        picks.append(p)
        u = os.path.join(tmp, "unredacted")
        os.makedirs(os.path.join(u, "site", "src", "content", "docs"))
        with open(os.path.join(u, "site", "src", "cut.json"), "w") as f:
            f.write('{"date": "2026-11-17"}\n')
        for i, p in enumerate(picks):
            shutil.copy(os.path.join(root, p), os.path.join(u, "site", "src", "content", "docs", f"spec{i}.md"))
        got = rules_of(ec.check_cut(u, MANIFEST, IDENT)[0])
        ok(len(picks) == 3, f"three specs found for the unredacted run (got {len(picks)})")
        for r_ in ("X1", "X2", "X3"):
            ok(r_ in got, f"unredacted specs fail {r_} (got {sorted(got)})")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print(f"TEST export_check: {checks} checks, {len(failed)} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
