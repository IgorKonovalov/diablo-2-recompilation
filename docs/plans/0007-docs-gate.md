# 0007 — Docs gate: mechanical checks for anchors, tags, links and parser surveys

> **Status:** in-progress (approved)
> **Created:** 2026-10-11
> **Owner skill(s):** archivist
> **Related ADRs:** 0001-target-toolchain-evidence-sources, 0006-docs-gate

## TL;DR

Which of our rules can a script check, and does the repository pass? This plan builds
`tools/gate.py` (ADR-0006). Its fast tier checks every anchor in specs and findings against its
registry, the placement of `[L]`, front-matter tag counts, `re/symbols.csv` and relative links. Its
`--full` tier reruns the parser surveys against `workspace/` and compares their counts with
committed baselines. A PreToolUse hook then runs the fast tier on every `git commit` that touches
`docs/` or `re/`. When it's done, a broken anchor or link can't be committed, and a parser
regression shows up as a count diff.

## Context

- The rule list the gate enforces is in `.claude/skills/architect/references/evidence-rules.md`
  § Mechanical checks, written with ADR-0006. That section is the spec for Phases 1–2: the gate
  implements it, error for error, and adds no rules of its own.
- Prototype (2026-10-11, done during planning and thrown away): all 322 `fn:`/`data:` anchors
  resolve by name and address, no spec has `[L]` outside *Open questions*, and all four specs'
  front-matter `tags:` match their bodies. `re/symbols.csv` passes E7, and every `src:`, `run:` and
  `fmt:` anchor resolves. The only E4 hit was `tbl:monstats.txt` against `MonStats.md`, which is why
  E4 compares table names case-insensitively. Phase 1 is expected to be green on `main`, so anything red
  is either a real defect or a gate bug.
- `re/symbols.csv` has quoted `signature` fields that contain commas. Read it with the `csv` module,
  not by splitting.
- Existing `survey` subcommands: `ds1.py`, `dt1.py`, `d2s.py`, `excel_survey.py`. Plan 0006 adds
  `dc6.py`/`dcc.py` surveys later. They're picked up by the same mechanism when they land, without
  amending this plan.
- A spec is a file under `docs/specs/` with `spec:` front matter. `docs/specs/README.md` (the
  research map) is not a spec.
- Plan 0006 runs in a parallel worktree (`plan-0006-asset-rendering`). This plan touches
  `tools/dt1.py`/`tools/ds1.py` only to add a summary line (Phase 2). Keep that edit minimal so the
  merge stays trivial.
- **Priority:** in the archivist lane this plan is small and comes after plan 0005 Phase 4 (D2S). It
  doesn't block any research plan.

## Phases

### Phase 1 — Fast tier
- **Owner skill:** archivist
- **What:** Write `tools/gate.py`, standard library only and run with `python3 -I`, implementing
  every fast-tier rule in evidence-rules § Mechanical checks, plus its self-test.
- **Outputs:** `tools/gate.py`. `tools/test_gate.py` (`unittest`) with small fixture docs under
  `tools/gate/fixtures/`.
- **Done when:**
  - `python3 -I tools/gate.py` exits 0 on `main` in under 5 s and reads nothing under `workspace/`.
    It prints one line per check, with a count.
  - The output separates errors (exit 1) from warnings (exit 0).
  - `python3 -I -m unittest tools/test_gate.py` passes. It has one fixture per error rule that makes
    the gate red with a message naming the file, the line and the rule. It also has one fixture per
    warning rule.
  - Each of these breaks on a scratch copy turns the gate red: renaming one symbol in
    `re/symbols.csv`; changing a cited address by one digit; deleting a `docs/sources.md` row; moving
    an `[L]` line out of *Open questions*; editing a front-matter count; breaking one `#heading`
    link. Record the result in the implementation log.

### Phase 2 — Full tier: survey regression
- **Owner skill:** archivist
- **What:** Give each `survey` subcommand one machine-readable summary line. The gate's `--full` tier
  runs every registered survey and diffs that line against a committed baseline.
- **Outputs:**
  - A final `SURVEY <tool> key=value …` line from `ds1.py`, `dt1.py`, `d2s.py` and `excel_survey.py`.
    The keys are counts only: files, records or blocks, errors, unknown or leftover bytes.
  - A survey registry in `tools/gate.py`, giving tool, args and the workspace path it needs.
  - `tools/gate/baselines/<tool>.txt`.
  - A *Docs gate* note in `docs/formats/README.md` (or the nearest index) saying how to refresh a
    baseline.
- **Done when:**
  - `tools/gate.py --full` reproduces every baseline on this machine.
  - Editing one number in one baseline turns it red with a key-by-key diff.
  - With `workspace/` absent (a fresh worktree without the symlink), it prints `SKIPPED: workspace
    absent` and exits 0, and with `--require-workspace` it exits non-zero.
  - No baseline line holds anything but integer counts. Check this with a grep in the log.
  - The full-tier wall time is logged, and a survey slower than 60 s is marked opt-in
    (`--full=<tool>`) rather than run by default.

### Phase 3 — Commit hook
- **Owner skill:** archivist
- **What:** Run the fast tier from a PreToolUse hook on `git commit` when anything staged is under
  `docs/` or `re/`, and deny the commit on red.
- **Outputs:**
  - `.claude/hooks/gate-on-commit.js`, wired in `.claude/settings.json` next to the other hooks.
  - One line for it in `CLAUDE.md` § Commit hygiene.
