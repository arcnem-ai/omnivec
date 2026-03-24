"""Runtime settings and derived filesystem paths for Omnivec."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration for Omnivec."""

    model_config = SettingsConfigDict(
        env_prefix="OMNIVEC_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Omnivec Asset Librarian"
    data_dir: Path = Path(".omnivec-data")
    api_key: str | None = None
    llm_model: str = Field(
        default="openai/gpt-4o-mini",
        validation_alias="MODEL",
    )
    texvec_bin: str = "texvec"
    picvec_bin: str = "picvec"
    max_concurrent_jobs: int = Field(default=1, ge=1)
    max_neighbors: int = Field(default=3, ge=1, le=20)
    job_ttl_hours: int = Field(default=72, ge=1)
    openai_api_key: str | None = Field(default=None, validation_alias="OPENAI_API_KEY")

    @property
    def base_data_dir(self) -> Path:
        return self.data_dir.expanduser().resolve()

    @property
    def jobs_dir(self) -> Path:
        return self.base_data_dir / "jobs"

    @property
    def cache_dir(self) -> Path:
        return self.base_data_dir / "cache"

    def prepare_directories(self) -> None:
        self.jobs_dir.mkdir(parents=True, exist_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    settings = Settings()
    settings.prepare_directories()
    return settings
