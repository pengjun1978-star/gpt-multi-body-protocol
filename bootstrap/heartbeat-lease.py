#!/usr/bin/env python3
import json,sys,time
from pathlib import Path

def main():
    if len(sys.argv) != 3:
        raise SystemExit('usage: heartbeat-lease.py STATE.json COMMAND')
    p, cmd = Path(sys.argv[1]), sys.argv[2]
    d=json.loads(p.read_text()) if p.exists() else {'nodes':{},'leases':{},'events':[]}
    now=int(time.time())
    if cmd.startswith('heartbeat:'):
        node=cmd.split(':',1)[1]; d['nodes'][node]={'last_heartbeat':now,'state':'ONLINE'}
    elif cmd.startswith('lease:'):
        _,task,node,ttl=cmd.split(':'); d['leases'][task]={'node_id':node,'started_at':now,'expires_at':now+int(ttl),'state':'RUNNING','side_effect_state':'NONE'}
    elif cmd.startswith('evaluate:'):
        _,task,age=cmd.split(':'); lease=d['leases'][task]; age=int(age)
        if age <= lease['expires_at']-lease['started_at']: lease['state']='RUNNING'
        elif age <= 2*(lease['expires_at']-lease['started_at']): lease['state']='STALE'
        else: lease['state']='ORPHANED'
        d['events'].append({'task_id':task,'state':lease['state'],'at':now})
    elif cmd.startswith('recover:'):
        _,task,action=cmd.split(':'); lease=d['leases'][task]
        if lease['state']!='ORPHANED': raise SystemExit('RECOVERY_REQUIRES_ORPHANED')
        if action=='retry' and lease['side_effect_state']=='NONE': lease['state']='RETRY'
        elif action=='reroute' and lease['side_effect_state']=='NONE': lease['state']='REROUTE'
        else: lease['state']='BLOCKED'
    else: raise SystemExit('unknown command')
    p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(d,ensure_ascii=False))
main()
