from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    postgres_uri: str
    postgres_engine: str
    postgres_user: str
    postgres_password: str
    postgres_host: str
    postgres_port: str
    postgres_name: str

    explorer_address_url: str
    explorer_transaction_url: str
    chain_id: int
    node_url: str
    project_name: str
    model_config = SettingsConfigDict(env_file=f"{BASE_DIR}/.env")


settings = Settings()
