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
PAGE_B = ("# Beta\n\n## Second\n\nBeta text, see [Alpha](a.md) and [self](#second).\n\n"
          "Read [how we know](method.md#tags) and [hidden](hidden.md).\n")
MANIFEST = "group g 1 Group\npage a.md - 1\npage b.md g 2\nalias method.md a.md\n"


def main():
    # redactor
    t, n = eb.redact_text("Steps once. [C] (fn:RNG_Step@0x0045C370, run:2026-10-11-rng-emu) Next."), 0
    ok("fn:" not in t and "[C]" in t and "Next." in t, f"evidence parenthetical dropped, tag kept ({t!r})")
    ok(eb.redact_text("Calls (see the table) twice.") == "Calls (see the table) twice.", "an ordinary parenthetical stays")
    ok(eb.redact_text("sub_00556F60_ItemRollQualityCreate runs") == "ItemRollQualityCreate runs", "sub_ prefix stripped")
    # architect review 2026-11-17: an offset-only parenthetical goes; a "See <path link>." pointer goes
    ok(eb.redact_text("Its seed (`unit+0x20`) drives the picks.") == "Its seed (`unit+0x20`) drives the picks.",
       "an in-memory offset parenthetical is content now (owner decision 2026-11-17)")
    ok(eb.redact_text("Its seed (`unit+0x20`, fn:Foo@0x0045ABCD) drives.") == "Its seed (`unit+0x20`, fn:Foo@0x0045ABCD) drives.",
       "a parenthetical with an offset is not evidence-only")
    ok(eb.redact_text("Its seed (`unit+0x20`, the source) drives.") == "Its seed (`unit+0x20`, the source) drives.",
       "an offset parenthetical with words stays (the simplifier drops the unit)")
    ok(eb.redact_text("it is confirmed\n([spec](../specs/rng/README.md#notes)):\n") == "it is confirmed:\n",
       "a dropped parenthetical on its own line takes its punctuation back")
    ok(eb.redact_text("it is read\n(fn:X@0x0045C370) and then\nmore.") == "it is read\n and then\nmore.",
       "a dropped parenthetical before a word keeps the line break")
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
    # Phase 9 review: a tag's evidence parenthetical that fails a text rule goes whole; one that passes stays
    t = eb.redact_text("It drops. [C] (r2's pushes, the 20 search sites) Next.")
    ok("r2" not in t and "[C]" in t and "Next." in t, f"a failing parenthetical after a tag goes ({t!r})")
    ok(eb.redact_text("It drops. [C] (all 1607 rows) Next.") == "It drops. [C] (all 1607 rows) Next.",
       "a passing parenthetical after a tag stays")
    ok(eb.redact_text("It drops (read with objdump) here.") == "It drops (read with objdump) here.",
       "a failing parenthetical not after a tag stays (the simplifier drops the unit)")
    ok(eb.rewrite_row("| step | [C] read with objdump beside the reading |") == "| step | [C] |"
       and eb.rewrite_row("| step | [C] 26 574 returns |") == "| step | [C] 26 574 returns |",
       "a cell that opens with its tag keeps the tag alone when the rest fails a rule")
    # anchor rewrite (Phase 9 prerequisite)
    rt = eb.rewrite_text
    ok(rt("It calls fn:Foo@0x0045ABCD twice.") == "It calls `Foo` twice.", "fn:Name@0x becomes `Name`")
    ok(rt("It calls `fn:Foo@0x0045ABCD` twice.") == "It calls `Foo` twice.", "an anchor already in backticks is not doubled")
    ok(rt("Reads data:g_Table@0x0070A000 and tbl:Skills.txt:minmana, fmt:DT1 and tbl:Levels.") ==
       "Reads `g_Table` and `Skills.txt:minmana`, `DT1` and `Levels`.", "data:, tbl:, fmt: anchors, with a column")
    ok(rt("It calls fn:sub_00456789_Foo@0x00456789 here.") == "It calls here.", "a sub_ name is removed whole")
    ok(rt("Read data:DAT_00556F60@0x00556F60 here.") == "Read here.", "a DAT_ name is removed whole")
    ok(rt("Call fn:Cafe00Bad@0x0045ABCD again.") == "Call again.", "a name holding a hex run of 6+ digits is removed")
    # an in-memory offset is content (owner decision 2026-11-17): a struct anchor becomes its offset (review of lane/x70b2)
    ok(rt("The field struct:Unit+0x20 holds it.") == "The field `Unit+0x20` holds it.", "a struct: anchor becomes its offset")
    ok(rt("The field `struct:Unit+0x20` holds it.") == "The field `Unit+0x20` holds it.", "a backticked struct: anchor too")
    ok("0045ABCD" not in rt("The field struct:Unit+0x0045ABCD holds it.") and "DAT_" not in rt("A struct:DAT_00556F60+0x4 b."),
       "a struct: anchor with an image-shaped offset or a code name never stays")
    ok(rt("Seen in run:2026-10-11-rng-emu and src:arreat-summit.") == "Seen.", "run: and src: ids removed, dangling and/in go")
    ok(rt("Listed A, items/0012-slug#x, B.") == "Listed A, B." and rt("Read items/0012 now.") == "Read now.",
       "a finding id is removed")
    ok(rt("It holds (items/0012, run:2026-10-11-a) here.") == "It holds here.", "an emptied parenthetical goes")
    ok(rt("It holds (see run:2026-10-11-a) here.") == "It holds here.", "a parenthetical left with only 'see' goes")
    ok(rt("Checked at run:2026-10-11-a.") == "Checked.", "a dangling 'at' goes")
    ok(rt("Listed A, run:2026-10-11-a, B.") == "Listed A, B.", "an emptied list slot leaves no doubled comma")
    ok(rt("Read [the finding](../findings/rng/0001.md) first.") == "Read first.", "a link into findings/ goes whole")
    ok(rt("Read [the page](a.md) and [fn:Foo@0x0045ABCD](b.md).") == "Read [the page](a.md) and [`Foo`](b.md).",
       "other links stay, their labels are rewritten")
    ok(rt("Plain text, no anchors (a, b).") == "Plain text, no anchors (a, b).", "an unchanged unit is unchanged")
    ok("X1" in eb.unit_fails(rt("The call at 0x1234567890 and fn:Foo@0x0045ABCD."), ec.Allow()),
       "a unit that still carries a 6+ hex after the rewrite still fails (and is dropped)")
    # spec citations
    ok(rt("as in drlg/maze.md § 3 here") == "as in maze.md § 3 here", "folder + .md with a section is reduced to the file name")
    ok(rt("as in `drlg/maze.md` § 3 here") == "as in `maze.md` § 3 here", "a backticked citation keeps its backticks")
    ok(rt("as in maze.md § 3 here") == "as in maze.md § 3 here", "file.md § X passes")
    ok(rt("as in drlg/maze and rng/seeds") == "as in drlg/maze and rng/seeds", "bare subsystem names pass")
    ok(rt("Details: spec drlg/README.md.") == eb.BROKEN, "a folder path .md with no section is removed, 'spec' too; "
       "a label left with nothing after its colon is broken")
    ok(rt("Read it, see spec drlg/README.md.") == "Read it.", "a folder path .md with no section is removed, 'spec' too")
    # review of lane/x70a: a working-tree citation is never reduced to its file name
    for c in ("findings/items/0012-x.md", "../plans/0070-redacted-public-export.md", "docs/adrs/0031-constants.md",
              "`findings/rng/0001.md`", "findings/drlg/experiments.md", "docs/backlog/2026-11-17-foo.md",
              ".claude/skills/archivist/references/review-fixes.md"):
        r = rt("see " + c + " § 3 here")
        ok(r == eb.BROKEN, f"a working-tree citation with a section drops the unit ({r!r})")
    ok(rt("see 0012-slug.md § 3 here") == "see 0012-slug.md § 3 here", "no folder, no rewrite")
    ok(rt("per tables/Levels.md § Columns") == "per Levels.md § Columns", "a table doc citation is reduced")
    # review of lane/x70a: a removed token the unit can't read without drops the unit
    ok(rt("- [findings/data/0002-x.md § 4](../../findings/data/0002-x.md#4): the language byte.") == eb.BROKEN,
       "an item whose head before the colon went is broken")
    ok(rt("- Findings: [a/0001](../../findings/a/0001.md), [a/0002](../../findings/a/0002.md).") == eb.BROKEN,
       "a label whose whole list went is broken")
    ok(rt("It takes [the finding](../findings/x/0001.md)'s reading.") == eb.BROKEN, "a removed possessive is broken")
    ok(rt("no build of run:2026-10-15-vendors passed 20 failures") == eb.BROKEN,
       "a removed object of a preposition with words after it is broken")
    ok(rt("It is passed to fn:sub_0045ABCD_X@0x0045ABCD.") == eb.BROKEN, "'to' before a removed token is broken")
    ok(rt("All from kept logs of run:2026-10-20-chain, each reproduced.") == "All from kept logs, each reproduced.",
       "a dangling 'of' before punctuation goes with the token")
    ok(rt("fn:sub_0045ABCD_X@0x0045ABCD, the 1 330 kept logs") == "the 1 330 kept logs",
       "a list whose first slot went loses the leading comma")
    ok(eb.rewrite_row("| a | fn:sub_0045ABCD_X@0x0045ABCD: the call | 2 |") == "| a | — | 2 |", "a broken cell is an em dash")
    ok(eb.rewrite_row("| a | fn:sub_0045ABCD_X@0x0045ABCD → fn:sub_0045ABCE_Y@0x0045ABCE | 2 |") == "| a | — | 2 |",
       "a cell left with arrows only is an em dash")
    # review of lane/x70b2: a statement cell the rewrite breaks drops its row, it never reads as "none"
    ok(eb.rewrite_row("| Q80 | The collision test `0x0064FF90`'s result per crossed subtile | 2 |") == eb.BROKEN,
       "a broken statement cell breaks the row")
    ok(eb.rewrite_row("| a | 10 000 | fn:PLAYER_GoldCap@0x00622E70, run:2026-10-17-e (the cap reached at L 30, "
                      "[x § 1](../../findings/items/experiments.md#x)) |") == "| a | 10 000 | — |",
       "a broken evidence cell (opening with its anchor) is still a dash")
    ok(eb.rewrite_row("| a | The test `0x0064FF90`'s result per subtile | x |", row_breaks=False) == "| a | — | x |",
       "a header row never breaks")
    ok(rt("[C] (run:2026-10-18-quests2: x-talk2)") == "[C] (x-talk2)", "a run id before a colon in a parenthetical goes with it")
    ok(rt("[C] run:2026-11-03-path-emu-2, 994 022 draws") == "[C] 994 022 draws", "no comma left after a tag")
    ok(rt("**It rebuilds nothing.** In run:2026-10-27-sweep-vendors, 7 opens found it.") ==
       "**It rebuilds nothing.** 7 opens found it.", "a dangling 'In' at a sentence's start goes with its comma")
    ok(rt("All rows: [a/0005 § 6](../../findings/a/0005.md); the run-time rows.") == eb.BROKEN,
       "a label whose list went, before a semicolon, is broken")
    ok(rt("each a section: [S2b](../../findings/i/0005.md#s2b) (full-table reads), [S2c](../../findings/i/0005.md#s2c) (vendors)")
       == eb.BROKEN, "a parenthetical that glossed a removed token is broken")
    ok(rt("- Runs: [run:2026-10-17-e](../../findings/i/experiments.md#r): 33 logs.") == eb.BROKEN, "a label's colon before a removed head is broken")
    ok(rt("For quests this is [save/0002](../../findings/save/0002.md); for the NPC") == eb.BROKEN, "a removed complement of 'is' is broken")
    ok(rt("Details (README.md) here.") == "Details here.", "a README name with no section is removed")
    ok(rt("Details in README.md § 2 here.") == "Details in README.md § 2 here.", "README.md § X passes")
    ok(rt("Details [x](../specs/drlg/maze.md) here.") == "Details [x](../specs/drlg/maze.md) here.", "a link target is not a citation")
    # Phase 9 second round (plan 0070): code-image addresses, plan/ADR/lane references, repository paths and file names
    ok(rt("It reads the row from 0x00556F60, then loops.") == "It reads the row, then loops.", "an address with its 'from' goes")
    ok(rt("Called at 0x00556F60.") == "Called.", "'at' goes with a trailing address")
    ok(rt("Called at 0x00556F60 and 00556F64, run it.") == "Called, run it.", "an address pair, 0x and bare 8-digit, goes")
    ok(rt("The block `0x005E9F10\u20130x005EA078` ends.") == "The block ends." and rt("The block `0x005E9F10` ends.") == "The block ends.",
       "a backticked address or range goes")
    ok(rt("Range 0x005E9F10\u20130x005EA078 is checked, then.") == "Range is checked, then.", "an address range goes as one token")
    ok(rt("The 0x005E9F10 handler runs.") == eb.BROKEN, "an address after a determiner is broken")
    ok(rt("0x005E9F10 reads the table.") == eb.BROKEN, "a removed subject is broken")
    ok(rt("0x005E9F10 = the handler.") == eb.BROKEN and rt("x is 0x005E9F10 \u2013 the handler.") == eb.BROKEN,
       "a token before = or a dash is broken")
    ok(rt("The prefix 0x0063xxxx is a handler.") == "The prefix is a handler." and rt("Prefix 0x006XXXXX here.") == "Prefix here." and rt("Calls outside `0x4xxxxx` pass a set.") == eb.BROKEN, "a partial address goes")
    ok(rt("the value 5E9F10 and 500000 and 0x400000 end.") == "the value and 500000 and end.",
       "a bare 6-digit hex in the image range goes, a decimal number stays")
    ok(rt("the seed 0xC0FFEE and 12 345 and 0x20000 stay.") == "the seed 0xC0FFEE and 12 345 and 0x20000 stay.",
       "a value out of the image range is not an address")
    eb.PAGE_PINS = {0x0090CE87: "r"}
    try:
        ok(rt("the high word 0090CE87 and 0x0090CE88 here.") == "the high word 0090CE87 and here.",
           "a pinned value stays, another image-range value goes")
    finally:
        eb.PAGE_PINS = {}
    ok(rt("Its field `ItemData+0x10` and Game+0x6A+0x4 stay.") == "Its field `ItemData+0x10` and Game+0x6A+0x4 stay.",
       "a struct offset and a chain stay (owner decision 2026-11-17)")
    ok(rt("Done (plan 0038 Phase 2b) and more.") == "Done and more.", "a plan reference in a parenthetical goes with it")
    ok(rt("Per ADR-0014 the time is in frames.") == eb.BROKEN and rt("Time is in frames, per ADR-0014.") == "Time is in frames.",
       "an ADR reference goes (the unit drops when it was the object)")
    ok("ADR" not in rt("Time is in frames (ADR-0014, ADR-0029 \u00a7 2).") and "lane" not in rt("Fixed by lane/x70a in review."),
       "ADR and lane references go")
    ok(rt("Run `tools/tc.py check` to see.") == eb.BROKEN, "a run-the-tool clause is broken")
    ok(rt("The check (tc.py, cube.csv, run.log) is ours.") == "The check is ours." and rt("The files are tc.py and run.log.") == eb.BROKEN,
       "file names go")
    ok(rt("It is ours (re/symbols.csv, .claude/skills/x).") == "It is ours." and ".claude" not in rt("Ours, .claude/skills/x too."),
       "repository paths go")
    ok(rt("The model, in `tools/x.py`, does it.") == "The model, does it.", "a backticked repository path goes whole")
    ok(eb.rewrite_row("| a | 0x00555DDF | 2 |") == "| a | \u2014 | 2 |" and
       eb.rewrite_row("| a | 0x00555DDF, 0x00555DE0 | 2 |") == "| a | \u2014 | 2 |" and
       eb.rewrite_row("| a | `0x00555DDF`\u20130x00555E00 | 2 |") == "| a | \u2014 | 2 |", "a cell made only of addresses is an em dash")
    ok(eb.rewrite_row("| a | `+0x1C` | b |") == "| a | `+0x1C` | b |", "an offset cell stays")
    ok(not eb.is_evidence_cell("`+0x1C`") and eb.redact_table(["| a | b |", "|---|---|", "| x | `+0x10` |", "| y | `+0x14` |"])[2] == "| x | `+0x10` |",
       "a column of offsets is content, not evidence")
    # pseudocode lines: evidence tails
    fl = eb.rewrite_fence_line
    ok(fl("A1. Foo(x) \u2192 i32:                  [C] (fn:Foo@0x0045ABCD, run:2026-10-16-combat)") == "A1. Foo(x) \u2192 i32:                  [C]",
       "a pseudocode head line: the evidence parenthetical goes, the tag stays")
    ok(fl("A1. Foo(x):   [C] (fn:Foo@0x0045ABCD, all of A1\u2013A6; run:2026-10-16-x)").endswith("[C] (Foo, all of A1\u2013A6)"),
       "an anchor in a tail becomes its bare name")
    ok(fl("1. U+0xC4 \u2190 U+0xC4 | 0x20000      ; every event      [I] (0x005E9F10, 0x005EA078)") ==
       "1. U+0xC4 \u2190 U+0xC4 | 0x20000      ; every event      [I]", "a trailing evidence list goes, offsets and masks stay")
    ok(fl("2. x \u2190 y            ; at 0x005E9F10") == "2. x \u2190 y", "a trailing comment left empty goes")
    ok(fl("3. x \u2190 y            // see 0x005E9F10") == "3. x \u2190 y", "a trailing // comment left empty goes")
    ok(fl("4. x \u2190 y            ; step 3: run:2026-10-16-x") == "4. x \u2190 y            ; step 3", "a label left bare goes")
    ok(fl("5. r \u2190 0x00588D60(&u)") == "5. r \u2190 0x00588D60(&u)", "an address in the code part: the line stays as it was (the block fails)")
    ok(fl("6. x \u2190 y") == "6. x \u2190 y", "a clean line is unchanged")
    ok(fl("7. f(and)   [C]") == "7. f(and)   [C]", "a word in parentheses is no evidence")
    pgf = eb.Page({"path": "p.md", "route": "p", "order": 1})
    bl = eb.parse_blocks(("## H\n\n```\nA1. Foo(x):        [C] (fn:Foo@0x0045ABCD, run:2026-10-16-c)\n  y \u2190 {a, b}   ; (unsigned) mod 3  [I] (0x0045ABCD)\n```\n"
                          "\n```\nA2. Bar(x):   [C]\n  r \u2190 0x00588D60(&u)\n```\n").split("\n"))
    rd = eb.redact(pgf, bl)
    kp = eb.simplify(pgf, rd, ec.Allow())
    kt = "\n".join("\n".join(b["lines"]) for b in kp)
    ok("fn:" not in kt and "A1. Foo(x):        [C]" in kt and "A2." not in kt and len(pgf.drops) == 1 and pgf.drops[0][1] == "X1",
       f"a block with an evidence tail survives; one with an address in code drops ({kt!r}, {pgf.drops})")
    # measurement: words, units and fenced blocks per page
    pgm = eb.Page({"path": "m.md", "route": "m", "order": 1})
    bm = eb.parse_blocks(("## H\n\nOne two three four. Five six 0x00556F60 seven. Eight 0x1234567890 nine.\n\n```\nA1. Foo(x):  [C]\n```\n\n```\nb = f(x);\n```\n").split("\n"))
    pgm.count_source(bm)
    kk = eb.simplify(pgm, eb.redact(pgm, bm), ec.Allow())
    pgm.count_kept(kk)
    ok(pgm.fences == 2 and pgm.fences_kept == 1 and pgm.words > pgm.words_kept > 0, f"words and fenced blocks are counted ({pgm.words}, {pgm.words_kept}, {pgm.fences_kept})")
    tmpm = tempfile.mkdtemp(prefix="export_rep_")
    try:
        pgm.dropped_page = False
        eb.write_report(tmpm, [(pgm, kk)], "2026-11-17")
        rtxt = open(os.path.join(tmpm, "report.txt"), encoding="utf-8").read()
        ok("total: 1 pages: units dropped" in rtxt and "words dropped" in rtxt and "fenced blocks kept 1/2" in rtxt and " | 1/2 | " in rtxt,
           "the report gives units, words and fenced blocks, per page and in total")
    finally:
        shutil.rmtree(tmpm, ignore_errors=True)
    # a link fragment whose slug carries a hex seed is dropped (the heading itself may stay under a worked-example section)
    pa = eb.Page({"path": "a.md", "route": "a", "order": 1}); pb = eb.Page({"path": "b.md", "route": "b", "order": 1})
    pb.headings = {"ex-k--b3e5b26e3c7cb331", "plain-one"}
    byp = {"a.md": pa, "b.md": pb}
    ok(eb.rewrite_links("[x](b.md#ex-k--b3e5b26e3c7cb331) [y](b.md#plain-one)", pa, byp) == "[x](../b/) [y](../b/#plain-one)",
       "a heading anchor carrying a hex run is dropped, a plain one stays")
    # rows and cells
    ok(eb.rewrite_row("| a | fn:Foo@0x0045ABCD | 2 |") == "| a | `Foo` | 2 |", "a row: anchor cell rewritten")
    ok(eb.rewrite_row("| a | run:2026-10-11-a | 2 |") == "| a | — | 2 |", "an emptied cell becomes an em dash")
    ok(eb.rewrite_row("| a | b |") == "| a | b |", "an unchanged row is unchanged")
    pg = eb.Page({"path": "p.md", "route": "p", "order": 1})
    blks = eb.parse_blocks(("## H\n\nIt calls fn:Foo@0x0045ABCD. src:abc-def.\n\n- item struct:U+0x4\n- run:2026-10-11-a\n\n"
                            "| n | v |\n|---|---|\n| x | run:2026-10-11-a |\n| y | fn:Bar@0x0045ABCD |\n| z | plain |\n").split("\n"))
    red = eb.redact(pg, blks)
    txt = "\n".join("\n".join(b["lines"]) for b in red)
    ok("It calls `Foo`." in txt and "src" not in txt and "src" not in txt and "- item" in txt and "(run" not in txt
       and "| x | — |" in txt and "| y | `Bar` |" in txt, f"redact: units rewritten, an emptied sentence and item dropped ({txt!r})")
    ok(len(pg.rewrites) == 5 and pg.rewrites[0][0] == "H" and pg.rewrites[0][1].startswith("It calls fn:Foo"),
       f"every rewrite is recorded with its heading, before and after ({len(pg.rewrites)})")
    ok(any(d[1] == "empty" for d in pg.drops), "a unit left with no words is a drop")
    tmpo = tempfile.mkdtemp(prefix="export_rep_")
    try:
        eb.write_report(tmpo, [(pg, red)], "2026-11-17")
        rl = [x for x in open(os.path.join(tmpo, "report.txt"), encoding="utf-8").read().split("\n") if x.startswith("REWRITE")]
        ok(len(rl) == 5 and all(len(x.split("\t")) == 5 for x in rl) and rl[0].split("\t")[1:3] == ["p.md", "H"],
           f"REWRITE report line: REWRITE, page, heading, before, after, tab-separated ({rl[:1]})")
    finally:
        shutil.rmtree(tmpo, ignore_errors=True)
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
    ok("--schematic" in src and eb.SCHEMATIC_TOOLS == ("maze_anim.py", "tc_anim.py", "rng_anim.py", "seedtree_anim.py", "quality_anim.py",
                                                      "special_anim.py", "timing_anim.py", "frame_anim.py", "links_anim.py", "preset_anim.py",
                                                      "pack_anim.py", "pool_anim.py"), "schematic tools only")
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
        ok("[how we know](../../a/)" in b and "[hidden]" not in b and "hidden" in b,
           "an alias line sends a link to its page (anchor dropped when absent); others lose their target")
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
        ok("Seed: illustrative, an input of our own." in txt, "an illustrative seed is labelled")
        res = eb.illustration_block(pg, {"lines": ["```illustration", "id: i3", "tool: maze_anim.py", "args: --frame 1320",
                                                   "seed: none", "illustrates: x", "caption: Hi.", "```"]},
                                    tmp, out, al, "H")
        txt = "\n".join(l for b in res for l in b["lines"])
        ok("The picture takes no seed." in txt and "Seed:" not in txt, "review of lane/x11b: a generator with no seed gets no seed label")
        ok("computed by our model" in txt, "values: computed is the default")
        res = eb.illustration_block(pg, {"lines": ["```illustration", "id: i4", "tool: maze_anim.py", "args: --frame 1320",
                                                   "seed: none", "values: restated", "illustrates: x", "caption: Hi.", "```"]},
                                    tmp, out, al, "H")
        txt = "\n".join(l for b in res for l in b["lines"])
        ok("The picture restates the spec; nothing shown is observed in the game." in txt and "computed by our model" not in txt,
           "review of lane/x11s: values: restated drops the model label")
        ok("bad values" in eb.parse_illustration("id: i5\ntool: t.py\nargs:\nseed: none\nvalues: guessed\nillustrates: x\ncaption: c.")[1],
           "values takes computed or restated only")
        shutil.rmtree(os.path.join(out, "site", "public", "illustrations"), ignore_errors=True)
        # Phase 9 review: a route stem on a `page` line; an over-limit table the manifest does not name goes whole,
        # a named one (by its source header line, front matter counted) stays, and the cut passes X6 either way
        rows = "".join(f"| {i} | step {i} |\n" for i in range(22))
        page_c = (f"---\nstatus: reviewed\n---\n# Gamma\n\n## Steps\n\n| # | step |\n|---|---|\n{rows}\n"
                  f"## List\n\n| # | row |\n|---|---|\n{rows}\nAfter.\n")
        with open(os.path.join(tmp, "docs", "README.md"), "w") as f:
            f.write(page_c)
        man2 = "group s 1 Spec\npage README.md s 1 overview\ntable README.md 8 our step table\ntable README.md 99 nothing\n"
        with open(os.path.join(tmp, "manifest2.txt"), "w") as f:
            f.write(man2)
        eb.build(out, os.path.join(tmp, "manifest2.txt"), tmp, "2026-11-17", al, run_illus=False)
        cpath = os.path.join(out, "site", "src", "content", "docs", "s", "overview.md")
        c = open(cpath, encoding="utf-8").read() if os.path.isfile(cpath) else ""
        ok(c.count("| 21 | step 21 |") == 1 and "| # | step |" in c and "| # | row |" not in c and "After." in c,
           "the named table stays, the unnamed one over the limit goes whole, the route takes the stem")
        rep = open(os.path.join(out, "report.txt"), encoding="utf-8").read()
        ok("| X6 | table | 22 body rows, source line 35" in rep and "names line 99, where no table starts" in rep,
           f"the X6 drop and an unmatched `table` line are report lines ({[l for l in rep.splitlines() if 'X6' in l][:1]})")
        fails, _ = ec.check_cut(out, os.path.join(tmp, "manifest2.txt"), ())
        ok(not fails, f"the cut with a left-out table passes export_check ({fails[:3]})")
        ok(ec.parse_manifest(os.path.join(tmp, "manifest2.txt")) == ({"README.md": "s/overview"}, {"s/overview": 2}),
           "the check reads the route stem")
    finally:
        eb.DOCS, eb.subprocess.run = old_docs, old_run
        ec.set_allow(None)
        shutil.rmtree(tmp, ignore_errors=True)
        shutil.rmtree(out, ignore_errors=True)
    print(f"TEST export_build: {checks} checks, {len(failed)} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
