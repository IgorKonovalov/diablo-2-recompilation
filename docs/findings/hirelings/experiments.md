# Hirelings: runtime experiments

Run records for [hirelings/0001](0001-hirelings.md). Harness and evidence rules: ADR-0003, ADR-0004, ADR-0011;
[tooling](../../../.claude/skills/reverser/references/tooling.md), [harness-play](../../../.claude/skills/reverser/references/harness-play.md).

## run:2026-10-16-hirelings

- **Question:** plan 0033 Phase 2. Does `tools/hirelings.py`, the model of hirelings/0001 (`HIRE_BuildStock` from
  the NPC seed, `HIRELING_RollEntry`, `MERC_SetLevel`, the save's level loop, `MERC_Create`'s classic act test),
  reproduce every logged hire table, list entry, hire, mercenary level and stat block, and every mercenary loaded
  from a save? Does `tools/monpool.py` reproduce the MonStatsInit level of the five hireling classes (the
  monsters/pool open question)? Does a mercenary's kill count its owner's magic find? Boundary (architect ruling,
  plan 0033 log): the NPC seed S is asserted at each `HIRE_BuildStock` entry against the chain of the model's own
  draws since the last known S; vendor draws on S would be an oracle (none happened: no trade or gamble window was
  opened in this run); one check per game that S = `Init(low of the game seed's step)` at `NPCSTORE_CtlCreate`.
