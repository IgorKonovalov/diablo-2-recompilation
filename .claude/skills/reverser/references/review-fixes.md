# Common review fixes — reverser

Fixes the architect's reviews keep making on reverser lanes. One rule each; check your finding against
all of them before you file the review request. Review entries are in the plan logs named; the
categories are those of the [lane run ledger](../../../../docs/plans/metrics.md).

1. **A new code reading is `[I]`.** `[C]` needs a named second source (a reproduction of logged calls, a
   writer/reader pair, a full-table check, an independent tool). Don't name a meaning the code does not
   give. Seen: S1e rows 51/64 ([0038](../../../../docs/plans/0038-inferred-claims-sweep.md), 2026-10-17); `0x400` "good/evil"
   ([0040](../../../../docs/plans/done/0040-drlg-room-lifecycle.md) P1 review); a meaning word ("the missile count", "the
   charge speed", "moves the unit's path to its owner's point") inside a `[C]` of the batch's column-reader entry (`lane/p46m6`, `lane/p46m8` and `lane/p46m15` reviews,
   [0046](../../../../docs/plans/0046-skills-function-catalogue.md)); "the unit's full stat" for the `s` of anim/0002's ADR-0015 bonus map, where the map
   covers `UnitGetStat(unit, stat, 0)` only (`lane/p50b` review, [0050](../../../../docs/plans/0050-animation-frame-timing.md)).
2. **Recount every count from the binary with a kept command**, never from memory or a partial scan:
   writers, call sites, instructions, items. Copy a run's counts from the kept, hashed check output, never from an
   earlier check. Seen: bit-17 writers 5 → 21
   ([0039](../../../../docs/plans/done/0039-backlog-sweep-4.md) P1b review); S4b row 17 short by 9, "7" instructions for 8 (0038);
   eight wear and resurrection counts one off `check-run.txt` ([0043](../../../../docs/plans/done/0043-items-economy.md) P2 review);
   pool 12's "six of the 25 `boss` classes" met for five (`lane/h4a` review, 0038); "2 708 do events" in the record for the logs' 1 840, which hid the 2 000 skill-use floor's shortfall (`lane/p45h` review, [0045](../../../../docs/plans/0045-skills-missiles-machinery.md)); 318 pattern-5 creations for `patterns.txt`'s 360 (`lane/h5d` review, 0038); a 27-line manifest filed as "26 lines", and the 9 non-ItemStatCost `UpdateAnimRate` sites
   described without the scan's own breakdown (2 unidentified among them; `lane/p50b` review, 0050).
3. **Take totals against `main` after merging it**, not against the totals your batch started from.
   Seen: S2c, S3b and S1a reviews (0038), each recomputed; H3b's totals taken before the `lane/r1h` moves had landed
   (`lane/h3b` review, 0038).
4. **"Never", "only", "no X": say what the run separates.** If one case carries both readings (Andariel has
   flag `0x08` and `boss`), that half stays `[I]`. An observed absence counts only while a control is shown live over
   the whole window. Seen: resume-lane review
   ([0037](../../../../docs/plans/done/0037-combat-formulas.md)), re-scoped at the `lane/p37t` review; "sell draws only
   through item creations" with 2 unexplained sales, and question 9's absence after a control saturated in two frames
   ([0043](../../../../docs/plans/done/0043-items-economy.md) P2 review); a gamble window opened before the control's first
   line (0043 P2b review); 304 caster resyncs "not logged by this run" where 87 match the caster's own logged `THR`
   rolls (`lane/p45h` review, [0045](../../../../docs/plans/0045-skills-missiles-machinery.md)); "the breakpoint tables
   are not copied" where the lane's own check transcribes all 39 (`lane/p50c` review,
   [0050](../../../../docs/plans/0050-animation-frame-timing.md)); `PlrModeSkillFrame` writing the event index "at every
   player frame event" where a unit with no used skill returns 2 first (`lane/p50a` review, 0050); "the periodic save
   does not save without a host callback" with a logger at the entry only, where `0x00730FFC` and the time tests come
   before the callback test (`lane/h1b` review, [0038](../../../../docs/plans/0038-inferred-claims-sweep.md)).
5. **An existing reviewed symbol name wins.** Merge `main` and grep `re/symbols.csv` for every address
   before you name it; rename your side. Seen: six addresses named twice, `lane/p41r`
   ([0041](../../../../docs/plans/done/0041-stats-and-states.md) P1 review). The same holds inside `re/types/`
   comments: `MON_ModeEveryFrame` for the row's `sub_005A6B10_MonModeEveryFrame` (`lane/p50a` review,
   [0050](../../../../docs/plans/0050-animation-frame-timing.md)).
