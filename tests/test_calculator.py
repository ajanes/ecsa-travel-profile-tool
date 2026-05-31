from app.services.calculator import InvalidTripError, calculate_trip, haversine_km


def test_haversine_km_returns_reasonable_distance():
    vienna = {"lat": 48.2082, "lon": 16.3738}
    bolzano = {"lat": 46.4983, "lon": 11.3548}

    distance = haversine_km(vienna, bolzano)

    assert round(distance, 0) == 423


def test_calculate_trip_returns_totals(app):
    config = app.config["APP_CONFIG"]
    destination = config.conference.destination_place
    segments = [
        {
            "departure": {"label": "Vienna, Austria", "lat": 48.2082, "lon": 16.3738},
            "arrival": destination,
            "transport_mode": "train",
        }
    ]

    result = calculate_trip(
        segments,
        config.transport_modes,
        destination,
        transport_mode_options=config.transport_mode_options,
    )

    assert result["total_distance_km"] == 423.1
    assert result["segments"][0]["transport_mode"] == "Train"
    assert result["segments"][0]["transport_mode_key"] == "train"
    assert result["total_emissions_kg"] == 15.02
    assert result["study_code"] == "48.2082,16.3738;1,46.4983,11.3548"


def test_calculate_trip_resolves_international_flight_to_short_haul(app):
    config = app.config["APP_CONFIG"]
    destination = {"label": "London, United Kingdom", "lat": 51.5072, "lon": -0.1276}
    segments = [
        {
            "departure": {"label": "Vienna, Austria", "lat": 48.2082, "lon": 16.3738},
            "arrival": destination,
            "transport_mode": "flight_international",
        }
    ]

    result = calculate_trip(
        segments,
        config.transport_modes,
        destination,
        transport_mode_options=config.transport_mode_options,
    )

    assert result["segments"][0]["transport_mode"] == "Flight: Short-haul (up to 3700km distance)"
    assert result["segments"][0]["transport_mode_key"] == "flight_short_haul"
    assert result["study_code"] == "48.2082,16.3738;9,51.5072,-0.1276"


def test_calculate_trip_resolves_international_flight_to_long_haul(app):
    config = app.config["APP_CONFIG"]
    destination = {"label": "New York, United States", "lat": 40.7128, "lon": -74.006}
    segments = [
        {
            "departure": {"label": "Vienna, Austria", "lat": 48.2082, "lon": 16.3738},
            "arrival": destination,
            "transport_mode": "flight_international",
        }
    ]

    result = calculate_trip(
        segments,
        config.transport_modes,
        destination,
        transport_mode_options=config.transport_mode_options,
    )

    assert result["segments"][0]["transport_mode"] == "Flight: Long-haul (over 3700km distance)"
    assert result["segments"][0]["transport_mode_key"] == "flight_long_haul"
    assert result["study_code"] == "48.2082,16.3738;10,40.7128,-74.006"


def test_calculate_trip_rejects_non_destination_final_arrival(app):
    config = app.config["APP_CONFIG"]
    destination = config.conference.destination_place
    segments = [
        {
            "departure": {"label": "Vienna, Austria", "lat": 48.2082, "lon": 16.3738},
            "arrival": {"label": "Munich, Germany", "lat": 48.1371, "lon": 11.5754},
            "transport_mode": "train",
        }
    ]

    try:
        calculate_trip(segments, config.transport_modes, destination)
    except InvalidTripError as exc:
        assert "Bolzano, Italy" in str(exc)
    else:
        raise AssertionError("Expected InvalidTripError")
