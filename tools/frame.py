#!/usr/bin/env python3
"""The server-frame order model over the kept frame-stamped logs (plan 0055 Phase 2a).

    python3 -I tools/frame.py reach [--exe EXE] [ADDR ...]   the pass set of every hook of KINDS (or of the addresses
                                                             given): the direct-call reach up to a pass root
    python3 -I tools/frame.py kinds                          the kind-to-pass map, one line per logger family and kind
    python3 -I tools/frame.py check [--exe EXE] [--out DIR] <logs-root> [LOG ...]
                                                             the order and seed check over the corpus logs (the
                                                             frame-stamped, run-attributed rows of the Phase 0 index
                                                             workspace/logs/frame-corpus/frame-corpus-logs.tsv, or the
                                                             LOGs given, relative to <logs-root>)
    python3 -I tools/frame.py rechain <logs-root> GAPS ...   the caster resyncs a `tools/skills.py check --gaps` file
                                                             lists, walked again over every logged seed observation
                                                             of the unit between the two events, in model order

The frame (docs/findings/frame/0001 § 2, 0002 §§ 1-2, 0003 § 1). One stamp N (`Game+0xA8` as the loggers read it,
`fr`, or `frame` in the combat `g` block) covers GameTick(N) and the message drain after it: `GameTick` increments
`Game+0xA8` before its first pass, and the drain of a host-loop pass runs before `ServerGamesFrame`, so a packet
handled after frame N's tick reads N and acts before frame N+1 (frame/0001 § 5). The passes, in rank order:

    1 ActsClockPass  2 GameFpsStats  3 NewRoomsUpdate
    4..13 GameRunUnitEvents: missiles every-frame, missiles slot, players every-frame, players slot, monsters
          every-frame, monsters slot, objects every-frame, objects slot, items every-frame, items slot
    14 ClientsRoomSync  15 ActUnitsFrameReset  16 ActsRoomRemovalsClear  17 QUESTS_TimersRun (frame % 20)
    18 RoomsDeactivate (frame % 12)  19 the unload tick (frame % 11)  20 ExpirySweepTick  21 the drain (after the tick)

The kind-to-pass map (KINDS). Each logged kind has a rule:
  reach H      the pass set of the hooked function H by its direct callers (`call`/`jmp rel32`, objdump), walked up to
               a pass root: GameTick's passes, the five event runners (called once per walk pair), the event tables
               of the four types with a table (an entry runs in its type's two walks), MissileDoFrame (the missile
               runner's only dispatch), the drain and its dispatchers, the packet table's handlers. A function with
               no direct caller that is no root (a pointer-reached function: a skill, mode, AI, missile or quest
               callback) leaves the set open; an open set places nothing (the event is not compared).
  ra F H       as reach, from the function holding the event's own return address (field F) when its reach closes,
               else from H.
  site S       a fixed pass set read from one call site (the dispatch calls of the slot branches).
  ph           anim's EF line carries the runner's phase at the call (`ph`, the logger's breakpoints at the ten walk
               calls of GameRunUnitEvents): phase k in 1..10 is walk k (rank 3 + k); 0 and 11 are outside the walks.
  type         by the event's unit type, one hook per type (combat RGN, stats AU, h6b RPE).
  skip         a logger's own bookkeeping line (a window, a dump, a table header): not a game event.
A pass set narrowed by the unit type: where the roots are event tables of several types, the event's own unit type
keeps its type's walks. Nested events take their caller's pass: an event logged between the begin and end lines of a
pair whose set is closed has its set intersected with the pair's (an empty intersection is a mismatch).

`check` per log, segmented where the stamp falls (a new game): for every frame with two or more events, the logged
order against the model's (a greedy placement of each placed event at the lowest rank of its set not below the last
placed one; an event with no such rank is a mismatch), the separating pairs (two placed events whose sets do not
overlap: the reverse order would fail), the same frames under four control orders, the slot-list order of anim's
PDS/MDS dispatches against their records' queue order (SCH and CQ lines; oldest queued first, frame/0002 § 2.1), the
every-frame order of skills' MF0 lines against their missiles' creation (newest first, § 2.2), the cross-type
every-frame queues of anim's EF lines (a record queued in an earlier walk of the frame than its type's every-frame
walk: P1.2 review ruling 1), and for every pair of events on one seed in one frame, the hand-off from the first to
the second in model order: handed (the first's exit is the second's entry), stepped k (k draws unlogged between, k
<= 4096), reversed (the second's value lies before the first's on the stream: an order mismatch) or off (neither
within 4096 steps). Writes check.txt and per-log rows (frame-check-logs.tsv) under --out.
Stdlib and objdump. Read-only on the logs.
"""
import argparse
import bisect
import collections
import csv
import hashlib
import json
import os
import re
import struct
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import frame_corpus  # noqa: E402

EXE = os.path.join(ROOT, "workspace", "install", "app", "game.exe")
INDEX = os.path.join(ROOT, "workspace", "logs", "frame-corpus", "frame-corpus-logs.tsv")
BASE = 0x400000

PASS_NAMES = {1: "clock", 2: "fps", 3: "rooms", 4: "mis-ef", 5: "mis-slot", 6: "plr-ef", 7: "plr-slot",
              8: "mon-ef", 9: "mon-slot", 10: "obj-ef", 11: "obj-slot", 12: "item-ef", 13: "item-slot",
              14: "roomsync", 15: "reset", 16: "removals", 17: "quests", 18: "deact", 19: "unload", 20: "sweep",
              21: "drain"}
ALL = frozenset(PASS_NAMES)
# unit type -> its (every-frame, slot) walk ranks; g_UnitTypeEventList 0x006E0B9C: player 0, monster 1, object 3,
# missile 2, item 4, and the walks run missiles, players, monsters, objects, items (frame/0002 § 1)
TYPE_WALKS = {0: (6, 7), 1: (8, 9), 2: (10, 11), 3: (4, 5), 4: (12, 13)}
WALK_TYPE = {r: t for t, ws in TYPE_WALKS.items() for r in ws}

# pass roots: address -> (rank set, unit type or None, name)
PASS_FUNCS = ((0x0052D7B0, 1, "ActsClockPass"), (0x0052D720, 2, "GameFpsStats"), (0x0052D160, 3, "NewRoomsUpdate"),
              (0x0052D440, 14, "ClientsRoomSync"), (0x0053B000, 15, "ActUnitsFrameReset"),
              (0x0053A820, 16, "ActsRoomRemovalsClear"), (0x00543E10, 17, "QUESTS_TimersRun"),
              (0x0052D240, 18, "RoomsDeactivate"), (0x0061AA20, 19, "ActLevelsUnloadTickWrap"),
              (0x0052D310, 20, "ExpirySweepTick"))
RUNNERS = ((0x00541240, 3, "MissileEventsRun"), (0x00540F60, 0, "PlayerEventsRun"), (0x00541060, 1, "MonEventsRun"),
           (0x00541160, 2, "ObjEventsRun"), (0x00541320, 4, "ItemEventsRun"))
DRAIN = ((0x0052CFE0, "SrvDrainMessages"), (0x0054D750, "SrvPacketDispatch"), (0x0053F100, "SrvClientMsgDispatch"),
         (0x0052CC20, "SrvHostMessage"), (0x0053F3D0, "SrvProcessClientMessage"))
EVENT_TABLES = ((0x006E1810, 0, "g_PlayerEventFuncs"), (0x006E2490, 1, "g_MonEventFuncs"),
                (0x006E19B0, 2, "g_ObjEventFns"), (0x006E117C, 4, "g_ItemEventFuncs"))
MISSILE_DO = (0x005ADBB0, "MissileDoFrame")
PACKET_TABLE = 0x006E0D18   # g_SrvPacketTable, 8-byte entries {handler, flag}, opcodes 0..0x66 (items/0008)

