"""Record layouts of compiled excel .bin tables, used by tools/excel_bin.py.

Each layout: size (record bytes), fields (list), and optionally txt (the .txt basename to diff
against, default = the table name), txt_only ({column: reason} for .txt columns that have no field
in the .bin), explain ({(column, record): reason} or {column: fn(i, cell, got) -> reason|None} for
known, documented mismatches), partial (True when the layout maps only some columns on purpose; diff
then reports the rest as outside the layout rather than as having no .bin field).

Field constructors:
  I(col, off, type, blank=0)          integer; type u8/s8/u16/s16/u32/s32; a blank cell reads as `blank`
  B(col, off, bit)                    one bit of the byte at off
  S(col, off, length)                 NUL-terminated char array of `length` bytes (blank = empty string)
  C(col, off)                         4-byte code, space padded ("hax "); blank = 4 spaces
  R(col, off, ref, int[, blank])      index into the rows of another table: ref is "table:column"
                                      or "t1:c+t2:c+..." (concatenated row lists). The cell, blank
                                      included, is looked up (first matching row); a key that is not
                                      found stores -1. `blank` overrides the value of a blank cell for
                                      the few columns that do not follow that rule.
                                      Options: distinct=True (ordinal among distinct key values),
                                      bias=N (stored index + N), fallback=V (value for a cell that
                                      does not resolve), code4=True (cell cut to 4 chars; default for
                                      itemtypes:Code), nocase=True (key matched case-insensitively)
  T(col, off)                         u16 string-table index of the key in the cell (tools/tbl.py)
  K(col, off, code)                   s32 offset into the header-less <code>.bin bytecode; -1 = blank
  E(col, off, choices, int="u8")      keyword cell stored as its position in the fixed list `choices`
                                      (a list held by the compiler, not a table); not found stores -1
  U(name, off, type)                  field with no .txt column (unknown or derived); documented, not diffed
  I(..., conv=fn, part=name)          one of several fields compiled from one cell: fn(cell, refs) gives this
                                      field's value (cubemain input/output cells, tools/cubemain.py)
  P(col, off, choices, part, int)     one cell looked up in several tables in turn: choices is a list of
                                      (tag, "table:column", distinct); part "tag" stores the tag of the
                                      first table holding the key, part "index" its row index there;
                                      not found stores -1 (monpreset Place)

A column missing from a .txt is checked against the missing-column default (excel_bin.absent_value).
split_with names the other .bin compiled from the same .txt (levels / leveldefs).

Offsets were found with `excel_bin.py probe` and are checked by `excel_bin.py diff` over every record.
"""


def I(col, off, type, blank=0, **kw):
    return dict(col=col, off=off, type=type, blank=blank, **kw)


def B(col, off, bit, **kw):
    return dict(col=col, off=off, type="bit", bit=bit, **kw)


def S(col, off, length, **kw):
    return dict(col=col, off=off, type="str", len=length, **kw)


def C(col, off, **kw):
    return dict(col=col, off=off, type="code", **kw)


def R(col, off, ref, int="u16", blank=None, **kw):
    if ref.endswith(":Code") and ref.startswith("itemtypes"):
        kw.setdefault("code4", True)
    return dict(col=col, off=off, type="ref", ref=ref, int=int, blank=blank, **kw)


def P(col, off, choices, part, int="u16", **kw):
    return dict(col=col, off=off, type="tagref", choices=choices, part=part, int=int, **kw)


def E(col, off, choices, int="u8", **kw):
    return dict(col=col, off=off, type="enum", choices=choices, int=int, **kw)


def U(name, off, type, **kw):
    d = dict(name=name, off=off, type=type, **kw)
    return d


LAYOUTS = {}

# ------------------------------------------------------------------ itemratio (68 B)
LAYOUTS["itemratio"] = dict(size=68, fields=[
    I("Unique", 0x00, "u32"), I("UniqueDivisor", 0x04, "u32"), I("UniqueMin", 0x08, "u32"),
    I("Rare", 0x0C, "u32"), I("RareDivisor", 0x10, "u32"), I("RareMin", 0x14, "u32"),
    I("Set", 0x18, "u32"), I("SetDivisor", 0x1C, "u32"), I("SetMin", 0x20, "u32"),
    I("Magic", 0x24, "u32"), I("MagicDivisor", 0x28, "u32"), I("MagicMin", 0x2C, "u32"),
    I("HiQuality", 0x30, "u32"), I("HiQualityDivisor", 0x34, "u32"),
    I("Normal", 0x38, "u32"), I("NormalDivisor", 0x3C, "u32"),
    I("Version", 0x40, "u16"), I("Uber", 0x42, "u8"), I("Class Specific", 0x43, "u8"),
], txt_only={"Function": "comment column (row description); no bytes in the record"})

# ------------------------------------------------------------------ treasureclassex (736 B)
LAYOUTS["treasureclassex"] = dict(size=736, fields=[
    S("Treasure Class", 0x000, 32),
    I("Picks", 0x020, "s32"),
    I("group", 0x024, "u16"), I("level", 0x026, "u16"),
    I("Magic", 0x028, "u16"), I("Rare", 0x02A, "u16"), I("Set", 0x02C, "u16"), I("Unique", 0x02E, "u16"),
    U("unk_30", 0x030, "u32"),
    I("NoDrop", 0x034, "u32"),
] + [S("Item%d" % (i + 1), 0x038 + 64 * i, 64) for i in range(10)]
  + [I("Prob%d" % (i + 1), 0x2B8 + 4 * i, "u32") for i in range(10)],
    txt_only={
        "SumItems": "editor helper (count of ItemN); not in the record",
        "TotalProb": "editor helper (sum of ProbN); not in the record",
        "DropChance": "editor helper (computed percentage); not in the record",
        "Term": "terminator column, 0 or blank in every row; no field found (+0x30 is 0 in every record)",
    })

# ------------------------------------------------------------------ itemtypes (228 B)
LAYOUTS["itemtypes"] = dict(size=228, fields=[
    C("Code", 0x000),
    R("Equiv1", 0x004, "itemtypes:Code", "u16"),
    R("Equiv2", 0x006, "itemtypes:Code", "u16"),
    I("Repair", 0x008, "u8"), I("Body", 0x009, "u8"),
    R("BodyLoc1", 0x00A, "bodylocs:Code", "u8"),
    R("BodyLoc2", 0x00B, "bodylocs:Code", "u8"),
    R("Shoots", 0x00C, "itemtypes:Code", "u16"),
    R("Quiver", 0x00E, "itemtypes:Code", "u16"),
    I("Throwable", 0x010, "u8"), I("Reload", 0x011, "u8"), I("ReEquip", 0x012, "u8"),
    I("AutoStack", 0x013, "u8"), I("Magic", 0x014, "u8"), I("Rare", 0x015, "u8"),
    I("Normal", 0x016, "u8"), I("Charm", 0x017, "u8"), I("Gem", 0x018, "u8"),
    I("Beltable", 0x019, "u8"), I("MaxSock1", 0x01A, "u8"), I("MaxSock25", 0x01B, "u8"),
    I("MaxSock40", 0x01C, "u8"), I("TreasureClass", 0x01D, "u8"), I("Rarity", 0x01E, "u8"),
    R("StaffMods", 0x01F, "playerclass:Code", "u8"),
    I("CostFormula", 0x020, "u8"),
    R("Class", 0x021, "playerclass:Code", "u8"),
    R("StorePage", 0x022, "storepage:Code", "u8"),
    I("VarInvGfx", 0x023, "u8"),
] + [S("InvGfx%d" % (i + 1), 0x024 + 32 * i, 32) for i in range(6)],
    txt_only={"ItemType": "display name for editors; not in the record (rows are addressed by Code / index)",
              "*eol": "end-of-line marker column"})

# ------------------------------------------------------------------ weapons / armor / misc (424 B)
# One record layout for all three item tables (the game concatenates them into one item list).
# Columns a given .txt lacks are zero-filled in its .bin (checked by diff).


def T(col, off, **kw):
    """u16 string-table index of the key in the cell (tools/tbl.py); unknown or blank key = 5382."""
    return dict(col=col, off=off, type="tbl", **kw)


def K(col, off, code, **kw):
    """s32 offset into the header-less <code>.bin bytecode file; -1 = blank cell."""
    return dict(col=col, off=off, type="calc", code=code, **kw)


VENDORS = ["Akara", "Gheed", "Charsi", "Fara", "Lysander", "Drognan", "Hralti", "Alkor", "Ormus",
           "Elzix", "Asheara", "Cain", "Halbu", "Jamella", "Malah", "Larzuk", "Drehya"]

ITEM_FIELDS = [
    S("flippyfile", 0x000, 32), S("invfile", 0x020, 32), S("uniqueinvfile", 0x040, 32), S("setinvfile", 0x060, 32),
    C("code", 0x080), C("normcode", 0x084), C("ubercode", 0x088), C("ultracode", 0x08C), C("alternategfx", 0x090),
    I("pSpell", 0x094, "u32"),
    R("state", 0x098, "states:state", "u16"),
    R("cstate1", 0x09A, "states:state", "u16"),
    R("cstate2", 0x09C, "states:state", "u16"),
    R("stat1", 0x09E, "itemstatcost:Stat", "u16"),
    R("stat2", 0x0A0, "itemstatcost:Stat", "u16"),
    R("stat3", 0x0A2, "itemstatcost:Stat", "u16"),
    K("calc1", 0x0A4, "itemscode"), K("calc2", 0x0A8, "itemscode"), K("calc3", 0x0AC, "itemscode"),
    K("len", 0x0B0, "itemscode"),
    I("spelldesc", 0x0B4, "u16"),
    T("spelldescstr", 0x0B6),
    K("spelldesccalc", 0x0B8, "itemscode"),
    C("BetterGem", 0x0BC), C("wclass", 0x0C0), C("2handedwclass", 0x0C4), C("TMogType", 0x0C8),
    I("minac", 0x0CC, "u32"), I("maxac", 0x0D0, "u32"),
    I("gamble cost", 0x0D4, "u32"), I("speed", 0x0D8, "s32"), I("bitfield1", 0x0DC, "u32"),
    I("cost", 0x0E0, "u32"), I("minstack", 0x0E4, "u32"), I("maxstack", 0x0E8, "u32"),
    I("spawnstack", 0x0EC, "u32"),
    # gemoffset: every cell 0; GEMS_Load rewrites it at run time (docs/findings/data/0004 section 3)
    I("gemoffset", 0x0F0, "s32"),
    T("namestr", 0x0F4),
    I("version", 0x0F6, "u16"), I("auto prefix", 0x0F8, "u16"), I("missiletype", 0x0FA, "u16"),
    I("rarity", 0x0FC, "u8"), I("level", 0x0FD, "u8"),
    I("mindam", 0x0FE, "u8"), I("maxdam", 0x0FF, "u8"), I("minmisdam", 0x100, "u8"), I("maxmisdam", 0x101, "u8"),
    I("2handmindam", 0x102, "u8"), I("2handmaxdam", 0x103, "u8"),
    I("rangeadder", 0x104, "s16"), I("StrBonus", 0x106, "s16"), I("DexBonus", 0x108, "s16"),
    I("reqstr", 0x10A, "u16"), I("reqdex", 0x10C, "u16"),
    I("absorbs", 0x10E, "u8"), I("invwidth", 0x10F, "u8"), I("invheight", 0x110, "u8"), I("block", 0x111, "u8"),
    I("durability", 0x112, "u8"), I("nodurability", 0x113, "u8"),
    I("missile", 0x114, "u8"),  # column in no shipped .txt (missing-column default 0), data/0004
    I("component", 0x115, "u8"),
    I("rArm", 0x116, "u8"), I("lArm", 0x117, "u8"), I("Torso", 0x118, "u8"), I("Legs", 0x119, "u8"),
    I("rSPad", 0x11A, "u8"), I("lSPad", 0x11B, "u8"),
    I("2handed", 0x11C, "u8"), I("useable", 0x11D, "u8"),
    R("type", 0x11E, "itemtypes:Code", "u16"),
    R("type2", 0x120, "itemtypes:Code", "u16"),
    I("subtype", 0x122, "u8"),  # column in no shipped .txt (missing-column default 0), data/0004
    U("pad_123", 0x123, "u8"),
    R("dropsound", 0x124, "sounds:Sound", "u16"),
    R("usesound", 0x126, "sounds:Sound", "u16"),
    I("dropsfxframe", 0x128, "u8"), I("unique", 0x129, "u8"), I("quest", 0x12A, "u8"),
    I("questdiffcheck", 0x12B, "u8"), I("transparent", 0x12C, "u8"), I("transtbl", 0x12D, "u8"),
    U("pad_12E", 0x12E, "u8"),
    I("lightradius", 0x12F, "u8"), I("belt", 0x130, "u8"), I("autobelt", 0x131, "u8"),
    I("stackable", 0x132, "u8"), I("spawnable", 0x133, "u8"), I("spellicon", 0x134, "s8"),
    I("durwarning", 0x135, "u8"), I("qntwarning", 0x136, "u8"), I("hasinv", 0x137, "u8"),
    I("gemsockets", 0x138, "u8"), I("Transmogrify", 0x139, "u8"), I("TMogMin", 0x13A, "u8"), I("TMogMax", 0x13B, "u8"),
    R("hit class", 0x13C, "hitclass:Code", "u8"),
    I("1or2handed", 0x13D, "u8"), I("gemapplytype", 0x13E, "u8"), I("levelreq", 0x13F, "u8"),
    I("magic lvl", 0x140, "u8"), I("Transform", 0x141, "u8"), I("InvTrans", 0x142, "u8"),
    I("compactsave", 0x143, "u8"), I("SkipName", 0x144, "u8"), I("Nameable", 0x145, "u8"),
] + [I(v + "Min", 0x146 + i, "u8") for i, v in enumerate(VENDORS)] \
  + [I(v + "Max", 0x157 + i, "u8") for i, v in enumerate(VENDORS)] \
  + [I(v + "MagicMin", 0x168 + i, "u8") for i, v in enumerate(VENDORS)] \
  + [I(v + "MagicMax", 0x179 + i, "u8") for i, v in enumerate(VENDORS)] \
  + [I(v + "MagicLvl", 0x18A + i, "u8") for i, v in enumerate(VENDORS)] + [
    U("pad_19B", 0x19B, "u8"),
    C("NightmareUpgrade", 0x19C), C("HellUpgrade", 0x1A0),
    I("PermStoreItem", 0x1A4, "u8"), I("multibuy", 0x1A5, "u8"),
    U("pad_1A6", 0x1A6, "u16"),
]

