# Object experiments

## run:2026-10-14-objects-window

- **Question:** (plan 0023 Phase 1) Does the slot loop of [objects/0001](0001-object-population.md), written from the
  code, account for every room-seed draw of the objects window (`RW3` → `RW4`) in the logs already on disk? Does the
  inactive-unit restore draw nothing on a first activation (`RW2` → `RW3`)?
- **Setup:** no new game run. This is a re-analysis of 22 existing logs from three earlier runs, all written by
  `tools/d2run.py` under the ADR-0003 harness:
  - run:2026-10-13-mon-spawn: `workspace/logs/monspawn-s1-12345-normal-a1.log`, `monspawn-s2-12345-normal-a2-5.log`,
    `monspawn-s3-1-hell-a1.log`
  - run:2026-10-14-collision: `workspace/logs/collision-s1-2026-normal.log` … `collision-s7-2026-normal-a1.log` (7 logs)
  - run:2026-10-14-mon-special: `workspace/logs/monspecial-s1-2101-normal.log` … `monspecial-s12-2112-nightmare.log` (12 logs)

  Their loggers (`mon-spawn.gdb`, `collision.gdb`, `mon-special.gdb`) all write `RW0`..`RW4`: the room seed `rs` and
  game seed `gs` (`low:high`) after each out-of-scope call of `sub_0052D160_NewRoomsUpdate`, with the room's level id.
  `RW2` follows the preset units, `RW3` the inactive-unit restore and `RW4` the object population. Tables:
  `levels.bin`, `objgroup.bin` and `objects.bin` from `workspace/merged/data/global/excel`. Checker:
  `tools/objects.py` (sha256 prefix `ed5077d5d9d284a6`).
- **Procedure:**
  ```
  L=workspace/logs
  python3 -I tools/objects.py window $L/monspawn-s1-12345-normal-a1.log $L/monspawn-s2-12345-normal-a2-5.log \
      $L/monspawn-s3-1-hell-a1.log $L/collision-s[1-7]-*.log $L/monspecial-s[0-9]*-*.log -v
  ```
  The model is in the docstring of `tools/objects.py`. Three things in the window are unknown to the logs: the
  placement attempts of the shrine and well handlers, their caps, and the gate and forced-shrine state. The checker
  enumerates them and requires that exactly the logged `RW4` room seed is reached. A room is "exact" when no unknown
  besides the gate was needed.
- **Observed:**
  ```
  objects-window: logs=22 rooms=2090 restore_checked=2090 restore_moved=0 closed=685 closed_town=222 exact=915
  branched=490 forced=3 fail=0 slot_passes=2307 member_none=259 shrine=420 well=359 trap=35 init46=24 other_handlers=1210
  FORCED monspecial-s10-2110-hell.log 44024832 76
  FORCED monspecial-s10-2110-hell.log 44024704 76
  FORCED monspecial-s1-2101-normal.log 56248448 4
  ```
  - 2090 first activations. The inactive-unit restore left the room and game seed unchanged in all 2090.
  - 685 windows drew nothing: 222 in towns, 463 in levels with object groups (gate closed).
  - 1405 windows drew, and each one is accounted for:
    - 915 with no unknown: 8 slot draws, plus one pick draw per passing slot, plus one draw per trap handler.
    - 490 that needed the placement-attempt or cap unknowns of the shrine and well handlers, or InitFn 46's
      monster draws (24 picks of object 369, City of the Damned).
  - 2307 slots passed. 259 of them picked no member, because the draw was at least the members' `PROB` sum.
  - 3 windows only fit with the forced rule: `r = 100` on slots whose group index names an Objects row with
    `SubClass ≠ 0`, in Spider Forest (2) and Stony Field (1).
  - A first version of the model without that rule failed exactly these 3 rooms, plus 6 rooms of City of the Damned
    (InitFn 46) that the wildcard now covers.
- **Conclusion:** this upgrades the following claims of [objects/0001](0001-object-population.md) to confirmed for the
  room seed (this is a bit-exact check of the room-seed draw sequence; the object-region seed is not logged):
  - the slot loop: draw, comparison, group 0, member pick, sum below 100;
  - which handlers draw the room seed (2, 8, 9) and which do not (1, 3, 4, 5, 6, 7);
  - the trap handler's single draw;
  - the shape of the shrine and well draws (`1 + 2a`);
  - closed town windows;
  - the forced-slot rule as an outcome;
  - the restore's "no draw" on a first activation.

  What stays inferred: placement positions, the object-region draws, the trigger of the forced rule and the gate
  conditions other than town. Raw logs: the 22 files above. No new log was written.
