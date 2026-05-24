from app.services.places import PhotonPlaceService


class StubPlaceService(PhotonPlaceService):
    def __init__(self):
        pass

    def search(self, query, limit=None):
        return [
            {
                "id": "1",
                "label": "Vienna, Austria",
                "type": "city",
                "lat": 48.2082,
                "lon": 16.3738,
                "country": "Austria",
            }
        ]


def test_index_renders(client):
    response = client.get("/")

    assert response.status_code == 200
    assert b"ECSA Travel Profile Tool" in response.data


def test_places_route_returns_normalized_results(app, client):
    app.config["PLACE_SERVICE"] = StubPlaceService()

    response = client.get("/api/places?q=Vienna")

    assert response.status_code == 200
    assert response.get_json()["results"][0]["label"] == "Vienna, Austria"


def test_calculate_route_rejects_invalid_segments(client):
    response = client.post("/api/calculate", json={"segments": []})

    assert response.status_code == 400
    assert "At least one trip segment" in response.get_json()["error"]


def test_calculate_route_returns_totals(app, client):
    destination = app.config["APP_CONFIG"].conference.destination_place
    response = client.post(
        "/api/calculate",
        json={
            "segments": [
                {
                    "departure": {
                        "label": "Vienna, Austria",
                        "lat": 48.2082,
                        "lon": 16.3738,
                    },
                    "arrival": destination,
                    "transport_mode": "train",
                }
            ]
        },
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["total_distance_km"] == 423.1
    assert payload["total_emissions_kg"] == 15.02


def test_itinerary_route_decodes_study_code(client):
    response = client.get("/api/itinerary?code=48.2082,16.3738,1,46.4983,11.3548")

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["itinerary"][0]["transport_mode"] == "train"
    assert payload["itinerary"][0]["arrival"]["label"] == "Bolzano, Italy"
    assert payload["estimates"]["total_distance_km"] == 423.1
    assert payload["estimates"]["total_emissions_kg"] == 15.02


def test_itinerary_route_rejects_invalid_study_code(client):
    response = client.get("/api/itinerary?code=bad-code")

    assert response.status_code == 400
    assert "5 comma-separated values" in response.get_json()["error"]