# ---------------------------------------------------------------------------------------------- the kind map
# family -> kind -> (rule, args, anchor). Begin lines of pairs only (an end line folds into its begin's event).
R, RA, SITE, PH, TYPE, SKIP = "reach", "ra", "site", "ph", "type", "skip"
KINDS = {
    "anim": {
        "PDS": (SITE, {7}, "0x00540FC4 PlayerEventDispatch call in PlayerEventsRun's slot branch (mode test 0x00540F63)"),
        "MDS": (SITE, {9}, "0x005410C4 MonEventDispatch call in MonEventsRun's slot branch (mode test 0x00541063)"),
        "EF": (PH, None, "SUNIT_ModeEveryFrame 0x00553F00; ph from the breakpoints at 0x005414F6..0x00541589, 0x0054158E"),
        "OEV": (R, [0x00581490], "sub_00581490_ObjEvOperateEnd, g_ObjEventFns[1]"),
        "SR": (RA, ("ra", [0x00623F50]), "UNIT_AnimSetRate 0x00623F50, the call's return address"),
        "MSET": (RA, ("ra", [0x00624690]), "UNIT_SetMode 0x00624690, the call's return address"),
        "CAN": (RA, ("ra", [0x00540E60]), "UNIT_CancelEvents 0x00540E60, the call's return address"),
        "CQ": (RA, ("ra", [0x005417D0]), "UnitQueueEvent 0x005417D0 from the skill catalogue, the return address"),
        "SCH": (R, [0x005539B0], "SUNIT_ScheduleModeEvents 0x005539B0"),
        "RSC": (R, [0x00553B10, 0x00553C70, 0x00553DC0], "the catalogue reschedules"),
        "OA0": (R, [0x00624390], "UNIT_AnimInit 0x00624390"),
        "OQ": (R, [0x00580000], "the object code's UnitQueueEvent sites (0x00580000..0x0058FFFF)"),
        "FREE": (R, [0x00555600], "UnitFree 0x00555600"),
        "PS0": (R, [0x00650840], "sub_00650840_PathStep (site 0x00650899)"),
        "CT": (R, [0x00650150], "sub_00650150_PathStepCollide (site 0x00650215)"),
        "AD0": (R, [0x00623E00], "UNIT_AnimAdvance 0x00623E00"),
        "DR0": (R, [0x0057F240], "sub_0057F240_RunStaminaDrain"),
        "GR0": (R, [0x0057CB00], "sub_0057CB00_GetHitRoll"),
        "GH": (R, [0x0057CEE0], "COMBAT_GetHit 0x0057CEE0"),
        "PA0": (R, [0x0057EEC0], "sub_0057EEC0_PlayerModeAllowed"),
        "PL0": (R, [0x0057EDD0], "sub_0057EDD0_PlrModeLeaveOk"),
        "PLE": (R, [0x0057EDD0], "inside PlrModeLeaveOk (0x0057ED7A, 0x0057EDBC)"),
        "KBE": (R, [0x005A8520], "sub_005A8520_MonKnockbackEnd"),
        "DLY": (R, [0x0056EF90], "SKILLS_SetDelayState 0x0056EF90"),
        "WIN": (SKIP, None, "the logger's monster window opened (at an MSET)"),
        "WINX": (SKIP, None, "the logger's monster window closed"),
    },
    "skills": {
        "SST0": (RA, ("ret", [0x0056F640]), "SKILLS_SrvStart 0x0056F640, the return address"),
        "SDO0": (RA, ("ret", [0x0056F7F0]), "SKILLS_SrvDo 0x0056F7F0, the return address"),
        "CU0": (RA, ("ret", [0x00647960]), "SKILLS_CanUse 0x00647960 from the request handlers; cl:1 the client's"),
        "MC0": (R, [0x0059FA30], "sub_0059FA30_MissileCreate"),
        "MF0": (R, [0x005ADBB0], "sub_005ADBB0_MissileDoFrame (site 0x005ADC97)"),
        "MH0": (R, [0x005ADF10], "MISSILE_HitUnit 0x005ADF10"),
        "EVH": (R, [0x005C0C40], "UNIT_DispatchEvent's handler call 0x005C0C8E"),
        "MAS0": (R, [0x005A4F50], "sub_005A4F50_MonAttackStats"),
        "SP0": (R, [0x0056D940], "sub_0056D940_SpawnOwnedMonster"),
        "PF0": (R, [0x005D5220], "COMBAT_PrgFinisher 0x005D5220"),
        "DLY": (R, [0x0056EF90], "SKILLS_SetDelayState 0x0056EF90"),
        "STA": (R, [0x0056E970], "STATE_ApplyTimed 0x0056E970"),
    },
    "combat": {
        "EV0": (RA, ("ret", [0x0057EC10]), "COMBAT_MeleeHitTest 0x0057EC10, the return address"),
        "MS0": (R, [0x005AD730], "MISSILE_ApplyDamage 0x005AD730 (site 0x005AD757)"),
        "MAS0": (R, [0x005A4F50], "sub_005A4F50_MonAttackStats"),
        "AD0": (R, [0x0057C6C0], "COMBAT_ApplyDamage 0x0057C6C0"),
        "RGN": (TYPE, {0: [0x00580610], 1: [0x005A6920]}, "0x00580610 (player regeneration tick) / sub_005A6920_MonRegenEvent"),
        "STA": (R, [0x0056E970], "STATE_ApplyTimed 0x0056E970"),
    },
    "stats": {
        "AU0": (TYPE, {0: [0x0056FCB0, 0x0056FE40], 1: [0x0056FCB0, 0x0056FE40]},
                "EVENT_SelectedAuraTick 0x0056FCB0 / EVENT_ItemAuraTick 0x0056FE40; w p a player, h a hireling"),
        "CA": (R, [0x006250B0], "STATLIST_CacheAdd 0x006250B0"),
        "CW": (R, [0x00625150], "STATLIST_CacheWrite 0x00625150"),
        "DMG": (R, [0x00627A40, 0x00627860], "STATLIST_Disable/EnableDamageStats"),
        "EQR": (R, [0x0055DBC0], "sub_0055DBC0_EquipReqRefresh"),
        "EXP0": (R, [0x00580800], "EVENT_TimedListExpire 0x00580800"),
        "GRP": (R, [0x0056C740], "STATE_GroupClear 0x0056C740"),
        "LNK": (RA, ("ra", [0x00626E10]), "STATLIST_LinkToUnit 0x00626E10, the return address"),
        "MSK": (R, [0x00663CC0], "inside SETS_UpdateOnEquip (0x00663D09)"),
        "PAS": (R, [0x00646D60], "SKILLS_RefreshPassive 0x00646D60"),
        "PRP": (RA, ("ra", [0x00626920]), "STATLIST_Propagate 0x00626920, the return address"),
        "RD": (R, [0x00624F60], "sub_00624F60_StatListGetValue"),
        "RNGA": (TYPE, {0: [0x0056FCB0, 0x0056FE40], 1: [0x0056FCB0, 0x0056FE40]}, "an LCG site inside an AU0 run"),
        "RQ0": (R, [0x0062EAF0], "sub_0062EAF0_ItemReqCheck"),
        "RQ91": (R, [0x0062EAF0], "inside ItemReqCheck"), "RQD": (R, [0x0062EAF0], "inside ItemReqCheck"),
        "RQF": (R, [0x0062EAF0], "inside ItemReqCheck"), "RQL": (R, [0x0062EAF0], "inside ItemReqCheck"),
        "SBA": (R, [0x00660120], "sub_00660120_SetBonusApply"),
        "SCB": (R, [0x0055B800], "sub_0055B800_MonStatCallback"),
        "SHR0": (R, [0x00583C70], "OBJOP_Shrine 0x00583C70"),
        "STA0": (R, [0x0056E970], "STATE_ApplyTimed 0x0056E970"),
        "TGL": (R, [0x006279A0], "UNIT_ToggleStatListByState 0x006279A0"),
        "TIP": (R, [0x00663A20], "SETS_ToggleItemAProps 0x00663A20"),
        "TK0": (R, [0x00580810], "sub_00580810_RegenEvent"),
        "UOB": (R, [0x00663B40], "SETS_UpdateOwnerBonusList 0x00663B40"),
        "UOE": (R, [0x00663CC0], "SETS_UpdateOnEquip 0x00663CC0"),
        "ULK": (R, [0x006269F0], "STATLIST_Unlink 0x006269F0"),
        "WEL0": (R, [0x00585720], "the well use 0x00585720"),
        "ISC": (SKIP, None, "the ItemStatCost dump, once per game"),
        "OBJS": (SKIP, None, "the object dump every 2 s"),
        "TREE": (SKIP, None, "the player's tree dump after a top-level list event"),
        "TREE0": (SKIP, None, "the first tree dump"),
    },
    "economy": {
        "CD0": (R, [0x0057D3D0], "COMBAT_DurabilityLoss 0x0057D3D0"),
        "CDS": (R, [0x0057D3D0], "inside COMBAT_DurabilityLoss"), "CDU": (R, [0x0057D3D0], "inside it"),
        "CDW": (R, [0x0057D3D0], "inside it"),
        "CI0": (R, [0x00578460], "NPC_CainIdentify 0x00578460"),
        "DA0": (R, [0x0055A090], "sub_0055A090_DropGoldAmount"),
        "DG0": (R, [0x005357D0], "PLAYER_DeathGoldLoss 0x005357D0"),
        "DL0": (R, [0x00559E30], "ITEMS_DurabilityLossRoll 0x00559E30"),
        "DUL": (R, [0x00559A30], "sub_00559A30_DropItemAtUnit (site 0x00559AF8)"),
        "GA0": (RA, ("ra", [0x00557AD9]), "the gold amount at creation (0x00557AD9), the return address"),
        "GF0": (R, [0x005589A0], "sub_005589A0_DropGoldFind"), "GFK": (R, [0x005589A0], "inside it"),
        "GG0": (R, [0x0055B060], "sub_0055B060_PlayerGiveGold"),
        "GPL": (R, [0x00559300], "sub_00559300_DropGoldPile (site 0x00559338)"),
        "IB0": (R, [0x0055F900], "sub_0055F900_ItemRepairBroken"),
        "IC0": (R, [0x0056C310], "sub_0056C310_ItemConsumeOne"),
        "IR0": (R, [0x005761C0], "sub_005761C0_ItemRepairAll"),
        "MC0": (R, [0x006637B0], "MERC_ResurrectCost 0x006637B0"),
        "MR0": (R, [0x00579C00], "MERC_Resurrect 0x00579C00"),
        "NB0": (R, [0x00577830], "NPC_BuyItem 0x00577830"),
        "NR0": (R, [0x00578050], "sub_00578050_NpcRepair"),
        "NS0": (R, [0x00579510], "NPC_SellItem 0x00579510"), "NSX": (R, [0x00579510], "inside NPC_SellItem"),
        "PG0": (R, [0x00576D90], "sub_00576D90_PayGold"),
        "PR0": (RA, ("ra", [0x0062EFB0]), "ITEMS_TradePriceCore 0x0062EFB0, the return address"),
        "RC0": (R, [0x0062FE60], "sub_0062FE60_RepairCost"),
        "RP0": (RA, ("ra", [0x00562D30]), "ITEMEVENT_Replenish 0x00562D30, g_ItemEventFuncs[3]"),
        "UA0": (R, [0x0056C3F0], "PLAYER_UseAmmo 0x0056C3F0"),
        "UG0": (R, [0x0053FF00], "sub_0053FF00_UnitAddGoldStat"),
        "WG0": (R, [0x00594630], "sub_00594630_A1Q4_WirtGold"),
        "WGN": (R, [0x00594630], "inside it"), "WGS": (R, [0x00594630], "inside it"),
        "SWC": (RA, ("pc", []), "the read watchpoint's pc on the store record"),
        "SWW": (RA, ("pc", []), "the read watchpoint's pc on the store record"),
        "ECON": (SKIP, None, "the table dump, once per game"),
        "SWSET": (SKIP, None, "the watchpoint armed"),
    },
    "h6b": {
        "RPE": (TYPE, None, "sub_00558530_ItemReplenishDurTimer (stat 252) / sub_00558580_ItemReplenishQtyTimer (253)"),
        "RPS": (TYPE, None, "the schedule calls 0x00558574 / 0x005585C4"),
    },
}
FAMILY = {"anim.gdb": "anim", "skills.gdb": "skills", "combat.gdb": "combat", "two-combat.gdb": "combat",
          "stats.gdb": "stats", "economy.gdb": "economy", "economy2.gdb": "economy", "economy-hire.gdb": "economy",
          "h6b.gdb": "h6b"}