6. **Keep the tool behind every claim**: the script in `tools/` (seeded, if it generates cases), its
   output hashed, logs under `workspace/logs/` with a manifest line, one path base per manifest so `sha256sum -c` passes from one directory (H7a review, 0038; again 0043 P2 review), and every tool revision behind a cited output named. Seen: the unseeded `eval` case
   writer (S1e, 0038); the *Fleshripper* log left in session scratch (resume lane, 0037). An aborted session's
   partial log is kept as a development log, not deleted (0040 P2 review). A development run's outputs are written under their own names, not overwritten by the kept run
   (`lane/p46m9` review, [0046](../../../../docs/plans/0046-skills-function-catalogue.md)), and no kept file is renamed or
   reused under a name a kept manifest lists: the stub renamed so a session could run under its name broke one line of
   `manifest-r2-ckpt1.txt` (`lane/p48r2` review, [0048](../../../../docs/plans/done/0048-seed-to-world.md)); `-r2` reruns
   whose save copies overwrote the first sessions' copies under the same directory, and a dev manifest said to pass from
   the directory above its files (`lane/h1b` review, 0038); the crashed `--early` probes' logs and the crash files
   they left in the shared game directory deleted, not kept in `dev/`, and the session screenshots left outside the
   kept manifest (`lane/h3b` review, 0038).
7. **A conclusion needs an address, `fn:` or `run:` anchor**, not a link to another finding (gate W1).
   Seen: the resume lane's experiments addendum (0037); `lane/w1`'s 104 W1 lines (0039); the levels
   `+0x033..+0x035` refinement and the 18th `-txt`-only (`sounds`) call filed without their writer and call addresses
   (`lane/h3b` review, 0038).
8. **Split a raise where it has a remainder** and head the row "raised in part", in the ledger itself.
   Seen: special 65 (H4b), sock 14 (S2c), special 43 (S3b), all 0038; five `[C]` bullets of drlg/0009 § 11 with an
   unreached branch inside (the wanderer gate's `+0x78`, the item drop on expiry; [0040](../../../../docs/plans/done/0040-drlg-room-lifecycle.md) P2 review);
   sell's seed with five refusal tests unreached (0043 P2b review); spawn 41 filed raised with its "other sizes" half
   d-none (`lane/h5d` review, [0038](../../../../docs/plans/0038-inferred-claims-sweep.md)); the language clamp filed
   raised on a made-up `use` byte of 0x0E, where only edited data reaches it (ADR-0010: that half stays `[I]`,
   d-edit; `lane/h3b` review, 0038).
9. **Name the path for every claim about a caller**, or say "unfollowed" with the count. Seen: the
   superunique minion path (0039 P1b, Q19); the 8/9 case's `RoomTileSetFlags` call (0039 P1a); "the effect flag is 1
   only from handler 20" without `SKILLS_SrvDo`'s seven other calls, and `SKILLS_PayCost`'s 0 for a zero-cost row
   without its three calls, none of which tests it (`lane/p46m12` review, [0046](../../../../docs/plans/0046-skills-function-catalogue.md));
   "the only RNG call" of a call graph with 3 indirect calls unfollowed, and the mode graph's 118, left out of the
   text (`lane/p50a` review, [0050](../../../../docs/plans/0050-animation-frame-timing.md)); a logged load chain written
   without the two frames between `PlayerLoad` and the logged returns (`PlayerLoadFromFile`, `PlayerLoadFromClient`;
   `lane/h1b` review, [0038](../../../../docs/plans/0038-inferred-claims-sweep.md)); an undisassembled reader of the
   host callback, 0x0052BFC0, left "callers unfollowed" when one raw scan settles it, and the nearest indexed store
   (0x0052C134) left unbounded beside a "no block write" claim (`lane/r1h` review, 0038); a logged `EXCEL_FindName`
   return (0x0065A33B) credited to `TC_LoadAll` where it lies in `TC_BuildChestTable`, which `TC_LoadAll` calls
   (`lane/h3b` review, 0038).
10. **One case decides only if a wrong reading could not match it by chance.** Seen: aff 28's durability
    value, about one in eight (S2b, 0038). Count the cases that separate the readings, not the cases checked: a
    rounding needs a remainder (three curse lengths whose `MulDiv` is exact), and a model fix's counter is not its
    evidence (59 events counted, one separating; `lane/p47b` review, [0047](../../../../docs/plans/done/0047-simulation-shortfalls.md));
    Radament's `2 + r` escorts filed raised on r = 0 alone (`lane/h4a` review, 0038); `MonIsNpc`'s "`npc` or `inTown`"
    scored against `npc` alone but not against `inTown` alone, which every stock row also fits (`lane/h5d` review, 0038).
11. **"Moved" names the destination plan**; otherwise write "out of this plan". Seen: status bit 1
    (0039 P1b ruling 4); a closed entry's "(3) deferred" with no home (H7a review, 0038).
12. **Carry a correction into the section it corrects**, not only into the run's ledger section: the claim, its
    tables and the summary lists that repeat it. Seen: the summit door and the P1b summit-warp verdict
    ([0042](../../../../docs/plans/done/0042-quests-travel.md) P2 part 1 review); NPC 266's two draws, word 40's bit map and
    the switched-off reward writes, left in § 16 only (0042 P2 part 2 review); skills/0001's *Leads used* detail still
    naming start 25 for do 46's finisher calls after the § 12 note corrected it (`lane/p46m11` review,
    [0046](../../../../docs/plans/0046-skills-function-catalogue.md)); skills/0003 § 2's `EDX`-the-skill note filed under the
    bullet after the one that still said `EDX` the level (`lane/p46m12` review, 0046); class 312's remainder met by H4a but
    still `[I]` in monsters/0004's H4b section (`lane/h4a` review, 0038); special 66's mod 12, met by H4a (special 68)
    but still `[I]` in monsters/0003's H4b section (`lane/p51r` review, [0051](../../../../docs/plans/done/0051-backlog-sweep-6.md));
    drlg/0005 § 5's `[C]` *Pattern from size* still stating the `npc`-only rule with the correction appended after it
    (`lane/h5d` review, 0038);
    a summary that drops what the section states: stats/0001's Answer bullet for op 6/7 without the source-value gate
    and with op 7's "value" unnamed, and multiplayer/0001's MP31 cell calling the clipped offer a cancel (`lane/p51s`
    review, 0051); `re/types/anim.h` saying a monster frame function's 2 "ends the mode" against the finding's own § 6
    (the return is not read), and the summary's "S3 to S4" for a generic S3 that queues no event (`lane/p50a` review,
    [0050](../../../../docs/plans/0050-animation-frame-timing.md)); skills/0001's Answer bullet giving, inside its `[C]`, the client
    filter as the reason no refused request reached the server, which § 18 holds `[I]` (`lane/p45k` review,
    [0045](../../../../docs/plans/0045-skills-missiles-machinery.md)).
