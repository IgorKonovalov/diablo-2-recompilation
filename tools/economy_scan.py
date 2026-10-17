#!/usr/bin/env python3
"""Static call-site and reader scans behind items/0011 (plan 0043 Phase 1).

Usage:
  python3 -I tools/economy_scan.py <game.exe>            # all sections
  python3 -I tools/economy_scan.py <game.exe> calls      # callers of the economy functions
  python3 -I tools/economy_scan.py <game.exe> books      # Books record readers (BOOKS_GetRecord call sites)
  python3 -I tools/economy_scan.py <game.exe> draws      # LCG constant and RNG calls inside the read functions
  python3 -I tools/economy_scan.py <game.exe> pointers   # 4-byte image search for each target address
  python3 -I tools/economy_scan.py <game.exe> storerec   # byte reads at +0x24..+0x26 / +0x10..+0x12 in the read functions

Runs `objdump -d -M intel --no-show-raw-insn` on the pinned Game.exe and prints one line per finding, then a
`SCAN` summary line per section. Prints addresses only, no game data. Patterns:
  calls     an instruction `call   0x<target>` or `jmp    0x<target>` (direct only; no pointer table holds any of
            these targets, checked separately by a 4-byte search of the image).
  books     each `call   0x6374b0`, then the `[reg+0xNN]` operands (reg not ebp/esp) of the next 16 instructions; and every operand
            naming 0x96cc60 or 0x96cc64 (the table count and base).
  storerec  in the function ranges listed in STORE_FUNCS, any operand `BYTE PTR [reg+0x24|0x25|0x26]` or
            `[reg+0x10|0x11|0x12]` (the record + 0x14 form of NPCSTORE_CtlCreate).
"""
import re
import subprocess
import sys

TARGETS = {
    0x0062FDC0: "sub_0062FDC0_ItemTradePrice",
    0x0062EFB0: "ITEMS_TradePriceCore",
    0x0062FE60: "sub_0062FE60_RepairCost",
    0x00629370: "sub_00629370_GamblePrice",
    0x00576D90: "sub_00576D90_PayGold",
    0x0055B060: "sub_0055B060_PlayerGiveGold",
    0x0053FF00: "sub_0053FF00_UnitAddGoldStat",
    0x00622E70: "PLAYER_GoldCap",
    0x00623460: "PLAYER_StashGoldCap",
    0x006637B0: "MERC_ResurrectCost",
    0x005357D0: "PLAYER_DeathGoldLoss",
    0x00535510: "sub_00535510_PlayerDropGold",
    0x0055A090: "sub_0055A090_DropGoldAmount",
    0x00559E30: "ITEMS_DurabilityLossRoll",
    0x0057D3D0: "COMBAT_DurabilityLoss",
    0x0056C3F0: "PLAYER_UseAmmo",
    0x0056C310: "sub_0056C310_ItemConsumeOne",
    0x0056BEC0: "sub_0056BEC0_UseCharge",
    0x005DAA40: "sub_005DAA40_SkillWeaponWear",
    0x00562C40: "sub_00562C40_ReplenishStep",
    0x00578ED0: "sub_00578ED0_NpcHealDead",
    0x00578460: "NPC_CainIdentify",
    0x006374B0: "BOOKS_GetRecord",
}

# Function ranges (start, end) read in items/0011 that handle an NPC: none takes a NpcStoreRec.
STORE_FUNCS = [
    (0x0062EFB0, 0x0062FDC0), (0x0062FDC0, 0x0062FDF0), (0x0062FE60, 0x0062FF70),
    (0x00577830, 0x00577F30), (0x00578050, 0x00578460), (0x00578460, 0x00578610),
    (0x00579510, 0x00579AA0), (0x00579C00, 0x00579D60), (0x005761C0, 0x005762B0),
    (0x00576D90, 0x00576E40),
]

# Functions whose draws items/0011 § 8 states: (start, name). The end is the first int3 after the start, except the
# price core (its jump table follows the code), the staff-mod term (no padding before the core) and MERC_Resurrect
# (no padding before NPC_MenuAction): FIXED_END.
DRAW_FUNCS = [
    (0x0062EFB0, "ITEMS_TradePriceCore"), (0x0062EDD0, "PriceStaffModTerm"), (0x00628E70, "PriceStatTerms"),
    (0x006292F0, "PriceSocketTerm"), (0x00628D30, "RechargeCost"), (0x00629370, "GamblePrice"),
    (0x0062E660, "ItemCanRepair"), (0x0062A840, "ItemHasCharges"), (0x0062E5D0, "ItemIsRepairableStack"),
    (0x0062FE60, "RepairCost"), (0x00577830, "NPC_BuyItem"), (0x00578050, "NpcRepair"),
    (0x00578460, "NPC_CainIdentify"), (0x00579510, "NPC_SellItem"), (0x00579C00, "MERC_Resurrect"),
    (0x005761C0, "ItemRepairAll"), (0x00576D90, "PayGold"), (0x006637B0, "MERC_ResurrectCost"),
    (0x005357D0, "PLAYER_DeathGoldLoss"), (0x00535510, "PlayerDropGold"), (0x0055A090, "DropGoldAmount"),
    (0x0055B060, "PlayerGiveGold"), (0x0053FF00, "UnitAddGoldStat"), (0x0055C850, "GoldPickup"),
    (0x00564D50, "StashGoldMove"), (0x00562D30, "ITEMEVENT_Replenish"), (0x00562C40, "ReplenishStep"),
    (0x0056C310, "ItemConsumeOne"), (0x0056C3F0, "PLAYER_UseAmmo"), (0x0056BEC0, "UseCharge"),
    (0x00558530, "ItemReplenishDurTimer"), (0x00558580, "ItemReplenishQtyTimer"), (0x0057D3D0, "COMBAT_DurabilityLoss"),
    (0x00559E30, "ITEMS_DurabilityLossRoll"), (0x005DAA40, "SkillWeaponWear"), (0x0055F900, "ItemRepairBroken"),
    (0x0055FE80, "ItemRefillCharges"),
]
FIXED_END = {0x0062EFB0: 0x0062FDC0, 0x0062EDD0: 0x0062EFB0, 0x00579C00: 0x00579D60}
RNG_CALLS = {0x0045C370: "RNG_Step", 0x0045C390: "RNG_Range", 0x0045C3E0: "RNG_RangeB", 0x00472210: "RNG_RangePow2",
             0x00472240: "RNG_RangePow2Plus", 0x00472280: "RNG_RangeOffset", 0x004BC500: "RNG_RandLoHi"}

