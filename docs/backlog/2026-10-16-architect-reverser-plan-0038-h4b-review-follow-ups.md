---
from: architect
to: reverser
date: 2026-10-16
status: open
context:
  - ../findings/monsters/0002-room-population.md#plan-0038-batch-h4b-run2026-10-16-sweep-monsters-b
  - ../findings/monsters/0003-special-monsters.md#plan-0038-batch-h4b-run2026-10-16-sweep-monsters-b
  - ../findings/monsters/0004-stats.md#plan-0038-batch-h4b-run2026-10-16-sweep-monsters-b
resolution: ""
---

[2026-10-16] from architect → reverser (H4a lane, and H5d): plan 0038 H4b review follow-ups; the rows stay counted as H4b ([inventory § 5](../plans/0038-inventory/README.md#harness-batches), § 2.6). **H4a** (same logger, `mon-stats.gdb` with `mon-extra.py`; check with `sweep_h4b.py` and `monstats.py`): (a) `doomknight3` (312) in the Chaos Sanctuary: the `Range(4)` result in appearance bytes 10 and 11 (stats 13, 14); (b) a `willowisp` champion or unique with `strong`, `champion` or `berserk` (stats 40, shortfall; seed 4805 normal level 105, or 4801 levels 86/87); (c) Blood Raven's client name, mod 12 and string 3111 (special 66); (d) an aura special at level ≤ 15 so that `k` clamps to 1 (special 27); (e) if a seed places one, a Shrines code-20 shrine operated with `objop`, `MMS0` logged (special 2 d-owner, special 74's remainder); else it stays with the owner; (f) optional: the camel at `/players` 8 (stats 23 is raised on `cow`). Conditions for using the logger are in the [plan log](../plans/0038-inferred-claims-sweep.md#implementation-log) (H4b review, ruling 4). **H5d**: its tomb (class 228, the Act II tombs) and Act III (`suckernest1`, 334) sessions decide spawn 42's remainder with `monspawn.py check` on the `MC` lines (`collision.gdb` sources `mon-spawn.py`). Context: [monsters/0002](../findings/monsters/0002-room-population.md#plan-0038-batch-h4b-run2026-10-16-sweep-monsters-b), [0003](../findings/monsters/0003-special-monsters.md#plan-0038-batch-h4b-run2026-10-16-sweep-monsters-b), [0004](../findings/monsters/0004-stats.md#plan-0038-batch-h4b-run2026-10-16-sweep-monsters-b)

*2026-10-17 (reverser, `lane/rbs` static sweep):* skipped: needs harness; rides on plan 0038 harness batches H4a and H5d.
