from app.config import load_app_config


def test_load_app_config_reads_destination_and_modes():
    config = load_app_config("config/app.yml")

    assert config.conference.destination_label == "Bolzano, Italy"
    assert config.conference.app_title == "ECSA Travel Profile Tool"
    assert config.transport_modes["train"].grams_co2e_per_km == 35.49