LINE = re.compile(r"^\s+([0-9a-f]+):\s+(.*)$")


def disasm(exe):
    out = subprocess.run(["objdump", "-d", "-M", "intel", "--no-show-raw-insn", exe],
                         capture_output=True, text=True, check=True).stdout
    rows = []
    for ln in out.splitlines():
        m = LINE.match(ln)
        if m:
            rows.append((int(m.group(1), 16), m.group(2).strip()))
    return rows


def calls(rows):
    n = 0
    for t, name in TARGETS.items():
        pat = re.compile(r"^(call|jmp)\s+0x%x$" % t)
        sites = [a for a, ins in rows if pat.match(ins)]
        n += len(sites)
        print("CALLS %s 0x%08X %d %s" % (name, t, len(sites), " ".join("0x%08X" % a for a in sites)))
    print("SCAN calls targets=%d sites=%d" % (len(TARGETS), n))


def books(rows):
    disp = re.compile(r"\[e(?:ax|bx|cx|dx|si|di)\+0x([0-9a-f]+)\]")
    sites = 0
    for i, (a, ins) in enumerate(rows):
        if re.match(r"^call\s+0x6374b0$", ins):
            sites += 1
            seen = []
            for b, ins2 in rows[i + 1:i + 17]:
                for d in disp.findall(ins2):
                    seen.append("0x%08X:+0x%s" % (b, d))
            print("BOOKS call 0x%08X %s" % (a, " ".join(seen)))
    refs = [a for a, ins in rows if "0x96cc60" in ins or "0x96cc64" in ins]
    print("BOOKS tablerefs %s" % " ".join("0x%08X" % a for a in refs))
    print("SCAN books calls=%d tablerefs=%d" % (sites, len(refs)))


def storerec(rows):
    pat = re.compile(r"BYTE PTR \[e(ax|bx|cx|dx|si|di)\+0x(24|25|26|10|11|12)\]")
    hits = 0
    for lo, hi in STORE_FUNCS:
        for a, ins in rows:
            if lo <= a < hi and pat.search(ins):
                hits += 1
                print("STOREREC 0x%08X %s" % (a, ins))
    print("SCAN storerec funcs=%d hits=%d" % (len(STORE_FUNCS), hits))


def draws(rows):
    idx = {a: i for i, (a, _) in enumerate(rows)}
    total = 0
    for start, name in DRAW_FUNCS:
        i = idx[start] + 1
        while i < len(rows) and rows[i][1] != "int3":
            i += 1
        end = FIXED_END.get(start, rows[i][0])
        hits = []
        for a, ins in rows[idx[start]:i]:
            if a >= end:
                break
            if "0x6ac690c5" in ins:
                hits.append("0x%08X:LCG" % a)
            m = re.match(r"^call\s+0x([0-9a-f]+)$", ins)
            if m and int(m.group(1), 16) in RNG_CALLS:
                hits.append("0x%08X:%s" % (a, RNG_CALLS[int(m.group(1), 16)]))
        total += len(hits)
        print("DRAWS %s 0x%08X-0x%08X %d %s" % (name, start, end, len(hits), " ".join(hits)))
    print("SCAN draws funcs=%d hits=%d" % (len(DRAW_FUNCS), total))


def pointers(exe):
    import struct
    data = open(exe, "rb").read()
    total = 0
    for t, name in TARGETS.items():
        b = struct.pack("<I", t)
        offs, i = [], data.find(b)
        while i != -1:
            offs.append(i)
            i = data.find(b, i + 1)
        total += len(offs)
        print("PTR %s 0x%08X %d %s" % (name, t, len(offs), " ".join("file+0x%X" % o for o in offs)))
    print("SCAN pointers targets=%d hits=%d" % (len(TARGETS), total))


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 2
    rows = disasm(argv[1])
    which = argv[2] if len(argv) > 2 else "all"
    if which in ("all", "calls"):
        calls(rows)
    if which in ("all", "books"):
        books(rows)
    if which in ("all", "draws"):
        draws(rows)
    if which in ("all", "pointers"):
        pointers(argv[1])
    if which in ("all", "storerec"):
        storerec(rows)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
