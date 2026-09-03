"""Durable legacy-to-successor generation lineage."""
import sqlite3, uuid
from datetime import datetime, timezone

class SuccessorLineage:
    def __init__(self,path):
        self.db=sqlite3.connect(path); self.db.execute('''CREATE TABLE IF NOT EXISTS lineage (business_task_id TEXT, execution_generation INTEGER, codex_thread_session_id TEXT PRIMARY KEY, predecessor_session_id TEXT, transition_reason TEXT, created_at TEXT, status TEXT)'''); self.db.commit()
    def add(self,business_task_id,generation,session,predecessor,reason,status='ACTIVE'):
        uuid.UUID(session); uuid.UUID(predecessor)
        if self.db.execute('SELECT 1 FROM lineage WHERE business_task_id=? AND execution_generation=?',(business_task_id,generation)).fetchone(): raise ValueError('GENERATION_ALREADY_EXISTS')
        self.db.execute('INSERT INTO lineage VALUES (?,?,?,?,?,?,?)',(business_task_id,generation,session,predecessor,reason,datetime.now(timezone.utc).isoformat(),status)); self.db.commit()
    def get(self,session):
        r=self.db.execute('SELECT * FROM lineage WHERE codex_thread_session_id=?',(session,)).fetchone(); return dict(zip(('business_task_id','execution_generation','codex_thread_session_id','predecessor_session_id','transition_reason','created_at','status'),r)) if r else None
