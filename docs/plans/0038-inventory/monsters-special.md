# Plan 0038 inventory: monsters/special

- **Spec:** [monsters/special.md](../../specs/monsters/special.md), read at `main` `e1c807a` (last change to the spec: `89686af`).
- **Front matter `I`:** 91; the *count* column sums to 91.
- **Finding:** [monsters/0003](../../findings/monsters/0003-special-monsters.md) (sections given as `§n`; other subsystems' findings named in full).
- **Cluster:** 0c (monsters, hirelings, player). Classes, tiers and batches as in [plan 0038](../0038-inferred-claims-sweep.md#classes).
- Guard rows marked (a-logs) with "0 → d-none" are re-read first: a guard the later logs never took is reclassified d-none by the batch, not raised.

| # | Spec section | Claim | Finding anchor | Class | Route | Tier | Batch | Count |
|---|---|---|---|---|---|---|---|---|
| 1 | [Entry points](../../specs/monsters/special.md#entry-points) | Inactive restore of a special or minion | §1, SpecialMonRestore 0x005A4440 | b | H4b logger lines at SpecialMonRestore/MinionRestore; leave and re-enter a level so a special's room goes inactive | T3 | H4b | 1 |
| 2 | [Entry points](../../specs/monsters/special.md#entry-points) | MonMakeSpecial from caller 0x00583050 | §1, MonMakeSpecial 0x005A4940 | b | read the caller statically first, then a session if stock play reaches it | T3 | H4b | 1 |
| 3 | [Tables](../../specs/monsters/special.md#tables) | Server handler table and its null rows | §4, g_UModHandlers 0x0073C008 | a-logs | HD0/HDX lines of the 12 `monspecial` and 11 `monstats` logs: every listed mod with a null row got no call | T1 | S3a | 1 |
| 4 | [Tables](../../specs/monsters/special.md#tables) | Always-run mods 1, 2, 3, 4 | §4, g_UModAlwaysMods 0x006E2168 | a-logs | the 606 seed-asserted handler calls already show the order; addendum | T1 | S3a | 1 |
| 5 | [Tables](../../specs/monsters/special.md#tables) | Aura table: eight rows | §4, g_UModAuraTable 0x0073BF68 | b | extend AUR to log the skill id and level written; H4b aura uniques | T1 | H4b | 1 |
| 6 | [Tables](../../specs/monsters/special.md#tables) | Champion name strings | §8, g_ChampionNameStr 0x006DA488 | b | client name logging extended to champions (string index per CN call) | T3 | H4b | 1 |
| 7 | [Tables](../../specs/monsters/special.md#tables) | Client handler table: rows 1, 12, 16, 36–39 | §8, g_ClientUModHandlers 0x00724D78 | b | as above | T3 | H4b | 1 |
| 8 | [Constants](../../specs/monsters/special.md#constants) | Unique mod cap: at most 9 mods | §2, 0x005A088F | d (d-none) | d-none: no stock special reaches 9 | T3 | - | 1 |
| 9 | [Constants](../../specs/monsters/special.md#constants) | THIEF 24 dropped from fixed mods | §6, 0x005A4AF0 | a-run | H4a Chaos seals: Lord De Seis (`Mod3` 24) | T3 | H4a | 1 |
| 10 | [Constants](../../specs/monsters/special.md#constants) | Aura classes: ubermephisto and Lord De Seis | §4, UModAura 0x005A1650 | a-run | H4a De Seis; the class-704 half is d-owner (Uber Tristram) | T3 | H4a | 1 |
| 11 | [Constants](../../specs/monsters/special.md#constants) | Name formats 1721, 1722, 11072 | §8, ClientMonNameBuild 0x004AC870 | b | client name logging (format index per call) | T3 | H4b | 1 |
| 12 | [A. Champion or unique](../../specs/monsters/special.md#a-champion-or-unique) | SpecialModsRoll header and four guards | §2, SpecialModsRoll 0x005A0760 | d (d-none) | d-none: difficulty ≥ 3, k ≥ 8, k + n ≥ 9 and m = 0 are never met on stock data | T3 | - | 5 |
| 13 | [A. Champion or unique](../../specs/monsters/special.md#a-champion-or-unique) | ModAppend full: writes nothing | §2, ModAppend 0x005A02E0 | d (d-none) | d-none | T3 | - | 1 |
| 14 | [B. The weighted picks](../../specs/monsters/special.md#b-the-weighted-picks) | ChampionModPick header; 256-candidate cap | §3, ChampionModPick 0x005A0500 | d (d-none) | d-none: MonUMod has 43 rows | T3 | - | 2 |
| 15 | [B. The weighted picks](../../specs/monsters/special.md#b-the-weighted-picks) | ModEligible header; MonTypeIsA exclusion true | §3, ModEligible 0x005A03E0 | a-run | H4b seeded hunt: Act II level whose pool holds `sandleaper1..5`; a unique sandleaper's pick shows `lightning` excluded | T1 | H4b | 2 |
| 16 | [B. The weighted picks](../../specs/monsters/special.md#b-the-weighted-picks) | MonTypeIsA matrix | §3, MonTypeIsA 0x005A0070 | a-run | as above (first call returning 1) | T1 | H4b | 1 |
| 17 | [B. The weighted picks](../../specs/monsters/special.md#b-the-weighted-picks) | Unique pick's inlined draw equals Range | §3, 0x005A06CC | a-logs | count unique picks with a power-of-two total among the 153 + monstats picks; both forms already reproduced | T1 | S3a | 1 |
| 18 | [B. The weighted picks](../../specs/monsters/special.md#b-the-weighted-picks) | Matrix reach and the sandleaper exclusion | §3, MonTypeReachable 0x00658460 | a-run | as the sandleaper row | T1 | H4b | 1 |
| 19 | [B. The weighted picks](../../specs/monsters/special.md#b-the-weighted-picks) | Champion-0 row with a cpick weight never picked | §3, 0x005A056F | d (d-none) | d-none: no stock row has the combination | T3 | - | 1 |
| 20 | [C. Mod handlers](../../specs/monsters/special.md#c-mod-handlers) | UModAura header (two mentions) | §4 | b | follows the aura lines | T1 | H4b | 2 |
| 21 | [C. Mod handlers](../../specs/monsters/special.md#c-mod-handlers) | Aura handler returns on flag 0 | §4 | a-logs | the 75 flag-0 aura calls of `monstats-s*` (TST: no change) | T1 | S3a | 1 |
| 22 | [C. Mod handlers](../../specs/monsters/special.md#c-mod-handlers) | Aura level ≤ 0 guard | §4, 0x005A1685 | d (d-none) | d-none | T3 | - | 1 |
| 23 | [C. Mod handlers](../../specs/monsters/special.md#c-mod-handlers) | Row count n by minLevel | §4 | a-logs | AUR `n` against `lvl` in the 12 + 30 aura draws | T1 | S3a | 1 |
| 24 | [C. Mod handlers](../../specs/monsters/special.md#c-mod-handlers) | n = 0 guard; local seed without MonsterData (two lines) | §4, 0x005A16EE | d (d-none) | d-none | T3 | - | 2 |
| 25 | [C. Mod handlers](../../specs/monsters/special.md#c-mod-handlers) | Lord De Seis forced index 5 | §4, 0x005A172C | a-run | H4a Chaos seals | T3 | H4a | 1 |
| 26 | [C. Mod handlers](../../specs/monsters/special.md#c-mod-handlers) | ubermephisto Conviction 20 | §4, 0x005A1748 | d (d-owner) | d-owner: Uber Tristram (cube organs) is beyond the pilot | T3 | - | 1 |
| 27 | [C. Mod handlers](../../specs/monsters/special.md#c-mod-handlers) | Aura skill level formula, clamp and skill (three lines) | §4, 0x005A1776 | b | AUR extended with the skill id and level written | T1 | H4b | 3 |
| 28 | [C. Mod handlers](../../specs/monsters/special.md#c-mod-handlers) | Group walk via MonsterData+0x28 over the leader's list | §4, MonGroupForEach 0x0058F380 | a-logs | TH0 unit sets against each boss's minion list in the 12 + 11 logs | T1 | S3a | 1 |
| 29 | [C. Mod handlers](../../specs/monsters/special.md#c-mod-handlers) | Aura table row values | §4, g_UModAuraTable | b | as the Tables aura row | T1 | H4b | 1 |
| 30 | [C. Mod handlers](../../specs/monsters/special.md#c-mod-handlers) | Superunique aura runs twice, same index | §6, SuperUniqueSpawn 0x005A49B0 | a-run | H4a Travincal (Bremm Sparkfist, `Mod1` 30) and Lord De Seis | T2 | H4a | 1 |
| 31 | [C. Mod handlers](../../specs/monsters/special.md#c-mod-handlers) | De Seis and ubermephisto also step the local seed | §4, 0x005A1727 | a-run | H4a De Seis (ubermephisto stays d-owner) | T3 | H4a | 1 |
| 32 | [C. Mod handlers](../../specs/monsters/special.md#c-mod-handlers) | Aura guards unreached by stock data | §4 | d (d-none) | d-none | T3 | - | 1 |
| 33 | [D. Per-mod draws](../../specs/monsters/special.md#d-per-mod-draws) | Row 0 `none`: null handler | §4 | d (d-none) | d-none: row 0 is never in a list | T3 | - | 1 |
| 34 | [D. Per-mod draws](../../specs/monsters/special.md#d-per-mod-draws) | Rows 10, 11, 13, 14, 15: null handlers | §4 | a-logs | specials whose lists held post-create mods in the kept logs; else (a-run) H4a (Treehead WoodFist, `brute2` 13) | T3 | S3a | 1 |
| 35 | [D. Per-mod draws](../../specs/monsters/special.md#d-per-mod-draws) | Row 12 `bloodraven`: client name only | §8 | b | H4a Blood Raven hunt with the client name lines | T3 | H4a | 1 |
| 36 | [D. Per-mod draws](../../specs/monsters/special.md#d-per-mod-draws) | Rows 19, 21: null handlers | §4 | d (d-none) | d-none: never in a stock list | T3 | - | 1 |
| 37 | [D. Per-mod draws](../../specs/monsters/special.md#d-per-mod-draws) | Row 23 `poisonhit` | §4, UModPoisonHit 0x005A1E00 | d (d-owner) | d-owner: only Baal Subject 2 (`Mod1` 23) carries it; unique weight 0 | T3 | - | 1 |
| 38 | [D. Per-mod draws](../../specs/monsters/special.md#d-per-mod-draws) | Row 24 `thief`: never written | §6 | a-run | H4a De Seis | T3 | H4a | 1 |
| 39 | [D. Per-mod draws](../../specs/monsters/special.md#d-per-mod-draws) | Rows 31–35, 40, 42: null handlers | §4 | a-logs | Act V uniques of `reanimatedhorde`/`frozenhorror`/`suicideminion` in `monstats-s3/s8/s9/s10` and `berserkf` logs (mods 33–35); 31, 32, 40, 42 stay d-none | T3 | S3a | 1 |
| 40 | [D. Per-mod draws](../../specs/monsters/special.md#d-per-mod-draws) | Row 41 `always_run_ai` | §4, UModAlwaysRunAi 0x005A1330 | d (d-none) | d-none: no stock special carries 41 | T3 | - | 1 |
| 41 | [D. Per-mod draws](../../specs/monsters/special.md#d-per-mod-draws) | Note: inferred rows never in a logged list | §4 | a-logs | follows the rows above | T3 | S3a | 1 |
| 42 | [E. Unique minions and transfer](../../specs/monsters/special.md#e-unique-minions-and-transfer) | UniqueMinions header; invalid class | §5, UniqueMinions 0x005A0C00 | d (d-none) | d-none | T3 | - | 2 |
| 43 | [E. Unique minions and transfer](../../specs/monsters/special.md#e-unique-minions-and-transfer) | Minion's own handlers not called; copied list is sent | §5, MonUnitPacketBuild 0x0053E2E0 | c | second path: the packet builder and the client's mod reader use the copied list | T3 | S3b | 1 |
| 44 | [E. Unique minions and transfer](../../specs/monsters/special.md#e-unique-minions-and-transfer) | A minion with c mods examines at most 9 − c | §5, 0x005A09A8 | d (d-none) | d-none: never binding on stock data | T3 | - | 1 |
| 45 | [F. Champion pack members and preset ch…](../../specs/monsters/special.md#f-champion-pack-members-and-preset-champions) | ChampionMemberMark header and two guards | §5 | d (d-none) | d-none | T3 | - | 3 |
| 46 | [G. Superuniques](../../specs/monsters/special.md#g-superuniques) | SuperUniqueSpawn header: the tails | §6 | a-run | follows the tail rows | T2 | H4a | 1 |
| 47 | [G. Superuniques](../../specs/monsters/special.md#g-superuniques) | Difficulty > 2; no record (two lines) | §6 | d (d-none) | d-none | T3 | - | 2 |
| 48 | [G. Superuniques](../../specs/monsters/special.md#g-superuniques) | Placed bit stops a non-stacking repeat | §6, 0x005A4A09 | a-logs | SU0 lines with the placed bit set in the 12 + 11 logs; none → (a-run) H4a re-entry of a superunique level | T2 | S3a | 1 |
| 49 | [G. Superuniques](../../specs/monsters/special.md#g-superuniques) | Five or more mods: nothing below runs | §6, 0x005A4AD4 | d (d-none) | d-none | T3 | - | 1 |
| 50 | [G. Superuniques](../../specs/monsters/special.md#g-superuniques) | Thief skipped; aura flagged (two lines) | §6 | a-run | H4a De Seis and Bremm Sparkfist | T2 | H4a | 2 |
| 51 | [G. Superuniques](../../specs/monsters/special.md#g-superuniques) | Second UModAura call | §6 | a-run | H4a, as above | T2 | H4a | 1 |
| 52 | [G. Superuniques](../../specs/monsters/special.md#g-superuniques) | Tail by record index, non-default cases | §6 | a-run | H4a sessions per tail below | T2 | H4a | 1 |
| 53 | [G. Superuniques](../../specs/monsters/special.md#g-superuniques) | Tail 6: the Countess | §6 | d (d-0032) | d-0032: the owner addendum's Countess sessions; add the `mon-stats.gdb` SUT tag to them ([backlog](../../backlog.md)) | T2 | - | 1 |
| 54 | [G. Superuniques](../../specs/monsters/special.md#g-superuniques) | Tail 10: Radament and his escorts | §6, 0x005A4CD1 | a-run | H4a: Sewers Level 2 waypoint, `--descend`, `hunt --mon-cls` radament | T2 | H4a | 1 |
| 55 | [G. Superuniques](../../specs/monsters/special.md#g-superuniques) | Tails 26, 27, 29: council quest hook | §6 | a-run | H4a Travincal waypoint, explore | T2 | H4a | 1 |
| 56 | [G. Superuniques](../../specs/monsters/special.md#g-superuniques) | Tails 36–38: seal bosses | §6 | a-run | H4a Chaos Sanctuary, `objop` on the five seals | T2 | H4a | 1 |
| 57 | [G. Superuniques](../../specs/monsters/special.md#g-superuniques) | Tail 39: the Cow King | §6 | d (d-0032) | d-0032: the owner addendum's Cow King session | T2 | - | 1 |
| 58 | [G. Superuniques](../../specs/monsters/special.md#g-superuniques) | Tail 42: Siege Boss escorts | §6, EscortSpawn 0x005B24E0 | a-run | H4a Bloody Foothills from Harrogath (`--any-level`) | T2 | H4a | 1 |
| 59 | [G. Superuniques](../../specs/monsters/special.md#g-superuniques) | Tails 43–45: Ancient Barbarians | §6 | b | new recipe with the Ancients quest open, `objop` on the altar; may fall to d-owner | T3 | H4a | 1 |
| 60 | [G. Superuniques](../../specs/monsters/special.md#g-superuniques) | Tail 60: Nihlathak and escorts | §6, EscortSpawn | a-run | H4a Halls of Pain waypoint, `--descend` to Halls of Vaught | T2 | H4a | 1 |
| 61 | [G. Superuniques](../../specs/monsters/special.md#g-superuniques) | Tail 62: Baal Subject 2 escorts | §6, EscortSpawn | d (d-owner) | d-owner: Throne of Destruction waves | T3 | - | 1 |
| 62 | [G. Superuniques](../../specs/monsters/special.md#g-superuniques) | Fixed mods skip ModEligible | §6, 0x005A4AF0 | a-logs | Megaflow Rectifier's fixed `rndname` (fPick 0) in run:2026-10-13-mon-spawn; addendum | T1 | S3a | 1 |
| 63 | [G. Superuniques](../../specs/monsters/special.md#g-superuniques) | One-bound MinGrp/MaxGrp gets no bonus | §6, 0x005A4B72 | d (d-none) | d-none: no stock record has one bound only | T3 | - | 1 |
| 64 | [G. Superuniques](../../specs/monsters/special.md#g-superuniques) | `Stacks` is the only repeat switch; no quest test | §6, 0x005A4A09 | a-logs | the 18 superuniques of the kept logs spawned for characters with every quest done (`quests: all`) | T1 | S3a | 1 |
| 65 | [H. MonPlace presets](../../specs/monsters/special.md#h-monplace-presets) | MonPlace 0x11–0x20 fixed classes and fallen variants | §7, PresetFallenVariant 0x0054E2A0 | a-logs | MU lines inside the RW1→RW4 windows of the kept logs (Black Marsh, Cold Plains, Stony Field); else (b) H4b PM lines for these cases | T1 | S3a | 1 |
| 66 | [I. Names](../../specs/monsters/special.md#i-names) | Client name header: the rest of I1 | §8 | b | client name logging | T3 | H4b | 1 |
| 67 | [I. Names](../../specs/monsters/special.md#i-names) | Minions get no name; superunique and champion names (three lines) | §8, ClientMonModsApply 0x004AD020 | b | client name logging | T3 | H4b | 3 |
| 68 | [I. Names](../../specs/monsters/special.md#i-names) | Blood Raven's name string 3111 | §8 | b | H4a Blood Raven hunt with the client name lines | T3 | H4a | 1 |
| 69 | [I. Names](../../specs/monsters/special.md#i-names) | Fixed boss strings for 156, 211, 242, … | §8 | b | H4a hunts of Andariel (156) and Izual (256) with the client name lines | T3 | H4a | 1 |
| 70 | [I. Names](../../specs/monsters/special.md#i-names) | String index 0 or unresolved gives empty | §8, 0x0096D4B4 | d (d-none) | d-none: every stock name row resolves | T3 | - | 1 |
| 71 | [I. Names](../../specs/monsters/special.md#i-names) | Builder re-seeds per call; champion name order | §8 | b | client name logging (champions) | T3 | H4b | 1 |
| 72 | [I. Names](../../specs/monsters/special.md#i-names) | `UniqueTitle` loaded and never read | §8, MonsterTablesLoad 0x0065A400 | b | watchpoint on the loaded table during an H4 session | T3 | H4b | 1 |
| 73 | [J. Other entry paths and pre-existing …](../../specs/monsters/special.md#j-other-entry-paths-and-pre-existing-mods) | Post-create mods by BaseId | §6, MonPostCreateMods 0x005B21B0 | a-logs | mod lists at MU vs BaseId in the 12 + 11 + 6 logs (Beetleburst's 20 is one case) | T1 | S3a | 1 |
| 74 | [J. Other entry paths and pre-existing …](../../specs/monsters/special.md#j-other-entry-paths-and-pre-existing-mods) | Restore and MonMakeSpecial paths | §1 | b | as § Entry points | T3 | H4b | 1 |

**Totals by class:** a-logs 14, a-run 20, b 23, c 1, d-0032 2, d-none 28, d-owner 3 (sum 91).
