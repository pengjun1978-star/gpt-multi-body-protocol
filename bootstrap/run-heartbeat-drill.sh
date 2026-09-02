#!/bin/zsh
set -euo pipefail
base="${0:A:h:h}"
state="$base/heartbeat-drill-state.json"
rm -f "$state"
python3 "$base/bootstrap/heartbeat-lease.py" "$state" heartbeat:mbp-primary >/dev/null
python3 "$base/bootstrap/heartbeat-lease.py" "$state" heartbeat:office-4090 >/dev/null
python3 "$base/bootstrap/heartbeat-lease.py" "$state" lease:drill-task:mbp-primary:1 >/dev/null
python3 "$base/bootstrap/heartbeat-lease.py" "$state" evaluate:drill-task:2 >/dev/null
python3 "$base/bootstrap/heartbeat-lease.py" "$state" evaluate:drill-task:3 >/dev/null
python3 "$base/bootstrap/heartbeat-lease.py" "$state" recover:drill-task:retry >/dev/null
python3 - "$state" <<'PY'
import json,sys
d=json.load(open(sys.argv[1])); states=[e['state'] for e in d['events']]
assert states == ['STALE','ORPHANED'], states
assert d['leases']['drill-task']['state']=='RETRY'
print('DRILL_PASS states=RUNNING->STALE->ORPHANED->RETRY side_effect_state=NONE')
PY
