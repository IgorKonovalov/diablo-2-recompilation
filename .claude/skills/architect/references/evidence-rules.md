# Evidence rules (operational detail for ADR-0001)

Every lane reads this file. The architect enforces it in review.

## Tags

| Tag | Meaning | Minimum evidence |
|---|---|---|
| `[C]` | confirmed | A code anchor in the pinned `Game.exe` **plus** one independent corroboration (below) |
| `[I]` | inferred | A code anchor we read and understood; no independent corroboration yet |
| `[L]` | lead | No anchor in our binary. External doc, symbol-name guess, or hypothesis |

Independent corroboration is one of:
1. **Second code path**: another function that reads or writes the same field consistently (for example writer and reader agree).
2. **Data behaviour**: the claim explains every row in a table (e.g. the decoded column matches all values in `Levels.txt`).
3. **Runtime experiment** (`run:` anchor): observed under wine, through a debugger, a memory read or save inspection.
4. **Bit-exact reproduction**: a `tools/` reimplementation gives identical outputs to the binary for recorded inputs.
   An out-of-scope callee that shares a seed may be a logged **boundary oracle** (ADR-0004): the model asserts the
   seed on entry to every oracle call, then takes the logged exit seed and return value. Such a `[C]` covers the
   in-scope code only and names its oracles.
   The binary's side may also be its own code run under Ghidra's p-code emulator, with a declared memory image
   (ADR-0015): no patched code, every memory read accounted for, and the `[C]` covers the code's map from the bytes it
   reads, not what the game stores at those offsets or when it runs; faults, x87 results and OS calls are not covered.
   A case may end at an **observed boundary** (ADR-0021, amending ADR-0015 (1) and (3)): the emulator stops at a
   declared callee's entry, reached by the program's own flow with nothing patched; the checker asserts per case which
   boundary and which call site (return address) was reached, and compares every argument, pre-call byte and seed state
   the claim uses. Such a `[C]` covers the code up to the boundary only: not the callee, not the caller's code after
   it, not the return value. The finding names each claim's boundary and lists the code after it as not covered.

Data-format claims follow the same scheme. A field layout is `[C]` once a parser reads every file
of that type without error *and* the decoded values make sense, or once the code that reads the
field is anchored. This covers *layout*: offsets, widths, encodings and counts that the data alone
pins down. An *interpretation* drawn from the data alone (what a field means, why bytes are padding,
which palette or row order the game uses, a field being "stale memory") is `[L]`, because `[I]`
requires a code anchor in `docs/formats/` exactly as everywhere else. A data-only check that rules out
every alternative encoding (for example glyph shapes that fix a row order) makes the *encoding* `[C]`;
how the game uses it still needs code.

## Anchors

```
0x0045A1B0                         address in pinned Game.exe (8 hex digits, 0x-prefixed)
fn:RNG_Next@0x0045A1B0             named function (name must exist in re/symbols.csv)
data:g_pLevels@0x0096C888          named global (kind `data` in re/symbols.csv)
struct:Unit+0x14                   field offset in a type from re/types/
tbl:TreasureClassEx.txt:Picks      table column
fmt:ds1#header.version             format doc field
run:2026-10-12-rng-seq             experiment record in docs/findings/<subsystem>/experiments.md
                                   (or docs/formats/experiments.md, for format claims)
src:pk-tc-guide                    docs/sources.md entry (leads only)
```

Put the tag first and anchors in brackets at the end of the statement:
`[I] The pick count is read as a signed 32-bit value; negative means "pick each entry N times". (0x0045B2C0, tbl:TreasureClassEx.txt:Picks)`

## Promotion

- `[L]` → `[I]`: find the code, add the address, add the function to `re/symbols.csv`.
- `[I]` → `[C]`: add the corroboration and name it in the statement.
- Demotion is allowed and expected. When new evidence contradicts a claim, downgrade it, record the
  contradiction in the finding, and add a backlog entry if a spec cites it.