ITEM_TXT_ONLY = {
    "name": "editor name; the record holds the namestr string index instead",
    "*name": "comment column",
    "OpenBetaGfx": "obsolete art code; no field matches",
    "special": "free-text note (\"primarily thrown\", ...); not compiled",
    "#col18": "unnamed weapons.txt column 18 (values 13..19); not compiled",
    "Source Art": "editor note; blank",
    "Game Art": "editor note; blank or a single space",
    "szFlavorText": "blank in every misc row; no field identified",
    "quivered": "weapons: 1 on 42 bows/crossbows, but no byte or bit in the record follows it; not compiled",
    "throwable": "0 in every armor/misc row; not located (weapons.txt has no such column)",
    "spelloffset": "armor: 0 in every row; not located",
    "mindam#2": "armor.txt repeats the header mindam; the first occurrence feeds +0x0FE, this one is 0 in every row",
    "maxdam#2": "armor.txt repeats the header maxdam; the first occurrence feeds +0x0FF, this one is 0 in every row",
    "HratliMagicLvl": "misspelled header in weapons/armor: the field HraltiMagicLvl +0x190 stays 0 (column not found)",
}

for _t in ("weapons", "armor", "misc"):
    LAYOUTS[_t] = dict(size=424, fields=ITEM_FIELDS, txt_only=ITEM_TXT_ONLY)

# ------------------------------------------------------------------ monstats (424 B)
# TC columns store (treasureclassex row + 161): runtime TC 0 is empty and 1-160 are the auto item-type
# TCs built at load (docs/findings/data/0001-excel-loader.md section 7). Monster self-references use the
# ordinal among distinct Id values.
MON_TC = "treasureclassex:Treasure Class"
_D = ["", "(N)", "(H)"]


def _tri(name, off, type, step=None, **kw):
    """name, name(N), name(H) at off, off+size, off+2*size (or a given step)."""
    from excel_bin import INT_SIZE
    n = step or INT_SIZE[type]
    return [I(name + d, off + n * k, type, **kw) for k, d in enumerate(_D)]


_MON_BITS = [
    (0x0C, ["isSpawn", "isMelee", "noRatio", "opendoors", "SetBoss", "BossXfer", "boss", "primeevil"]),
    (0x0D, ["npc", "interact", "inTown", "lUndead", "hUndead", "demon", "flying", "killable"]),
    (0x0E, ["switchai", "nomultishot", "neverCount", "petIgnore", "deathDmg", "genericSpawn", "zoo", "placespawn"]),
    (0x0F, ["inventory", "enabled", "NoShldBlock", "noAura", "rangedtype"]),
]

MONSTATS_FIELDS = [
    R("Id", 0x000, "monstats:Id", "u16", distinct=True),
    R("BaseId", 0x002, "monstats:Id", "u16", distinct=True),
    R("NextInClass", 0x004, "monstats:Id", "u16", distinct=True),
    T("NameStr", 0x006), T("DescStr", 0x008),
    U("pad_00A", 0x00A, "u16"),  # no descriptor entry, no writer (data/0004); also +0x00F bits 5-7
] + [B(c, off, b) for off, cols in _MON_BITS for b, c in enumerate(cols)] + [
    C("Code", 0x010),
    R("MonSound", 0x014, "monsounds:Id", "u16"),
    R("UMonSound", 0x016, "monsounds:Id", "u16"),
    R("MonStatsEx", 0x018, "monstats2:Id", "u16"),
    R("MonProp", 0x01A, "monprop:Id", "u16"),
    R("MonType", 0x01C, "montype:type", "u16"),
    R("AI", 0x01E, "monai:AI", "u16"),
    R("spawn", 0x020, "monstats:Id", "u16", distinct=True),
    I("spawnx", 0x022, "s8"), I("spawny", 0x023, "s8"),
    R("spawnmode", 0x024, "monmode:code", "u8"),
    U("pad_025", 0x025, "u8"),
    R("minion1", 0x026, "monstats:Id", "u16", distinct=True),
    R("minion2", 0x028, "monstats:Id", "u16", distinct=True),
    U("MonEquipRow", 0x02A, "s16"),  # first monequip row of the class, -1 none; MONEQUIP_Load (data/0004)
    I("PartyMin", 0x02C, "u8"), I("PartyMax", 0x02D, "u8"), I("Rarity", 0x02E, "u8"),
    I("MinGrp", 0x02F, "u8"), I("MaxGrp", 0x030, "u8"), I("sparsePopulate", 0x031, "u8"),
    I("Velocity", 0x032, "u16"), I("Run", 0x034, "u16"),
    U("WalkDerived", 0x036, "s16"), U("RunDerived", 0x038, "s16"),  # sub_00650F00_MonStatsSpeeds (data/0004)
] + [R(c, 0x03A + 2 * k, "missiles:Missile", "u16")
     for k, c in enumerate(["MissA1", "MissA2", "MissS1", "MissS2", "MissS3", "MissS4", "MissC", "MissSQ"])] + [
    U("ClassChainLen", 0x04A, "u8"), U("ClassChainPos", 0x04B, "u8"),  # sub_00651040_MonClassChain (data/0004)
    I("Align", 0x04C, "u8"), I("TransLvl", 0x04D, "u8"), I("threat", 0x04E, "u8"),
] + _tri("aidel", 0x04F, "u8") + _tri("aidist", 0x052, "u8") + [
    U("pad_055", 0x055, "u8"),
] + [f for k in range(8) for f in _tri("aip%d" % (k + 1), 0x056 + 6 * k, "u16")] + [
    R(c, 0x086 + 2 * k, MON_TC, "u16", 0, bias=161)
    for k, c in enumerate(["TreasureClass%d%s" % (n, d) for d in _D for n in (1, 2, 3, 4)])
] + [
    I("TCQuestId", 0x09E, "u8"), I("TCQuestCP", 0x09F, "u8"),
] + _tri("Drain", 0x0A0, "u8") + _tri("ToBlock", 0x0A3, "u8") + [
    I("Crit", 0x0A6, "u8"), U("pad_0A7", 0x0A7, "u8"),
    R("SkillDamage", 0x0A8, "skills:skill", "u16"),
    I("Level", 0x0AA, "u16"), I("Level(N)", 0x0AC, "u16"), I("Level(H)", 0x0AE, "u16"),
    I("minHP", 0x0B0, "u16"), I("MinHP(N)", 0x0B2, "u16"), I("MinHP(H)", 0x0B4, "u16"),
    I("maxHP", 0x0B6, "u16"), I("MaxHP(N)", 0x0B8, "u16"), I("MaxHP(H)", 0x0BA, "u16"),
] + _tri("AC", 0x0BC, "u16") + _tri("A1TH", 0x0C2, "u16") + _tri("A2TH", 0x0C8, "u16") \
  + _tri("S1TH", 0x0CE, "u16") + _tri("Exp", 0x0D4, "u16") \
  + _tri("A1MinD", 0x0DA, "u16") + _tri("A1MaxD", 0x0E0, "u16") \
  + _tri("A2MinD", 0x0E6, "u16") + _tri("A2MaxD", 0x0EC, "u16") \
  + _tri("S1MinD", 0x0F2, "u16") + _tri("S1MaxD", 0x0F8, "u16") + [
    R("El1Mode", 0x0FE, "monmode:code", "u8"),
    R("El2Mode", 0x0FF, "monmode:code", "u8"),
    R("El3Mode", 0x100, "monmode:code", "u8"),
    R("El1Type", 0x101, "elemtypes:Code", "u8"),
    R("El2Type", 0x102, "elemtypes:Code", "u8"),
    R("El3Type", 0x103, "elemtypes:Code", "u8"),
] + [f for e in (1, 2, 3) for f in _tri("El%dPct" % e, 0x104 + 3 * (e - 1), "u8")] + [
    U("pad_10D", 0x10D, "u8"),
] + [f for e in (1, 2, 3) for f in _tri("El%dMinD" % e, 0x10E + 6 * (e - 1), "u16")] \
  + [f for e in (1, 2, 3) for f in _tri("El%dMaxD" % e, 0x120 + 6 * (e - 1), "u16")] \
  + [f for e in (1, 2, 3) for f in _tri("El%dDur" % e, 0x132 + 6 * (e - 1), "u16")] \
  + [f for k, r in enumerate(["Dm", "Ma", "Fi", "Li", "Co", "Po"]) for f in _tri("Res" + r, 0x144 + 6 * k, "s16")] \
  + _tri("coldeffect", 0x168, "s8") + [
    U("pad_16B", 0x16B, "u8"),
    I("SendSkills", 0x16C, "u32"),
] + [R("Skill%d" % (k + 1), 0x170 + 2 * k, "skills:skill", "u16") for k in range(8)] \
  + [R("Sk%dmode" % (k + 1), 0x180 + k, "monmode:code", "u8", 0, fallback=14) for k in range(8)] \
  + [dict(R("Sk%dmode" % (k + 1), 0x188 + 2 * k, "monseq:sequence", "s16", -1, distinct=True, fallback=-1),
          name="Sk%dseq" % (k + 1)) for k in range(8)] \
  + [I("Sk%dlvl" % (k + 1), 0x198 + k, "u8") for k in range(8)] + [
    I("DamageRegen", 0x1A0, "u32"),
    I("SplEndDeath", 0x1A4, "u8"), I("SplGetModeChart", 0x1A5, "u8"),
    I("SplEndGeneric", 0x1A6, "u8"), I("SplClientEnd", 0x1A7, "u8"),
]

LAYOUTS["monstats"] = dict(
    size=424, fields=MONSTATS_FIELDS,
    txt_only={"hcIdx": "editor row number; +0x000 is the distinct-Id ordinal instead (differs after the duplicate Id cr_lancer8)",
              "*eol": "end-of-line marker column"},
    explain={("NameStr", 707): "uberandariel 'Lilith': the .bin holds 5382 (key not found) although the shipped "
                               "patchstring.tbl has the key at 11154 (probably compiled against an older patchstring.tbl)"})

# ------------------------------------------------------------------ lvlprest (432 B)
# One record per LvlPrest.txt row. File1..6 are DS1 paths relative to data/global/tiles
# (tools/ds1.py lvlprest resolves them).
LAYOUTS["lvlprest"] = dict(size=432, fields=[
    I("Def", 0x000, "u32"), I("LevelId", 0x004, "u32"),
    I("Populate", 0x008, "u32"), I("Logicals", 0x00C, "u32"), I("Outdoors", 0x010, "u32"),
    I("Animate", 0x014, "u32"), I("KillEdge", 0x018, "u32"), I("FillBlanks", 0x01C, "u32"),
    I("Expansion", 0x020, "u32"),
    U("unk_024", 0x024, "u32"),
    I("SizeX", 0x028, "s32"), I("SizeY", 0x02C, "s32"), I("AutoMap", 0x030, "u32"), I("Scan", 0x034, "u32"),
    I("Pops", 0x038, "u32"), I("PopPad", 0x03C, "s32"), I("Files", 0x040, "u32"),
] + [S("File%d" % (i + 1), 0x044 + 60 * i, 60) for i in range(6)] + [
    I("Dt1Mask", 0x1AC, "u32"),
], txt_only={"Name": "editor name; not in the record (rows are addressed by Def / row index)",
             "Beta": "no field in lvlprest.bin matches it"})

# ------------------------------------------------------------------ lvlwarp (48 B)
# Direction is one char ('b'/'l'/'r') in a 4-byte slot; the 3 bytes after it are 0 in every record.
LAYOUTS["lvlwarp"] = dict(size=48, fields=[
    I("Id", 0x000, "s32"), I("SelectX", 0x004, "s32"), I("SelectY", 0x008, "s32"),
    I("SelectDX", 0x00C, "s32"), I("SelectDY", 0x010, "s32"),
    I("ExitWalkX", 0x014, "s32"), I("ExitWalkY", 0x018, "s32"),
    I("OffsetX", 0x01C, "s32"), I("OffsetY", 0x020, "s32"),
    I("LitVersion", 0x024, "u32"), I("Tiles", 0x028, "u32"),
    S("Direction", 0x02C, 1),
    U("pad_02D", 0x02D, "u8"), U("pad_02E", 0x02E, "u16"),
], txt_only={"Name": "editor name; not in the record",
             "Beta": "no field in lvlwarp.bin matches it"})

# ------------------------------------------------------------------ levels (544 B) + leveldefs (156 B)
# Both .bin files have one record per Levels.txt row (Expansion marker dropped); each column of
# Levels.txt lands in exactly one of them. Monster columns store the distinct-Id ordinal of monstats.
_MON = "monstats:Id"

LAYOUTS["levels"] = dict(size=544, fields=[
    I("Id", 0x000, "u8"), U("pad_001", 0x001, "u8"),  # Id compiled as a u8; +0x001 never written (data/0004)
    I("Pal", 0x002, "u8"), I("Act", 0x003, "u8"),
    I("Teleport", 0x004, "u8"), I("Rain", 0x005, "u8"), I("Mud", 0x006, "u8"), I("NoPer", 0x007, "u8"),
    I("IsInside", 0x008, "u8"), I("DrawEdges", 0x009, "u8"),
    U("pad_00A", 0x00A, "u16"),
    I("WarpDist", 0x00C, "u32"),
    I("MonLvl1", 0x010, "u16"), I("MonLvl2", 0x012, "u16"), I("MonLvl3", 0x014, "u16"),
    I("MonLvl1Ex", 0x016, "u16"), I("MonLvl2Ex", 0x018, "u16"), I("MonLvl3Ex", 0x01A, "u16"),
    I("MonDen", 0x01C, "u32"), I("MonDen(N)", 0x020, "u32"), I("MonDen(H)", 0x024, "u32"),
    I("MonUMin", 0x028, "u8"), I("MonUMin(N)", 0x029, "u8"), I("MonUMin(H)", 0x02A, "u8"),
    I("MonUMax", 0x02B, "u8"), I("MonUMax(N)", 0x02C, "u8"), I("MonUMax(H)", 0x02D, "u8"),
    I("MonWndr", 0x02E, "u8"), I("MonSpcWalk", 0x02F, "u8"), I("Quest", 0x030, "u8"),
    I("rangedspawn", 0x031, "u8"), I("NumMon", 0x032, "u8"),
    U("unk_033", 0x033, "u8"), U("unk_034", 0x034, "u16"),
] + [R("mon%d" % (k + 1), 0x036 + 2 * k, _MON, "u16", distinct=True) for k in range(10)]
  + [U("mon%d" % (k + 1), 0x036 + 2 * k, "u16") for k in range(10, 25)]
  + [R("nmon%d" % (k + 1), 0x068 + 2 * k, _MON, "u16", distinct=True) for k in range(10)]
  + [U("nmon%d" % (k + 1), 0x068 + 2 * k, "u16") for k in range(10, 25)]
  + [R("umon%d" % (k + 1), 0x09A + 2 * k, _MON, "u16", distinct=True) for k in range(10)]
  + [U("umon%d" % (k + 1), 0x09A + 2 * k, "u16") for k in range(10, 25)]
  + [R("cmon%d" % (k + 1), 0x0CC + 2 * k, _MON, "u16", distinct=True) for k in range(4)]
  + [I("cpct%d" % (k + 1), 0x0D4 + 2 * k, "u16") for k in range(4)]
  # camt1..camt4 are four descriptor entries that all write +0x0DC (the last camt column present wins);
  # +0x0DE..+0x0E3 are never compiled, though the critter code reads +0x0DC + 2k (data/0004)
  + [I("camt%d" % (k + 1), 0x0DC, "s16") for k in range(4)]
  + [U("camt_unwritten_%d" % (k + 2), 0x0DE + 2 * k, "s16") for k in range(3)] + [
    I("Waypoint", 0x0E4, "u8"),
] + [I("ObjGrp%d" % k, 0x0E5 + k, "u8") for k in range(8)] \
  + [I("ObjPrb%d" % k, 0x0ED + k, "u8") for k in range(8)] + [
    S("LevelName", 0x0F5, 40), S("LevelWarp", 0x11D, 40), S("EntryFile", 0x145, 40),
    U("pad_16D", 0x16D, "u8"),
    # localised LevelName / LevelWarp text, wchar[40] each, written by DRLG_LoadLevels (data/0004)
    U("LevelNameText", 0x16E, "str", len=80), U("LevelWarpText", 0x1BE, "str", len=80),
    U("pad_20E", 0x20E, "u16"),
    I("Themes", 0x210, "u32"), I("FloorFilter", 0x214, "u32"), I("BlankScreen", 0x218, "u32"),
    I("SoundEnv", 0x21C, "u32"),
], txt_only={"Name": "editor name; not in the record (rows are addressed by Id / row index)",
             "Beta": "no field in levels.bin or leveldefs.bin matches it"},
   split_with="leveldefs")

