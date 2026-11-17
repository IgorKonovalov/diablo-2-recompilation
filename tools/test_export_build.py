#!/usr/bin/env python3
"""Self-tests of tools/export_build.py (plan 0070 Phase 3; gate rule E20).

Usage: python3 -I tools/test_export_build.py

Unit checks of the redactor, the simplifier and the link rewriter; the output-path refusal; the illustration run
(only `--schematic`, only the tools that have the mode, a failure is a report line); no network module; and an
end-to-end build of a small docs tree whose cut passes export_check. Prints `TEST export_build: N checks, M failed`.
"""
import os
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import export_build as eb  # noqa: E402
import export_check as ec  # noqa: E402

checks, failed = 0, []


def ok(cond, what):
    global checks
    checks += 1
    if not cond:
        failed.append(what)
        print(f"FAIL {what}")


PAGE_A = """---
title: front matter goes
---
# Alpha page

The RNG steps once per draw. [C] (fn:RNG_Step@0x0045C370, run:2026-10-11-rng-emu, [0001](../findings/rng/0001.md))
This sentence holds the address 0x00556F60 and is dropped. The seed 0xC0FFEE is illustrative.

- a clean bullet
- a bullet decoded with Ghidra
  - a child of the dropped bullet
- a lead [L] that stays out

| name | value | evidence |
|---|---|---|
| step | 1 | fn:RNG_Step@0x0045C370 |
| range | 2 | fn:RNG_Range@0x0045C390 |

```
1. x: i32 ← sub_00556F60_ItemRollQualityCreate(y)
```

```
3. bad = f(x);
```

```mermaid
flowchart LR
  A --> B
```

See [Beta](b.md#second) and [the plan](../plans/0070-x.md) and [outside](https://example.com/x).

## Gone section with sub_00556F60 in it

Nothing survives here.

## Open questions

Leads: [L] src:abc.

## Second

Text under second.

```illustration
id: no-mode
tool: site_build.py
args: 1 2
seed: illustrative
illustrates: x
caption: A caption.
```
"""
PAGE_B = "# Beta\n\n## Second\n\nBeta text, see [Alpha](a.md) and [self](#second).\n"
MANIFEST = "group g 1 Group\npage a.md - 1\npage b.md g 2\n"


