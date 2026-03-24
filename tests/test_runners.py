from __future__ import annotations

import sqlite3
from pathlib import Path

from omnivec.runners import PicvecRunner, TexvecRunner, parse_list_output, parse_search_output
from omnivec.settings import Settings


def test_texvec_build_env_uses_texvec_home(tmp_path: Path) -> None:
    settings = Settings(data_dir=tmp_path / "data")
    runner = TexvecRunner(settings)

    env = runner.build_env(tmp_path / "job-home")

    assert env["TEXVEC_HOME"] == str(tmp_path / "job-home")


def test_picvec_build_env_overrides_home(tmp_path: Path) -> None:
    settings = Settings(data_dir=tmp_path / "data")
    runner = PicvecRunner(settings)

    env = runner.build_env(tmp_path / "fake-home")

    assert env["HOME"] == str(tmp_path / "fake-home")


def test_runner_env_paths_are_absolute_for_relative_inputs(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    settings = Settings(data_dir=Path(".relative-data"))

    texvec_env = TexvecRunner(settings).build_env(Path(".relative-data/jobs/job1/texvec-home"))
    picvec_env = PicvecRunner(settings).build_env(Path(".relative-data/jobs/job1/picvec-user"))

    assert Path(texvec_env["TEXVEC_HOME"]).is_absolute()
    assert Path(picvec_env["HOME"]).is_absolute()


def test_parse_search_output_reads_distance_and_path() -> None:
    hits = parse_search_output("0.1000  docs/a.md\n0.2500  docs/b.md\n")

    assert [hit.path for hit in hits] == ["docs/a.md", "docs/b.md"]
    assert hits[0].distance == 0.1


def test_parse_list_output_reads_models() -> None:
    entries = parse_list_output("docs/a.md  [all-minilm-l6-v2, bge-small-en-v1.5]\n")

    assert entries[0].path == "docs/a.md"
    assert entries[0].models == ["all-minilm-l6-v2", "bge-small-en-v1.5"]


def test_picvec_prepare_job_home_bootstraps_missing_schema(tmp_path: Path) -> None:
    settings = Settings(data_dir=tmp_path / "data")
    runner = PicvecRunner(settings)
    runner.shared_picvec_home.mkdir(parents=True, exist_ok=True)
    (runner.shared_picvec_home / "models").mkdir(parents=True, exist_ok=True)
    (runner.shared_picvec_home / "lib").mkdir(parents=True, exist_ok=True)
    (runner.shared_picvec_home / "config.json").write_text('{"default_model":"clip"}')
    connection = sqlite3.connect(runner.shared_picvec_home / "picvec.db")
    connection.execute(
        "CREATE TABLE IF NOT EXISTS image_embeddings (image_id TEXT, model_id TEXT, embedding BLOB)"
    )
    connection.commit()
    connection.close()
    runner._shared_ready = True

    job_dir = tmp_path / "job"
    stale_home = job_dir / "picvec-user" / ".picvec"
    stale_home.mkdir(parents=True, exist_ok=True)
    sqlite3.connect(stale_home / "picvec.db").close()

    runner.prepare_job_home(job_dir)

    job_db = stale_home / "picvec.db"
    job_config = stale_home / "config.json"
    tables = (
        sqlite3.connect(job_db)
        .execute("SELECT name FROM sqlite_master WHERE type='table'")
        .fetchall()
    )

    assert ("image_embeddings",) in tables
    assert job_config.exists()