# begin/end pairs read_events leaves as two events (their tags are not TAG0/TAG1/TAGX): stats' and anim's; the end
# line takes its begin's pass (it is the same call), and serves the seed hand-off as the begin's exit
EXTRA_PAIRS = {"PRX": "PRP", "LNX": "LNK", "ULX": "ULK", "TGX": "TGL", "EQX": "EQR", "GRX": "GRP", "UOX": "UOE",
               "SBX": "SBA", "PAX": "PAS", "WINX": "WIN"}
RPE_HOOK = {252: 0x00558530, 253: 0x00558580}
SKIP_ALWAYS = {"CAP"}


# ---------------------------------------------------------------------------------------------- the binary
class Binary:
    """Direct calls of the pinned image (objdump) and its pointer tables, for the reach of a hook."""

    def __init__(self, exe=EXE):
        self.exe = exe
        with open(exe, "rb") as fh:
            self.img = fh.read()
        self.sha256 = hashlib.sha256(self.img).hexdigest()
        out = subprocess.run(["objdump", "-d", "--no-show-raw-insn", exe], check=True, capture_output=True,
                             text=True).stdout
        rx = re.compile(r"^\s+([0-9a-f]+):\s+(call|jmp)\s+0x([0-9a-f]+)\s*$", re.M)
        calls = [(int(a, 16), k, int(t, 16)) for a, k, t in rx.findall(out)]
        funcs = set()
        with open(os.path.join(ROOT, "re", "symbols.csv")) as fh:
            for row in csv.reader(fh):
                if len(row) > 2 and row[1] == "func":
                    try:
                        funcs.add(int(row[0], 16))
                    except ValueError:
                        pass
        funcs.update(t for _a, k, t in calls if k == "call")
        self.funcs = funcs
        self.flist = sorted(funcs)
        self.rev = collections.defaultdict(set)
        for a, k, t in calls:
            f = self.func_of(a)
            if k == "jmp" and self.func_of(t) == f:
                continue          # a branch inside the function
            if k == "jmp" and t not in funcs:
                continue          # a jump into another body that is no function entry: not a call edge
            self.rev[t].add(f)
        self.roots = self._roots()
        self._cache = {}

    def dword(self, va):
        return struct.unpack_from("<I", self.img, va - BASE)[0]

    def func_of(self, a):
        i = bisect.bisect_right(self.flist, a) - 1
        return self.flist[i] if i >= 0 else None

    def _roots(self):
        roots = {}

        def put(a, ranks, utype, name):
            if a in roots:
                old = roots[a]
                roots[a] = (old[0] | frozenset(ranks), None if old[1] != utype else utype, old[2] + "+" + name)
            else:
                roots[a] = (frozenset(ranks), utype, name)
        for a, r, n in PASS_FUNCS:
            put(a, {r}, None, n)
        for a, t, n in RUNNERS:
            put(a, TYPE_WALKS[t], t, n)
        for a, n in DRAIN:
            put(a, {21}, None, n)
        for base, t, n in EVENT_TABLES:
            for k in range(15):
                f = self.dword(base + 4 * k)
                if f:
                    put(f, TYPE_WALKS[t], t, "%s[%d]" % (n, k))
        put(MISSILE_DO[0], TYPE_WALKS[3], 3, MISSILE_DO[1])
        for op in range(0x67):
            f = self.dword(PACKET_TABLE + 8 * op)
            if 0x401000 <= f < 0x6CC000:
                put(f, {21}, None, "pkt%02X" % op)
        return roots

    def reach(self, addr):
        """-> (roots reached [(addr, ranks, utype, name)], open roots [addr], functions visited)."""
        f = addr if addr in self.funcs else self.func_of(addr)
        if f in self._cache:
            return self._cache[f]
        seen, todo, got, opened = {f}, [f], [], []
        while todo:
            x = todo.pop()
            if x in self.roots:
                got.append((x,) + self.roots[x])
                continue
            callers = self.rev.get(x, ())
            new = [c for c in callers if c not in seen]
            if not callers:
                opened.append(x)
            for c in new:
                seen.add(c)
                todo.append(c)
        res = (sorted(got), sorted(opened), len(seen))
        self._cache[f] = res
        return res

    def passes(self, addrs, utype=None):
        """The pass set of a list of hooks, narrowed by the unit type; None when any reach is open or empty."""
        out = set()
        for a in addrs:
            got, opened, _n = self.reach(a)
            if opened or not got:
                return None
            typed = [g for g in got if g[2] is not None]
            if utype is not None and any(g[2] == utype for g in typed):
                got = [g for g in got if g[2] is None or g[2] == utype]
            for g in got:
                out |= g[1]
        return frozenset(out) if out else None


