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
    ok("X1" in t("0x00556F60") and "X1" in t("sub_00556F60") and "X1" in t("Game+0x00401B24") and "X1" in t("DAT_foo+0x1B"), "X1 shapes")
    # owner decision 2026-11-17: an in-memory struct offset passes, a code-image value in any spelling still fails
    ok(t("ItemData+0x10 and Unit+0x10+0x4 and `+0x1C` and U+0xC4") == set(), "X1: a struct offset, a chain and a bare offset pass")
    ok("X1" in t("0x0063xxxx") and "X1" in t("see 0x0063XXXX") and "X1" in t("0x006Axxxx")
       and "X1" in t("outside `0x4xxxxx` pass") and "X1" in t("0x006XXXXX"), "X1: a partial address fails")
    ok(t("0x1xxxxx and 0x0xx and 0xFFxx") == set(), "X1: a partial value outside the image's prefixes passes")
    ok("X1" in t("0x00401B24") and "X1" in t("00401B24") and "X1" in t("at 5E9F10 here") and "X1" in t("@0x00556F60"),
       "X1: a code-image value fails in every spelling (offsets admitted notwithstanding)")
    ok("X3" in t("see run.log") and "X3" in t("the file tc.log here") and "X3" in t("under .claude/skills") and "X3" in t("`.claude`"),
       "X3: a .log name and a .claude path fail")
    ok(t("console.log(x) in the site script") == set() and "X3" in t("console.log(x) and run.log"), "X3: JS console.log is no file name, the .log beside it fails")
    ok(t("the blog or a log of it, catalog.") == set(), "X3: ordinary words with log in them pass")
    ok("X3" in t("ADR-0031") and "X3" in t("findings/rng/0001") and "X3" in t("tools/gate.py"), "X3 shapes")
    ok("X4" in t("/home/x/y") and "X4" in ec.text_rules("hi secret-repo-name", IDENT), "X4 shapes")
    def urlok(u):
        return bool(ec.RE_URL_ALLOW.match(u.lower()))
    ok(all(urlok(u) for u in ("https://github.com/igorkonovalov/arpg-1-14d-notes", "https://github.com/IgorKonovalov/arpg-1-14d-notes/",
                              "https://github.com/IgorKonovalov/ARPG-1-14d-notes.git", "https://github.com/igorkonovalov/arpg-1-14d-notes#x",
                              "https://igorkonovalov.github.io/arpg-1-14d-notes/a/b", "https://IgorKonovalov.github.io/arpg-1-14d-notes",
                              "https://igorkonovalov.github.io")), "X7: the export repository and its site pass")
    ok(not any(urlok(u) for u in ("https://github.com/igorkonovalov", "https://github.com/igorkonovalov/other",
                                  "https://github.com/igorkonovalov/arpg-1-14d-notes-old", "https://github.com/igorkonovalov/arpg-1-14d-notes2/x",
                                  "https://igorkonovalov.github.io/arpg-1-14d-notes-old/", "https://igorkonovalov.github.io/other/",
                                  "https://github.com/other/arpg-1-14d-notes")), "X7: other repositories and extended names fail")
    ok(t("Igor Konovalov, https-free github.com/IgorKonovalov") == set(), "owner name and account pass X4")
    ok("X5" in t("```\nx = f(y);\n```"), "X5 on a unit that is a fenced block")
    ok(t("```mermaid\nflowchart LR\n  A[\"x;\"] --> B{y}\n```") == set(), "mermaid fence exempt from X5")
    ok(t("```\n1. n: i32 ← tbl.Picks    ; draw#1\n2. m: u32 ← (u64) a × b\n```") == set(),
       "our pseudocode passes X5")
    ok(t("```\n1. S ← {a, b}\n2. {hi:lo} ← draw           ; (unsigned) and (int32) notes\n   x ← (unsigned) a ÷ b\n```") == set(),
       "X5: set braces and integer-semantics notes pass")
    ok("X5" in t("```\nif (x) {\n  y;\n}\n```") and "X5" in t("```\n(DWORD *)p\n```") and "X5" in t("```\nx = (int)y\n```")
       and "X5" in t("```\n} else\n```"), "X5: C braces and glued casts still fail")
    ok(t("```\nif v14 = 0: Place(3, 3, 629, 0);\n  else: load File(i + 1) into ps[+0x0C];\n  if n < k: goto next\n```") == set(),
       "X5: our `;` separators, `=` as equality and `goto next` pass")
    ok("X5" in t("```\nx = f(y);\n```") and "X5" in t("```\nint n = 3;\n```") and "X5" in t("```\nif (a == b) c;\n```")
       and "X5" in t("```\ngoto LAB_00401000\n```") and "X5" in t("```\np->x\n```") and "X5" in t("```\n*(int *)p\n```")
       and t("```\n1. x ← a *(b + c)\n```") == set(), "X5: C statements, LAB_ and -> still fail")
    ok("X5" in t("```\n(int)x\n```") and "X5" in t("```\nuVar1 = 3\n```") and "X5" in t("```\nreturn __thiscall\n```"),
       "casts, decompiler names, calling conventions fail X5")
    # review of lane/x70b2: C-shaped lines the narrowed X5 let through
    for c in ("x += 3;", "x |= 0x10;", "foo(a, b);", "return x;", "unsigned int x = 5;", "struct Unit *p = q;",
              "x = 1; // c", "if (x) { y = 1; }", "DWORD dw;", "--i;", "(*p).x = 1;"):
        ok("X5" in t("```\n" + c + "\n```"), "X5 still fails " + c)
    for c in ("p.flags &= ~8", "r.init(game, unit, &blk)     ; blk laid out as an AiCtx: ctl, MonStats;",
              "type Seed { low: u32; high: u32 }", "F(x): for n ≥ 41 the fatal path (pushed before the call);"):
        ok(t("```\n" + c + "\n```") == set(), "X5 passes our pseudocode " + c)
    # other spellings of an image address, and offsets from the image
    for c in ("0X004A1B20", "0X4A1B20", "4A1B20h", "0x0045_1B20", "Game.exe+0x5C00", "image base + 0x1A2B3", "`D2Common.dll+0x1234`",
              "0x0063????"):
        ok("X1" in t(c), "X1 fails " + c)
    ok(t("`Game+0x10F4`, `base +0x114`, flag 0x40000? or 0x66?") == set(), "X1 passes a struct named Game, base, a flag in a question")
    # narrowings and widenings of the architect review (2026-11-17)
    ok("X1" in t("DAT_00556F60") and "X1" in t("g_Table_00556F60") and "X1" in t("at 00556860"),
       "an address after `_` or bare in the image range fails X1")
    ok("X3" in t("../../docs/plans/0070-x.md") and "X3" in t("[a](../docs/specs/rng.md)"),
       "a relative docs/ path fails X3")
    ok(t("site/src/content/docs/items.md") == set(), "the export repository's content/docs/ passes X3")
    ok("X4" in t("file:///home/someone/x") and "X4" in t("x:/Users/someone/y"), "home paths fail X4 anywhere")
    ok("X9" in t("Battle-net") and "X9" in t("opened in rizin") and "X9" in t("run under wine"),
       "Battle-net and more tool names fail X9")
    # Phase 9 review: objdump, debugger, and r2 as the tool fail X9; r2 as a variable passes
    for c in ("an objdump walk finds 13 calls", "written by a debugger", "by objdump and r2 alike", "read with r2 beside",
              "Python and r2 agree", "r2 reads the third push", "agreeing with r2's, 852 each", "read by r2.", "both item loggers", "the two harnesses", "read from the image and by r2: entries 43",
              "r2 and objdump equal"):
        ok("X9" in t(c), "X9 fails " + c)
    for c in ("r2 \u2190 aip(5)", "r1 and r2 are the two draws", "the sum of r1 and r2", "with r2 \u2190 0", "q \u2190 x \u00f7 r2",
              "r2 = Range(seed, 4)"):
        ok("X9" not in t(c), "X9 passes the variable in " + c)
    # Phase 9 review: a bare identifier mixing letter cases is a name (`deadD2`), unless its value is in the image
    ok("X1" not in t("s.dead and deadD2 0 here") and "X1" not in t("deadD2 is a squared distance"),
       "a mixed-case identifier passes X1")
    ok("X1" in t("deaddd2 is hex") and "X1" in t("bad 5e8A4b here"), "a one-case run and an image value in mixed case fail X1")
    # the hex allowance (owner decision 2026-11-17): listed game math passes, the same value elsewhere fails,
    # an image-range entry is refused, and the scoped rule for a schematic folder's draw shapes
    al = ec.Allow({0xC0FFEE: "illustrative seed", 0x6AC690C5: "the RNG multiplier"})
    ta = lambda s, **k: ec.check_text(s, (), allow=al, **k)
    ok(ta("seed 0xc0ffee and 6AC690C5") == [], "an allowed seed and the multiplier pass X1")
    ok(any(h[0] == "X1" for h in ec.check_text("seed 0xc0ffee", ())) and ec.check_text("seed 0xc0ffee", (), allow=ec.Allow()),
       "the same value fails without the allowlist")
    ok(any(h[0] == "X1" for h in ta("the seed 0xdeadbeef")), "a value off the allowlist fails")
    ok(any(h[0] == "X3" for h in ec.check_text("seed 00c0ffee", (), allow=ec.Allow())), "commit-hash shape fails off the list")
    ok(ta("seed 00c0ffee") == [], "an allowed value passes X3 too, in any spelling")
    ok(any(h[0] == "X1" for h in ta("DAT_00c0ffee")) and any(h[0] == "X1" for h in ta("x+0xc0ffee")),
       "an allowed value after `_` or `+` still fails")
    ok(any(h[0] == "X1" for h in ta("at 0x00556F60")) and any(h[0] == "X1" for h in ta("sub_00556F60")),
       "image-range addresses fail with an allowlist present")
    bad = os.path.join(tempfile.mkdtemp(prefix="export_allow_"), "allow.txt")
    for line in ("0x00556F60 an address\n", "00507fab seed that looks like one\n", "c0ffee\n",
                 "0096D66C a .data address\n", "pin 0x00405450 wiki/x.md :: a named address\n",
                 "pin 0090CE87 wiki/x.md\n"):
        with open(bad, "w") as f:
            f.write(line)
        try:
            ec.load_allow(bad)
            ok(False, f"load_allow refuses {line.strip()!r}")
        except ValueError:
            ok(True, "")
    with open(bad, "w") as f:
        f.write("# c\n0xC0FFEE illustrative seed\n6ac690c5 the RNG multiplier\n")
    ok(set(ec.load_allow(bad).values) == {0xC0FFEE, 0x6AC690C5}, "load_allow reads a good file")
    shutil.rmtree(os.path.dirname(bad), ignore_errors=True)
    real = os.path.join(HERE, "..", "docs", "export", "allow-hex.txt")
    if os.path.isfile(real):
        ra = ec.load_allow(real)
        ok(len(ra.values) > 0 and not any(ec.in_image(v) for v in ra.values),
           "docs/export/allow-hex.txt loads (no image-range value entry)")
        ok(all(ec.in_image(v) for d in ra.pins.values() for v in d), "every pin is an image-range value (else a value entry)")
    sc = lambda s: ec.check_text(s, (), allow=ec.Allow(), scoped=True)
    ok(sc("draw lo = 0x7f8b96aa; seed after {ceb6f65b:3ac5bf6e}; {start, 666} = {6bf39f86, 666}") == [],
       "scoped: the draw shapes pass")
    ok(sc("seed {a28ed4c0:00507fab}; {00507fab, 666}") == [], "scoped: a draw value in the image range passes in a brace seed state")
    ok(any(h[0] == "X1" for h in sc("lo = 0x00507fab")) and any(h[0] == "X1" for h in sc("seed 0x0096d66c")),
       "scoped: an image-range value in a `lo =` or `seed` shape fails")
    ok("X2" in ec.text_rules("a lead. [L]", ()) and "X2" not in ec.text_rules("[C] and [I]", ()), "an [L] tag fails X2")
    # the image range is the whole mapped image, .data/.bss included (architect review 2026-11-17)
    ok(any(h[0] == "X1" for h in ec.check_text("at 0x0096D66C", (), allow=ec.Allow(), sect=True))
       and any(h[0] == "X1" for h in ec.check_text("at 00912345", (), allow=ec.Allow())),
       "a .data address (0x0096D66C) fails in a section; a bare all-digit 009xxxxx fails")
    # sections: any non-image hex passes under the heading, image-range values and names do not
    sa = ec.Allow(sections={("wiki/x.md", "A worked example"): "illustrative"})
    page = ("# T\n\n## A worked example: seed 12345\n\nlow `015B2E77`, high `0000141D`.\n\n### Step\n\n"
            "`8B57C5B0`\n\n## Next\n\nlow `015B2E77`.\n")
    sl = ec.section_lines(page, "wiki/x.md", sa)
    hits = ec.check_text(page, (), allow=sa, sect_lines=sl)
    ok([h[1] for h in hits] == [13], f"a section admits its hex, subsections included, and ends at its level: {hits}")
    ok(any(h[0] == "X1" for h in ec.check_text("`0090CE87` and sub_0090CE87 and x+0x1B24", (), allow=sa, sect=True)),
       "a section does not admit an image-range value or a sub_ name")
    ok(ec.section_lines(page, "wiki/y.md", sa) == set(), "a section entry admits nothing on another page")
    # pins: one image-range value, one page
    ok(ec.check_text("`0090CE87`", (), allow=sa, sect=True, pins={0x0090CE87: "r"}) == []
       and any(h[0] == "X1" for h in ec.check_text("`0090CE88`", (), allow=sa, sect=True, pins={0x0090CE87: "r"}))
       and any(h[0] == "X1" for h in ec.check_text("sub_0090CE87", (), allow=sa, pins={0x0090CE87: "r"})),
       "a pin admits its value only; never as a sub_ name")
    ok(any(h[0] == "X1" for h in sc("see 0x00556F60")) and any(h[0] == "X1" for h in sc("the sub_00556F60 call")),
       "scoped: an address outside a draw shape fails")
    ok(any(h[0] == "X1" for h in ec.check_text("lo = 0x7f8b96aa", (), allow=ec.Allow())),
       "the draw shapes pass only in a schematic folder (unscoped fails)")
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
        shutil.rmtree(os.path.join(r, ".git"))
        os.makedirs(os.path.join(r, "site", "public"))
        fav = os.path.join(r, "site", "public", "favicon.svg")
        good = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32"><rect width="32" height="32" '
                'fill="#3a3f58"/><path d="M8 8h16v16H8z" stroke="#e8e4d8"/></svg>\n')
        for body, want, what in (
                (good, False, "our own plain favicon passes (repo)"),
                (good.replace("<path", '<image href="x.png"/><path'), True, "a favicon embedding an image fails X8"),
                (good.replace("</svg>", "<script>1</script></svg>"), True, "a favicon with a script fails X8"),
                (good.replace('viewBox', 'onload="x()" viewBox'), True, "a favicon with an event handler fails X8"),
                (good.replace("<path", '<text>0x00556F60</text><path'), True, "a favicon with text elements fails X8")):
            with open(fav, "w", encoding="ascii") as f:
                f.write(body)
            ok(("X8" in rules_of(ec.check_repo(r, IDENT))) == want, what)
        os.remove(fav)
        with open(os.path.join(r, "site", "public", "logo.svg"), "w", encoding="ascii") as f:
            f.write(good)
        ok({"X8", "X11"} <= rules_of(ec.check_repo(r, IDENT)), "any other image file in the repo still fails X8 and X11")
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
        for label, line, want in (("draw", "Pick: level draw lo = 0x2f8cad61; seed after {ceb6f65b:3ac5bf6e}.", True),
                                  ("address", "Pick: see 0x00556F60.", False)):
            c3 = os.path.join(tmp, "cut-" + label)
            shutil.copytree(c, c3)
            m3 = os.path.join(c3, "site", "public", "illustrations", "maze")
            with open(os.path.join(m3, "steps.json"), "w", encoding="utf-8") as f:
                f.write('{"marker": "%s", "steps": [{"caption": "%s"}]}' % (ec.MARKER, line))
            with open(os.path.join(m3, "schematic.json"), encoding="utf-8") as f:
                meta = ec.json.load(f)
            meta["files"]["steps.json"] = ec._sha(os.path.join(m3, "steps.json"))
            with open(os.path.join(m3, "schematic.json"), "w", encoding="utf-8") as f:
                ec.json.dump(meta, f)
            ec.set_allow(None)
            ok(bool(not ec.check_cut(c3, MANIFEST, IDENT)[0]) == want, f"calc-panel {label} line in a folder: pass={want}")
        ok(not ec.check_cut(c, MANIFEST, IDENT)[0], "the clean copy still passes after .git is removed")
        # neutral marker: no project name; a tool key in schematic.json is refused; X8 takes the root-absolute target only
        ok("d2recon" not in ec.MARKER, "the marker carries no project name")
        c4 = os.path.join(tmp, "cut-tool")
        shutil.copytree(c, c4)
        sj4 = os.path.join(c4, "site", "public", "illustrations", "maze", "schematic.json")
        with open(sj4, encoding="utf-8") as f:
            meta = ec.json.load(f)
        meta["tool"] = "maze_anim"
        with open(sj4, "w", encoding="utf-8") as f:
            ec.json.dump(meta, f)
        ok("X11" in rules_of(ec.check_cut(c4, MANIFEST, IDENT)[0]), "a tool key in schematic.json fails X11")
        ill = {("maze", "maze.gif")}
        chk = lambda tgt: [h[0] for h in ec.check_page(f"![a]({tgt})\n", "i.md", "index", 0, ill, IDENT)]
        ok(chk("/illustrations/maze/maze.gif") == [], "X8 accepts /illustrations/<id>/<file> of a verified folder")
        ok("X8" in chk("../illustrations/maze/maze.gif") and "X8" in chk("/illustrations/maze/other.gif")
           and "X8" in chk("/other/illustrations/maze/maze.gif"), "X8 refuses a relative, unlisted or elsewhere target")
        # X4 skips only a `](/illustrations/<id>/<file>)` target: not prose, not a dot segment
        ok(all("X4" in {h[0] for h in ec.check_text(t)} for t in ("see (/illustrations/igor/x)", "/illustrations/a/b",
                                                                     "![a](/illustrations/../home)", "![a](/illustrations/m/../x)")),
           "X4 still fails a bare, parenthesised or dot-segment /illustrations/ path")
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
    # the step page's URL rule: a scheme starts at a word boundary (review of lane/x11a)
    for txt in ("draws: 3", "Tomb pairs: 2", "news: none", "<li>two draws: 87, 64</li>"):
        ok("external URL" not in ec.html_problems(txt, set()), f"html_problems passes text {txt!r}")
    for txt in ("ws://x", "wss://x", " ws:x", "see WS:x", "(https://x.y)", "ftp:x", "//cdn.example.com/a.js"):
        ok("external URL" in ec.html_problems(txt, set()), f"html_problems fails URL {txt!r}")
    print(f"TEST export_check: {checks} checks, {len(failed)} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
