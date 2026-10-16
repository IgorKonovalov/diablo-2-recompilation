# Data experiments

## run:2026-10-15-strings

- **Question:** (plan 0028 Phase 1) Does the model of the run-time string lookups in `tools/tbl.py` (`GameStrings`:
  `STRTABLE_GetByIndex`, `STRTABLE_GetByKey`, `STRTABLE_FindInTable`, written from the code in
  [data/0003](0003-string-tables.md)) reproduce every logged lookup, the table, entry, node, probe count and the
  returned UTF-16 text included, in an expansion and a classic session?
- **Setup:** two agent-driven sessions, single player, Normal, harness slot 2 (display `:9`, prefix
  `workspace/wineprefix-2`, ADR-0011), gdb by `tools/d2run.py`, game directory `workspace/runtime/game` (stock: no loose
  data file, no `-direct`). Logger `tools/gdb/strings.gdb` (`b825a525…37b28`), which sources `tools/gdb/pilot.py`
  (`1ad48a4c…86801`; the lines the pilot steers by) and `tools/gdb/strings.py` (`b9ebdb10…37c75`; `SIDX`, `SKEY`,
  `SSTAT`). Breakpoints only print and continue. Rate limit: one line per distinct (index, loaded tables) and per
  distinct (key, loaded tables); `SSTAT` counts every hit. Model: `tools/tbl.py` (`49eb3277…09fdd3e`) over the English
  tables `workspace/merged/data/local/lng/eng` and the font map `workspace/merged/data/local/font/latin/default.map`.
  - **Characters** (ADR-0003 tool-built inputs, the reference builds of harness-play):
    - expansion: `UniqNova`, `tools/d2s.py build workspace/merged/data/global/excel tools/d2s_recipes/uniqnova.json
      workspace/samples/d2s-owner/smpsor-l50.d2s workspace/runtime/strings-chars/UniqNova.d2s` (recipe `3c2f57dc…`,
      save `2c793a3d…d7ddc376`, byte-identical to the plan 0019 save);
    - classic: `UniqClassic`, the same with `tools/d2s_recipes/uniqclassic.json` on
      `workspace/runtime/monspawn-chars/cls/smpsor.d2s` (recipe `e58db639…`, save `68e46a96…31eaf0ea`). Classic
      checked: status byte (`+0x24`) `0x00`, bit `0x20` clear; in game the pilot's waypoint hop with the classic
      four-tab geometry (`--wp 4,2 --wp-tab-x0 120 --wp-tab-w 78`) reached level 106 (City of the Damned); tab 4 at
      x = 393 would be the Act V tab of a five-tab menu.
  - Installed only with `tools/saves.py --slot 2` (tags `h28`, `h28c`: an empty aside, install, restore) and restored
    at the end: slot 2 saves empty, `aside: none`, `harness: idle`, `slots.py stop 2` done.
  - **Sessions:**

    | seed | mode | log | play |
    |---|---|---|---|
    | 2802 | expansion, Normal, Act IV town | `strings-s2-2802-exp.log` | UI tour (scratch `ui.sh`: inventory hover over every cell, character, skill tree hover, quests, automap), then `d2pilot.py --slot 2 farm <log> --wp 5,2 --players 1 --time 150 --sweep --nova-key F1 --es-key F2 --es 20` (Frigid Highlands: Eldritch and a champion pack down), then Alt held over the ground |
    | 2803 | classic, Normal, Act IV town | `strings-s2-2803-cls.log` | the same UI tour, then `farm --wp 4,2 --wp-tab-x0 120 --wp-tab-w 78`, the rest as above (City of the Damned: a champion pack down) |

    Both: `python3 -I tools/d2run.py --slot 2 --seed N --gdb tools/gdb/strings.gdb --steps
    tools/gdb/uniques-normal.steps --after 900 --log workspace/logs/<log>`, ended with `slots.py stop 2`.
- **Logs** (workspace, not in git): `workspace/logs/strings-s2-2802-exp.log` (`968e9514…ea38b2`),
  `strings-s2-2803-cls.log` (`a484c177…efdc18`); manifest `workspace/logs/strings-manifest.txt`. The dev log
  `strings-dev-s2-2801-exp.log` (first logger, with one breakpoint per probe) is not part of the run: a key absent from
  a table examines all `max_probes` nodes of it (1 179, 2 453, 5 192), so that logger made the game load ~1 key a
  second; the run's logger reads the probe count at the two exits instead.
