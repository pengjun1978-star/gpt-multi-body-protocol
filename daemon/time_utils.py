"""v1.0.1 time contract: epoch for calculations, Asia/Shanghai for output."""
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

BEIJING = ZoneInfo("Asia/Shanghai")

def now_epoch() -> float:
    return datetime.now(timezone.utc).timestamp()

def canonical_now() -> str:
    return datetime.now(timezone.utc).astimezone(BEIJING).isoformat(timespec="milliseconds")

def canonical_from_epoch(value: float) -> str:
    return datetime.fromtimestamp(float(value), timezone.utc).astimezone(BEIJING).isoformat(timespec="milliseconds")