# ---------------------------------------------------------------------------------------------- events
Ev = collections.namedtuple("Ev", "line end frame kind utype uid units entry exit raw")


def spans(path):
    """{begin line: end line} with read_events' pairing (end.k == begin.n, else the latest open begin of the tag)."""
    _h, tagstats, _l = frame_corpus.scan_log(path)
    ends = frame_corpus.pair_tags(tagstats)
    for e, b in EXTRA_PAIRS.items():
        if e in tagstats and b in tagstats and b not in ends:
            ends[b] = e
    e2b = {e: b for b, e in ends.items()}
    out = {}
    by_n = {}
    stack = collections.defaultdict(list)
    with open(path, errors="replace") as fh:
        fh.readline()
        for ln, line in enumerate(fh, 2):
            i = line.find(" {")
            if i < 1 or i > 12:
                continue
            tag = line[:i]
            framed = frame_corpus.RE_FR.search(line) or frame_corpus.RE_FRAME.search(line)
            if not framed and tag not in e2b:
                continue
            if tag not in e2b and tag not in ends:
                continue
            try:
                o = json.loads(line[i + 1:])
            except ValueError:
                continue
            if not isinstance(o, dict):
                continue
            if tag in e2b:
                base = e2b[tag]
                b = None
                if "k" in o and o["k"] in by_n:
                    b = by_n.pop(o["k"])
                    if b in stack[base]:
                        stack[base].remove(b)
                elif stack[base]:
                    b = stack[base].pop()
                if b is not None:
                    out[b] = ln
                continue
            if "n" in o:
                by_n[o["n"]] = ln
            stack[tag].append(ln)
    return out


RAW_FIELDS = ("ra", "ret", "pc", "ph", "u", "k", "a", "b", "q", "T", "m", "cl", "w", "stat", "t", "site", "do", "o", "d", "mi")


def load(path):
    """-> [Ev] for one log, in line order: read_events' stream with each begin's end line and the raw fields the
    rules need (a field kept only when the line holds it)."""
    evs = list(frame_corpus.read_events(path))
    span = spans(path)
    want = {e.line for e in evs}
    raw = {}
    with open(path, errors="replace") as fh:
        fh.readline()
        for ln, line in enumerate(fh, 2):
            if ln not in want:
                continue
            i = line.find(" {")
            try:
                o = json.loads(line[i + 1:])
            except ValueError:
                continue
            raw[ln] = {k: o[k] for k in RAW_FIELDS if k in o}
    out = [Ev(e.line, span.get(e.line), e.frame, e.kind, e.utype, e.uid, e.units, e.entry, e.exit, raw.get(e.line, {}))
           for e in evs]
    out.sort(key=lambda e: e.line)
    return out


class UnitTypes:
    """unit pointer -> type at a line: the nearest typed reference to that pointer at or before the line, else the
    first after it (a pointer is reused by later units, of any type)."""

    def __init__(self, evs):
        self.m = collections.defaultdict(list)
        for e in evs:
            for _k, v in e.raw.items():
                if isinstance(v, dict) and isinstance(v.get("u"), int) and isinstance(v.get("t"), int):
                    self.m[v["u"]].append((e.line, v["t"]))
            if isinstance(e.raw.get("u"), int) and isinstance(e.raw.get("t"), int) and e.kind != "STA":
                self.m[e.raw["u"]].append((e.line, e.raw["t"]))

    def at(self, ptr, line):
        xs = self.m.get(ptr)
        if not xs:
            return None
        i = bisect.bisect_right(xs, (line, 99)) - 1
        return xs[i][1] if i >= 0 else xs[0][1]


def own_set(bin_, fam, e, ptypes):
    """-> (pass set or None, class) for one event: class names the rule's outcome ('skip', 'client', 'open', or
    the set's name)."""
    rule = KINDS.get(fam, {}).get(e.kind)
    if e.kind in SKIP_ALWAYS:
        return None, "skip"
    if e.kind in EXTRA_PAIRS:
        return None, "end"
    if rule is None:
        return None, "unmapped"
    kind, args, _anchor = rule
    utype = e.utype
    if utype is None and isinstance(e.raw.get("u"), int):
        utype = ptypes.at(e.raw["u"], e.line)
    if kind == SKIP:
        return None, "skip"
    if kind == SITE:
        return frozenset(args), "site"
    if kind == PH:
        ph = e.raw.get("ph")
        if not isinstance(ph, int):
            return None, "no-ph"          # logger revisions 1 and 2 (before the phase breakpoints)
        if 1 <= ph <= 10:
            return frozenset({3 + ph}), "ph"
        return ALL - frozenset(range(4, 14)), "ph-out"
    if kind == TYPE:
        if fam == "h6b":
            hook = RPE_HOOK.get(e.raw.get("stat"))
            if hook is None:
                return None, "open"
            s = bin_.passes([hook], 4)
            return (s, "reach") if s else (None, "open")
        if fam == "combat":
            t = e.raw.get("t")
        else:
            w = e.raw.get("w")
            if isinstance(w, list) and len(w) == 1:
                w = w[0]
            t = {"p": 0, "h": 1}.get(w) if isinstance(w, str) else None
        hooks = args.get(t) if isinstance(args, dict) else None
        if hooks is None:
            return None, "open"
        s = bin_.passes(hooks, t)
        return (s, "reach") if s else (None, "open")
    if kind == R:
        s = bin_.passes(args, utype)
        return (s, "reach") if s else (None, "open")
    if kind == RA:
        field, hooks = args
        if fam == "skills" and e.kind == "CU0" and (e.raw.get("cl") or e.raw.get("ret") == 0x004D9FCA):
            return None, "client"         # the client's per-frame button check (return 0x004D9FCA; "cl" from rev 5)
        ra = e.raw.get(field)
        if isinstance(ra, int) and 0x401000 <= ra < 0x6CC000:
            s = bin_.passes([ra], utype)
            if s:
                return s, "ra"
        s = bin_.passes(hooks, utype) if hooks else None
        return (s, "reach") if s else (None, "open")
    return None, "unmapped"


