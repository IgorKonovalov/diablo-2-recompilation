# 0058 — Party and player count: the experience split, the share radius and every player-count effect, in one page

> **Status:** approved (owner, 2026-10-30: "approve all of them", every scoping question answered as recommended); drafted 2026-10-30 (architect, `lane/plans57`)
> **Created:** 2026-10-30
> **Owner skill(s):** reverser (phase 1), spec-writer (phases 2, 3)
> **Related ADRs:** 0008-two-client-harness, 0015-emulated-reproduction, 0017-scope-quests-travel-economy

## TL;DR

How is a kill's experience split among players, what bounds who shares, and what does the player count change across
the game? **Most of it is already specified**, so this plan is small: the split is
[player/creation § J4](../specs/player/creation.md#j-other-level-and-experience-changes) (`XP_PartyShare`: alive, same
level, distance² ≤ 6400, at most 8; `total = exp + ((n − 1) × exp × 89) ÷ 256`; the f32 quotient and the unrounded
member product; `[C]` for n = 2 by run:2026-10-20-two-clients), the level-difference penalty is § G3 (`[C]`), and the
player-count effects are spread over five specs. When it is done, the split is `[C]` for n = 3 to 8 by emulation, the
hireling's and the minion's credit are stated, and `docs/specs/player/party.md` (row `player/party`) composes every
party and player-count rule with links to the owning sections.

## Context

