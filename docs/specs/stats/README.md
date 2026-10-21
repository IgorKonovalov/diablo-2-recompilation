---
spec: stats/overview
status: reviewed
target: Diablo II LoD 1.14d, Game.exe sha256 631066c1649c4ea9…
depends_on: [rng, rng/seeds, items/properties, items/uniques-sets, player/creation, monsters/stats, data/calc, combat/overview]
consumed_by: [combat/overview, player/creation, monsters/stats, data/calc, objects]
tags: {C: 16, I: 3, L: 3}
updated: 2026-10-21
---

# Stats and states: how a unit's stats add up, and how timed states live and die

## Purpose

Every unit carries a tree of stat lists: its own base entries, the lists of its equipped items (with their sockets
and set bonuses), and the lists of the states on it (curses, auras, potions, shrines, passives). This subsystem
specifies how the server keeps the **full value** of every stat of that tree in a cache, how the `ItemStatCost` `op`
derivations add terms to it, what the maxima are, which items count, how set bonuses switch on, and, for the states,
how a timed state is applied, refreshed, replaced, expired and cleared by group, how the per-frame regeneration tick
changes life, mana and stamina, and how auras, shrines and wells put states on a unit. It is phase (2) of
[ADR-0014](../../adrs/0014-scope-game-simulation.md); combat ([combat](../combat/README.md), phase 1) reads the values
this subsystem produces, and a skill's own effect is phase (3).

```mermaid
flowchart LR
  base["unit's own entries (+0x24)"] --> cache["unit list: full cache (+0x48)"]
  items["item lists (property, sockets, aprop)"] -->|"link / unlink"| cache
  sets["set bonus lists (states 165..170)"] -->|"link / toggle"| cache
  states["state lists (curse, aura, potion, shrine, passive)"] -->|"STATE_ApplyTimed / expiry"| cache
  ops["ItemStatCost op 1..13"] -.->|"re-evaluation of op-linked stats"| cache
  cache --> reads["every full read (combat, ticks, calc stat())"]
  tick["regeneration tick, every frame"] -->|"stats 6, 8, 10"| base
```

## Files

| File | Covers | Status |
|---|---|---|
| [aggregate.md](aggregate.md) | the list tree and the cache, propagation and recompute, `op` 1–13, the reads, the maxima and their rescale, item requirements and the equipment refresh, dual wield, set bonuses, passive stat lists | reviewed |
| [states.md](states.md) | the state bit and its list, the timed apply (curses, refresh, refuse, replace), expiry, removal, the `group` clear, the regeneration tick, auras, shrines and wells, the draws per event kind | reviewed |

