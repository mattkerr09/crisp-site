"""One UTC day for site date writers and checks."""
import os
import re
from datetime import date, datetime, timezone


def utc_today() -> date:
    """Today's UTC date, or a validated SITE_TODAY override for tests."""
    override = os.environ.get("SITE_TODAY")
    if override is not None:
        if not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", override):
            raise ValueError("SITE_TODAY must be YYYY-MM-DD")
        return date.fromisoformat(override)
    return datetime.now(timezone.utc).date()


def utc_today_iso() -> str:
    """Today's UTC date in YYYY-MM-DD form."""
    return utc_today().isoformat()
