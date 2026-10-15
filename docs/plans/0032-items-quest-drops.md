# 0032 — Items: quest drops, quest rewards and special drops

> **Status:** in-progress (approved 2026-10-15)
> **Created:** 2026-10-15
> **Owner skill(s):** archivist, reverser, spec-writer
> **Related ADRs:** 0001-target-toolchain-evidence-sources, 0002-scope-creation-paths-and-enablers, 0003-runtime-experiments, 0004-boundary-oracles-in-reproduction, 0007-fetched-leads-only, 0010-forced-path-runs, 0011-harness-slots

## TL;DR

**Question:** how does quest state change what drops, and which items do quests create outside the treasure class
path? This covers four things:
- the quest TC switch (`TreasureClass4` when the quest is not done, [items/tc](../specs/items/tc.md) step B6, `[I]`);
- the special drops: the Countess's rune TC, the Cow King and the cows, the Hellforge's gems;
- the quest items: the Horadric Cube and staff parts, Wirt's Leg, the scrolls, the quest-object drops;
- the quest rewards that create or change items: Charsi's imbue, Larzuk's sockets, Anya's personalisation, the
  Hellforge rune, and the Ancients' and Malah's items.

When it is done, `docs/findings/items/0010-quest-drops.md` states each path. `tools/tc.py` and the item chain model
the quest switch and the reward paths. `docs/specs/items/quest-drops.md` is drafted, and items/tc B6 is `[C]`.

It also takes the monsters/pool `boss` question ([pool.md](../specs/monsters/pool.md) *Open questions*): an act
boss's creation in an expansion Nightmare or Hell game. The kills this plan needs reach the bosses anyway.

## Context

- Research-map row `items/quest-drops`: `not started`. Dependency `items/tc` reviewed. B6 is `[I]`, with one
  unlogged sighting (Andariel took `Andarielq (N)`).
