from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    database_uri: str
    database_engine: str
    database_user: str
    database_password: str
    database_host: str
    database_port: str
    database_name: str

    explorer_url: str
    node_url: str
    project_name: str
    model_config = SettingsConfigDict(env_file=f"{BASE_DIR}/.env")


settings = Settings()
