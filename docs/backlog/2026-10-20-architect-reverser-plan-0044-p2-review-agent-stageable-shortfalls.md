---
from: architect
to: reverser
date: 2026-10-20
status: open
context:
  - ../plans/done/0044-multiplayer-branches.md#implementation-log
  - ../findings/multiplayer/experiments.md#run2026-10-20-two-clients
resolution: ""
---

Out of plan 0044 (Phase 2 review, 2026-10-20), for a later two-client run when both slots are free; none blocks Phase 3. (1) drivers/ufwcheck.sh must exit non-zero on a change (today it always exits 0, and its Policy="ACCEPT" pattern misses the upper-case line); keep it in tools/ next time, not only in the run's drivers. (2) Agent-stageable shortfalls: MP18 (a recipe with a rune and a socketed item for the joiner), MP21 (plan 0040's lifecycle logger merged into a two-client logger), MP27 (a QuestFlag portal session), MP28 (b) and (c) (a pilot route that reaches every Den room), MP30 (an e9/e10 line in quests.py), MP25's offensive auras (a recipe with an 0x8000 aura), MP20's per-player room attribution, MP16 kills just inside d2 6400; MP31 and MP32 need their predictions written first (Phase 1 ruling d). (3) combat.py --no-shield is hand-fed from the recipes; a logged shield flag on the defender would make it a check. (4) Added at the plan 0044 close (Phase 3 review, 2026-10-20): the plan 0047 case logged in plan 0044 after its run, open wounds on a player (stat 135 comes only from item properties, so only a hostile player wounds a player): player B, hostile, wearing an open-wounds item (tool-built, ADR-0013 Neutral), hits player A; the stats logger's state and tick lines on A ([plan 0047 log](../plans/done/0047-simulation-shortfalls.md#implementation-log)).

2026-10-20, reverser (`lane/mp26`): (1) done statically. `tools/ufwcheck.sh <session> <baseline> <log>` is the fixed successor of `drivers/ufwcheck.sh` (the run copy is kept unchanged, manifest hash `47c1d42d…`): it exits 1 with `UFW-CHANGED` unless ufw is active and enabled, the line is exactly `DEFAULT_INPUT_POLICY="DROP"`, `ENABLED=yes` and every baseline hash checks, and exits 2 on a missing argument or baseline; it reads only the input-policy line (the unchanged file also holds `DEFAULT_OUTPUT_POLICY="ACCEPT"`). Self-test in `workspace/logs/mp26/check-mp26.txt` § C ([experiments](../findings/multiplayer/experiments.md#run2026-10-20-two-clients), the precondition). (2)–(4) stay open: they need both harness slots.

*2026-10-25 (reverser, `lane/p51r`, [plan 0051](../plans/0051-backlog-sweep-6.md) Phase 1a, no slot, no game):*
**Staged:** MP18, MP25's offensive auras, MP30 and the open-wounds pair. MP31 and MP32 go to Phase 1b. The rest
stays with the two-client run.
- **MP18:** recipe `tools/d2s_recipes/mp-sock-join.json` (MpSockJoin: level 30, a `cap` with 2 empty sockets and the
  runes `r01`, `r02`); pair MP18 in `tools/mp_saves.py` (host MpNovaHost); logger `tools/gdb/two-sockets.gdb` (pilot,
  two-players, `sockets.py`; host side). The prediction is the one in multiplayer/0001 § 2: no INSX and no error 3.
  If no PKT `0x28` line appears, MP18 is a shortfall (Phase 1 ruling e).
- **MP25, offensive auras:** recipe `mp-pal-conv.json` (MpPalConv, a Paladin at level 30: Conviction on the right
  button, Holy Fire, Holy Shock, Holy Freeze and Might on hot keys); pair "MP25 offensive" (host MpNovaHost, hostile).
  Logger `two-combat.gdb` as pal-1. `mp_check.py aura` already models `0x8000` (passes iff the pair is hostile). The
  prediction is multiplayer/0001 § 4's, with its stated gap: `0x80`/`0x400` need the target's `+0xC4` bits 2 and 3,
  which are not read.
- **MP30:** `tools/gdb/quests.py` gains, as tags only, QL0 (`0x00543BD0` entry, the leaving player), QE9 (`0x00543C87`,
  each e9 callback call: quest object, callback, item, player), Q4B/Q4C (the `bks `/`bkd ` callback `0x00592C80`: its
  `+0x7C` count before and after the code test), Q4R (`0x00592CDC`, the reset call), QE10 (`0x00543CA2`, the e10
  dispatch), QLR (`0x00545240` entries while a leave is open) and QL1 (`0x00543CA7`). Checker `mp_check.py leave`
  checks the order (the player's own QE9 lines, then one QE10, then QL1) and the count (−1 exactly for `bks `/`bkd `,
  unchanged otherwise). It counts, without predicting, the list removals, the resets and the quest-bit writes inside a
  leave. Pair MP30 is unchanged (MpScrollJoin, `two-quests.gdb`).
- **(4) the open-wounds pair:** recipe `mp-wound-join.json` (MpWoundJoin: level 30, strength and dexterity 150,
  *Ripsaw* equipped: `openwounds` 80, stat 135 on the built item); pair "open wounds" (host MpPvpHost, life 8000,
  hostile). Logger `tools/gdb/two-wounds.gdb` (pilot, two-players, `combat.py`, `stats.py`). Checks: `combat.py check`
  (its open-wounds handler and the windowed stat-74 ticks), `stats.py check`, `mp_check.py gates`. Expected
  (stats/0002, `[I]`): state 62 for 200 frames per application, and a life tick that adds the negative stat 74 but
  never takes life below 1. The joiner's melee clicks are the run's driver steps, as `meleeJ.steps` was for pvp-1.
  `combat.py` and `stats.py` have not run in one gdb before. The session's first minutes show whether the two
  coexist.
- **Tests:** `mp_saves.py check` gives 30 recipes and 21 pairs, 0 bad. The three new recipes pass their own conditions,
  and MpPvpJoin fails each. `test_p51_staging.py` covers `mp_check.py leave` on synthetic good and bad leaves. gdb
  parses and arms `two-sockets.gdb`, `two-wounds.gdb`, `two-quests.gdb` and `quests.gdb` against the pinned image.
  `mp_check.py leave` on the kept qjoin-1 host log reports 0 leaves (that log predates the lines). Outputs:
  `workspace/logs/p51r/`.
- **MP31, MP32 → plan 0051 Phase 1b** (new readings): items/0011 names `sub_00540900_PartyGoldShare` ("a split by
  `PartyCount`") without its arithmetic, and the player-to-player trade is not read. Neither prediction can be written
  from the findings.
- **Still open for the two-client run (both slots):** (2) MP16, MP20, MP21, MP27, MP28 (b), (c); (3) the shield flag
  for `combat.py --no-shield`; and the sessions of everything staged above. The entry stays open.
