from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class PlaceApiConfig:
    base_url: str
    search_path: str
    reverse_path: str
    user_agent: str
    limit: int
    bearer_token: str | None
    bypass_proxy: bool


@dataclass(frozen=True)
class ConferenceConfig:
    app_title: str
    destination_label: str
    destination_country: str
    destination_lat: float
    destination_lon: float

    @property
    def destination_place(self) -> dict[str, Any]:
        return {
            "id": "conference-destination",
            "label": self.destination_label,
            "type": "city",
            "lat": self.destination_lat,
            "lon": self.destination_lon,
            "country": self.destination_country,
        }

@dataclass(frozen=True)
class TransportMode:
    key: str
    label: str
    grams_co2e_per_km: float


@dataclass(frozen=True)
class TransportModeOption:
    key: str
    label: str
    transport_mode: str | None = None
    resolver: str | None = None


@dataclass(frozen=True)
class AppConfig:
    conference: ConferenceConfig
    place_api: PlaceApiConfig
    transport_modes: dict[str, TransportMode]
    transport_mode_options: dict[str, TransportModeOption]


def load_app_config(config_path: str) -> AppConfig:
    requested_path = Path(config_path)
    if not requested_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {requested_path}")

    raw = yaml.safe_load(requested_path.read_text(encoding="utf-8"))

    conference = raw["conference"]
    destination = conference["destination"]
    place_api = raw["place_api"]

    transport_modes = {
        key: TransportMode(
            key=key,
            label=value["label"],
            grams_co2e_per_km=float(value["grams_co2e_per_km"]),
        )
        for key, value in raw["transport_modes"].items()
    }
    transport_mode_options = {
        key: TransportModeOption(
            key=key,
            label=value["label"],
            transport_mode=value.get("transport_mode"),
            resolver=value.get("resolver"),
        )
        for key, value in raw["transport_mode_options"].items()
    }

    return AppConfig(
        conference=ConferenceConfig(
            app_title=conference["app_title"],
            destination_label=destination["label"],
            destination_country=destination["country"],
            destination_lat=float(destination["lat"]),
            destination_lon=float(destination["lon"]),
        ),
        place_api=PlaceApiConfig(
            base_url=place_api["base_url"],
            search_path=place_api.get("search_path", "/api"),
            reverse_path=place_api.get("reverse_path", "/reverse"),
            user_agent=place_api["user_agent"],
            limit=int(place_api["limit"]),
            bearer_token=place_api.get("bearer_token"),
            bypass_proxy=bool(place_api.get("bypass_proxy", False)),
        ),
        transport_modes=transport_modes,
        transport_mode_options=transport_mode_options,
    )
