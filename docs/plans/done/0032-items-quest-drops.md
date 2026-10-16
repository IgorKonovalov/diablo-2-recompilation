# 0032 — Items: quest drops, quest rewards and special drops

> **Status:** done (approved 2026-10-15, closed 2026-10-16)
> **Created:** 2026-10-15
> **Owner skill(s):** archivist, reverser, spec-writer
> **Related ADRs:** 0001-target-toolchain-evidence-sources, 0002-scope-creation-paths-and-enablers, 0003-runtime-experiments, 0004-boundary-oracles-in-reproduction, 0007-fetched-leads-only, 0010-forced-path-runs, 0011-harness-slots

## TL;DR

**Question:** how does quest state change what drops, and which items do quests create outside the treasure class
path? This covers four things:
- the quest TC switch (`TreasureClass4` when the quest is not done, [items/tc](../../specs/items/tc.md) step B6, `[I]`);
- the special drops: the Countess's rune TC, the Cow King and the cows, the Hellforge's gems;
- the quest items: the Horadric Cube and staff parts, Wirt's Leg, the scrolls, the quest-object drops;
- the quest rewards that create or change items: Charsi's imbue, Larzuk's sockets, Anya's personalisation, the
  Hellforge rune, and the Ancients' and Malah's items.

When it is done, `docs/findings/items/0010-quest-drops.md` states each path. `tools/tc.py` and the item chain model
the quest switch and the reward paths. `docs/specs/items/quest-drops.md` is drafted, and items/tc B6 is `[C]`.

It also takes the monsters/pool `boss` question ([pool.md](../../specs/monsters/pool.md) *Open questions*): an act
boss's creation in an expansion Nightmare or Hell game. The kills this plan needs reach the bosses anyway.

## Context

- Research-map row `items/quest-drops`: `not started`. Dependency `items/tc` reviewed. B6 is `[I]`, with one
  unlogged sighting (Andariel took `Andarielq (N)`).
