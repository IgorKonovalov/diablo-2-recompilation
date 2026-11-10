---
from: architect
to: archivist
date: 2026-11-10
status: open
context:
  - ../plans/0064-clean-room-test.md#implementation-log
  - ../plans/0064-cleanroom/S1.md
  - ../plans/0064-cleanroom/S2.md
  - ../formats/golden-trace.md#fields
resolution: ""
---

**Format defect (plan 0064 P3 triage): fmt:golden-trace leaves the field and input conventions to `tools/golden.py`.** Both clean-room implementers guessed these right, but from the code's output, not a sentence; write each one into the format doc from `tools/golden.py` (world_expected, drop_case, canon, value_digest). World (S1 rows 2–5): (a) `.N` of `chain.B1.level_seed_base.N` is the act number 1 to 5, not rng/seeds' 0-based actIndex; (b) which acts and levels a case holds (predicted: five acts, classic too; observed: what the log shows), and that `check` compares only the expected fields, so extra candidate fields are not counted (§ Checking); (c) the level set of `chain.B2.level_seeds_digest` and `monsters.pool.digest` (`golden.py`: every level with a non-zero seed, resp. every level of the model's list; name the ids) and the digested object's form: decimal-string keys, `low:high` lower-case values, canonical JSON (sorted keys, `,` `:`, ASCII), sha256 lower-case hex. Drop (S2 rows 1, 4–10): (d) `nodrop`: one entry per positive-picks pick (the `NDP` line at 0x0055A9D9, where every positive pick joins, `noNoDrop` included?), value the NoDrop after F's scaling, and `[0, total]` when the TC's NoDrop is 0; "per roll" and the link to items/tc § F alone read as one entry per `ScaleNoDrop` call, which cost S2 1 113 first-pass mismatches; (e) `pick`: the raw `Range` result before `− nd`, positive picks only; (f) `select`: NoDrop picks left out, negative picks in, an off-the-end index recorded; (g) `subtc`: the top TC excluded, entered sub-TCs' indices in push order; (h) `quality`: one entry per `DropRollQuality` call (`QOUT`), refunded classic throwables included, forced and unique/set qualities not; (i) input `tc` is the resolver's `t0` after the level upgrade (no C1–C2 upgrade to apply); (j) what an absent `players`/`party`/`cap` means (when the logger prints them) and the default a reimplementation uses; (k) `g6a` is `Game+0x6A` (items/tc *Runtime state*), and which inputs are context only (`game_seed`, `killer_class`, `source_class`…). Check each against the logger (`tools/gdb/tc-drops.gdb`) and the code before writing it. S3 and S4 use (b) and (c); land at least those before their clean-room runs.
