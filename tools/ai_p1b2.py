#!/usr/bin/env python3
"""Plan 0052 Phase 1b case P1b-2 (docs/findings/ai/0014 section 4): per case log of a session run with AI_P1B2=1 (tools/gdb/ai-p1b2.py),
the placements (P12 lines), the Greater Mummy (AI row 22) decisions, and for each MonSkillTargetOk call (0x005FD470) of those decisions the
kind of corpse that was its second argument (champ, uniq, unplaced) and its result; with the command that followed.

    python3 -I tools/ai_p1b2.py CASE_LOG [CASE_LOG ...]
Stdlib only."""
import sys,json,collections
# per case log: P12 placements (unit ptr -> kind), GM decisions (ai 22), MonSkillTargetOk (0x5fd470) calls: arg1 = corpse ptr, AIR eax
for f in sys.argv[1:]:
    L=open(f,errors='replace').read().split('\n')
    kind={}; cls={}
    dec={}
    air={}
    out=collections.Counter()
    for l in L:
        t=l.split(' ',1)[0]
        if t=='P12' and ' place ' in l:
            kv=dict(x.split('=') for x in l.split()[2:] if '=' in x)
            kind[int(kv['u'])]=kv['kind']; cls[int(kv['u'])]=kv['cls']
    for l in L:
        t=l.split(' ',1)[0]
        if t=='AID':
            d=json.loads(l[4:]); dec[d['n']]=d
            if d['ai']==22: out['gm_decisions']+=1
        elif t=='AIB':
            d=json.loads(l[4:])
            if d['k'] in dec and dec[d['k']]['ai']==22 and d['fn']==0x5fd470:
                air[d['n']]=d
        elif t=='AIR':
            d=json.loads(l[4:])
            if d['b'] in air:
                b=air[d['b']]; u=b['a'][1]
                out[('FD470',kind.get(u,'unplaced'),b['a'][0],'eax=%d'%d['eax'])]+=1
    print(f.split('/')[-1]); print(' placed', collections.Counter(kind.values())); 
    for k,v in sorted(out.items(),key=str): print('  ',k,v)
