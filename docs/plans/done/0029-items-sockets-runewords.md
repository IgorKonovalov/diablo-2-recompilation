# 0029 — Items: socket filling, gems, runes and jewels, runeword activation

> **Status:** done (approved 2026-10-15, closed 2026-10-15)
> **Created:** 2026-10-15
> **Owner skill(s):** archivist, reverser, spec-writer
> **Related ADRs:** 0001-target-toolchain-evidence-sources, 0002-scope-creation-paths-and-enablers, 0003-runtime-experiments, 0004-boundary-oracles-in-reproduction, 0007-fetched-leads-only, 0010-forced-path-runs, 0011-harness-slots

## TL;DR

**Question:** when a gem, rune or jewel goes into a socketed item, what does the game check, what does the item gain,
and when do the inserted runes make a runeword, with which property rolls on which seed? The number of sockets a drop
gets is already `[C]` ([items/properties](../../specs/items/properties.md) § F). The filling and the runeword are unread.
When it is done:
- `docs/tables/Gems.md` and `docs/tables/Runes.md` exist, as table docs with `.bin` layouts;
- `docs/findings/items/0007-sockets-runewords.md` names the insert handler, the socketable checks, the gem/rune/jewel
  property transfer per item class (weapon, armour/helm, shield), the runeword match, and the runeword property rolls;
- `tools/sockets.py` predicts an item's state after each insert and reproduces a logged run;
- `docs/specs/items/sockets-runewords.md` is drafted.

## Context

- Research-map row `items/sockets-runewords`: `not started`. Dependency `items/properties` is reviewed (C 125 / I 36 /
  L 6). The property roll per `func` (§ E) is what a runeword's properties go through, presumably.
- Code already named or seen:
  - `sub_00556B60_ItemRollSockets`, `sub_0062BC20_ItemMaxSockets`, `ITEMS_SetSockets` `0x0062BCB0`,
    `PROP_Func14_Sockets` `0x0065F590` (all `[I]`); `GEMS_Load` `0x00636B70`, `GEMS_GetRecord` `0x006372C0`.
  - [items/0006](../../findings/items/0006-properties.md) *Open questions*: four other callers of `ItemApplyProps`
    (`0x004C0D20`, `0x004E6720`, `0x004E67D0`, `0x0055C2C0`), "probably socket filling and runewords". Phase 1 starts
    there.
  - The `Runes` record getter `0x0062BED0`, `n_filled` `0x0062A900`, `0x0062BE00` (in
    [save/0001 § 7](../../findings/save/0001-d2s-io.md); not in `re/symbols.csv`). save/0001 hands this row the meaning of
    `Runes` `+0x82`, stored at item data `+0x38`, and the runeword property list state 171.
  - The Runes loader probes `runessrv` at `0x00639420` (data/0001, not followed).
  - The `ITEMS_SetSockets` quality clamps (magic ≤ 4, rare ≤ 2, crafted ≤ 3), properties § F6 `[I]`.
  - Gem colour on socketed items: items/0003 § 3 (presentation; named only).
- Data: no table doc and no layout for `gems` (`.bin`) and `runes` (288 B per record).
  [Misc](../../tables/Misc.md) covers `gemoffset`, `BetterGem` and the misc gem/rune rows. The `gemsockets`,
  `gemapplytype` and `MaxSock*` columns are in Weapons/Armor.
- Harness: `tools/d2s.py build` can place items in the inventory and the cube, but it can't build a socketed base
  (it always writes `n_filled = 0`, never sets flag bit 11), and `keep_items` refuses socketed items.
  `tools/d2pilot.py` has no inventory actions. `tools/xdrive.py` can click and right-click at window coordinates,
  which is all an insert needs (pick the rune up, click it onto the item).
- Out of scope here: the cube's socket recipes and rune upgrades ([plan 0030](../0030-items-cube.md)), Larzuk's socket
  reward and Charsi's imbue ([plan 0032](../0032-items-quest-drops.md)), and removing socketed items (no stock path in
  1.14d except the cube).
- Leads: `src:pd-sockets`, `src:planetdiablo-socketing-guide`, `src:arreat-summit-magic-items` (§ Jewels),
  `src:d2dfg-blizzard` (§ Runes.txt, § Gems.txt; describes D2R, so read for 1.14d differences). Runewords are among the
  best-documented mechanics in the community, so Phase 1b is required.

