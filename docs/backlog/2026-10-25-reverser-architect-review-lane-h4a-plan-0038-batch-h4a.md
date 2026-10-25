---
from: reverser
to: architect
date: 2026-10-25
status: open
context:
  - ../plans/0038-inferred-claims-sweep.md#implementation-log
  - ../plans/0038-inventory/README.md#26-moves-made-by-the-batch-reviews
  - ../findings/monsters/experiments.md#run2026-10-21-sweep-monsters-a
  - ../findings/monsters/0001-level-pool.md#plan-0038-batch-h4a-run2026-10-21-sweep-monsters-a
  - ../findings/monsters/0002-room-population.md#plan-0038-batch-h4a-run2026-10-21-sweep-monsters-a
  - ../findings/monsters/0003-special-monsters.md#plan-0038-batch-h4a-run2026-10-21-sweep-monsters-a
  - ../findings/monsters/0004-stats.md#plan-0038-batch-h4a-run2026-10-21-sweep-monsters-a
  - ../findings/items/0010-quest-drops.md#plan-0038-batch-h4a-run2026-10-21-sweep-monsters-a
resolution: ""
---

Review plan 0038 batch H4a (`monsters-a`; monsters/pool, spawn, special, stats and items/quest-drops; `lane/h4a`),
run:2026-10-21-sweep-monsters-a. Twelve kept sessions on slot 1 (expansion Nightmare, `UniqNova`), nine development logs
in `dev/` (the Chaos Sanctuary attempts, raven-nowp); no log has `internal-error:`. Manifests
`workspace/logs/h4a/h4a-manifest.sha256` (logs, pilot outputs, `check/`) and `h4a-manifest-dev.sha256`, both
`sha256sum -c` from `workspace/logs/h4a`. Checks produced by `check/run-checks.sh` under `MemoryMax=4G`:
`sweep_h4a.py check` bad 0 in every part on the twelve logs (`sweep-check.txt`) and the 63 kept logs
(`check-kept-final.txt`); `monstats.py` 0 mismatches on all twelve (`monstats-h4a.txt`).

Ledger of the 32 statements: **raised 16, raised in part 8, shortfall 8** (inventory § 2.6 H4a block).

Points for the ruling:
- (a) **Lord De Seis not met.** chaos7 opened seals 392, 393, 395 and 396 (the Infector and the Vizier, tails 36 and
  38), logged seal 394 at (7773, 5155) but found no hop towards it (d 33, two objops). Special 9, 10, 25, 31, 38 and
  50's thief half, and spawn 11 (the closed gate), are filed as shortfalls with an owner-play route, as the resume
  note said to. Candidate for an owner session; not routed to d-owner by the lane.
- (b) **A wanderer roll fired** (chaos7, level 108): the tick's step left low `0xD17D0000`, `WRL` came on that seed,
  one more step, 82 ≥ 3, no further draw. `sweep_h4a.py wander` now models every tick (11 969 ticks over the 75 logs).
  spawn 47 is filed in part (the mask's width is not separated: 16 zero bits) and spawn 48 in part **with a
  correction** of its "never fired" note, against the inventory's expected shortfall.
- (c) **special 50/51 control.** Three superuniques with an extra-picked 30 (records 36, 42, 60) get one `AUR` and no
  second call; the fixed-30 record (28) gets two (`check/aura-control.txt`). The fixed-30 side has one case in this
  batch's logs (two more on kept logs).
- (d) **Chained-model mismatches** on council (DRLG room tiles, 3), nihl2 (monspawn: Nihlathak's post-create mod 22
  missing from `monspawn.py`'s table for class 526) and chaos7 (collision bit `0x1000` at the two seal bosses'
  placement cells). None is on a tag these rows rest on; the earlier pause-time check (`monstats-h4a-part1.txt`) had
  been run with `--no-chain`, which is why they surface only now. Whether they need entries of their own is the
  review's call.
- (e) **H4b pieces met:** class 312's two `Range(4)` bytes (stats 14 and 13's remainder; 63 creations, all four values)
  and special 66's mod 12. The rows stay H4b's; the review may raise stats 14's remainder.
- (f) **stats 7, 18, 21** cite run:2026-10-20-chain's reviewed check (the routed creations were met there first); this
  batch re-ran `monstats.py` on those two logs only.
- (g) **Symbols:** `sub_005B24E0_EscortSpawn` I → C (rule 14). **Totals** against `main` `e3ac907` after merging it:
  no class move; static 567, harness 526, blocked 414, deferred 2, raised 17: 1 526.

Spec-writer entry filed: `2026-10-25-reverser-spec-writer-h4a-monsters-a-raises-and-the-spawn-48.md` (to be released
with the review). Not blocking.