- Code already named: `QUESTRECORD_GetState` `0x0065C310`, `SetState`, `ClearState` (I), which the B6 tests call;
  the killer-to-player resolution `0x0063A690` and `0x00625760(…,0x800)` (items/0001 *Open questions*);
  `sub_005B1CF0_MonPostCreateBoss` and the quest hooks of the Countess (hook 5) and the Cow King (hook 4)
  ([monsters/special](../specs/monsters/special.md)); `OBJ_PresetQuestObject` `0x0054F430` (its class depends on quest
  13's state, [objects](../specs/objects/README.md)); `sub_00628CD0_ItemBaseIsQuest`; `sub_00546270_QuestsPlayerJoin`.
- Data: [MonStats](../tables/MonStats.md) `TCQuestId` (`+0x9E`) and `TCQuestCP` (`+0x9F`); [Misc](../tables/Misc.md)
  `quest` and `questdiffcheck`; [save/0002](../findings/save/0002-quest-words.md): the quest record (768 bits,
  `16·q + s`), bits 0 per quest decoded, bits 1, 15 and the CP states not. The `TreasureClassEx` rows for the
  Countess and the cows are documented in [TreasureClassEx](../tables/TreasureClassEx.md).
- Harness: `tools/d2s.py build` sets quest bit 0 only (`quests`, `acts_open`). This plan needs any bit of any quest
  word, so Phase 0 adds it. The quest bosses of Normal are killable with the Nova build; Nightmare and Hell bosses need
  the Hell build of harness-play (or are logged at creation only, which is all the `boss` case needs). NPC dialogue
  (for rewards) is the `tools/d2pilot.py npc` action of [plan 0031](0031-items-vendors.md), so this plan's Phase 2
  runs after 0031's Phase 2.
- Leads: `src:pd-item-generation` (the Countess's picks), `src:pk-monstats-guide`, `src:arreat-summit-item-pages`,
  `src:d2dfg-blizzard`. Quest rewards are well documented (Arreat Summit quest pages, to be searched and registered).

## Phases

### Phase 0 — Quest bits in saves, and the quest data
- **Owner skill:** archivist
- **What:** let `tools/d2s.py build` set any quest bit, and document the quest-related data.
- **Outputs:**
  - `tools/d2s.py build`: a recipe key `quest_bits: {difficulty: {word: [bits]}}` (set and clear), with a test; the
    existing `quests` key unchanged;
  - recipes: `questfresh.json` (expansion, each act's boss quest not done, for the B6 kills), `questrewards.json`
    (each reward quest at the state just before the reward: imbue, socket, personalise, the Hellforge rune, the
    Ancients), `questcows.json` (Wirt's Leg and a tome, cow quest not done), and a Hell variant of each where it applies;
  - [MonStats](../tables/MonStats.md): `TCQuestId`/`TCQuestCP` cross-referenced to the quest ids of save/0002, with a
    survey of every class that has a quest TC and its `TreasureClass4` per difficulty;
  - [save/0002](../findings/save/0002-quest-words.md) § Recipe: which bit a recipe must set for each reward state.
    Static reading of the quest scripts is the reverser's in Phase 1, so this states only what the save shows.
- **Done when:** each recipe builds and loads; `d2s.py survey` shows exactly the bits the recipe asked for; the
  MonStats survey runs. The tome crash is plan 0027's (Phase 1); if it is not landed yet, `questcows.json` waits.

### Phase 1 — Read the quest paths
- **Owner skill:** reverser
- **What:** read B6's three quest tests and the killer resolution, the special-drop hooks, and the quest reward
  handlers up to their item creation calls.
- **Outputs:** `docs/findings/items/0010-quest-drops.md`; `re/symbols.csv` rows (subsystem `items/quest-drops`);
  [items/0001](../findings/items/0001-tc-resolution.md) *Open questions* answered where they belong.
- **Done when:** the finding states, with addresses and `[I]` or better:
  - **B6:** what the three state tests mean (bits 15, 1 and the `TCQuestCP` state), how the killer resolves to a
    player (pets, minions, missiles), and which party member's quest record is read;
  - **the special drops:** the Countess's rune TC and its quest dependence; the cow level's drops (the Cow King's
    quest hook); the Hellforge's gem drop (object operate → item creation, with its draws, per difficulty); any other
    hardcoded TC or forced drop met in the quest code (Diablo's and Baal's first kill, Nihlathak, the Ancients);
  - **quest items:** how each quest item is created (from a TC, an object, or a script), and whether the quest state
    or `questdiffcheck` refuses a duplicate;
  - **rewards:** Charsi's imbue (the rare roll it makes: ilvl, affix count, which item model entry), Larzuk's sockets
    (the socket count arithmetic vs properties § F), Anya's personalisation (the name only, no stat change; named),
    the Hellforge rune (the rune range per difficulty), the Ancients' rewards, Malah's scroll;
  - **the `boss` exception** of monsters/pool § E4: read again, and the Phase 2 case set;
  - **the boundary decision** for Phase 2. Quest scripts that are game simulation (dialogue, timers) stay inputs.
    Recommend one; the architect rules at the review.

### Phase 1b — Community cross-check
- **Owner skill:** reverser
- **What:** fetch the leads above; search for and register quest reward and special drop documentation (imbue
  ilvl and affix counts, Larzuk's sockets, Hellforge rune ranges, Countess runes, cow drops). Compare blind.
- **Outputs:** `docs/sources.md` entries; verdicts in the finding's *Leads used*.
- **Done when:** each claim carries a verdict; every `contradicted` claim reachable on stock data is a required case
  of Phase 2.

### Phase 2 — Bit-exact reproduction
- **Owner skill:** reverser (agent-driven per [harness-play](../../.claude/skills/reverser/references/harness-play.md),
  after plan 0031 Phase 2 lands the NPC action; at most two slots; owner play is the fallback for bosses scripted play
  can't kill)
- **What:** extend `tools/tc.py` (B6) and the item chain (rewards), add quest-state lines to `tools/gdb/tc-drops.gdb` or
  a new `tools/gdb/quests.gdb`, and log a run.
- **Logging:** for each quest-TC kill: the killer, the quest record bits read, the TC chosen; for each reward and
  special drop: the trigger, every draw, the item lines; for each boss creation: the MonStatsInit level lines.
- **Done when:** a run `run:YYYY-MM-DD-quest-drops` reproduces with 0 mismatches:
  - the B6 switch taken and not taken for at least three quest bosses (Andariel, Duriel and Mephisto in Normal at
    least), the quest TC drop reproduced by `tc.py`;
  - the Countess's drop with her quest not done and done, in at least two difficulties;
  - at least 5 Hellforge operations (the gem and the rune per difficulty), each reproduced;
  - Charsi's imbue at least 5 times and Larzuk's sockets at least 5 times (each a fresh game from the reward save),
    reproduced through the item chain;
  - the cow portal and at least 50 cow kills with their drops, if plan 0027 and [plan 0030](0030-items-cube.md) have
    opened it; otherwise a named boundary;
  - the `boss` case: an act boss created in an expansion Nightmare and Hell game, logged at MonStatsInit, with its level
    reproduced by `tools/monpool.py`, so monsters/pool's open question closes;
  - the Phase 1b cases.

  In-scope claims go to `[C]`, citing the run. items/tc B6 moves to `[C]`.

### Phase 3 — Spec: items/quest-drops
- **Owner skill:** spec-writer
- **What:** write `docs/specs/items/quest-drops.md`; update items/tc B6 and *Open questions*, monsters/pool § E4 and
  *Open questions* (`boss`), objects (the Hellforge and quest objects), and the items README.
- **Done when:** the spec follows the template, and every statement is tagged. It has a table of quest-dependent TCs, a
  section per special drop and per reward with its draws, and worked examples from the run (a quest TC kill and an
  imbue). The architect's review passes.

## Open questions

- Quest progression itself (dialogue, triggers, timers) is game simulation (ADR-0002); only the state bits the item
  paths read are specified.
- Multiplayer quest sharing (which member's record B6 reads in a party) is named from the code; no two-client run
  unless ADR-0008 is accepted.

## Implementation log

_(lanes append dated entries as phases land: what was found, the confidence reached, surprises)_

- **2026-10-15 — Drafted and approved.** The owner asked for a queue of plans to run unattended, and approved all of
  them in advance. Written in the architect worktree `lane/plans0028`.