def set_name(s):
    if s is None:
        return "-"
    rs = sorted(s)
    if len(rs) <= 3:
        return "+".join(PASS_NAMES[r] for r in rs)
    return "%s..%s(%d)" % (PASS_NAMES[rs[0]], PASS_NAMES[rs[-1]], len(rs))


# ---------------------------------------------------------------------------------------------- RNG
M32 = 0xFFFFFFFF
MULT = 0x6AC690C5


def sd(s):
    lo, hi = s.split(":")
    return int(lo, 16), int(hi, 16)


def step(t):
    v = t[0] * MULT + t[1]
    return v & M32, (v >> 32) & M32


def steps(a, b, limit=4096):
    t = a
    for i in range(limit + 1):
        if t == b:
            return i
        t = step(t)
    return None


def _unit_obj(e, role):
    """A unit's seed object: ('unit', pointer) when the line gives the pointer (the server's and the client's copies
    of one unit share type and id), else ('unit-id', type, id)."""
    p = e.raw.get(role)
    if isinstance(p, dict) and isinstance(p.get("u"), int):
        return ("unit", p["u"])
    if isinstance(p, int) and p > 0xFFFF:
        return ("unit", p)
    obj = e.units.get(role)
    if obj and obj[1] is not None:
        return ("unit-id",) + tuple(obj)
    return None


def seed_objects(e, side):
    """{seed object: value} of one event's entry (side 'entry') or exit seeds. Objects: ('game',), ('player',) for
    the stats and economy families' gs/us/ps, ('unit', pointer) of a unit role (or ('unit-id', type, id))."""
    seeds = e.entry if side == "entry" else e.exit
    out = {}
    for k, v in seeds.items():
        leaf = k.split(".")[-1]
        role = k.split(".")[0] if "." in k else None
        if leaf == "gs":
            out[("game",)] = v
            continue
        if leaf in ("us", "ps"):
            w = e.raw.get("w")
            if isinstance(w, list) and len(w) == 1:
                w = w[0]
            if w in ("h", "m"):
                # stats' STA0 (target "t") and AU0 ("u") of a hireling or a monster: that unit's seed
                p = e.raw.get("t") if e.kind == "STA0" else e.raw.get("u")
                out[("unit", p) if isinstance(p, int) else ("unknown",)] = v
            else:
                out[("player",)] = v
            continue
        if role is not None and leaf == "s":
            obj = _unit_obj(e, role)
            if obj:
                out[obj] = v
            continue
        if role is None and leaf in ("s", "sa", "sd", "sb", "su", "so", "sm"):
            r = {"s": None, "sa": "a", "sd": "d", "sb": "b", "su": "u", "so": "o", "sm": "m"}[leaf]
            for c in ([r] if r else ["u", "o", "d", "m", "mi"]):
                obj = _unit_obj(e, c)
                if obj:
                    out[obj] = v
                    break
    return out


# ---------------------------------------------------------------------------------------------- the check
# control orders: a rank permutation each (old rank -> new rank)
def _perm(order):
    return {r: i for i, r in enumerate(order, 1)}


BASE_ORDER = list(range(1, 22))
CONTROLS = {
    "monsters-before-players": _perm([1, 2, 3, 4, 5, 8, 9, 6, 7] + list(range(10, 22))),
    "slot-before-every-frame": _perm([1, 2, 3, 5, 4, 7, 6, 9, 8, 11, 10, 13, 12] + list(range(14, 22))),
    "missiles-after-items": _perm([1, 2, 3, 6, 7, 8, 9, 10, 11, 12, 13, 4, 5] + list(range(14, 22))),
    "drain-before-the-tick": _perm([21] + list(range(1, 21))),
}


def place(seq, perm=None):
    """Greedy placement of [(index, set)] in logged order -> [indices that cannot be placed]."""
    cur = 0
    bad = []
    for i, s in seq:
        rs = sorted(perm[r] for r in s) if perm else sorted(s)
        c = [r for r in rs if r >= cur]
        if not c:
            bad.append(i)
            continue
        cur = c[0]
    return bad