LAYOUTS["leveldefs"] = dict(size=156, txt="levels", fields=[
    I("QuestFlag", 0x000, "u32"), I("QuestFlagEx", 0x004, "u32"), I("Layer", 0x008, "u32"),
    I("SizeX", 0x00C, "s32"), I("SizeX(N)", 0x010, "s32"), I("SizeX(H)", 0x014, "s32"),
    I("SizeY", 0x018, "s32"), I("SizeY(N)", 0x01C, "s32"), I("SizeY(H)", 0x020, "s32"),
    I("OffsetX", 0x024, "s32"), I("OffsetY", 0x028, "s32"), I("Depend", 0x02C, "u32"),
    I("DrlgType", 0x030, "u32"), I("LevelType", 0x034, "u32"),
    I("SubType", 0x038, "s32"), I("SubTheme", 0x03C, "s32"), I("SubWaypoint", 0x040, "s32"), I("SubShrine", 0x044, "s32"),
] + [I("Vis%d" % k, 0x048 + 4 * k, "s32") for k in range(8)]
  + [I("Warp%d" % k, 0x068 + 4 * k, "s32") for k in range(8)] + [
    I("Intensity", 0x088, "u8"), I("Red", 0x089, "u8"), I("Green", 0x08A, "u8"), I("Blue", 0x08B, "u8"),
    I("Portal", 0x08C, "u32"), I("Position", 0x090, "u32"), I("SaveMonsters", 0x094, "u32"), I("LOSDraw", 0x098, "u32"),
], txt_only={"Name": "editor name; not in the record",
             "Beta": "no field in levels.bin or leveldefs.bin matches it"},
   split_with="levels")

# ------------------------------------------------------------------ magicprefix / magicsuffix / automagic (144 B)
# Shared affix layout, learned from magicprefix/magicsuffix (.txt and .bin both from patch_d2) and used
# to diff automagic (.txt from d2exp, .bin from patch_d2).
_IT = "itemtypes:Code"
AFFIX_FIELDS = [
    S("Name", 0x000, 34), I("version", 0x022, "u16"),
] + [f for k in range(3) for f in (
    R("mod%dcode" % (k + 1), 0x024 + 16 * k, "properties:code", "u32"),
    I("mod%dparam" % (k + 1), 0x028 + 16 * k, "s32"),
    I("mod%dmin" % (k + 1), 0x02C + 16 * k, "s32"),
    I("mod%dmax" % (k + 1), 0x030 + 16 * k, "s32"))] + [
    I("spawnable", 0x054, "u16"),
    R("transformcolor", 0x056, "colors:Code", "u8"),
    U("unk_057", 0x057, "u8"),
    I("level", 0x058, "u32"), I("group", 0x05C, "u32"), I("maxlevel", 0x060, "u32"),
    I("rare", 0x064, "u8"), I("levelreq", 0x065, "u8"),
    R("classspecific", 0x066, "playerclass:Code", "u8"),
    R("class", 0x067, "playerclass:Code", "u8"),
    I("classlevelreq", 0x068, "u16"),
] + [R("itype%d" % (k + 1), 0x06A + 2 * k, _IT, "u16") for k in range(7)] \
  + [R("etype%d" % (k + 1), 0x078 + 2 * k, _IT, "u16") for k in range(5)] + [
    I("frequency", 0x082, "u16"),
    I("divide", 0x084, "u32"), I("multiply", 0x088, "u32"), I("add", 0x08C, "u32"),
]
_AFFIX_TXT_ONLY = {"transform": "1 on many rows but no byte or bit follows it (+0x057 is 0 in every record)"}
for _t in ("magicprefix", "magicsuffix", "automagic"):
    LAYOUTS[_t] = dict(size=144, fields=AFFIX_FIELDS, txt_only=_AFFIX_TXT_ONLY)

# ------------------------------------------------------------------ RarePrefix / RareSuffix (72 B)
# .txt from d2exp, .bin from patch_d2 (re-compiled at 72 B; the d2exp .bin had 60-byte records).
# version (0 in every row) sits where ITEMS_RareNameTypeOk reads it, +0x00E (findings/items/0005 section 6); the
# data alone cannot place it. +0x00C is the string key of name, written by the loader (0 in the file).
RARE_FIELDS = [
    U("unk_000", 0x000, "u32"), U("unk_004", 0x004, "u32"), U("unk_008", 0x008, "u32"), U("strkey_00C", 0x00C, "u16"),
    I("version", 0x00E, "u16"),
] + [R("itype%d" % (k + 1), 0x010 + 2 * k, _IT, "u16") for k in range(7)] \
  + [R("etype%d" % (k + 1), 0x01E + 2 * k, _IT, "u16") for k in range(4)] + [
    S("name", 0x026, 34),
]
_RARE_TXT_ONLY = {
    "add": "not located (+0x000..+0x00D are 0 in every record)",
    "multiply": "not located (+0x000..+0x00D are 0 in every record)",
    "divide": "not located (+0x000..+0x00D are 0 in every record)",
}
for _t in ("rareprefix", "raresuffix"):
    LAYOUTS[_t] = dict(size=72, fields=RARE_FIELDS, txt_only=_RARE_TXT_ONLY)

# ------------------------------------------------------------------ itemstatcost (324 B = 0x144)
# Plan 0024 Phase 0 (docs/tables/ItemStatCost.md). One record per itemstatcost.txt row (359, no Expansion
# marker); ID equals the row index and is the stat id. Offsets from `excel_bin.py probe`; widths from the
# next field. The flag columns are bits of +0x004 and +0x005. CSvParam (blank in every row) and CSvSigned
# (blank or 0) match any always-zero byte, so the data cannot place them: their slots are where the code
# reads them (+0x00B, +0x005 bit 5; findings/save/0001 section 7). dgrpstr2 is blank in every row; its slot
# follows the stride of dgrpstrpos/dgrpstrneg. +0x05E..+0x13F (226 B) has no .txt column (0 in every record).
_STAT = "itemstatcost:Stat"
LAYOUTS["itemstatcost"] = dict(size=0x144, fields=[
    I("ID", 0x000, "u16"),
    U("unk_002", 0x002, "u16"),
    B("Send Other", 0x004, 0), B("Signed", 0x004, 1), B("damagerelated", 0x004, 2), B("itemspecific", 0x004, 3),
    B("direct", 0x004, 4),
    B("UpdateAnimRate", 0x005, 1), B("fMin", 0x005, 2), B("fCallback", 0x005, 3), B("Saved", 0x005, 4),
    B("CSvSigned", 0x005, 5),
    U("unk_006", 0x006, "u16"),
    I("Send Bits", 0x008, "u8"), I("Send Param Bits", 0x009, "u8"),
    I("CSvBits", 0x00A, "u8"), I("CSvParam", 0x00B, "u8"),
    I("Divide", 0x00C, "s32"), I("Multiply", 0x010, "s32"), I("Add", 0x014, "s32"),
    I("ValShift", 0x018, "u8"), I("Save Bits", 0x019, "u8"), I("1.09-Save Bits", 0x01A, "u8"),
    U("pad_01B", 0x01B, "u8"),
    I("Save Add", 0x01C, "s32"), I("1.09-Save Add", 0x020, "s32"),
    I("Save Param Bits", 0x024, "u32"),
    U("unk_028", 0x028, "u32"),
    I("MinAccr", 0x02C, "u32"),
    I("Encode", 0x030, "u16"),
    R("maxstat", 0x032, _STAT, "u16"),
    I("descpriority", 0x034, "u16"),
    I("descfunc", 0x036, "u8"), I("descval", 0x037, "u8"),
    T("descstrpos", 0x038), T("descstrneg", 0x03A), T("descstr2", 0x03C),
    I("dgrp", 0x03E, "u16"),
    I("dgrpfunc", 0x040, "u8"), I("dgrpval", 0x041, "u8"),
    T("dgrpstrpos", 0x042), T("dgrpstrneg", 0x044), T("dgrpstr2", 0x046),
    R("itemevent1", 0x048, "events:event", "u16"), R("itemevent2", 0x04A, "events:event", "u16"),
    I("itemeventfunc1", 0x04C, "u16"), I("itemeventfunc2", 0x04E, "u16"),
    I("keepzero", 0x050, "u32"),
    I("op", 0x054, "u8"), I("op param", 0x055, "u8"),
    R("op base", 0x056, _STAT, "u16"),
    R("op stat1", 0x058, _STAT, "u16"), R("op stat2", 0x05A, _STAT, "u16"), R("op stat3", 0x05C, _STAT, "u16"),
    U("unk_05E", 0x05E, "str", len=0x140 - 0x05E),
    I("stuff", 0x140, "u32"),
], txt_only={"Stat": "key (stat name); the record holds ID (= row index), which other tables store",
             "*eol": "end-of-line marker column"})

# ------------------------------------------------------------------ properties (46 B = 0x2E)
# Plan 0024 Phase 0 (docs/tables/Properties.md). One record per properties.txt row (268; the Expansion
# marker has none). code is stored as the row's own index. Seven (set, val, func, stat) slots in four
# parallel arrays: set1..7 u8 at +0x002, val1..7 at +0x00A (2 B each), func1..7 u8 at +0x018, stat1..7 u16
# itemstatcost row indices at +0x020 (blank = 0xFFFF). Only set1, val1 and func1..7/stat1..7 hold values;
# set2..7 and val2..7 are blank in every row, so their slots follow the stride of the array.
LAYOUTS["properties"] = dict(size=0x2E, fields=[
    R("code", 0x000, "properties:code", "u16"),
] + [I("set%d" % (k + 1), 0x002 + k, "u8") for k in range(7)] + [
    U("pad_009", 0x009, "u8"),
] + [I("val%d" % (k + 1), 0x00A + 2 * k, "s16") for k in range(7)]
  + [I("func%d" % (k + 1), 0x018 + k, "u8") for k in range(7)] + [
    U("pad_01F", 0x01F, "u8"),
] + [R("stat%d" % (k + 1), 0x020 + 2 * k, _STAT, "u16") for k in range(7)],
    txt_only={"*done": "editor progress column (1 or blank); not in the record",
              "*desc": "comment column; not in the record", "*param": "comment column; not in the record",
              "*min": "comment column; not in the record", "*max": "comment column; not in the record",
              "*notes": "comment column; not in the record", "*eol": "end-of-line marker column"})

# ------------------------------------------------------------------ lvltypes (1928 B = 0x788)
# One record per LvlTypes.txt row. File 1..32 are DT1 paths relative to data/global/tiles, 0x3C
# apart from +0x000, matching DRLG_LoadLvlTypes / DRLG_LevelDt1ListBuild (docs/findings/drlg/0001).
# tools/dt1.py lvltypes prints one type's paths.
LAYOUTS["lvltypes"] = dict(size=0x788, fields=[
    S("File %d" % (i + 1), 0x3C * i, 0x3C) for i in range(32)
] + [
    # Act a u8 (+0x781..+0x783 never written), Expansion an s32 (data/0004)
    I("Act", 0x780, "u8"), U("pad_781", 0x781, "str", len=3), I("Expansion", 0x784, "s32"),
], txt_only={"Name": "editor name; not in the record (rows are addressed by row index)",
             "Id": "equals the row index in every row; no field in lvltypes.bin holds it",
             "Beta": "no field in lvltypes.bin matches it"})

# ------------------------------------------------------------------ lvlmaze (28 B = 0x1C)
# One record per lvlmaze.txt row (Expansion marker dropped). Every byte is covered.
LAYOUTS["lvlmaze"] = dict(size=0x1C, fields=[
    I("Level", 0x000, "u32"),
    I("Rooms", 0x004, "u32"), I("Rooms(N)", 0x008, "u32"), I("Rooms(H)", 0x00C, "u32"),
    I("SizeX", 0x010, "u32"), I("SizeY", 0x014, "u32"), I("Merge", 0x018, "u32"),
], txt_only={"Name": "editor name; not in the record (rows are addressed by Level / row index)",
             "Beta": "no field in lvlmaze.bin matches it"})

# ------------------------------------------------------------------ lvlsub (348 B = 0x15C)
# One record per LvlSub.txt row (Expansion marker dropped). The .bin does not follow .txt column
# order: Dt1Mask (+0x048) precedes GridSize (+0x04C), and Prob0..4 / Trials0..4 / Max0..4 are grouped
# per column rather than interleaved per theme. +0x050..+0x11B holds no .txt column (zero in every
# record; drlg/0002 reads +0x050 as the run-time DS1 pointer). File is a DS1 path relative to
# data/global/tiles. CheckAll is 0 in every row, so its offset (+0x040) is the code's, not probe's.
LAYOUTS["lvlsub"] = dict(size=0x15C, fields=[
    I("Type", 0x000, "u32"), S("File", 0x004, 0x3C), I("CheckAll", 0x040, "u32"),
    I("BordType", 0x044, "s32"), I("Dt1Mask", 0x048, "u32"), I("GridSize", 0x04C, "u32"),
    U("unk_050", 0x050, "u32"),
] + [I("Prob%d" % t, 0x11C + 4 * t, "u32") for t in range(5)]
  + [I("Trials%d" % t, 0x130 + 4 * t, "s32") for t in range(5)]
  + [I("Max%d" % t, 0x144 + 4 * t, "u32") for t in range(5)] + [
    I("Expansion", 0x158, "u32"),
], txt_only={"Name": "editor name; not in the record (rows are addressed by Type / row index)",
             "Beta": "no field in lvlsub.bin matches it"})

