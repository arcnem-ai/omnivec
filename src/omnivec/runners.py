"""Thin wrappers around the `texvec` and `picvec` CLIs."""

from __future__ import annotations

import os
import re
import shutil
import sqlite3
import subprocess
import threading
from pathlib import Path
from typing import NamedTuple, Protocol

from omnivec.schemas import SearchHit
from omnivec.settings import Settings

SEARCH_RESULT_RE = re.compile(r"^\s*(?P<distance>\d+(?:\.\d+)?)\s+(?P<path>.+?)\s*$")
LIST_RESULT_RE = re.compile(r"^(?P<path>.+?)\s+\[(?P<models>.*)\]\s*$")


class RunnerError(RuntimeError):
    """Raised when a CLI similarity runner fails."""


class SimilarityRunner(Protocol):
    def index_files(self, job_dir: Path, workspace: Path, files: list[str]) -> None: ...
    def search(self, job_dir: Path, workspace: Path, query: str, limit: int) -> list[SearchHit]: ...


class ParsedListEntry(NamedTuple):
    path: str
    models: list[str]


def parse_search_output(output: str) -> list[SearchHit]:
    results: list[SearchHit] = []
    for raw_line in output.splitlines():
        line = raw_line.strip()
        if not line or line == "No results found.":
            continue

        match = SEARCH_RESULT_RE.match(line)
        if not match:
            continue

        results.append(
            SearchHit(
                path=match.group("path"),
                distance=float(match.group("distance")),
            )
        )
    return results


def parse_list_output(output: str) -> list[ParsedListEntry]:
    results: list[ParsedListEntry] = []
    for raw_line in output.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("No "):
            continue

        match = LIST_RESULT_RE.match(line)
        if not match:
            continue

        models = [model.strip() for model in match.group("models").split(",") if model.strip()]
        results.append(ParsedListEntry(match.group("path"), models))
    return results


class BaseCliRunner:
    """Shared subprocess behavior for similarity runners."""

    def __init__(self, settings: Settings, binary: str) -> None:
        self.settings = settings
        self.binary = binary
        self._init_lock = threading.Lock()
        self._shared_ready = False

    def _run(self, args: list[str], *, env: dict[str, str], cwd: Path) -> str:
        command = [self.binary, *args]
        completed = subprocess.run(
            command,
            cwd=cwd,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        if completed.returncode != 0:
            details = completed.stderr.strip() or completed.stdout.strip() or "unknown error"
            raise RunnerError(f"{' '.join(command)} failed: {details}")
        return completed.stdout


class TexvecRunner(BaseCliRunner):
    """Document similarity runner with shared model cache wiring."""

    def __init__(self, settings: Settings) -> None:
        super().__init__(settings, settings.texvec_bin)
        self.shared_home = settings.cache_dir / "texvec"

    def build_env(self, job_home: Path) -> dict[str, str]:
        env = os.environ.copy()
        env["TEXVEC_HOME"] = str(job_home.resolve())
        return env

    def ensure_shared_ready(self) -> None:
        with self._init_lock:
            if self._shared_ready:
                return
            self.shared_home.mkdir(parents=True, exist_ok=True)
            self._run(["init"], env=self.build_env(self.shared_home), cwd=self.shared_home)
            self._shared_ready = True

    def prepare_job_home(self, job_dir: Path) -> Path:
        self.ensure_shared_ready()
        job_home = job_dir / "texvec-home"
        job_home.mkdir(parents=True, exist_ok=True)
        _link_shared_directory(self.shared_home / "models", job_home / "models")
        _link_shared_directory(self.shared_home / "lib", job_home / "lib")
        return job_home

    def index_files(self, job_dir: Path, workspace: Path, files: list[str]) -> None:
        job_home = self.prepare_job_home(job_dir)
        env = self.build_env(job_home)
        for file_path in files:
            self._run(["embed", file_path], env=env, cwd=workspace)

    def search(self, job_dir: Path, workspace: Path, query: str, limit: int) -> list[SearchHit]:
        job_home = self.prepare_job_home(job_dir)
        env = self.build_env(job_home)
        output = self._run(["search", "--limit", str(limit), query], env=env, cwd=workspace)
        return parse_search_output(output)


class PicvecRunner(BaseCliRunner):
    """Image similarity runner with per-job HOME and shared cache wiring."""

    def __init__(self, settings: Settings) -> None:
        super().__init__(settings, settings.picvec_bin)
        self.shared_user_home = settings.cache_dir / "picvec-home"

    @property
    def shared_picvec_home(self) -> Path:
        return self.shared_user_home / ".picvec"

    def build_env(self, home_dir: Path) -> dict[str, str]:
        env = os.environ.copy()
        env["HOME"] = str(home_dir.resolve())
        return env

    def ensure_shared_ready(self) -> None:
        with self._init_lock:
            if self._shared_ready:
                return
            self.shared_user_home.mkdir(parents=True, exist_ok=True)
            self._run(
                ["init"], env=self.build_env(self.shared_user_home), cwd=self.shared_user_home
            )
            self._shared_ready = True

    def prepare_job_home(self, job_dir: Path) -> Path:
        self.ensure_shared_ready()
        user_home = job_dir / "picvec-user"
        user_home.mkdir(parents=True, exist_ok=True)

        picvec_home = user_home / ".picvec"
        picvec_home.mkdir(parents=True, exist_ok=True)
        _link_shared_directory(self.shared_picvec_home / "models", picvec_home / "models")
        _link_shared_directory(self.shared_picvec_home / "lib", picvec_home / "lib")
        _copy_if_missing(self.shared_picvec_home / "config.json", picvec_home / "config.json")

        db_path = picvec_home / "picvec.db"
        if not _sqlite_table_exists(db_path, "image_embeddings"):
            shutil.copy2(self.shared_picvec_home / "picvec.db", db_path)
            if not _sqlite_table_exists(db_path, "image_embeddings"):
                raise RunnerError("shared picvec database is missing the image_embeddings schema")

        return user_home

    def index_files(self, job_dir: Path, workspace: Path, files: list[str]) -> None:
        user_home = self.prepare_job_home(job_dir)
        env = self.build_env(user_home)
        for file_path in files:
            self._run(["embed", file_path], env=env, cwd=workspace)

    def search(self, job_dir: Path, workspace: Path, query: str, limit: int) -> list[SearchHit]:
        user_home = self.prepare_job_home(job_dir)
        env = self.build_env(user_home)
        output = self._run(["search", "--limit", str(limit), query], env=env, cwd=workspace)
        return parse_search_output(output)


def _link_shared_directory(source: Path, target: Path) -> None:
    source.mkdir(parents=True, exist_ok=True)
    if target.is_symlink() or target.exists():
        if target.is_symlink() and target.resolve() == source.resolve():
            return
        if target.is_dir() and not target.is_symlink():
            return
        target.unlink()
    target.symlink_to(source, target_is_directory=True)


def _copy_if_missing(source: Path, target: Path) -> None:
    if target.exists():
        return
    shutil.copy2(source, target)


def _sqlite_table_exists(db_path: Path, table_name: str) -> bool:
    if not db_path.exists():
        return False

    try:
        connection = sqlite3.connect(db_path)
    except sqlite3.Error:
        return False

    try:
        cursor = connection.execute(
            "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ? LIMIT 1",
            (table_name,),
        )
        return cursor.fetchone() is not None
    except sqlite3.Error:
        return False
    finally:
        connection.close()
