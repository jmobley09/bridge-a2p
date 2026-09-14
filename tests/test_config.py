from app.core.config import DEFAULT_DATABASE_URL, Settings


def test_database_url_takes_precedence() -> None:
    settings = Settings(
        database_url="postgresql+psycopg://user:pass@example.com:5432/app",
        db_host="ignored.example.com",
        db_name="ignored",
        db_user="ignored",
        db_password="ignored",
        _env_file=None,
    )

    assert settings.get_database_url() == "postgresql+psycopg://user:pass@example.com:5432/app"


def test_database_url_is_built_from_separate_fields_with_encoded_password() -> None:
    settings = Settings(
        db_host="bridge-a2p-server.postgres.database.azure.com",
        db_port=5432,
        db_name="bridge_a2p",
        db_user="postgres",
        db_password=r"quj!GPS5Nt\@Z7sp#8jC",
        db_sslmode="require",
        _env_file=None,
    )

    assert settings.get_database_url() == (
        "postgresql+psycopg://postgres:quj%21GPS5Nt%5C%40Z7sp%238jC"
        "@bridge-a2p-server.postgres.database.azure.com:5432/bridge_a2p?sslmode=require"
    )


def test_default_database_url_is_used_when_database_settings_are_missing() -> None:
    settings = Settings(_env_file=None)

    assert settings.get_database_url() == DEFAULT_DATABASE_URL
