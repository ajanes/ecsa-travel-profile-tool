from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class PlaceApiConfig:
    base_url: str
    user_agent: str
    limit: int


@dataclass(frozen=True)
class ConferenceConfig:
    name: str
    dates: str
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
class EmissionsSourceConfig:
    label: str
    url: str
    year: int


@dataclass(frozen=True)
class TransportMode:
    key: str
    label: str
    icon: str
    grams_co2e_per_km: float
    source_entity: str


@dataclass(frozen=True)
class AppConfig:
    conference: ConferenceConfig
    emissions_source: EmissionsSourceConfig
    place_api: PlaceApiConfig
    transport_modes: dict[str, TransportMode]


def load_app_config(config_path: str) -> AppConfig:
    raw = yaml.safe_load(Path(config_path).read_text(encoding="utf-8"))

    conference = raw["conference"]
    destination = conference["destination"]
    emissions = raw["emissions"]
    place_api = raw["place_api"]

    transport_modes = {
        key: TransportMode(
            key=key,
            label=value["label"],
            icon=value["icon"],
            grams_co2e_per_km=float(value["grams_co2e_per_km"]),
            source_entity=value["source_entity"],
        )
        for key, value in raw["transport_modes"].items()
    }

    return AppConfig(
        conference=ConferenceConfig(
            name=conference["name"],
            dates=conference["dates"],
            destination_label=destination["label"],
            destination_country=destination["country"],
            destination_lat=float(destination["lat"]),
            destination_lon=float(destination["lon"]),
        ),
        emissions_source=EmissionsSourceConfig(
            label=emissions["source"]["label"],
            url=emissions["source"]["url"],
            year=int(emissions["source"]["year"]),
        ),
        place_api=PlaceApiConfig(
            base_url=place_api["base_url"],
            user_agent=place_api["user_agent"],
            limit=int(place_api["limit"]),
        ),
        transport_modes=transport_modes,
    )