13. **At an observed boundary (ADR-0021), the `[C]` ends at the call.** What the callee makes of a compared argument
    (a class word, a register it must preserve, a mode) and every later call go in "After, `[I]`", also in the Answer
    summary. Seen: the radius of hits 24, 44 and 14 in a callee-saved register (`lane/p46m3` review); hit 52's row 0
    (`arrow`) and hits 51/52's later creations under `[C]` (`lane/p46m4` review, both
    [0046](../../../../docs/plans/0046-skills-function-catalogue.md)).
14. **Raise the symbols your run checks.** A function whose logged return the run compares with a model or a table row
    (and whose consumer agrees) is `[C]` in `re/symbols.csv` and the finding's Functions table, evidence column moved
    to the finding that holds the claim; don't leave it to the review. Seen: five H2b symbols (`lane/h2b` review fix 4);
    `sub_00633680_ItemIndexByCode`, `lsd ` → 31 logged 141 times (`lane/h2c` review, both
    [0038](../../../../docs/plans/0038-inferred-claims-sweep.md)). Scope: the return logged by the game on its own data. An
    ADR-0015/0021 emulation over a declared scratch image confirms the map, not the role the name states, and raises no
    symbol row (`lane/p46m12` review ruling 7, [0046](../../../../docs/plans/0046-skills-function-catalogue.md)).
    Seen also: `D2S_WriteMercItems` left I beside a raised `D2S_ReadMercItems` and `D2S_WriteCorpses` on the same evidence (`lane/h1b`
    review, 0038). `DRLG_LoadLevels` raised in `re/symbols.csv` but left I in data/0001's Functions table (`lane/h3b`
    review, 0038).
15. **State an integer wrap or overflow bound from a kept computation**: the largest input that still fits and the
    first that wraps, with the product written out, and what the code does past it. Seen: a negative ring step count
    called an endless loop where the signed index wraps past −2³¹ (`lane/p46m11` review); `PathDirection`'s
    `(minor << 16) × 0x7F` said to wrap past 257 subtiles, where 258 still fits (`lane/p46m13` review); do 105's
    `h·A` said to wrap as a 32-bit product where it cannot on any path that uses it, the subtraction after it being
    what wraps: name the operation that wraps and whether a wrapping path reaches a use (`lane/p46m14` review, all
    three [0046](../../../../docs/plans/0046-skills-function-catalogue.md)); do 140's try offsets said not to wrap "below
    2³¹ − 9" where 2³¹ − 9 itself still fits (`lane/p46m15` review, 0046); `x − 90q` said to wrap "for `x` within 270
    of `INT32_MIN`" where the bound is `x < INT32_MIN + 90q` (`lane/p51s` review, [0051](../../../../docs/plans/done/0051-backlog-sweep-6.md)).
