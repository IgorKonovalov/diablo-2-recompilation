# 0062 — Debug and cut content: developer switches left in the exe, and data and code the stock game never reaches

> **Status:** done (closed 2026-11-04); was approved (owner, 2026-10-30: "approve all of them", every scoping question answered as recommended); drafted 2026-10-30 (architect, `lane/plans57`)
> **Created:** 2026-10-30
> **Owner skill(s):** reverser (phase 1), archivist (phase 2), spec-writer (phase 3)
> **Related ADRs:** 0001-target-toolchain-evidence-sources, 0002-scope-creation-paths-and-enablers

## TL;DR

What did the developers leave in the 1.14d `Game.exe` and its data that the stock game never uses? Debug switches and
command-line options, developer-only messages, table rows no spawner, warp or drop reaches, and code paths with no
caller. A reimplementer needs this list for two reasons: the switches that change behaviour (the harness already uses
some command-line options, and `/players` changes drops) must be known, and the unreachable rows must still be loaded
the same way so that indices do not shift. When it is done, a finding lists each item with its anchor and reach
(reachable by a stock option, by a switch, or never), and each switch that changes behaviour is a branch in its
owning spec. No spec row unless owner question 1 asks for one.

## Context

- **Where the pieces live now:** `GameTick`'s debug fault switch at `Game+0x1DC8` (values 1–4) and `g_ServerFps`'s
  setter with no caller, frame/0001 (`[I]`); `RangePow2Plus` with no caller and eight more unreferenced bodies, rng
  (`[C]`); unread table columns, data/0001 and data/excel; MonStats rows with no stock spawner and class 560 with no
  row, monsters/pool E2; levels 39 and 134 as named boundaries, drlg/outdoor; AI table rows no stock row names, plan
  0052 (the whole AI table, owner 2026-10-27); unused skill and missile functions, plan 0046's function index; the
  `-act` grants and other options the harness drives, player/creation J1 and the harness notes; `/players`,
  items/tc and monsters/stats.
- **The gap:** no single list; the command-line parser and the chat-command table (if any in 1.14d) are unread; the
  unreachable data rows are counted per spec but not together.
- **Dependencies:** none open. The AI and skill catalogues (0052, 0046) feed the "never reached" list as they land;
  this plan cites them rather than waiting.

## Phases

### Phase 1 — The switches, from the code
- **Owner skill:** reverser (static; one headless Ghidra `-Xmx3G`; no slot)
- **What:** the command-line parser (every option, what it sets, who reads it), any chat or developer command table,
  the debug globals the frame and the game structure carry, and the developer-only client messages (flagged in
  `g_SrvPacketTable`, if plan 0061 has not read them yet).
- **Outputs:** `docs/findings/archaeology/0001-switches.md`; `re/symbols.csv`.
- **Done when:** every option the parser accepts is listed with its target and its readers `[I]` or better, and each
  behaviour-changing switch names the spec section it changes.

### Phase 2 — The unreached data, counted
- **Owner skill:** archivist (no Ghidra)
- **What:** a survey over the tables of rows no stock path reaches, from the readers the specs already name (Levels
  rows with no warp and no waypoint, MonStats rows no pool, TC, summon or preset names, items with no TC, no vendor and
  no recipe, unused states and skills), each with the spec that defines "reach".
- **Outputs:** `docs/findings/archaeology/0002-unreached-rows.md`; `tools/unreached.py`.
- **Done when:** each table's count of unreached rows is reproduced by the tool, and each "unreached" cites the reader
  that would reach it.

### Phase 3 — The behaviour-changing switches into their specs
- **Owner skill:** spec-writer (Sonnet suffices)
- **What:** each Phase 1 switch that changes a specified outcome becomes a branch or an input of its owning spec, with
  the finding's tag; the rest stay in the findings. (The wiki covers reviewed specs only, ADR-0012, so the findings get
  no wiki page unless question 1 makes a row.)
- **Done when:** every behaviour-changing switch is named in its owning spec or listed under its open questions, and
  the gate is green.

## Resources and limits

- One static lane run with one Ghidra; one archivist run; one short spec-writer run. No slot.
- **Estimate:** P1 one reverser run; P2 one archivist run; P3 one short run.

## Owner questions (recommendations)