def main():
    # redactor
    t, n = eb.redact_text("Steps once. [C] (fn:RNG_Step@0x0045C370, run:2026-10-11-rng-emu) Next."), 0
    ok("fn:" not in t and "[C]" in t and "Next." in t, f"evidence parenthetical dropped, tag kept ({t!r})")
    ok(eb.redact_text("Calls (see the table) twice.") == "Calls (see the table) twice.", "an ordinary parenthetical stays")
    ok(eb.redact_text("sub_00556F60_ItemRollQualityCreate runs") == "ItemRollQualityCreate runs", "sub_ prefix stripped")
    # architect review 2026-11-17: an offset-only parenthetical goes; a "See <path link>." pointer goes
    ok(eb.redact_text("Its seed (`unit+0x20`) drives the picks.") == "Its seed drives the picks.",
       "an in-memory offset parenthetical dropped")
    ok(eb.redact_text("Its seed (`unit+0x20`, the source) drives.") == "Its seed (`unit+0x20`, the source) drives.",
       "an offset parenthetical with words stays (the simplifier drops the unit)")
    t = eb.redact_text("- **Seed**: a state. See [specs/rng](specs/rng/README.md) and [findings/rng/0001](f.md).")
    ok(t == "- **Seed**: a state.", f"a See sentence of path-labelled links dropped ({t!r})")
    ok(eb.redact_text("See [the randomness page](randomness.md).") == "See [the randomness page](randomness.md).",
       "a See sentence with a worded link stays")
    ok("X3" in ec.text_rules("as in specs/items/tc", ()) and "X3" not in ec.text_rules("site/src/content/docs/x", ()),
       "a working-docs path fails X3")
    rows = eb.redact_table(["| a | b | c |", "|---|---|---|", "| x | 1 | fn:X@0x0045C370 |", "| y | 2 | data:T |"])
    ok(all(r.count("|") == 3 for r in rows), f"anchor-only column dropped ({rows})")
    rows = eb.redact_table(["| a | b |", "|---|---|", "| x | fn:X@0x0045C370 |", "| y | plain words |"])
    ok(len(rows[0].split("|")) == 4, "a column with prose cells stays")
    # path refusal and no network
    for bad in ("/tmp/x", os.path.join(eb.REPO, "docs"), os.path.join(eb.WS, "site"), os.path.join(eb.WS, "exports")):
        try:
            eb.safe_out(bad)
            ok(False, f"--out {bad} refused")
        except SystemExit:
            ok(True, "")
    ok(eb.safe_out(os.path.join(eb.WS, "export")).endswith("export"), "workspace/export accepted")
    src = open(os.path.join(HERE, "export_build.py"), encoding="utf-8").read()
    ok(not any(w in src for w in ("import socket", "urllib", "http.client", "requests", "ftplib")), "no network module")
    ok("--schematic" in src and eb.SCHEMATIC_TOOLS == ("maze_anim.py", "tc_anim.py"), "schematic tools only")
    ok(eb.tool_has_schematic("maze_anim.py") and eb.tool_has_schematic("tc_anim.py")
       and not eb.tool_has_schematic("site_build.py") and not eb.tool_has_schematic("../x.py"), "tool_has_schematic")
    # end to end on a small docs tree
    tmp = tempfile.mkdtemp(prefix="export_build_")
    out = os.path.join(eb.WS, "export-selftest")
    old_docs, old_run = eb.DOCS, eb.subprocess.run
    try:
        os.makedirs(os.path.join(tmp, "docs"))
        for name, body in (("a.md", PAGE_A), ("b.md", PAGE_B)):
            with open(os.path.join(tmp, "docs", name), "w") as f:
                f.write(body)
        with open(os.path.join(tmp, "manifest.txt"), "w") as f:
            f.write(MANIFEST)
        eb.DOCS = os.path.join(tmp, "docs")
        al = ec.Allow({0xC0FFEE: "illustrative seed"})
        ec.set_allow(al)
        calls = []

        def fake_run(cmd, **kw):
            calls.append(cmd)
            raise AssertionError("no tool may run for a tool without the mode")
        ec.git_identity()          # prime its cache: it shells out to git
        eb.subprocess.run = fake_run
        pages = eb.build(out, os.path.join(tmp, "manifest.txt"), tmp, "2026-11-17", al)
        ok(not calls, "no illustration tool ran for a tool without a schematic mode")
        a = open(os.path.join(out, "site", "src", "content", "docs", "a.md"), encoding="utf-8").read()
        b = open(os.path.join(out, "site", "src", "content", "docs", "g", "b.md"), encoding="utf-8").read()
        ok(a.startswith('---\ntitle: "Alpha page"\nsidebar:\n  order: 1\n---\n') and "# Alpha page" not in a,
           "title and sidebar.order in the front matter, the h1 removed")
        ok("front matter goes" not in a, "source front matter removed")
        ok("0x00556F60" not in a and "The seed 0xC0FFEE is illustrative." in a, "address sentence dropped, allowed seed kept")
        ok("a clean bullet" in a and "Ghidra" not in a and "child of the dropped" not in a, "bullets: failing item and its child dropped")
        ok("[L]" not in a and "Leads" not in a and "Open questions" not in a, "[L] unit and Open questions section dropped")
        ok("fn:" not in a and "| step | 1 |" in a and "evidence" not in a, "anchor column dropped, rows kept")
        ok("ItemRollQualityCreate" in a and "sub_" not in a and "f(x);" not in a, "pseudocode kept clean, decompiler-like block dropped")
        ok("```mermaid" in a, "mermaid fence kept")
        ok("[Beta](../g/b/#second)" in a and "the plan" in a and "](../plans" not in a and "example.com" not in a,
           "links: manifest page to its route with anchor, others lose their target")
        ok("Gone section" not in a and "Nothing survives" not in a, "a section with a failing heading goes whole")
        ok("[Alpha](../../a/)" in b or "[Alpha](../" in b, f"link from a nested route is relative ({b.splitlines()[-1]!r})")
        ok("[self](#second)" in b, "a same-page anchor that exists stays")
        rep = open(os.path.join(out, "report.txt"), encoding="utf-8").read()
        ok("DROP a.md" in rep and "X1" in rep and "X9" in rep and "has no schematic mode" in rep,
           "every drop is a report line with page, heading, rule and text")
        ok(os.path.isfile(os.path.join(out, "site", "src", "cut.json")) and '"label": "Group"' in
           open(os.path.join(out, "site", "src", "cut.json")).read(), "cut.json with date and groups")
        fails, _ = ec.check_cut(out, os.path.join(tmp, "manifest.txt"), ())
        ok(not fails, f"the cut passes export_check ({fails[:3]})")
        # a tool with the mode runs with --schematic, last before --out, and a failure is a report line
        calls.clear()

        def fake_fail(cmd, **kw):
            calls.append(cmd)

            class R:
                returncode, stdout, stderr = 1, "", "boom"
            return R()
        eb.subprocess.run = fake_fail
        pg = eb.Page({"path": "a.md", "route": "a", "order": 1})
        res = eb.illustration_block(pg, {"lines": ["```illustration", "id: i1", "tool: maze_anim.py", "args: 36 0xc0ffee",
                                                   "seed: illustrative", "illustrates: x", "caption: Hi.", "```"]},
                                    tmp, out, al, "H")
        ok(res == [] and calls and "--schematic" in calls[0] and calls[0].index("--schematic") < calls[0].index("--out")
           and "-I" in calls[0], "the tool runs under -I with --schematic")
        ok(any("tool failed" in d[3] for d in pg.drops), "a failed tool is a report line")

        def fake_good(cmd, **kw):
            dest = cmd[cmd.index("--out") + 1]
            os.makedirs(dest, exist_ok=True)
            for n in ("index.html", "m.gif"):
                open(os.path.join(dest, n), "w").close()

            class R:
                returncode, stdout, stderr = 0, "", ""
            return R()
        eb.subprocess.run = fake_good
        pg = eb.Page({"path": "a.md", "route": "x/y", "order": 1})
        res = eb.illustration_block(pg, {"lines": ["```illustration", "id: i2", "tool: maze_anim.py", "args: 36 0xc0ffee",
                                                   "seed: illustrative", "illustrates: x", "caption: Hi.", "```"]},
                                    tmp, out, al, "H")
        txt = "\n".join(l for b in res for l in b["lines"])
        ok("![Animation: i2](/illustrations/i2/m.gif)" in txt and "[Step through i2](../../illustrations/i2/index.html)" in txt,
           "the GIF is an inline image with a root-absolute target, plus the step-through link")
        ok(not ec.check_page(txt, "x/y.md", "x/y", 0, {("i2", "m.gif")}, ())
           and "X8" in {h[0] for h in ec.check_page(txt, "x/y.md", "x/y", 0, set(), ())}, "X8 accepts it only for a verified folder")
        shutil.rmtree(os.path.join(out, "site", "public", "illustrations"), ignore_errors=True)
    finally:
        eb.DOCS, eb.subprocess.run = old_docs, old_run
        ec.set_allow(None)
        shutil.rmtree(tmp, ignore_errors=True)
        shutil.rmtree(out, ignore_errors=True)
    print(f"TEST export_build: {checks} checks, {len(failed)} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
