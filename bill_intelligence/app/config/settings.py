"""Runtime configuration loaded from environment variables."""

from __future__ import annotations

import os


class Settings:
    """All configuration is read from environment at construction time."""

    def __init__(self) -> None:
        self.google_cloud_project: str = os.environ.get("GOOGLE_CLOUD_PROJECT", "")
        self.documentai_location: str = os.environ.get("DOCUMENTAI_LOCATION", "eu")
        # Accept either DOCUMENTAI_FORM_PROCESSOR_ID (Form Parser, what we have)
        # or DOCUMENTAI_UTILITY_PROCESSOR_ID (Utility Parser, specialized).
        # Form Parser is used as primary when utility is absent.
        self.documentai_primary_processor_id: str = (
            os.environ.get("DOCUMENTAI_UTILITY_PROCESSOR_ID")
            or os.environ.get("DOCUMENTAI_FORM_PROCESSOR_ID")
            or ""
        )
        self.documentai_primary_processor_type: str = (
            "utility"
            if os.environ.get("DOCUMENTAI_UTILITY_PROCESSOR_ID")
            else "form"
        )
        self.documentai_fallback_processor_id: str | None = (
            os.environ.get("DOCUMENTAI_FALLBACK_FORM_PROCESSOR_ID")
            or os.environ.get("DOCUMENTAI_FALLBACK_UTILITY_PROCESSOR_ID")
        ) or None
        self.use_fake_documentai: bool = (
            os.environ.get("USE_FAKE_DOCUMENTAI", "false").lower() == "true"
        )
        self.include_raw_document: bool = (
            os.environ.get("INCLUDE_RAW_DOCUMENT", "false").lower() == "true"
        )

    def validate_for_real_client(self) -> list[str]:
        """Return list of missing required env vars for the real Document AI client."""
        missing: list[str] = []
        if not self.google_cloud_project:
            missing.append("GOOGLE_CLOUD_PROJECT")
        if not self.documentai_primary_processor_id:
            missing.append("DOCUMENTAI_FORM_PROCESSOR_ID (or DOCUMENTAI_UTILITY_PROCESSOR_ID)")
        return missing


_settings: Settings | None = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
