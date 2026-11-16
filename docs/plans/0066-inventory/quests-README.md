# Plan 0066 inventory: quests/README

- **Spec:** [quests/README](../../specs/quests/README.md), read at `main` `b5999f5e`.
- **Front matter `I`:** 6; the *Count* column sums to 6.
- Classes, batches and conventions as in [the inventory README](README.md#conventions).

| # | Line | Section | Claim (excerpt) | Anchor | Class | Route or reason | Batch | Count |
|---|---|---|---|---|---|---|---|---|
| 1 | 62 | Shared model | The bit grammar. Bit 0 done, bit 1 done with a reward pending, bits 2–11 … | – | a-logs | QS/QC lines and the written saves of the plan 0042 logs (save_check): bits 0, 1, 2-11, 12 by their writers **S3a 2026-11-15: raised in part.** [C] bits 0 and 1 by their writers (the reward pairs of row 56 on 9 words), bit 13 (game record and player), bit 15 (word 9's clear) and `SetState`/`ClearState` on the word (430 QS, 38 QC next-old pairs) (`s3a-check.txt` P13, `s3a-check-r2.txt` P16/P56). Remainder → a-run (H3a): bits 2 to 11, as progression row 16. | S3a | 1 |
| 2 | 72 | Shared model | Draws. Quest events draw on the quest seed (NPC 331, the eclipse, the cairn order, … | – | a-logs | the per-kind seed lines and QGS reads of the plan 0042 and quests.gdb logs **S3a 2026-11-15: raised in part.** [C] the quest-seed draws named here run at their sites only (progression rows 63, 65, 322: NPC 331 45, Anya 3, the eclipse 3, the timers 7) (`s3a-check.txt` P63, P65, P322). Remainder → b (H3b): the kill draws (cairn order aside). | S3a | 1 |
| 3 | 82 | Shared model | The Zoo's quest-seed draws and NPC 377's player-seed draw are not reached on stock data: … | – | c | the DS1, Levels and SuperUniques scans for object 567 and NPC 377 repeated with a second parser (as progression 179, 302) **S3c part 1 2026-11-16: not settled, → S3c part 2.** Open: the DS1/Levels/SuperUniques scans with a second parser. **S3c part 2 2026-11-16: raised.** [C] as progression 179 and 302: no LvlPrest-named DS1 places NPC 377 or its placeholders, and no DS1 places object 567; two DS1 readers, tables read twice (`check-s3c-p2.txt` data). | S3c | 1 |
| 4 | 91 | Shared model | The Durance portal places the player the same way, read from the code. | `fn:sub_00546AC0_DuranceActTravel@0x00546AC0` | a-run | the Durance portal operated under the `durance` bracket (travel 49) | H3e | 1 |
| 5 | 98 | Inputs and oracles | party membership, the players' rooms and near lists, held … — input | `fn:sub_00540510_PartyForEach@0x00540510` | d-2c | party membership and near lists of several players | – | 1 |
| 6 | 113 | Evidence and status | for this plan: the steps triggered by kills, boss events | – | d-none | an evidence-status note: names what stays inferred, no claim of its own | – | 1 |

**Totals by class:** a-logs 2, a-run 1, c 1, d-2c 1, d-none 1 (sum 6).