class Check:
    def __init__(self, bin_):
        self.bin = bin_
        self.c = collections.Counter()           # global counters
        self.kind = collections.defaultdict(collections.Counter)   # (family, kind) -> counters
        self.sep = collections.Counter()         # (set name A, set name B) separating pairs
        self.ctrl = collections.Counter()
        self.ctrl_frames = collections.Counter()
        self.seed = collections.Counter()
        self.seed_k = collections.Counter()
        self.seed_kind = collections.defaultdict(collections.Counter)
        self.slot = collections.Counter()
        self.mf = collections.Counter()
        self.cross = collections.Counter()
        self.notes = []
        self.rows = []

    def note(self, s):
        if len(self.notes) < 400:
            self.notes.append(s)

    def log(self, root, rel, logger):
        fam = FAMILY.get(logger)
        path = os.path.join(root, rel)
        evs = load(path)
        ptypes = UnitTypes(evs)
        # an EXTRA_PAIRS end line is its begin's call: the seed hand-off takes the two as one event
        ends = {e.end: e for e in evs if e.end}
        self.canon = {e.line: ends[e.line] for e in evs if e.kind in EXTRA_PAIRS and e.line in ends}
        row = collections.Counter()
        # segments: a new game where the stamp falls
        seg = 0
        last = None
        frames = collections.OrderedDict()
        for e in evs:
            if e.frame is None:
                row["no-frame"] += 1
                continue
            if last is not None and e.frame < last:
                seg += 1
                self.note("%s: stamp falls %d -> %d at line %d (segment %d)" % (rel, last, e.frame, e.line, seg))
            last = e.frame
            frames.setdefault((seg, e.frame), []).append(e)
        row["segments"] = seg + 1
        sets = {}
        for e in evs:
            s, cls = own_set(self.bin, fam, e, ptypes)
            sets[e.line] = (s, cls)
            self.kind[(fam, e.kind)]["events"] += 1
            self.kind[(fam, e.kind)]["class " + cls] += 1
            row["events"] += 1
            if e.uid is None:
                row["no unit id"] += 1
                self.kind[(fam, e.kind)]["no unit id"] += 1
            if not e.entry and not e.exit:
                row["no seed"] += 1
                self.kind[(fam, e.kind)]["no seed"] += 1
        # nesting: intersect with every closed pair the event lies in
        opened = []
        eff = {}
        for e in evs:
            while opened and opened[-1][0] < e.line:
                opened.pop()
            s, cls = sets[e.line]
            if cls == "skip" or cls == "client":
                eff[e.line] = (None, cls)
            else:
                cs = [x[1] for x in opened if x[1] is not None]
                if cs:
                    inter = frozenset.intersection(*cs)
                    if s is None:
                        s, cls = inter, "nested"
                    else:
                        s2 = s & inter
                        if not s2:
                            self.c["nesting conflicts"] += 1
                            self.note("%s:%d %s nesting conflict own %s outer %s" % (rel, e.line, e.kind, set_name(s),
                                                                                     set_name(inter)))
                            cls = "conflict"
                        s = s2
                eff[e.line] = (s if s else None, cls)
            if e.end is not None and e.end > e.line:
                ins = sets[e.line][0] if sets[e.line][1] not in ("skip", "client") else None
                if eff[e.line][0] is not None:
                    ins = eff[e.line][0]
                opened.append((e.end, ins))
                opened.sort(key=lambda x: -x[0])
        for (sg, fr), fevs in frames.items():
            real = [e for e in fevs if eff[e.line][1] not in ("skip", "client")]
            if len(real) < 2:
                continue
            row["frames2"] += 1
            row["events in frames2"] += len(real)
            placed = [(e, eff[e.line][0]) for e in real if eff[e.line][0] is not None]
            for e in real:
                self.kind[(fam, e.kind)]["in frames2"] += 1
            self.seeds(rel, fr, real, eff, fam)
            if len(placed) < 2:
                continue
            row["frames placed2"] += 1
            for e, s in placed:
                self.kind[(fam, e.kind)]["compared"] += 1
                self.kind[(fam, e.kind)]["compared as " + ("nested" if eff[e.line][1] == "nested" else "own")] += 1
                if eff[e.line][1] != "nested":
                    row["compared own"] += 1
                row["compared"] += 1
            bad = place([(i, s) for i, (e, s) in enumerate(placed)])
            for i in bad:
                e = placed[i][0]
                self.kind[(fam, e.kind)]["mismatch"] += 1
                row["mismatch"] += 1
                self.note("%s:%d frame %d %s set %s: order mismatch" % (rel, e.line, fr, e.kind, set_name(placed[i][1])))
            for name, perm in CONTROLS.items():
                b2 = place([(i, s) for i, (e, s) in enumerate(placed)], perm)
                if b2:
                    self.ctrl[name] += len(b2)
                    self.ctrl_frames[name] += 1
            for (ea, sa), (eb, sb) in zip(placed, placed[1:]):
                if max(sa) < min(sb):
                    self.sep[(set_name(sa), set_name(sb))] += 1
                    row["separating"] += 1
        if fam == "anim":
            self.slot_order(rel, evs, frames, ptypes)
            self.cross_ef(rel, evs, ptypes)
        if fam == "skills":
            self.mf_order(rel, evs, frames)
        for k, v in row.items():
            self.c[k] += v
        self.c["logs"] += 1
        self.rows.append((rel, logger, row))

    # ------------------------------------------------------------------ seeds
    def seeds(self, rel, fr, real, eff, fam):
        """The seed observations of one frame in time order (an event's entry at its line, its exit at its end line):
        each pair of consecutive observations of one seed object by two events is a hand-off."""
        obs = []
        for e in real:
            e = self.canon.get(e.line, e)
            for obj, v in seed_objects(e, "entry").items():
                obs.append((e.line, 0, obj, v, e))
            for obj, v in seed_objects(e, "exit").items():
                obs.append((e.end if e.end else e.line, 1, obj, v, e))
        obs.sort(key=lambda x: (x[0], x[1]))
        last = {}
        for pos, _side, obj, v, e in obs:
            if obj in last:
                pe, pv = last[obj]
                if pe is not e:
                    self.handoff(rel, fr, pe, pv, e, v, obj, fam)
            last[obj] = (e, v)

    def handoff(self, rel, fr, pe, pv, e, v, obj, fam):
        key = (fam, obj[0])
        if pv == v:
            r = "handed"
        else:
            a, b = sd(pv), sd(v)
            k = steps(a, b)
            if k is not None:
                r = "stepped"
                self.seed_k[(fam, obj[0], min(k, 9) if k < 10 else (10 if k < 100 else 100))] += 1
            elif steps(b, a) is not None:
                r = "reversed"
                self.note("%s:%d frame %d %s after %s:%d on %s: seed reversed" % (rel, e.line, fr, e.kind, pe.kind,
                                                                                 pe.line, obj))
            else:
                r = "off"
                if self.c["off notes"] < 60:
                    self.c["off notes"] += 1
                    self.note("%s:%d frame %d %s after %s:%d on %s: off the stream (%s -> %s)" % (
                        rel, e.line, fr, e.kind, pe.kind, pe.line, obj, pv, v))
        self.seed[key + (r,)] += 1
        self.seed_kind[(fam, pe.kind, e.kind)][r] += 1

    # ------------------------------------------------------------------ slot order (anim)
    def slot_order(self, rel, evs, frames, ptypes):
        """PDS/MDS dispatches against the queue order of their records (SCH q, CQ q), oldest queued first."""
        recs = collections.defaultdict(list)    # (ptr, kind, a, b, frame) -> [queue key]
        seq = 0
        for e in evs:
            r = e.raw
            if e.kind in ("SCH", "RSC") and isinstance(r.get("q"), list):
                u = r.get("u", {}).get("u") if isinstance(r.get("u"), dict) else None
                T = r.get("T", e.frame)
                for q in r["q"]:
                    if not (isinstance(q, list) and len(q) == 4):
                        continue
                    kind, f, a, b = q
                    if f == -1:
                        continue
                    if T is not None and f <= T:
                        f = T + 1
                    seq += 1
                    recs[(u, kind, a, b, f)].append(seq)
            elif e.kind == "CQ" and isinstance(r.get("q"), list) and len(r["q"]) == 4:
                u = r.get("u", {}).get("u") if isinstance(r.get("u"), dict) else None
                kind, f, a, b = r["q"]
                if f == -1:
                    continue
                if e.frame is not None and f <= e.frame:
                    f = e.frame + 1
                seq += 1
                recs[(u, kind, a, b, f)].append(seq)
            elif e.kind == "CAN":
                # UNIT_CancelEvents(unit, kind, x): the logger does not write x; taken as 0 (every record of the
                # kind), so a partial cancel can only leave a later dispatch unmatched, never matched wrongly
                for key in [k for k in recs if k[0] == r.get("u") and k[1] == r.get("k")]:
                    self.slot["records cancelled (CAN)"] += len(recs.pop(key))
            elif e.kind in ("PDS", "MDS"):
                key = (r.get("u"), r.get("k"), r.get("a"), r.get("b"), e.frame)
                c = recs.get(key)
                if c:
                    e.raw["_q"] = c.pop(0)
        for (sg, fr), fevs in frames.items():
            for tag in ("PDS", "MDS"):
                ds = [e for e in fevs if e.kind == tag]
                if not ds:
                    continue
                m = [e for e in ds if "_q" in e.raw]
                self.slot[tag + " dispatches"] += len(ds)
                self.slot[tag + " matched to a logged queue"] += len(m)
                if len(m) < 2:
                    continue
                self.slot[tag + " frames with 2+ matched"] += 1
                self.slot[tag + " matched in those frames"] += len(m)
                for x, y in zip(m, m[1:]):
                    if x.raw["_q"] < y.raw["_q"]:
                        self.slot[tag + " pairs in queue order"] += 1
                    else:
                        self.slot[tag + " pairs inverted"] += 1
                        self.note("%s:%d frame %d %s before %d queued later" % (rel, x.line, fr, tag, y.line))

    # ------------------------------------------------------------------ every-frame order (skills MF0)
    def mf_order(self, rel, evs, frames):
        """MF0 lines of one frame: each windowed missile's first line, against its creation (MC1) line."""
        created = collections.defaultdict(list)   # missile pointer -> [MC1 lines] (a pointer is reused)
        self._mc_lines(rel, created)
        for (sg, fr), fevs in frames.items():
            seen = []
            for e in fevs:
                if e.kind == "MF0" and isinstance(e.raw.get("m"), int):
                    p = e.raw["m"]
                    if p not in [x[0] for x in seen]:
                        c = [x for x in created.get(p, ()) if x < e.line]
                        seen.append((p, c[-1] if c else None))
            if len(seen) < 2:
                continue
            self.mf["frames with 2+ windowed missiles"] += 1
            for (pa, ca), (pb, cb) in zip(seen, seen[1:]):
                if ca is None or cb is None:
                    self.mf["pairs without a logged creation"] += 1
                elif ca > cb:
                    self.mf["pairs newest first"] += 1
                else:
                    self.mf["pairs oldest first"] += 1
                    self.note("%s frame %d MF0 missile %d (created line %d) before %d (line %d)" % (rel, fr, pa, ca, pb,
                                                                                                 cb))

    def _mc_lines(self, rel, created):
        path = self._abs
        with open(path, errors="replace") as fh:
            for ln, line in enumerate(fh, 1):
                if line.startswith("MC1 {"):
                    try:
                        o = json.loads(line[4:])
                    except ValueError:
                        continue
                    m = o.get("m")
                    if isinstance(m, dict) and isinstance(m.get("u"), int):
                        created[m["u"]].append(ln)

    # ------------------------------------------------------------------ cross-type every-frame queues (anim EF)
    def cross_ef(self, rel, evs, ptypes):
        for e in evs:
            if e.kind != "EF":
                continue
            t = ptypes.at(e.raw.get("u"), e.line)
            ph = e.raw.get("ph")
            if not isinstance(ph, int):
                self.cross["EF without a phase (logger rev 1, 2)"] += 1
                continue
            if t not in (0, 1):
                self.cross["EF unit type not logged near it"] += 1
                continue
            recv = TYPE_WALKS[t][0] - 3          # the receiving type's every-frame phase
            tn = {0: "player", 1: "monster"}.get(t, str(t))
            if 1 <= ph < recv:
                self.cross["%s queued in an earlier walk (%s): runs this frame" % (tn, PASS_NAMES[ph + 3])] += 1
                self.cross["%s cross-type, this frame" % tn] += 1
            elif 1 <= ph <= 10:
                self.cross["%s queued in its own or a later walk (%s): next frame" % (tn, PASS_NAMES[ph + 3])] += 1
            else:
                self.cross["%s queued outside the walks (ph %d): next frame's walk" % (tn, ph)] += 1