# ------------------------------------------------------------------ uniqueitems (332 B), partial
# Plan 0009 Phase 2: the identity and art head of the record (+0x000..+0x08B) only. The prop1..12
# block (+0x08C..+0x14B, 12 x 16 B) is out of scope (items/uniques work); `partial` makes diff list
# those columns as out of scope instead of "no .bin field". Offsets from `excel_bin.py probe`.
# Plan 0019 Phase 1 (docs/findings/items/0004-uniques-sets.md section 7): +0x000 (row index) and
# +0x022 (string key of index) are written at load, so index is char[32]; nolimit is flag bit 1
# (read by ITEMS_UniqueMarkMade, section 3.3; blank in every row, so placed by code, not by data);
# lvl is read as s16 (movsx, section 3.2).
LAYOUTS["uniqueitems"] = dict(size=332, partial=True, fields=[
    U("rowIndex", 0x000, "u16"),
    S("index", 0x002, 32),
    U("nameKey", 0x022, "u16"),
    I("version", 0x024, "u32"),
    C("code", 0x028),
    B("enabled", 0x02C, 0), B("nolimit", 0x02C, 1), B("carry1", 0x02C, 2), B("ladder", 0x02C, 3),
    I("rarity", 0x030, "u32"),
    I("lvl", 0x034, "s16"), I("lvl req", 0x036, "u16"),
    R("chrtransform", 0x038, "colors:Code", "u8"),
    R("invtransform", 0x039, "colors:Code", "u8"),
    S("flippyfile", 0x03A, 32), S("invfile", 0x05A, 32),
    U("unk_07A", 0x07A, "u16"),
    I("cost mult", 0x07C, "u32"), I("cost add", 0x080, "u32"),
    R("dropsound", 0x084, "sounds:Sound", "u16", blank=0),
    R("usesound", 0x086, "sounds:Sound", "u16", blank=0),
    I("dropsfxframe", 0x088, "u32"),
])

