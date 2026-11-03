# 0012 — Item use and inventory: the use request and the dispatch by use type

> **Subsystem:** items/use
> **Question:** what does the server do when a player uses an item: which requests reach which use entry, what each
> `pSpell` kind does, with which amount rule and which draws, and what `useable`, `belt` and the warning columns gate?
> **Date:** 2026-11-03   **Plan:** 0060 (Phase 1.1)   **Status:** for review (`lane/r60a`)

Static reading of the pinned `Game.exe` (objdump and the lane's Ghidra copy `ghidra-r60a`), then emulation under ADR-0015
and ADR-0021 with `re/ghidra_scripts/EmuBoundary.java` (unchanged), `tools/use_emu.py` against the model
`tools/item_inventory.py` (run:2026-11-03-use-emu: **7 320 cases, 0 mismatches, 0 stops**, 11 families; each case ends at its entry's first callee against declared scratch
memory, so nothing after that callee is covered).

**Tag convention.** A claim marked **[C] (ADR-0021)** (run:2026-11-03-use-emu) rests on cases that end at a named callee's entry: nothing is
patched, the checker asserts per case the boundary, the return address, the arguments and the user's seed at it, and
**the callee and all code after it are not covered** (written "after, `[I]`"). The image is declared scratch, not the
game's own structures, so the `[C]` is the code's map from the bytes it reads (ADR-0015), and no symbol row is raised
(review-fixes 14). A plain `[I]` is a code reading the emulator does not reach. Nothing here ran on a live game: Phase 2 does.

## Answer (summary)

- [I] **Requests.** Packet `0x20` (use an inventory item) → `sub_0055E170_PlayerUseInvItem`; `0x26` (use a belt item) →
  `sub_00562390_PlayerUseBeltItem`; `0x27` (item on item: identify, tome and scroll on a target) →
  `sub_00561ED0_PlayerUseItemOnItem`; `0x61` (the mercenary button) → `sub_0054D230_MercGiveCursorItem`. Each ends in
  `sub_005BF240_ItemUse`; do 113 reaches the first two as well. (data:g_SrvPacketTable@0x006E0D18,
  fn:sub_0054B1E0_Pkt20UseInvItem@0x0054B1E0, fn:sub_0054B560_Pkt26UseBeltItem@0x0054B560,
  fn:sub_0054B280_Pkt27ItemOnItem@0x0054B280, fn:sub_0054D430_Pkt61MercItem@0x0054D430)
- [C] (ADR-0021) **The dispatch.** `ItemUse` refuses a user that is not type 0 or 1 and an item that is not type 4. A
  book or scroll with a Books row takes `Books+0x0C` as the skill argument and, when `Books+0x04 > 0`, that as the kind;
  otherwise the kind is Misc `pSpell`. A kind below 1, at or above 31, or with an empty slot returns 0. With a `test`
  (kind 1 only) and item flag 4 clear it ends at `test(item, 0, x, y, skill)`; else it sets flag 4 and ends at
  `use(item, arg2, x, y, skill)`. After either, `[I]`. (fn:sub_005BF240_ItemUse@0x005BF240, data:g_ItemUseFns@0x00741790,
  run:2026-11-03-use-emu)
- [C] (ADR-0021) **Healing and mana potions (kind 3): a total, spread over `len`, with a chance of double.**
  `calc1` is the **total**, not a per-frame rate. For `hpregen` and `manarecovery` it is `<< 8`, then scaled by class:
  life Amazon, Paladin, Assassin `v + (v >> 1)`, Barbarian and every non-player `2v`, the others `v`; mana Amazon, Paladin,
  Assassin `v + (v >> 1)`, Sorceress, Necromancer, Druid `2v`, the others `v`. **Then two draws on the user's seed when
  vitality (life) or energy (mana) is above 0:** `r1 = RangeB(stat)`, `r2 = Range(100)`, and `r2 < r1 >> 1` doubles the
  amount. Then `<< ValShift`; a refill's frame rate is `(old rate · remaining + v) / (len + remaining)`, truncated, and
  the list's end moves to `now + remaining + len`. The rate is observed on a slot after the first; the stock potions'
  slot 0 reaches the same instructions only past the event queue call, so for them it is `[I]` (§ 4). (fn:sub_005BE3F0_ItemUsePotion@0x005BE3F0,
  fn:sub_0062A5D0_PotionLifeMul@0x0062A5D0, fn:sub_0062A620_PotionManaMul@0x0062A620, run:2026-11-03-use-emu)
- [C] (ADR-0021) **Rejuvenation (kind 5): a percent of the maximum, at once, no draw.** `v = MulDiv(max, calc, 100)`, or
  `max` itself at exactly 100, capped so `current + v ≤ max`, added to the stat by `UnitAddStat`; stock `rvs` 35 and `rvl`
  100 percent of life and of mana. (fn:sub_005BEAC0_ItemUseRejuv@0x005BEAC0, run:2026-11-03-use-emu)
- [C] (ADR-0021) **Elixir (kind 8): neither `stat1` nor `calc1`.** It adds the **item's** stat 71 to the stat numbered
  by the item's file index (ItemData `+0x28`) when that is a valid stat and the value is not 0. No draw before the
  boundary. (fn:sub_005BF060_ItemUseElixir@0x005BF060, run:2026-11-03-use-emu)
- [C] (ADR-0021) **Identify (kind 1) is two requests.** The test sets item flag 4 on the scroll or tome and ends at the
  client message (`0x3F`, the row's spell icon, the skill), returning 1 so that `ItemUse` returns 0: nothing is used up.
  The use refuses while the user interacts with a player unit that exists, for an identified target, and for a target
  not in the user's inventory; else it ends at `sub_00562590_ItemIdentify(target)`.
  (fn:sub_005BE130_ItemUseIdentifyTest@0x005BE130, fn:sub_005BE230_ItemUseIdentify@0x005BE230, run:2026-11-03-use-emu)
- [C] (ADR-0021) **The cube (kind 7) opens, returns 0, and is never used up.** For a player not busy it ends at
  `PlayerSetInteract(user, 4, cube guid)`; busy, it goes on only when the interaction is object class `0x10B`, ending at
  `PlayerClearInteract`; else it returns 0. (fn:sub_005BF0C0_ItemUseCube@0x005BF0C0, run:2026-11-03-use-emu)
- [C] (ADR-0021) **Keys have no use entry** (`key` has `useable` 0 and no `pSpell`). `sub_0055F140_KeyConsume` takes the
  first item of type 41 on page 0 in the inventory; quantity − 1 above 0 ends at `UnitAddStat(key, 70, −1, 0)`, else at
  the removal `sub_0055E000_InvItemConsume`; no key returns 0. Its two callers are the chest (skipped for class 6) and a
  case of the object mode switch. (fn:sub_0055F140_KeyConsume@0x0055F140, fn:OBJOP_Chest@0x00585F60, 0x00581DC1,
  run:2026-11-03-use-emu)
- [C] (data + code) **What the columns gate.** On the server `useable` (`+0x11D`) is a required test of both use
  requests: 2 of its 5 getter calls are theirs, the other 3 in client code. `belt` (`+0x130`), `autobelt`, `durwarning`
  and `qntwarning` gate **no use**: their readers are in § 7. A `useable` row with no `pSpell` (`hpo`, `rps`, …) passes
  the test and does nothing. (fn:sub_00628C20_ItemIsUseable@0x00628C20, 0x0055E212, 0x00562433, `static.txt`,
  run:2026-11-03-use-emu)
- [I] **Corrections.** Healing and mana potions do **not** run the group clear: kind 3 has no call of `STATE_GroupClear`
  (its only call in the use entries is `0x005BEE15`, in `ItemUseTimedState`, so kinds 6 and 9); stats/states B3 says
  "potions" (§ 9). `calc1` is not added per tick (Misc, § 9). (0x005BE3F0, 0x005BEE15)

- [I] **Draws over a whole use are not bounded.** The counts above (0 draws for kinds 4, 5, 7, 8, 1, keys; 2 for kind 3) hold
  only up to each entry's first callee. Whether a callee draws is open until Phase 2 (§ 8). (fn:sub_005BF240_ItemUse@0x005BF240, `rcg-summary.txt`)

## Leads used

No community source was compared; every claim is from the code. The doubling draw has no lead in `docs/sources.md`.

## Functions

| Address | Name | Role | Tag |
|---|---|---|---|
| `0x0054B1E0` | `sub_0054B1E0_Pkt20UseInvItem` | packet `0x20`, 13 bytes: guid, x, y | I |
| `0x0054B560` | `sub_0054B560_Pkt26UseBeltItem` | packet `0x26`, 13 bytes: guid, the mercenary flag | I |
| `0x0054B280` | `sub_0054B280_Pkt27ItemOnItem` | packet `0x27`, 9 bytes: target guid, used guid | I |
| `0x0054D430` | `sub_0054D430_Pkt61MercItem` | packet `0x61`, 3 bytes | I |
| `0x0054D230` | `sub_0054D230_MercGiveCursorItem` | the cursor item to the mercenary | I |
| `0x00549150`, `0x005492F0`, `0x00549220` | `sub_00549150_PktInvItemBad`, `sub_005492F0_PktBeltItemBad`, `sub_00549220_PktOwnedItemBad` | the handlers' item tests | I |
| `0x00548EF0` | `sub_00548EF0_PktPosFar` | the handlers' distance test | I |
| `0x0055E170` | `sub_0055E170_PlayerUseInvItem` | the inventory use and its consumption | I |
| `0x00562390` | `sub_00562390_PlayerUseBeltItem` | the belt use and its consumption | I |
| `0x00561ED0` | `sub_00561ED0_PlayerUseItemOnItem` | the item-on-item use and its consumption | I |
| `0x0055BF50` | `sub_0055BF50_InvClearUseMarks` | clears flag 4 on all inventory items | I |
| `0x0055E000` | `sub_0055E000_InvItemConsume` | message, then the removal | I |
| `0x00561E70` | `sub_00561E70_BeltItemConsume` | message, then the belt removal | I |
| `0x0055EDC0` | `sub_0055EDC0_BeltColumnShift` | closes the gap in a belt column | I |
| `0x0055E050` | `sub_0055E050_BookScrollSkill` | Books `+0x0C` (book) or `+0x08` (scroll), else −1 | I |
| `0x0055E0D0` | `sub_0055E0D0_SkillQtyDec` | the skill's quantity − 1 and its message | I |
| `0x005BE130`, `0x005BE230` | `sub_005BE130_ItemUseIdentifyTest`, `sub_005BE230_ItemUseIdentify` | kind 1 | I (map C) |
| `0x005BE180` | `sub_005BE180_InvHoldsItem` | the target-in-inventory walk | I (map C) |
| `0x005BE3F0` | `sub_005BE3F0_ItemUsePotion` | kind 3 | I (map C) |
| `0x005BE7B0` | `sub_005BE7B0_ItemUseStatPlain` | kind 4, no stock row | I (map C) |
| `0x005BEAC0` | `sub_005BEAC0_ItemUseRejuv` | kind 5 | I (map C) |
| `0x005BEF90` | `sub_005BEF90_ItemUseCure` | kind 6 | I |
| `0x005BF060` | `sub_005BF060_ItemUseElixir` | kind 8 | I (map C) |
| `0x005BF0C0` | `sub_005BF0C0_ItemUseCube` | kind 7 | I (map C) |
| `0x0062A5D0`, `0x0062A620` | `sub_0062A5D0_PotionLifeMul`, `sub_0062A620_PotionManaMul` | the class scales | I (map C) |
| `0x005C6870`, `0x005C5F10` | `sub_005C6870_GolemHealShare`, `sub_005C5F10_GolemHeal` | the Blood Golem's share | I (map C up to the heal) |
| `0x005678A0` | `sub_005678A0_InteractIsPlayer` | the interaction test the uses refuse on | I (map C) |
| `0x0055F140` | `sub_0055F140_KeyConsume` | one key used | I (map C) |
| `0x00562590` | `sub_00562590_ItemIdentify` | the identification | I |
| `0x005805D0`, `0x00571A10` | `sub_005805D0_UnitLifePct`, `sub_00571A10_MsgLifePct` | the life-percent message | I |
| `0x00628C20` | `sub_00628C20_ItemIsUseable` | `useable` getter | I |
| `0x00621ED0`, `0x006297A0`, `0x00629800` | `sub_00621ED0_ItemBeltByte`, `sub_006297A0_ItemDurWarning`, `sub_00629800_ItemQntWarning` | column getters | I |
| `0x0062BB20` | `sub_0062BB20_ItemSpellIcon` | Books `+0x02` or Misc `spellicon` | I |
| `0x0063C830` | `sub_0063C830_BeltBoxQuery` | client: reads `useable` and `belt` | I |

## 1. The requests

- [I] **`0x20`.** Length must be 13 (else 3). `sub_00549150_PktInvItemBad` (the item exists, mode 0, and `0x0063AD50`
  finds it with the player) and `sub_00548EF0_PktPosFar` (each axis of the player's position within 50 of the packet's x
  and y, as `u16`) come first; either's non-zero is returned. (0x0054B1E0, 0x00548EF0, 0x0054B222)
- [I] **`0x26`.** Length 13. The fields are the guid (`+1`) and a flag (`+5`); the position tested and passed is the
  player's own, so the distance test holds with any input. `sub_005492F0_PktBeltItemBad` wants mode 2. (0x0054B560)
- [I] **`0x27`.** Length 9. `+1` is the target and `+5` the used item; both must pass `sub_00549220_PktOwnedItemBad`.
  (0x0054B280, 0x00561ED0)
- [I] **`0x61`.** Length 3; expansion games only (`game+0x70`), else 3. With a cursor item that is not a quest item the
  mercenary path runs; the player must have no used skill and be alive, and the pet of type 7 alive. (0x0054D430)
- [I] A refusal flagged by the use function returns 3 from the handler; what the drain does with 3 is P1.3's. (0x0054B1E0)

## 2. The dispatch

[C] (ADR-0021) § Answer's rule. `ITEMS_UnitIsType(item, 18)` or `(item, 22)` selects the Books row by suffix word
`+0x3E`; the row's `+0x04` above 0 jumps past the Misc read, so a Books row wins over Misc `pSpell`. With a Books `+0x04`
≤ 0, or no row, Misc `pSpell` is read, the skill argument keeping `+0x0C` or −1. (0x005BF27C–0x005BF2D1, family
`dispatch`, 600 cases: 44 `test`, 226 at the `use` of 10 kinds, 330 refusals or empty slots.) Kinds 4 and 12..30 hold no stock
row; kind 4's `use` is an address in the table and the empty ones return 0.

[I] After the boundary: a test returning 0, or a use returning 0, clears the use marks (`sub_005BE1C0_InvClearUseMark`)
and sends message `0x7C`; a test's non-zero leaves them. **`ItemUse` returns 0 after any test**, and the use's own return
otherwise. Only kind 1 has a test, and it returns 1. (0x005BF320–0x005BF34C, 0x005BF38C–0x005BF3B6)

## 3. Consumption, in the callers

- [I] **`0x20`, in order:** clear use marks; find the item; refuse a cursor item; mode 0 and `useable` else flag; a book
  with stat 70 below 1 returns 0; `InteractIsPlayer` returns 0; `ItemUse(item, item, x, y)`. (0x0055E170–0x0055E25D)
- [I] **`ItemUse` non-zero, a book** with a skill and stat 70 above 0: stat 70 − 1, its messages,
  `SkillQtyDec`. No removal. **Otherwise** (a scroll, a potion): `SkillFindByOwner`; if one is found, its quantity − 1, and
  at 0 or below it is cleared from the right hand when it is there; then the removal. (0x0055E263–0x0055E2F0)
- [I] **`ItemUse` zero.** The four quest codes run here and **not** through `pSpell`: `ass` (state 9/5: +1 stat 5),
  `xyz` (state 20/5: +0x1400 stat 7), `tr2` (state 37/8 and not 37/7: the resistance bonus), `toa` (the stat reset). Each
  removes the item when it applies. Any other code returns 0 with nothing used; so a `useable` row with no kind does
  nothing, and so does a first identify. (0x0055E263 onward, 0x20737361, 0x207A7978, 0x20327274, 0x20616F74)
- [I] **`0x26`, in order:** clear marks; find; refuse a cursor item; mode 2 and `useable` else flag; `InteractIsPlayer`
  returns 0. With the packet's flag, a player user and an expansion game, the item must be of type 76, 81 or 80, else 0, and
  the pet of type 7, when there is one, becomes the user. Non-zero from `ItemUse`: the skill's quantity as above, then
  `BeltItemConsume` and `BeltColumnShift(x & 3)`, which moves each remaining item of that column down. The column's
  items stay at rows in their order. (0x00562390, 0x0056245B–0x0056249D, 0x0055EDC0)
- [I] **`0x27`** does not clear the marks before `ItemUse` (so flag 4 from the first request stands), and clears them after
  its consumption and on its refusals. A used item in the belt must be of type 22, else flag. A target of mode other than
  0 or 1 does not reach `ItemUse`: a used item in the belt is **removed anyway**, a book in the inventory loses a charge (floored at 0), and nothing is
  identified. A book of 0 charges refuses. Otherwise `ItemUse(used, target, 0, 0)`; non-zero uses one up: a belt item by
  `SkillQtyDec` and `BeltItemConsume`, a book by stat 70 − 1, an inventory scroll by the removal. Note the belt case does
  not shift the column here. (0x00561F60–0x005621F4)
- [I] **`0x61`** with a cursor item identified, without flag `0x100` and of type 76, 81 or 80: `ItemUse(item, item, 0, 0)`,
  then the cursor is consumed **whatever it returned**. The user is the mercenary (`EDX` from the function's `ECX`). (0x0054D3FD–0x0054D406, fn:sub_0055EEA0_CursorItemConsume@0x0055EEA0)

## 4. Kinds 3, 4, 5: the amount

```c
// fn:sub_005BE3F0_ItemUsePotion@0x005BE3F0, trimmed. Kind 4 omits the class scale and draws; kind 5 is § 4.
len = eval(rec.len); state = rec.state;             // blank offset 0xFFFFFFFF evaluates to 0
if (len > 0) {
    if (state < 1 || state >= nStates) return 0;
    L = FindStatListByState(user, state);
    if (L) rem = L.end - frame;                      // can be negative
}
for (k = 0; k < 3; k++) {
    s = rec.stat[k];
    if (s < 0 || s >= nISC) break;                   // kind 5 continues instead
    v = eval(rec.calc[k]);
    if (s == 26 || s == 74) v <<= 8;
    if (s is 8 or 26) { v = ManaMul(user, v); n = stat(user, 1); }
    if (s is 6 or 74) { v = LifeMul(user, v); n = stat(user, 3); }
    if (s in {6, 8, 26, 74} && n > 0) {              // draws even when v is 0
        r1 = RNG_RangeB(user+0x20, n);               // draw #1, user's seed
        r2 = RNG_Range (user+0x20, 100);             // draw #2, user's seed
        if ((int)r2 < (int)(r1 >> 1)) v *= 2;
    }
    v <<= isc[s].ValShift;
    if (v <= 0) continue;
    if ((s == 6 || s == 74) && user is player) v = GolemHealShare(user, v);
    if (len < 1) {                                   // instant: no stock row of kind 3
        if (isc[s].maxstat < nISC && stat(s) + v > stat(maxstat)) v = stat(maxstat) - stat(s);
        UnitAddStat(user, s, v, 0);
    } else {
        end = frame + rem + len;
        if (!L) L = new list(end) ... ;              // after, [I]: § 5, 0x005BE607
        SetEnd(L, end);                              // bit 2 when end > 0
        old = L.base(s);
        if (k == 0) QueueEvent(user, 12, end);
        if (len + rem > 0) SetStat(L, s, (old * rem + v) / (len + rem), 0);
    }
}
```

- [C] (ADR-0021) The map above up to the first of `UnitAddStat` (`0x005BE5C7`), `STATLIST_Alloc` (`0x005BE607`, args
  `game+0x1C, 2, end, user type, user id`), `UnitQueueEvent` (`0x005BE6B3`, args `12, end, 0, 0`), `STATLIST_SetStat`
  (`0x005BE6D4`), the golem's heal, or the return (families `stat3`, `stat4`, `stat5`; kinds 4 and 5 at their own sites in
  `SITES`). What each case saw: the arguments, the list's end and bit 2, the seed. The rate's division is only reachable as a
  boundary for a slot after the first, because slot 0's event queue comes first; the cases reach it by a slot 0 whose
  amount is 0. So the **stock** path's rate (slot 0) is the same instructions after the queue call, not itself observed:
  `[I]` for slot 0 until Phase 2. After, `[I]`: every effect of the callees.
- [C] (ADR-0021) What separates (run:2026-11-03-use-emu, fn:sub_005BE3F0_ItemUsePotion@0x005BE3F0): control `draw1` (one draw) and `nodraw` fail 905 cases each; `half` (`r2 < r1`) 51;
  `floordiv` 120; `nocap` 207; `pctflat` 252; `no100` 28; `sar` 20 in `classmul`. (`check.txt`)
- [C] **The class scales** return exactly as stated for all 7 classes, other classes and types, odd and negative
  amounts, and a null unit (`2v` life, `v` mana); 800 cases, no boundary. The non-player rule is `2v` for life and `v` for
  mana. (family `classmul`, run:2026-11-03-use-emu, fn:sub_0062A5D0_PotionLifeMul@0x0062A5D0, fn:sub_0062A620_PotionManaMul@0x0062A620)
- [I] **The draw's chance** for `n`: `Σ min(100, r >> 1) / (100 n)` over `r < n`, from `tools/item_inventory.py`
  `double_chance`: 2.0 % at 10, 5.76 % at 25, 12.0 % at 50, 24.5 % at 100, 49.5 % at 200, 79.8 % at 500. The stats read are
  `STATS_GetUnitStat(user, 3 or 1, 0)`; on a non-player user they are whatever its list holds, usually none, so no draw.
  (0x005BE514–0x005BE53B)
- [I] **Stock totals** (`python3 -I tools/item_inventory.py stock`): `hp1` 30 → 7 680 stored units for a Sorceress, 11 520 for
  an Amazon, 15 360 for a Barbarian, i.e. 30, 45 or 60 life. The stored rate truncates: `hp3` (100, `len` 171) gives
  25 600 / 171 = 149 per frame, 25 479 over the 171 frames, 99 life and a remainder. Stock `ValShift` of stats 26 and 74 is
  blank, so 0. (tools/item_inventory.py, fn:sub_005BE3F0_ItemUsePotion@0x005BE3F0)
- [C] (ADR-0021) **Kind 5 (§ 4).** The slot is skipped, not ended, for a bad stat, a stat with no `maxstat`, or `calc ≤ 0`.
  `MulDiv(max, calc, 100)` is the `sub_00483360_MulDiv` of three branches, so above `0x100000` it may be `(max / 100) ·
  calc`; at exactly 100 the maximum is taken instead (`no100` fails 28 cases). The cap uses the same `max`, read
  raw by `STATS_GetUnitStat` and not `UnitGetMaxHp`. The stored stats are `<< 8` and so is `max`: no shift is applied. A
  timed path exists with the same list code; no stock row has `len` here. (0x005BEBC1–0x005BEC3E)
- [I] **After the loop, when stat 6 got an amount, on a player** (kinds 3, 4: only when `|stat 352 − pct| > 4`; kind 5:
  always): `sub_00571A10_MsgLifePct` and stat 352 set to `sub_005805D0_UnitLifePct` (`life · 128 / max`, 128 at full). No
  stock potion of kind 3 names stat 6; both rejuvenations do. (0x005BE6F0–0x005BE738, 0x005BED55)

## 5. Timed list, after the boundary

[I] A fresh list: `STATLIST_Alloc(game+0x1C, 2, end, type, id)`, its state, `STATE_Set(user, state, 1)`; for a non-player
user `UNIT_CancelEvents(3, 0)` and event 3 at `frame + 1`; the remove callback `0x0056E900`, `STATLIST_LinkToUnit(user,
list, 1)`. Then `SetEnd`, and the rest of the loop as above with `rem = 0`, so the rate is `v / len`. (0x005BE5E8–0x005BE673)

[I] **Repeat drinking extends and blends, it does not stack lists:** a second potion of the same state before the first
ends uses the same list, end `now + rem + len`, and rate `(old · rem + v) / (len + rem)`, so the undelivered part of the
first is carried and spread over the longer window. (0x005BE678–0x005BE6CF)

## 6. The other kinds

- [C] (ADR-0021) **Kind 1.** § Answer. The test's message is `0x53D220(icon, 0, 1, skill)` after the client lookup
  `0x005531C0` (the boundary, site `0x005BE165`); a book or scroll with no Books row returns 1 with flag 4 set and no
  message. `InteractIsPlayer` (`0x005678A0`) tests `+0x6C` set, `+0x68` type 0, and the unit found. (families `idtest` 120,
  `idfn` 300) After, `[I]`: `ItemIdentify` sets flag `0x10` through `ItemIdentifyAttach`, sets flag 1, clears flag
  `0x4000`, then refreshes and closes the event (0x00562590); it fatals on flag `0x100000`.
- [I] **Kind 2.** `ITEMUSE_TownPortal`, player only; refused in town and on level 136, as quests/travel G1. (0x005BE290)
- [I] **Kind 6.** For each of `cstate1`, `cstate2` (`+0x9A`) that is a valid state: the unit's list of that state unlinked
  and freed, the state cleared when set; then `ItemUseTimedState`. It returns 1 when any named state was processed or the
  state applied. (fn:sub_005BEF90_ItemUseCure@0x005BEF90)
- [I] **Kinds 6, 9.** `sub_005BEDA0_ItemUseTimedState` as data/0005, and **only these** run `STATE_GroupClear`. Here `calc`
  goes to the list as is, so `calc` is the value held for `len` frames. (0x005BEE15)
- [C] (ADR-0021) **Kind 7.** § Answer; busy means an interaction, a cursor item or player data `+0x4C`. Object class
  `0x10B` is the only interaction it replaces. (family `cube` 300) After, `[I]`: messages `0x11`, `0x15`, and
  `0x0055FA40`, read as far as its walk of page-0 items. The return is 0, so `PlayerUseInvItem` falls to § 3's quest codes
  and returns 0: the cube stays.
- [C] (ADR-0021) **Kind 8.** § Answer. (family `elix` 200) `elx` carries `stat1` `experience`, `calc1` 5 in Misc: this
  code reads neither. (fn:sub_005BF060_ItemUseElixir@0x005BF060, run:2026-11-03-use-emu)
- [I] **Kinds 10, 11** cast skill 47 at level 1; no stock row, skills/0015. (0x005BF170, 0x005BF1F0)
- [C] (ADR-0021) **Blood Golem.** For a positive life amount on a player: pet type 3, class `0x122`; the row's MonStats
  `+0x170` names a Skills row, whose `+0x15C` is a percent. `share = v · p / 100` truncated goes to `GolemHeal`, up to the
  golem's maximum, and the player keeps `v − returned` (after, `[I]`). No such pet or another class returns `v`.
  (family `golem` 300, and 27 + 11 cases of `stat3`, `stat5`, run:2026-11-03-use-emu, fn:sub_005BE3F0_ItemUsePotion@0x005BE3F0) [I] `v = 0` sets the golem to full; no use entry sends it.

## 7. What the columns gate

`[C]` (run:2026-11-03-use-emu, `static.txt`) The counts are `static.txt`'s, an image-wide scan of `u8` reads at the offset plus the getter calls. Reading a
`0x4xxxxx` address as client code is the project's convention, `[I]` per site.

| Column | Readers | Gate |
|---|---|---|
| `useable` `+0x11D` | 10 `u8` matches: `0x00628C5B` and `0x0063C8B1` on an item record; `0x00498A5B`, `0x004AF989`, `0x004AFAD2` and the five at `0x006910EA`..`0x0069BB63` not classified; getter `0x00628C20` has 5 calls: `0x00487844`, `0x00499229`, `0x00499331`, and the server's `0x0055E212`, `0x00562433` | `[I]` Both use requests require it. Its absence sets the refuse flag, so the handler returns 3. It does not select a kind |
| `belt` `+0x130` | 9: `0x00543390` is on a 0x134-byte row of `DataTables+0xA90` reached from MonStats `+0x18`, not this table; six at `0x004C56A7`..`0x004CDAAF` not classified; `0x00621F12` getter (3 calls: `0x0049907F`, `0x0056091B`, `0x0063C6A3`), `0x0063C8B9` | `[I]` **No use.** `0x0056091B` passes it to `0x00660CB0`, the Belts record path (P1.2). `sub_0063C830_BeltBoxQuery` tests `useable` and `belt` both 1 with size 1 × 1, called only from `0x004979AD`, so a client rule on this reading |
| `autobelt` `+0x131` | 8, the server's `0x00628BEA`, `0x0063C731` | `[I]` P1.2 (placement), player/0001 |
| `durwarning` `+0x135` | 5, all `0x4xxxxx` but the getter `0x006297E9`, which has 0 direct calls | `[I]` no server gate found among direct calls; indirect callers unfollowed; the column is 0 in all rows |
| `qntwarning` `+0x136` | 3: `0x004CD8D5`, `0x00629849` (getter, 1 call `0x00497EAF`), and `0x0059FD01`, which is in `sub_0059FA30_MissileCreate` on a Missiles record, not this table | `[I]` no server gate found among direct calls; indirect callers unfollowed |

Scope: indirect calls and table pointers to the getters are not followed; the scan is direct calls.

## 8. Draws per seed

| Use | Draws | Seed | Tag |
|---|---|---|---|
| Kind 3 `hp1..5`, `mp1..5` | 2 per stat with an amount slot when vitality or energy > 0, else 0: one slot on all ten | the user's (`unit+0x20`) | [C] (ADR-0021) before the boundary (fn:sub_005BE3F0_ItemUsePotion@0x005BE3F0, run:2026-11-03-use-emu) |
| Kind 4 | 0 | | [C] (ADR-0021) before the boundary, no stock row |
| Kind 5 | 0 | | [C] (ADR-0021) before the boundary (fn:sub_005BEAC0_ItemUseRejuv@0x005BEAC0, run:2026-11-03-use-emu) |
| Kind 8 | 0 | | [C] (ADR-0021) before the boundary (fn:sub_005BF060_ItemUseElixir@0x005BF060, run:2026-11-03-use-emu) |
| Kind 1 test, use | 0 | | [C] (ADR-0021) before the boundary (fn:sub_005BE130_ItemUseIdentifyTest@0x005BE130, fn:sub_005BE230_ItemUseIdentify@0x005BE230, run:2026-11-03-use-emu) |
| Kind 7 | 0 | | [C] (ADR-0021) before the boundary (fn:sub_005BF0C0_ItemUseCube@0x005BF0C0, run:2026-11-03-use-emu) |
| Key | 0 | | [C] (ADR-0021) before the boundary (fn:sub_0055F140_KeyConsume@0x0055F140, run:2026-11-03-use-emu) |
| Kinds 2, 6, 9 | 0 in the entry's own body | | [I] direct calls (fn:sub_005BEDA0_ItemUseTimedState@0x005BEDA0, `rcg-summary.txt`) |

[I] **No bound past the boundaries.** `rcg-summary.txt` gives, for `0x0055E000`, `0x0055E0D0`, `0x0055F140`, `0x00561E70`,
`0x00562590` and the entries 1, 2, 5, 6, 7, 9, 2 097..2 115 functions with 118 holding a seed step (119 under entry 3: its
own), indirect calls unfollowed (112 in the three whose summary lines were read), and the steps at depth 5 or more,
among them the room population and level creation, which no reading here connects to a use. The narrow closures: test
`0x005BE130` 559 functions and 0 with a step, entry 8 `0x005BF060` 574 and 0, `0x0055EDC0` 636 and 0. So "no draw in the whole use"
stays open; Phase 2's seed comparison settles it.

## 9. Corrections

- [I] stats/states B3 "**Potions** … run the group clear": only kinds 6 and 9 (`yps`, `wms`, `vps`, `hrb`). The nine call
  sites of `0x0056C740` hold `0x005BEE15` as the only one in `0x005BE130..0x005BF3D0`. Spec-writer entry filed.
- [I] Misc § Timed states "the amounts `calc1`… added to life at each tick": `calc1` is a total, scaled, and divided by
  `len` into the frame rate. The tick's own reading stands. Archivist entry filed. (fn:sub_005BE3F0_ItemUsePotion@0x005BE3F0, fn:sub_00580610_LifeRegenTick@0x00580610)
- [I] Misc's `[L]` flat-or-percent is answered: kind 5 percent of the maximum, kind 8 reads neither. (fn:sub_005BEAC0_ItemUseRejuv@0x005BEAC0, fn:sub_005BF060_ItemUseElixir@0x005BF060)
- [I] data/0005's reading of `ItemUseTimedState` stands for what it covers; the note "the potions" there came from the
  same table row. 0x005BE430 and 0x005BE4D9 were the `len` and `calc` reads of a different function. (0x005BE3F0)

## 10. Harness cases for Phase 2

Each with the user's seed logged before and after, stats 1, 3, 6, 7, 8, 9, 26, 74, the list's end, and the expected
values from `tools/item_inventory.py`.

1. `hp1` from the belt, Sorceress, vitality > 0, life below max: 2 draws, frame rate, end, event 12; **slot 0's rate**.
2. `hp1` for an Amazon and a Barbarian: 1.5 and 2 scales. Then a seed that doubles and one that does not (replays).
3. `mp1` for Sorceress and Barbarian: the mana scales and energy as `n`.
4. A second `hp1` during the first: the blend, one list, the rounding.
5. `hp5` at full life: the amount is still applied, not refused. `ret` and consumption.
6. `rvs`, `rvl` at low life and mana: percent, cap, immediate; stat 352 and the message; no draw.
7. `rvl` on a character with maximum life above 4 096, with `rvs`: MulDiv's large branch, 100's exact maximum.
8. `yps`, `wms`, `vps`, `hrb`: the group clear; `cstate1` cleared; a healing potion beside them not cleared.
9. Blood Golem out: `hp1` and `rvs` split; golem's life.
10. `isc` from the inventory: the first request (flag 4, message, nothing used), the second on an unidentified item
    (used up, identified); then on an identified item (refused, marks cleared, kept).
11. `ibk` with 0 charges, with 1: refusal, charge down; the book stays at 0.
12. `isc` from the belt on an item: the column **not** shifted (§ 3); and a `tsc` from the belt: shifted.
13. `tsc`, `tbk` outside town; in town (the refusal); the seed.
14. `box`: opens, stays; while busy at the stash.
15. A `useable` row with no kind (`hpo`, `rps` if placeable): nothing happens, nothing is used.
16. A `key` on a locked chest; a stack of 2 and of 1; none; an Assassin with none; a locked door.
17. Potion to the mercenary: from the belt with the flag (non-potion refused), from the cursor (`0x61`): merc's seed, `2v`.
18. A use while trading (interaction with a player): refused.
19. `elx` if an item can be placed: the added stat. No stock row spawns it in any normal path, read to P1.3 or left.
20. Quest codes `ass`, `xyz`, `tr2`, `toa`: each state set and clear, consumed or not.

## Data touched

tbl:Misc.txt:pSpell, tbl:Misc.txt:useable, tbl:Misc.txt:belt, tbl:Misc.txt:state, tbl:Misc.txt:cstate1, tbl:Misc.txt:cstate2,
tbl:Misc.txt:len, tbl:Misc.txt:stat1, tbl:Misc.txt:calc1, tbl:Misc.txt:spellicon, tbl:ItemStatCost.txt:ValShift,
tbl:ItemStatCost.txt:maxstat, tbl:Books.txt:pSpell, tbl:Books.txt:BookSkill, tbl:Books.txt:ScrollSkill.

## Dead ends

- `0x0054B9F0` as the handler of `0x20`: a 12-byte stride; `g_SrvPacketTable` is 8-byte entries.
- `0x2079656B` (the code `key `) has no immediate: the key is found by type 41.

## Open questions

- `[L]` Slot 0's rate on the stock path (the queue call precedes it): Phase 2 case 1 resolves it.
- `[L]` Whether any draw occurs in a whole use past the boundaries (§ 8): Phase 2's seed comparison.
- `[L]` The case of the object mode switch at `0x00581DBC`, what it is for and whether a class test precedes it: read
  the door path, or Phase 2 case 16. The Assassin's skip is read at `0x00585FB1` for the chest only.
- `[L]` `useable`'s client readers and `belt`'s Belts path are P1.2's.
- `[L]` `elx` reaches a player how; its file index and stat 71 have no writer named here.
