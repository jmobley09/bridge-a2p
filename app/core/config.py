from functools import lru_cache
from urllib.parse import quote

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_DATABASE_URL = "postgresql+psycopg://bridge:bridge@localhost:5432/bridge_a2p"


class Settings(BaseSettings):
    database_url: str | None = Field(default=None)
    db_host: str | None = None
    db_port: int = 5432
    db_name: str | None = None
    db_user: str | None = None
    db_password: str | None = None
    db_sslmode: str | None = None
    app_env: str = "local"
    twilio_account_sid: str | None = None
    twilio_api_key_sid: str | None = None
    twilio_api_key_secret: str | None = None
    twilio_auth_token: str | None = None
    twilio_validate_signature: bool = True
    public_webhook_base_url: str | None = None

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    def get_database_url(self) -> str:
        if self.database_url:
            return self.database_url

        if not all([self.db_host, self.db_name, self.db_user, self.db_password]):
            return DEFAULT_DATABASE_URL

        encoded_user = quote(self.db_user or "", safe="")
        encoded_password = quote(self.db_password or "", safe="")
        url = (
            f"postgresql+psycopg://{encoded_user}:{encoded_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )
        if self.db_sslmode:
            url = f"{url}?sslmode={quote(self.db_sslmode, safe='')}"
        return url


@lru_cache
def get_settings() -> Settings:
    return Settings()
