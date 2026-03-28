from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

# Free monthly limits per Google Maps Platform pricing
FREE_LIMITS = {
    "building_insights": 10_000,
    "data_layers": 1_000,
}

_DEFAULT_PATH = Path(__file__).parent.parent / ".usage.json"


class FreeTierExceeded(Exception):
    """Raised before making a call that would exceed the free monthly limit."""


class UsageTracker:
    """Persists monthly API call counts to a local JSON file.

    Resets automatically at the start of each calendar month.
    Raises :class:`FreeTierExceeded` before any call that would exceed the
    free-tier limit so you never receive an unexpected bill.
    """

    def __init__(self, path: Path = _DEFAULT_PATH) -> None:
        self._path = path
        self._data = self._load()

    # ---- public ----

    def check_and_increment(self, endpoint: str) -> None:
        """Check the limit, then record one call. Raises FreeTierExceeded if over."""
        self._maybe_reset()
        current = self._data["counts"].get(endpoint, 0)
        limit = FREE_LIMITS.get(endpoint)

        if limit is not None and current >= limit:
            raise FreeTierExceeded(
                f"Free tier limit reached for '{endpoint}': "
                f"{current}/{limit} calls this month. "
                "Pass allow_paid=True to the client to proceed anyway."
            )

        self._data["counts"][endpoint] = current + 1
        self._save()

    def status(self) -> dict[str, dict]:
        """Return current usage vs. free limits for all tracked endpoints."""
        self._maybe_reset()
        result = {}
        for endpoint, limit in FREE_LIMITS.items():
            used = self._data["counts"].get(endpoint, 0)
            result[endpoint] = {
                "used": used,
                "free_limit": limit,
                "remaining": max(0, limit - used),
                "month": self._data["month"],
            }
        return result

    def print_status(self) -> None:
        for endpoint, info in self.status().items():
            print(
                f"{endpoint}: {info['used']}/{info['free_limit']} used "
                f"({info['remaining']} remaining) — {info['month']}"
            )

    # ---- internal ----

    def _current_month(self) -> str:
        return datetime.now().strftime("%Y-%m")

    def _maybe_reset(self) -> None:
        if self._data.get("month") != self._current_month():
            self._data = {"month": self._current_month(), "counts": {}}
            self._save()

    def _load(self) -> dict:
        if self._path.exists():
            try:
                return json.loads(self._path.read_text())
            except (json.JSONDecodeError, KeyError):
                pass
        return {"month": self._current_month(), "counts": {}}

    def _save(self) -> None:
        self._path.write_text(json.dumps(self._data, indent=2))
