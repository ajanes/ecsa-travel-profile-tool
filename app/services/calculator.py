from __future__ import annotations

from math import asin, cos, radians, sin, sqrt

INTERNATIONAL_FLIGHT_SHORT_HAUL_MAX_KM = 3700.0


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


def calculate_trip(
    segments: list[dict],
    transport_modes: dict,
    destination: dict,
    transport_mode_options: dict | None = None,
) -> dict:
    if not segments:
        raise InvalidTripError("At least one trip segment is required.")

    final_arrival = segments[-1].get("arrival")
    if not _same_place(final_arrival, destination):
        raise InvalidTripError(f"The final segment must end in {destination['label']}.")

    calculated_segments = []
    encoded_segments = []
    total_distance = 0.0
    total_emissions = 0.0

    for segment in segments:
        departure = segment.get("departure")
        arrival = segment.get("arrival")
        mode_key = segment.get("transport_mode")

        if not departure or not arrival or not mode_key:
            raise InvalidTripError("Each segment requires departure, arrival, and transport mode.")
        distance_km = haversine_km(departure, arrival)
        resolved_mode_key = _resolve_transport_mode_key(
            mode_key,
            distance_km,
            transport_modes,
            transport_mode_options=transport_mode_options,
        )
        mode = transport_modes[resolved_mode_key]
        emissions_kg = (distance_km * mode.grams_co2e_per_km) / 1000

        total_distance += distance_km
        total_emissions += emissions_kg
        calculated_segments.append(
            {
                "departure_label": departure["label"],
                "arrival_label": arrival["label"],
                "transport_mode": mode.label,
                "transport_mode_key": resolved_mode_key,
                "distance_km": round(distance_km, 1),
                "emissions_kg": round(emissions_kg, 2),
            }
        )
        encoded_segments.append(
            {
                "departure": departure,
                "arrival": arrival,
                "transport_mode": resolved_mode_key,
            }
        )

    return {
        "segments": calculated_segments,
        "total_distance_km": round(total_distance, 1),
        "total_emissions_kg": round(total_emissions, 2),
        "study_code": _encode_study_code(encoded_segments, transport_modes),
    }


def decode_study_code(
    study_code: str,
    transport_modes: dict,
    destination: dict,
    reverse_lookup=None,
) -> dict:
    segments = _segments_from_study_code(study_code, transport_modes, destination, reverse_lookup=reverse_lookup)
    result = calculate_trip(segments, transport_modes, destination)

    return {
        "segments": [
            {
                "from_label": segment["departure"]["label"],
                "from": [segment["departure"]["lat"], segment["departure"]["lon"]],
                "to_label": segment["arrival"]["label"],
                "to": [segment["arrival"]["lat"], segment["arrival"]["lon"]],
                "transport_mode": result["segments"][index]["transport_mode"],
                "transport_mode_key": segment["transport_mode"],
                "distance_km": result["segments"][index]["distance_km"],
                "emissions_kg": result["segments"][index]["emissions_kg"],
            }
            for index, segment in enumerate(segments)
        ],
        "total_distance_km": result["total_distance_km"],
        "total_emissions_kg": result["total_emissions_kg"],
    }


def _segments_from_study_code(study_code: str, transport_modes: dict, destination: dict, reverse_lookup=None) -> list[dict]:
    if not study_code or not study_code.strip():
        raise InvalidTripError("A non-empty study code is required.")

    ordered_mode_keys = list(transport_modes.keys())
    encoded_parts = [part.strip() for part in study_code.split(";") if part.strip()]
    if len(encoded_parts) < 2:
        raise InvalidTripError("Study code must contain a start coordinate pair followed by at least one leg.")

    start_parts = [part.strip() for part in encoded_parts[0].split(",")]
    if len(start_parts) != 2:
        raise InvalidTripError("The study code header must contain exactly 2 comma-separated start coordinates.")

    try:
        current_departure_lat = float(start_parts[0])
        current_departure_lon = float(start_parts[1])
    except ValueError as exc:
        raise InvalidTripError("Study code contains invalid start coordinates.") from exc

    segments = []

    for raw_segment in encoded_parts[1:]:
        parts = [part.strip() for part in raw_segment.split(",")]
        if len(parts) != 3:
            raise InvalidTripError("Each encoded leg must contain 3 comma-separated values.")

        try:
            mode_index = int(parts[0])
            arrival_lat = float(parts[1])
            arrival_lon = float(parts[2])
        except ValueError as exc:
            raise InvalidTripError("Study code contains invalid coordinates or transport mode ids.") from exc

        if mode_index < 1 or mode_index > len(ordered_mode_keys):
            raise InvalidTripError(f"Unknown transport mode id: {mode_index}.")

        departure = _place_from_coordinates(
            current_departure_lat,
            current_departure_lon,
            destination,
            reverse_lookup=reverse_lookup,
        )
        arrival = _place_from_coordinates(arrival_lat, arrival_lon, destination, reverse_lookup=reverse_lookup)
        segments.append(
            {
                "departure": departure,
                "arrival": arrival,
                "transport_mode": ordered_mode_keys[mode_index - 1],
            }
        )
        current_departure_lat = arrival_lat
        current_departure_lon = arrival_lon

    return segments


def _place_from_coordinates(lat: float, lon: float, destination: dict, reverse_lookup=None) -> dict:
    if abs(lat - float(destination["lat"])) < 0.0001 and abs(lon - float(destination["lon"])) < 0.0001:
        return destination

    if reverse_lookup is not None:
        try:
            place = reverse_lookup(lat, lon)
        except Exception:
            place = None
        if place:
            return place

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


def _resolve_transport_mode_key(
    mode_key: str,
    distance_km: float,
    transport_modes: dict,
    transport_mode_options: dict | None = None,
) -> str:
    if mode_key in transport_modes:
        return mode_key

    if transport_mode_options is None or mode_key not in transport_mode_options:
        raise InvalidTripError(f"Unknown transport mode: {mode_key}.")

    option = transport_mode_options[mode_key]
    if option.transport_mode:
        return option.transport_mode
    if option.resolver == "flight_international":
        if distance_km <= INTERNATIONAL_FLIGHT_SHORT_HAUL_MAX_KM:
            return "flight_short_haul"
        return "flight_long_haul"

    raise InvalidTripError(f"Unsupported transport mode resolver: {option.resolver}.")


def _encode_study_code(segments: list[dict], transport_modes: dict) -> str:
    if not segments:
        return ""

    transport_mode_codes = {key: index + 1 for index, key in enumerate(transport_modes.keys())}
    first_segment = segments[0]
    parts = [
        ",".join(
            [
                _round_coordinate(first_segment["departure"]["lat"]),
                _round_coordinate(first_segment["departure"]["lon"]),
            ]
        )
    ]

    for segment in segments:
        parts.append(
            ",".join(
                [
                    str(transport_mode_codes[segment["transport_mode"]]),
                    _round_coordinate(segment["arrival"]["lat"]),
                    _round_coordinate(segment["arrival"]["lon"]),
                ]
            )
        )

    return ";".join(parts)


def _round_coordinate(value: float) -> str:
    return str(round(float(value), 4))
