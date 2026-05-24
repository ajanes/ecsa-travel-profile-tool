from __future__ import annotations

from flask import Blueprint, current_app, jsonify, render_template, request

from app.services.calculator import InvalidTripError, calculate_trip, decode_study_code

bp = Blueprint("main", __name__)


@bp.get("/")
def index():
    app_config = current_app.config["APP_CONFIG"]
    destination = app_config.conference.destination_place
    transport_modes = [mode.__dict__ for mode in app_config.transport_modes.values()]
    return render_template(
        "index.html",
        conference=app_config.conference,
        destination=destination,
        emissions_source=app_config.emissions_source,
        transport_modes=transport_modes,
    )


@bp.get("/api/places")
def places():
    query = request.args.get("q", "").strip()
    if len(query) < 2:
        return jsonify({"results": []})

    app_config = current_app.config["APP_CONFIG"]
    service = current_app.config["PLACE_SERVICE"]
    results = service.search(query, limit=app_config.place_api.limit)
    return jsonify({"results": results})


@bp.post("/api/calculate")
def calculate():
    payload = request.get_json(silent=True) or {}
    segments = payload.get("segments") or []
    app_config = current_app.config["APP_CONFIG"]

    try:
        result = calculate_trip(segments, app_config.transport_modes, app_config.conference.destination_place)
    except InvalidTripError as exc:
        return jsonify({"error": str(exc)}), 400

    return jsonify(result)


@bp.get("/api/itinerary")
def itinerary():
    study_code = request.args.get("code", "").strip()
    app_config = current_app.config["APP_CONFIG"]

    try:
        result = decode_study_code(study_code, app_config.transport_modes, app_config.conference.destination_place)
    except InvalidTripError as exc:
        return jsonify({"error": str(exc)}), 400

    return jsonify(result)
