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