Names of functions, structs and fields are ours ([stats/0001](../../findings/stats/0001-aggregate.md),
[stats/0002](../../findings/stats/0002-states.md), `re/types/stats.h`). `MulDiv(a, b, c)` is the helper of
[monsters/stats § A](../monsters/stats.md#a-muldiv-and-monlvlstats). Stat values are i32; life, mana and stamina are
in 1/256 points. A stat key is `stat << 16 | param`. Time is in game frames, the frame counter at `game +0xA8`.

## Entry points

| When | Function | Tag |
|---|---|---|
| A list is linked under a unit, or unlinked | fn:STATLIST_LinkToUnit@0x00626E10, fn:STATLIST_Unlink@0x006269F0 | [C] (run:2026-10-17-stats: 26 087 links and unlinks) |
| A list entry is added or set (any writer) | fn:STATLIST_AddStat@0x00627030, fn:STATLIST_SetStatEx@0x006270B0 → fn:STATLIST_Propagate@0x00626920 | [C] (run:2026-10-17-stats: 101 995 own writes) |
| A full stat is read | fn:sub_00624F60_StatListGetValue@0x00624F60 | [C] (run:2026-10-17-stats: 891 844 reads) |
| An item is equipped, unequipped, or the requirements are refreshed | fn:ITEMS_AttachToOwner@0x0055C2C0, fn:ITEMS_DetachFromOwner@0x0055C730, fn:sub_0055DBC0_EquipReqRefresh@0x0055DBC0 | [C] for the refresh (run:2026-10-17-stats: 972 refreshes); [I] for the attach and detach bodies |
| A timed state is put on a unit | fn:STATE_ApplyTimed@0x0056E970 | [C] (run:2026-10-17-stats: 3 643 applies) |
| A timed list's end frame is reached | fn:EVENT_TimedListExpire@0x00580800 | [C] (run:2026-10-17-stats: 2 749 runs) |
| A player's regeneration tick, every frame | fn:sub_00580810_RegenEvent@0x00580810 | [C] (run:2026-10-17-stats: 54 719 ticks) |
| An aura runs | fn:EVENT_SelectedAuraTick@0x0056FCB0, fn:EVENT_ItemAuraTick@0x0056FE40 | [C] (run:2026-10-17-stats: 3 629 runs) |
| A shrine or a well is operated | fn:OBJOP_Shrine@0x00583C70, `0x00585720` | [I] (15 operates over run:2026-10-17-stats and run:2026-10-20-shortfalls, a named shortfall) |

## The boundary (plan 0041 Phase 2)

| Kind | What | Tag |
|---|---|---|
| value oracles | a skill's own calc results where the formula reads unit state (data/calc's unit-reading variables); the shrine to-hit and damage values (`SHRINE_StatValue` cases 19 and 21); monster AI; the combat appliers that put a state on the player (poison, cold, open wounds) are inputs; the item's required level and the strength and dexterity the requirement check reads through `0x0062B450`, as the run record names them | [C] (run:2026-10-17-stats) |
| modelled inputs | the passive calcs, evaluated with the level the list records in stat 351 | [C] (fn:SKILLS_RefreshPassive@0x00646D60, run:2026-10-17-stats) |
| no remainder (since the 2026-10-20 re-check) | the 180 wearer set lists of the full Trang-Oul's Avatar (full blocks with a `state` and an `oskill` property), taken as logged at the run, are predicted by the kept checker: values stored `<< ValShift`, the `state` block writing stat 98 with param 176 and value 1, so all 5 749 wearer set lists are checked ([aggregate § J](aggregate.md#j-set-bonuses)) | [C] (fn:sub_00660120_SetBonusApply@0x00660120, fn:PROP_Func24_ParParam@0x0065F390, run:2026-10-17-stats) |

[C] Under this boundary run:2026-10-17-stats reproduced 18 sessions of six characters with 0 mismatches: every link,
unlink, propagation and cache write of the player's tree in order, every read in the 50-frame windows, the stat
callback and its rescale, the requirement checks, the set masks, toggles and lists, the passive lists, every apply,
expiry, tick, aura run and duration, and the shrines and wells reached. (run:2026-10-17-stats)

[C] Under the same boundary run:2026-10-20-shortfalls (plan 0047 Phase 2) reproduced 10 sessions with 0 mismatches,
among them curse requests on monsters, the aura ends by the skill switch and the different-state group clears
([states](states.md)), and the kept run list re-checks byte for byte with the same checker. (run:2026-10-20-shortfalls)

[C] Under the same boundary run:2026-10-21-shortfalls2 (plan 0047 Phase 2b) reproduced 14 sessions with 0
mismatches, among them the curse resistance cut on the player, group 3's nested clears and 296 expiries
([states](states.md)); the kept run lists of the two earlier runs re-check byte for byte with its checker.
(run:2026-10-21-shortfalls2)

The stat values that plans 0034 and 0037 took as value oracles stay oracles: run:2026-10-16-combat logs values, not
lists, and the level-up maxima of run:2026-10-16-player were compared only for consistency (the P2 review ruled that
none is replaced). A reimplementation that models this subsystem computes those values; the earlier runs do not yet
check that composition.

## Draw order

[C] Seed invariance was logged at the entry and the exit of every event of eight kinds (game seed and acting unit's
seed): link 12 868, unlink 12 853, own write 101 995, toggle 19 525, apply 6 232, expire 2 749, tick 54 719, aura
2 763 unchanged. Those kinds draw nothing, except a damaging aura's drawing run below. (run:2026-10-17-stats)