- Code already named: `QUESTRECORD_GetState` `0x0065C310`, `SetState`, `ClearState` (I), which the B6 tests call;
  the killer-to-player resolution `0x0063A690` and `0x00625760(…,0x800)` (items/0001 *Open questions*);
  `sub_005B1CF0_MonPostCreateBoss` and the quest hooks of the Countess (hook 5) and the Cow King (hook 4)
  ([monsters/special](../../specs/monsters/special.md)); `OBJ_PresetQuestObject` `0x0054F430` (its class depends on quest
  13's state, [objects](../../specs/objects/README.md)); `sub_00628CD0_ItemBaseIsQuest`; `sub_00546270_QuestsPlayerJoin`.
- Data: [MonStats](../../tables/MonStats.md) `TCQuestId` (`+0x9E`) and `TCQuestCP` (`+0x9F`); [Misc](../../tables/Misc.md)
  `quest` and `questdiffcheck`; [save/0002](../../findings/save/0002-quest-words.md): the quest record (768 bits,
  `16·q + s`), bits 0 per quest decoded, bits 1, 15 and the CP states not. The `TreasureClassEx` rows for the
  Countess and the cows are documented in [TreasureClassEx](../../tables/TreasureClassEx.md).
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
  - [MonStats](../../tables/MonStats.md): `TCQuestId`/`TCQuestCP` cross-referenced to the quest ids of save/0002, with a
    survey of every class that has a quest TC and its `TreasureClass4` per difficulty;
  - [save/0002](../../findings/save/0002-quest-words.md) § Recipe: which bit a recipe must set for each reward state.
    Static reading of the quest scripts is the reverser's in Phase 1, so this states only what the save shows.
- **Done when:** each recipe builds and loads; `d2s.py survey` shows exactly the bits the recipe asked for; the
  MonStats survey runs. The tome crash is plan 0027's (Phase 1); if it is not landed yet, `questcows.json` waits.

### Phase 1 — Read the quest paths
- **Owner skill:** reverser
- **What:** read B6's three quest tests and the killer resolution, the special-drop hooks, and the quest reward
  handlers up to their item creation calls.
- **Outputs:** `docs/findings/items/0010-quest-drops.md`; `re/symbols.csv` rows (subsystem `items/quest-drops`);
  [items/0001](../../findings/items/0001-tc-resolution.md) *Open questions* answered where they belong.
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
- **Owner skill:** reverser (agent-driven per [harness-play](../../../.claude/skills/reverser/references/harness-play.md),
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
  - the Phase 1b cases;
  - first, the five quest saves (`questfresh`, `questfreshv`, `questrewards`, `questrewardsh`, `questcows`) loaded,
    written back by *Save and Exit*, `d2s.py questbits <written> <built>` showing no quest bit lost or added beyond
    what the game's own load rules set (bit 15 from a saved bit 1, bits 13–14 cleared; items/0010 § 3), and their
    `test_d2s.py` hashes pinned (moved from Phase 0 at its review); a reward state that does not offer its reward is a
    blocking entry to the archivist.

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
- **2026-10-15 — Phase 1 and 1b (reverser, `lane/r32p1`).** [items/0010](../../findings/items/0010-quest-drops.md), static
  only, **C 0 / I 41 / L 22** (17 `[L]` are Phase 1b verdicts, 5 open questions); 89 symbol rows under
  `items/quest-drops`. B6: the resolved killer's own record, bits 15, 1 and `TCQuestCP`; the drop runs inside the death
  set-mode, **before** the quest scripts see the kill, so the first kill always gets the quest TC; Andariel (CP 1)
  keeps the quest TC in later games once reported, Duriel/Mephisto/Diablo/Baal only until the first kill. Killer
  resolution: owner of a pet, or the caster of a `states.txt` `exp` state (conversion, attract, confuse). Special drops
  are scripted on a **quest seed** (`Game+0x10F4`+0x18, seeded from one game-seed step): Andariel's three gems, the
  Hellforge's per-player gem waves and expansion rune, Baal's first-kill gold, quest chests' gold; the Countess has no
  quest dependence; the Cow King drops 8 `vps`. Rewards: imbue = new rare, ilvl clvl (+4 when > 5), fresh seeds; Larzuk
  max / 1+RangeB(min(max,2)) / 1; Anya name only; all three repair and recharge. `boss` E4 test confirmed at
  0x00573E3A, case set in § 7. Recommended boundary in § 8 (model the B6 test and the quest-seed draws; quest bits and
  per-player counts are inputs; assert the quest seed per drop). Phase 1b: 17 verdict lines, one contradiction (the
  data guide's Act I `TCQuestId` labels, off by one), no contradiction on behaviour; Larzuk does not reach items/0007's
  crafted-above-1 case (it asks for 1).
- **2026-10-15 — Phase 1 and Phase 1b accepted with fixes, boundary ruled (architect).** items/0010 meets every
  Phase 1 *Done when* item (the imbue's affix count is the ordinary rare build of items/affixes at the stated ilvl) and
  Phase 1b gives each compared claim a verdict; Phase 1 (2a04443) has no `src:` and precedes the cross-check
  (963210b). Re-read with r2 in review, all agree: the B6 tests (0x005A6705–0x005A67DF: `+0x9E`, `+0x8C + 8·diff`,
  `0x0058F0D0`, `0x0063A690`, `0x00625760(…, 0x800)`, `QUESTS_PlayerRecord`, `GetState` 15, 1, `+0x9F`), the
  drop-before-script order (0x0057CDC4 → `0x005A7C20`, mode-0 start `0x005A6FF0` in table `0x006E2260`, then
  0x0057CDD9 → `QUESTS_MonsterDeathEvent`), the quest seed (`QUESTS_GetSeed` = `Game+0x10F4` + 0x18; one LCG step of
  `Game+0xD0` written back at 0x00545F45), the `boss` mask test (0x00573E2E–0x00573E40, masks 4 and 0x40) and Larzuk's
  count (0x0057A38F–0x0057A3E2: magic `1 + RangeB(min(max, 2))`, qualities 5–9 `1` when max ≥ 1, else `max`), which
  agrees with items/0007 § 7 (the caller 0x0057A3E2 named there). After merging main, four addresses keep main's names
  (`ITEMS_CreateForStore`, `NPC_MenuAction`, `UNIT_GetPlayerData`, `sub_00629C80_ItemMagicStockable`); 85 rows stay
  under `items/quest-drops`. **Phase 2 boundary:** as § 8 recommends. `tools/tc.py` models the B6 test and the killer
  resolution from logged inputs (the killer chain, the resolved player's word bits); the scripted drops' draws, the
  imbue chain, Larzuk's count and the personalization are modelled; when quest bits are set, the per-player counts and
  the quest-seed state on entry are inputs, and each scripted drop asserts the logged quest seed on entry (ADR-0004
  boundary oracle), with the start value checked once at `QUESTS_InitGame`. The open questions on the mode table and a
  missile killer are answered by the B6 log. Larzuk asks for 1 socket on a crafted item, so the crafted cap that
  items/sockets-runewords leaves open is not reachable through him (plan 0030's cube, or a forced path, ADR-0010).
- **2026-10-15 — Phase 0 landed (archivist, `lane/a34p0`, after plan 0034 Phase 0), review requested.**
  `tools/d2s.py build` gains `quest_bits` (`{difficulty: {word: [bits] | {"set", "clear"}}}`, applied after `quests`)
  and `"quest_diff"` for simple quest items (stat 356, required); `d2s.py questbits <save> [<base>]` lists a save's
  quest bits or its changes; `QuestBitsTest`. Recipes `questfresh`, `questfreshv` (Baal), `questrewards`,
  `questrewardsh` (the Soulstone of Hell), `questcows`, each with its bits in all three difficulties
  ([d2s.md § Quest saves](../../formats/d2s.md#quest-saves)); [save/0002 § Quest and reward states](../../findings/save/0002-quest-words.md#quest-and-reward-states-plan-0032-phase-0-archivist)
  gives each state's bits and evidence. [MonStats § Quest TCs](../../tables/MonStats.md#quest-tcs-plan-0032-phase-0) and
  `tools/quest_survey.py` (gate survey `quest`): five classes, `TCQuestId` = the quest word B6 reads (6, 14, 22, 26,
  40; `[I]` through `QUESTRECORD_GetState`), `TCQuestCP` 1 (Andariel), 5 (Duriel), 0; the quest items of
  weapons/misc. Lead registered: `src:trevin-d2s-109` (quest names and bit notes, 1.09). Surprises: Duriel's
  `TCQuestCP` 5 is the bit a game-written save holds after his kill; Larzuk's pending state is in a game-written save
  (word 35 bits 1, 3); the Misc `quest` cell is not the quest word in every row; a simple quest item stores stat 356,
  which the builder could not write before. **Not done:** no save was loaded (no harness slot); proposed for Phase 2.
- **2026-10-15 — Phase 0 accepted with fixes (architect review, `lane/a34p0`).** The five recipes build;
  `d2s.py questbits <built> <base>` lists exactly each recipe's `quests`/`acts_open`/`quest_bits` bits (rerun in
  review) and `QuestBitsTest` asserts it; the MonStats quest survey runs (gate survey `quest`); gate and `test_d2s`
  green after merging main. `src:trevin-d2s-109` is honestly registered as a lead (1.09 prose, use scoped to the quest
  table) and every bit meaning that rests on it alone is `[L]` (save/0002 rows, MonStats quest names, the stat 356
  meaning). No doc contradicts items/0010: the reward states the recipes set are the ones its § 6 handlers test (word 3
  bit 1, word 35 bit 1, word 38 bit 1), the Hellforge operates with word 27 bits 0 and 1 clear (the recipe's bit 2 is
  harmless), and word 4 bit 10 is the Cow King's credit that `CUBE_CowPortalOpen` refuses on; those `[L]` move up in a
  follow-up (backlog). Fix: save/0002 *Leads used* now names the lead. Rulings: (1) the loads move to Phase 2's first
  step (added to its *Done when*), as for plans 0031/0033 Phase 0. (2) **`questbits <built> <base>` meets "`d2s.py
  survey` shows exactly the bits"**: the criterion asks that a tool show the built file's bits against the recipe, and
  `questbits` is the `d2s.py` reader that does, per bit, with the exactness under test; `survey` has no per-bit
  output and needs none. The Phase 2 load step reuses it on the written-back saves.
- **2026-10-16 — Phase 2 (reverser, `lane/h32p2`), review requested.** run:2026-10-16-quest-drops: 53 agent-driven
  sessions on slots 3 and 4 with the new `tools/gdb/quests.gdb`; `tools/questdrops.py`, `tools/tc.py` (B6 now modelled:
  `b6_model`), `tools/items_chain.py affixes` and `tools/monpool.py` reproduce every session with 0 mismatches. The five
  quest saves load and come back with only the load rules' bit 15 and word 40 bit 10 (set at the join by
  `sub_0058E430_A5Q6_PlayerJoin`); hashes pinned. B6 `[C]` from 8 kills (Andariel and Duriel taken and not taken,
  Mephisto taken; drop before the death script; a Nova kill's killer is the player). The quest seed `[C]`; Andariel's
  gems and 5 Hellforge operations (Normal 3, Nightmare 2: 20 gem waves, 5 runes) `[C]`; 17 imbues, 15 Larzuk sockets
  (magic), 15 personalizations `[C]`; the `boss` exception `[C]` (Andariel in Nightmare 49 and Hell 75); the cow portal
  and 565 cow kills. Surprises: a `quests: all` save keeps Duriel's quest TC (CP 5 is not bit 0), so the not-taken case
  needs word 14 bit 5 (`questdurielk.json`); the Hellforge's strikes need an `hfh` with stat 356 ≥ the difficulty
  (`questdiffcheck` 1), which the Phase 0 reward recipes lack above Normal; the hammer must be equipped; personalize
  writes the flag and name after placing the copy. **Shortfalls** (stay `[I]`, owner-played addendum proposed in the
  run record): Mephisto quest done (4 attempts), the Countess in all four states (10 attempts), the Hell Hellforge (3
  deaths), the Cow King. New pilot actions: `npc … imbue|socket|personalize`, `objop`, `hunt`, `--descend` lists
  (tooling.md § Quest services). No owner play.
- **2026-10-16 — Phase 2 review (architect): accept with fixes**, applied on `lane/h32p2`. Rechecked: `questdrops.py
  check` on the 53 logs (0 mismatches), the log manifest, `tc.py replay` and `monpool.py check` on the boss sessions, r2
  on the personalize order, the join's word 40 bit 10 and Duriel's bit 5. Fixes: hammer drops 11; the forge-operate
  `[C]` rests on the two `FOP` sessions and leaves the 356 = difficulty boundary `[I]`; B6 `[C]` single-player only
  (party `[I]`); the per-boss `[C]` limited to the tested states; § 6 points at the personalize correction; 11 symbols
  `C`. Rulings: (1) **The stat-356 hammer** (`questservices.json`, `item_stats` 356 = 2) is a tool-built save on stock
  tables, an ADR-0003 input (ADR-0013 § Neutral), not a forced path: `sub_00557AB0_ItemInitStats` gives a created quest
  item stat 356 = the difficulty, so a Hell-made hammer in a Nightmare game is a stock state. It backs `[C]` for the
  forge code that reads it, nothing about how a player gets it. The Phase 0 recipes' Hellforge gap goes to the archivist
  (backlog). (2) **Shortfalls accepted; Phase 2 closes** with Mephisto done, the Countess, the Hell Hellforge and the
  Cow King `[I]`, and the not-attempted paths (hireling/golem/`exp` killer, party, classic, imbue below clvl 6, Larzuk
  on non-magic) `[I]`. Each rests on code already exercised in another state (the same B6 test, the ordinary
  superunique TC path, the same `ForgeWave` with another rune table, the same death-script creator), so the spec can
  state it `[I]`. Phase 3 may start; the owner addendum (backlog, `human`) raises them later under the same run id.
  (3) The true-tomb observation (act `+0x094`) is not in the run record, so it confirms nothing yet; one line in the run
  record with the sessions and values would let drlg/0006 cite it.
- **2026-10-16 — Phase 3 (spec-writer, `lane/s32p3`), review requested.** [items/quest-drops](../../specs/items/quest-drops.md)
  drafted, **C 71 / I 83 / L 7** (7 open questions): § A the quest record and the quest seed, § B the B6 test with the
  table of the five quest TCs and a state-by-state outcome table, § C the two scripted creators, § D one section per
  special drop (Andariel's gems, the Countess, the Cow King, the Hellforge, Baal, the scripts that create nothing),
  § E the quest items (table, duplicates, the `quest` column, the item-move gate), § F the imbue, Larzuk, Anya and the
  given items, § G the `boss` exception; four worked examples from run:2026-10-16-quest-drops (Andariel's first kill
  in 3344 with the quest TC walk and the three gem draws, the imbue in 3311, a Normal Hellforge in 3315, a Larzuk
  socket in 3311), every value checked against the logs. The Phase 2 shortfalls and the not-attempted paths are `[I]`
  (Mephisto done, the Countess, the Hell forge, the Cow King, hireling/golem/`exp` killer, party, classic, imbue below
  clvl 6, Larzuk on non-magic); B6 `[C]` single player only; the stat-356 = difficulty boundary `[I]`. Updated:
  [items/tc](../../specs/items/tc.md) B6 to `[C]` and its open question struck (C 45 / I 76 / L 7);
  [monsters/pool](../../specs/monsters/pool.md) E4's `boss` test to `[C]` and its open question struck (C 81 / I 29 / L 3);
  [objects](../../specs/objects/README.md) § L, the quest objects (C 136 / I 64 / L 4); the [items README](../../specs/items/README.md);
  four glossary terms. Map status bump requested in the backlog.
- **2026-10-16 — Phase 3 review (architect): accept with fixes; plan closed.** Anchors: `MONSTER_DropItems`,
  `QUESTS_InitGame`, `QUESTS_GetSeed`, `sub_005B6710_A4Q3_ForgeWave`, `NPC_MenuAction`, `QUESTRECORD_GetState`,
  `sub_00573CB0_MonStatsInit` and `sub_00559A30_DropItemAtUnit` resolve in `re/symbols.csv`; gate green. The Phase 2
  shortfalls and not-attempted paths are `[I]` (Mephisto done, the Countess's four states, the Hell forge and
  `FORGE_RUNES[2]`, the Cow King, the hireling/golem/`exp` killer, a party and the forge's `n` > 1, classic, the imbue
  at clvl ≤ 5, Larzuk on non-magic, the stat-356 = difficulty boundary); no `[L]` outside *Open questions*; the one
  `contradicted` lead (src:d2dfg-blizzard's Act I `TCQuestId` labels) is resolved by the run and stated in the
  reimplementation notes. Rulings on the writer's points: (a) the worked examples were spot-checked against the three
  raw logs (`python3 -I`, read-only): 3344's `QI1` quest seed, B6 lines (word `0x18`, three `GetState` 0), the
  `Andarielq` walk (`Range(41)`, rolls 27/38/34/7, picks 2–7 below 19) and the three `QDI` gem seeds; 3311's
  `IMB0`/`IMB1`/`IC0` (ilvl 84, f80 `0x22`, game seed `c4763324:169bee5b` → start `61ae3c3d`), the rare-name rolls
  37/38 → 194 and 0/12 → 47, the five `AFR` ids, and Larzuk's `LZS`/`LZR` (`a02949bd` → `c36e110b`, r 1); 3315's four
  gem seeds and `r07` with the end seed `5522b5b8:2225af82`; every `Step` recomputed. All hold. The logs are pinned by
  the run's manifest, so citing the run id is acceptable; a reverser entry asks for the four examples to be carried as
  test vectors so they survive without `workspace/`. (b) Both run-backed `[C]` stand: "a scripted creation leaves the
  quest seed unchanged" has the code anchor plus the logged entry/exit seed of every scripted creation (`QDI`/`QDX`);
  "the imbue takes two fresh game-seed steps" has the code anchor plus the logged game seed and a bit-exact rare build.
  (c) Neither the spec nor items/0010 says how an object operate reaches `QUESTS_ObjectOperate`: now an `[L]` in the
  spec's *Open questions* and a reverser backlog entry. **Fixes made:** that open question (L 7 → 8) and its pointer in
  the entry-point row and in objects' open question; objects § L's Hellforge row scoped (`[C]` for one player in Normal
  and Nightmare, `n` > 1 and Hell inferred); the worked examples say the logs are pinned; status `reviewed`; tags
  **{C: 71, I: 83, L: 8}**; research map rows `items/quest-drops`, `items/tc` (C 45 / I 76 / L 7), `monsters/pool`
  (C 81 / I 29 / L 3) and `objects` (C 136 / I 64 / L 4); plan moved to `done/` with its links. All phases done; plan
  closed. The owner-played addendum stays open in the backlog.
- **2026-10-16 — Owner-played addendum (reverser, `lane/o32`; the owner played, no agent session).** The seven
  sessions of the run record's addendum list were played by the owner on slot 0 (seeds 3501–3507, logger
  `tools/gdb/quests.gdb`, no steps, no *Save and Exit*) and all seven reached their target: Mephisto with his quest
  done (Normal), the Countess killed in her four states (Normal and Nightmare, done and not done), the Cow King and his
  eight `vps`, the Hellforge struck in Hell with its four waves and `r19`. The four checkers re-run on each log:
  195 quest-bit writes and 14 scripted creations with 0 mismatches, 221 `TC_ResolveDrops` calls, 355 creations and
  4737 monster levels with 0 failures; the quest seed is game-seed draw 4 in all seven. Recorded as
  [run:2026-10-16-quest-drops § Owner-played addendum](../../findings/items/experiments.md#owner-played-addendum-same-run-id-2026-10-16-result)
  (state owner-played; manifest `workspace/logs/quests-owner-manifest.txt`). Raised in
  [items/0010 § Owner-played addendum](../../findings/items/0010-quest-drops.md#owner-played-addendum-run2026-10-16-quest-drops-2026-10-16):
  Mephisto done, the Countess's TC (Normal, Nightmare), the Cow King's potions for a qualifying killer, the Hell forge
  with `FORGE_RUNES[2]`, the stat-356 = difficulty boundary. Still `[I]`: hireling/golem/`exp` killer, party,
  classic, Diablo and Baal, the Countess in Hell, the Cow King's refusals, Mephisto's kill-time bit 0. No
  contradiction; refinement: the Cow King's quality-0 request yields quality-2 items. Owner backlog entry struck;
  architect review and spec-writer re-tag (items/quest-drops, objects § L) requested in the backlog.
