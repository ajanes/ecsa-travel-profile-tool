from __future__ import annotations

from typing import Any

import requests

from app.config import PlaceApiConfig


class PhotonPlaceService:
    def __init__(self, config: PlaceApiConfig):
        self._config = config
        self._session = requests.Session()
        self._session.headers.update({"User-Agent": config.user_agent})

    def search(self, query: str, limit: int | None = None) -> list[dict[str, Any]]:
        response = self._session.get(
            f"{self._config.base_url.rstrip('/')}/api",
            params={
                "q": query,
                "limit": limit or self._config.limit,
            },
            timeout=10,
        )
        response.raise_for_status()
        payload = response.json()
        return [self._normalize_place(item) for item in payload.get("features", [])]

    def _normalize_place(self, item: dict[str, Any]) -> dict[str, Any]:
        properties = item.get("properties", {})
        coordinates = item.get("geometry", {}).get("coordinates", [])
        country = properties.get("country", "")
        place_type = self._classify(properties)
        label = self._build_label(properties, country)

        return {
            "id": str(properties.get("osm_id", item.get("id", label))),
            "label": label,
            "type": place_type,
            "lat": float(coordinates[1]),
            "lon": float(coordinates[0]),
            "country": country,
        }

    def _build_label(self, properties: dict[str, Any], country: str) -> str:
        name = properties.get("name") or properties.get("city") or properties.get("county") or properties.get("state")
        if name and country:
            return f"{name}, {country}"
        if name:
            return name

        return country or "Unknown place"

    def _classify(self, properties: dict[str, Any]) -> str:
        kind = properties.get("osm_value", "")
        category = properties.get("osm_key", "")

        if "airport" in kind or "aerodrome" in kind:
            return "airport"
        if "station" in kind or "railway" in category or "public_transport" in category:
            return "station"
        if kind in {"city", "town", "village", "municipality", "hamlet"}:
            return "city"
        return "place"