- **Where the pieces live now:** the split and the radius, player/creation J4 (n = 2 `[C]`; n ≥ 3 the same code,
  unrun); the penalty and the ratio, G3–G4; the death loss and the corpse's 75 %, J3 (`[I]`, unrun); the monster's hit
  points and experience at **+50 % per player beyond the first**, frozen at creation, monsters/stats § C1 (`[C]`);
  NoDrop and the drop count by players, items/tc; the crushing-blow divisor and `MonAttackStats` damage by the
  monster's stat 100, combat/README (`[C]` and `[I]`); the gold pickup's `PartyGoldShare`, items/economy G4 (`[I]`);
  quest credit to the party, quests/progression (e.g. the Ancients' e8 row); the case list,
  [multiplayer/0001](../findings/multiplayer/0001-cases.md) MP16.
- **The gap:** no page states these together; n ≥ 3 is unrun (the two harness slots give two clients, so a third
  player needs slot 0, the owner's); G6's mercenary cap and the minion credit of G0 are `[I]`; J4's record branch counts
  are one off (265 against 264 single inputs, already filed to the reverser).
- **Dependencies:** none open (player/creation, monsters/stats, items/tc, combat, items/economy are reviewed).

## Phases

### Phase 1 — The n ≥ 3 split and the credit edges, from the code and by emulation
- **Owner skill:** reverser (static; one headless Ghidra `-Xmx3G` at most; emulation under ADR-0015; no slot)
- **What:** emulate `XP_PartyShare` (`0x0057E6C0`) and `sub_0057E5A0_PartyXpCollect` (`0x0057E5A0`) over generated
  member sets for n = 1 to 8 (levels, distances at and around 6400, dead and other-level members, a ninth member) and
  check `tools/player.py`'s model against every output; read the mercenary's and the minion's credit (G0, G6) and the
  party definition the collector tests; close the 265/264 branch count entry if it is this code.
- **Outputs:** a section in [player/0001](../findings/player/0001-creation.md) (or `docs/findings/player/0002-party.md`
  if it passes 150 lines); `tools/player.py` updated; the emulation run's record in `docs/findings/player/experiments.md`.
- **Done when:** the emulated outputs match the model for every generated set (count stated), the member cap and the
  distance bound's edge are stated with the deciding instruction, and G0/G6 are `[I]` or better with anchors.

### Phase 2 — The page
- **Owner skill:** spec-writer (Opus)
- **What:** `docs/specs/player/party.md`: who shares (J4), how much (J4, G3–G4), what the player count changes at
  creation and at a kill (monsters/stats C, items/tc, combat, items/economy G4, quests), each rule restated with its tag
  and a link; Phase 1's results raise J4 for n ≥ 3 in player/creation itself, and the page links it.
- **Outputs:** `docs/specs/player/party.md`; player/creation J4 updated; `docs/specs/player/README.md`; research-map
  row `player/party`.
- **Done when:** every player-count reader the five specs name is listed with its input (the monster's frozen stat 100
  or the current count), each line links its owning section, and the gate is green.

### Phase 3 — Wiki
- **Owner skill:** spec-writer (wiki; Sonnet)
- **What:** a section of `docs/wiki/characters.md` (or its own page), no claims of its own.
- **Done when:** the section links the page and the wiki index is current.

## Resources and limits

- No harness slot in the recommended form. Ghidra at most one session, inside the two-Ghidra limit. P1 fits a static
  lane slot between 0052's and 0055's batches, or the archivist-free spec-writer queue for P2.
- **Estimate:** P1 one short reverser run; P2 one spec-writer run; P3 one short run.

## Owner questions (recommendations)

1. **A plan at all, or a section of the quirks index?** *Recommendation: this small plan*, because a reimplementer
   looks for "player count" in one place and the n ≥ 3 split is a real `[I]`.
2. **n ≥ 3 by emulation or by play?** *Recommendation: emulation* (ADR-0015 gives `[C]` for a function body over its
   inputs). A three-client run needs slot 0 and the owner; keep it an optional owner session.
3. **Row or section?** *Recommendation: its own file and row `player/party`* under Creation paths, since it is read by
   six specs.
4. **The death loss (J3) and the experience cap:** (the companion sweep is **owner 2026-10-30: may be drafted, as `draft` only, never started** (no plan after the approved roster is approved or started), so both stay `[I]` as stated) *Recommendation: leave them to the companion `[I]` sweep* (queued
   after 0055·P2a), which has the harness slots; name them there as targets.

## Open questions

- Whether `/players` changed mid-game re-reads any party rule (monsters keep their creation count; the drop count and
  the gold share are read at the event): stated from the code in Phase 1, run only if the companion sweep takes it.

## Implementation log

_(lanes append dated entries as phases land: what was found, the confidence reached, surprises)_

- **2026-10-30 — Drafted (architect, `lane/plans57`).** Status `draft`; rank 2. The survey found the split already
  specified (player/creation J4, `[C]` for n = 2), so the plan covers only n ≥ 3, the credit edges and the composed
  page; four owner questions.
- **2026-10-30 — Approved (owner; recorded by the architect, `lane/appr2`).** "Approve all of them": all four questions as recommended: this small plan; n ≥ 3 by emulation (a three-client run stays an optional owner session); its own file and row `player/party`; the death loss (J3) and the experience cap left to the companion `[I]` sweep, which the owner then limited to a draft that is not started, so they stay `[I]`. P1 takes static lane B after 0054·P1 per the run order. Status `approved`.
- **2026-11-03 — Phase 1 (reverser, `lane/r58a`).** run:2026-11-03-party-emu, 6 166 emulated kills, 0 mismatches ([player/0002](../findings/player/0002-party.md)). **The model was wrong and is fixed:** the distance is to the killed monster, not the credited player; the credited player is tested like the others, and n = 1 pays it whoever the member was (n = 0: nobody). The old model is kept as two negative controls; no log separates them. Member cap: `cmp eax,8` / `jl` (0x0057E662, 0x0057E665), a ninth that passes reaches the fatal path, not a clip. Edge: `cmp edx,0x1900` / `ja` (0x0057E654, 0x0057E65A), d² = 6400 stays in; d² wraps at 32 bits. G0 and G6 `[C]` as maps with anchors, the 40 logged mercenary kills reproduced. The 265/264 entry is closed: it was the record's cut-off kill (no open entry; J4's note stale). The open question: the split reads no player count; four think functions re-read `MonPlayerBonus` at their run. x87 values for n ≥ 3 agree but stay `[I]` by ADR-0015 (5). Phase 2 has a spec-writer entry for J4, G0 and the table row. New open: a player victim's award in play, a live far-killer case (both optional).
- **2026-11-03 — `lane/r58a` review (architect, Tier A): accept with fixes (9).** Reviewed on the lane, head `7c26cd1e`, which merged main `ad0c039e`; main has since moved to `aa771762`, and a trial merge conflicts only in `docs/plans/metrics.md`'s appended rows. Tier A because the lane overturns `[C]` statements of a reviewed spec. **Re-run:** the kept and both dev manifests pass; `party_emu.py check` and `mp_check.py xpshare` reproduce `check.txt` and `check-xpshare-all.txt` byte for byte; `cases` regenerates all five `.cases` and `.mem`; the tool hashes equal `tools-used.txt`; 15 unit tests pass. **Disassembly (objdump, pinned sha256):** the origin: `XP_OnMonsterKill` pushes `[ebp+8]`, the pointer it read stats 13 and 12 from, as `XP_PartyShare`'s second stack argument (0x0057EA6D, 0x0057EA75), stored at the block's `+0x00` (0x0057E6DA, 0x0057E6E7), read by the collector as `edi` (0x0057E5BE), so it holds. The n = 1 arm: 0x0057E70D–0x0057E733 use `ebx`, the credited player of 0x0057E6D3, and `[ebp+0x10]`, the level argument, and read no block slot, so it holds. Also as filed: the cap (0x0057E662, `jl` 0x0057E665, the first call at 0x0057E66C), the edge (0x0057E654, `ja` 0x0057E65A), G0 (0x0057E7B0–0x0057E856, the victim's `esi` store even when it is none), G6 (0x0057EA28–0x0057EA39, `cdq`, `and edx,0xFF`, `sar 8`), the party walk (0x005405A0, 0x00540710, 0x0063D450), the wrap numbers recomputed. **Fixes, in the documents:** overclaim 4: § 1's `[C]` map took in the gate and `UnitKilled`'s call, which no case runs (every case enters at 0x0057E990 or 0x0057E6C0); player/0001's "the caster" inside a `[C]`, the finding's "owner of a stat list with flag `0x800`"; `mercfull` credited with the exemption, which it does not separate; `dev-2` called the final tool, where its checker differs by one line. Omission 4: the logs separate neither correction, not only the distance (648 of 648 credited players in range), and 4 partied kills have no `KILL` line, so any of their pairs among the 431 are alike by construction; the member with y = 0, unreached (the review's perturbation `member-y0` fails nothing); `n1member`'s 282 = 243 + 39 of `evaluated-n1`; the spec-writer entry (below). Tool not kept 1: `EmuBoundary.java`'s new revision unnamed in the record. **Weighing.** (1) **Live case: not required** before the spec states either correction `[C]`. ADR-0015 (3) gives the map, and both are register-level data flow with no x87, fault or import, cited from objdump; condition (3)'s remainder is met by the logs: the pointer is the killed monster (`XK0`), its X is non-zero then (partied kills pay), the same getters on players predict the member sets. The statement carries its scope ("the code's map; no logged kill separates it"), and what follows in play (the far hireling, the dead killer) stays `[I]`. A live case is recommended, cheap with the next two-client session, and routed; it does not block. (2) **Earlier logged runs:** run:2026-10-20-two-clients showed the member sets and inputs at n = 1 and 2, and the `[C]`s it carried on those stand. It never showed the origin: "of the credited player" was the checker's assumption inside a `[C]`, and the kills cannot tell it from the monster's position because killer and monster were never on opposite sides of the bound. The same review failure as reverser rule 4, and the plan 0044 review passed it. run:2026-10-16-player has one player and says nothing of a party. (3) **Other documents repeating the old model:** spec player/creation (J4, its step notes, G0, the constants row) and wiki/characters' *Party share*, routed; docs/tables/States.md's `exp` `[L]`, now answered, routed; no other finding or spec: hirelings/0001, hirelings/README, Q25 and Q29 agree with the correction, items/tc and multiplayer/0002 state no party distance. (4) **dev-1's tool revision: acceptable.** No claim rests on it, its outputs and manifest are kept, the record says what it was, and `dev-2`'s five outputs are byte-identical to the kept run. This holds for a development pass only. (5) **The ten controls each separate what they name**, with two scopes now written or noted: `cap` (9) moves the ninth only, so its 60 `ten` cases pass; `mercfull` above. `f32product` separates the model, and its evidence stays the logs' 98 inputs. The review's own perturbations of `player.py` (session scratch, no tag rests on them) test what no control names: a clip at 8 fails 120 (`nine`, `ten`), a signed d² compare 3 (`wrap`), always cutting the mercenary 236, the victim's level for the credited player's 40, `Y = 0` tested on the victim 12, a none from the victim not winning 30, base and evaluated level swapped 40 and 39. So "not a clip", "unsigned" and "the victim's level is not read" are separated by the comparison, not only read. (6) **264 closed:** `check-xpshare-kills.txt` gives 222 + 42 single, 649 kills, 1 cut off; the archived entry exists; J4's note is stale and routed. **Rulings.** (a) **The raises' scope:** `XP_PartyShare` and `sub_0057E5A0_PartyXpCollect` to C stand, on the game's own logged `XC0` calls, per reverser rule 14: the role the name states, at n = 1 and 2, with 9 beyond, 109 in another level and 108 dead excluded. They raise neither the origin nor the cap, which keep the finding's tags; `sub_0057E7B0_XpCreditPlayer` and `sub_005A4EF0_KillExpGate` rightly `I`. (b) **x87 for n ≥ 3 stays `[I]`** though every case agrees: ADR-0015 (5) has no exception for agreement, and the emulator's float is the thing not evidenced. The reasons a reimplementer can rely on it are the same instructions as the logged n = 2 and player/creation's note that the product is exact in f64. A session at n ≥ 3 is the only way up. The plan's "`[C]` for n = 3 to 8" holds for the integer steps only. (c) **`trace` is admitted, and kept runs are unaffected.** It patches nothing and ends nothing, so ADR-0015 (1) holds and ADR-0021 does not apply; it is not a boundary. The 15 added lines are comments, the directive's parse, the set, and a block entered only for a traced pc; a spec without the directive prints what it did, and before this revision a `trace` line threw, so no earlier spec has one. Earlier records cite `286393aa…` and `0c88b790…`, both in git. (d) **Open items:** a player's award from a player and the live case stay `[L]`, not blocking; party-list writers, 0x005408CB and the gate's flag were left "not read" with no route, now routed to the reverser. **Spec-writer entry:** complete on J4's corrections, short of the tag split, the map's scope, the cap's scope, G0's one-member line, the wiki and the README pointer; added as items (7) to (14). `docs/specs/player/creation.md` states the old model under `[C]` until it lands, so that entry goes first in Phase 2's lane. **Phase 2 may start** once this lane merges. Research-map row `player/party` updated.
- **2026-11-03 — Phase 2 (spec-writer, `lane/s67`).** The correction first: [player/creation](../specs/player/creation.md) G0 (the credit in full), the G6 note (the mercenary's award, before the share and independent of it), J4 and its notes, the constants, all items (1) to (14) of the closed entry; C 139 / I 50 / L 1. Tags as ruled: the distance to the killed monster and the n = 1 credit `[C]` as the code's map with "no logged kill separates it"; the member set, the integer steps, n = 0 and the cap to its call `[C]` for n up to 8; what follows in play and past the fatal call `[I]`; the x87 steps `[C]` for n = 2 and `[I]` for n ≥ 3 under ADR-0015 (5). [hirelings](../specs/hirelings/README.md) G2 and the call path raised to `[C]` as the code's map with player/0002 § 5 (the entry asked for a link; the finding states the raise), C 143 / I 41 / L 7. The page: [player/party](../specs/player/party.md), `draft`, C 46 / I 22 / L 4 (the four `[L]` only under Open questions), 14 readers each with its input and owning section, the `/players` answer of player/0002 § 7, six notes. Quirks: Q446 to Q453, C 346 / I 107, `quirks.py check` 0 errors; Q25 and Q29 stand. Wiki: characters *Party share* and the levelling paragraph; Phase 3's section waits for this page's review. **Found while composing, filed to the reverser:** ai/0012 calls `MonPlayerBonus`'s word `b+0x0C` the player count, while the type and monsters/stats C1 have `+0x0C` as the difficulty and ai/0002 reads it so; held at `[L]` on the page. Status change to report at review: row `player/party` to reviewed.
