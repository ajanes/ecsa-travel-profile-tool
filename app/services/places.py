from __future__ import annotations

from typing import Any

import requests

from app.config import PlaceApiConfig


class PhotonPlaceService:
    def __init__(self, config: PlaceApiConfig):
        self._config = config
        self._session = requests.Session()
        self._session.trust_env = not config.bypass_proxy
        headers = {"User-Agent": config.user_agent}
        if config.bearer_token:
            headers["Authorization"] = f"Bearer {config.bearer_token}"
        self._session.headers.update(headers)

    def search(self, query: str, limit: int | None = None) -> list[dict[str, Any]]:
        response = self._session.get(
            self._build_url(self._config.search_path),
            params={
                "q": query,
                "limit": limit or self._config.limit,
            },
            timeout=10,
        )
        response.raise_for_status()
        payload = response.json()
        return [self._normalize_place(item) for item in payload.get("features", [])]

    def reverse(self, lat: float, lon: float) -> dict[str, Any] | None:
        response = self._session.get(
            self._build_url(self._config.reverse_path),
            params={
                "lat": lat,
                "lon": lon,
                "limit": 1,
            },
            timeout=10,
        )
        response.raise_for_status()
        payload = response.json()
        features = payload.get("features", [])
        if not features:
            return None

        return self._normalize_place(features[0])

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

    def _build_url(self, path: str) -> str:
        return f"{self._config.base_url.rstrip('/')}/{path.lstrip('/')}"
