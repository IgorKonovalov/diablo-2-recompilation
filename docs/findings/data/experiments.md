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

- **Addendum 2026-10-16: plan 0038 batch S1b (static, no new session; `tools/sweep_s1b.py` sha256
  `f0df814a30306bab…`).** The two logs above, sha256 equal to `strings-manifest.txt`, re-read:
  ```
  python3 -I tools/sweep_s1b.py strings
  S1B strings lines=4264 model_mismatches=0 skey_GetStringByKey=906 skey_GEMS_Load=136 skey_LoadRareAffixes=394
      skey_RUNES_Load=336 getstringbykey_found=886 getstringbykey_not_found=20 gems_logged_keys_distinct=68
      gems_keys_distinct=68 gems_idx_nonzero=0 rare_logged_keys_distinct=197 rare_keys_logged_by_other_caller=3
      rare_idx_eq_model=197 runes_logged_keys_distinct=168 runes_duplicated_names=1 key_7f_chars_lost=2
      keys_walked=8949 logged_dup_keys=3 logged_dup_keys_lowest=3 keys_present_only_under_other_case=0
      sidx_5382_lines=1 bad=0
  ```
  The lines per return address are those of the table loaders the finding names; the gem keys are the `gems.bin`
  bytes `+0x28..+0x2A`, the rare-name keys the records' names, the rune keys the `runes.bin` names. Conclusion:
  [data/0003 § Plan 0038 batch S1b](0003-string-tables.md#plan-0038-batch-s1b-2026-10-16) (strings rows 1, 3, 11, 21,
  31 in part, 33; excel rows 57 in part, 72, 75, 76).

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

