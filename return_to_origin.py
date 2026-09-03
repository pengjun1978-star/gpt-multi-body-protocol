"""Durable Return-to-Origin binding and callback delivery for v1.1.1 Gate C.

The transport adapter is deliberately explicit: accepted by an adapter is not
the same as visible in the parent GPT UI.  The bundled adapter records the
platform boundary and queues safely for retry.
"""
from __future__ import annotations
import hashlib, json, sqlite3, time, uuid
from pathlib import Path

DELIVERY = ("PENDING", "ACCEPTED", "DELIVERED", "ACKED", "OUTBOX")

class PlatformBoundary(RuntimeError): pass

class ReturnToOrigin:
    def __init__(self, db_path: str | Path):
        self.db_path = str(db_path)
        with sqlite3.connect(self.db_path) as c:
            c.executescript("""
            CREATE TABLE IF NOT EXISTS route_bindings(
              task_id TEXT PRIMARY KEY, parent_gpt_conversation_id TEXT NOT NULL,
              origin_route TEXT NOT NULL, codex_thread_id TEXT NOT NULL,
              codex_session_id TEXT, branch TEXT, generation INTEGER NOT NULL,
              created_at REAL NOT NULL, updated_at REAL NOT NULL);
            CREATE TABLE IF NOT EXISTS callbacks(
              callback_event_id TEXT PRIMARY KEY, task_id TEXT NOT NULL,
              idempotency_key TEXT UNIQUE NOT NULL, envelope TEXT NOT NULL,
              delivery_state TEXT NOT NULL, attempts INTEGER NOT NULL DEFAULT 0,
              last_error TEXT, ack_id TEXT, accepted_at REAL, delivered_at REAL,
              acked_at REAL);
            """)

    def _conn(self): return sqlite3.connect(self.db_path)
    def bind(self, *, task_id, parent_gpt_conversation_id=None, origin_route=None,
             codex_thread_id, codex_session_id=None, branch=None, generation=0,
             inherit_task_id=None):
        now = time.time()
        if inherit_task_id:
            with self._conn() as c:
                row = c.execute("SELECT * FROM route_bindings WHERE task_id=?", (inherit_task_id,)).fetchone()
            if not row: raise KeyError("PARENT_ROUTE_NOT_FOUND")
            parent_gpt_conversation_id, origin_route = row[1], row[2]
        with self._conn() as c:
            c.execute("""INSERT INTO route_bindings VALUES(?,?,?,?,?,?,?,?,?)
              ON CONFLICT(task_id) DO UPDATE SET codex_thread_id=excluded.codex_thread_id,
              codex_session_id=excluded.codex_session_id,branch=excluded.branch,
              generation=excluded.generation,updated_at=excluded.updated_at""",
              (task_id,parent_gpt_conversation_id,json.dumps(origin_route,ensure_ascii=False),
               codex_thread_id,codex_session_id,branch,generation,now,now))
        return self.route(task_id)
    def route(self, task_id):
        with self._conn() as c: row=c.execute("SELECT * FROM route_bindings WHERE task_id=?",(task_id,)).fetchone()
        if not row: raise KeyError("PARENT_ROUTE_NOT_FOUND")
        d=dict(zip(("task_id","parent_gpt_conversation_id","origin_route","codex_thread_id","codex_session_id","branch","generation","created_at","updated_at"),row)); d["origin_route"]=json.loads(d["origin_route"]); return d
    def envelope(self, *, task_id, status, body, evidence=None, receipt=None, limitations=None, next_action=None):
        r=self.route(task_id); event_id=str(uuid.uuid4())
        e={"schema_version":"1.1.1-gate-c","callback_event_id":event_id,"task_id":task_id,"status":status,
           "execution_generation":r["generation"],"body":body,"origin":{"parent_gpt_conversation_id":r["parent_gpt_conversation_id"],"route":r["origin_route"]},
           "thread":{"codex_thread_id":r["codex_thread_id"],"codex_session_id":r["codex_session_id"]},"branch":r["branch"],"commit":None,
           "evidence":evidence or [],"receipts":receipt or [],"limitations":limitations or [],"next_action":next_action}
        key=hashlib.sha256(json.dumps(e,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
        with self._conn() as c: c.execute("INSERT INTO callbacks VALUES(?,?,?,?,?,?,?,?,?,?,?)",(event_id,task_id,key,json.dumps(e,ensure_ascii=False),"PENDING",0,None,None,None,None,None))
        return e
    def deliver(self, callback_event_id, adapter):
        with self._conn() as c: row=c.execute("SELECT * FROM callbacks WHERE callback_event_id=?",(callback_event_id,)).fetchone()
        if not row: raise KeyError(callback_event_id)
        if row[4] in ("ACKED","DELIVERED","ACCEPTED"): return row[4]
        e=json.loads(row[3]); attempts=row[5]+1
        try:
            result=adapter.send(e); state=result.get("state","ACCEPTED")
            with self._conn() as c: c.execute("UPDATE callbacks SET attempts=?,delivery_state=?,accepted_at=? WHERE callback_event_id=?",(attempts,state,time.time(),callback_event_id))
            return state
        except Exception as exc:
            with self._conn() as c: c.execute("UPDATE callbacks SET attempts=?,delivery_state='OUTBOX',last_error=? WHERE callback_event_id=?",(attempts,str(exc),callback_event_id))
            return "OUTBOX"
    def acknowledge(self, callback_event_id, ack_id):
        with self._conn() as c:
            row=c.execute("SELECT delivery_state FROM callbacks WHERE callback_event_id=?",(callback_event_id,)).fetchone()
            if not row or row[0] not in ("ACCEPTED","DELIVERED"): raise ValueError("ACK_REJECTED")
            c.execute("UPDATE callbacks SET delivery_state='ACKED',ack_id=?,acked_at=? WHERE callback_event_id=?",(ack_id,time.time(),callback_event_id))
        return "ACKED"

class ParentGPTTransport:
    """Platform adapter contract. Current product cannot confirm parent UI visibility."""
    def send(self, envelope):
        raise PlatformBoundary("PLATFORM_BOUNDARY: no supported parent-GPT UI transport adapter")

class RecordingTransport:
    """Test adapter: proves correct route and idempotent delivery semantics."""
    def __init__(self, fail=False): self.fail, self.sent = fail, []
    def send(self, envelope):
        if self.fail: raise ConnectionError("ROUTE_UNAVAILABLE")
        if envelope["callback_event_id"] not in [x["callback_event_id"] for x in self.sent]: self.sent.append(envelope)
        return {"state":"ACCEPTED"}
