#!/bin/zsh
set -euo pipefail
state_file="${1:-}"
max_age="${2:-300}"
[[ -n "$state_file" && -f "$state_file" ]] || { print -u2 "usage: $0 STATE_JSON [MAX_AGE_SECONDS]"; exit 64; }
/usr/bin/python3 - "$state_file" "$max_age" <<'PY'
import json,sys,time
p,limit=sys.argv[1],int(sys.argv[2])
with open(p,encoding='utf-8') as f: d=json.load(f)
thread=d.get('thread_status'); receipt=d.get('receipt_status'); heartbeat_age=d.get('heartbeat_age_seconds')
if thread=='idle' and receipt=='completed': result='COMPLETED'
elif d.get('explicit_blocked') is True or d.get('recovery_state')=='BLOCKED': result='BLOCKED'
elif heartbeat_age is not None and heartbeat_age > limit:
    result='STALE_REQUIRES_RECOVERY'
else: result='ACTIVE_CONTINUE_MONITORING'
print(json.dumps({'result':result,'thread_status':thread,'receipt_status':receipt,'heartbeat_age_seconds':heartbeat_age,'max_wait_seconds':limit},ensure_ascii=False))
PY
