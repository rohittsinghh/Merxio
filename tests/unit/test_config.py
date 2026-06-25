from app.core.config import Settings


def test_settings_defaults_are_development_friendly() -> None:
    """The app should boot locally even before Docker or secrets are configured."""
    settings = Settings(_env_file=None)

    assert settings.app_name == "Merxio"
    assert settings.is_production is False
    assert "localhost" in settings.database_url
