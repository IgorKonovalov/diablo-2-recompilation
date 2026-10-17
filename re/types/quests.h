/* Quest engine and travel structures (partial: only the fields findings cite). Field names are ours.
 * Evidence: docs/findings/quests/0001-progression.md, docs/findings/quests/0002-travel.md,
 * docs/findings/items/0010-quest-drops.md (quest object and control, first read in plan 0032). [I] unless noted. */
#include <stdint.h>

typedef struct QuestDesc {        /* g_QuestDescs (0x00731510), 37 records, count at 0x00731888 */
    void   * pInit;               /* +0x00 init function (ECX = quest object) */
    uint8_t  act;                 /* +0x04 act 0..4 (dword in the image) */
    uint8_t  _pad05[3];
    uint32_t unk08;               /* +0x08 100 or 0; no reader found */
    uint8_t  noJoinMark;          /* +0x0C non-zero: skipped by the join's bit-15 pass (dword in the image) */
    uint8_t  _pad0D[3];
    int32_t  questId;             /* +0x10 quest object id */
    int32_t  word;                /* +0x14 record word marked by the join's bit-15 pass */
} QuestDesc;

typedef struct QuestDesc2 {       /* second table (0x0073188C), 4 records, count at 0x007318AC: ids 37 + i */
    void   * pInit;               /* +0x00 */
    uint32_t act;                 /* +0x04 0, 1, 2, 4 */
} QuestDesc2;

typedef struct QuestObject {      /* 0xF8 bytes, one per descriptor, .\QUESTS\QUESTS.CPP */
    int32_t  questId;             /* +0x00 */
    struct Game * pGame;          /* +0x04 */
    uint8_t  act;                 /* +0x08 the dispatch's act filter compares it */
    uint8_t  active;              /* +0x09 1 at init (0 for the second table); 0 when the first joiner had the quest done */
    uint8_t  getsEvents;          /* +0x0A 1: receives unforced events (set by every init) */
    uint8_t  state;               /* +0x0B broadcast state (0x00544300) */
    uint8_t  step;                /* +0x0C quest step (0x00544350, "changing state to %d") */
    uint8_t  lastStep;            /* +0x0D set by the init */
    uint8_t  _pad0E[2];
    int32_t  nextQuest;           /* +0x10 quest id whose +0xF0 is called when this one is done (ChainNext) */
    uint8_t  _pad14[4];
    void   * pPrivate;            /* +0x18 per-quest private data */
    uint32_t players[32];         /* +0x1C player guids (quest-specific use), count at +0x9C */
    uint16_t nPlayers;            /* +0x9C */
    uint8_t  _pad9E[2];
    void   * pEvent[15];          /* +0xA0 event callbacks 0..12; +0xD4 (13) first join, +0xD8 (14) later join */
    void   * pDialogue;           /* +0xDC dialogue table (presentation) */
    int32_t  word;                /* +0x0E0 record word */
    int32_t  word2;               /* +0x0E4 second word (word 1's object: 41) */
    void   * pLogState;           /* +0x0E8 quest-log state callback, 0 = 0x00543F90 */
    void   * pNpcHasQuest;        /* +0x0EC (ECX quest, EDX npc class, gameRec, playerRec) -> bool */
    void   * pChainStart;         /* +0x0F0 start, or pass to nextQuest's */
    struct QuestObject * pNext;   /* +0x0F4 list, head = QuestControl+0x00, last created first */
} QuestObject;

typedef struct QuestTimer {       /* 0x14 bytes, 0x00543F10 */
    void   * pFn;                 /* +0x00 returns 1 to be removed */
    struct QuestObject * pQuest;  /* +0x04 */
    uint32_t due;                 /* +0x08 tick at which it runs */
    uint32_t period;              /* +0x0C */
    struct QuestTimer * pNext;    /* +0x10 */
} QuestTimer;

typedef struct QuestControl {     /* Game+0x10F4, allocated by QUESTS_InitGame */
    struct QuestObject * pHead;   /* +0x00 */
    uint32_t running;             /* +0x04 1 while the timers run */
    uint32_t recordReady;         /* +0x08 set by the first join */
    void   * pGameRecord;         /* +0x0C game-wide quest record (96 bytes) */
    struct QuestTimer * pTimers;  /* +0x10 */
    uint32_t tick;                /* +0x14 incremented once per game tick */
    uint32_t seed[2];             /* +0x18 quest seed ([C], items/0010) */
    uint8_t  byte20;              /* +0x20 written by 0x00545760 */
} QuestControl;

typedef struct QuestEvent {       /* event block passed in EDI (dispatch) or EDX (callbacks) */
    struct Game * pGame;          /* +0x00 */
    int32_t  event;               /* +0x04 0..12 */
    void   * pUnit;               /* +0x08 the hooked unit, NPC, item */
    void   * pPlayer;             /* +0x0C */
    uint32_t arg10;               /* +0x10 */
    uint32_t arg14;               /* +0x14 e3: level left; e11: NPC class */
    uint32_t arg18;               /* +0x18 e3: level entered; e11: message id */
} QuestEvent;

typedef struct PlayerTravel {     /* view of PlayerData (unit+0x14 of a player) for travel */
    uint8_t  _pad000[0x48];
    uint32_t ownPortalId;         /* +0x048 the player's field portal (class 59) */
    uint32_t actChangeBusy;       /* +0x04C 1 after an act change; blocks operates */
    uint8_t  _pad050[0x110];
    uint32_t tickStamp;           /* +0x160 GetTickCount() written by 0x0055B720 */
} PlayerTravel;