- **Addendum 2026-10-16: plan 0038 batch S1b (static, no new session; `tools/sweep_s1b.py` sha256
  `f0df814a30306bab…`).** The 14 logs above, sha256 equal to `calc-manifest.txt`, re-read per pool:
  ```
  python3 -I tools/sweep_s1b.py calc
  S1B calc ce_skillscode=14658 ce_skilldesccode=28771 ce_misscode=1044 ce_itemscode=56 (ce_whole_file_* the same)
      pool_bases_constant=35 pool_bases_varying=0 ra2_misscode_0064B1A4=522 ra2_misscode_0064B274=522
      ra2_itemscode_005BEE04=21 ra2_itemscode_005BEF16=35 callsite_ok=4 callsite_in_body=4 item_ctx=56
      item_ctx_unit_is_player=56 item_ctx_word1_distinct=21 image_miss_count=4 image_items_count=4
      itemuse9_is_timedstate=1 itemuse6_calls_timedstate=1 bad=0
  ```
  Every evaluation's function table and count are its pool's, offset + length is the pool file's size, and each
  logged caller follows a call of the entry point in the function the finding names. Conclusion:
  [data/0005 § Plan 0038 batch S1b](0005-calc.md#plan-0038-batch-s1b-2026-10-16) (rows 1, 2, 6, 7; 18 and 19 in part)
  and [data/0001 § Plan 0038 batch S1b](0001-excel-loader.md#plan-0038-batch-s1b-2026-10-16) (excel row 31).

- **Addendum 2026-10-16: plan 0038 batch S1a (static, no new session; `tools/sweep_s1a.py` sha256 `c07086a3…`, log manifest `workspace/logs/sweep-s1a-manifest.txt` `18318973…1676`).** The 14 logs above (sha256 as in
  `calc-manifest.txt`) and the 14 installed saves (`workspace/scratch-h35p2/Calc*.d2s`, sha256 prefixes as the log headers):
  ```
  python3 -I tools/sweep_s1a.py calc
  S1A calc bad=0 cast_path_evals=5073 cast_skills_hotkeyed=34 cf_shifted_skill_bytes_fail=7 classes_cast_in_slot_order=7
      hotkeys_empty=56 hotkeys_flagged=0 hotkeys_set=56 level1_extra_evals=68 skills_checked=207 skills_saved_nonzero=187
      skills_saved_zero=20 skills_without_cells=3
  ```
  Hover sessions: each class skill's evaluations run at its saved `if` byte (and the next level), a 0 byte at level 1.
  Field sessions: every evaluation through a caller absent from the hover sessions is of a hotkeyed skill, first cast in
  slot order. Conclusion: [save/0001 § Plan 0038 batch S1a](../save/0001-d2s-io.md#plan-0038-batch-s1a-2026-10-16) (rows
  32, 70).

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
  missile cells that call `skill`, and when a monster's `rand` draws in play. Admitted as evidence under
  [ADR-0015](../../adrs/0015-emulated-reproduction.md) (architect review of `lane/rbl`, 2026-10-16); the read set its
  condition 2 asks for is in [data/0005 § 11](0005-calc.md#11-static-emulation-of-the-functions-and-the-missile-context-run2026-10-16-calc-emu).
  (fn:MISS_CalcVar@0x0064B340, fn:MISS_EvalCalc@0x0064B7C0)
- **Addendum 2026-10-27** (plan 0051 Phase 1b): re-run under `EmuTrace` as run:2026-10-27-p51s-emu
  ([stats experiments](../stats/experiments.md#run2026-10-27-p51s-emu)). The outputs are byte-identical, and the
  traced read set adds the two `.text` jump tables to [data/0005 § 11](0005-calc.md)'s list. No tag depends on it.
  (fn:MISS_CalcVar@0x0064B340, run:2026-10-27-p51s-emu)

## run:2026-10-17-sweep-emu

- **Question:** (plan 0038 batch S1e, the c-emu rows of [inventory § 5](../../plans/0038-inventory/README.md#5-batch-list))
  Do the binary's calc evaluator and compiler, the calc entry points and `SKILLS_CalcVar`, the excel code and name
  links, the `.txt` cell converters, the language table, the string-table lookups, `RNG_RangePow2Plus` and
  `BITBUF_WriteClamped` produce exactly what the findings say, on inputs no stock play reaches?
- **Setup:** Ghidra 12.1.2 p-code emulator (`EmulatorHelper`) on the pinned `game.exe` (lane copy
  `GHIDRA_PROJ_DIR=workspace/ghidra-s1e`, symbols replayed from `re/symbols.csv`, heap 3 GB). No wine, nothing runs
  natively. New script `re/ghidra_scripts/EmuTrace.java` (`be7a0b2d…`, `tools/ghidra.sh emutrace`): per case it applies
  a memory spec (`const` lines once), writes the case's memory and registers, calls one function with a sentinel return
  address, prints EAX, EDX, the bytes popped and dumps, and stops a case that leaves the image's code or passes 20 M
  steps. It traces every data read and write outside the stack, the spec and the case memory (instruction fetches
  excluded) and prints them aggregated, so the read set of ADR-0015 condition 2 is enumerated by the tool and not only
  by reading the code. Models, case writers and checks: `tools/sweep_s1e.py` (`8e5f2aad…`; it reuses `tools/calc.py`'s
  compiler for the compile family, `tools/rng.py` and `tools/tbl.py`), unit tests `tools/test_sweep_s1e.py` (10).
  Stock inputs: `workspace/merged/data/local/lng/eng/*.tbl`; everything else is synthetic. Files in
  `workspace/logs/sweep-s1e/`, `manifest.txt` `94c19392…` (53 files: cases, memory specs, expected values, outputs,
  the synthetic `.tbl` and text arrays). Full report `workspace/logs/sweep-s1e-all.txt` (`3293ae63…`).
- **Procedure:**
  ```
  D=workspace/logs/sweep-s1e
  python3 -I tools/sweep_s1e.py cases                      # writes D/<family>.cases, .mem, .json (seeded: "s1e-<family>")
  for f in rng bitbuf eval calcvar entry excel lang strings compile parsetxt; do
    tools/ghidra.sh emutrace $D/$f.cases $D/$f.mem > $D/$f.out
  done
  for f in compile parsetxt; do tools/ghidra.sh emutrace $D/$f.cases $D/$f-sse.mem > $D/$f-sse.out; done
  systemd-run --user --scope -p MemoryMax=4G python3 -I tools/sweep_s1e.py all      # checks, static, manifest
  ```
  The `-sse` runs set the CRT's SSE2 flag (`data:g_Sse2Available@0x00994C88`, written once at start-up by
  0x0069A8C5), which picks `memcpy`/`memset`'s path; both values must give the same output. `__locale_changed`
  (`data:g_LocaleChanged@0x0096DFE4`) is set to 0 by the spec: its one writer (0x006926F7) lies in
  `fn:CRT_setlocale@0x0069263E`, which has no caller and no pointer in the image (`sweep_s1e.py static`), so the ctype
  functions take their table path through `data:g_pctype@0x0074AB98`.
- **Observed** (`S1E` lines; `neg` = cases where the negative control's perturbed model differs, `undeclared` =
  traced accesses outside the declared read set):
  ```
  S1E rng      cases=3000 match=3000 bad=0 neg=2239 traced=0  undeclared=0
  S1E bitbuf   cases=2500 match=2500 bad=0 neg=881  traced=8  undeclared=0   clamped_neg=1092 clamped_pos=737 n32=77 overflow=404
  S1E eval     cases=6000 match=6000 bad=0 neg=205  traced=83 undeclared=0   lone_op=256 stack_full=5844 len_le0=232 operand_past_len=197
               var_null=714 f_out_of_range=2406 argc0=58 argc1=89 argc2=1102 argc3=85 argc_other=124 div_zero=522 pow=369
               pow_e_le0=936 ternary_short=430 wrap10/11/12=30/38/99 rand_in_unused_drew=3 sklvl=15
  S1E calcvar  cases=5000 match=5000 bad=0 neg=25   traced=53 undeclared=0   codes 0-16 21 22 35-37 42 54-72 >72, each also at lvl < 1
  S1E entry    cases=1556 match=1556 bad=0 neg=227  traced=23 undeclared=0   null_pool=126 off_ge_size=722 eval=708
  S1E excel    cases=5500 match=5500 bad=0 neg=1048 traced=79 undeclared=0   find_probe_ge_2^31=1021 find_case_variant_miss=316
               find_unsorted=336 add_bumped=665 add_wrapped=221 name_key_over_31=435 name_key_over_31_hit=57 name_mixed_case=894
  S1E lang     cases=182  match=182  bad=0 neg=28   traced=201 undeclared=0  entries 0-12, entry0 (ids >= 14)=70, entry13=28
  S1E strings  cases=885  match=885  bad=0 neg=423  traced=0  undeclared=0   GetByIndex 373 (via 11078: 141, entry 500: 218)
               key lookups at string entry 0: 10, found nowhere: 48; charcount_nofontmap=300
  S1E compile  cases=3620 match=3620 bad=0 neg=112  traced=334 undeclared=0  compile_ok=2109 compile_fail=891 bare_ident_var0=402
               itemvar_zero=200 cell_append=190 cell_fail=97 cell_null=13 cell_noop_off0=120      (compile-sse: identical)
  S1E parsetxt cases=400  match=400  bad=0 neg=399  traced=87 undeclared=0   int_byte_ge_0x80=2312 code misses 1 931, name misses 1 258
               name_over31=1 058                                                                    (parsetxt-sse: identical)
  S1E static   pins=53 pins_ok=53 clamp_sequence_equal=1 data_reads=6 data_stores=6 (all six in entry 13 and entry 12 +0x14)
               locale_changed_writers=1 setlocale_refs=0
  ```
  One informative case outside the checks: `CALC_Eval` on `09 00000080 07 FF 13 00` (`INT32_MIN ÷ −1`) returned 0 under
  the emulator; the hardware raises the divide error there. ADR-0015 condition 5 excludes faults, so it is evidence of
  nothing and is recorded as a SLEIGH limit for this instruction.
- **Conclusion:** bit-exact reproduction (evidence rule 4, under ADR-0015) of every function above on the cases
  listed, with each traced access declared (the per-family read sets and the writer scan are in the "Plan 0038 batch
  S1e" sections of [data/0005](0005-calc.md#plan-0038-batch-s1e-2026-10-17),
  [data/0001](0001-excel-loader.md#plan-0038-batch-s1e-2026-10-17), [data/0002](0002-mpq-precedence.md#plan-0038-batch-s1e-2026-10-17),
  [data/0003](0003-string-tables.md#plan-0038-batch-s1e-2026-10-17), [data/0004](0004-cell-converters.md#plan-0038-batch-s1e-2026-10-17),
  [rng/0001](../rng/0001-rng-core.md#plan-0038-batch-s1e-2026-10-17) and [save/0001](../save/0001-d2s-io.md#plan-0038-batch-s1e-2026-10-17)).
  It contradicts one statement: `LNG_GetLanguageCode` does not fall back to entry 0 for id 13 (data/0002). Not
  covered: faults (the divide error, the language table's entry 13 copy), `TC_ParseItemCell` (every resolved cell
  allocates through 0x0040B4B0), and who calls these functions in play. (fn:CALC_Eval@0x006C0BC0,
  fn:CALC_Compile@0x006C1AE0, fn:SKILLS_CalcVar@0x00646460, fn:EXCEL_ParseTxt@0x006BD780)
- **Review re-run (architect, 2026-10-17).** The manifest matches its 53 files. `sweep_s1e.py static` (53 of 53 pins,
  the writer scan, `clamp_sequence_equal=1`) and `test_sweep_s1e.py` (10 tests) re-run identically. Under the lane's
  Ghidra copy (heap 3 GB, `tools/ghidra.sh emutrace`), the kept `lang` and `calcvar` cases gave outputs byte-identical
  to the kept `.out` files, and `check` gave `lang` 182/182 (neg 28, undeclared 0) and `calcvar` 5 000/5 000 (neg 25,
  undeclared 0). `cases` regenerated every family's files identically except `eval`: its skill index for the
  `skillsvar` configuration was drawn from Python's unseeded module generator (`CalcVarWorld.rnd_skill()` called
  without the family's generator), so the kept `eval.cases` cannot be regenerated. The review fixed the call (the
  generator is now a required argument; `tools/sweep_s1e.py` `c9134335…`, the other families' output unchanged),
  regenerated `eval` twice (identical), and ran it: 6 000/6 000 bit-exact, neg 196, undeclared 0. The kept `eval`
  files remain the lane's record; the fixed tool regenerates a different, reproducible case set. A corrupted `eval`
  output (one EAX bit flipped, one undeclared read added) gave `bad=2`, `undeclared=1`, so the checker fails when it
  should.

## run:2026-10-17-sweep-emu2

- **Question:** (plan 0038 batch S1f, the 15 c-emu statements of [inventory § 2.6](../../plans/0038-inventory/README.md#26-moves-made-by-the-batch-reviews),
  S1f table) Do `MONSTATS_ValidId`, `sub_00483360_MulDiv`, `sub_005C0D00_AffixCandAdd` and its caller
  `ITEMS_PickMagicAffix`, `SKILLS_CalcVar` codes 43–48, `EXCEL_ParseTxt`'s defaults pass and callback order,
  `sub_005BDB20_MonVariantRoll` and `ITEMS_BuildSetPick` do what the findings say on the branches no stock play
  reaches, with no case reaching the allocator, an import or the fatal path?
- **Setup:** as run:2026-10-17-sweep-emu: Ghidra 12.1.2 p-code emulator (`EmulatorHelper`) on the pinned `game.exe`,
  lane copy `GHIDRA_PROJ_DIR=workspace/ghidra-s1f` (symbols replayed from `re/symbols.csv`), heap 3 GB, each run under
  `systemd-run --user --scope -p MemoryMax=4G`. No wine, nothing runs natively, no slot. `re/ghidra_scripts/EmuTrace.java`
  (`3255db0c…`) gains one directive, `guard <addr>`: a case whose pc reaches the address stops (`STOP … guard address
  reached`); the S1e records do not use it and re-run unchanged. Every S1f memory spec guards the fatal path
  (0x00408090, 0x00408A60, 0x00681E09) and the three pool-allocator entries (0x0040B4B0, 0x0040B430, 0x0040B480), so
  review condition (a) is checked by the tool: a case that reached either would be a `STOP`, and every family has
  `stopped=0`. Models, case writers and checks: `tools/sweep_s1f.py` (`0fb5b3fc…`, which imports `tools/sweep_s1e.py`'s
  report, read-set accounting, CALC models and `.txt` world), unit tests `tools/test_sweep_s1f.py` (`b4c55e4d…`, 7). All
  inputs are synthetic, written by generators seeded `"s1f-<family>"` (worlds by fixed integer seeds); `cases` regenerates
  every file byte for byte (checked against the kept files). DataTables fields are written one dword per field the
  code reads (not a whole page), so a read of any other field would be traced. Files in `workspace/logs/sweep-s1f/`,
  `manifest.txt` `a1e058cc…` (38 files: cases, memory specs, expected inputs, outputs). Full report
  `workspace/logs/sweep-s1f-all.txt` (`e108a769…`).
- **Procedure:**
  ```
  D=workspace/logs/sweep-s1f
  python3 -I tools/sweep_s1f.py cases                     # D/<family>.cases, .mem, .json; parsetxt2-sse.mem
  for f in validid muldiv candadd calcvar2 varroll setpick guardctl parsetxt2 pickaffix; do
    tools/ghidra.sh emutrace $D/$f.cases $D/$f.mem > $D/$f.out
  done
  tools/ghidra.sh emutrace $D/parsetxt2.cases $D/parsetxt2-sse.mem > $D/parsetxt2-sse.out
  python3 -I tools/sweep_s1f.py manifest --write
  python3 -I tools/sweep_s1f.py all                        # checks, static, manifest; exits 0
  ```
  (The lane ran `analyzeHeadless … -readOnly -postScript EmuTrace.java <out> <cases> <mem>` with its own `-log`, the
  same script call `tools/ghidra.sh emutrace` makes, because another lane shared `workspace/logs/ghidra-last.log`.)
- **Observed** (`S1F` lines; `neg` = cases where the negative control's perturbed model differs; `undeclared` = traced
  accesses outside the declared read set; `stopped` = cases that did not return):
  ```
  S1F validid   cases=2000 match=2000 bad=0 neg=190  traced=0   undeclared=0 stopped=0  in_range=599 id_ge_n=830 neg_id=571 n_le0=532
  S1F muldiv    cases=4000 match=4000 bad=0 neg=1948 traced=0   undeclared=0 stopped=0  c0=382 32bit=272 32bit_wrapped=1300
                a_big_div_first=605 a_big_64=215 (q_wide 39) b_big_div_first=960 b_big_64=266 (q_wide 26) neg_c=1030
  S1F candadd   cases=3000 match=3000 bad=0 neg=65   traced=0   undeclared=0 stopped=0  stored=1635 at_or_past_cap=1365
                n_eq_510=78 n_eq_511=65 n_negative=195
  S1F pickaffix cases=500  match=500  bad=0 neg=125  traced=9   undeclared=0 stopped=0  eligible_gt_511=207 eligible_le_511=245
                x_beyond_stored=22 x_within_stored=185 fell_through_last=22 picked=383 picked_last=33 no_candidate=14
                no_roll=48 autogroup=64 weight_freq_x_level=182
  S1F calcvar2  cases=3000 match=3000 bad=0 neg=239  traced=10  undeclared=0 stopped=0  code43..48: 204 219 213 202 198 196
                (missile 0, 0, 0, 0, 1, 1) calc_eval=611 calc_none=462 calc_off_ge_size=159 lvl_le0=232 no_skilldesc=583
                no_missile=461; MulDiv inside: 32bit=67 32bit_wrapped=292 a_big_div_first=205
  S1F parsetxt2 cases=300  match=300  bad=0 neg=300  traced=402 undeclared=0 stopped=0  neg_desc_order=290 rows=618
                absent entries by type 01..1A: every type, 113..1 261 each; calc_columns_present=3092 unknown_header=221
                                                                                       (parsetxt2-sse: identical)
  S1F varroll   cases=3000 match=3000 bad=0 neg=192  traced=0   undeclared=0 stopped=0  tries_went_negative=192
                (ended at tries -1: 112, -3: 38, -5: 25, -7: 10, -9: 3, -11: 3, -13: 1) stopped_at_zero_appended_dup=93
                k1=1084 k_ge2=137 set0=233 cap_binds=1142 n_le0=645 full=78 no_monstats2=930
  S1F setpick   cases=3000 match=3000 bad=0 neg=254  traced=1   undeclared=0 stopped=0  weight0_as_1=1842 picked_weight0=230
                weight_negative=2452 total_negative_nodraw=458 walk_fails=134 total0_return=1878 picked=976 forced=12
  S1F guardctl  cases=2    match=2                                                       guard_fatal=1 guard_alloc=1
  S1F static    pins=65 pins_ok=65 masks_ok=1 ro_reads=9 data_stores=0
  ```
  `guardctl` is the guards' own control: `MonVariantRoll` with a NULL seed stops at 0x00408090 (the assert path) and
  the item calc cell callback appending to a pool at capacity stops at 0x0040B4B0 (`CalcPoolAppend`'s growth). A
  corrupted `varroll` output (one entry byte changed, one undeclared read added) gave `bad=2`, `undeclared=1`.
- **Conclusion:** bit-exact reproduction (evidence rule 4, under ADR-0015) of the eight functions on the cases above,
  each traced access declared and no case stopped. Per-statement rulings and read sets are in the "Plan 0038 batch
  S1f" sections of [drlg/0004](../drlg/0004-preset-units.md#plan-0038-batch-s1f-2026-10-17),
  [monsters/0004](../monsters/0004-stats.md#plan-0038-batch-s1f-2026-10-17),
  [monsters/0001](../monsters/0001-level-pool.md#plan-0038-batch-s1f-2026-10-17),
  [items/0005](../items/0005-affixes.md#plan-0038-batch-s1f-2026-10-17),
  [items/0004](../items/0004-uniques-sets.md#plan-0038-batch-s1f-2026-10-17),
  [data/0005](0005-calc.md#plan-0038-batch-s1f-2026-10-17) and [data/0004](0004-cell-converters.md#plan-0038-batch-s1f-2026-10-17).
  Not covered: faults (`MulDiv`'s `INT32_MIN ÷ −1` in its 32-bit branch was left out of the cases), property
  functions (every set record had no property, every affix pick ran with `applyProps` 0), registration columns
  present in a `.txt` (their first pass allocates), and who calls these functions in play.
  (fn:MONSTATS_ValidId@0x004E6C50, fn:sub_00483360_MulDiv@0x00483360, fn:ITEMS_PickMagicAffix@0x005C1560,
  fn:SKILLS_CalcVar@0x00646460, fn:EXCEL_ParseTxt@0x006BD780, fn:sub_005BDB20_MonVariantRoll@0x005BDB20,
  fn:ITEMS_BuildSetPick@0x005C25C0)
- **Review re-run (architect, 2026-10-17).** The manifest matches its 38 files. `sweep_s1f.py static` (65 of 65 pins,
  the closures, the writer scan: 0 stores) and `test_sweep_s1f.py` (7 tests) re-run identically, and `cases` into a
  fresh directory regenerated every kept `.cases`, `.mem` and `.json` byte for byte. Under the lane's Ghidra copy
  (`analyzeHeadless … -readOnly -postScript EmuTrace.java`, heap 3 GB, `MemoryMax=4G`, the review's own `-log`), the
  `muldiv`, `setpick` and `pickaffix` cases gave `.out` files byte-identical to the kept ones, and `check` gave
  4 000/4 000 (neg 1 948), 3 000/3 000 (neg 254) and 500/500 (neg 125), undeclared 0, stopped 0. A corrupted `setpick`
  output (one EAX bit flipped, one undeclared read added) gave `bad=2`, `undeclared=1`; one case rewritten as a guard
  stop at 0x0040B4B0 gave `stopped=1`, so a guarded case cannot pass. Anchors read with objdump at the review:
  `MONSTATS_ValidId` whole; `MulDiv` whole (0x00483360–0x004833D7) and its `CRT_alldiv` call; `AffixCandAdd` whole and
  the caller's weight adds (0x005C17E1/0x005C17EA); `ITEMS_BuildSetPick`'s store, zero-total exit and walk
  (0x005C2675–0x005C26FB); `MonVariantRoll`'s `tries` (0x005BDCC0, 0x005BDE28, 0x005BDE46) and `shl esi, cl`
  (0x005BDB87); the defaults dispatch at 0x006BDFBE, its 26-entry table at 0x006BE128 and the callback call
  (0x006BDFFC–0x006BE01A: ECX 0, EDX the record, the offset as the first stack argument); the `÷ 3` sequences
  (0x006468BE, 0x00646918). All match the ledgers.

## run:2026-10-27-sweep-data-load

- **Question:** (plan 0038 batch H3b, `data-load`) Do the startup and load steps of data/excel, data/strings and
  data/README that no attached logger could see (gdb came 3 s after the window) reproduce from program start: the file
  I/O mode, the archive opens and their list, the file lookup and its sources with and without `-direct`, `-txt`, the
  language byte, the string-table load and release, the excel load order, the item-code and TC-name lookups, the
  record bytes filled at load, and the client's rare-name lines?
- **The start mode (review ruling 3, built and tested before the batch):** `tools/d2run.py --early`. The launcher polls
  every 2 ms for a descendant whose command line holds `\game.exe` and whose `/proc/<pid>/maps` maps that file at
  0x00400000, sends it SIGSTOP, forks the driver (which waits for the window itself) and execs gdb on the stopped
  process; gdb attaches and the script's `continue` resumes it. Tested first off-slot on a stopped two-thread
  process (attach, resume, normal exit), then on slot 2 with a probe script (the game stopped 0.9–2.0 s after launch;
  breakpoints at `InitGame`, `InitFileIO`, the archive opens, the language index and both `LoadAll`s hit). The probe
  runs without `set displaced-stepping off` ended the game at its second breakpoint (exit code 5, an empty
  `BlizzardError/<time>/Crash.txt` in the game directory, removed); with it, as every harness logger has it, the game
  ran normally. In the kept runs the stop came 0.50–0.57 s after launch and `XATT` found every startup global still 0.
- **Setup:** seven runs, single player, expansion, Normal, harness slot 2 only (display `:9`, prefix
  `workspace/wineprefix-2`, ADR-0011), launched by `tools/h3b_sessions.py run --slot 2 --tag h3b --save
  workspace/runtime/h3b-chars/H3bRare.d2s --run h3b <session>…` (revision `6b4acfde…` for the first four,
  `377e7355…` for the last three, which only adds them), each as `tools/d2run.py --slot 2 --early --seed N --gdb
  tools/gdb/excel.gdb --steps tools/gdb/enter-normal.steps --after 1800 --install h3b <save> --game-dir <dir>
  [--game-args=…]` (`d2run.py` `d80370bc…`) and then the xdrive steps files `tools/gdb/h3b-hover.steps`,
  `h3b-leave.steps` (Escape, *Save and Exit*, *Exit* to the main menu), `h3b-cine.steps` (*Cinematics*, the first
  film, Escape, *Cancel*) and `h3b-quit.steps` (*Exit Diablo II*). Logger `tools/gdb/excel.gdb` (`75ebc28c…`):
  `tools/gdb/pilot.py` (`1ad48a4c…`), `tools/gdb/strings.py` (`b9ebdb10…`) and `tools/gdb/excel.py` (`0e59d2e7…`;
  the `X*` lines, documented in its header; record dumps into `$H3B_DUMP`). Breakpoints only print and continue.
  - **Character** (ADR-0003 tool-built input): `H3bRare`, `python3 -I tools/d2s.py build workspace/merged/data/global/excel
    tools/d2s_recipes/h3brare.json workspace/samples/d2s-owner/smpsor-l50.d2s workspace/runtime/h3b-chars/H3bRare.d2s`
    (recipe `52aa64e8…`, save `ce57d8f7…`): four rare items in the inventory, names (160, 121), (200, 10), (170, 50),
    (230, 100); 230 is past the 201 merged rare-name records. Installed with `--install` on an empty aside `h3b`, the
    saves directory restored after every run (`saves.py --slot 2 status`: empty, no aside, idle at the end).
  - **Game directories** (`h3b_sessions.py stage --slot 2`, all under `workspace/wineprefix-2/h3b/`, each a symlink
    farm of `workspace/runtime/game` plus its own files; removed with `unstage` after the checks, their files hashed in
    `check/staged-files-h3b*.txt`): `game-txt` (an empty `data/global/excel/`), `game-loose` and `game-direct` (as
    listed in [data/0002 § Plan 0038 batch H3b](0002-mpq-precedence.md#plan-0038-batch-h3b-run2026-10-27-sweep-data-load)),
    `game-rus` (`data/local/use` = `0B`), `game-clamp` (`data/local/use` = `0E`). The stock run used
    `workspace/runtime/game` itself. The two `-txt` runs' written `.bin` files are hashed in
    `check/txt-written-bins-h3b.txt` and `…-dtxt.txt` (the same 90 hashes).
  - **Runs:**

    | seed | session | directory, switches | play | end |
    |---|---|---|---|---|
    | 3101 | stock | `workspace/runtime/game` | hover, leave, cinematic, quit | exited normally |
    | 3102 | txt | `game-txt`, `-txt` | leave, quit | exited normally |
    | 3103 | loose | `game-loose` | leave, quit | exited normally |
    | 3104 | direct | `game-direct`, `-direct` | leave, quit | exited normally |
    | 3105 | dtxt | `game-txt` (restaged, empty), `-direct -txt` | leave, quit | exited normally |
    | 3106 | rus | `game-rus`, `-direct` | none (no game) | exit code 0377 at the font map |
    | 3107 | clamp | `game-clamp`, `-direct` | leave, quit | exited normally |

- **Logs** (workspace, not in git): `workspace/logs/h3b/h3b-s2-<seed>-<session>.log`, the dumps beside each in
  `…-dump/`, the screenshots in `…-shots/`, the driver output in `.driver.txt` and `h3b-sessions*.driver-main.txt`;
  manifest `workspace/logs/h3b/h3b-manifest.sha256` (`0b75400a…`, 88 files, `sha256sum -c` from `workspace/logs/h3b`).
  Development runs (the probes, two early stock runs; no claim rests on them): `workspace/logs/h3b/dev/`, manifest
  `h3b-manifest-dev.sha256` (`73e35bff…`, checked from `workspace/logs/h3b/dev`).
- **Procedure:**
  ```
  python3 -I tools/h3b_sessions.py stage --slot 2          # the loose files again, byte for byte (staged-files-h3b-2.txt)
  python3 -I tools/sweep_h3b.py check --written workspace/logs/h3b/check/txt-written-bins-h3b-dtxt.txt \
      workspace/logs/h3b/h3b-s2-310{1-stock,2-txt,3-loose,4-direct,5-dtxt,6-rus,7-clamp}.log
      # check/check-h3b.txt, sweep_h3b.py 2872bc90…; TOTAL bad=0 (check-h3b-rev1.txt, by 8a60af88… with the
      # directories still in place after the runs, is the same byte for byte)
  python3 -I tools/h3b_sessions.py unstage --slot 2
  python3 -I tools/sweep_h3b.py txtfiles <game-txt>/data/global/excel     # check/txtfiles-h3b.txt, …-dtxt.txt
  CHECK txtfiles written=90 identical=89 different=1                      # monstats.bin
  python3 -I tools/tbl.py check workspace/merged/data/local/lng/eng <log>  # check/tbl-check-h3b.txt: 0 mismatches
  ```
  Per run (stock / txt / loose / direct / dtxt / rus / clamp):

  | check | result |
  |---|---|
  | early | `XATT` early in all 7; `InitFileIO` `ECX` 0/0/0/1/1/1/1, both direct flags equal after it |
  | archives | 12 startup opens in A1's order and priorities, 10 handles, in all 7; A2's list after every open (22 / 14 × 6 snapshots); stock: one `d2video` open at 1000, front of the 1000 band, 5 game archives closed and reopened around it |
  | files | `FindFile` in `FILE_LoadWhole` 442 / 530 / 418 / 418 / 521 / 8 / 413, every one as A3; buffers equal to the source the model picks (the 3 rus failures excepted, which return 0); disk 0 / 0 / 0 / 5 / 95 / 1 / 1; all `FindFile` calls 1 107 / 1 186 / 1 074 / 1 072 / 1 173 / – / 1 064 |
  | language | `use` byte 00 / 00 / 00 / 00 (4 bytes) / 00 / 0B / 0E → 0 / 0 / 0 / 0 / 0 / 11 / 0 |
  | strings | 3 loads at count 0 and 3 releases to 0 per run (not rus); no count above 1 |
  | excel | one `LoadAll`; 73 / 91 / 73 / 73 / 91 / – / 73 tables, each with its `.bin` read; the 18 `-txt`-only calls only under `-txt`; the same order in every run |
  | lookups | `ITEMS_GetByCode` 127 / 323 / 126 / 125 / 321 / – / 125 lines (29 in play); `EXCEL_FindName` on `g_TCLink` 503 / 858 / 503 / 503 / 858 / – / 503; `TC_GetByName` 0 hits |
  | records | 10 dumps per run (not rus), every byte as listed in data/0004 § H3b |
  | hover (stock) | 7 rare-name indices at the two client calls, each the record's load-time key index; 1 id without a record |
  | rus | the first failed load `DATA\LOCAL\Font\CYR\Font16.dc6`, then `Font16.tbl`, `default.map`; no `LoadAll` returned |

- **Conclusion:** the start mode works, and every logged event reproduces with 0 mismatches. Per-statement rulings are
  in the "Plan 0038 batch H3b" sections of [data/0001](0001-excel-loader.md#plan-0038-batch-h3b-run2026-10-27-sweep-data-load),
  [data/0002](0002-mpq-precedence.md#plan-0038-batch-h3b-run2026-10-27-sweep-data-load),
  [data/0003](0003-string-tables.md#plan-0038-batch-h3b-run2026-10-27-sweep-data-load),
  [data/0004](0004-cell-converters.md#plan-0038-batch-h3b-run2026-10-27-sweep-data-load) and
  [player/0001](../player/0001-creation.md#plan-0038-batch-h3b-run2026-10-27-sweep-data-load). Not reached: a
  string-table load or release with the count above 1, the third `STRTABLE_LoadAll` caller 0x00441B91, the raw rare name
  for a stored index of 0, the charstats name fallback, and any TC name lookup in play.
  (fn:STRTABLE_LoadAll@0x005259C0, fn:STORM_FindFile@0x00417F10, fn:DATATBLS_LoadAll@0x00619300)
