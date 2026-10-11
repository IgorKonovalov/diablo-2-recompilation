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

Data-format claims follow the same scheme. A field layout is `[C]` once a parser reads every file
of that type without error *and* the decoded values make sense, or once the code that reads the
field is anchored.

## Anchors

```
0x0045A1B0                         address in pinned Game.exe (8 hex digits, 0x-prefixed)
fn:RNG_Next@0x0045A1B0             named function (name must exist in re/symbols.csv)
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

## What never counts as evidence

- A function *name* from a community offset list (it's a lead until we read the code).
- Agreement with D2MOO or any decompiled third-party source. We don't read those (ADR-0001).
- "It's obvious."