- **Procedure:**
  ```
  python3 -I tools/tbl.py check workspace/merged/data/local/lng/eng workspace/logs/strings-s2-2802-exp.log
  tables loaded per line: spx=2151
  SIDX lines per table: p=22 s=139 x=26
  CHECK strings sidx=187 sidx_ok=187 skey=1964 skey_ok=1964 fallback_11078=0 fallback_500=0 finds=4728
        finds_missed=2844 chains_gt1=885 not_found=79 empty_key=1 unwritten_unit=3 logerr=0 distinct_idx=187
        distinct_key=1964
  python3 -I tools/tbl.py check workspace/merged/data/local/lng/eng workspace/logs/strings-s2-2803-cls.log
  tables loaded per line: spx=2113
  SIDX lines per table: p=16 s=130 x=3
  CHECK strings sidx=149 sidx_ok=149 skey=1964 skey_ok=1964 … chains_gt1=885 not_found=79 … distinct_idx=149
        distinct_key=1964
  python3 -I tools/tbl.py check … both logs
  longest hit chain: 5159 nodes, key b'not used' table s home 157 -> slot 5315, entry 5384
  CHECK strings sidx=336 sidx_ok=336 skey=3928 skey_ok=3928 … distinct_idx=201 distinct_key=1964
  ```
  Hits behind the lines (`SSTAT`, last): expansion 57 890 `GetByIndex` and 3 573 `GetByKey` calls, classic 17 952
  and 3 578.
