#!/usr/bin/env python3
import argparse,json,time
from pathlib import Path
from time_utils import canonical_from_epoch, canonical_now, now_epoch
def main():
 ap=argparse.ArgumentParser(); ap.add_argument('state',nargs='+'); ap.add_argument('--stale-after',type=int,default=45); ap.add_argument('--orphan-after',type=int,default=90); a=ap.parse_args(); now=now_epoch(); out=[]
 for x in a.state:
  p=Path(x); d=json.loads(p.read_text()); heartbeat_epoch=d.get('last_heartbeat_epoch', d.get('last_heartbeat')); age=max(0,now-float(heartbeat_epoch)); s='ONLINE' if age<=a.stale_after else ('STALE' if age<=a.orphan_after else 'ORPHANED'); out.append({'node_id':d['node_id'],'age_seconds':age,'last_heartbeat_epoch':heartbeat_epoch,'last_heartbeat':canonical_from_epoch(float(heartbeat_epoch)),'lease_ttl_seconds':(d.get('lease') or {}).get('expires_at',0)-now if d.get('lease') else None,'current_task':d.get('current_task'),'state':s})
 print(json.dumps({'evaluated_at':canonical_now(),'evaluated_at_epoch':now,'canonical_timezone':'Asia/Shanghai','nodes':out},ensure_ascii=False,indent=2))
if __name__=='__main__': main()
