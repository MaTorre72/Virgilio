from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo


ROME_TZ = ZoneInfo("Europe/Rome")


def rome_now() -> datetime:
    return datetime.now(ROME_TZ)


def rome_isoformat() -> str:
    return rome_now().isoformat()


def rome_timestamp() -> str:
    return rome_now().strftime("%Y%m%d_%H%M%S")


def rome_min() -> datetime:
    return datetime.min.replace(tzinfo=ROME_TZ)
