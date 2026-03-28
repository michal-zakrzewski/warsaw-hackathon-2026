from __future__ import annotations


class SolarApiError(Exception):
    """Raised when the Google Solar API returns a non-2xx response."""

    def __init__(self, status_code: int, message: str) -> None:
        self.status_code = status_code
        self.message = message
        super().__init__(f"Solar API {status_code}: {message}")