def corpus_logs(index=INDEX):
    out = []
    with open(index) as fh:
        for r in csv.DictReader(fh, delimiter="\t"):
            if r["harness"] == "True" and int(r["framed"]) > 0 and r["runs"]:
                out.append((r["path"], r["gdb"]))
    return out


def cmd_check(a):
    bin_ = Binary(a.exe)
    ck = Check(bin_)
    if a.logs:
        idx = {p: g for p, g in corpus_logs()}
        todo = [(p, idx.get(p) or frame_corpus.header(open(os.path.join(a.root, p)).readline())["gdb"]) for p in a.logs]
    else:
        todo = corpus_logs()
    for rel, logger in todo:
        ck._abs = os.path.join(a.root, rel)
        ck.log(a.root, rel, logger)
        sys.stderr.write("done %s\n" % rel)
    lines = report(ck, bin_, todo)
    text = "\n".join(lines) + "\n"
    if a.out:
        os.makedirs(a.out, exist_ok=True)
        with open(os.path.join(a.out, "check.txt"), "w") as fh:
            fh.write(text)
        with open(os.path.join(a.out, "frame-check-logs.tsv"), "w") as fh:
            keys = ROW_KEYS
            fh.write("log\tlogger\t" + "\t".join(keys) + "\n")
            for rel, logger, row in ck.rows:
                fh.write("%s\t%s\t%s\n" % (rel, logger, "\t".join(str(row[k]) for k in keys)))
    sys.stdout.write(text)
    mism = ck.c["mismatch"] + ck.c["nesting conflicts"] + ck.slot["PDS pairs inverted"] + \
        ck.slot["MDS pairs inverted"] + ck.mf["pairs oldest first"] + \
        sum(v for k, v in ck.seed.items() if k[2] == "reversed")
    return 1 if mism else 0


ROW_KEYS = ["events", "no unit id", "no seed", "segments", "frames2", "events in frames2", "frames placed2", "compared",
            "compared own", "separating", "mismatch", "no-frame"]


def report(ck, bin_, todo):
    L = []
    L.append("frame.py check (plan 0055 Phase 2a); game.exe %s" % bin_.sha256)
    L.append("tool sha256 %s; frame_corpus.py %s" % (_sha(__file__), _sha(frame_corpus.__file__)))
    L.append("logs %d" % len(todo))
    L.append("")
    L.append("== totals")
    for k in ["logs"] + ROW_KEYS + ["nesting conflicts"]:
        L.append("  %-22s %d" % (k, ck.c[k]))
    L.append("")
    L.append("== per logger (gdb script): logs, " + ", ".join(ROW_KEYS))
    by = collections.defaultdict(collections.Counter)
    nlogs = collections.Counter()
    for _rel, logger, row in ck.rows:
        by[logger].update(row)
        nlogs[logger] += 1
    for logger in sorted(by):
        L.append("  %-17s logs %3d  %s" % (logger, nlogs[logger], "  ".join("%s %d" % (k, by[logger][k]) for k in ROW_KEYS)))
    L.append("")
    L.append("== per family and kind: events, in frames with 2+ events, compared (placed, in a frame with 2+ "
             "placed), mismatches; the rule's outcome per event")
    for (fam, kind) in sorted(ck.kind):
        c = ck.kind[(fam, kind)]
        cls = " ".join("%s=%d" % (k[6:], v) for k, v in sorted(c.items()) if k.startswith("class "))
        L.append("  %-8s %-6s events %8d  in-frames2 %8d  compared %8d (own %d, nested %d)  mismatch %d  "
                 "no-uid %d  no-seed %d  [%s]" % (
                     fam, kind, c["events"], c["in frames2"], c["compared"], c["compared as own"],
                     c["compared as nested"], c["mismatch"], c["no unit id"], c["no seed"], cls))
    L.append("")
    L.append("== separating pairs (consecutive placed events whose sets do not overlap), by set")
    for (a, b), v in sorted(ck.sep.items(), key=lambda x: -x[1]):
        L.append("  %8d  %s -> %s" % (v, a, b))
    L.append("")
    L.append("== control orders: events that cannot be placed, frames failing")
    for name in CONTROLS:
        L.append("  %-26s events %d frames %d" % (name, ck.ctrl[name], ck.ctrl_frames[name]))
    L.append("")
    L.append("== slot-list order (anim PDS/MDS against the queue order of SCH/RSC/CQ records)")
    for k in sorted(ck.slot):
        L.append("  %-40s %d" % (k, ck.slot[k]))
    L.append("")
    L.append("== every-frame order (skills MF0 against the missiles' MC1 creation lines)")
    for k in sorted(ck.mf):
        L.append("  %-40s %d" % (k, ck.mf[k]))
    L.append("")
    L.append("== cross-type every-frame queues (anim EF: the queueing walk against the receiving type's every-frame walk)")
    for k in sorted(ck.cross):
        L.append("  %-70s %d" % (k, ck.cross[k]))
    L.append("")
    L.append("== seed hand-offs in one frame (family, object, result)")
    for k in sorted(ck.seed):
        L.append("  %-8s %-7s %-9s %d" % (k[0], k[1], k[2], ck.seed[k]))
    L.append("  steps of the stepped hand-offs (family, object, k: 1..9, 10 = 10..99, 100 = 100..4096)")
    for k in sorted(ck.seed_k):
        L.append("    %-8s %-7s %3d  %d" % (k[0], k[1], k[2], ck.seed_k[k]))
    L.append("  by kind pair (family, first, second): handed / stepped / reversed / off")
    for k in sorted(ck.seed_kind):
        c = ck.seed_kind[k]
        L.append("    %-8s %-6s %-6s %d / %d / %d / %d" % (k[0], k[1], k[2], c["handed"], c["stepped"], c["reversed"],
                                                          c["off"]))
    L.append("")
    L.append("== notes (first 400)")
    L.extend("  " + n for n in ck.notes)
    return L