- **Setup:** agent-driven sessions on harness slot 1 (display `:8`, prefix `workspace/wineprefix-1`), single player,
  pinned `game.exe` in `workspace/runtime/game` (stock data), gdb by `tools/d2run.py`, `-seed` per session. Logger
  `tools/gdb/hirelings.gdb` (`c5145380…`) sourcing `tools/gdb/pilot.py` (`1ad48a4c…`), `tools/gdb/vendors.py`
  (`eddbff8c…`, unchanged; its `NPC`/`OBJP`/`TICK` lines steer the pilot, `VSC0`/`VSC1` give the NPC seed),
  `tools/gdb/mon-pool.py` (`2c17c655…`, unchanged; `MPS`/`MPR`/`MLV`/`CR*`) and `tools/gdb/hirelings.py` in two
  revisions: r1 for sessions 3301–3361 (`MFK` without the owner's read), r2 (`869a5d89…`, 0cc3242) for 3371, which
  adds the breakpoint at 0x005585FB (the game's read of the owner's stat 80) and the owner's full-list stat 80; no
  other line changed. r1 was never committed (0cc3242 holds r2 only), so its hash is not recorded; the r1 logs are
  pinned by the run manifest, every r1 line other than `MFK` has r2's format and is read by the same checker, and no
  r1 `MFK` line is used (the three kills are 3371's) (review ruling, plan 0033 log). Breakpoints only print and continue. Driver `tools/hireling_sessions.py` (0cc3242):
  `tour` (from the Act IV start, the town waypoint and a `wpchain` hop, capped with `timeout`, to each seller's town;
  `d2pilot.py npc <log> <seller> hire` opens the list and Escape closes it), `--buy NPC:K` (`d2pilot.py npc … hire
  --buy 1`: the top row K times, Yes in the "This Mercenary will replace your current one" box), `load` (one game per
  save, ended after `MSX`), `kill`. Each session installs one save with `d2run.py --install h33p2` after
  `saves.py --slot 1 restore`/`aside`, and ends with `slots.py stop 1` and `saves.py --slot 1 restore h33p2`.
- **Characters** (ADR-0003 tool-built inputs; no test-state key): `VendorNova` (`vendornova.json`, expansion, clvl 30,
  `eed8939c…`), `VendorNova75` (`vendornova75.json`, clvl 75, `dc2ca939…`), `MercNova` (`mercnova.json`, `1a80a833…`),
  `MercClassic` (`mercclassic.json`, classic, `69381d3a…`), `MercMF` (`mercmf.json`, new: `mercnova.json` with
  *Chance Guards* and *Wartraveler*, `e98a6b9d…`), the 21 saves of `tools/merc_saves.py` (hashes in its output, as
  run in Phase 0), and 9 classic act variants from `hireling_sessions.py saves` (`Merc<cls><n|m|h>ca`: the classic
  saves with difficulty bytes `0x80 | act − 1` of the mercenary's act, so that `MERC_Create` meets the act it
  tests). All start in the Act IV town except the act variants.

### Sessions

| seeds | save | difficulty | what | lists | hires |
|---|---|---|---|---:|---:|
| 3301 | VendorNova | Normal | tour (Greiz: the pilot walked into the sewer; Kashya not reached) | 2 | 0 |
| 3302, 3303 | VendorNova | Normal | tour, nine hires at Kashya each (the 10th hire's list was too short for the pilot's list detection, fixed after) | 8 | 18 |
| 3304 | VendorNova75 | Nightmare | tour, nine hires at Qual-Kehk | 4 | 9 |
| 3305 | VendorNova75 | Hell | tour, four hires at Asheara | 4 | 4 |
| 3306, 3307 | VendorNova | Nightmare, Hell | tour, four hires at Kashya / Qual-Kehk (clvl 30 below the band: `d < 0`) | 7 | 8 |
| 3308–3314 | VendorNova, VendorNova75 | the three | tours | 26 | 0 |
| 3320 | VendorNova | Normal | ten hires at Qual-Kehk, then the list opened again (the rebuild) | 2 | 10 |
| 3330–3361 | MercNova, MercClassic, the 21 merc saves, the 9 act variants | the save's | one load each | | |
| 3371 | MercMF | Normal | Cold Plains; the character walks, the mercenary kills | | |

Calibration, not part of the run: `hire-dev-s1-probe1` (the first logger, whose `MIN` read the `{name, seed}` block
in the wrong order; 10 hires and a rebuild by hand) and `hire-dev-s1-3370-kill` (logger r1: the owner's stat 80 read
from the base list, which holds no item bonus). Greiz failed in four tours (3301, 3306, 3308, 3314: the pilot gave
up after 60 s, once walking into the sewer); every other opening succeeded. Run list `workspace/logs/hire-run.lst`
(`79ddb047…`, 48 logs), per-file sha256 in `workspace/logs/hire-run-manifest.txt` (`4559f158…`).

### Procedure and result

```
python3 -I tools/hirelings.py check workspace/merged/data/global/excel $(cat workspace/logs/hire-run.lst)   # exit 0
python3 -I tools/monpool.py  check workspace/merged/data/global/excel $(cat workspace/logs/hire-run.lst)   # exit 0
```

`tools/hirelings.py check` (trimmed; the full output is `workspace/scratch-h33p2/run-check.txt`):

```
logs 48, games 48
NPC seed = Init(low of the game-seed step)                                       48
NPC seed from game-seed draw 3 (gs after 2 steps from Init(-seed))               48
S at HIRE_BuildStock entry = the model's chain                                   53
hire table (69 entries: name, seed, hired, listed)                               53
S after HIRE_BuildStock (n + 10 draws)                                           53   (draws on S 2625)
first builds 52 (trigger HIRE_SendList at the first interaction); rebuild 1 (HIRE_RebuildIfEmpty)
rebuild only when no listed, unhired entry is left                               1
HIRELING_RollEntry: client list draw 530, HIRE_Hire 49, MERC_Init 72, client merc init 72
client list entry is a listed, unhired entry of the table                        530
hires 49: price paid = RollEntry price 49; gold first, then the stash 49; MERC_Init {name, seed} = the entry 49;
  hired class = Class of the seller's Normal row 49; fresh hire level = RollEntry level 49
merc headers read 33; MERC_Create: act = HIRELING_GetAct(name) 33; created as the model says 33;
  loaded level from experience 23; loaded class = the saved Id's row Class 23
MERC_SetLevel row (band) 72, stats 72, skills 72; stats clamped to 0 (absent from the list) 16
  cases: hire d>0 30, hire d<0 19, load d>0 2, load d=0 21
  levels where Resist/Lvl /4 and /8 differ 32; levels where truncation and floor differ (d < 0) 17
hire lists built (seller, difficulty): Asheara 6/4/4, Greiz 3/3/4, Kashya 5/4/4, Qual-Kehk 8/4/4 (53)
list entry level minus player level (client draws): -5:109 -4:92 -3:112 -2:107 -1:110
mercenary kills 3: own stat 80 0, owner (the player, type 0) read 40 = its full-list stat 80 40, total 40
hirelings: 0 mismatches
```

`tools/monpool.py check`: `monpool: 10788/10788 match`. The mercenary creations among them (`MLV`, class: game
difficulty → level, `d`): 271 Normal/Nightmare/Hell (expansion 21/5/1, classic 1/1/1), 338 (1/1/1 each), 359
(expansion 13/9/13, classic 1/1/1), 561 (expansion 11/10/5): every one level 1 with `d` = 0, where MonStats
`Level(N)`/`Level(H)` are 34/67 for 271, 338 and 359.

### Cases

- **Hire lists** of Kashya, Greiz, Asheara and Qual-Kehk in Normal, Nightmare and Hell (expansion), 53 builds ≥ 50,
  each table bit for bit and S after it; one rebuild in one game (3320: the 10th hire emptied the list,
  `HIRE_RebuildIfEmpty` built a new table from the chained S inside `HIRE_Hire`, and the list opened after it shows
  that table's entries).
- **Hires:** 49 ≥ 20, each mercenary's level, row, stats and skills after `MERC_SetLevel` reproduced: clvl 30 in
  Normal (`d` 22..26 on the band-3 rows), clvl 75 in Nightmare and Hell (`d > 0`), clvl 30 in Nightmare and Hell
  (`d` −11..−41 below the first band: life clamped to 40, AR and defence clamped to 0 and so absent from the stat
  list, truncating division where floor would differ in 17 levels).
- **Loads:** `MercNova` (the Rogue of `mercnova.json`, L 30 from 2 790 000 experience; the same mercenary block in
  `MercMF` showed Short Bow, Leather Armor and Cap equipped and the screen's level 30, next level 3 075 200, life 288,
  resistances 54, `workspace/logs/hire-shots/merc-inventory-s1.png`); `MercClassic` (classic Act IV start, Rogue
  of Act I: not created); the 12 expansion merc saves (271, 338, 359, 561 × the three difficulties, each in its
  difficulty: created, level from experience); the 9 classic ones from the Act IV start (not created: `MERC_Create`
  returns 0, `pact` 3 ≠ `mact`) and their 9 act variants (created, level and stats reproduced). Class 560 has no
  `hireling.txt` row: no save and no hire can make it (unreachable on stock data, as Phase 0 recorded).
- **Magic find:** three kills by the `MercMF` Rogue: `ITEMS_DropMagicFind` read the mercenary's stat 80 (0) and
  its owner's (40, the player's full stat list with the gloves' bonus), total 40.
- **Phase 1b cases:** (a) `Resist/Lvl` ÷4: 32 mercenary levels where ÷4 and ÷8 differ, every resistance as ÷4 (e.g.
  Normal Rogue, `Resist/Lvl` 8, band 3, L 27: 48); (b) the list level: the 530 client list entries lie at
  player level −5 .. −1 (no entry above the player; the `max(2, …)` floor not reached at clvl 30 and 75).

### Review check (architect, plan 0033 Phase 3)

`tools/hirelings.py check` does not compare a load's `MIN` `{name, seed}` with the header. Recounted read-only from
the same 48 logs (a scratch script over the `MRH`, `MCA` and `MIN` lines, not kept): 48 `MRH` headers, 15 all zero
(no `MCA` follows any of them) and 33 not; for the 23 created loads, `MIN`'s seed = the header's seed, `MIN`'s name =
the header's name + the Id's first-row `+0x114`, and `MIN`'s Id = the header's Id, 23 of 23 each (saved name values
0 in 21 loads and 3 in 2); no header had the dead bit set.

### Limits

No classic hire list and no classic hire (the classic `Version` 0 rows are exercised by the 9 classic loads, through
`MERC_Init`'s `RollEntry` and `MERC_SetLevel`); no Greiz hire; no free mercenary (`HIRE_GiveFreeMerc`); no refused
hire (Kashya's level gate, Qual-Kehk's quest gate, too little gold); the stash part of the payment (inventory gold
always sufficed); no hire of an unlisted entry; no build through `NPC_OpenStore` (Asheara's trade was never opened
first); no mercenary level-up in play (`MERC_AddExp`); no dead mercenary in a save; no multiplayer game (the table
shared by players); no written save (`D2S_WriteMercHeader`). The client's list window is checked through its
`RollEntry` calls (seed, player level, output), not its drawn text.