- **Done when:**
  - A commit that stages a doc with a broken anchor is denied, and the deny message carries the gate's
    error lines.
  - A commit staging only `tools/` changes doesn't run the gate.
  - A green commit goes through with no visible output.
  - The hook resolves the repository root from `$CLAUDE_PROJECT_DIR`, so it gates the worktree
    being committed, and the log records a check from the plan 0006 worktree.

## Open questions

- Should warnings ever become errors? Revisit after two plan closes. If a warning rule has had no
  false positives by then, the architect may promote it by amending § Mechanical checks.
- `tbl:` and `fmt:` anchors are checked to file level only. Checking the column, or the `#field`
  after `fmt:`, needs each table and format doc to list its columns in a parseable form. Deferred
  until those docs settle.
- Bit-exact reproduction checks (`tools/rng.py check …`) are regression tests too. They join the full
  tier only once their recorded inputs have a stable home in `workspace/`. That's for the reverser to
  propose through the backlog.
- This plan doesn't decide whether to adopt a conductor. It only provides the gate one would need.

## Implementation log

_(lanes append dated entries as phases land)_

### 2026-10-11 — Phase 1 (archivist): fast tier

Outputs: `tools/gate.py` (stdlib, `--root DIR` to check another tree, `--no-warnings` to print
warning counts only), `tools/test_gate.py` (5 tests), fixtures in `tools/gate/fixtures/`: `base/` is
a small green tree, and `E1`–`E8`, `W1`–`W3` are overlays that each break one rule.

**Real tree** (this branch, 0.78 s wall, about 0.85 s with interpreter start; reads only tracked
files under `docs/` and `re/`, the tracked-path list from `git ls-files`, nothing under `workspace/`):

| Rule | Checked | Result |
|---|---:|---|
| E1 | 322 `fn:`/`data:` anchors | 0 errors |
| E2 | 10 `src:` | 0 |
| E3 | 95 `run:` | 0 |
| E4 | 63 `tbl:`/`fmt:`/`struct:` | **3 errors**, see below |
| E5 | 16 `[L]` in specs | 0 |
| E6 | 4 specs | 0 |
| E7 | 185 rows | 0 |
| E8 | 376 relative links | 0 after one own-lane fix (below) |
| W1 | 307 `[C]`/`[I]` statements | 59 warnings (most are `docs/findings/README.md` index rows, which count as findings by the scope rule) |
| W2 | 185 tagged table rows | 1 (`specs/data/excel.md:68`) |
| W3 | 185 symbols | 16 (nine `*_LinkPick` functions, one option table, six table-count globals) |

Genuine defects found:
- **E4, open (reverser):** `struct:DataTables` (`findings/data/0001-excel-loader.md:376`), `struct:Game`
  and `struct:Unit` (`findings/items/0001-tc-resolution.md:433–434`) name types that no `re/types/*.h`
  declares (only `tc.h` exists). The planning prototype didn't check `struct:`. Not fixed here (other
  lane); backlog entry to the reverser. **So the fast tier exits 1 on this branch**, and the first
  Done-when bullet can only be met once that entry is done.
- **E8, fixed:** `docs/backlog.md:10`, an archivist entry, linked
  `formats/installer.md#launch-path-in-this-install-not-used-by-us`; the heading is now *Launch path in
  the 1.14d install*. Link updated.

Deliberate breaks, each on a scratch copy of every tracked file (`--root`), each on its own:

| Break | Result |
|---|---|
| Rename `GAME_InitSeeds` in `re/symbols.csv` | RED: 8 × E1 `name … not in re/symbols.csv` (spec + finding lines), +1 W3 |
| `fn:GAME_InitSeeds@0x0052C280` → `…C281` in `specs/rng/seeds.md` | RED: E1 `seeds.md:26 … re/symbols.csv has GAME_InitSeeds at 0x0052C280` |
| Delete the `siramy-ds1edit` row of `docs/sources.md` | RED: 10 × E2 in `formats/ds1.md`, `formats/dt1.md` |
| Move a `[L]` bullet of `seeds.md` from *Open questions* to *Purpose* | RED: E5 `seeds.md:15` |
| `tags: {C: 51 …}` → `C: 50` in `seeds.md` | RED: E6 `seeds.md:7 tags: C: 50 but the body has 51 [C]` |
| `#open-questions` → `#open-question` in a `seeds.md` link | RED: E8 `seeds.md:349 … no heading with slug #open-question` |

Choices for the review:
- Anchor syntax is matched only in its well-formed shape (`fn:Name@0x…`, `run:YYYY-MM-DD-slug`,
  `src:<id>` starting with a letter or digit…), so placeholders like `` `src:` ``, `run:YYYY-…` and
  `fn:Name` without an address are not anchors. `struct:` is checked with or without `+0x…`.
- E2–E4 strip nothing: anchors inside code blocks (pseudocode comments) are checked. E8 skips fenced
  code and code spans. E5/E6 count every `[C]`/`[I]`/`[L]` in the body, code included (matches
  all four specs).
- W1 reads a statement as a table row or a whole list item/paragraph with its wrapped lines, since the
  tag opens a bullet and the anchors close it. Bare `0x00XXXXXX` addresses count as anchors (the
  evidence-rules example uses one). W3 counts a symbol as cited when its name appears anywhere in
  `docs/`.
- E7's image bound is `[0x00400000, 0x009BA000)` (end of `.reloc`, `docs/inventory.md`), a constant.
- The Done-when command `python3 -I -m unittest tools/test_gate.py` can't import the module under
  `-I` (no cwd on `sys.path`). Equivalent: `python3 -I tools/test_gate.py` or
  `python3 -I -m unittest discover -s tools -p test_gate.py`. Both pass.
