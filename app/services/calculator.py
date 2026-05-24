from __future__ import annotations

from math import asin, cos, radians, sin, sqrt


class InvalidTripError(ValueError):
    pass


def haversine_km(origin: dict, destination: dict) -> float:
    radius_km = 6371.0
    lat1 = radians(float(origin["lat"]))
    lon1 = radians(float(origin["lon"]))
    lat2 = radians(float(destination["lat"]))
    lon2 = radians(float(destination["lon"]))

    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * asin(sqrt(a))
    return radius_km * c


def calculate_trip(segments: list[dict], transport_modes: dict, destination: dict) -> dict:
    if not segments:
        raise InvalidTripError("At least one trip segment is required.")

    final_arrival = segments[-1].get("arrival")
    if not _same_place(final_arrival, destination):
        raise InvalidTripError(f"The final segment must end in {destination['label']}.")

    calculated_segments = []
    total_distance = 0.0
    total_emissions = 0.0

    for segment in segments:
        departure = segment.get("departure")
        arrival = segment.get("arrival")
        mode_key = segment.get("transport_mode")

        if not departure or not arrival or not mode_key:
            raise InvalidTripError("Each segment requires departure, arrival, and transport mode.")
        if mode_key not in transport_modes:
            raise InvalidTripError(f"Unknown transport mode: {mode_key}.")

        mode = transport_modes[mode_key]
        distance_km = haversine_km(departure, arrival)
        emissions_kg = (distance_km * mode.grams_co2e_per_km) / 1000

        total_distance += distance_km
        total_emissions += emissions_kg
        calculated_segments.append(
            {
                "departure_label": departure["label"],
                "arrival_label": arrival["label"],
                "transport_mode": mode.label,
                "transport_mode_key": mode.key,
                "distance_km": round(distance_km, 1),
                "emissions_kg": round(emissions_kg, 2),
            }
        )

    return {
        "segments": calculated_segments,
        "total_distance_km": round(total_distance, 1),
        "total_emissions_kg": round(total_emissions, 2),
    }


def decode_study_code(study_code: str, transport_modes: dict, destination: dict) -> dict:
    segments = _segments_from_study_code(study_code, transport_modes, destination)
    result = calculate_trip(segments, transport_modes, destination)

    return {
        "itinerary": segments,
        "estimates": result,
    }


def _segments_from_study_code(study_code: str, transport_modes: dict, destination: dict) -> list[dict]:
    if not study_code or not study_code.strip():
        raise InvalidTripError("A non-empty study code is required.")

    ordered_mode_keys = list(transport_modes.keys())
    segments = []

    for raw_segment in study_code.split(";"):
        parts = [part.strip() for part in raw_segment.split(",")]
        if len(parts) != 5:
            raise InvalidTripError("Each encoded segment must contain 5 comma-separated values.")

        try:
            departure_lat = float(parts[0])
            departure_lon = float(parts[1])
            mode_index = int(parts[2])
            arrival_lat = float(parts[3])
            arrival_lon = float(parts[4])
        except ValueError as exc:
            raise InvalidTripError("Study code contains invalid coordinates or transport mode ids.") from exc

        if mode_index < 1 or mode_index > len(ordered_mode_keys):
            raise InvalidTripError(f"Unknown transport mode id: {mode_index}.")

        departure = _place_from_coordinates(departure_lat, departure_lon, destination)
        arrival = _place_from_coordinates(arrival_lat, arrival_lon, destination)
        segments.append(
            {
                "departure": departure,
                "arrival": arrival,
                "transport_mode": ordered_mode_keys[mode_index - 1],
            }
        )

    return segments


def _place_from_coordinates(lat: float, lon: float, destination: dict) -> dict:
    if abs(lat - float(destination["lat"])) < 0.0001 and abs(lon - float(destination["lon"])) < 0.0001:
        return destination

    label = f"{lat:.4f},{lon:.4f}"
    return {
        "label": label,
        "type": "coordinate",
        "country": "",
        "lat": lat,
        "lon": lon,
    }


def _same_place(left: dict | None, right: dict) -> bool:
    if not left:
        return False

    try:
        return (
            left["label"] == right["label"]
            and abs(float(left["lat"]) - float(right["lat"])) < 0.0001
            and abs(float(left["lon"]) - float(right["lon"])) < 0.0001
        )
    except (KeyError, TypeError, ValueError):
        return False
