# ECSA Travel Profile Tool

Small Flask application for collecting conference travel profiles and estimating travel emissions for multi-leg trips ending at a configured destination.

## Features

- Single-page travel profile form with repeatable trip legs
- Live place lookup for cities, airports, and stations
- Locked final destination from YAML config
- Emissions estimates based on configurable per-kilometer factors
- Compact study-data export string plus hidden decode API
- Docker and `docker compose` support

## Run locally

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python run.py
```

Open `http://localhost:5000`.

## Run with Docker

```bash
docker compose up --build
```

## Configuration

Edit `config/app.yml` to change:

- conference name, dates, and fixed destination
- transport modes and emissions factors
- place lookup API settings

## HTTP API

### `GET /api/places?q=term`

Returns normalized place suggestions:

```json
{
  "results": [
    {
      "id": "123",
      "label": "Vienna, Austria",
      "type": "city",
      "lat": 48.2082,
      "lon": 16.3738,
      "country": "Austria"
    }
  ]
}
```

### `POST /api/calculate`

Request:

```json
{
  "segments": [
    {
      "departure": {
        "label": "Vienna, Austria",
        "lat": 48.2082,
        "lon": 16.3738
      },
      "arrival": {
        "label": "Bolzano, Italy",
        "lat": 46.4983,
        "lon": 11.3548
      },
      "transport_mode": "train"
    }
  ]
}
```

Response:

```json
{
  "segments": [
    {
      "departure_label": "Vienna, Austria",
      "arrival_label": "Bolzano, Italy",
      "transport_mode": "Train",
      "transport_mode_key": "train",
      "distance_km": 423.1,
      "emissions_kg": 15.02
    }
  ],
  "total_distance_km": 423.1,
  "total_emissions_kg": 15.02
}
```

### `GET /api/itinerary?code=...`

Decodes the compact study-data string and returns a reconstructed itinerary plus estimated totals.

Example:

```text
/api/itinerary?code=48.2082,16.3738,1,46.4983,11.3548
```

Response:

```json
{
  "itinerary": [
    {
      "departure": {
        "label": "48.2082,16.3738",
        "type": "coordinate",
        "country": "",
        "lat": 48.2082,
        "lon": 16.3738
      },
      "arrival": {
        "id": "conference-destination",
        "label": "Bolzano, Italy",
        "type": "city",
        "lat": 46.4983,
        "lon": 11.3548,
        "country": "Italy"
      },
      "transport_mode": "train"
    }
  ],
  "estimates": {
    "segments": [
      {
        "departure_label": "48.2082,16.3738",
        "arrival_label": "Bolzano, Italy",
        "transport_mode": "Train",
        "transport_mode_key": "train",
        "distance_km": 423.1,
        "emissions_kg": 15.02
      }
    ],
    "total_distance_km": 423.1,
    "total_emissions_kg": 15.02
  }
}
```

## Study Data Format

The UI generates a compact study string like:

```text
48.2082,16.3738,1,46.4983,11.3548;47.3769,8.5417,2,46.4983,11.3548
```

Each segment is:

```text
from_lat,from_lon,mode_id,to_lat,to_lon
```

Segments are joined with `;`.

`mode_id` is the 1-based position of the transport mode in `config/app.yml`.

## Notes

- The application does not ship with its own city database.
  When a user types a prefix such as `Mu`, the frontend calls `GET /api/places`,
  and the backend queries the live place lookup service configured in `config/app.yml`.
  With the default setup, suggestions such as `Munich` come from the Photon geocoder.
- Place coordinates come from the live place lookup service configured in `config/app.yml`.
  The default setup uses Photon and stores the returned latitude and longitude
  for the selected city, airport, or station.
- Distance uses a haversine estimate between coordinates.
- The final trip segment must end at the configured conference destination.
- Emissions weights are seeded from Our World in Data:
  https://ourworldindata.org/grapher/carbon-footprint-travel-mode
