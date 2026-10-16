# Plan 0038 inventory: items/sockets-runewords

Phase 0 of [plan 0038](../0038-inferred-claims-sweep.md), cluster (0a) items.

- **Spec:** [items/sockets-runewords](../../specs/items/sockets-runewords.md), status `reviewed`, read at commit `c3167c6` (on `main` at `e1c807a`).
  Front matter `I` = **77**; the *count* column below sums to 77.
- **Finding:** [items/0007](../../findings/items/0007-sockets-runewords.md); run records in
  [findings/items/experiments.md](../../findings/items/experiments.md).
- **Columns.** *Section* links the spec section and lists the spec lines of the statements at that commit. *Anchor* is the
  finding number and the first code address of the statement. *Class*, *tier* and *batch* follow the plan's
  [Classes](../0038-inferred-claims-sweep.md#classes). A forced-run row is class `b` with a route that starts `forced:`.
  A `—` batch means the row is class (d) and no batch takes it.
- **Totals by class:** a-logs 18, b 23, c 9, d-edit 16, d-none 11.

| # | Section | Claim | Anchor | Class | Route | Tier | Batch | Count |
|---|---|---|---|---|---|---|---|---|
| 1 | [Entry points](../../specs/items/sockets-runewords.md#entry-points) (L51, L283, L284, L288) | Golem reader and item copier re-insert children (their caller values) | 0007 · `0x0056AE50` | b | sock plan: personalize a socketed item (copier) and an iron golem from a socketed item; sockets.gdb | T2 | H6b | 4 |
| 2 | [Entry points](../../specs/items/sockets-runewords.md#entry-points) (L52) | Creation sets the socket count through ITEMS_SetSockets | 0007 · `0x0062BCB0` | a-logs | props SOK lines and cube-sock logs | T2 | S2c | 1 |
| 3 | [Entry points](../../specs/items/sockets-runewords.md#entry-points) (L59) | Readers and copier set the child to mode 4 | 0007 · `0x0056ADF5` | a-logs | sockets-load logs (saves with socketed items loaded) | T2 | S2c | 1 |
| 4 | [Tables](../../specs/items/sockets-runewords.md#tables) (L90) | itype/etype offsets in the Runes record | 0007 · `0x0062BFD0` | a-logs | sockets.py runeword matches (50) and non-matches | T2 | S2c | 1 |
| 5 | [Tables](../../specs/items/sockets-runewords.md#tables) (L93) | T1Param cells resolve through PropParamCell | 0007 · `0x006336A0` | c | data check: the 109 stock cells | T3 | S2c | 1 |
| 6 | [Tables](../../specs/items/sockets-runewords.md#tables) (L99) | Name → +0x82; Passion and Patience share an index | 0007 · `0x006394A0` | c | loader read against the save field (Steel holds 0x509F) | T3 | S2c | 1 |
| 7 | [Tables](../../specs/items/sockets-runewords.md#tables) (L103) | Gems `letter` in the client description | 0007 · `0x00486670` | d-none | client display only; no mechanic to observe | T3 | — | 1 |
| 8 | [Constants](../../specs/items/sockets-runewords.md#constants) (L128) | Gem group offsets +0x30/+0x60/+0x90 | 0007 · `0x0065C6D0` | a-logs | sockets.py: gem inserts into weapons, armour and shields | T2 | S2c | 1 |
| 9 | [A. The client test](../../specs/items/sockets-runewords.md#a-the-client-test) (L167) | Client refuses outside UI states 10/11 | 0007 · `0x007BCBF0` | b | sock-refuse plan: click a gem with another UI state | T3 | H6b | 1 |
| 10 | [A. The client test](../../specs/items/sockets-runewords.md#a-the-client-test) (L170, L171) | Client refuses hasinv 0 and ItemMaxSockets 0 | 0007 · `0x004843E0` | b | sock-refuse plan: gems on unsocketable bases | T2 | H6b | 2 |
| 11 | [A. The client test](../../specs/items/sockets-runewords.md#a-the-client-test) (L172) | Client refuses an unidentified target | 0007 · `0x004843E0` | d-none | screened by the socketed test first (A1 note) | T3 | — | 1 |
| 12 | [A. The client test](../../specs/items/sockets-runewords.md#a-the-client-test) (L173, L174) | Client refuses flag 0x100 and no inventory | 0007 · `0x004843E0` | b | sock-refuse plan: broken (0x100) target | T3 | H6b | 2 |
| 13 | [A. The client test](../../specs/items/sockets-runewords.md#a-the-client-test) (L181) | Unseen client refusals stay [I] as refusals | 0007 · `0x004843E0` | b | as the client refusal rows | T2 | H6b | 1 |
| 14 | [A. The client test](../../specs/items/sockets-runewords.md#a-the-client-test) (L187) | An unidentified socketed parent fails as not socketed | 0007 · `0x004843E0` | a-logs | client flags in sock-refuse logs; else b (more cases) | T3 | S2c | 1 |
| 15 | [B. The server insert](../../specs/items/sockets-runewords.md#b-the-server-insert-the-refusal-list) (L214, L215, L216, L217, L218, L219, L220, L221, L223, L224, L225, L226, L255) | Server refusal lines screened by the client | 0007 · `0x00562660` | d-edit | reachable only by a forged 0x28 packet (ADR-0010) | T3 | — | 13 |
| 16 | [B. The server insert](../../specs/items/sockets-runewords.md#b-the-server-insert-the-refusal-list) (L236, L274) | Child x = count before append, y = 0 | 0007 · `0x0063AF20` | b | sockets.gdb: log child x and y at InvAppendItem | T2 | H6b | 2 |
| 17 | [B. The server insert](../../specs/items/sockets-runewords.md#b-the-server-insert-the-refusal-list) (L237, L291) | p4–p7 meanings; p5 clears the cursor | 0007 · `0x005627CB` | b | sockets.gdb: log cursor slot and option flags | T2 | H6b | 2 |
| 18 | [B. The server insert](../../specs/items/sockets-runewords.md#b-the-server-insert-the-refusal-list) (L243, L450) | Replenish events for stats 252 and 253 | 0007 · `0x00558530` | b | sock plan: insert into or make a runeword with a replenish stat | T3 | H6b | 2 |
| 19 | [B. The server insert](../../specs/items/sockets-runewords.md#b-the-server-insert-the-refusal-list) (L245) | Readers: no parent update | 0007 · `0x0056284F` | a-logs | sockets-load logs | T2 | S2c | 1 |
| 20 | [B. The server insert](../../specs/items/sockets-runewords.md#b-the-server-insert-the-refusal-list) (L246) | Parent flags update and client update | 0007 · `0x0056284F` | a-logs | parent flags in the sockets logs; else b | T2 | S2c | 1 |
| 21 | [B. The server insert](../../specs/items/sockets-runewords.md#b-the-server-insert-the-refusal-list) (L262) | No level-requirement test for the child | 0007 · `0x00562660` | b | sock plan: a low-level character inserting a high rune | T2 | H6b | 1 |
| 22 | [B. The server insert](../../specs/items/sockets-runewords.md#b-the-server-insert-the-refusal-list) (L268, L602) | Packet handler checks; error return 3 | 0007 · `0x0054B650` | d-edit | forged packets only; the trade part is d-2c | T3 | — | 2 |
| 23 | [B. The server insert](../../specs/items/sockets-runewords.md#b-the-server-insert-the-refusal-list) (L277) | Ladder games apply ladder-only rows | 0007 · `0x00562660` | d-none | no ladder game in this setup | T3 | — | 1 |
| 24 | [C. What a gem, rune or jewel brings](../../specs/items/sockets-runewords.md#c-what-a-gem-rune-or-jewel-brings) (L301) | Gem group ≥ 3 is fatal | 0007 · `0x0065C6D0` | d-none | no stock group ≥ 3 | T3 | — | 1 |
| 25 | [C. What a gem, rune or jewel brings](../../specs/items/sockets-runewords.md#c-what-a-gem-rune-or-jewel-brings) (L306) | Stock bases column: 384 hasinv rows | 0007 · `0x0065C6D0` | c | data check (rule 2) | T3 | S2c | 1 |
| 26 | [C. What a gem, rune or jewel brings](../../specs/items/sockets-runewords.md#c-what-a-gem-rune-or-jewel-brings) (L341) | The child is the handlers' item and target | 0007 · `0x0065EBA0` | a-logs | sockets.py child stat lists for Pul, Ith, Sol, Ohm inserts | T2 | S2c | 1 |
| 27 | [C. What a gem, rune or jewel brings](../../specs/items/sockets-runewords.md#c-what-a-gem-rune-or-jewel-brings) (L343) | `nummods` not read | 0007 · `0x0065C6D0` | a-logs | sockets.py reproduces without it | T2 | S2c | 1 |
| 28 | [C. What a gem, rune or jewel brings](../../specs/items/sockets-runewords.md#c-what-a-gem-rune-or-jewel-brings) (L346, L669) | `gemoffset` is the child's | 0007 · `0x0055C2C0` | a-logs | gem inserts into parents whose own gemoffset differs | T2 | S2c | 2 |
| 29 | [C. What a gem, rune or jewel brings](../../specs/items/sockets-runewords.md#c-what-a-gem-rune-or-jewel-brings) (L352) | List enable toggle; child flag 0x100 | 0007 · `0x0055C2C0` | b | sock plan: insert into an equipped parent | T2 | H6b | 1 |
| 30 | [C. What a gem, rune or jewel brings](../../specs/items/sockets-runewords.md#c-what-a-gem-rune-or-jewel-brings) (L354) | Client copy fatal on a missing row | 0007 · `0x004C0D20` | d-none | client only | T3 | — | 1 |
| 31 | [D. The runeword match](../../specs/items/sockets-runewords.md#d-the-runeword-match) (L420, L667) | One rune more than sockets reads a stale slot | 0007 · `0x0062BFA3` | d-none | a stale stack word; no controllable observable | T3 | — | 2 |
| 32 | [D. The runeword match](../../specs/items/sockets-runewords.md#d-the-runeword-match) (L422) | Scan order changes no stock result | 0007 · `0x0062BF6B` | c | data check over complete rows | T3 | S2c | 1 |
| 33 | [D. The runeword match](../../specs/items/sockets-runewords.md#d-the-runeword-match) (L424) | `etype` excludes; no stock row | 0007 · `0x0062BFD0` | d-none | no stock complete row uses etype | T3 | — | 1 |
| 34 | [D. The runeword match](../../specs/items/sockets-runewords.md#d-the-runeword-match) (L430) | The match tests no server, version or game type | 0007 · `0x0062BED0` | a-logs | sock-classic logs: runes in a classic game | T2 | S2c | 1 |
| 35 | [E. The runeword](../../specs/items/sockets-runewords.md#e-the-runeword-flag-list-and-rolls) (L438, L470) | A parent already holding a 171 list gets nothing | 0007 · `0x006600BC` | a-logs | sockets-load logs: reloaded runewords not rerolled | T2 | S2c | 2 |
| 36 | [E. The runeword](../../specs/items/sockets-runewords.md#e-the-runeword-flag-list-and-rolls) (L442, L472) | First blank ends the lines; no gap in stock rows | 0007 · `0x006600DD` | c | data check over 169 rows | T3 | S2c | 2 |
| 37 | [E. The runeword](../../specs/items/sockets-runewords.md#e-the-runeword-flag-list-and-rolls) (L479) | Func 8 reuse branch unreachable | 0007 · `0x0065F2B0` | d-none | func 8 is always the first slot | T3 | — | 1 |
| 38 | [E. The runeword](../../specs/items/sockets-runewords.md#e-the-runeword-flag-list-and-rolls) (L481, L482, L490, L505, L507) | Funcs 17, 24 and 20 in runewords | 0007 · `0x0065FA40` | b | sock-rw plans for Harmony or Fortitude (17), the func-24 row and an indestructible runeword (20) | T2 | H6b | 5 |
| 39 | [E. The runeword](../../specs/items/sockets-runewords.md#e-the-runeword-flag-list-and-rolls) (L486) | Func 7: no +1 fallback in runewords | 0007 · `0x0065F010` | d-none | weapon branch never taken | T3 | — | 1 |
| 40 | [E. The runeword](../../specs/items/sockets-runewords.md#e-the-runeword-flag-list-and-rolls) (L488) | Func 11 ilvl branch unreachable | 0007 · `0x0065F470` | d-none | every stock line has max > 0 | T3 | — | 1 |
| 41 | [E. The runeword](../../specs/items/sockets-runewords.md#e-the-runeword-flag-list-and-rolls) (L512) | Readers do not refill charges | 0007 · `0x0055FE80` | a-logs | sockets-load logs of a charged runeword | T2 | S2c | 1 |
| 42 | [F. Socket counts](../../specs/items/sockets-runewords.md#f-socket-counts-the-two-setters) (L521) | SetSockets clamps by quality, inventory, 6, max sockets | 0007 · `0x0062BCB0` | a-logs | props SOK, cube-sock and quest Larzuk logs | T2 | S2c | 1 |
| 43 | [F. Socket counts](../../specs/items/sockets-runewords.md#f-socket-counts-the-two-setters) (L537) | SetSocketsOnLoad without the quality switch | 0007 · `0x0062BE00` | a-logs | sockets-load and d2sio logs | T2 | S2c | 1 |
| 44 | [F. Socket counts](../../specs/items/sockets-runewords.md#f-socket-counts-the-two-setters) (L544) | Low, normal, superior: no quality clamp | 0007 · `0x0062BCB0` | a-logs | props SOK lines of normal and superior drops | T1 | S2c | 1 |
| 45 | [F. Socket counts](../../specs/items/sockets-runewords.md#f-socket-counts-the-two-setters) (L547) | SetSockets callers | 0007 · `0x00556B60` | c | full xref | T3 | S2c | 1 |
| 46 | [G. In the save](../../specs/items/sockets-runewords.md#g-in-the-save) (L556) | Runeword field in the save | 0007 · `0x006394A0` | c | second source: save/d2s writer and reader; Steel save value | T2 | S2c | 1 |
| 47 | [G. In the save](../../specs/items/sockets-runewords.md#g-in-the-save) (L565) | `n_filled` counts the child list when hasinv | 0007 · `0x0062A900` | c | second source: save/d2s reader | T2 | S2c | 1 |
| 48 | [G. In the save](../../specs/items/sockets-runewords.md#g-in-the-save) (L568) | A loaded runeword that no longer matches is discarded | 0007 · `0x00563470` | d-edit | needs an edited save or Runes table | T3 | — | 1 |
