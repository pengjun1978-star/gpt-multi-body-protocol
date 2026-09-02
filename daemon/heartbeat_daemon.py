#!/usr/bin/env python3
import argparse,json,os,signal,time
from pathlib import Path
from time_utils import canonical_from_epoch, canonical_now, now_epoch

STOP=False
def stop(*_):
    global STOP; STOP=True
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--node-id',required=True); ap.add_argument('--role',required=True); ap.add_argument('--state-dir',required=True); ap.add_argument('--interval',type=int,default=15); ap.add_argument('--once',action='store_true'); a=ap.parse_args()
    d=Path(a.state_dir); d.mkdir(parents=True,exist_ok=True); state=d/'health.json'; log=d/'heartbeat.log'
    signal.signal(signal.SIGTERM,stop); signal.signal(signal.SIGINT,stop)
    while not STOP:
        now=now_epoch(); prior={}
        if state.exists():
            try: prior=json.loads(state.read_text())
            except Exception: prior={}
        out={'schema':'heartbeat-lease','node_id':a.node_id,'role':a.role,'state':'BUSY' if prior.get('current_task') else 'ONLINE','last_heartbeat_epoch':now,'last_heartbeat':canonical_from_epoch(now),'current_task':prior.get('current_task'), 'lease':prior.get('lease'), 'protocol_version':'1.0.1','base_version':'1.0','canonical_timezone':'Asia/Shanghai','time_semantics':'epoch/UTC instant for age and TTL; +08:00 for serialization'}
        tmp=state.with_suffix('.tmp'); tmp.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n'); os.replace(tmp,state)
        with log.open('a') as f: f.write(json.dumps({'at':canonical_now(),'at_epoch':now,'event':'heartbeat','node_id':a.node_id})+'\n')
        if a.once: break
        time.sleep(a.interval)
if __name__=='__main__': main()