## Phases

### Phase 0 — Gems and Runes tables, and socketed saves
- **Owner skill:** archivist
- **What:** document `gems` and `runes` with `.bin` layouts, and teach `tools/d2s.py build` to write socketed items.
- **Outputs:**
  - `docs/tables/Gems.md` (the three mod groups per item class `weaponMod*`, `helmMod*`, `shieldMod*`, `transform`,
    the item link at `+0x28`, the colour byte `+0x2F`) and `docs/tables/Runes.md` (`Name`, `Rune Name`, `complete`,
    `server`, `itype1..6`, `etype1..3`, `Rune1..6`, `T1Code1..7` / `T1Param` / `T1Min` / `T1Max`, the record field
    `+0x82`), each with a survey of the stock rows (how many runewords are `complete`, how many are classic-legal);
  - `tools/excel_layouts.py` entries and the regenerated `excel_layout` baseline;
  - `tools/d2s.py build`: a recipe item can carry `sockets: N` (empty sockets: flag bit 11, stat 194) and `filled:
    [items…]` (socketed children, written after the parent, byte-aligned, as save/0001 § 7 states), with a round-trip
    test in `tools/test_d2s.py`; the `keep_items` refusal lifted for socketed items, or kept with the reason;
  - two recipes in `tools/d2s_recipes/`: `socketnova.json` (expansion, Nova sorceress with socketed bases of each item
    class: weapon, body armour, helm, shield, 2–6 sockets, plus a stack of gems, runes and jewels in the inventory and
    a set of rune combinations for at least five stock runewords) and `socketclassic.json` (classic: gems only).
- **Done when:** `excel_bin.py diff` passes on both tables with 0 mismatches and no uncovered bytes; the runeword survey
  prints for each row its item types, runes and property lines; a built socketed save loads in the game (a short
  harness check) and round-trips through `tools/d2s.py`. Meanings stay `[L]` beyond layout.

### Phase 1 — Read the insert path and the runeword
- **Owner skill:** reverser
- **What:** read the server's socket-insert handler from the client packet to the stored result, and the runeword
  check that runs after it.
- **Outputs:** `docs/findings/items/0007-sockets-runewords.md`; `re/symbols.csv` rows (subsystem
  `items/sockets-runewords`, the three addresses above among them); `re/types/` additions (the Runes and Gems records).
