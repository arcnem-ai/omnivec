from __future__ import annotations

from pathlib import Path

from omnivec.settings import Settings


def test_settings_accepts_model_env(monkeypatch) -> None:
    monkeypatch.setenv("MODEL", "openai/gpt-4.1")
    monkeypatch.delenv("OMNIVEC_LLM_MODEL", raising=False)

    settings = Settings(_env_file=None)

    assert settings.llm_model == "openai/gpt-4.1"


def test_settings_ignores_legacy_omnivec_llm_model_env(monkeypatch) -> None:
    monkeypatch.setenv("OMNIVEC_LLM_MODEL", "openai/gpt-4.1-mini")
    monkeypatch.delenv("MODEL", raising=False)

    settings = Settings(_env_file=None)

    assert settings.llm_model == "openai/gpt-4o-mini"


def test_settings_resolve_relative_data_dir_to_absolute_path(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)

    settings = Settings(data_dir=Path(".omnivec-data"), _env_file=None)

    assert settings.base_data_dir == (tmp_path / ".omnivec-data").resolve()
    assert settings.jobs_dir == (tmp_path / ".omnivec-data" / "jobs").resolve()
