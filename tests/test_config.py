from app.config import load_app_config


def test_load_app_config_reads_destination_and_modes():
    config = load_app_config("config/travel-profile-tool.yml")

    assert config.conference.destination_label == "Bolzano, Italy"
    assert config.conference.app_title == "ECSA Travel Profile Tool"
    assert config.transport_modes["train"].grams_co2e_per_km == 35.49
    assert config.place_api.bearer_token
    assert config.place_api.base_url == "http://10.12.202.52:8080"
    assert config.place_api.search_path == "/travel-profile-tool/api"
    assert config.place_api.reverse_path == "/travel-profile-tool/reverse"
    assert config.place_api.bypass_proxy is True


def test_load_app_config_raises_clear_error_when_missing():
    missing_path = "config/does-not-exist.yml"

    try:
        load_app_config(missing_path)
    except FileNotFoundError as exc:
        assert str(exc) == f"Configuration file not found: {missing_path}"
    else:
        raise AssertionError("Expected FileNotFoundError for missing config file")