1. **Row or findings only?** *Recommendation: findings only, no spec row and so no wiki page*; a switch that changes
   behaviour goes into its owning spec as a branch (Phase 3). A row `archaeology` (and a wiki page over it) is the
   alternative if the owner wants the list readable outside the findings.
2. **Priority.** *Recommendation: last of this batch*; it fills a static slot when nothing higher is ready.
3. **Exercise the switches in the harness?** *Recommendation: no*, except the ones the harness already uses.

## Open questions

- Whether 1.14d keeps any developer chat command at all; the plan does not assume one.

## Implementation log

_(lanes append dated entries as phases land: what was found, the confidence reached, surprises)_

- **2026-10-30 — Drafted (architect, `lane/plans57`).** Status `draft`; rank 6 (archaeology, low priority); three
  owner questions.
- **2026-10-30 — Approved (owner; recorded by the architect, `lane/appr2`).** "Approve all of them": all three questions as recommended: findings only, no spec row and no wiki page (a behaviour-changing switch goes into its owning spec in Phase 3); last of this batch, filling a static slot when nothing higher is ready; no harness beyond the switches it already uses. Status `approved`.

- 2026-10-30 (archivist, `lane/a62`): Phase 2 done. `tools/unreached.py` and `docs/findings/archaeology/0002-unreached-rows.md`
  (numbered 0002 as named; 0001 is Phase 1's and does not exist yet). Unreached by table readers: Levels 5 of 137, MonStats
  129 of 734 (98 enabled), Skills 13 of 357, States 58 of 185, Misc 26 of 659 items (Weapons and Armor 0). All counts are upper
  bounds where code passes an immediate id; the finding's Gaps list what was not read (Objects, Missiles, Shrines, recipes).

- 2026-11-04 (reverser, `lane/r62a`): Phase 1 done, for review. [archaeology/0001](../../findings/archaeology/0001-switches.md), `tools/switches_scan.py`, 51 symbol rows; no emulation. Three parsers, not one: `g_CmdLineOptions` (58 rows, 55 offsets), the module names (6, by a separate `strtok`) and a registry-only table (9, `Default Command Line`; the routine that would feed it the command line has no reference). 17 rows have no traced use, among them `-rare -unique -nm -m -i -cheats -questall`; `-opengl` is cleared after parsing. Behaviour-changing, with sections, in § 7; `-nosave` is in no spec. Chat: `/fps /framerate /players /nopickup`, the unslashed `soundchaosdebug`, and no command table, which answers this plan's open question within the compare scan. `Game+0x1DC8`'s writer and `SetServerFps` have no reference; `g_SrvPacketTable`'s flag has no reader. [Review request](../../backlog/archive/2026-11-04-reverser-architect-plan-0062-p1-review.md); [Phase 3 input](../../backlog/archive/2026-11-04-reverser-spec-writer-plan-0062-p1-switches-for-phase-3.md). Open: the server's reader of `-arena`, `0x0051ED00`'s text commands, `0x00450950`'s copy of `+0x1DC8`, and whether sound behind `-ns` draws from a tracked seed.

- 2026-11-04 (reverser, `lane/r63`): the `-ns` priority, for review. **It went this way: no rerun is ordered now; the paired session (archaeology/0003 § 6) decides.** `-ns` changes draws only on the client player's seed `[0x007A6A70]+0x20` `[I]`; no server seed is on the draw-site list (15 skipped bodies, 451 sound-return call sites, 257 indirect calls unfollowed). 20 kept `--sound` logs hold every seed-stream checker at 0 mismatches, and the map-seed chain matches `-ns` logs of the same seed on 63 of 63 levels and 1152 rooms `[C]`. Still not known: the game seed under identical inputs, and whether the device opened in those runs, since a checker's 0 can't see a game-seed draw between its windows. The session that settles both is [archaeology/0003 § 6](../../findings/archaeology/0003-sound-draws.md#6-the-case-for-the-next-harness-run), filed for the next harness run. `tools/sound_draws_scan.py`, `tools/sound_pair.py`, run:2026-11-04-sound-logs, 23 symbol rows; no game started, no emulation.

- 2026-11-04 (architect, `lane/r63` Tier B check): process slip, not repaired: the first decompile of the lane ran Ghidra with the default 8G heap, against the memory-budget rule (`-Xmx3G`). Nothing to repair.

- 2026-11-04 (reverser, `lane/snd`): the sound pair session of archaeology/0003 § 6 ran on slot 2 (run:2026-11-04-sound-pair, [archaeology/0003](../../findings/archaeology/0003-sound-draws.md) § 7). **Two `-ns` runs agree; the device opened under `--sound`; the game seed's stream is identical with and without sound for the walk tested** (seed 12345, act-5 save on Normal, Harrogath pop steps, 147 `gs` values, 14 level creations, every seed field of every logged line equal) `[C]`, scoped to that one walk. The client player's seed differs A vs B, but also between the two `-ns` runs, so it does not separate sound (stays `[I]`). No rerun of a kept run is ordered by this session. `tools/gdb/sound-pair.gdb`, `tools/gdb/sound-pair.steps` new; logs `workspace/logs/snd/` with `manifest-snd.txt`. Request filed to the architect.
- 2026-11-04 (spec-writer, `lane/s69`): Phase 3 done, for review. P1 accepted with fixes (Tier B, `lane/r62a`), P2 done. save/d2s C1 and C2: `-nosave` `[I]`. player/creation § Entry points: the class rows, `-name`, `-ctemp` `[I]`. items/economy G10: `-gametype` as a source of `g_ClientGameMode`, `-arena`'s write `[I]`, the server's reader of `+0x207` under open questions `[L]`. items/tc F2 and player/party § E lacked the client-mode gate on `/players` (modes 0, 1, 6, 8): added `[I]`. `-seed`, `-act`, `-txt`, `-direct` were already stated. `-ns` stays with archaeology/0003 § 6: no spec names an outcome that depends on it.

- **2026-11-04 — `lane/s69` review (architect, Tier A): accept with fixes (10: overclaim 3, misread 2, omission 3, wrong anchor 1, under-claim 1).** Covers the backlog sweep and this plan's Phase 3. **Overclaim:** quests/travel B1 held "`other` is a walk's origin" inside the `line` `[C]`: `line` runs the walk alone, and the search's handing `other` to it is `drop`'s (items/0014 § 6), now its own `[I]` (`drop`, pending). drlg/lifecycle G1's "so no game reaches it" in a `[C]` sentence, now the frame count only, and the wrap stated at 32 bits, read signed by the sweep (G1 returns `u32`). wiki/saves' "both file writers": `SaveViaCallback` is the hook's path, not a file writer. **Misread:** `-arena`'s `+0x207` and `+0x209` are offsets of the config block `g_ClientConfig` (0x00477D07), not of the message, carried from archaeology/0001 § 7: the message takes the words at `+0x25` and `+0x27` (0x00477D3A, 0x00477D44, message at `[ebp-0x30]`); items/economy G10 and its `[L]` rewritten. Missiles H1's "logged before the callback" for all 654: 618 are, the 36 of `0x005AC040` are read at `MissileCreate`'s exit (`tools/path_emu3.py` `cmd_h1log`). **Omission:** B1's `dx`, `dy` values, which a reimplementer can't get without the binary (read from the image, equal to `tools/item_inventory.py`), and the centre 128 `[I]` that items/0014 § 1 keeps out of the `[C]`; G2's field end had no radius or step, the pair form pushes 50 and 1 (0x0064E81C, 0x0064E81E), so "the portal's size 3 and step 5" is two ends, stated apart; lifecycle § A left out `DropGoldPile`, in the no-expiry group of items/0014 § 3. **Wrong anchor:** Q128 said `PathPlan` steps the seed on the old anchors. **Under-claim:** catalogue R2's walk and low word sat under the trailing `[I]`, now `[C]` by H4. Tags: quests/travel I 89, catalogue C 257. **Rulings.** (1) `drop` at `[I]` pending ADR-0029 is right, and rising with no re-run is what the ADR says of the emulation; the raise is not free, since the ADR keeps its lock scan as a lane tool output, so it goes finding first (a reverser lane), then the three B1 bullets. G2's note stays `[I]` either way: size 3 was not run. Check: `drop`'s statements match items/0014 §§ 1, 6 and the pseudocode matches its loops. (2) G1's raise to `[C]` beyond the entry is **accepted**: review-fixes rule 8 asks for it, and the `expiry` family was accepted at the `lane/r60c` review. The disassembly of `0x00558A10` gives every line (`0x00558A1E`, `0x00558A2B`, `0x00558A36`, `0x00558A4C`, `0x00558A5B`, `0x00558A76`); the family runs the real callees over a declared item, 600 cases in all 4 outcomes, three controls. It is scoped: ADR-0015's map from the bytes, "not logged in a game" on both lines, in the Constants row and in the open question, and nothing says when the game takes these branches. (3) § A's no-expiry `[I]` with the `[L]` for Phase 2 case 7 is right: it carries the finding's limits (block copy, deeper chains unfollowed). The sweep's `[C]` holds to `UnitGetRoom` only. (4) Phase 3's inclusion is fine: the phase was ready, Sonnet-sized, and in the plan. **§ 7's "stated" column, unverified at the r62a check, is verified here:** `-seed` (rng/seeds Entry points, step 2's config row; the finding's "step 1" is loose but the statement is there), `-act` (player/creation Entry points, B5), `-txt` (data/excel § B, data/calc § C, data/strings), `-direct` (data/README Data flow), `-gametype`'s value (items/economy G10), `/players` (items/tc F2, player/party § E). All hold. Against the disassembly: `-nosave` (0x0044D58B into 0x00530F30; 0x00531ED1 returns 0; 0x00532257 jumps to the exit), the class rows (0x0044D6B9–0x0044D6F9: 0, 3, 1, 2, 4), `-ctemp`'s test, the `/players` gate and clamp (0x0047C4B4–0x0047C4F3, 0x0047C536). `g_SaveEnabled` has two direct reads, so `-nosave` does not stop the client-buffer path, and C1, C2's "neither writes" is scoped to the two. (5) The oracle rows narrowed and kept: right until `path/search` is reviewed; path/0003's own entry asks for that order. (6) H1's `[C]` "logged in the game" holds: the manifest of `workspace/logs/r54c` passes, `path_emu3.py check` reproduces `check.txt` byte for byte, `p3-h1log.txt` gives 442, 176 and 36 at 0 mismatches, the bodies of both callbacks and `PathSetByte90` read as stated, and the stock rows give `Range` 40, 98, 20 with blank `LevRange`. This is the promotion re-check, since path/0003 had a Tier B check only. The `[I]` on the logged range equalling the row's stays: the tool tallies the range per class and does not read the table, so the equality is two outputs read side by side, and it is the finding's tag. (7) **The wiki is reconciled.** I read the sentences on the four pages: monsters and seed-to-world say nothing of expiry, sweep, free cell or missile re-seeds that changed; objects says nothing of a chest drop's lifetime; randomness' "the new missile's own path setup then advances" still holds and makes no "not read" claim. No stale sentence behind a moved date. Of the changed pages only saves needed a fix. (8) The map's `lane/s69` rows are final, and the six `lane/s68` rows still reading "review pending" with them (my miss at that review). **Routes:** [reverser](../../backlog/archive/2026-11-04-architect-reverser-s69-review-finding-corrections.md) (archaeology/0001 §§ 5, 7, open question 1; path/0003 § 10). [Request closed](../../backlog/archive/2026-11-04-spec-writer-architect-lane-s69-review.md). **Plan 0062:** every phase is done and reviewed and its *Done when* is met, so it can close at this merge. Left outside it: `-arena`'s server reader (plan 0061 P1), the sound pair session ([entry](../../backlog/archive/2026-11-04-reverser-reverser-sound-pair-session-next-harness.md), next harness run), and archaeology/0001's minor open questions. Gate green; `tools/quirks.py check` 0 errors.
- **2026-11-04 — Closed (architect, `lane/c62`).** All three phases are done and reviewed (P1 and P2 by the lane checks, P3 at the `lane/s69` Tier A review) and the *Done when* of each is met; moved to `done/`, links rewritten. Left outside it: `-arena`'s server reader (plan 0061 P1), archaeology/0001's minor open questions.
- **2026-11-04 — `lane/r70` (reverser, correction after close).** The `lane/s69` review's three corrections to archaeology/0001 are made as dated corrections: `+0x207` and `+0x209` are offsets of `g_ClientConfig`, copied by `ClientGameCreateMsg` to the message at `+0x25` and `+0x27` (§ 5, § 7, open question 1); § 7's "not stated: Phase 3" and "to be checked" cells and the "`-nosave` is in no spec yet" bullet now read stated. path/0003 § 10's "all 654" is corrected (plan 0054).
