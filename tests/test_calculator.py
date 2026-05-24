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

    result = calculate_trip(segments, config.transport_modes, destination)

    assert result["total_distance_km"] == 423.1
    assert result["segments"][0]["transport_mode"] == "Train"
    assert result["total_emissions_kg"] == 15.02


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
