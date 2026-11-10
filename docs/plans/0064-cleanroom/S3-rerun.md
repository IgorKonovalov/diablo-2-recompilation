# Clean-room ledger: S3 (pools), Phase 5 re-run

- **Slice:** S3 pools, fields `monsters.pool.*` (612 predicted `world` cases)
- **Date:** 2026-11-10
- **Implementation:** Python, reading the `.bin` tables (`levels`, `monstats`, `monstats2`) at the offsets of
  monsters/pool § Inputs; RNG from rng § Algorithm; game seed from rng/seeds step 1 (override branch).
- **Runs of `score.sh`:** 1
- **First-pass line:** `cleanroom: slice S3 run 1 (first pass): 211140 fields compared, 0 different, 0 cases missing`
- **First-pass per prefix (as printed):**
  ```
  monsters.pool.den.N                   52632 compared      0 different
  monsters.pool.digest                    612 compared      0 different
  monsters.pool.mlvl.N                  52632 compared      0 different
  monsters.pool.region.N                52632 compared      0 different
  monsters.pool.uniques.N               52632 compared      0 different
  ```
- **Final line:** same as the first pass (no second run).
- **Guesses needed:** none that the scored fields depend on. Before the first pass the model was checked only
  against monsters/pool § Worked example (seed 1, Normal: pools of levels 1 to 3, `monDen`, `monUMin`/`monUMax`,
  `monLvl` and the `R` seed after each level all matched the spec's values).

| # | Slice | Case kind | Field or spec section | What was missing or ambiguous | What you guessed | Pass | Triage (P5 close) |
|---|---|---|---|---|---|---|---|
| 1 | S3 | predicted world | monsters/pool § Inputs, § Evidence; conformance § Which spec section; golden-trace § Fields | Links to `findings/`, `plans/`, `inventory.md`, `re/types/` and `tools/` point outside the sandbox (dead). None was needed: the spec text and tables doc gave every offset and rule used | nothing; not followed | yes | implementer error, no defect: dead evidence links are the sandbox by design (ADR-0032), as in Phase 2; no entry |
| 2 | S3 | predicted world | monsters/pool § D, step D1 | The out-of-range rule for `MonStatsEx` is given only as `[I]` (`< 0` or `≥` count); spec says stock data never reaches it and any rule may be used | used `i2 < 0 or i2 ≥ nMonStats2` as written | yes (not exercised) | missing finding (unreached): D1's rule is `[I]` and stated; the getter's own test is open in [monstats2rec-bound-test](../../backlog/2026-11-10-spec-writer-reverser-monstats2rec-bound-test.md); no new entry |
| 3 | S3 | predicted world | monsters/pool § D, step D2 | `cap: i32 ← (1 << (x & 31)) − nVariants`: with `x & 31 = 31` the shift would overflow i32; the spec types it i32 but does not say so for that case | wrapped to i32 (negative cap → no sets). Stock `+0x025` values never give 31 after `& 31` (max 49 → 17) | yes (not exercised) | implementer error, no defect: D2 types `cap` i32; no stock record reaches `& 31` = 31 (largest 17); no entry |
| 4 | S3 | predicted world | MonStats table, "`+0x00F` bit 4", "`+0x00C` bit 0" | Bit numbering of the flag bytes is not restated in the pool spec | LSB-0 byte masks (`0x10`, `0x01`), as monsters/pool § E's boss note (`+0x00C & 0x40` for bit 6) implies; not a real guess | yes | implementer error, no defect: the masks follow § E's notation, as the row says; no entry |

No prefix mismatched on the first pass, so there are no mismatch rows.
