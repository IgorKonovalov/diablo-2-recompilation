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

### Addendum 2026-10-16: plan 0038 batch S3a

- Re-analysis of this run's kept logs; no new session (plan 0038 Phase 1, ruling 2026-10-15 (a)). `python3 -I
  tools/mon_sweep.py logs` checks each log's sha256 against `hire-run-manifest.txt` and writes the batch manifest
  `workspace/logs/sweep-s3a-manifest.txt` (sha256 `274ed527…f37b`).
- `python3 -I tools/mon_sweep.py hire`: `tools/hirelings.py check` exit 0 (`hirelings: 0 mismatches`); 53 hire tables with
  slot `i` = name `first + i` and zero slots past the range; 49 hires whose `t[name − first]` holds the name, unhired, with
  `MERC_Init`'s seed; 48 headers: 15 all zero (no `MERC_Create`), 33 others (all entered it, 30 with a saved name of 0).
- Backs the S3a section of [hirelings/0001](0001-hirelings.md#plan-0038-batch-s3a-2026-10-16) and pool 4 of
  [monsters/0001](../monsters/0001-level-pool.md#plan-0038-batch-s3a-2026-10-16).

### Addendum 2026-10-16: plan 0038 batch S3b

- No new session (plan 0038 Phase 1). `python3 -I tools/sweep_s3b.py hire` re-runs `tools/hirelings.py check` on the 48
  logs of `workspace/logs/hire-run-manifest.txt`: `hirelings: 0 mismatches`, with the `GetRecord` walk the S3b section
  compares with the greatest-band reading over the whole table.
- Backs hirelings 7 and 8 of [hirelings/0001 § Plan 0038 batch S3b](0001-hirelings.md#plan-0038-batch-s3b-2026-10-16).


## run:2026-10-27-sweep-hirelings

- **Question:** (plan 0038 Phase 2, batch H6f, [inventory § 5](../../plans/0038-inventory/README.md#5-batch-list)) Do
  the hire paths run:2026-10-16-hirelings left `[I]` run as [hirelings/0001](0001-hirelings.md) reads them: Asheara's
  trade before her hire list (`NPC_OpenStore`), the client's name 1057, the level floor of a list entry, a level-up
  between the list and the hire, the quest, level and gold gates of `HIRE_Hire` and the stash payment, a Greiz hire and
  classic hires, the quest gift `HIRE_GiveFreeMerc`, a saved mercenary past level 99, with a name past its range and
  dead, `MERC_Create` with a hire table present, `PETS_OnDeath`, the resurrection, and `MERC_AddExp` with
  `MERC_CapExpGain`? Boundary as run:2026-10-16-hirelings (the NPC seed asserted at every `HIRE_BuildStock`, vendor
  builds an oracle); every new line is compared with a model written from the code before the run.
- **Status:** done (2026-10-27). Evidence in
  [hirelings/0001 § Plan 0038 batch H6f](0001-hirelings.md#plan-0038-batch-h6f-run2026-10-27-sweep-hirelings).
- **Setup:** agent-driven sessions on harness **slot 2** (display `:9`, `workspace/wineprefix-2`), stock data, pinned
  `game.exe` in `workspace/runtime/game`, one player, single player; no crash-prone probe, so no game copy was needed.
  - **Logger** `tools/gdb/h6f.gdb` (`543cf71b…`): `tools/gdb/hirelings.gdb`'s four loggers unchanged (`pilot.py`
    `05d89736…`, `vendors.py` `eddbff8c…`, `mon-pool.py` `2c17c655…`, `hirelings.py` `869ff4b5…`) plus
    `tools/gdb/h6f.py` (`168b8f24…`, one revision for every session; its header lists each address): `OSH`, `CLN`,
    `HSV`, `HQS`, `HRF`, `HPG`/`HPR`, `GFM0`/`GFMT`/`GFMP`/`GFMK`/`GFMX`, `RBE`, `MCE`/`MCT`/`MCT2`/`MCR`, `RMH`/`RMD`,
    `POD`/`PODT`/`PODN`, `RES0`/`RESU`/`RESC`/`RESP`/`RESF`/`RESX`, `KX0`/`KXG`/`KXS`, `CEG0`/`CEGX`, `AX0`/`AXX`.
  - **Session driver** `tools/h6f_sessions.py` (`b00ac949…` at the end; sessions were added to it during the run, and
    each session's function was unchanged from its first launch on, except `s_dead`, switched from Qual-Kehk to
    Kashya before its only launch, and `s_classic`, which gained the waypoint walk for Greiz before `cl2` 6624): per
    session `saves.py --slot 2 restore`/`aside h6f`, `d2run.py --slot 2 --seed S --gdb tools/gdb/h6f.gdb --steps
    tools/gdb/enter-normal.steps` (Hell: `enter-hell.steps`) `--after 3000 --install h6f <save>`, the session's
    `d2pilot.py` moves (`npc`, `waypoint walk`, `wpchain`, `explore --nova 2`), then `slots.py stop 2` and
    `saves.py --slot 2 restore h6f`. `tools/d2pilot.py` (`638f3c51…`) gained the menu entry `kashyares` (Kashya with
    a dead mercenary: talk, resurrect, hire, cancel, as Qual-Kehk's measured one; the run confirmed it) and the done
    line alias `RESX` for `MR1`.
  - **Characters** (`python3 -I tools/h6f_sessions.py write`: recipes `tools/d2s_recipes/h6f-<name>.json`, saves
    `workspace/logs/h6f/saves/<Name>/<Name>.d2s`, hashed in the manifest; ADR-0003 tool-built inputs on stock tables,
    bases `workspace/samples/d2s-owner/smpsor-l50.d2s` and, classic, `workspace/runtime/monspawn-chars/cls/smpsor.d2s`).
    Built (test) states, each backing only the code that reads it: clvl 3 and 7 with every later quest done
    (`floor`, `free`, `lvl`: the hire gates read the level and quest word 2 only); Nova at clvl 7 (`lvl`; the hire roll
    reads only the level); the merc name id 50 past the row's range 0..40 (`n99`, key `name_unchecked`: only
    `D2S_ReadMercHeader`'s clamp reads it); the dead bit (`dead`: the header's flag, what the game writes for a dead
    mercenary, H1b); a 100-gold, 2 410-stash character sized by `h6f_sessions.py plan` (`qk`); experience one point
    below a level (`lvl`, `l30`, `hexp`, `hx3`). Act start bytes 128..130 (`cl1`, `cl3`, `floor`, `free`, `lvl`, `l30`)
    and 131 (the rest) as the `-a4` recipes; no checked code reads the start act.
- **Sessions** (`python3 -I tools/h6f_sessions.py run <session> --slot 2 --tag h6f --seed S --log
  workspace/logs/h6f/h6f-s2-<S>-<session>.log --shots workspace/logs/h6f/shots/<S>-<session>`; the driver's output is
  `<log stem>.driver.txt`):

  | seed, session (log sha256) | save | what | result |
  |---|---|---|---|
  | 6602 `ash` `6a7b3124…` | H6fAsh (VendorNova) | Act III: Asheara's trade, then her list and 8 top-row hires (1057 is row 8 on this seed) | kept |
  | 6611 `floor` `4066d965…` | H6fFloor, clvl 3, word 2 open | Kashya's menu: talk, cancel (no hire line) | kept (shots overwritten by 6612/6613: the menu count is the driver's line) |
  | 6612 `free` `a09a389b…` | H6fFree, clvl 3, word 2 bit 1 | the quest gift at Kashya's talk; then a hire at clvl 3 | kept |
  | 6613 `lvlup` `618da4d4…` | H6fLvl, clvl 7 at 32 885 | menu without hire at 7; Cold Plains kills to 8; a hire at 8 | kept |
  | 6614 `lvl30` `45027ba0…` | H6fL30, clvl 30 at 5 493 362 | Kashya's list at 30; kills to 31; a hire at 31 | kept |
  | 6621 `cl1` `4b1be399…` | H6fCl1, classic, Act I | Kashya: list and a hire | kept |
  | 6623 `cl3` `e4af9e6f…` | H6fCl3, classic, Act III | Asheara: list and a hire | kept |
  | 6631 `qk` `f418b1c5…` | H6fQk, word 36 open | Qual-Kehk's menu: talk, cancel; Asheara: a hire paid 100 + 2 400 from the stash, then one refused for gold | kept |
  | 6641 `mact` `e0a7d094…` | H6fMact (a loaded Rogue) | Kashya's list, the waypoint to Act II, a Greiz hire, back to Act I | kept |
  | 6642 `dead` `635f8c84…` | H6fDead | a dead Rogue loaded; resurrected at Kashya | kept |
  | 6643 `hexp` `445de59f…` | H6fHexp (clvl 80, Rogue L 10) | Hell Cold Plains, Nova; the Rogue levels to 11, then dies | kept |
  | 6644 `n99` `32dda009…` | H6fN99 (Rogue past 99, name 50) | the load; Cold Plains, the Rogue fights | kept |
  | 6645 `qkh` `2e3fd939…` | H6fAsh | one Qual-Kehk hire (word 36 done) | kept |
  | 6646 `hx3` `3867b479…` | H6fHx3 (Rogue L 3) | Hell Cold Plains; the cap binds; 3 → 4, then dies | kept |
  | 6647 `hx85` `d6524571…` | H6fHx85 (Rogue L 85, owner 80) | Hell Cold Plains; gains with no effect; dies | kept |
  | 6622, 6624 `cl2`; 6625, 6626 `cl2w` | H6fCl2 / H6fCl1, classic | Greiz: not found from the Act II start (twice), and walked into the sewer from the waypoint (twice) | development (`dev/`), no claim |

  **Launches: 19** (the batch cap is 20): 15 kept, 4 development.
- **Procedure** (from the worktree, under `systemd-run --user --scope -q -p MemoryMax=4G`):
  `python3 -I tools/sweep_h6f.py check workspace/merged/data/global/excel $(cat workspace/logs/h6f/kept.lst) >
  workspace/logs/h6f/check/check-final.txt` (checker `e272b456…`; it runs `tools/hirelings.py check` (`f6500b6e…`)
  first); the regressions `python3 -I tools/hirelings.py check … $(cat workspace/logs/hire-run.lst) >
  check/regress-hire-run.txt` (the 48 logs of run:2026-10-16-hirelings: byte-identical to the output of the
  `main` revision of `hirelings.py`, 0 mismatches) and `python3 -I tools/monpool.py check … $(cat kept.lst) >
  check/monpool.txt` (4 613 of 4 613). `tools/hirelings.py` changed in one place: a hire is counted made when
  `MERC_Init` ran inside `HIRE_Hire`, not when `HHX`'s `EAX` is non-zero (`HIRE_Hire` returns no value; the refused
  hire returned 15).
- **Observed** (`check/check-final.txt` `943f181f…`, `check/regress-hire-run.txt` `637d34c4…`, `check/monpool.txt`
  `d65e5fbf…`; manifests in `workspace/logs/h6f/`: `manifest-final.sha256` `545e6d90…` (64 lines: the 15 kept logs,
  their driver and `d2run` outputs, `kept.lst`, the three checks, the 15 built saves) and `manifest-shots.sha256`
  `fe15ef8d…` (18 screenshots), each passing `sha256sum -c` from `workspace/logs/h6f/`; `dev/manifest-dev.sha256`
  `ef75f5ee…` (16 lines) passes from `workspace/logs/h6f/dev/`; trimmed):
  ```
  tools/hirelings.py check: logs 15; hires 16; RollEntry 17 HIRE_Hire, 23 MERC_Init, 109 list draws, 23 client
    merc init; 13 tables; MERC_SetLevel stats 25; loads 6; hirelings: 0 mismatches
  H6f checks over 15 logs (comparisons):
    VENDOR_StockLevel 17; quest word 2 read only below 8: 4; word 36 read for Qual-Kehk 1; none for Greiz, Asheara 12
    PayGold price = roll 17; PayGold = gold + stash >= price 17; refusal 0x6AE, nothing paid 1
    HIRE_RebuildIfEmpty rebuilds only at 0 left 17
    free mercenary: pick 1, MERC_Init 1, RebuildIfEmpty after it 1
    client name string (1057 -> 11021, else itself) 122
    saved name clamp 6; dead flag and mode 6; PETS_OnDeath node bit 4
    MERC_ResurrectCost 1; resurrection PayGold 1; paid and revived 1
    share x 86/256 unless the killer 42; MERC_AddExp 42; MERC_CapExpGain 246
    NPC_OpenStore's hire test after the first-interaction build 1
  notes: paid from gold and the stash: price 2500, gold 100, stash 2410 -> 10; refused for gold: price 2650, gold 0,
    stash 10; gate passed at 150: stock level 3 (word 2 read 1), 8 (no read), 12 (no read); at 515: word 36 read 1;
    free mercenary from 150 (dead-or-alive pet test 0), RebuildIfEmpty from 0x57933f, 9 left;
    name 1057 drawn as 11021 at the list (3) and init (1) sites; hire of an entry drawn at 30 and 31, rolled at 31
    (level 30); rolls at the floor 2: 12 (unclamped -2..1); loads: levels 3, 10, 30 (2), 85, 99 (exp 150 000 000);
    saved name 50 -> 3411 (reset), 3, 5, 6, 7 kept; PETS_OnDeath from 0x56abd7 (the load) 1, from 0x57cd26 (in play) 3;
    resurrected: L 30, cost 6 750, flags 0x840b0203 -> 0x840a220f, mode 12 -> 1;
    kill award: the mercenary's kill 3, another's 39; MERC_CapExpGain capped 4, below 35, a player's 207;
    MERC_AddExp: added 4, level-ups 2 (3 -> 4 and 10 -> 11), L >= owner's level 33, gain <= 0 3;
    MERC_Create from 0x56aae8 (the load) 6, no other caller
  h6f: 603 comparisons, 0 failing
  ```
- **Limits:** no classic Greiz hire (four launches, the pilot failed to reach him); no hire or list at Kashya below
  level 8 with word 2 open and none at Qual-Kehk with word 36 open: the client's menu offered no hire line, so the
  server's two quest refusals were not sent (which client code drops the line is unfollowed); no Act III quest gift;
  no classic free mercenary; no `MERC_Create` with a hire table present (the only calls were at the load, and the act
  changes of `mact` made none); a `MERC_AddExp` at L ≥ 98 with a gain > 0 (`n99`'s gains were 0); resurrection at
  Greiz, Asheara or Tyrael. Dev logs: the four Greiz attempts.
