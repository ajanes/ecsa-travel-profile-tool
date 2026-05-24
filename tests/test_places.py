from app.services.places import PhotonPlaceService


class DummyResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


def test_place_service_normalizes_results(monkeypatch, app):
    config = app.config["APP_CONFIG"].place_api
    service = PhotonPlaceService(config)

    def fake_get(url, params, timeout):
        assert params["q"] == "Bolzano"
        return DummyResponse(
            {
                "features": [
                    {
                        "type": "Feature",
                        "properties": {
                            "osm_id": 123,
                            "name": "Bolzano",
                            "country": "Italy",
                            "osm_key": "place",
                            "osm_value": "city",
                        },
                        "geometry": {"type": "Point", "coordinates": [11.3548, 46.4983]},
                    }
                ]
            }
        )

    monkeypatch.setattr(service._session, "get", fake_get)
    results = service.search("Bolzano", limit=5)

    assert results == [
        {
            "id": "123",
            "label": "Bolzano, Italy",
            "type": "city",
            "lat": 46.4983,
            "lon": 11.3548,
            "country": "Italy",
        }
    ]
