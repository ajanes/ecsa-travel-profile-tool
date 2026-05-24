from app.config import load_app_config


def test_load_app_config_reads_destination_and_modes():
    config = load_app_config("config/app.yml")

    assert config.conference.destination_label == "Bolzano, Italy"
    assert config.transport_modes["train"].source_entity == "National rail"
    assert config.emissions_source.year == 2022
