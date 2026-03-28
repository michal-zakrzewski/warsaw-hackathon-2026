from __future__ import annotations

from pathlib import Path
from typing import Any

import requests

from solar_client.exceptions import SolarApiError
from solar_client.models import BuildingInsights, DataLayers
from solar_client.usage_tracker import UsageTracker


class GoogleSolarClient:
    """Thin Python wrapper around the Google Maps Platform Solar API.

    Docs: https://developers.google.com/maps/documentation/solar/overview

    By default the client enforces free-tier monthly limits and raises
    ``FreeTierExceeded`` before making a call that would incur a charge.
    Pass ``allow_paid=True`` to disable this guard.
    """

    BASE_URL = "https://solar.googleapis.com/v1"

    def __init__(
        self,
        api_key: str,
        *,
        timeout: int = 30,
        allow_paid: bool = False,
    ) -> None:
        self.api_key = api_key
        self.timeout = timeout
        self.allow_paid = allow_paid
        self._session = requests.Session()
        self._usage = UsageTracker()

    # ---- low-level ----

    def _get(self, path: str, params: dict[str, Any]) -> dict[str, Any]:
        params = {**params, "key": self.api_key}
        resp = self._session.get(
            f"{self.BASE_URL}/{path}",
            params=params,
            timeout=self.timeout,
        )
        if not resp.ok:
            raise SolarApiError(resp.status_code, resp.text)
        return resp.json()

    def _track(self, endpoint: str) -> None:
        if not self.allow_paid:
            self._usage.check_and_increment(endpoint)

    # ---- building insights ----

    def find_closest_building(
        self,
        latitude: float,
        longitude: float,
        *,
        required_quality: str = "HIGH",
    ) -> BuildingInsights:
        """Return solar insights for the building closest to the given point.

        ``required_quality`` can be ``HIGH``, ``MEDIUM``, or ``LOW``.
        The API returns the highest quality available at or above the requested level.
        """
        self._track("building_insights")
        data = self._get(
            "buildingInsights:findClosest",
            {
                "location.latitude": latitude,
                "location.longitude": longitude,
                "requiredQuality": required_quality,
            },
        )
        return BuildingInsights.model_validate(data)

    # ---- data layers ----

    def get_data_layers(
        self,
        latitude: float,
        longitude: float,
        *,
        radius_meters: float = 50,
        required_quality: str = "HIGH",
        pixel_size_meters: float = 0.1,
        view: str = "FULL_LAYERS",
    ) -> DataLayers:
        """Return URLs to GeoTIFF rasters for the area around a point.

        The returned URLs are short-lived (a few hours). Use
        :meth:`download_geotiff` to persist them locally.
        """
        self._track("data_layers")
        data = self._get(
            "dataLayers:get",
            {
                "location.latitude": latitude,
                "location.longitude": longitude,
                "radiusMeters": radius_meters,
                "requiredQuality": required_quality,
                "pixelSizeMeters": pixel_size_meters,
                "view": view,
            },
        )
        return DataLayers.model_validate(data)

    # ---- geotiff download ----

    def download_geotiff(self, url: str, output_path: str | Path) -> Path:
        """Download a GeoTIFF from a URL returned by :meth:`get_data_layers`.

        The API key is appended automatically.
        GeoTIFF downloads are not counted against API quotas.
        """
        output_path = Path(output_path)
        resp = self._session.get(
            url,
            params={"key": self.api_key},
            timeout=self.timeout,
            stream=True,
        )
        if not resp.ok:
            raise SolarApiError(resp.status_code, resp.text)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "wb") as f:
            for chunk in resp.iter_content(chunk_size=8192):
                f.write(chunk)
        return output_path

    # ---- geocoding helper ----

    def geocode(self, address: str) -> tuple[float, float]:
        """Geocode an address to (latitude, longitude) via Google Geocoding API.

        Requires the Geocoding API enabled on the same API key.
        """
        resp = self._session.get(
            "https://maps.googleapis.com/maps/api/geocode/json",
            params={"address": address, "key": self.api_key},
            timeout=self.timeout,
        )
        if not resp.ok:
            raise SolarApiError(resp.status_code, resp.text)

        data = resp.json()
        if data["status"] != "OK" or not data.get("results"):
            raise SolarApiError(0, f"Geocoding failed: {data['status']}")

        loc = data["results"][0]["geometry"]["location"]
        return loc["lat"], loc["lng"]

    # ---- usage ----

    def usage_status(self) -> None:
        """Print current monthly usage vs. free-tier limits to stdout."""
        self._usage.print_status()