- **Done when:** the finding states, with addresses and `[I]` or better:
  - **the insert:** the checks that refuse an insert (socket count, `n_filled`, item types, the `gemapplytype` of the
    base, a jewel's or rune's level requirement, classic vs expansion), and which unit the child becomes (owner,
    position, the parent's socket list order);
  - **the property transfer:** how a gem's or rune's `weaponMod`/`helmMod`/`shieldMod` group is picked from the parent's
    `gemapplytype`, which `func` path each property takes (items/properties § E), and whether any draw is made. A
    jewel brings its own rolled properties. Say whether the parent's stat list is changed or a child list is linked;
  - **the runeword:** when the match runs (each insert, or only on the last socket), how a `Runes` row is matched
    (order of the scan, `complete`, the item types `itype`/`etype`, rune order, socket count equal to rune count,
    the base's quality: normal or superior only?), what `+0x82` is, and what the item gets: flag bit 26, the
    runeword id at `+0x38`, the property list with state 171, and the name;
  - **the runeword property rolls:** which seed (the item's own seed, the game seed, or a fresh one), the draws per
    `T1Code` line, in order, and how they go through the `func` table; in particular ranged properties and the
    `aura`/`oskill`/`hit-skill` lines;
  - **ITEMS_SetSockets** clamps (properties § F6) read in full, so § F6 can move off `[I]` in Phase 2;
  - **the boundary decision** for Phase 2. Recommend one; the architect rules at the review.

### Phase 1b — Community cross-check
- **Owner skill:** reverser
- **What:** fetch the leads above (ADR-0007: read in-session, downloads in the scratchpad), search for and register
  runeword-mechanics documentation (rune order, base restrictions, the "variable stats" runewords, gem mods per
  slot), and compare blind per `evidence-rules.md` § Community cross-checks.
- **Outputs:** `docs/sources.md` entries; verdicts in the finding's *Leads used*.
- **Done when:** each claim about insert restrictions, gem/rune mods per item class, the runeword match and the
  runeword rolls carries a verdict. Every `contradicted` claim reachable on stock data is a required case of Phase 2.

### Phase 2 — Bit-exact reproduction
- **Owner skill:** reverser (agent-driven per [harness-play](../../../.claude/skills/reverser/references/harness-play.md);
  at most two slots)
- **What:** write `tools/sockets.py` (the insert and runeword model, chained after `tools/props.py`), a
  `tools/gdb/sockets.gdb` logger, and an inventory action in `tools/d2pilot.py` (`insert <src cell> <dst cell>`:
  left-click the child, left-click the parent, using the inventory grid geometry measured once and recorded in
  `.claude/skills/reverser/references/tooling.md`). Then log a run.
- **Logging:** per insert: parent and child (class, quality, seed, sockets, `n_filled`), the verdict, every draw on
  every seed between the insert packet and the end of the handler, the parent's stat list after it; per runeword:
  the row matched, its property lines and the values set.
- **Done when:** a run `run:YYYY-MM-DD-sockets` reproduces with 0 mismatches:
  - at least 150 inserts, covering gems of every type and grade into each item class, runes into each item class,
    and magic and rare jewels;
  - at least 30 runewords made, from at least 8 different rows, including a runeword with ranged property lines
    (made at least three times, to show the rolls vary), an aura runeword if one is buildable on stock data, and a
    refused runeword (wrong base type, wrong rune order, and a magic base);
  - at least 5 refused inserts of different reasons;
  - the classic session shows gems only, and runes refused if they can be placed at all;
  - the Phase 1b cases;
  - the § F6 clamps reached (a magic base with more than 4 `sock`, forced path if needed, ADR-0010).

  In-scope claims go to `[C]`, citing the run.

### Phase 3 — Spec: items/sockets-runewords
- **Owner skill:** spec-writer
- **What:** write `docs/specs/items/sockets-runewords.md`; link it from items/properties § F (sockets on creation), the
  items README, and save/d2s (flag bit 26, `+0x38`, state 171).
- **Done when:** the spec follows the template, and every statement is tagged. It has the insert checks as an ordered
  decision list, the gem/rune mod group table, the runeword match as pseudocode, and the RNG call sequence of one
  runeword's rolls as a worked example from the run. The architect's review passes.

## Open questions

- Socketed-item removal and rune upgrades are cube recipes ([plan 0030](../0030-items-cube.md)).
- Runewords that the stock `complete` column disables are named only, unless a forced-path run (ADR-0010) is cheap.
- Client-side display (gem colours, socket graphics) is presentation (ADR-0005).

## Implementation log

_(lanes append dated entries as phases land: what was found, the confidence reached, surprises)_

- **2026-10-15 — Drafted and approved.** The owner asked for a queue of plans to run unattended, and approved all of
  them in advance. Written in the architect worktree `lane/plans0028`.
- **2026-10-15 — Phase 1 and 1b landed (reverser, branch `lane/r29p1`; Phase 0 not merged yet, column names read
  from the `.txt` headers).** [items/0007](../../findings/items/0007-sockets-runewords.md), committed blind before any
  lead was read, then cross-checked. Every *Done when* bullet:
  - *the insert*: `ITEMS_InsertSocket` 0x00562660, reached from the 9-byte packet handler `SOCK_PacketInsert` and
    from the save/golem readers and the item copier. Refusal order (§ 1): child on the cursor, parent identified,
    parent stored/equipped (packet), child `sock` type and identified, parent socketed with `hasinv`, a free socket.
    **No** level, `gemapplytype`, quality or expansion test. The child is appended to the parent's inventory list
    (x = socket index, y = 0, mode 6), so socket order = insert order. `[I]`.
  - *the property transfer*: the group is picked by the parent's `gemapplytype` (0 weapon, 1 helm/armour, 2
    shield); it is applied in mode 2 (gem) or 5 (rune) with the **child** as both the item and the target, and the
    child's list is then linked to the parent. The parent's own lists are untouched. Jewels: nothing applied, their
    list is linked. **No draw on stock data** (`[C]` by a data check over all 69 `gems` rows).
  - *the runeword*: `RUNEWORD_Match` 0x0062BED0 runs after every insert, but matches only when the children fill
    stat 194. Quality 4..9 excluded (low quality is **not**), `quest` bases excluded, `Runes` scanned from record 0,
    `complete`, exact rune order, `etype` then `itype` via `ITEMS_UnitIsType`. `server` rows apply only in a ladder
    game. `+0x82` = the string index of `Name`. The parent gets flag bit 26 and a state-171 list. `[I]`, with flag 26,
    the 171 list and the ethereal base `[C]` from the game-written *Steel* save.
  - *the rolls*: on the item seed of the **child whose insert completed the word** (`[I]` until Phase 2 logs the
    seed), through the items/0006 handlers,
    `T1Code1..7` in order, a blank code ending the list. The handlers see the rune as "the item" (`[C]`): `ac%` resets
    nothing, `dmg-min`/`dmg-max` take the non-weapon branch (`[C]`: the *Steel* save holds 21/23/159 and 22/24/160),
    `dmg%` has no `+1` fallback, *Famine*'s `ethereal` is a no-op. Funcs 11/22 (`hit-skill`, `aura`, `oskill`) as
    items/0006; func 19 draws once, and the packet path then refills charges to the maximum.
  - *ITEMS_SetSockets*: read in full (§ 7): magic ≤ 4, rare ≤ 2, crafted and 9 ≤ 3, set/unique 1 (or keep the
    current count), then `ItemMaxSockets`; the load setter has no quality clamp.
  - *boundary*: recommended in § 8: no oracle; the child's item seed at `RUNEWORD_Apply` entry logged as an input.
  - *Phase 1b*: five sources (two new rows, `arreat-summit-socketing`, `d2runewizard-runeword-faq`), 25 verdicts.
    Contradicted: the crafted socket cap (1 in the Arreat Summit, 3 in the code; a required Phase 2 case) and the D2R
    `gemoffset` text (not observable on stock data). Backlog 2026-10-15 (three entries).
  - Surprise for Phase 2: a rune's item seed after a save load is a fresh game-seed draw (no reader sets the start
    seed), so the seed must be logged, not derived from the save.
- **2026-10-15 — Phase 0 landed (archivist, branch `lane/a29p0`; review requested in the backlog).**
  - Tables: [Gems](../../tables/Gems.md) (68 records × 192 B, 2788 cells) and [Runes](../../tables/Runes.md) (169 × 288 B,
    7943 cells), `excel_bin.py diff` 0 mismatches on both; the only bytes no column covers are zero in every record
    (gems `+0x02C` padding; runes `+0x082`, `+0x084`). Layout `[C]`, meanings `[L]` beyond it. The item links are
    item record indices (s32); the mod blocks are 16-byte `code`/`param`/`min`/`max` as in the other item tables.
  - Surprises: a `T1Param` cell may hold a skill name, compiled to the skill's row index case-insensitively (109
    cells; `excel_bin.py` got a field option `names=` for it). `nummods` is not the number of mod lines (3 on every
    gem, 1 on every rune). `Runeword95` names two rows. `runes +0x082` is 0 in the file, and the one saved runeword
    (20639) is the string index of its row's `Name`, so it is likely filled at load (`[L]`, Phase 1).
  - Survey (`tools/socket_survey.py`, gate survey `socket_survey`): 78 `complete` rows (rune counts 2: 13, 3: 28,
    4: 25, 5: 9, 6: 3), 23 `server` rows (all complete), 508 property lines, **no classic-legal row** (every rune is a
    version-100 item); each complete row has at least one base by `itype`/`Equiv` and `gemsockets`.
  - Builder: `tools/d2s.py build` takes `sockets` (bounded by properties F5–F6) and `filled` (gems, runes, jewels,
    written after the parent at location 6), `store: "stash"`, and `keep_items` keeps a socketed item with its
    children; `tools/test_d2s.py` `SocketTest`. Recipes `socketnova.json` (expansion: bases of every item class with
    2–6 sockets, three pre-filled bases, runes for *Steel*, *Stealth*, *Lore*, *Rhyme*, *Malice*, gems, jewels) and
    `socketclassic.json` (classic, gems only).
  - Load check [run:2026-10-15-socket-saves](../../formats/experiments.md#run2026-10-15-socket-saves) (slot 3): both
    built saves entered the game and, after *Save and Exit*, every item came back field for field (stash included);
    both round-trip through `tools/d2s.py`. `store` 5 = stash is now `[C]` in d2s.md.
  - For Phase 1: the questions in the backlog entry "data questions from plan 0029 Phase 0".
- **2026-10-15 — Phase 2 landed (reverser, branch `lane/h29p2`; review requested in the backlog).**
  [run:2026-10-15-sockets](../../findings/items/experiments.md#run2026-10-15-sockets): 23 sessions on slots 1, 2 and 4,
  one character per session built from `tools/d2s_recipes/sock-*.json` (`tools/socket_sessions.py`), inserts
  played by the new `tools/d2pilot.py insert`, logger `tools/gdb/sockets.gdb`, model `tools/sockets.py`.
  - `tools/sockets.py check`: 351 inserts (346 packet, 5 save-reader), 50 runewords from 29 rows and 357 client
    verdicts reproduced, **0 mismatches**. 105/105 gem × group transfers; *Splendor* 5×, *Sanctuary* 4× (ranged),
    *Bramble* 2× (aura); refused runewords for wrong type, wrong order, magic/rare/crafted base, `quest` base,
    `server` row, the 3-of-4 *Bramble* prefix.
  - Tags raised in [items/0007](../../findings/items/0007-sockets-runewords.md): the insert and its test order, the
    tail placement, the match, the rolls on the completing child's seed, the refill, the load path above the clamps
    and the client test to `[C]`; open questions on the opcode (`0x28`), the client side, the rune seed and
    `kids[n]` closed. Symbols raised to C; `sub_004843E0_UiCanInsertSocket` added.
  - Short of the letter of the Done-when: the refused inserts are five different situations but four different
    first-failing tests (client: not a filler, not socketed, full; server: child unidentified), because the client
    test hides every other server refusal from clicks. The client's identified test is not reachable either: an
    unidentified socketed item lacks the socketed flag on the client (`[I]`, one case).
  - Surprises: a rune loaded from a save has item seed `{startSeed, 666}`, not a fresh game-seed draw as Phase 1
    expected; a rune is accepted in a classic game. `ITEMS_SetSockets`' clamps stay `[I]` (no insert runs it).
- **2026-10-15 — Phase 2 reviewed (architect): accept with fixes, fixes applied.** `tools/sockets.py check` rerun on
  the 23 logs of `sockets-run.lst` (manifest hashes verified): 351 inserts, 50 runewords from 29 rows, 357 client
  tests, 0 mismatches. Spot-checked on the pinned `Game.exe` with r2: `0x004843E0` (UI state, filler, flag `0x800`,
  `hasinv`, `ItemMaxSockets`, `0x10`, `0x100`, in that order), `0x006E0E58` (= `0x0054B650`, flag 1),
  `0x0062BED0` (quality 4..9 → no match, then base `+0x12A`), `0x0063B210`.
  - Ruling on the refused inserts: **the Done-when is met** by five refused situations with four first-failing
    tests. The server tests behind the client test cannot be reached by clicks, and the plan asked for refusals a
    player can cause; a forged `0x28` packet is not required. Consequence, recorded in items/0007: of the server
    refusals only the unidentified child is `[C]`; the others are `[I]` as refusals (seen passing, in order, never
    failing), and the spec states the server list as the authority with the client test in front of it.
  - Tags: the tail-placement raise kept `[C]` for the tail order, the count and mode 6 only; x = count and y = 0
    split out as `[I]` (not logged). The load-path raise is sound: the code read (§ 7, no quality switch) and the
    `forced` session's logged stat 194 (6/4/5/4 on magic, magic, rare, crafted) filled to the count.
  - Run record: the dropped calibration log is now stated with its times, the interruption and the `load` session
    that replaced it; it reproduces too (8 inserts, 0 mismatches), so nothing failing was dropped.
  - Doc fixes: the client test's order in items/0007 (the UI-state test is first, as in the code and the model);
    the Functions table tags brought in line with `re/symbols.csv`, `sub_004843E0_UiCanInsertSocket` added.
  - Phase 3 (spec-writer) can start after the merge.
- **2026-10-15 — Phase 3 landed (spec-writer, branch `lane/s29p3`; review requested in the backlog).**
  [items/sockets-runewords](../../specs/items/sockets-runewords.md), draft, **C 76 / I 70 / L 9**: § A the client test and
  § B the server insert as ordered refusal tables (the server list the authority, the client test in front of it; per
  the Phase 2 ruling only "child unidentified" is `[C]` among the server refusals, and of the client refusals the three
  the run produced), the option flags per caller, placement; § C the gem/rune mod group table and the transfer (no
  draw); § D `RUNEWORD_Match` as pseudocode, with the stale `kids[n]` slot; § E `RUNEWORD_Apply`, the "rune is the item"
  table per func, the refill; § F the two socket setters; § G the save side; § H the RNG call sequence. Worked
  examples: *Sanctuary* from run:2026-10-15-sockets (session `rw1`, three draws on Mal's `{startSeed, 666}` seed,
  recomputed with the rng step) and the game-written *Steel* save. Links added: items/properties § F (F6 note; its
  "four other callers" open question struck, L 5 → 4), items/README (file row, downstream), save/d2s (Tables row,
  after I5, the runeword-field open question struck, L 6 → 5), two glossary terms. 9 open questions; one new gap (the
  readers' `p5`) sent to the reverser.
- 2026-10-15 (architect): Phase 3 accepted with fixes; plan closed. Spot checks: all `fn:` anchors resolve in
  `re/symbols.csv` (gate E1), no `[L]` in the body, and Example 1 recomputes with `tools/rng.py` from Mal's
  `{0xD2E66F6E, 666}`: `0xA515A240 mod 31` = 12, `0x8A60DAE1 mod 21` = 20, `0xB088006A mod 53` = 1, ending at
  `{0xB088006A, 0x39B76FCB}`. Rulings: (1) **§ E func coverage**: which funcs the run's runewords reached is a
  reading of the run's `SLOT` lines, which is investigation; a spec cannot raise a tag on its own log count. The
  rows for funcs 1, 3, 8, 10, 21, 22 and 15–17 go to `[I]` (the finding gives them from the handlers, `[I]`); funcs
  2, 5, 6, 7, 19 and 23 stay `[C]` on the corroborated bullets of items/0007's Answer. The reverser records the per-func
  coverage in items/0007 (backlog), after which the spec may raise those rows. Fix applied: C 76 → 74, I 70 → 73 (gate
  count). (2) **`p5`**: handled honestly: the logged 0 at 0x00531355 is `[C]` (items/0007 Answer, the `load`
  session), the table's 1 for the other sites `[I]`, an *Open questions* entry, and the reverser backlog entry exists.
  (3) The server refusals follow the Phase 2 ruling: only "child unidentified" is `[C]` as a refusal, the client's
  three seen refusals `[C]`, the rest `[I]`. (4) The edits to the reviewed items/properties (F6 note, open question
  struck, L 5 → 4) and save/d2s (Tables row `tbl:Runes.txt:Name`, note after I5, open question struck, L 6 → 5) are
  links and agree with items/0007; both stay `reviewed`. `items/sockets-runewords` is **reviewed**.
- **2026-10-15 — Post-close update (spec-writer, branch `lane/r29fu`): tags raised from the reviewed items/0007
  follow-ups.** [items/sockets-runewords](../../specs/items/sockets-runewords.md) § E3: the rows for funcs 1, 3, 8,
  10, 21, 22 (`Roll`, func 3's reuse), 15–17 (no draw where `par` ≠ 0 or `min` = `max`) and 11 (no draw, level =
  `max`) are `[C]` on the per-func coverage table of items/0007 § 5 and run:2026-10-15-sockets; func 8's reuse branch,
  func 17's `par` 0 roll and func 11's ilvl branch are split into their own `[I]` rows, beside func 7's `+1` fallback
  and funcs 20 and 24; the "stay inferred until…" step note is replaced by a `[C]` coverage note. § B: the 0x00531355
  row is a plain `[C]`, the other reader rows cite items/0007 § 1 and stay `[I]`; the `p5` open question is struck.
  *Open questions*: plan 0032 dropped from the crafted-socket-cap item (Larzuk asks for 1 socket, items/0010 § 6;
  the case goes to plan 0030 Phase 2). Tags C 74 / I 73 / L 9 → **C 79 / I 73 / L 8**; open questions 9 → 8. The
  spec stays `reviewed`.
