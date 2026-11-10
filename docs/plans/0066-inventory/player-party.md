# Plan 0066 inventory: player/party

- **Spec:** [player/party](../../specs/player/party.md), read at `main` `b5999f5e`.
- **Front matter `I`:** 26; the *Count* column sums to 26.
- Classes, batches and conventions as in [the inventory README](README.md#conventions).

| # | Line | Section | Claim (excerpt) | Anchor | Class | Route or reason | Batch | Count |
|---|---|---|---|---|---|---|---|---|
| 1 | 41 | Entry points | A unit is killed: the gate, then the award; … | `fn:sub_005A4EF0_KillExpGate@0x005A4EF0` | b | a breakpoint line at `KillExpGate` and its award call in a one-client kill session (no logger has it) | H7a | 1 |
| 2 | 81 | Algorithm | §§ A to D make no RNG draw: the direct-call walk from XP_OnMonsterKill and the … | `fn:XP_OnMonsterKill@0x0057E990` | c | a kept call-graph scan with a second tool (`rngcallgraph` plus an r2 LCG scan) from `XP_OnMonsterKill` and the collector | S7a | 1 |
| 3 | 92 | A. Who is credited | What holds the list in play, and what the gate's flag bit 26 of + … | `0x005A4EFE` | d-none | a scope note: says what the code does not settle | – | 1 |
| 4 | 94 | A. Who is credited | Whether play reaches that is not read. | `0x0057CD28` | d-none | a scope note (not read); raising it is new reading, not a corroboration | – | 1 |
| 5 | 101 | B. What a party is | The writers of the list, what makes two players one party, and whether a list … | `0x005408CB` | d-none | a scope note (not read) | – | 1 |
| 6 | 128 | C. Who shares | What follows that call is the fatal path, not run, and whether a list can … | `0x0057E671` | d-none | a ninth member needs a list past 8; no stock game holds one | – | 1 |
| 7 | 144 | D. How much | What the origin and the n = 1 credit lead to in play: a partied … | `0x0057E6FB` | d-2c | a partied owner and a second member near the victim | – | 1 |
| 8 | 146 | D. How much | A negative total gives each member an input ≤ 0 through the float steps below, … | `0x0057E754` | d-2c | a negative total needs the n = 8 wrap, a full party; and the float steps are x87 | – | 1 |
| 9 | 148 | D. How much | For n ≥ 3 those float steps are the same instructions and agree in every … | `0x0057E754` | d-2c | n ≥ 3 partied members | – | 1 |
| 10 | 176 | E. Every player-count reader, with its input | Game type 1 also takes it, and other types do not; the set of states … | `fn:sub_00535790_PlayerCount@0x00535790` | a-run | a one-client TCP/IP host (the H1b recipe) with `/players` set, `g_PlayersOverride` read at `PlayerCount` | H7a | 1 |
| 11 | 177 | E. Every player-count reader, with its input | The client's chat parser takes /players only in client modes 0, 1, 6 and 8 … | `fn:sub_0047C420_ChatInputParse@0x0047C420` | b | pilot types `/players 0` and `/players 9` in a single-player game; read `g_PlayersOverride` (new pilot step) | H7a | 1 |
| 12 | 185 | E. Every player-count reader, with its input | MonAttackStats damage — expansion, Nightmare and Hell: + value × b ÷ … | `fn:sub_005A4F50_MonAttackStats@0x005A4F50` | a-run | `combat.gdb` on a Hell expansion session at `/players 8`: monster damage against the rule | H7a | 1 |
| 13 | 187 | E. Every player-count reader, with its input | NoDrop's cap — for the cap's effect | `0x0055A926` | d-2c | the cap acts only when the party count exceeds the frozen count: a second player joins later | – | 1 |
| 14 | 188 | E. Every player-count reader, with its input | four think functions — nothing by the count; a changed /players has no … | `0x005E8D6B` | c | a scan of the four thinks' reads of the bonus block with a second tool: only word `+0x0C` | S7a | 1 |
| 15 | 190 | E. Every player-count reader, with its input | NoDrop's party count — the party above | `0x0055A8E4` | d-none | a clamp at 8 that a party of at most 8 never reaches | – | 1 |
| 16 | 191 | E. Every player-count reader, with its input | gold pickup — a split by the party count; not run; no … | `fn:sub_00540900_PartyGoldShare@0x00540900` | d-2c | a split needs a party | – | 1 |
| 17 | 192 | E. Every player-count reader, with its input | quest credit — the same bits to each member with bits 0 … | `fn:sub_00540510_PartyForEach@0x00540510` | d-2c | the shape needs two partied members in different acts | – | 1 |
| 18 | 193 | E. Every player-count reader, with its input | the Ancients' grant — who gets the grant | `fn:sub_0058C6D0_A5Q5_PartyExpGrant@0x0058C6D0` | d-2c | the grant's party branch needs partied members | – | 1 |
| 19 | 194 | E. Every player-count reader, with its input | the forge's n, Baal's and the chests' loops — per-player counts, not PlayerCount | `fn:sub_005537D0_GameForEachUnit@0x005537D0` | d-2c | a per-player count of one can't separate it from `PlayerCount` | – | 1 |
| 20 | 203 | E. Every player-count reader, with its input | PlayerCount has 2 direct references: TC_ResolveDrops | `0x0055A8F4` | c | an exhaustive xref scan with a second tool (r2 `axt`) on the three names | S7a | 1 |
| 21 | 204 | E. Every player-count reader, with its input | … the new count. So a change reaches the next creation and the next drop's PlayerCount. | `0x0055A8F4` | a-run | `tc-drops.gdb` with a `/players` change between two kills: the drop's `PlayerCount` read | H7a | 1 |
| 22 | 205 | E. Every player-count reader, with its input | The four: sub_005E8810_AiDiabloDecide, sub_005FC450_AiBaalDecideRanged, sub_005F0B00_AiCorruptRogue and sub_005E9750_AiDiabloDecideUnref, which has no reference. All four read only … | `0x005f0b00` | c | as row 14 | S7a | 1 |
| 23 | 217 | Worked example | n = 3, the float steps — inputs 84, 56, 28 (tools/player.py xp_share_inputs) | `0x0057E754` | d-2c | n = 3 partied members; the float steps are x87, out of emulation's evidence | – | 1 |
| 24 | 218 | Worked example | n = 8, the wrap — the total and the return for an input ≤ … | `0x0057E754` | d-2c | n = 8 partied members (the wrap); x87 sign | – | 1 |
| 25 | 224 | Reimplementation notes | … owner alone, and a dead killer can be paid while the living member is not. | `0x0057E6FB` | d-2c | a partied far owner and a member near the victim | – | 1 |
| 26 | 226 | Reimplementation notes | … to the call Past the call, and whether a list can hold nine, is unread. | `0x0057E671` | d-none | a ninth member never exists in a stock game | – | 1 |

**Totals by class:** a-run 3, b 2, c 4, d-2c 11, d-none 6 (sum 26).