[C] A damaging aura's run (Sanctuary) that draws moves the caster's unit seed by one `RNG_RangeB`, in the elemental
damage roll (phase 3's): 865 drawing runs, 865 steps, each exit asserted against the logged draws; 746 chained pairs,
115 next runs entered elsewhere, 4 drawing runs with no next run in their log (`tools/stats.py`'s counts, keyed by the
caster unit). The run did not count the units each run hit.
(fn:SKILLS_RollElemDamage@0x0056E0C0, fn:RNG_RangeB@0x0045C3E0, run:2026-10-17-stats)

[I] The draw is one per run whatever the number of units hit: do 66 makes its one `SKILLS_RollElemDamage` call
(at 0x005CF5D5) before its target pass, and the pass copies the packet it fills to every unit hit (`rep movs` at
0x005CF367). (fn:sub_005CF3A0_AuraHitDo@0x005CF3A0, fn:sub_005CF2A0_AuraHitUnitCb@0x005CF2A0,
[skills/0011 § 3](../../findings/skills/0011-paladin.md#3-the-aura-functions-do-65-66-81-82), [stats/0002 § 7](../../findings/stats/0002-states.md#7-events-inputs-outputs-draws)) Details:
[states § H](states.md#h-draws-per-event-kind).

## Evidence

- [stats/0001](../../findings/stats/0001-aggregate.md) (aggregation, § 1–9) and
  [stats/0002](../../findings/stats/0002-states.md) (states, § 1–8).
- [stats/0002 § 9](../../findings/stats/0002-states.md#9-plan-0047-phase-2-the-shortfalls-run2026-10-20-shortfalls) and
  [stats/experiments § The stats sessions of run:2026-10-20-shortfalls](../../findings/stats/experiments.md#the-stats-sessions-of-run2026-10-20-shortfalls),
  with the Phase 2 review in the [plan 0047 log](../../plans/0047-simulation-shortfalls.md#implementation-log).
- [stats/experiments § run:2026-10-17-stats](../../findings/stats/experiments.md#run2026-10-17-stats) and its review
  in the [plan 0041 log](../../plans/done/0041-stats-and-states.md#implementation-log); its *Re-check 2026-10-20*
  (plan 0047 Phase 1: the full set blocks built, the aura chained pairs counted) and its review in the
  [plan 0047 log](../../plans/0047-simulation-shortfalls.md#implementation-log).
- `tools/stats.py` (the model behind the confirmed tags, `check` over the run list), `tools/gdb/stats.gdb`.
- Tables: [ItemStatCost](../../tables/ItemStatCost.md), [CharStats](../../tables/CharStats.md),
  [States](../../tables/States.md), [Skills](../../tables/Skills.md), [Sets](../../tables/Sets.md),
  [SetItems](../../tables/SetItems.md), [Shrines](../../tables/Shrines.md), [Objects](../../tables/Objects.md).
- Upstream: [items/properties](../items/properties.md) (the lists an item is created with),
  [items/uniques-sets](../items/uniques-sets.md) (set membership), [player/creation](../player/creation.md) (base
  stats), [monsters/stats](../monsters/stats.md) (a monster's creation stats, the stat callback),
  [data/calc](../data/calc.md) (the passive and aura calcs). Downstream: [combat](../combat/README.md) (every stat it
  reads), [player/creation § I](../player/creation.md#i-level-up--player_levelup) (the refill maxima),
  [objects](../objects/README.md) (shrine and well operates).

## Open questions

- [L] Phase (3): a skill's own effect, Holy Shield and the progressive skills, the timed self-states (armours,
  shouts), a damaging aura's hit, charged and item-granted skills.
- [L] Two clients (plan 0044): offensive auras on a hostile player and hostile states; the party aura filter is
  [states F3](states.md)'s (run:2026-10-20-two-clients).
- [L] The shortfalls final for plan 0047 (shrines and wells, 21 of 50; the 256 floor, 0; the curse cut's rounding
  and its refusal at 100) are listed in [states](states.md#open-questions), out of that plan. An aura state's end,
  groups 1–3, `attract` on monsters, the curse cut on the player and the 300 expiries are reached there.