- **Counts** (the plan's): distinct indices 187 (expansion) and 149 (classic), 201 over both; distinct keys 1 964 in
  each (the same keys); hash chains longer than one node that ended on a match: 885 per session (of 1 884 hits), plus
  2 844 searches per session that examined all `max_probes` nodes and missed (a key absent from `patchstring`, or
  from `expansionstring`, before the table that has it). Worked example, `of Amianthus` (expansion session): patchstring
  home 961, 1 179 nodes, miss; expansionstring home 34, 3 nodes (34, 35, 36), entry 925 at slot 36 → index 20925.
- **Observations:**
  - Every `SIDX` and `SKEY` line matches the model: 0 mismatches over 336 index and 3 928 key lookups.
  - **`expansionstring.tbl` is loaded in the classic game too** (`ld = "spx"` on every line of both logs, and from
    the main menu on: the first `SIDX` lines are menu text before any game). The classic session resolved 3 indices
    ≥ 20000 through `expansionstring`: 21796 `CHARACTER`, 22730 `EXPANSION`, 22732 `CONVERT TO`, the character-select
    screen's offer to convert the classic character. The load condition is the stack argument of `STRTABLE_LoadAll`, the result of
    `sub_00408F20_HasExpansionMpq` (d2exp.mpq present), not the game's expansion flag (data/0003 § Loading).
  - A key absent from a table is searched over all `max_probes` nodes of it, through unused ones (2 844 such searches
    per session, each with `n = max_probes`): the search does not stop at an unused node.
  - Keys with a byte ≥ 0x80 reached the hash: `GEMS_Load` passes 68 two-byte keys built on its stack
    (`"-\x02"` … `"\x82\x02"`, caller 0x0063721C). For `"\x80\x02"`, `"\x81\x02"`, `"\x82\x02"` the logged home
    slots (patchstring 361, 345, 329) are the signed-char hash; the unsigned hash gives 869, 885, 901.
  - Not-found keys (79 per session: the 68 above, `"Elite Uniques"` from `sub_006342B0_LoadUniqueItems`, and ten keys
    through `STRTABLE_GetStringByKey` (0x00524E35): `"To The Pandemonium Run 1"`–`3`, `funeralpire`, `burninglogs`,
    `stma`, `BBQB`, `btor`, `Zoo`, `Keeper`) return index 0 and the
    placeholder `<key> -not xlated call ken` + a space: the suffix at 0x00730520 is `" -not xlated call ken w"`
    and the conversion drops the last character. For the key `"\x7f\x02"` it drops two (0x7F counts as a two-byte
    character in the latin font map), and for `"\x80\x02"` … the decoder stops at the first byte and leaves one unit
    unwritten (`unwritten_unit=3`; it read as 0 once, giving an empty text). The one empty key (from
    `sub_00633730_LoadMagicAffixes`) returns 0 and an empty text without a search.
  - No lookup reached the entry-500 fallback, the 11078 fallback or a fatal path.
- **Conclusion:** the lookup rules of data/0003 reproduce on stock data with 0 mismatches in both modes: index →
  table and entry, entry → node, key → table order and index, the hash (signed chars), the probe walk over unused
  nodes to `max_probes`, the empty-key and not-found returns, and the UTF-8 → UTF-16 conversion with its character
  count. Unreached and still `[I]`: the 500 and 11078 fallbacks and the fatal checks
  ([data/0003 § Open questions](0003-string-tables.md#open-questions), fn:STRTABLE_EntryToString@0x00524930).

## run:2026-10-16-calc

- **Question:** (plan 0035 Phase 2) Does the model of `fn:CALC_Eval@0x006C0BC0` in `tools/calc.py` reproduce every
  evaluation the game makes in ordinary play (skill descriptions shown, skills cast, missiles fired, potions drunk),
  value for value, with the same variable reads and function calls in the same order, and does it reach every
  opcode of the stock pools?
- **Setup:** 14 agent-driven sessions, single player, expansion, Normal, harness slot 3 (display `:10`, prefix
  `workspace/wineprefix-3`, ADR-0011), gdb by `tools/d2run.py`, game directory `workspace/runtime/game` (stock: no
  loose data, no `-direct`, so the pools are the shipped `*code.bin`). Breakpoints only print and continue; no rate
  limit (every evaluation is logged).
  - **Logger:** `tools/gdb/calc.gdb` (hover sessions) or `tools/gdb/calc-field.gdb` (field sessions: the pilot's
    loggers of `mon-special.gdb` plus the same calc logger), both sourcing `tools/gdb/calc.py` (`38a0f2e2…b7d0abe5`).
    Lines: `CE` at `CALC_Eval` entry (code, length, variable reader, function table and count, the context's first
    four dwords, the pool and offset the code lies in, the code bytes walked to their end, the return address and the
    caller's), `CV`/`CVR` around each variable-reader call (0x006C0C28, 0x006C0C5C, 0x006C0C8F: index, value), `CF`/
    `CFR` around each function call (0x006C0D5C argc 3, 0x006C0D9B the others: index, pointer, argc, a, b, c, value;
    for `rand` the seed), `CX` at the three returns (0x006C0BD7, 0x006C1145, 0x006C1161). The division case jumps to
    the push after the function call (0x006C0ED1 → 0x006C0D9D), so a `CFR` is written only when ESP is the pending
    call's ESP + 8 (the callee pops two stack arguments); a first logger without that test (dev log
    `calc-dev-s3-cal1.log`) closed calls at divisions.
  - **Characters** (ADR-0003 tool-built inputs): one per class, `tools/calc_sessions.py write` (`f783b128…39b96e36`)
    → `tools/d2s_recipes/calc-<cls>.json` (hover) and `calc-<cls>-field.json` (field: the same plus progression 15,
    Act IV, quests), built with `python3 -I tools/d2s.py build workspace/merged/data/global/excel <recipe>
    workspace/runtime/saves-backup/p0005/smp<cls>.d2s <out>` (`smpasn` for the Assassin). Clvl 80, every class skill
    at a level from a fixed pattern (1 3 0 4 8 2 5 13 20 6, some 0 so the tree shows a first level), with overrides
    that put the stock ternaries on both sides (Raise Skeleton and Raise Skeletal Mage 3, Zeal 4: the tree shows the
    current and the next level), hotkeys F1–F8 on the learned non-passive skills with the most formula cells, and
    seven potions in the inventory (`vps yps wms elx vps yps wms`, the misc rows with formula cells). Saves (sha256
    prefix…suffix): CalcSor `787a2291…3b49acf6`, CalcNec `90cceb97…f115fac6`, CalcPal `0591a06e…27839345`, CalcDru
    `d6185cb4…955dfc85`, CalcAss `d28ac300…dd89820f`, CalcAma `527952cb…67afc944`, CalcBar `7323b23d…16724fde`;
    field variants CalcSorF `b26247d5…b4b76737`, CalcNecF `542a53e5…ad21ff0a`, CalcPalF `0412888b…4ffdbdd6`,
    CalcDruF `b437f895…151a6799`, CalcAssF `4ed3eb4e…1293cc93`, CalcAmaF `3ae9a886…a70fc15a`, CalcBarF
    `9b7da6b7…3395e1fc`. Installed with `d2run.py --install h35p2` after `saves.py --slot 3 restore h35p2; aside
    h35p2` (one character per session); restored at the end: slot 3 saves empty, `aside: none`, `harness: idle`.
  - **Sessions** (scratch loops `hover.sh`, `field.sh`; seeds 3511–3517 hover, 3531–3537 field, in the class order
    sor nec pal dru ass ama bar):

    | kind | steps | play |
    |---|---|---|
    | hover | `tools/gdb/enter-sp.steps` (Rogue Encampment) | `xdrive.py --slot 3 --window "Diablo II" run tools/gdb/calc-<cls>-hover.steps`: skill tree, each tab, the pointer on every skill for 1 s; inventory, the pointer on each potion for 1 s, three potions drunk (right click) |
    | field | `tools/gdb/uniques-normal.steps` (Act IV town) | `d2pilot.py --slot 3 farm <log> --wp 1,2 --players 1 --time 8` (Cold Plains), then `calc-<cls>-cast.steps`: each hotkey F1–F8, three right clicks around the character |

    Each session: `d2run.py --slot 3 --seed N --gdb … --after 400|600 --log workspace/logs/calc-s3-<cls>-<kind>.log`,
    ended with `slots.py stop 3`. Not part of the run: `calc-dev-s3-cal1.log` (calibration, first logger) and
    `calc-dev-s3-sor-field0.log` (a field session started in Act I, where the pilot found no waypoint).
- **Logs** (workspace, not in git): the 14 `workspace/logs/calc-s3-{sor,nec,pal,dru,ass,ama,bar}-{hover,field}.log`,
  sha256 per file in `workspace/logs/calc-manifest.txt` (`b8edef66…ed3a1e2a`). Evaluations per log (CE lines): hover
  4 967, 5 410, 5 257, 5 805, 6 558, 4 550, 5 675; field 3 054, 203, 325, 1 511, 766, 358, 90.
- **Procedure** (`run.lst` = the 14 logs; `tools/calc.py check` (`29b0b851…b972a43b`), model of data/0005 §§ 5–7):
  ```
  python3 -I tools/calc.py check workspace/merged/data/global/excel $(cat run.lst) -v
  evaluations: 44529 complete (44529 checked ok), 0 left open at the end of a log
    itemscode 56 evaluations, 8 distinct cells;  misscode 1044, 12;  skilldesccode 28771, 821;  skillscode 14658, 347
  opcodes executed (evaluations): 00 44429  01 12169  02 100  04 34173  07 20498  08 5958  0A 361  0B 25
                                  10 7797  11 1558  12 12156  13 2114  15 282  16 386
  operator outcomes (evaluations): 0A 0 150, 0A 1 211, 0B 1 25, 13 exact 725, 13 neg 25, 13 trunc 1392,
                                   16 False 150, 16 True 236
  stock opcodes not reached: none
  variable reads: 41021 (row model ok 38076, formula link ok 682, oracle 2263)
  function calls: skills min 979 (979 model ok), skill 18593 (oracle), sklvl 150 (50 model ok, 100 oracle),
                  miss 80 (oracle), stat 6 (oracle); missiles skill 1224 (oracle)
  SURVEY calc_run evals=44529 ok=44529 mismatches=0 open=0 anomalies=0 cells=1188 opcodes=14 stock_opcodes=14
         not_reached=0 var_reads=41021 var_model=38076 var_formula=682 var_oracle=2263 fn_calls=21032
  ```
  Per evaluation the check: the code lies in a pool, its length is the pool size minus the offset, the logged bytes are
  the stock bytes; the variable reader, the function table and its count are the pool's context's; the model, run
  on the stock bytes, makes the logged reads and calls in the logged order with the logged indices and arguments,
  takes their logged values, and returns the logged value. Then the computed checks: `min` from its arguments;
  `sklvl` where both its variables read only the row; every row-only `skillcalc` variable (§ 7.1: `ln` `dm` `par`
  `lvl` `toht` `mana`-family) from the skills record at the context's (skill, level); every formula-valued variable
  (`clc1..4`, `len`, `toht` with a formula, …) as exactly one nested evaluation of the field's offset in the same
  (unit, skill, level) context whose result is the read's value.
- **Oracles (ADR-0004, value oracles: no seed is shared):** the unit-state reads, logged and taken as given: the
  functions `skill` (skills and missiles contexts), `miss`, `stat`, `sklvl` with a unit-reading variable, and the
  variables `edmn edmx edln edns edxs enma exma enms exms m1en m1ex m2en m2ex m3en m3ex m1eo m1ey ulvl math madm macr`.
  `CALC_Eval` draws only through `rand`, which no session called, so no seed passes through the evaluator and the
  entry-seed assertion of ADR-0004 has nothing to assert.
- **Not reached:** opcodes `05 06 09 0C 0D 0E 0F 14` (no stock cell contains them); the functions `max` (one stock
  cell, skills row 326 `BearSmite`) and `rand` (one, row 282 `Imp Inferno`: monster skills), the missile-context
  `miss` (index 4 ≥ the table's 4 entries); the missile variable reader `MISS_CalcVar` (no evaluation in the
  missiles context read a variable: the 12 missile cells reached call only `skill`); the 30 `skillcalc` codes `dm78 mana m1el m2el m3el m1rn m2rn m3rn blvl m2eo m2ey me3o me3y edma clc2 clc3 rng ast1`–`ast6 pst1`–`pst5 pets skpt` as variables (`blvl` is reached only as the constant in `skill(…'.blvl)`); the zero divisor, 32-bit wrap, `0B` false, an empty-stack
  pop and a full stack.
- **Observations:**
  - Callers seen (the `CE` return address `ra` and, one frame up, `ra2`): through `SKILLS_EvalDescCalc` (ra
    0x00646D59) from 0x004EDEF1 and 0x004EDF0D (the skill tree's description); through `SKILLS_EvalCalc` (ra
    0x00646CF9) from 76 call sites, among them the description (0x004E3F35, 0x004E3F52, 0x004E3F6F) and
    `SKILLS_GetMasteryCalc` (0x00647ECA); **directly** (ra inside the function, the `{unit, skill, lvl}` context built
    in its own frame) from `SKILLS_CalcVar` at 0x00646A07 (the formula-valued codes), `SKILLS_GetElemMin`/`Max`/`Len`
    (ra 0x00644E07, 0x00644EE6, 0x0064500C) and `SKILLS_GetToHit` (ra 0x00644A7E); `MISS_EvalCalc` (ra 0x0064B855)
    from `MISS_GetElemMin`/`Max` (0x0064B1A4, 0x0064B274), with a NULL missile (the description, 932) and with a
    missile unit (in flight, 112); `ITEMS_EvalCalc` (ra 0x00627C7F) from 0x005BEE04 (`len`) and 0x005BEF16 (`calc1`,
    `calc2`) inside `0x005BEDA0`: 8 evaluations per session, the cells of the three potions drunk (stamina `len`,
    `calc1`; antidote and thawing `len`, `calc1`, `calc2`), none while the pointer rested on the potions.
  - Integer division truncates toward zero: 25 evaluations divided a negative value inexactly and match `idiv`, not a
    floor.
  - Fire Wall's unclosed `(` (skills row 51 `EDmgSymPerCalc`, bytes ending `… 10 02 00`) ends the evaluation at `02`
    with the top of the stack, 100 times.
- **Conclusion:** the evaluator model reproduces all 44 529 evaluations with 0 mismatches, covering all 14 opcodes of
  the stock pools and 1 188 distinct cells, with the row-only variables, `min`, the row-only `sklvl` and the formula
  links computed. Corroborated (`[C]`) for that scope; the oracles above and the unreached items stay `[I]`.
  (fn:CALC_Eval@0x006C0BC0, [data/0005 § 10](0005-calc.md))

## run:2026-10-16-calc-emu

- **Question:** (backlog 2026-10-16, plan 0035 leftovers) Do the calc functions `min`, `max` and `rand` of the
  skills, items and missiles tables, `MISS_CalcVar` and `MISS_EvalCalc` with its context produce exactly what
  [data/0005](0005-calc.md) § 6, § 7.2 say? No stock play reached `max`, `rand` or a missile variable
  (run:2026-10-16-calc), so the binary's own functions are run under emulation instead.
- **Setup:** Ghidra 12.1.2 p-code emulator (`EmulatorHelper`) on the pinned `game.exe` (a lane copy of the project,
  `GHIDRA_PROJ_DIR=workspace/ghidra-rbl`, symbols replayed from `re/symbols.csv`). No wine, nothing runs natively.
  Scripts `re/ghidra_scripts/EmuCalcFunc.java` (`dd4cc1a2…`: `ECX = a`, `EDX = b`, stack `c, ctx`; a scratch context
  whose dword 0 points at a scratch unit; the seed written at `unit + 0x20` and at `ctx + 0x20`; checks the callee pops
  8) and `re/ghidra_scripts/EmuCall.java` (`d7e4bb10…`: registers, stack arguments, a memory spec applied before each
  case, prints `eax` and the bytes popped), through `tools/ghidra.sh emucalc` / `emucall`. Models and case writers
  in `tools/calc_funcs.py` (`4b3a7a59…`), which uses `tools/rng.py` (`RNG_RangeB` = its `range`) and, for the stock
  cells, `tools/calc.py`'s evaluator. Stock tables from `workspace/merged/data/global/excel` (`misscode.bin`,
  `missiles.bin`). Files in `workspace/logs/calc-emu/`, `manifest.txt` `4ca75152…` (sha256 of every case, memory
  and output file).
- **Procedure:**
  ```
  D=workspace/logs/calc-emu; X=workspace/merged/data/global/excel
  python3 -I tools/calc_funcs.py cases $D/calcfn-cases.txt 5000 1                   # 53d9ce47…
  for f in skills_min skills_max skills_rand items_min items_max items_rand miss_min miss_max miss_rand; do
    tools/ghidra.sh emucalc <addr of f, `calc_funcs.py fns`> $D/calcfn-cases.txt > $D/calcfn-$f.out
    python3 -I tools/calc_funcs.py check $f $D/calcfn-cases.txt $D/calcfn-$f.out
  done
  python3 -I tools/calc_funcs.py misscases $D/miss 5000 1                           # records bfe68d7b…, cases e2dccbb4…
  tools/ghidra.sh emucall 0x0064B340 $D/miss/miss-cases.txt $D/miss/miss-mem.txt > $D/miss/miss.out
  python3 -I tools/calc_funcs.py misscheck $D/miss $D/miss/miss.out
  python3 -I tools/calc_funcs.py evalcases $X $D/eval                               # cases a2bf2212…, memory 4ed61ff5…
  tools/ghidra.sh emucall 0x0064B7C0 $D/eval/eval-cases.txt $D/eval/eval-mem.txt > $D/eval/eval.out
  python3 -I tools/calc_funcs.py evalcheck $X $D/eval $D/eval/eval.out
  ```
  `miss-mem.txt` points `g_pDataTables` (`0x00744304`) at a scratch DataTables (`+0xB64` records, `+0xB6C` count 4)
  and places a type-3 and a type-1 unit; `eval-mem.txt` adds the stock pool (`+0x60`, size `+0x64`), the 684 stock
  records and one scratch missile unit per case (type 3, class = the row, `Unit+0x14` → data with the level at
  `+0x0C`). Negative control: checking `skills_min` against the `max` output gives 28/5000, `miss_rand` against the
  skills `rand` output 2087/5000.
- **Observed:**
  ```
  skills_min (0x006436E0): 5000/5000 match, 0 with a seed step
  skills_max (0x006436F0): 5000/5000 match, 0 with a seed step
  skills_rand (0x00643700): 5000/5000 match, 2913 with a seed step
  items_min (0x00627B50): 5000/5000 match, 0 with a seed step
  items_max (0x00627B60): 5000/5000 match, 0 with a seed step
  items_rand (0x00627B70): 5000/5000 match, 2913 with a seed step
  miss_min (0x0064B700): 5000/5000 match, 0 with a seed step
  miss_max (0x0064B710): 5000/5000 match, 0 with a seed step
  miss_rand (0x0064B720): 5000/5000 match, 2913 with a seed step
  MISS_CalcVar (0x0064B340): 5000/5000 match; codes reproduced: 0..18 28..42 43 255   (373 DimReturns cases capped)
  MISS_EvalCalc (0x0064B7C0): 236/236 match over 13 stock cells
  ```
- **Conclusion:** bit-exact reproduction (evidence rule 4) of the nine function-table entries, of `MISS_CalcVar`'s
  codes 0–18 and 28–42 with its guards, of `SKILLS_DimReturns`' cap, and of `MISS_EvalCalc`'s context
  `{missile, owner, missileId, lvl}` with its unit defaults on every stock missile cell that needs no unit. Raises
  them to `[C]` in [data/0005](0005-calc.md) § 6, § 7, § 11. Not covered: `MISS_CalcVar` codes 19–27, the 12 stock
  missile cells that call `skill`, and when a monster's `rand` draws in play. (fn:MISS_CalcVar@0x0064B340,
  fn:MISS_EvalCalc@0x0064B7C0)
