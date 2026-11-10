# Clean-room ledger: S1 (seeds), Phase 5 re-run

- **Slice:** S1 seeds, fields `chain.A*`, `chain.B*` (measured on `chain.B1.*`, `chain.B2.*`)
- **Date:** 2026-11-10
- **Sandbox:** `workspace/cleanroom/S1r/` (implementation `impl/s1.py`, candidate `impl/candidate.jsonl`)
- **Runs of `score.sh`:** 1 (the first pass is the final run; no change after it)
- **First pass (per-prefix lines as printed):**
  - `chain.B1.level_seed_base.N             3123 compared      0 different`
  - `chain.B2.level_seed.N                 53256 compared      0 different`
  - `chain.B2.level_seeds_digest             612 compared      0 different`
  - total: `cleanroom: slice S1 run 1 (first pass): 62035 fields compared, 0 different, 0 cases missing`
- **Final:** the same lines (run 1).
- Other prefixes on the first pass: `chain.A1.*` 649/649, `chain.A2.*` 612/612, `chain.A3.*` 649/649, `chain.A4.*` 612/612, all 0 different.

Specs read: `specs/conformance/README.md`, `formats/golden-trace.md` (§ Case, § Fields, § Conventions, § Checking),
`specs/rng/README.md`, `specs/rng/seeds.md` (§ Algorithm steps 1–4, step notes 1–4, § Worked example, § Reimplementation
notes), `specs/chain/README.md` (§ Algorithm A–B, § Worked example 1). Before scoring, the code reproduced the rng worked
example (row 1), the seeds worked example (`-seed 34844169`: base `FFFFFF87`, level 134 `0000000d:0000029a`) and chain
worked example 1 (`-seed 4802`: A3, A4 quest, level 57).

No prefix mismatched on the first pass, so every row below is a place I guessed or had to read between sections.

| # | Slice | Case kind | Field or spec section | What was missing or ambiguous | What you guessed | Pass |
|---|---|---|---|---|---|---|
| 1 | S1 | predicted | `chain.A2.monster_regions_seed`, `chain.A4.store_seed`, `chain.A4.quest_seed`; chain § Algorithm A2–A4 | A2 says "game draw 1 → monster regions: Init(low)" and A4 "game draw 3 → store seed" without `Init(low)`; whether the field is the raw game seed after the draw or `Init(low)` of it is not said for A4, and golden-trace § Fields says only "A4 game draws 3 and 4". Also not stated outright that no other consumer steps the game seed between draws 1 and 4 | every A2–A4 seed field is `Init(low of game seed after that draw)` (high 666), draws 1–4 consecutive; confirmed by chain § Worked example 1 (A4 values end in `0000029A`) | yes |
| 2 | S1 | both | `chain.A3.game_seed_after`, `chain.A4.game_seed_after_creation` | whether "game seed after" is the raw game seed (low:high) or an Init form | raw game seed state after draw 2 / draw 4; matches chain § Worked example 1 (`615B8C46:5DB3A30E`) | yes |
| 3 | S1 | predicted | `chain.B1.level_seed_base.N`; golden-trace § Conventions (act index), rng/seeds step note 3 | a predicted case holds all five acts, classic too; the spec never states Act V (expansion-only) is created in a classic game | emit the same `levelSeedBase` for acts 1–5 regardless of `expansion`, from rng/seeds step note 3 ("all acts share the same levelSeedBase") and § Conventions ("classic games too") | yes |
| 4 | S1 | both | `chain.B2.level_seed.N`, `chain.B2.level_seeds_digest`; golden-trace § Conventions (digests' level set) | the brief names data/excel (Levels) as a needed spec, but the digest's level set is fixed by § Conventions as 1–136 rather than derived from the table; `levels.txt` has 138 data rows (Id 0 to 136 plus one more) | took the level set 1–136 from § Conventions without reading `specs/data/excel.md`; the Levels table was not needed for S1 | yes |
| 5 | S1 | both | `chain.A1.*`; rng/seeds steps 1–2, step note 2 | the cases give `seed` as an int; the spec's override branch applies only to `1…0x7FFFFFFF` (0 takes the clock path) | all case seeds were in 4801–12345, so the override branch applies to every case; no handling for 0 or out-of-range seeds was needed | yes |
| 6 | S1 | — | dead links: conformance README → `formats/golden/sample-v1.jsonl`, `../../plans/0059-golden-traces.md`; rng, seeds, chain → `../../findings/...` | these targets are not in the sandbox | not followed; nothing in the slice depended on them | n/a |
