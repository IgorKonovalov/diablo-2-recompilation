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

Data-format claims follow the same scheme. A field layout is `[C]` once a parser reads every file
of that type without error *and* the decoded values make sense, or once the code that reads the
field is anchored.

## Anchors

```
0x0045A1B0                         address in pinned Game.exe (8 hex digits, 0x-prefixed)
fn:RNG_Next@0x0045A1B0             named function (name must exist in re/symbols.csv)
data:g_pLevels@0x0096C888          named global (kind `data` in re/symbols.csv)
struct:Unit+0x14                   field offset in a type from re/types/
tbl:TreasureClassEx.txt:Picks      table column
fmt:ds1#header.version             format doc field
run:2026-10-12-rng-seq             experiment record in docs/findings/<subsystem>/experiments.md
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

Record each one in `docs/findings/<subsystem>/experiments.md`:

```
## run:YYYY-MM-DD-slug
- Question: …
- Setup: wine prefix, save file, seed control method, tool versions
- Procedure: numbered steps
- Observed: raw output (trimmed)
- Conclusion: which claims this upgrades, by finding link
```

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
under `docs/findings/`.

Errors (fast tier):

| # | Rule | Applies to |
|---|---|---|
| E1 | `fn:Name@0x…` and `data:Name@0x…`: the name exists in `re/symbols.csv`, its address equals the cited one (case-insensitive hex), and `fn:` names a `func` row, `data:` a `data` row | specs, findings |
| E2 | `src:<id>` exists as an id in the `docs/sources.md` table | specs, findings, formats, tables |
| E3 | `run:<id>` exists as a `## run:<id>` heading in some `docs/findings/*/experiments.md` | specs, findings |
| E4 | `tbl:<File>.txt:<Col>`: `docs/tables/<File>.md` exists (file name compared case-insensitively, as the game does). `fmt:<name>#…`: `docs/formats/<name>.md` exists. `struct:<Type>+0x…`: `<Type>` is declared in a `re/types/*.h` | specs, findings |
| E5 | `[L]` in a spec appears only under the `## Open questions` heading | specs |
| E6 | A spec's front-matter `tags: {C: n, I: n, L: n}` equals the counts of `[C]`, `[I]` and `[L]` in its body | specs |
| E7 | `re/symbols.csv` has the header `address,kind,name,signature,confidence,subsystem,evidence`; `address` matches `0x00[0-9A-F]{6}` and lies inside the image; `kind` ∈ {`func`, `data`}; `confidence` ∈ {`C`, `I`, `L`}; `evidence` is an existing path; no duplicate address and no duplicate name | `re/symbols.csv` |
| E8 | A relative markdown link resolves to a tracked file, and a `#fragment` matches a heading slug in it (GitHub slug rules) | every tracked `.md` |

Warnings (fast tier):

| # | Heuristic | Applies to |
|---|---|---|
| W1 | A line or table row carrying `[C]` or `[I]` has no anchor of any kind | specs, findings |
| W2 | A table with a `Tag` column has a row whose tag cell is empty | specs, findings |
| W3 | A `re/symbols.csv` row is cited by no doc | `re/symbols.csv` |

Full tier (`--full`): each registered `survey` ends with one `SURVEY <tool> key=value …` line of
integer counts, compared with `tools/gate/baselines/<tool>.txt`. Any difference is an error. A
missing `workspace/` is `SKIPPED`, which isn't a failure unless `--require-workspace` is given. A
baseline changes only in the commit that changes the parser, and the reason goes in the message.

The gate proves that anchors resolve, not that claims are right. It never replaces the review.

## What never counts as evidence

- A function *name* from a community offset list (it's a lead until we read the code).
- Agreement with D2MOO or any decompiled third-party source. We don't read those (ADR-0001).
- "It's obvious."