## Experiments

Record each one in `docs/findings/<subsystem>/experiments.md`. A run whose claim is about a file
format's bytes, run by the archivist (a save written and reloaded, a parser-edited file loaded), goes
in `docs/formats/experiments.md` instead, which the archivist owns. Either way the record is
reproducible from itself (ADR-0003): exact command lines, steps files, and the raw-log path or a
statement that none was kept.

```
## run:YYYY-MM-DD-slug
- Question: …
- Setup: wine prefix, save file, seed control method, tool versions
- Procedure: numbered steps
- Observed: raw output (trimmed)
- Conclusion: which claims this upgrades, by finding link
```

**Forced-path runs** ([ADR-0010](../../../../docs/adrs/0010-forced-path-runs.md), decided cell by cell by
[ADR-0013](../../../../docs/adrs/0013-forced-path-runs-cell-level.md)). A run id ending in `-forced` edited cells of one
table (a loose `.bin` under `-direct`, every changed cell listed by `bindiff`) to make a rare stock path common. It
backs `[C]` only for a claim whose code reads none of the edited cells: the finding records that code's reads of the
table (row and column; a data-indexed row counts as the whole column), and a claim that reads or is named by an edited
cell stays `[I]`. Never for frequencies or for the edited cells' own effect. The plan must also log the path once on
stock data where stock play reaches it.

## Community cross-checks

