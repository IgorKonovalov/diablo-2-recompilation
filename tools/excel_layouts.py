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
                                      itemtypes:Code)
  T(col, off)                         u16 string-table index of the key in the cell (tools/tbl.py)
  K(col, off, code)                   s32 offset into the header-less <code>.bin bytecode; -1 = blank
  U(name, off, type)                  field with no .txt column (unknown or derived); documented, not diffed

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
    U("unk_0F0", 0x0F0, "u32"),
    T("namestr", 0x0F4),
    I("version", 0x0F6, "u16"), I("auto prefix", 0x0F8, "u16"), I("missiletype", 0x0FA, "u16"),
    I("rarity", 0x0FC, "u8"), I("level", 0x0FD, "u8"),
    I("mindam", 0x0FE, "u8"), I("maxdam", 0x0FF, "u8"), I("minmisdam", 0x100, "u8"), I("maxmisdam", 0x101, "u8"),
    I("2handmindam", 0x102, "u8"), I("2handmaxdam", 0x103, "u8"),
    I("rangeadder", 0x104, "s16"), I("StrBonus", 0x106, "s16"), I("DexBonus", 0x108, "s16"),
    I("reqstr", 0x10A, "u16"), I("reqdex", 0x10C, "u16"),
    I("absorbs", 0x10E, "u8"), I("invwidth", 0x10F, "u8"), I("invheight", 0x110, "u8"), I("block", 0x111, "u8"),
    I("durability", 0x112, "u8"), I("nodurability", 0x113, "u8"),
    U("unk_114", 0x114, "u8"),
    I("component", 0x115, "u8"),
    I("rArm", 0x116, "u8"), I("lArm", 0x117, "u8"), I("Torso", 0x118, "u8"), I("Legs", 0x119, "u8"),
    I("rSPad", 0x11A, "u8"), I("lSPad", 0x11B, "u8"),
    I("2handed", 0x11C, "u8"), I("useable", 0x11D, "u8"),
    R("type", 0x11E, "itemtypes:Code", "u16"),
    R("type2", 0x120, "itemtypes:Code", "u16"),
    U("unk_122", 0x122, "u16"),
    R("dropsound", 0x124, "sounds:Sound", "u16"),
    R("usesound", 0x126, "sounds:Sound", "u16"),
    I("dropsfxframe", 0x128, "u8"), I("unique", 0x129, "u8"), I("quest", 0x12A, "u8"),
    I("questdiffcheck", 0x12B, "u8"), I("transparent", 0x12C, "u8"), I("transtbl", 0x12D, "u8"),
    U("unk_12E", 0x12E, "u8"),
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
    "gemoffset": "0 in every row; not located",
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
    U("pad_00A", 0x00A, "u16"),
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
    U("unk_02A", 0x02A, "u16"),
    I("PartyMin", 0x02C, "u8"), I("PartyMax", 0x02D, "u8"), I("Rarity", 0x02E, "u8"),
    I("MinGrp", 0x02F, "u8"), I("MaxGrp", 0x030, "u8"), I("sparsePopulate", 0x031, "u8"),
    I("Velocity", 0x032, "u16"), I("Run", 0x034, "u16"),
    U("unk_036", 0x036, "u32"),
] + [R(c, 0x03A + 2 * k, "missiles:Missile", "u16")
     for k, c in enumerate(["MissA1", "MissA2", "MissS1", "MissS2", "MissS3", "MissS4", "MissC", "MissSQ"])] + [
    U("unk_04A", 0x04A, "u16"),
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
    I("Id", 0x000, "u16"), I("Pal", 0x002, "u8"), I("Act", 0x003, "u8"),
    I("Teleport", 0x004, "u8"), I("Rain", 0x005, "u8"), I("Mud", 0x006, "u8"), I("NoPer", 0x007, "u8"),
    I("IsInside", 0x008, "u8"), I("DrawEdges", 0x009, "u8"),
    U("unk_00A", 0x00A, "u16"),
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
  + [I("camt%d" % (k + 1), 0x0DC + 2 * k, "u16") for k in range(4)] + [
    I("Waypoint", 0x0E4, "u8"),
] + [I("ObjGrp%d" % k, 0x0E5 + k, "u8") for k in range(8)] \
  + [I("ObjPrb%d" % k, 0x0ED + k, "u8") for k in range(8)] + [
    S("LevelName", 0x0F5, 40), S("LevelWarp", 0x11D, 40), S("EntryFile", 0x145, 40),
    U("unk_16D", 0x16D, "str", len=0xA3),
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
RARE_FIELDS = [
    U("unk_000", 0x000, "u32"), U("unk_004", 0x004, "u32"), U("unk_008", 0x008, "u32"), U("unk_00C", 0x00C, "u32"),
] + [R("itype%d" % (k + 1), 0x010 + 2 * k, _IT, "u16") for k in range(7)] \
  + [R("etype%d" % (k + 1), 0x01E + 2 * k, _IT, "u16") for k in range(4)] + [
    S("name", 0x026, 34),
]
_RARE_TXT_ONLY = {
    "version": "0 in every row; not located (+0x000..+0x00F are 0 in every record)",
    "add": "not located (+0x000..+0x00F are 0 in every record)",
    "multiply": "not located (+0x000..+0x00F are 0 in every record)",
    "divide": "not located (+0x000..+0x00F are 0 in every record)",
}
for _t in ("rareprefix", "raresuffix"):
    LAYOUTS[_t] = dict(size=72, fields=RARE_FIELDS, txt_only=_RARE_TXT_ONLY)

# ------------------------------------------------------------------ itemstatcost (324 B), partial
# Only the save columns that tools/d2s.py reads (docs/formats/d2s.md); the full table belongs to
# items/properties. Offsets from `excel_bin.py probe`. Integer widths are the widest type probe accepts
# (the cells are all >= 0, so signedness is not pinned by data). CSvParam (blank in every row) and
# CSvSigned (blank or 0) match hundreds of zero bytes, so the data cannot place them.
LAYOUTS["itemstatcost"] = dict(size=324, fields=[
    I("ID", 0x000, "u16"),
    I("CSvBits", 0x00A, "u8"),
    I("Save Bits", 0x019, "u8"),
    I("Save Add", 0x01C, "s32"),
    I("Save Param Bits", 0x024, "u32"),
], txt_only={
    "CSvParam": "blank in every row; matches any always-zero byte, so its offset is not pinned by data",
    "CSvSigned": "blank or 0 in every row; matches any always-zero byte, so its offset is not pinned by data",
})

# ------------------------------------------------------------------ lvltypes (1928 B = 0x788)
# One record per LvlTypes.txt row. File 1..32 are DT1 paths relative to data/global/tiles, 0x3C
# apart from +0x000, matching DRLG_LoadLvlTypes / DRLG_LevelDt1ListBuild (docs/findings/drlg/0001).
# tools/dt1.py lvltypes prints one type's paths.
LAYOUTS["lvltypes"] = dict(size=0x788, fields=[
    S("File %d" % (i + 1), 0x3C * i, 0x3C) for i in range(32)
] + [
    I("Act", 0x780, "u32"), I("Expansion", 0x784, "u32"),
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
LAYOUTS["uniqueitems"] = dict(size=332, partial=True, fields=[
    U("unk_000", 0x000, "u16"),
    S("index", 0x002, 34),
    I("version", 0x024, "u32"),
    C("code", 0x028),
    B("enabled", 0x02C, 0), B("carry1", 0x02C, 2), B("ladder", 0x02C, 3),
    I("rarity", 0x030, "u32"),
    I("lvl", 0x034, "u16"), I("lvl req", 0x036, "u16"),
    R("chrtransform", 0x038, "colors:Code", "u8"),
    R("invtransform", 0x039, "colors:Code", "u8"),
    S("flippyfile", 0x03A, 32), S("invfile", 0x05A, 32),
    U("unk_07A", 0x07A, "u16"),
    I("cost mult", 0x07C, "u32"), I("cost add", 0x080, "u32"),
    R("dropsound", 0x084, "sounds:Sound", "u16", blank=0),
    R("usesound", 0x086, "sounds:Sound", "u16", blank=0),
    I("dropsfxframe", 0x088, "u32"),
], txt_only={"nolimit": "blank in every row; matches any always-zero byte or bit, so its position is not pinned by data"})

# ------------------------------------------------------------------ setitems (440 B), partial
# Same head shape as uniqueitems, shifted. prop1..9 and aprop1a..5b (+0x088..) are out of scope.
# chrtransform/invtransform are equal in every row, and flippyfile/invfile/dropsound/usesound/
# dropsfxframe are blank in every row, so their order within their slots follows uniqueitems and the
# .txt, not the data (docs/tables/SetItems.md).
LAYOUTS["setitems"] = dict(size=440, partial=True, fields=[
    U("unk_000", 0x000, "u16"),
    S("index", 0x002, 34),
    U("unk_024", 0x024, "u32"),
    C("item", 0x028),
    R("set", 0x02C, "sets:index", "u32"),
    I("lvl", 0x030, "u16"), I("lvl req", 0x032, "u16"),
    I("rarity", 0x034, "u32"),
    I("cost mult", 0x038, "u32"), I("cost add", 0x03C, "u32"),
    R("chrtransform", 0x040, "colors:Code", "u8"),
    R("invtransform", 0x041, "colors:Code", "u8"),
    S("flippyfile", 0x042, 32), S("invfile", 0x062, 32),
    R("dropsound", 0x082, "sounds:Sound", "u16", blank=0),
    R("usesound", 0x084, "sounds:Sound", "u16", blank=0),
    I("dropsfxframe", 0x086, "u8"),
    I("add func", 0x087, "u8"),
])

# ------------------------------------------------------------------ colors (4 B), compcode (4 B), armtype (52 B)
LAYOUTS["colors"] = dict(size=4, fields=[C("Code", 0x000)],
                         txt_only={"Transform Color": "editor name; not in the record"})
LAYOUTS["compcode"] = dict(size=4, fields=[C("code", 0x000)],
                           txt_only={"component": "editor name; not in the record"})
LAYOUTS["armtype"] = dict(size=52, fields=[
    S("Name", 0x000, 32), C("Token", 0x020),
    U("unk_024", 0x024, "u32"), U("unk_028", 0x028, "u32"), U("unk_02C", 0x02C, "u32"), U("unk_030", 0x030, "u32"),
])

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
