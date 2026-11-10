# Clean-room ledger: S2 drops, re-run on fixed specs (plan 0064 Phase 5)

| Key | Value |
|---|---|
| Slice | S2 drops, fields `chain.G1.*` |
| Date | 2026-11-10 |
| Sandbox | `workspace/cleanroom/S2r/` (implementation `work/drops.py`, Python, reads `data/global/excel/*.txt`) |
| Specs read | `specs/conformance/README.md`, `formats/golden-trace.md` (§ Case, § Fields, § Conventions, § Checking), `specs/rng/README.md`, `specs/items/tc.md` (whole), `specs/items/quality.md` (whole), `specs/data/excel.md` § C to G; table docs `TreasureClassEx`, `ItemTypes`, `Weapons` (row identity only), `tables/README.md` (counts) |
| First pass | `cleanroom: slice S2 run 1 (first pass): 32320 fields compared, 0 different, 0 cases missing` |
| Final | same as first pass (no second run) |
| Per prefix, first pass = final | `chain.G1.count` 4040 compared 0 different; `chain.G1.end_seed` 4040 / 0; `chain.G1.item` 4040 / 0; `chain.G1.nodrop` 4040 / 0; `chain.G1.pick` 4040 / 0; `chain.G1.quality` 4040 / 0; `chain.G1.select` 4040 / 0; `chain.G1.subtc` 4040 / 0; `golden: pass` |
| Runs of `score.sh` | 1 |
| Pre-score self-checks | the two worked examples of items/tc (seeds, picks, items, counts), the three of items/quality (codes and exit seeds) and the NoDrop example (10, 20) reproduced before the first score run |

No prefix mismatched on the first pass, so every row below is a place where I had to guess or fill a gap, with
whether the guess was exercised by the set.

| # | Slice | Case kind | Field or spec section | What was missing or ambiguous | What you guessed | Pass |
|---|---|---|---|---|---|---|
| 1 | S2 | observed drop | data/excel § G4; items/tc § A (entry layout), § H4 | For a cell resolved as UNIQUE i or SET i, the entry's `index` word (the base item that H6/H7 and the `chain.G1.item` base read) is not stated; only `aux` (the record index) and the flags are | base = the item index of the unique's `code` (set item's `item`) column | yes (not exercised: only `ROP (N)`/`ROP (H)` hold `Annihilus`, no case reaches them) |
| 2 | S2 | observed drop | data/excel § G3–G4 | Whether a TC cell may name a TC defined later in the table: G4 does `FindName` at parse time, but the spec does not say forward references miss | lookup sees only TCs already allocated (a forward name falls through to unique, set, then is dropped); a sub-TC's "own totalClassic" (A2) is its value at that moment | yes |
| 3 | S2 | observed drop | items/quality § B S2; Tables row (`ubercode`/`ultracode` "same offsets in Misc") | `misc.txt` has no `ubercode`/`ultracode` columns; what the record holds there is not stated | blank, so no misc base is uber (moot anyway: S2 also needs `weap`/`armo`) | yes |
| 4 | S2 | observed drop | items/quality § B S1; ItemTypes `Class` | The `.txt` cell is a class code (`pal`, `nec`, `sor`…), the spec gives the byte as a playerclass row index | mapped by the S1 note's list (ama 0 … ass 6), blank → `0xFF` → `cls` 0 | yes |
| 5 | S2 | observed drop | data/excel § C2; Weapons § Row identity | Working from `.txt` rather than `.bin`: how to recognise the `Expansion` marker row in each table | skipped the row whose name column is `Expansion` (itemtypes, weapons, armor, misc, uniqueitems, setitems); TreasureClassEx has none | yes |
| 6 | S2 | observed drop | items/tc § K, Open questions (equivalence walk form) | Depth of the `Equiv1`/`Equiv2` walk, cycles, and whether record 0 enters the set are open | full transitive closure with a visited set, record 0 included (blank reference) | yes |
| 7 | S2 | observed drop | golden-trace § Drop cases (`players`, `party`, `cap`) | An absent value is "read by nothing", but an implementation still needs a value to pass to F | defaults `players` 1, `party` 1, no cap; F only runs when NoDrop ≠ 0, which is exactly when the inputs are present | yes |
| 8 | S2 | observed drop | items/tc § H7 (`if unit = none: return`) | When `DropCreateItem` returns none (and whether a `CPRE` line is still logged) is not specified | creation never fails on stock data: every hand-off is an item and increments `count` | yes |
| 9 | S2 | observed drop | items/tc § D1, golden-trace § Drop cases (`max`) | The object-source cases carry `max` 6 and the spec says objects pass an output array; with `max` 0 the rule is `max ← 6` | `max < 1 → 6`, else the given `max` (same 6 either way here) | yes |
| 10 | S2 | observed drop | items/tc § H4, golden-trace (`fq`) | A forced quality is listed in `chain.G1.quality` per the format note, but no case has `fq` ≠ 0 | listed the forced code, no roll | yes (not exercised) |
| 11 | S2 | — | links in the sandbox specs | Many anchors point outside the sandbox (`../../findings/…`, `../../plans/0059…`, `re/types/*.h`, `tools/golden.py`, backlog entries): dead links under the rules | not followed; none was needed for S2 | n/a |

## Notes

- No change was made after the first pass, so no row is "guessed from the diff".
- No read outside the sandbox was made; the only write outside it is this ledger.