# ------------------------------------------------------------------ setitems (440 B)
# Same head shape as uniqueitems, shifted. Property block (plan 0024 Phase 1, items/0006 section 2):
# 16-byte (code s32, par s32, min s32, max s32) blocks, prop1..9 at +0x088, then aprop1a, aprop1b, ...,
# aprop5b at +0x118; a blank code stores -1, a code is matched case-insensitively (row 122 `Light`).
# A par cell holding a skill name stores that skill's row index (field option names=, as runes T1Param).
# chrtransform/invtransform are equal in every row, and flippyfile/invfile/dropsound/usesound/
# dropsfxframe are blank in every row, so their order within their slots follows uniqueitems and the
# .txt, not the data (docs/tables/SetItems.md).
# Plan 0019 Phase 1 (items/0004 section 7): +0x000 row index, +0x022 the set's version copied at
# load, +0x024 string key of index, +0x02E member slot are written at load (0 in the file); index is
# char[32], set a u16, lvl read as s16 (movsx, section 4).
LAYOUTS["setitems"] = dict(size=440, fields=[
    U("rowIndex", 0x000, "u16"),
    S("index", 0x002, 32),
    U("setVersion", 0x022, "u16"), U("nameKey", 0x024, "u16"), U("unk_026", 0x026, "u16"),
    C("item", 0x028),
    R("set", 0x02C, "sets:index", "u16"),
    U("memberSlot", 0x02E, "u16"),
    I("lvl", 0x030, "s16"), I("lvl req", 0x032, "u16"),
    I("rarity", 0x034, "u32"),
    I("cost mult", 0x038, "u32"), I("cost add", 0x03C, "u32"),
    R("chrtransform", 0x040, "colors:Code", "u8"),
    R("invtransform", 0x041, "colors:Code", "u8"),
    S("flippyfile", 0x042, 32), S("invfile", 0x062, 32),
    R("dropsound", 0x082, "sounds:Sound", "u16", blank=0),
    R("usesound", 0x084, "sounds:Sound", "u16", blank=0),
    I("dropsfxframe", 0x086, "u8"),
    I("add func", 0x087, "u8"),
] + [f for k in range(9) for f in (
    R("prop%d" % (k + 1), 0x088 + 16 * k, "properties:code", "s32", nocase=True),
    I("par%d" % (k + 1), 0x08C + 16 * k, "s32", names="skills:skill"),
    I("min%d" % (k + 1), 0x090 + 16 * k, "s32"),
    I("max%d" % (k + 1), 0x094 + 16 * k, "s32"))
] + [f for k in range(10) for f in (
    R("aprop%d%s" % (k // 2 + 1, "ab"[k % 2]), 0x118 + 16 * k, "properties:code", "s32", nocase=True),
    I("apar%d%s" % (k // 2 + 1, "ab"[k % 2]), 0x11C + 16 * k, "s32", names="skills:skill"),
    I("amin%d%s" % (k // 2 + 1, "ab"[k % 2]), 0x120 + 16 * k, "s32"),
    I("amax%d%s" % (k // 2 + 1, "ab"[k % 2]), 0x124 + 16 * k, "s32"))
])

# ------------------------------------------------------------------ sets (296 B = 0x128)
# Plan 0019 Phase 0: the identity head. Plan 0041 Phase 0: the sixteen bonus quads PCode2a..PMax5b and
# FCode1..FMax8 (+0x010..+0x10F, 16 x 16 B: code s32 (blank -1, properties row, case-insensitive), param,
# min, max s32), the setitems property-block shape. A param cell holding a name stores the row index of a
# skill (oskill) or of a state (state: fullsetgeneric, monsterset) (docs/tables/Sets.md). `index` is stored
# as the row's own index (u16), `name` as a string-table key. `level` has no field: probe finds it at no
# offset under any encoding (docs/tables/Sets.md).
# Plan 0019 Phase 1 (items/0004 section 7): +0x00C member count and +0x110..+0x127 six member
# pointers are filled at load (0 in the file); +0x008 has no writer or reader found.
LAYOUTS["sets"] = dict(size=0x128, fields=[
    R("index", 0x000, "sets:index", "u16"),
    T("name", 0x002),
    I("version", 0x004, "u32"),
    U("unk_008", 0x008, "u32"), U("nMembers", 0x00C, "u32"),
] + [f for k, (c, n) in enumerate([("P", "%d%s" % (k // 2 + 2, "ab"[k % 2])) for k in range(8)]
                                   + [("F", "%d" % (k + 1)) for k in range(8)]) for f in (
    R("%sCode%s" % (c, n), 0x010 + 16 * k, "properties:code", "s32", nocase=True),
    I("%sParam%s" % (c, n), 0x014 + 16 * k, "s32", names="skills:skill|states:state"),
    I("%sMin%s" % (c, n), 0x018 + 16 * k, "s32"),
    I("%sMax%s" % (c, n), 0x01C + 16 * k, "s32"))
] + [U("member%d" % k, 0x110 + 4 * k, "u32") for k in range(6)],
    txt_only={"level": "no field in sets.bin matches it (probe: no offset under any encoding)",
             "*eol": "end-of-line marker column"})

# ------------------------------------------------------------------ colors (4 B), compcode (4 B), armtype (52 B)
LAYOUTS["colors"] = dict(size=4, fields=[C("Code", 0x000)],
                         txt_only={"Transform Color": "editor name; not in the record"})
LAYOUTS["compcode"] = dict(size=4, fields=[C("code", 0x000)],
                           txt_only={"component": "editor name; not in the record"})
LAYOUTS["armtype"] = dict(size=52, fields=[
    S("Name", 0x000, 32), C("Token", 0x020),
    U("unk_024", 0x024, "u32"), U("unk_028", 0x028, "u32"), U("unk_02C", 0x02C, "u32"), U("unk_030", 0x030, "u32"),
])

# ------------------------------------------------------------------ superuniques (52 B = 0x34)
# hcIdx and the self-reference Superunique hold the row index in every record, so the data cannot say
# which of +0x000 (u16) and +0x008 (u32) is which; the three Utrans columns are equal in every row.
# TC per difficulty at +0x02C + 2*diff is read by MONSTER_DropItems (findings/items/0001 section 3).
LAYOUTS["superuniques"] = dict(size=52, fields=[
    I("hcIdx", 0x000, "u16"),
    T("Name", 0x002),
    R("Class", 0x004, "monstats:Id", "u32"),
    R("Superunique", 0x008, "superuniques:Superunique", "u32"),
    I("Mod1", 0x00C, "u32"), I("Mod2", 0x010, "u32"), I("Mod3", 0x014, "u32"),
    R("MonSound", 0x018, "monsounds:Id", "u32", blank=0),
    I("MinGrp", 0x01C, "u32"), I("MaxGrp", 0x020, "u32"),
    I("AutoPos", 0x024, "u8"), I("EClass", 0x025, "u8"), I("Stacks", 0x026, "u8"), I("Replaceable", 0x027, "u8"),
    I("Utrans", 0x028, "u8"), I("Utrans(N)", 0x029, "u8"), I("Utrans(H)", 0x02A, "u8"),
    U("unk_02B", 0x02B, "u8"),
    R("TC", 0x02C, "treasureclassex:Treasure Class", "u16", blank=0, bias=161),
    R("TC(N)", 0x02E, "treasureclassex:Treasure Class", "u16", blank=0, bias=161),
    R("TC(H)", 0x030, "treasureclassex:Treasure Class", "u16", blank=0, bias=161),
    U("unk_032", 0x032, "u16"),
], txt_only={"*eol": "end-of-line marker column"})

# ------------------------------------------------------------------ monlvl (120 B = 0x78)
# One record per MonLvl.txt row; Level equals the row index and is not compiled. Thirty u32 in .txt
# column order: for each of AC, TH, HP, DM, XP the three classic columns (X, X(N), X(H)) then the
# three expansion ones (L-X, L-X(N), L-X(H)). Where X and L-X hold the same values in every row
# (AC, the TH triple, HP and HP(N), the DM and XP triples) probe allows either slot, and the order
# comes from the stride and the columns that differ (docs/tables/MonLvl.md).
_MONLVL = ["AC", "TH", "HP", "DM", "XP"]
LAYOUTS["monlvl"] = dict(size=0x78, fields=[
    I(p + c + d, 0x18 * g + 0x0C * k + 4 * j, "u32")
    for g, c in enumerate(_MONLVL) for k, p in enumerate(["", "L-"]) for j, d in enumerate(_D)
], txt_only={"Level": "equals the row index (0..110) in every row; no field in monlvl.bin holds it"})

# ------------------------------------------------------------------ monstats2 (308 B = 0x134)
# One record per MonStats2.txt row (609; MonStats MonStatsEx +0x018 indexes it). The sixteen component
# columns HDv..S8v ("lit,med,hvy") compile twice: a u8 token count each at +0x015..+0x024, and twelve
# u8 CompCode row indices each (0xFF = empty) at +0x026 + 12*k. +0x025 is computed: the sum over the
# sixteen of (count - 1). Bit columns: the sixteen component flags HD..S8 at +0x0E8 (bit k), the mode
# flags mDT..mRN at +0x0F0 and the A1mv..S4mv flags at +0x104, both by monmode index (bit = mode). Where a
# column is constant (TR, A1mv, SCmv, S3mv, S4mv, Heart, BodyPart) or equal to a sibling (SizeX/SizeY,
# the d* bytes) probe cannot place it, and the slot comes from the stride (docs/tables/MonStats2.md).
_COMPS = ["HD", "TR", "LG", "RA", "LA", "RH", "LH", "SH", "S1", "S2", "S3", "S4", "S5", "S6", "S7", "S8"]
_COMPV = [c[0] + c[1:].lower() + "v" if c in ("RA", "LA") else c + "v" for c in _COMPS]   # Rav, Lav
_MODES = ["DT", "NU", "WL", "GH", "A1", "A2", "BL", "SC", "S1", "S2", "S3", "S4", "DD", "KB", "SQ", "RN"]
LAYOUTS["monstats2"] = dict(size=0x134, fields=[
    R("Id", 0x000, "monstats2:Id", "u16"),
    B("noGfxHitTest", 0x004, 0), B("noMap", 0x004, 1), B("noOvly", 0x004, 2), B("isSel", 0x004, 3),
    B("alSel", 0x004, 4), B("noSel", 0x004, 5), B("shiftSel", 0x004, 6), B("corpseSel", 0x004, 7),
    B("revive", 0x005, 0), B("isAtt", 0x005, 1), B("small", 0x005, 2), B("large", 0x005, 3),
    B("soft", 0x005, 4), B("critter", 0x005, 5), B("Shadow", 0x005, 6), B("noUniqueShift", 0x005, 7),
    B("compositeDeath", 0x006, 0), B("inert", 0x006, 1), B("objCol", 0x006, 2), B("deadCol", 0x006, 3),
    B("unflatDead", 0x006, 4),
    I("SizeX", 0x008, "u8"), I("SizeY", 0x009, "u8"), I("spawnCol", 0x00A, "u8"),
    I("Height", 0x00B, "u8"), I("OverlayHeight", 0x00C, "u8"), I("pixHeight", 0x00D, "u8"),
    I("MeleeRng", 0x00E, "u8"),
    C("BaseW", 0x010),
    I("HitClass", 0x014, "u8"),
] + [dict(col=v, off=0x015 + k, type="tokcount") for k, v in enumerate(_COMPV)]
  + [dict(col="HDv", cols=_COMPV, off=0x025, type="toksum")]
  + [dict(col=v, off=0x026 + 12 * k, type="toklist", len=12, ref="compcode:code") for k, v in enumerate(_COMPV)]
  + [B(c, 0x0E8 + k // 8, k % 8) for k, c in enumerate(_COMPS)]
  + [I("TotalPieces", 0x0EC, "u32")]
  + [B("m" + m, 0x0F0 + k // 8, k % 8) for k, m in enumerate(_MODES)]
  + [I("d" + m, 0x0F4 + k, "u8") for k, m in enumerate(_MODES)]
  + [B(m + "mv", 0x104 + k // 8, k % 8) for k, m in enumerate(_MODES) if m in ("A1", "A2", "SC", "S1", "S2", "S3", "S4")]
  + [
    I("InfernoLen", 0x108, "u8"), I("InfernoAnim", 0x109, "u8"), I("InfernoRollback", 0x10A, "u8"),
    R("ResurrectMode", 0x10B, "monmode:code", "u8", blank=0),
    R("ResurrectSkill", 0x10C, "skills:skill", "s16", blank=-1),
    I("htTop", 0x10E, "s16"), I("htLeft", 0x110, "s16"), I("htWidth", 0x112, "s16"), I("htHeight", 0x114, "s16"),
    I("automapCel", 0x118, "u32"),
    I("localBlood", 0x11C, "u8"), I("Bleed", 0x11D, "u8"), I("Light", 0x11E, "u8"),
    I("light-r", 0x11F, "u8"), I("light-g", 0x120, "u8"), I("light-b", 0x121, "u8"),
    I("Utrans", 0x122, "u8"), I("Utrans(N)", 0x123, "u8"), I("Utrans(H)", 0x124, "u8"),
    C("Heart", 0x128), C("BodyPart", 0x12C),
    I("restore", 0x130, "u32"),
], txt_only={"EOL": "end-of-line marker column, constant; no field"})

# ------------------------------------------------------------------ monplace (2 B)
# One u16 per MonPlace.txt row (37), equal to the row index: the compiled `code` column resolves to its
# own row. MonPreset Place names these rows (tag 0) beside monstats and superuniques.
LAYOUTS["monplace"] = dict(size=2, fields=[R("code", 0x000, "monplace:code", "u16")])

# ------------------------------------------------------------------ monpreset (4 B)
# One record per MonPreset.txt row (229). Place compiles twice: +0x001 the kind of name (0 = monplace
# code, 1 = monstats Id, 2 = superuniques Superunique) and +0x002 the row index in that table. Every
# Place value names exactly one of the three tables (case-sensitive), so the data cannot order the
# lookups; the order below is a choice of the layout (docs/tables/MonPreset.md).
_PLACE = [(1, "monstats:Id", True), (2, "superuniques:Superunique", False), (0, "monplace:code", False)]
LAYOUTS["monpreset"] = dict(size=4, fields=[
    I("Act", 0x000, "u8"),
    dict(P("Place", 0x001, _PLACE, "tag", "u8"), name="PlaceKind"),
    P("Place", 0x002, _PLACE, "index", "u16"),
])

# ------------------------------------------------------------------ montype (12 B)
# One record per MonType.txt row (59, row 0 blank). +0x000 is the row's own index (type looked up in
# its own column); equiv1..equiv3 are row indices of this table, blank = 0 (row 0 is the blank type).
# equiv3 is blank in every row and equiv2 set once, so their slots and the s16 width follow the stride
# and the reader (sub_00658520_MonTypeLoad, findings/monsters/0003 section 3). strsing/strplur are
# string-table keys (blank = 5382).
LAYOUTS["montype"] = dict(size=12, fields=[
    R("type", 0x000, "montype:type", "s16"),
    R("equiv1", 0x002, "montype:type", "s16", blank=0), R("equiv2", 0x004, "montype:type", "s16", blank=0),
    R("equiv3", 0x006, "montype:type", "s16", blank=0),
    T("strsing", 0x008), T("strplur", 0x00A),
], txt_only={"*eol": "end-of-line marker column"})

# ------------------------------------------------------------------ monumod (32 B = 0x20)
# One record per MonUMod.txt row (43). The champion and the three cpick columns hold equal values in
# every row (1 on champion, ghostly, fanatic, possessed, berserk), so probe places them only together:
# champion is the u8 at +0x008 (cpick is u16, the only u16 run of three), and the cpick order
# +0x00E + 2*diff is the reader's (findings/monsters/0002 section 5); the upick order follows the stride.
# exclude2 and fInit are blank in every row, so their slots come from the stride. constants is a
# separate list of 35 values (one per row, *constant desc names each); row 0 (20) is the champion chance.
LAYOUTS["monumod"] = dict(size=0x20, fields=[
    I("id", 0x000, "u32"),
    I("version", 0x004, "u16"), I("enabled", 0x006, "u8"), I("xfer", 0x007, "u8"),
    I("champion", 0x008, "u8"), I("fPick", 0x009, "u8"),
    R("exclude1", 0x00A, "montype:type", "u16", blank=0), R("exclude2", 0x00C, "montype:type", "u16", blank=0),
    I("cpick", 0x00E, "u16"), I("cpick (N)", 0x010, "u16"), I("cpick (H)", 0x012, "u16"),
    I("upick", 0x014, "u16"), I("upick (N)", 0x016, "u16"), I("upick (H)", 0x018, "u16"),
    I("fInit", 0x01A, "u16"),
    I("constants", 0x01C, "u32"),
], txt_only={"uniquemod": "key; the record holds only id (= row index)",
             "*constant desc": "comment column naming the constants value; no bytes",
             "*eol": "end-of-line marker column"})

# ------------------------------------------------------------------ monprop (312 B = 0x138)
# Plan 0025 Phase 0 (docs/tables/MonProp.md). One record per MonProp.txt row (13). Id is the row's own index
# (MonStats MonProp +0x01A indexes the table). Then per difficulty d (normal, (N), (H)) at +0x004 + 0x60*d six
# 16-byte slots k at + 0x10*k: prop (s32 properties row, blank -1), par, min, max (s32). probe pins prop, min
# and max of the used slots and the 0x10/0x60 strides. par and chance are blank in every row, so their slots
# are not pinned by data: par is the remaining dword of the slot, and the 18 chance cells are u8 at
# +0x124 + 6*d + (k-1), which fills the 20-byte tail with 2 bytes to spare (both choices: MonProp.md).
_MP_DIFF = ["", " (N)", " (H)"]
LAYOUTS["monprop"] = dict(size=0x138, fields=[
    R("Id", 0x000, "monprop:Id", "u32"),
] + [f for d, s in enumerate(_MP_DIFF) for k in range(6) for f in (
    R("prop%d%s" % (k + 1, s), 0x004 + 0x60 * d + 0x10 * k, "properties:code", "s32"),
    I("par%d%s" % (k + 1, s), 0x008 + 0x60 * d + 0x10 * k, "s32"),
    I("min%d%s" % (k + 1, s), 0x00C + 0x60 * d + 0x10 * k, "s32"),
    I("max%d%s" % (k + 1, s), 0x010 + 0x60 * d + 0x10 * k, "s32"))]
  + [I("chance%d%s" % (k + 1, s), 0x124 + 6 * d + k, "u8") for d, s in enumerate(_MP_DIFF) for k in range(6)]
  + [U("pad_136", 0x136, "u16")],
    txt_only={"*eol": "end-of-line marker column"})

# ------------------------------------------------------------------ difficultylevels (88 B = 0x58)
# Plan 0025 Phase 0 (docs/tables/DifficultyLevels.md). One record per row (3: Normal, Nightmare, Hell); Name is
# not compiled (the record index is the difficulty). 22 s32, not in .txt order: UltraCodeOddsNormal/Good sit
# at +0x020/+0x024, after the three divisors. The three divisors (equal in every row), LifeSteal/ManaSteal
# and UniqueDamageBonus/ChampionDamageBonus (equal in pairs) are placed only as groups by probe; their order
# inside a group follows the .txt order (DifficultyLevels.md).
LAYOUTS["difficultylevels"] = dict(size=0x58, fields=[
    I(c, 4 * k, "s32") for k, c in enumerate([
        "ResistPenalty", "DeathExpPenalty", "UberCodeOddsNormal", "UberCodeOddsGood", "MonsterSkillBonus",
        "MonsterFreezeDivisor", "MonsterColdDivisor", "AiCurseDivisor",
        "UltraCodeOddsNormal", "UltraCodeOddsGood", "LifeStealDivisor", "ManaStealDivisor",
        "UniqueDamageBonus", "ChampionDamageBonus", "HireableBossDamagePercent", "MonsterCEDamagePercent",
        "StaticFieldMin", "GambleRare", "GambleSet", "GambleUnique", "GambleUber", "GambleUltra"])
], txt_only={"Name": "editor name; the record index is the difficulty (0 normal, 1 nightmare, 2 hell)"})

# ------------------------------------------------------------------ unique monster name tables (2 B)
# One u16 string-table index per row: the Name key (uniqueprefix, uniquesuffix, uniqueappellation).
# uniquetitle's Name is "unused" in every row; its .bin holds the string index of that key, not of Namco.
LAYOUTS["uniqueprefix"] = dict(size=2, fields=[T("Name", 0x000)])
LAYOUTS["uniquesuffix"] = dict(size=2, fields=[T("Name", 0x000)])
LAYOUTS["uniqueappellation"] = dict(size=2, fields=[T("Name", 0x000)])
LAYOUTS["uniquetitle"] = dict(size=2, fields=[T("Name", 0x000)],
                              txt_only={"Namco": "title text column; not compiled (the record holds Name)"})

# ------------------------------------------------------------------ objects (448 B = 0x1C0)
# Plan 0023 Phase 0 (docs/tables/Objects.md). One record per objects.txt row (573; the Expansion separator
# has none). Id is not compiled: the record index is the class id (Id repeats 408/409 after the separator,
# so the two disagree from row 410 on). Where a run of columns holds equal values in every row (Selectable4..7,
# CycleAnim4/5 and 6/7, Lit4/5 and 6/7, HasCollision4/5, OrderFlag3..7) or is constant (Start0/6/7, nTgtBX/BY,
# LG..LH, S5..S8, TR, Damage) probe places it only as a group or anywhere; the slot follows the stride of
# the run (Objects.md, "Placed by stride"). Flicker has no field (probe: no offset under any encoding).
LAYOUTS["objects"] = dict(size=0x1C0, fields=[
    S("Name", 0x000, 64),
    U("unk_040", 0x040, "str", len=128),
    S("Token", 0x0C0, 3, truncate=True),
    I("SpawnMax", 0x0C3, "u8"),
] + [I("Selectable%d" % k, 0x0C4 + k, "u8") for k in range(8)] + [
    I("TrapProb", 0x0CC, "u32"),
    I("SizeX", 0x0D0, "u32"), I("SizeY", 0x0D4, "u32"),
] + [I("FrameCnt%d" % k, 0x0D8 + 4 * k, "u32") for k in range(8)]
  + [I("FrameDelta%d" % k, 0x0F8 + 2 * k, "u16") for k in range(8)]
  + [I("CycleAnim%d" % k, 0x108 + k, "u8") for k in range(8)]
  + [I("Lit%d" % k, 0x110 + k, "u8") for k in range(8)]
  + [I("BlocksLight%d" % k, 0x118 + k, "u8") for k in range(8)]
  + [I("HasCollision%d" % k, 0x120 + k, "u8") for k in range(8)]
  + [I("IsAttackable0", 0x128, "u8")]
  + [I("Start%d" % k, 0x129 + k, "u8") for k in range(8)]
  + [I("OrderFlag%d" % k, 0x131 + k, "u8") for k in range(8)] + [
    I("EnvEffect", 0x139, "u8"), I("IsDoor", 0x13A, "u8"), I("BlocksVis", 0x13B, "u8"),
    I("Orientation", 0x13C, "u8"), I("PreOperate", 0x13D, "u8"), I("Trans", 0x13E, "u8"),
] + [I("Mode%d" % k, 0x13F + k, "u8") for k in range(8)] + [
    U("pad_147", 0x147, "u8"),
    I("Xoffset", 0x148, "s32"), I("Yoffset", 0x14C, "s32"),
    I("Draw", 0x150, "u8"),
] + [I(c, 0x151 + k, "u8") for k, c in enumerate(_COMPS)] + [
    I("TotalPieces", 0x161, "u8"), I("Xspace", 0x162, "s8"), I("Yspace", 0x163, "s8"),
    I("Red", 0x164, "u8"), I("Green", 0x165, "u8"), I("Blue", 0x166, "u8"),
    I("SubClass", 0x167, "u8"),
    I("NameOffset", 0x168, "s32"),
    U("unk_16C", 0x16C, "u8"),
    I("MonsterOK", 0x16D, "u8"), I("OperateRange", 0x16E, "u8"),
    U("unk_16F", 0x16F, "u8"),
    I("Act", 0x170, "u8"), I("Lockable", 0x171, "u8"), I("Gore", 0x172, "u8"), I("Restore", 0x173, "u8"),
    I("RestoreVirgins", 0x174, "u8"), I("Sync", 0x175, "u8"),
    U("pad_176", 0x176, "u16"),
] + [I("Parm%d" % k, 0x178 + 4 * k, "s32") for k in range(8)] + [
    I("nTgtFX", 0x198, "u8"), I("nTgtFY", 0x199, "u8"), I("nTgtBX", 0x19A, "u8"), I("nTgtBY", 0x19B, "u8"),
    I("Damage", 0x19C, "u8"), I("CollisionSubst", 0x19D, "u8"),
    U("pad_19E", 0x19E, "u16"),
    I("Left", 0x1A0, "s32"), I("Top", 0x1A4, "s32"), I("Width", 0x1A8, "s32"), I("Height", 0x1AC, "s32"),
    I("Beta", 0x1B0, "u8"), I("InitFn", 0x1B1, "u8"), I("PopulateFn", 0x1B2, "u8"), I("OperateFn", 0x1B3, "u8"),
    I("ClientFn", 0x1B4, "u8"), I("Overlay", 0x1B5, "u8"), I("BlockMissile", 0x1B6, "u8"), I("DrawUnder", 0x1B7, "u8"),
    I("OpenWarp", 0x1B8, "u32"), I("AutoMap", 0x1BC, "u32"),
], txt_only={"description - not loaded": "comment column (its header says so); no bytes in the record",
             "Id": "not compiled: the record index is the class id (Id repeats 408/409 after the Expansion row)",
             "ShrineFunction": "0 in every row; no field found",
             "Flicker": "no field: probe finds no offset under any encoding"})

# ------------------------------------------------------------------ objgroup (52 B = 0x34)
# Plan 0023 Phase 0 (docs/tables/ObjGroup.md). One record per objgroup.txt row (133). The separator row is
# spelled "EXPANSION" (upper case), so excel_bin keeps it and so does the compiler: it is record 97, all zero,
# and Offset (= the row index, not compiled) skips it. DENSITY6/7 are equal in every row; their slots follow
# the stride of DENSITY0..5.
LAYOUTS["objgroup"] = dict(size=0x34, fields=[
    I("ID%d" % k, 0x000 + 4 * k, "u32") for k in range(8)
] + [I("DENSITY%d" % k, 0x020 + k, "u8") for k in range(8)]
  + [I("PROB%d" % k, 0x028 + k, "u8") for k in range(8)] + [
    I("SHRINES", 0x030, "u8"), I("WELLS", 0x031, "u8"),
    U("pad_032", 0x032, "u16"),
], txt_only={"GroupName": "editor name; not in the record",
             "Offset": "equals the row index (blank on the EXPANSION row); not compiled"})

# ------------------------------------------------------------------ shrines (184 B = 0xB8)
# Plan 0023 Phase 0 (docs/tables/Shrines.md). One record per shrines.txt row (23). Code equals the row index.
# view name and niftyphrase are "blah" in every row, so probe places them only as a pair; the widths (32 and
# 128) follow from the next field. effectclass is a u8 or the low byte of a u16 (+0x0B3 is 0 everywhere).
LAYOUTS["shrines"] = dict(size=0xB8, fields=[
    I("Code", 0x000, "u32"),
    I("Arg0", 0x004, "s32"), I("Arg1", 0x008, "s32"),
    I("Duration in frames", 0x00C, "u32"),
    I("reset time in minutes", 0x010, "u8"), I("rarity", 0x011, "u8"),
    S("view name", 0x012, 32), S("niftyphrase", 0x032, 128),
    I("effectclass", 0x0B2, "u8"), U("pad_0B3", 0x0B3, "u8"),
    I("LevelMin", 0x0B4, "u32"),
], txt_only={"Shrine Type": "editor grouping (Booster, Magic, Recharge, None); not in the record",
             "Shrine name": "editor name; not in the record",
             "Effect": "editor description; not in the record"})

# ------------------------------------------------------------------ objmode (52 B = 0x34)
# Plan 0023 Phase 0 (docs/tables/ObjMode.md). One record per ObjMode.txt row (8): the object mode names and
# their two-letter tokens. +0x024..+0x033 is zero in every record (no .txt column).
LAYOUTS["objmode"] = dict(size=0x34, fields=[
    S("Name", 0x000, 32), C("Token", 0x020),
    U("unk_024", 0x024, "str", len=16),
])

# ------------------------------------------------------------------ qualityitems (112 B = 0x70)
# Backlog sweep 4 (docs/tables/QualityItems.md). One record per qualityitems.txt row (8): the superior
# ("hiquality") mods. Bytes 0..9 are ten u8 type flags; the .txt has eleven. The six weapon-family columns
# (weapon, thrown, scepter, wand, staff, bow) are equal in every row and the five armour-family ones too, so
# probe places them only as families: weapon family at +0x001/+0x003..+0x006, armour family at +0x000/+0x002/
# +0x007..+0x009. One weapon-family column has no byte; the slots follow the .txt order without `thrown`,
# which is the order the superior type test reads them in (findings/items/0005 section 8). The ToHit/Dam%/
# AC%/Dur% ranges, level, multiply and add have no field (probe: no offset under any encoding).
LAYOUTS["qualityitems"] = dict(size=0x70, fields=[
    I("armor", 0x000, "u8"), I("weapon", 0x001, "u8"), I("shield", 0x002, "u8"), I("scepter", 0x003, "u8"),
    I("wand", 0x004, "u8"), I("staff", 0x005, "u8"), I("bow", 0x006, "u8"), I("boots", 0x007, "u8"),
    I("gloves", 0x008, "u8"), I("belt", 0x009, "u8"),
    I("nummods", 0x00A, "u8"), U("pad_00B", 0x00B, "u8"),
] + [f for k in range(2) for f in (
    R("mod%dcode" % (k + 1), 0x00C + 16 * k, "properties:code", "s32"),
    I("mod%dparam" % (k + 1), 0x010 + 16 * k, "s32"),
    I("mod%dmin" % (k + 1), 0x014 + 16 * k, "s32"),
    I("mod%dmax" % (k + 1), 0x018 + 16 * k, "s32"))] + [
    S("effect1", 0x02C, 32), S("effect2", 0x04C, 32),
    U("unk_06C", 0x06C, "u32"),
], txt_only={
    "thrown": "no byte: equal to weapon in every row, and the ten flag bytes take the other ten columns",
    "ToHitMin": "no field (probe); the to-hit range is mod1/mod2 of the att rows",
    "ToHitMax": "no field (probe)", "Dam%Min": "no field (probe)", "Dam%Max": "no field (probe)",
    "AC%Min": "no field (probe)", "AC%Max": "no field (probe)", "Dur%Min": "no field (probe)",
    "Dur%Max": "no field (probe)",
    "level": "no field (probe); 1 or 3",
    "multiply": "no field (probe); price column",
    "add": "no field (probe); price column"})

# ------------------------------------------------------------------ lowqualityitems (34 B = 0x22)
# Backlog sweep 4 (docs/tables/LowQualityItems.md). One record per row (4): the low-quality name prefix,
# a 34-byte NUL-terminated char array (the record has nothing else).
LAYOUTS["lowqualityitems"] = dict(size=0x22, fields=[S("Name", 0x000, 34)])

# ------------------------------------------------------------------ skills (572 B = 0x23C)
# Backlog sweep 4 (docs/tables/Skills.md). One record per skills.txt row (357, no Expansion marker); Id
# equals the row index (the skill id). Offsets from `excel_bin.py probe`, calc offsets from a scan for s32
# fields that are -1 exactly on blank cells (K fields into skillscode.bin). summon and sumskill1/2 are
# looked up case-insensitively ("ClayGolem" finds monstats "claygolem"). Columns blank in every row are
# placed by the stride of their run (itypea3, etypea2, itypeb2/3, etypeb1/2, aurastatcalc5/6,
# passivestat5/passivecalc5, sumskill5 neighbours, reqstr..reqvit, reqskill3, State3); see Skills.md.
_SK = "skills:skill"
_SKC = "skillscode"
_SK_BITS = [  # (column, byte, bit) of the packed flags at +0x004..+0x008
    ("decquant", 4, 0), ("lob", 4, 1), ("progressive", 4, 2), ("finishing", 4, 3), ("passive", 4, 4),
    ("aura", 4, 5), ("periodic", 4, 6), ("prgstack", 4, 7),
    ("InTown", 5, 0), ("Kick", 5, 1), ("InGame", 5, 2), ("repeat", 5, 3), ("stsuccessonly", 5, 4),
    ("stsounddelay", 5, 5), ("weaponsnd", 5, 6), ("immediate", 5, 7),
    ("noammo", 6, 0), ("enhanceable", 6, 1), ("durability", 6, 2), ("UseAttackRate", 6, 3),
    ("TargetableOnly", 6, 4), ("SearchEnemyXY", 6, 5), ("SearchEnemyNear", 6, 6), ("SearchOpenXY", 6, 7),
    ("TargetCorpse", 7, 0), ("TargetPet", 7, 1), ("TargetAlly", 7, 2), ("TargetItem", 7, 3),
    ("AttackNoMana", 7, 4), ("ItemTgtDo", 7, 5), ("leftskill", 7, 6), ("interrupt", 7, 7),
    ("TgtPlaceCheck", 8, 0), ("ItemCheckStart", 8, 1), ("ItemCltCheckStart", 8, 2), ("general", 8, 3),
    ("scroll", 8, 4), ("usemanaondo", 8, 5), ("warp", 8, 6),
]
LAYOUTS["skills"] = dict(size=0x23C, fields=[
    I("Id", 0x000, "u16"), U("unk_002", 0x002, "u16"),
] + [B(c, by, bit) for c, by, bit in _SK_BITS] + [
    U("unk_009", 0x009, "u8"), U("unk_00A", 0x00A, "u16"),
    R("charclass", 0x00C, "playerclass:Code", "u8"), U("unk_00D", 0x00D, "u8"), U("unk_00E", 0x00E, "u16"),
    R("anim", 0x010, "plrmode:Code", "u8"), R("monanim", 0x011, "monmode:code", "u8"),
    R("seqtrans", 0x012, "plrmode:Code", "u8"), I("seqnum", 0x013, "u8"),
    E("range", 0x014, ["none", "h2h", "rng", "both"]), I("SelectProc", 0x015, "u8"), I("seqinput", 0x016, "u16"),
    R("itypea1", 0x018, _IT, "u16"), R("itypea2", 0x01A, _IT, "u16"), R("itypea3", 0x01C, _IT, "u16"),
    R("itypeb1", 0x01E, _IT, "u16"), R("itypeb2", 0x020, _IT, "u16"), R("itypeb3", 0x022, _IT, "u16"),
    R("etypea1", 0x024, _IT, "u16"), R("etypea2", 0x026, _IT, "u16"),
    R("etypeb1", 0x028, _IT, "u16"), R("etypeb2", 0x02A, _IT, "u16"),
    I("srvstfunc", 0x02C, "u16"), I("srvdofunc", 0x02E, "u16"),
    I("srvprgfunc1", 0x030, "u16"), I("srvprgfunc2", 0x032, "u16"), I("srvprgfunc3", 0x034, "u16"),
    U("unk_036", 0x036, "u16"),
    K("prgcalc1", 0x038, _SKC), K("prgcalc2", 0x03C, _SKC), K("prgcalc3", 0x040, _SKC),
    I("prgdam", 0x044, "u16"),
    R("srvmissile", 0x046, "missiles:Missile", "u16"), R("srvmissilea", 0x048, "missiles:Missile", "u16"),
    R("srvmissileb", 0x04A, "missiles:Missile", "u16"), R("srvmissilec", 0x04C, "missiles:Missile", "u16"),
    R("srvoverlay", 0x04E, "overlay:overlay", "u16"),
    I("aurafilter", 0x050, "u32"),
] + [R("aurastat%d" % (k + 1), 0x054 + 2 * k, _STAT, "u16") for k in range(6)] + [
    K("auralencalc", 0x060, _SKC), K("aurarangecalc", 0x064, _SKC),
] + [K("aurastatcalc%d" % (k + 1), 0x068 + 4 * k, _SKC) for k in range(6)] + [
    R("aurastate", 0x080, "states:state", "u16"), R("auratargetstate", 0x082, "states:state", "u16"),
] + [R("auraevent%d" % (k + 1), 0x084 + 2 * k, "events:event", "u16") for k in range(3)] \
  + [I("auraeventfunc%d" % (k + 1), 0x08A + 2 * k, "u16") for k in range(3)] + [
    R("auratgtevent", 0x090, "events:event", "u16"), I("auratgteventfunc", 0x092, "u16"),
    R("passivestate", 0x094, "states:state", "u16"), R("passiveitype", 0x096, _IT, "u16"),
] + [R("passivestat%d" % (k + 1), 0x098 + 2 * k, _STAT, "u16") for k in range(5)] + [
    U("unk_0A2", 0x0A2, "u16"),
] + [K("passivecalc%d" % (k + 1), 0x0A4 + 4 * k, _SKC) for k in range(5)] + [
    R("passiveevent", 0x0B8, "events:event", "u16"), I("passiveeventfunc", 0x0BA, "u16"),
    R("summon", 0x0BC, "monstats:Id", "u16", nocase=True),
    R("pettype", 0x0BE, "pettype:pet type", "u8"), R("summode", 0x0BF, "monmode:code", "u8"),
    K("petmax", 0x0C0, _SKC),
] + [R("sumskill%d" % (k + 1), 0x0C4 + 2 * k, _SK, "u16", nocase=True) for k in range(5)] + [
    U("unk_0CE", 0x0CE, "u16"),
] + [K("sumsk%dcalc" % (k + 1), 0x0D0 + 4 * k, _SKC) for k in range(5)] + [
    I("sumumod", 0x0E4, "u16"), R("sumoverlay", 0x0E6, "overlay:overlay", "u16"),
    R("cltmissile", 0x0E8, "missiles:Missile", "u16"), R("cltmissilea", 0x0EA, "missiles:Missile", "u16"),
    R("cltmissileb", 0x0EC, "missiles:Missile", "u16"), R("cltmissilec", 0x0EE, "missiles:Missile", "u16"),
    R("cltmissiled", 0x0F0, "missiles:Missile", "u16"),
    I("cltstfunc", 0x0F2, "u16"), I("cltdofunc", 0x0F4, "u16"),
    I("cltprgfunc1", 0x0F6, "u16"), I("cltprgfunc2", 0x0F8, "u16"), I("cltprgfunc3", 0x0FA, "u16"),
    R("stsound", 0x0FC, "sounds:Sound", "u16", blank=0), R("stsoundclass", 0x0FE, "sounds:Sound", "u16", blank=0),
    R("dosound", 0x100, "sounds:Sound", "u16", blank=0), R("dosound a", 0x102, "sounds:Sound", "u16", blank=0),
    R("dosound b", 0x104, "sounds:Sound", "u16", blank=0),
    R("castoverlay", 0x106, "overlay:overlay", "u16"), R("tgtoverlay", 0x108, "overlay:overlay", "u16"),
    R("tgtsound", 0x10A, "sounds:Sound", "u16", blank=0),
    R("prgoverlay", 0x10C, "overlay:overlay", "u16"), R("prgsound", 0x10E, "sounds:Sound", "u16", blank=0),
    R("cltoverlaya", 0x110, "overlay:overlay", "u16"), R("cltoverlayb", 0x112, "overlay:overlay", "u16"),
    K("cltcalc1", 0x114, _SKC), K("cltcalc2", 0x118, _SKC), K("cltcalc3", 0x11C, _SKC),
    I("ItemTarget", 0x120, "u16"), R("ItemCastSound", 0x122, "sounds:Sound", "u16", blank=0),
    R("ItemCastOverlay", 0x124, "overlay:overlay", "u16"), U("unk_126", 0x126, "u16"),
    K("perdelay", 0x128, _SKC),
    I("maxlvl", 0x12C, "u16"), I("ResultFlags", 0x12E, "u16"),
    I("HitFlags", 0x130, "u32"), I("HitClass", 0x134, "u32"),
] + [K("calc%d" % (k + 1), 0x138 + 4 * k, _SKC) for k in range(4)] \
  + [I("Param%d" % (k + 1), 0x148 + 4 * k, "s32") for k in range(8)] + [
    I("weapsel", 0x168, "u16"), I("ItemEffect", 0x16A, "u16"), I("ItemCltEffect", 0x16C, "u16"),
    U("unk_16E", 0x16E, "u16"),
    K("skpoints", 0x170, _SKC),
    I("reqlevel", 0x174, "u16"),
    I("reqstr", 0x176, "u16"), I("reqdex", 0x178, "u16"), I("reqint", 0x17A, "u16"), I("reqvit", 0x17C, "u16"),
    R("reqskill1", 0x17E, _SK, "u16"), R("reqskill2", 0x180, _SK, "u16"), R("reqskill3", 0x182, _SK, "u16"),
    I("startmana", 0x184, "u16"), I("minmana", 0x186, "u16"), I("manashift", 0x188, "u16"),
    I("mana", 0x18A, "s16"), I("lvlmana", 0x18C, "s16"),
    I("attackrank", 0x18E, "u8"), I("LineOfSight", 0x18F, "u8"),
    K("delay", 0x190, _SKC),
    R("skilldesc", 0x194, "skilldesc:skilldesc", "u16"), U("unk_196", 0x196, "u16"),
    I("ToHit", 0x198, "s32"), I("LevToHit", 0x19C, "s32"), K("ToHitCalc", 0x1A0, _SKC),
    I("HitShift", 0x1A4, "u8"), I("SrcDam", 0x1A5, "u8"), U("unk_1A6", 0x1A6, "u16"),
    I("MinDam", 0x1A8, "s32"), I("MaxDam", 0x1AC, "s32"),
] + [I("MinLevDam%d" % (k + 1), 0x1B0 + 4 * k, "s32") for k in range(5)] \
  + [I("MaxLevDam%d" % (k + 1), 0x1C4 + 4 * k, "s32") for k in range(5)] + [
    K("DmgSymPerCalc", 0x1D8, _SKC),
    R("EType", 0x1DC, "elemtypes:Code", "u8"), U("unk_1DD", 0x1DD, "u8"), U("unk_1DE", 0x1DE, "u16"),
    I("EMin", 0x1E0, "s32"), I("EMax", 0x1E4, "s32"),
] + [I("EMinLev%d" % (k + 1), 0x1E8 + 4 * k, "s32") for k in range(5)] \
  + [I("EMaxLev%d" % (k + 1), 0x1FC + 4 * k, "s32") for k in range(5)] + [
    K("EDmgSymPerCalc", 0x210, _SKC),
    I("ELen", 0x214, "s32"),
] + [I("ELevLen%d" % (k + 1), 0x218 + 4 * k, "s32") for k in range(3)] + [
    K("ELenSymPerCalc", 0x224, _SKC),
    I("restrict", 0x228, "u8"), U("unk_229", 0x229, "u8"),
    R("State1", 0x22A, "states:state", "u16"), R("State2", 0x22C, "states:state", "u16"),
    R("State3", 0x22E, "states:state", "u16"),
    I("aitype", 0x230, "u16"), I("aibonus", 0x232, "s16"),
    I("cost mult", 0x234, "s32"), I("cost add", 0x238, "s32"),
], txt_only={"skill": "key; the record holds Id (= row index) instead",
             "checkfunc": "1..6 on 18 rows; no field (no offset under any integer encoding)",
             "nocostinstate": "1 on 2 rows (Wearwolf, Wearbear); no byte or bit follows it"})

# ------------------------------------------------------------------ gems (192 B = 0xC0)
# Plan 0029 Phase 0 (docs/tables/Gems.md). Three groups of three 16-byte mods (code s32, param s32,
# min s32, max s32): weaponMod1..3 at +0x030, helmMod1..3 at +0x060, shieldMod1..3 at +0x090; a blank
# code stores -1. `code` is the gem's item record index (s32, data/0004 section 3: GEMS_Load reads it
# at +0x28 and fills items +0x0F0). helmMod3 and shieldMod3 are blank in every row, so their slots
# follow the 16-byte stride, not the data.
_GEM_ITEMS = "weapons:code+armor:code+misc:code"
LAYOUTS["gems"] = dict(size=0xC0, fields=[
    S("name", 0x000, 32),
    S("letter", 0x020, 8),
    R("code", 0x028, _GEM_ITEMS, "s32"),
    U("pad_02C", 0x02C, "u16"),
    I("nummods", 0x02E, "u8"),
    I("transform", 0x02F, "u8"),
] + [f for g, base in (("weapon", 0x030), ("helm", 0x060), ("shield", 0x090)) for k in range(3) for f in (
    R("%sMod%dCode" % (g, k + 1), base + 16 * k, "properties:code", "s32"),
    I("%sMod%dParam" % (g, k + 1), base + 16 * k + 4, "s32"),
    I("%sMod%dMin" % (g, k + 1), base + 16 * k + 8, "s32"),
    I("%sMod%dMax" % (g, k + 1), base + 16 * k + 12, "s32"))
])

# ------------------------------------------------------------------ runes (288 B = 0x120)
# Plan 0029 Phase 0 (docs/tables/Runes.md). Rune1..6: the rune's item record index (s32, blank -1).
# T1Code1..7: 16-byte mods as in gems; a T1Param cell holding a skill name stores that skill's row
# index (case-insensitive: 'enchant', 'fanaticism'), every other cell its number. itype4..6 and etype1..3 are blank in every row: their u16 slots
# (+0x08C..+0x097) follow itype1..3 and the space left before Rune1, not the data.
LAYOUTS["runes"] = dict(size=0x120, fields=[
    S("Name", 0x000, 64),
    S("Rune Name", 0x040, 64),
    I("complete", 0x080, "u8"),
    I("server", 0x081, "u8"),
    U("unk_082", 0x082, "u16"),
    U("unk_084", 0x084, "u16"),
] + [R("itype%d" % (k + 1), 0x086 + 2 * k, "itemtypes:Code", "u16", blank=0) for k in range(6)]
  + [R("etype%d" % (k + 1), 0x092 + 2 * k, "itemtypes:Code", "u16", blank=0) for k in range(3)]
  + [R("Rune%d" % (k + 1), 0x098 + 4 * k, _GEM_ITEMS, "s32") for k in range(6)]
  + [f for k in range(7) for f in (
    R("T1Code%d" % (k + 1), 0x0B0 + 16 * k, "properties:code", "s32"),
    I("T1Param%d" % (k + 1), 0x0B4 + 16 * k, "s32", names="skills:skill"),
    I("T1Min%d" % (k + 1), 0x0B8 + 16 * k, "s32"),
    I("T1Max%d" % (k + 1), 0x0BC + 16 * k, "s32"))
], txt_only={"*runes": "editor comment (the rune letters joined); no bytes in the record",
             "eol": "end-of-line marker column"})


# ------------------------------------------------------------------ cubemain (328 B = 0x148)
# Plan 0030 Phase 0 (docs/tables/CubeMain.md). Header 0x14 bytes, seven 8-byte input records at +0x014, three 84-byte
# output records at +0x04C, +0x0A0, +0x0F4 (output, output b, output c), each with five 12-byte mod lines at +0x18.
# The input and output cells are parsed by the compiler into several fields each (tools/cubemain.py, conv=).
# Columns blank in every stock row (min diff, param, value, class, every mod chance, output b/c) are placed by the
# compile probe (run:2026-10-15-cube-saves): a cubemain.txt with filled cells compiled by the game under -direct -txt.
import cubemain as _cube  # noqa: E402

_CUBE_IN = [("flags", 0x0, "u16"), ("item", 0x2, "u16"), ("id", 0x4, "u16"), ("quality", 0x6, "u8"),
            ("qty", 0x7, "u8")]
_CUBE_OUT = [("flags", 0x0, "u16", None), ("item", 0x2, "u16", None), ("id", 0x4, "u16", None),
             ("quality", 0x6, "u8", None), ("qty", 0x7, "u8", None), ("kind", 0x8, "u8", None),
             ("pre", 0xC, "u16", 0), ("pre", 0xE, "u16", 1), ("pre", 0x10, "u16", 2),
             ("suf", 0x12, "u16", 0), ("suf", 0x14, "u16", 1), ("suf", 0x16, "u16", 2)]


def _cube_output(col, prefix, base):
    out = [I(col, base + o, t, conv=_cube.out_part(part, k), part=part + ("%d" % (k + 1) if k is not None else ""))
           for part, o, t, k in _CUBE_OUT]
    out += [I(prefix + "lvl", base + 0x09, "u8"), I(prefix + "plvl", base + 0x0A, "u8"),
            I(prefix + "ilvl", base + 0x0B, "u8")]
    for m in range(5):
        o, mod = base + 0x18 + 12 * m, "%smod %d" % (prefix, m + 1)
        out += [R(mod, o, "properties:code", "s32"), I(mod + " param", o + 4, "u16"), I(mod + " min", o + 6, "s16"),
                I(mod + " max", o + 8, "s16"), I(mod + " chance", o + 0xA, "u8"), U("%s_pad" % mod, o + 0xB, "u8")]
    return out


LAYOUTS["cubemain"] = dict(size=0x148, fields=[
    I("enabled", 0x00, "u8"), I("ladder", 0x01, "u8"), I("min diff", 0x02, "u8"),
    R("class", 0x03, "playerclass:Code", "u8"),
    I("op", 0x04, "u8"), U("pad_005", 0x05, "u16"), U("pad_007", 0x07, "u8"),
    I("param", 0x08, "s32"), I("value", 0x0C, "s32"),
    I("numinputs", 0x10, "u16"), I("version", 0x12, "u16"),
] + [I("input %d" % (k + 1), 0x14 + 8 * k + o, t, conv=_cube.in_part(part), part=part)
     for k in range(7) for part, o, t in _CUBE_IN]
  + _cube_output("output", "", 0x4C) + _cube_output("output b", "b ", 0xA0) + _cube_output("output c", "c ", 0xF4),
    txt_only={"description": "comment column (the recipe's description); not in the record",
              "*eol": "end-of-line marker column"})


# ------------------------------------------------------------------ charstats (196 B = 0xC4)
# Plan 0034 Phase 0 (docs/tables/CharStats.md). +0x000..+0x01F (32 bytes, 0 in the file) have no column; Class
# char[16]; the base attributes and per-level growth as u8 (PercentInt before PercentDex); ToHitFactor s32;
# baseWClass code; the five string keys as u16 string-table indices; ten 8-byte item slots (code, bodyloc u8,
# count u8, u16 0); StartSkill and Skill 1..10 as u16 skills rows (blank -1).
# StaminaPerLevel and StaminaPerVitality hold the same cells in every row (+0x044/+0x047 fit either): .txt order.
_CS_SKIP = {c: "editor column (animation frame note); not in the record"
            for c in ("#walk", "#run", "#swing", "#spell", "#gethit", "#bow")}
_CS_SKIP.update({"tot": "editor helper (sum of str/dex/int/vit); not in the record",
                 "Comment": "editor comment ('The following are in fourths'); not in the record"})
LAYOUTS["charstats"] = dict(size=0xC4, fields=[
    U("unk_000", 0x000, "str", len=32),
    S("class", 0x020, 16),
    I("str", 0x030, "u8"), I("dex", 0x031, "u8"), I("int", 0x032, "u8"), I("vit", 0x033, "u8"),
    I("stamina", 0x034, "u8"), I("hpadd", 0x035, "u8"),
    I("PercentStr", 0x036, "u8"), I("PercentInt", 0x037, "u8"), I("PercentDex", 0x038, "u8"),
    I("PercentVit", 0x039, "u8"), I("ManaRegen", 0x03A, "u8"), U("pad_03B", 0x03B, "u8"),
    I("ToHitFactor", 0x03C, "s32"),
    I("WalkVelocity", 0x040, "u8"), I("RunVelocity", 0x041, "u8"), I("RunDrain", 0x042, "u8"),
    I("LifePerLevel", 0x043, "u8"), I("StaminaPerLevel", 0x044, "u8"), I("ManaPerLevel", 0x045, "u8"),
    I("LifePerVitality", 0x046, "u8"), I("StaminaPerVitality", 0x047, "u8"), I("ManaPerMagic", 0x048, "u8"),
    I("BlockFactor", 0x049, "u8"), U("pad_04A", 0x04A, "u16"),
    C("baseWClass", 0x04C),
    I("StatPerLevel", 0x050, "u8"), U("pad_051", 0x051, "u8"),
    T("StrAllSkills", 0x052), T("StrSkillTab1", 0x054), T("StrSkillTab2", 0x056), T("StrSkillTab3", 0x058),
    T("StrClassOnly", 0x05A),
] + [f for k in range(10) for f in (
    C("item%d" % (k + 1), 0x05C + 8 * k),
    R("item%dloc" % (k + 1), 0x060 + 8 * k, "bodylocs:Code", "u8", blank=0),
    I("item%dcount" % (k + 1), 0x061 + 8 * k, "u8"),
    U("pad_%03X" % (0x062 + 8 * k), 0x062 + 8 * k, "u16"))]
  + [R("StartSkill", 0x0AC, "skills:skill", "u16", nocase=True)]
  + [R("Skill %d" % (k + 1), 0x0AE + 2 * k, "skills:skill", "u16", nocase=True) for k in range(10)]
  + [U("pad_0C2", 0x0C2, "u16")],
    txt_only=_CS_SKIP)

# ------------------------------------------------------------------ experience (32 B)
# Plan 0034 Phase 0 (docs/tables/Experience.md). Seven u32 class thresholds in .txt class order, then ExpRatio u32.
# Record 0 is the MaxLvl row (the per-class level cap), record L+1 the threshold of level L. The seven class
# columns hold the same cells in every row, so their order is the .txt order only.
_XP_CLASSES = ["Amazon", "Sorceress", "Necromancer", "Paladin", "Barbarian", "Druid", "Assassin"]
LAYOUTS["experience"] = dict(size=32, fields=[I(c, 4 * k, "u32") for k, c in enumerate(_XP_CLASSES)]
                             + [I("ExpRatio", 0x01C, "u32")],
                             txt_only={"Level": "row label (MaxLvl, 0..99); not in the record (the row index is)"})

# ------------------------------------------------------------------ chartemplate (240 B = 0xF0)
# Plan 0034 Phase 0 (docs/tables/CharTemplate.md). Name char[30], Class u8 (playerclass row), Level u8, Act u8,
# str/dex/int/vit u8, Mana u8, Hitpoints u8, the three rates u8, nine Skill s32 then nine SkillLevel s32, fifteen
# 8-byte item slots (code, loc u8 as written, count u8, u16 0). Velocity/AttackRate/OtherRate are 100 in every row
# (+0x028..+0x02A by .txt order); ManaRegenBonus and RightSkill are 0 in every row (+0x027, +0x02B..+0x02F zero).
_CT_SKIP = {"Template": "editor name of the template; not in the record",
            "tot": "editor helper (sum of str/dex/int/vit); not in the record",
            "Total Skills": "editor helper (count of skills); not in the record",
            "baseWClass": "hth in every row; no field holds it (every byte is another field or zero)"}
_CT_SKIP.update({c: "editor helper; not in the record (no field matches)"
                 for c in ("LifePerLevel", "ManaPerLevel", "LifePerVitality", "ManaPerMagic")})
_CT_SKIP.update({("SkillName" if k == 0 else "SkillName#%d" % (k + 1)): "editor label of Skill%d; not in the record"
                 % (k + 1) for k in range(9)})
_CT_SKIP.update({"ManaRegenBonus": "0 in every row; +0x027 or +0x02B..+0x02F (all zero), not identified",
                 "RightSkill": "0 in every row; +0x027 or +0x02B..+0x02F (all zero), not identified"})
LAYOUTS["chartemplate"] = dict(size=0xF0, fields=[
    S("Name", 0x000, 30),
    R("Class", 0x01E, "playerclass:Code", "u8"),
    I("Level", 0x01F, "u8"), I("Act", 0x020, "u8"),
    I("str", 0x021, "u8"), I("dex", 0x022, "u8"), I("int", 0x023, "u8"), I("vit", 0x024, "u8"),
    I("Mana", 0x025, "u8"), I("Hitpoints", 0x026, "u8"), U("unk_027", 0x027, "u8"),
    I("Velocity", 0x028, "u8"), I("AttackRate", 0x029, "u8"), I("OtherRate", 0x02A, "u8"),
    U("unk_02B", 0x02B, "u8"), U("unk_02C", 0x02C, "u32"),
] + [I("Skill%d" % (k + 1), 0x030 + 4 * k, "s32") for k in range(9)]
  + [I("SkillLevel%d" % (k + 1), 0x054 + 4 * k, "s32") for k in range(9)]
  + [f for k in range(15) for f in (
    C("item%d" % (k + 1), 0x078 + 8 * k),
    I("item%dloc" % (k + 1), 0x07C + 8 * k, "u8"),
    I("item%dcount" % (k + 1), 0x07D + 8 * k, "u8"),
    U("pad_%03X" % (0x07E + 8 * k), 0x07E + 8 * k, "u16"))],
    txt_only=_CT_SKIP)


# ------------------------------------------------------------------ missiles, skilldesc: formula columns only
# Plan 0035 Phase 0 (docs/formats/calc.md). Partial layouts: only the s32 offsets into misscode.bin /
# skilldesccode.bin. The record offsets are those of the loaders' descriptors read in data/0005 section 1 (plan 0035
# Phase 1); excel_bin.py diff and tools/calc_survey.py check them against every record.
LAYOUTS["missiles"] = dict(size=420, partial=True, fields=[
    K("SrvCalc1", 0x080, "misscode"), K("CltCalc1", 0x084, "misscode"), K("SHitCalc1", 0x088, "misscode"),
    K("CHitCalc1", 0x08C, "misscode"), K("DmgCalc1", 0x090, "misscode"),
    K("DmgSymPerCalc", 0x0E0, "misscode"), K("EDmgSymPerCalc", 0x118, "misscode")])
_SDC = "skilldesccode"
LAYOUTS["skilldesc"] = dict(size=288, partial=True, fields=[
    K("ddam calc1", 0x018, _SDC), K("ddam calc2", 0x01C, _SDC),
] + [K("p%ddmmin" % (k + 1), 0x024 + 4 * k, _SDC) for k in range(3)]
  + [K("p%ddmmax" % (k + 1), 0x030 + 4 * k, _SDC) for k in range(3)]
  + [K("desccalca%d" % (k + 1), 0x098 + 4 * k, _SDC) for k in range(6)]
  + [K("dsc2calca%d" % (k + 1), 0x0B0 + 4 * k, _SDC) for k in range(4)]
  + [K("dsc3calca%d" % (k + 1), 0x0C0 + 4 * k, _SDC) for k in range(7)]
  + [K("desccalcb%d" % (k + 1), 0x0DC + 4 * k, _SDC) for k in range(6)]
  + [K("dsc2calcb%d" % (k + 1), 0x0F4 + 4 * k, _SDC) for k in range(4)]
  + [K("dsc3calcb%d" % (k + 1), 0x104 + 4 * k, _SDC) for k in range(7)],
    explain={("desccalcb2", 95): "the cell is one space: no token, so no bytes and the field is -1 "
                                 "(docs/formats/calc.md, the one non-blank cell with no string)"})

# ------------------------------------------------------------------ skillcalc, misscalc (4 B)
# Plan 0035 Phase 0 (docs/tables/SkillCalc.md, MissCalc.md). Code lists: the formulas' variable names.
LAYOUTS["skillcalc"] = dict(size=4, fields=[C("code", 0x0)],
                            txt_only={"*desc": "editor comment (the variable's formula); not in the record"})
LAYOUTS["misscalc"] = dict(size=4, fields=[C("code", 0x0)],
                           txt_only={"*desc": "editor comment; not in the record"})
# ------------------------------------------------------------------ npc (76 B = 0x4C)
# Plan 0031 Phase 0 (docs/tables/Npc.md). u32 fields throughout. The base multipliers are stored sell, buy, rep (not
# the .txt order buy, sell, rep). The quest columns are grouped by kind: questflag A..C, questsellmult A..C, then two
# triplets that hold 1024 in every filled cell (questbuymult and questrepmult cannot be told apart by the stock data;
# buy before rep follows the base order). Group C is blank in every row: its slots follow the stride.
LAYOUTS["npc"] = dict(size=0x4C, fields=[
    R("npc", 0x00, "monstats:Id", "u32"),
    I("sell mult", 0x04, "u32"), I("buy mult", 0x08, "u32"), I("rep mult", 0x0C, "u32"),
] + [I("questflag %s" % g, 0x10 + 4 * k, "u32") for k, g in enumerate("ABC")]
  + [I("questsellmult %s" % g, 0x1C + 4 * k, "u32") for k, g in enumerate("ABC")]
  + [I("questbuymult %s" % g, 0x28 + 4 * k, "u32") for k, g in enumerate("ABC")]
  + [I("questrepmult %s" % g, 0x34 + 4 * k, "u32") for k, g in enumerate("ABC")]
  + [I("max buy", 0x40, "u32"), I("max buy (N)", 0x44, "u32"), I("max buy (H)", 0x48, "u32")])

# ------------------------------------------------------------------ books (32 B = 0x20)
# Plan 0043 Phase 0 (docs/tables/Books.md). One record per books.txt row (3). Name is the string index of the
# key `unused` (the same in every row); Namco and Completed have no field. ScrollSkill/BookSkill store the Skills row
# (blank = -1); the scroll and book codes follow the costs. +0x003 is 0 in every record.
LAYOUTS["books"] = dict(size=0x20, fields=[
    T("Name", 0x000), I("SpellIcon", 0x002, "s8"), U("pad_003", 0x003, "u8"),
    I("pSpell", 0x004, "u32"),
    R("ScrollSkill", 0x008, "skills:skill", "s32"), R("BookSkill", 0x00C, "skills:skill", "s32"),
    I("BaseCost", 0x010, "u32"), I("CostPerCharge", 0x014, "u32"),
    C("ScrollSpellCode", 0x018), C("BookSpellCode", 0x01C),
], txt_only={"Namco": "display suffix (\"of Town Portal\"); no field (its keys are not in the string tables)",
             "Completed": "1, 1, 0; no byte or bit follows it (+0x003 is 0 in every record)"})

# ------------------------------------------------------------------ gamble (12 B)
# Plan 0031 Phase 0 (docs/tables/Gamble.md). The item code, then 8 bytes that are 0 in every record (no column feeds
# them; filled at load or never, a question for the reverser).
LAYOUTS["gamble"] = dict(size=12, fields=[
    C("code", 0x0), U("unk_04", 0x4, "u32"), U("unk_08", 0x8, "u32"),
], txt_only={"name": "editor name of the base; not in the record"})

# ------------------------------------------------------------------ storepage (4 B)
# Plan 0031 Phase 0 (docs/tables/StorePage.md). Code list: the record is the 4-character code. Loaded only under -txt
# (data/0001 section 3), to resolve ItemTypes StorePage while compiling.
LAYOUTS["storepage"] = dict(size=4, fields=[C("Code", 0x0)],
                            txt_only={"Store Page": "editor name of the page; not in the record"})


# ------------------------------------------------------------------ hireling (280 B = 0x118)
# Plan 0033 Phase 0 (docs/tables/Hireling.md). s32 fields up to +0x077, then six skill slots in column-group order
# (Skill s32, Chance s32, ChancePerLvl s32, Mode u8, Level u8, LvlPerLvl u8), HireDesc u8, NameFirst/NameLast char[32].
# +0x114/+0x116 (u16 each, no column, 0 in the file) are the name string range save/0001 reads.
# Head and Weapon hold the same values in every row (+0x068/+0x070 both fit either); their order follows the .txt.
_HIRE_INT = ["Version", "Id", "Class", "Act", "Difficulty", "Seller", "Gold", "Level", "Exp/Lvl", "HP", "HP/Lvl",
             "Defense", "Def/Lvl", "Str", "Str/Lvl", "Dex", "Dex/Lvl", "AR", "AR/Lvl", "Share", "Dmg-Min", "Dmg-Max",
             "Dmg/Lvl", "Resist", "Resist/Lvl", "DefaultChance", "Head", "Torso", "Weapon", "Shield"]
# Widths from the loader's field descriptor (hirelings/0001 section 1): Version is u16 (+0x002 no field, 0), the
# Mode/Level/LvlPerLvl bytes are signed (a Mode > 15 signed ends the skill list).
LAYOUTS["hireling"] = dict(size=0x118, fields=[I("Version", 0x000, "u16"), U("pad_002", 0x002, "u16")]
  + [I(c, 4 * k, "s32") for k, c in enumerate(_HIRE_INT) if k]
  + [R("Skill%d" % (k + 1), 0x078 + 4 * k, "skills:skill", "s32") for k in range(6)]
  + [I("Chance%d" % (k + 1), 0x090 + 4 * k, "s32") for k in range(6)]
  + [I("ChancePerLvl%d" % (k + 1), 0x0A8 + 4 * k, "s32") for k in range(6)]
  + [I("Mode%d" % (k + 1), 0x0C0 + k, "s8") for k in range(6)]
  + [I("Level%d" % (k + 1), 0x0C6 + k, "s8") for k in range(6)]
  + [I("LvlPerLvl%d" % (k + 1), 0x0CC + k, "s8") for k in range(6)]
  + [R("HireDesc", 0x0D2, "hiredesc:Code", "u8"),
     S("NameFirst", 0x0D3, 32), S("NameLast", 0x0F3, 32),
     U("pad_113", 0x113, "u8"), U("unk_114", 0x114, "u16"), U("unk_116", 0x116, "u16")],
    txt_only={"Hireling": "editor name of the hireling kind; not in the record",
              "SubType": "editor sub-type label; not in the record",
              "WType1": "weapon item type code (bow, swor, spea, ...); no field matches",
              "WType2": "second weapon item type code (shie on some rows); no field matches"})

# ------------------------------------------------------------------ hiredesc (4 B)
# Plan 0033 Phase 0 (docs/tables/HireDesc.md). Code list, loaded only under -txt (data/0001 section 3).
LAYOUTS["hiredesc"] = dict(size=4, fields=[C("Code", 0x0)],
                           txt_only={"Hireling Description": "editor name; not in the record"})

# ------------------------------------------------------------------ states (60 B)
# docs/tables/States.md. Offsets by `excel_bin.py probe`. The 40 flag columns are bits 0..39 of the five bytes at
# +0x010; `exp` is flag bit 30 (+0x013 bit 6), the bit-set the loader builds at DataTables+0x144 (items/0010 section 2).
# rfred/rlred/rcred hold the same values in every row, so the data cannot tell bits 26..28 apart: they are assigned
# here in the order of the blue bits (rf, rc, rl = bits 20, 21, 22). Widths of the u16 fields whose high byte is 0
# in every row follow the packing of their neighbours.
_ST_FLAGS = [
    ("nosend", 0), ("aura", 1), ("hide", 2), ("transform", 3), ("pgsv", 4), ("active", 5), ("remhit", 6),
    ("damblue", 7), ("damred", 8), ("attblue", 9), ("curse", 11), ("curable", 12), ("plrstaydeath", 13),
    ("monstaydeath", 14), ("bossstaydeath", 15), ("disguise", 16), ("restrict", 17), ("blue", 18),
    ("armblue", 19), ("rfblue", 20), ("rcblue", 21), ("rlblue", 22), ("rpblue", 23), ("stambarblue", 24),
    ("armred", 25), ("rfred", 26), ("rcred", 27), ("rlred", 28), ("rpred", 29), ("exp", 30), ("shatter", 31),
    ("life", 32), ("udead", 33), ("green", 34), ("nooverlays", 35), ("noclear", 36), ("bossinv", 37),
    ("meleeonly", 38), ("notondead", 39)]
_OVL = "overlay:overlay"
LAYOUTS["states"] = dict(size=0x3C, fields=[
    I("id", 0x000, "u16"),
    R("overlay1", 0x002, _OVL, "u16"), R("overlay2", 0x004, _OVL, "u16"), R("overlay3", 0x006, _OVL, "u16"),
    R("overlay4", 0x008, _OVL, "u16"), R("castoverlay", 0x00A, _OVL, "u16"), R("removerlay", 0x00C, _OVL, "u16"),
    R("pgsvoverlay", 0x00E, _OVL, "u16")]
  + [B(c, 0x010 + k // 8, k % 8) for c, k in _ST_FLAGS]
  + [U("pad_015", 0x015, "u8"), U("pad_016", 0x016, "u16"),
     R("stat", 0x018, "itemstatcost:Stat", "u16"), I("setfunc", 0x01A, "u16"), I("remfunc", 0x01C, "u16"),
     I("group", 0x01E, "u8"), U("pad_01F", 0x01F, "u8"),
     I("colorpri", 0x020, "u8"), I("colorshift", 0x021, "u8"),
     I("light-r", 0x022, "u8"), I("light-g", 0x023, "u8"), I("light-b", 0x024, "u8"), U("pad_025", 0x025, "u8"),
     R("onsound", 0x026, "sounds:Sound", "u16", blank=0), R("offsound", 0x028, "sounds:Sound", "u16", blank=0),
     R("itemtype", 0x02A, "itemtypes:Code", "u16", blank=0), R("itemtrans", 0x02C, "colors:Code", "u8"),
     I("gfxtype", 0x02D, "u8"), I("gfxclass", 0x02E, "u16"),
     R("cltevent", 0x030, "events:event", "u16"), I("clteventfunc", 0x032, "u16"),
     I("cltactivefunc", 0x034, "u16"), I("srvactivefunc", 0x036, "u16"),
     R("skill", 0x038, "skills:skill", "u16", nocase=True), R("missile", 0x03A, "missiles:Missile", "u16")],
    txt_only={"state": "the row's name; the record holds id (+0x000), equal to the row index in every row",
              "immed": "1 on 12 rows, but no byte or bit of the record follows it; not located",
              "attred": "blank in every row; not located (flag bit 10, +0x011 bit 2, is 0 in every record)",
              "eol": "end-of-line marker column"})

# ------------------------------------------------------------------ elemtypes (4 B)
# Plan 0037 Phase 0 (docs/tables/ElemTypes.md). Code list: the record is the 4-character code; row 0 (`None`) has a
# blank code and stores four spaces. Loaded only under -txt (data/0001 section 3), to resolve the element columns
# (MonStats El<e>Type, Skills EType, ...) while compiling.
LAYOUTS["elemtypes"] = dict(size=4, fields=[C("Code", 0x0)],
                            txt_only={"Elemental Type": "editor name of the element; not in the record"})

# ------------------------------------------------------------------ monmode, plrmode (52 B = 0x34)
# Plan 0037 Phase 0 (docs/tables/MonMode.md, PlrMode.md). The ObjMode shape: the mode name, its two-letter Token
# (the animation token, not the Code column: `knockback` stores GH), then 16 bytes that are 0 in every record.
# The Code column (what other tables name a mode by) has no field. plrmode.bin is d2exp's, compiled from a .txt that
# had no Code column; the patch_d2 .txt added it and left Name and Token unchanged.
LAYOUTS["monmode"] = dict(size=0x34, fields=[
    S("name", 0x000, 32), C("token", 0x020), U("unk_024", 0x024, "str", len=16)],
    txt_only={"code": "the mode's code, the key other tables name it by (MonStats El<e>Mode, Sk<k>mode, ...); "
                      "not in the 52-byte record (the -txt code list reads it)"})
LAYOUTS["plrmode"] = dict(size=0x34, fields=[
    S("Name", 0x000, 32), C("Token", 0x020), U("unk_024", 0x024, "str", len=16)],
    txt_only={"Code": "the mode's code (Skills anim, seqtrans); not in the 52-byte record, and absent from the "
                      "d2exp .txt the shipped .bin was compiled from"})
