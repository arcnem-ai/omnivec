from __future__ import annotations

import io
import re
import time
import zipfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from omnivec.api import create_app
from omnivec.jobs import AssetAnalyzer, JobService
from omnivec.runners import SimilarityRunner
from omnivec.schemas import AssetAnalysis, JobState, SearchHit
from omnivec.settings import Settings
from omnivec.storage import JobStore

GROUP_SUFFIX_RE = re.compile(r"([_-])(copy|\d+)$")


class FakeSimilarityRunner(SimilarityRunner):
    def __init__(self) -> None:
        self.indexed: dict[str, list[str]] = {}

    def index_files(self, job_dir: Path, workspace: Path, files: list[str]) -> None:
        self.indexed[str(job_dir)] = list(files)

    def search(self, job_dir: Path, workspace: Path, query: str, limit: int) -> list[SearchHit]:
        indexed = self.indexed.get(str(job_dir), [])
        query_group = _group_key(query)
        hits = []
        for candidate in indexed:
            if candidate == query:
                continue
            distance = 0.1 if _group_key(candidate) == query_group else 0.9
            hits.append(SearchHit(path=candidate, distance=distance))
        hits.sort(key=lambda hit: (hit.distance, hit.path))
        return hits[:limit]


class FakeReportGenerator:
    def generate_report(self, analysis: AssetAnalysis) -> str:
        return (
            "# Asset Librarian Report\n\n"
            f"Supported files: {analysis.counts.total_supported}\n\n"
            f"Documents: {analysis.counts.documents}\n"
            f"Images: {analysis.counts.images}\n"
            f"Ignored: {analysis.counts.ignored}\n\n"
            f"Duplicate groups: {len(analysis.exact_duplicate_groups)}\n"
            f"Document clusters: {len(analysis.document_clusters)}\n"
            f"Image clusters: {len(analysis.image_clusters)}\n"
        )


def build_test_client(tmp_path: Path, api_key: str | None = "secret") -> TestClient:
    settings = Settings(
        data_dir=tmp_path / "data",
        api_key=api_key,
        texvec_bin="texvec",
        picvec_bin="picvec",
        llm_model="openai/gpt-4o-mini",
    )
    settings.prepare_directories()
    store = JobStore(settings)
    service = JobService(
        settings=settings,
        store=store,
        analyzer=AssetAnalyzer(
            settings=settings,
            document_runner=FakeSimilarityRunner(),
            image_runner=FakeSimilarityRunner(),
        ),
        report_generator=FakeReportGenerator(),
    )
    return TestClient(create_app(settings=settings, job_service=service))


def make_zip_bytes(members: dict[str, bytes]) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        for name, contents in members.items():
            archive.writestr(name, contents)
    return buffer.getvalue()


def wait_for_job(client: TestClient, job_id: str, headers: dict[str, str] | None = None) -> dict:
    headers = headers or {}
    for _ in range(100):
        response = client.get(f"/v1/jobs/{job_id}", headers=headers)
        payload = response.json()
        if payload["status"] in {JobState.SUCCEEDED.value, JobState.FAILED.value}:
            return payload
        time.sleep(0.05)
    raise AssertionError(f"Timed out waiting for job {job_id}")


def _group_key(path: str) -> str:
    stem = Path(path).stem.lower()
    return GROUP_SUFFIX_RE.sub("", stem)


@pytest.fixture
def auth_headers() -> dict[str, str]:
    return {"X-API-Key": "secret"}
