# 0007 — Docs gate: mechanical checks for anchors, tags, links and parser surveys

> **Status:** in-progress (Phases 1 and 3 accepted with fixes, merged 2026-10-11; Phase 2 next)
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
  - `python3 -I tools/test_gate.py` passes (`-I` drops the current directory from the import path, so
    `-m unittest tools/test_gate.py` can't import it). It has one fixture per error rule that makes
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
  - The hook resolves the repository root of the worktree being committed (the `git -C` path, else the
    hook input's `cwd`, else `$CLAUDE_PROJECT_DIR`, each through `git rev-parse --show-toplevel`), so it
    gates that worktree and not the session's project directory; the log records a check from the plan
    0006 worktree.
- **Merge order:** merge after `plan-0004-p1b`, which declares `DataTables`/`Game`/`Unit` in `re/types/`.
  Merged before it, `main` is red on E4 and every docs commit is denied. On merge, strike the E4 backlog
  entry as done.

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
| W1 | 307 `[C]`/`[I]` statements | 59 warnings: 5 are `docs/findings/README.md` index rows, the other 54 are real unanchored statements. After the review fixes (README.md is no longer a finding; W2 code-span fix; E8 over every tracked `.md` but the fixtures; W3 cites from specs and findings only), the real tree gives: E1 322/0, E2 10/0, E3 94/0, E4 63/3, E5 16/0, E6 4/0, E7 185/0, E8 390/0; W1 302/54, W2 185/0, W3 185/16; RED on the 3 E4 errors only, 0.33 s |
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

### 2026-10-11 — Phase 3 (archivist): commit hook

Outputs: `.claude/hooks/gate-on-commit.js` (Node, no dependencies), wired last in the Bash
`PreToolUse` list of `.claude/settings.json` (hook timeout 30 s; the gate itself is capped at 20 s);
`.claude/hooks/gate-on-commit.test.mjs` (`node --test`, 7 tests); one *Docs gate on commit* bullet in
`CLAUDE.md` § Commit hygiene.

Behaviour: fires on any simple command `git [-C dir] [-c k=v] … commit` in the command line, after
splitting on `&&`, `||`, `;`, `|` and newlines with a small quote-aware tokenizer. Root: the `-C` path
if given, else the hook input's `cwd`, else `$CLAUDE_PROJECT_DIR`, then `git rev-parse
--show-toplevel`. Paths: `git diff --cached --name-only`, plus the paths of every `git add` in the same
command line, plus `git diff --name-only` for `commit -a`/`--all`, plus any `git commit <pathspec>`.
Runs `python3 -I tools/gate.py --no-warnings --root <root>` only when one path is `docs/…` or `re/…`.
Exit 0 → `{}`, silent. Exit 1 → deny; the reason lists the gate's error lines (capped at 40) and its
summary line. No `tools/gate.py` in that root → allow silently. Python missing, timeout or any other
exit code → allow, one line on stderr (`gate-on-commit: could not run python3 (ENOENT); commit allowed
without the docs gate`).

Tests (`node --test .claude/hooks/gate-on-commit.test.mjs`, all pass, 3.1 s). Each builds a git repo
under `/tmp/claude-1000/hooktest/` from a copy of `docs/`, `re/`, `.claude/` and `tools/gate.py`.
`.claude/` is copied because `docs/backlog.md` links into it (E8). Each repo gets a
`re/types/hooktest.h` declaring `DataTables`, `Game`, `Unit` so that the copy starts green despite
the open E4 entry. The break is `fn:GAME_InitSeeds@0x0052C281` appended to `specs/rng/seeds.md`.

| Case | Result |
|---|---|
| base copy | gate exit 0 |
| (a) broken anchor staged, `git commit -m …` | denied; reason has `docs/specs/rng/seeds.md:N: E1 … GAME_InitSeeds …` and `gate fast tier: RED` |
| (a2) same, unstaged, `git add docs/… && git commit …` | denied, same E1 line |
| (b) red working tree, only `tools/x.py` staged (`git add tools/x.py && git commit`) | allowed, stdout `{}`, stderr empty: the gate did not run |
| (c) harmless `docs/backlog.md` line staged | allowed, stdout `{}`, stderr empty |
| (d) cwd = green repo, `git -C <red repo> commit` | denied, reason names the red repo's path; reverse (cwd red, `-C` green) allowed |
| no `tools/gate.py` in root | allowed silently |

Manual checks:
- **Plan 0006 worktree**: synthetic JSON with cwd = this worktree and `git -C
  /home/igor/Work/recompilcation-project-0006 add docs/plans/README.md && git -C … commit -m …` →
  **allowed silently** (`{}`), not denied: that branch (`4a2c43e`) predates `tools/gate.py`, so the
  older-branch rule applies. Root resolution is shown by (d). For the record, this branch's gate run on
  that tree (`--root …-0006`) is RED with 5 errors: the 3 known E4, plus E8 `README.md:25` →
  `docs/plans/0001-bootstrap.md` (moved to `done/`) and E8 `docs/backlog.md:10` (the stale installer slug
  fixed in Phase 1). Both E8 are fixed on this branch.
- **This worktree**: `git commit` with nothing under `docs/`/`re/` staged → `{}`.
  `git add docs/plans/README.md && git commit …` → **denied** on the 3 open E4 errors.
- **Python missing** (PATH holding only `git`) → allowed with the stderr line above.

For the review: once this lands on `main`, **every** commit touching `docs/` or `re/` is denied
until the reverser's E4 backlog entry (`struct:DataTables`, `struct:Game`, `struct:Unit`) is done, in
every lane. Either fix E4 before or with the merge, or merge the hook wiring after it.

### 2026-10-11 — Phase 3 review fixes (archivist)

The fixes from the "accept with fixes" review are applied. A leading `cd`/`pushd` now moves the cwd
that later `git` commands, their `-C` and the `git add` paths resolve against. `git add -u`/`--update`/`-A`/`--all` now
count every modified tracked path. Simple commands come from `simpleCommands` in
`block-push-and-history-rewrite.js`, which drops heredoc bodies and unwraps `bash -c "…"`. An exit 1
with no `gate fast tier:` summary line is now treated as a crash: the hook warns with the last stderr
line and allows. `-S` is no longer a value-taking flag. Tests: 14 of 14 pass. The new ones are (e) `cd`
to a subdirectory, (f) `cd` to another repo, (g) a heredoc body that mentions `git add docs/…`,
(h) `add -u`, (i) `bash -c`, (j) `-S` and (k) a stub `gate.py` that raises.
- **2026-10-11 — Phases 1 and 3 reviewed and merged (architect).** Phase 1 accepted with fixes (rule text
  `b8916dd`, code `9b9f425`); Phase 3 accepted with fixes (plan text `c66cae1`, code `1f6ff9d`, 14 hook tests
  pass). Merged into `main` after `plan-0004-p1b` as the merge order requires. `main` is green on the fast
  tier (0 errors, 71 warnings) and the hook is active. The E4 backlog entry is struck. Phase 2 is unblocked:
  `d2s.py` (0005·P4) and the `dt1.py`/`ds1.py` render changes (0006·P1–2) are on `main`.

### 2026-10-11 — Phase 2 (archivist): full tier, survey baselines

Outputs: a final `SURVEY <tool> key=value …` line in `tools/ds1.py`, `dt1.py`, `d2s.py` and
`excel_survey.py`; the `SURVEYS` registry, `--full[=TOOL,…]` and `--require-workspace` in
`tools/gate.py`; baselines in `tools/gate/baselines/{ds1,dt1,d2s,excel}.txt`; 10 new tests in
`tools/test_gate.py` (`FullTierTest`, a stub survey in a scratch root, no workspace needed; 17 of 17
pass); a *Docs gate* section in `docs/formats/README.md` on refreshing a baseline.

The four baselines:

```
SURVEY ds1 files=2276 parsed=2273 anomalies=3 errors=0 objects=17777 paths=136 leftover_bytes=44
SURVEY dt1 files=263 parsed=257 other_versions=6 errors=0 tiles=16456 blocks=361484 leftover_bytes=0
SURVEY d2s files=23 full=21 stubs=2 errors=0 items=228 leftover_bytes=0
SURVEY excel tables=97 txt=92 bin=92 txt_rows=22698 bin_records=21796 rows_eq=57 rows_x=30 diff=0 errors=0 recsize_unknown=4
```

Key meanings: ds1 `objects`/`paths` sum over cleanly parsed files, and `leftover_bytes` is the 44 of
the known-malformed `swamp2.ds1`. dt1 `tiles`/`blocks` sum over parsed 7.6 files, and
`leftover_bytes` sums over files rejected for leftover. d2s `leftover_bytes` is past the parsed end
of full saves. excel `bin_records` sums the leading counts of bins whose size fits the u32-count +
fixed-record layout; `recsize_unknown` counts the other four (`itemscode`, `misscode`,
`skilldesccode`, `skillscode`), whose leading u32 isn't a record count. excel `errors` counts bins
shorter than 4 bytes; the survey has no other failure mode.

Registry inputs come from the documented invocations: `workspace/merged` for ds1 and dt1
(`formats/ds1.md`, `formats/dt1.md`), `workspace/merged` + `workspace/logs/merged-manifest.tsv` for
excel (`tables/README.md`), and for d2s the excel dir plus `workspace/samples/d2s/*.d2s` and four
named `d2s-edited/` saves (`formats/d2s.md`, the 23-save command). Those paths are stable: all 24
files under `workspace/samples/` match the sha256 table in `d2s.md`. The glob does pick up any save
added there later, which then shows up as a `files=` diff.

Done-when:
- **Additive.** Each survey's output was captured with `main`'s tools (`f387831`) before the edit
  and after it. `diff` shows exactly one added last line per tool and nothing else; exit codes are
  unchanged (all 0). The `--md` form of `excel_survey.py` ends with the same line.
- **Reproduces.** `python3 -I tools/gate.py --full` → fast tier GREEN, then `S ds1 ok`, `S dt1 ok`,
  `S d2s ok`, `S excel ok`, `gate full tier: GREEN, 4 surveys, 0 errors`, exit 0.
- **One number edited.** `tiles=16456` → `16457` in `baselines/dt1.txt` (reverted after):
  `S dt1 FAIL`, `dt1: tiles: baseline 16457, survey 16456 (-1)`, then the full `now:` line, `gate
  full tier: RED`, exit 1. Missing or extra keys are reported per key too (unit tests).
- **Workspace absent.** A scratch git copy of every tracked file plus the new baselines, no
  `workspace` link, `--root` on it: fast tier GREEN, `SKIPPED: workspace absent`, `gate full tier:
  SKIPPED`, exit 0. With `--require-workspace`: `gate full tier: RED, workspace absent and
  --require-workspace given`, exit 1.
- **Integers only.** `grep -nE '=[^0-9]|=[0-9]+[^0-9 ]' tools/gate/baselines/*.txt` → no hits;
  `grep -cE '^SURVEY [a-z0-9_]+( [a-z0-9_]+=[0-9]+)+$'` → 1 in each of the four files. The gate
  itself rejects a baseline line that isn't `SURVEY <tool>` followed by `key=<int>` pairs.
- **Wall time** (from the gate's own per-survey timer): ds1 4.5 s, dt1 3.1 s, d2s 0.05 s, excel 0.06 s,
  7.8 s in all with a warm page cache. Cold, the standalone surveys took ds1 11.7 s and dt1 8.2 s. None
  is near 60 s, so none is opt-in. The `opt_in` field exists, and the gate flags any default survey
  that runs over 60 s.

Choices for the review:
- With `workspace/` present, a missing registered input (a path or a glob with no match) is an
  **error**, not a skip, so a moved sample directory can't silently drop a survey. Only an absent
  `workspace/` as a whole is `SKIPPED`.
- A survey that exits non-zero is an error even if its counts match the baseline.
- The gate runs the root's own `tools/` scripts (`--root` checks that tree's parsers).
- Adding `dc6` is one line: `Survey("dc6", ["tools/dc6.py", "survey", "workspace/merged"]),`, plus
  its baseline. Plan 0006 should check that its survey's input root matches this.
- `palette.py survey` exists but is outside this phase's list of four. It has no `SURVEY` line and
  isn't registered.