Community documentation is used in two ways. A **lead** helps locate code ("the TC picker reads
`Picks`"). A **cross-check** compares a finished finding with what the community says about the
same behaviour. A cross-check finds problems; it never promotes a tag.

- **Agreement adds nothing.** A matching community claim does not move `[I]` to `[C]`. Community
  docs are not independent of the code: much of the folklore comes from 1.10 decompiles.
- **Disagreement must be resolved.** It means one of three things: we misread the code (demote and
  re-read), 1.14d really differs from older versions (state it in the spec so a reimplementer
  doesn't "correct" it), or the community claim is wrong. Each contradiction gets a backlog entry
  and is settled by a second code path, an experiment or bit-exact reproduction.
- **A branch the docs describe and the finding omits is a gap.** Examples are difficulty special
  cases, expansion-only paths, caps and clamps. Chase it like any open question.

**Leads are fetched, not recalled (ADR-0007).** A `src:` lead is a document the lane fetched and read
in the same session, registered in `docs/sources.md` before use, with a URL that serves it and a note
naming the sections used. Recalled knowledge is not a lead: write "no lead; derived from data" (or
"from code"). A page that shows decompiled or decoder source is registered `rejected` and not used.

Procedure:

1. **Blind first.** Write a behavioural claim (formula, draw order, branch) from the code
   *before* reading the community write-up of that behaviour. Leads used to *locate* code may be
   read at any time.
2. **Register before you cite.** Every source compared against has a `docs/sources.md` entry
   saying which game version it describes.
3. **Record one verdict per compared claim** in the finding's *Leads used* section:
   `[L] src:<id>: <what it claims>. **held** | **held with refinement** | **contradicted** | **not covered**`
   followed by one line of detail. `contradicted` links its backlog entry.
4. **Code in docs is code.** A forum post or wiki page that reproduces decompiled or reconstructed
   game source falls under the sources policy (ADR-0001): stop reading, and list it in
   `docs/sources.md` with `rejected: contains decompiled code` in the Notes column.

Where it pays: items (TCs, NoDrop, quality, MF, alvl/ilvl, sockets) are heavily documented, so
cross-checks are expected there. Monsters are moderately documented. DRLG has little coverage, so
cross-check only where a source exists.

## Mechanical checks (ADR-0006)

`python3 -I tools/gate.py` checks the rules below. An **error** fails the gate and denies a commit
that touches `docs/` or `re/`. A **warning** prints and never fails. The gate implements this list
and no more: changing a rule means editing this section, which the architect owns.

Scope: a *spec* is a file under `docs/specs/` with `spec:` front matter. A *finding* is any `.md`
under `docs/findings/` except `README.md` (an index, not a finding).

Errors (fast tier):

| # | Rule | Applies to |
|---|---|---|
| E1 | `fn:Name@0x…` and `data:Name@0x…` (the address written with exactly 8 hex digits): the name exists in `re/symbols.csv`, its address equals the cited one (case-insensitive hex), and `fn:` names a `func` row, `data:` a `data` row | specs, findings |
| E2 | `src:<id>` exists as an id in the `docs/sources.md` table | specs, findings, formats, tables |
| E3 | `run:<id>` exists as a `## run:<id>` heading in some `docs/findings/*/experiments.md` or in `docs/formats/experiments.md` | specs, findings |
| E4 | `tbl:<File>.txt:<Col>`: `docs/tables/<File>.md` exists (file name compared case-insensitively, as the game does). `fmt:<name>#…`: `docs/formats/<name>.md` exists. `struct:<Type>+0x…`: `<Type>` is declared in a `re/types/*.h` | specs, findings |
| E5 | `[L]` in a spec appears only under the `## Open questions` heading, its subsections included; code blocks are included | specs |
| E6 | A spec's front-matter `tags: {C: n, I: n, L: n}` equals the counts of `[C]`, `[I]` and `[L]` in its body, code blocks included | specs |
| E7 | `re/symbols.csv` has the header `address,kind,name,signature,confidence,subsystem,evidence`; `address` matches `0x00[0-9A-F]{6}` and lies inside the image, `[0x00400000, 0x009BA000)` per the section table in `docs/inventory.md`; `kind` ∈ {`func`, `data`}; `confidence` ∈ {`C`, `I`, `L`}; `evidence` is an existing path; no duplicate address and no duplicate name | `re/symbols.csv` |
| E8 | A relative markdown link resolves to a tracked file, and a `#fragment` matches a heading slug in it (GitHub slug rules) | every tracked `.md` except the deliberately broken fixtures under `tools/gate/fixtures/` |
| E9 | Every ` ```mermaid ` block parses with Mermaid's own parser (`tools/mermaid_check.mjs` under `node`, using the Mermaid build VS Code ships, patched and cached in `workspace/cache/mermaid/`; no download); a failure is reported at the fence line plus the line the parser names. Without `node`, the bundle, `workspace/` or a patch point, E9 is skipped with one warning, never an error | every `.md` under `docs/` |
| E10 | No confidence tag (`[C]`, `[I]`, `[L]`), no `fn:`/`data:`/`tbl:`/`struct:` anchor and no `0x00XXXXXX` address appears anywhere in the page body, code spans, code blocks and diagrams included (ADR-0012) | every `.md` under `docs/wiki/` |
| E11 | A page has a `based_on:` front-matter list, either the single entry `process` or entries `<repo path> <YYYY-MM-DD>` (flow list or one `  - ` line each); each path is a spec and its `status:` is `reviewed` | `docs/wiki/` except `docs/wiki/README.md` |
| E12 | Every `##` section (its `###` subsections included) holds a relative link, inline or reference-style, into `docs/specs/` | `docs/wiki/` except `README.md` and pages with `based_on: [process]` |
| E13 | A backlog entry (ADR-0018): front matter as `tools/backlog.py` writes it (only the keys `from`, `to`, `date`, `status`, `context`, `resolution`); `from` and each `to` a lane (`architect`, `archivist`, `reverser`, `spec-writer`, `human`); `status` ∈ {`open`, `done`, `moved`, `dropped`}; a `resolution` when the status is not `open`, none when it is; the file named `YYYY-MM-DD-<from>-<to>-<slug>.md` with `date` equal to its prefix; each `context` link resolves as in E8; no `open` entry in `docs/backlog/archive/` (ADR-0019) | `docs/backlog/*.md` and `docs/backlog/archive/*.md` except `README.md` |
| E14 | Outside code fences, every row of a markdown table has as many cells as its header row. An escaped `\|` and a pipe inside a code span don't split cells; a code span opens at a run of backticks and closes at the next run of the same length, an unclosed run is literal (plan 0053) | every tracked `.md` except `tools/gate/fixtures/` |
| E15 | For each spec linked from a research-map row's last (Status) cell: the cell's words before the first ` · `, bold stripped, equal the first linked spec's `status:` mapped as `reviewed` → `reviewed`, `draft` → `draft spec`. In the text between a spec link and the next link, the first `C n / I n / L n` group gives all three numbers and equals that spec's `tags:`, and an `updated YYYY-MM-DD` equals its `updated:`. Map convention that keeps every group checked: each spec's own group comes first after its link, and a sum over several specs is written in words (`sum to C 240, I 191, L 24`), never as a group (plan 0053) | `docs/specs/README.md` |
| E16 | In `docs/plans/README.md`, each row linking a plan has a Status cell (the third) whose first word equals the first word of the plan's `> **Status:**` line, and the link points under `done/` if and only if that word is `done` or `abandoned`. In `docs/plans/README.md` and `docs/adrs/README.md`, the `Next free number: **NNNN**` line exists and is greater than every number in use in that directory, `done/` included (plan 0053) | those two indexes |

An error rule listed in `DEMOTED` in `tools/gate.py` is reported as a warning until the files it flags are fixed; the
entry that will fix them is named beside the set. Today: E14, until the reverser's six findings rows land (plan 0053).

Warnings (fast tier):

| # | Heuristic | Applies to |
|---|---|---|
| W1 | A table row, or a list item or paragraph (with its wrapped lines), carrying `[C]` or `[I]` has no anchor of any kind; a bare `0x00XXXXXX` address counts as an anchor | specs, findings |
| W2 | A table with a `Tag` column has a row whose tag cell is empty | specs, findings |
| W3 | A `re/symbols.csv` row whose name appears in no spec or finding (plans and the backlog don't count) | `re/symbols.csv` |
| W4 | A `based_on:` date is older than that spec's `updated:` date (the page may be stale) | `docs/wiki/` |
| W5 | The frozen archive holds an unstruck entry, or a struck copy of an entry that has its own file. A warning, not an error, so that a lane merge appending to the archive leaves `main` green; the orchestrator then runs `python3 -I tools/backlog.py archive`, which migrates first | `docs/backlog.md` |
| W6 | A closed entry (`done`, `moved`, `dropped`) still in `docs/backlog/` instead of `docs/backlog/archive/` (ADR-0019). A warning, so that a lane merged from an older branch, which closed the entry in place, leaves `main` green; the orchestrator then runs `python3 -I tools/backlog.py archive` | `docs/backlog/*.md` |
| W7 | A table row whose first cell is `Total` or `All` (any case, bold allowed): each numeric cell (spaces, no-break and narrow spaces and commas as digit separators) equals the sum of the numeric cells above it in that column, back to the separator row or the previous such row; a non-numeric cell is skipped (plan 0053) | specs, findings, plans |

Full tier (`--full`): each registered `survey` ends with one `SURVEY <tool> key=value …` line of
integer counts, compared with `tools/gate/baselines/<tool>.txt`. Any difference is an error. A
missing `workspace/` is `SKIPPED`, which isn't a failure unless `--require-workspace` is given. A
baseline changes only in the commit that changes the parser, and the reason goes in the message.

The gate proves that anchors resolve, not that claims are right. It never replaces the review.

## What never counts as evidence

- A function *name* from a community offset list (it's a lead until we read the code).
- Agreement with D2MOO or any decompiled third-party source. We don't read those (ADR-0001).
- "It's obvious."