def _sha(p):
    with open(p, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


# ---------------------------------------------------------------------------------------------- reach / kinds
def cmd_reach(a):
    bin_ = Binary(a.exe)
    addrs = [int(x, 16) for x in a.addrs]
    if not addrs:
        for fam, ks in sorted(KINDS.items()):
            for kind, (rule, args, _an) in sorted(ks.items()):
                hooks = []
                if rule == R:
                    hooks = args
                elif rule == RA:
                    hooks = args[1]
                elif rule == TYPE and isinstance(args, dict):
                    hooks = sorted({h for v in args.values() for h in v})
                elif rule == TYPE and fam == "h6b":
                    hooks = sorted(RPE_HOOK.values())
                for h in hooks:
                    addrs.append(h)
    print("game.exe %s; %d functions, %d roots" % (bin_.sha256, len(bin_.flist), len(bin_.roots)))
    for h in sorted(set(addrs)):
        got, opened, n = bin_.reach(h)
        f = h if h in bin_.funcs else bin_.func_of(h)
        s = bin_.passes([h])
        print("0x%08X fn 0x%08X visited %d roots %d open %d -> %s; roots %s%s" % (
            h, f, n, len(got), len(opened), set_name(s) if s else "open",
            ",".join(sorted({g[3] for g in got}))[:300], "" if not opened else "; open e.g. " +
            ",".join("0x%08X" % x for x in opened[:5])))
    return 0


def cmd_kinds(_a):
    for fam, ks in sorted(KINDS.items()):
        for kind, (rule, args, anchor) in sorted(ks.items()):
            if rule in (R,):
                arg = ",".join("0x%08X" % h for h in args)
            elif rule == RA:
                arg = "%s|%s" % (args[0], ",".join("0x%08X" % h for h in args[1]))
            elif rule == SITE:
                arg = set_name(frozenset(args))
            elif rule == TYPE and isinstance(args, dict):
                arg = ";".join("%s:%s" % (t, ",".join("0x%08X" % h for h in v)) for t, v in sorted(args.items()))
            else:
                arg = ""
            print("%s\t%s\t%s\t%s\t%s" % (fam, kind, rule, arg, anchor))
    return 0


# ---------------------------------------------------------------------------------------------- rechain
RE_GAP = re.compile(r"^(\S+\.log) n=(\d+) (player|monster) unit (\d+) \[([^\]]*)\]: (\S+) steps")


def cmd_rechain(a):
    """For every resync a skills.py --gaps file lists: the previous skill event (SST0/SDO0) of the unit before the
    entry line n, then every event between naming the unit's seed (any role, entry or exit) in model order (the logged
    order, which the check finds equal), each link handed (equal) or, for a single-draw line (THR, DRR: the seed after
    one draw), one step. Re-chained when the walk reaches the entry; otherwise the first link that does not close."""
    out = collections.Counter()
    reasons = collections.Counter()
    lines = []
    for gf in a.gaps:
        cache = {}
        with open(gf) as fh:
            for ln in fh:
                m = RE_GAP.match(ln)
                if not m:
                    continue
                log, n, who, u, why, k = m.group(1), int(m.group(2)), m.group(3), int(m.group(4)), m.group(5), m.group(6)
                out[(os.path.basename(gf), who, "listed")] += 1
                p = _find_log(a.root, log)
                if p not in cache:
                    cache.clear()
                    cache[p] = _skills_lines(p)
                res, info = _walk_gap(cache[p], n, u)
                out[(os.path.basename(gf), who, res)] += 1
                reasons[(os.path.basename(gf), who, res, why if res != "re-chained" else "")] += 1
                lines.append("%s %s n=%d %s unit %d [%s] skills.py %s steps -> %s: %s" % (os.path.basename(gf), log, n,
                                                                                       who, u, why, k, res, info))
    for k in sorted(out):
        print("%-36s %-8s %-28s %d" % (k[0], k[1], k[2], out[k]))
    print("by skills.py's reason:")
    for k in sorted(reasons):
        print("  %-36s %-8s %-28s %-70s %d" % (k[0], k[1], k[2], k[3], reasons[k]))
    if a.out:
        with open(a.out, "w") as fh:
            fh.write("\n".join(lines) + "\n")
    return 0


def _find_log(root, base):
    for dp, _dn, fn in os.walk(os.path.join(root, "skills")):
        if base in fn:
            return os.path.join(dp, base)
    raise SystemExit("log not found: " + base)


def _skills_lines(path):
    """[(tag, json)] by n (the logger's own line count), every tagged line."""
    out = []
    with open(path, errors="replace") as fh:
        fh.readline()
        for line in fh:
            i = line.find(" {")
            if i < 1 or i > 12:
                continue
            try:
                o = json.loads(line[i + 1:])
            except ValueError:
                continue
            if isinstance(o, dict):
                out.append((line[:i], o))
    return out


def _obs(tag, o, u):
    """The unit u's seed observations of one line: [(where, value)], where 'in' an entry, 'out' an exit, 'one' the
    seed after one draw (THR, DRR)."""
    res = []
    if tag == "THR" and o.get("a") == u and o.get("sa"):
        return [("one", o["sa"])]
    if tag == "DRR" and o.get("u") == u and o.get("s"):
        return [("one", o["s"])]
    end = tag.endswith("1") or tag.endswith("X") or tag in ("EVR", "MCB1")
    for k, v in o.items():
        if isinstance(v, dict) and v.get("u") == u and isinstance(v.get("s"), str):
            res.append(("out" if end else "in", v["s"]))
    for r, sk in (("a", "sa"), ("b", "sb"), ("d", "sd"), ("u", "su"), ("o", "so"), ("u", "s")):
        if o.get(r) == u and isinstance(o.get(sk), str):
            res.append(("out" if end else "in", o[sk]))
    return res


def _walk_gap(lines, n, u):
    idx = None
    for i, (t, o) in enumerate(lines):
        if o.get("n") == n:
            idx = i
            break
    if idx is None:
        return "entry not found", ""
    t0, o0 = lines[idx]
    target = (o0.get("u") or {}).get("s")
    j = idx - 1
    prev = None
    while j >= 0:
        t, o = lines[j]
        if t in ("SST1", "SDO1"):
            k = o.get("k")
            b = [x for x in lines[:j] if x[1].get("n") == k]
            if b and (b[0][1].get("u") or {}).get("u") == u:
                prev = (j, o.get("s"))
                break
        j -= 1
    if prev is None or not target:
        return "previous event not found", ""
    cur = sd(prev[1])
    tgt = sd(target)
    used = 0
    for t, o in lines[prev[0] + 1:idx]:
        for where, v in _obs(t, o, u):
            x = sd(v)
            if where == "one":
                if step(cur) == x:
                    cur = x
                    used += 1
                elif cur != x:
                    return "not re-chained", "%s n=%s off the walk (%d links)" % (t, o.get("n"), used)
            elif x != cur:
                return "not re-chained", "%s n=%s %s seed differs (%d links)" % (t, o.get("n"), where, used)
            else:
                used += 1
    if cur == tgt:
        return "re-chained", "%d links" % used
    k = steps(cur, tgt)
    return "not re-chained", "the walk ends %s steps before the entry (%d links)" % (k, used)


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd")
    p = sub.add_parser("reach")
    p.add_argument("--exe", default=EXE)
    p.add_argument("addrs", nargs="*")
    sub.add_parser("kinds")
    p = sub.add_parser("check")
    p.add_argument("--exe", default=EXE)
    p.add_argument("--out")
    p.add_argument("root")
    p.add_argument("logs", nargs="*")
    p = sub.add_parser("rechain")
    p.add_argument("--out")
    p.add_argument("root")
    p.add_argument("gaps", nargs="+")
    a = ap.parse_args(argv[1:])
    if a.cmd == "reach":
        return cmd_reach(a)
    if a.cmd == "kinds":
        return cmd_kinds(a)
    if a.cmd == "check":
        return cmd_check(a)
    if a.cmd == "rechain":
        return cmd_rechain(a)
    ap.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
