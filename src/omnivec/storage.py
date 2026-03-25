"""File-backed persistence for job status, analysis, and reports."""

from __future__ import annotations

import shutil
import threading
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4

from omnivec.schemas import AssetAnalysis, CurationGoal, JobState, JobStatusRecord
from omnivec.settings import Settings


class JobStore:
    """Read and write job artifacts under `OMNIVEC_DATA_DIR`."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._lock = threading.Lock()

    def prepare(self) -> None:
        self.settings.prepare_directories()

    def create_job(
        self, filename: str, curation_goal: CurationGoal | None = None
    ) -> JobStatusRecord:
        job_id = uuid4().hex
        now = _utcnow()
        record = JobStatusRecord(
            job_id=job_id,
            filename=filename,
            curation_goal=curation_goal,
            status=JobState.QUEUED,
            created_at=now,
            updated_at=now,
        )
        self.job_dir(job_id).mkdir(parents=True, exist_ok=True)
        self.save_status(record)
        return record

    def job_dir(self, job_id: str) -> Path:
        return self.settings.jobs_dir / job_id

    def upload_path(self, job_id: str) -> Path:
        return self.job_dir(job_id) / "upload.zip"

    def extracted_dir(self, job_id: str) -> Path:
        return self.job_dir(job_id) / "extracted"

    def status_path(self, job_id: str) -> Path:
        return self.job_dir(job_id) / "status.json"

    def analysis_path(self, job_id: str) -> Path:
        return self.job_dir(job_id) / "analysis.json"

    def report_path(self, job_id: str) -> Path:
        return self.job_dir(job_id) / "report.md"

    def save_status(self, record: JobStatusRecord) -> None:
        self._write_text(
            self.status_path(record.job_id), record.model_dump_json(indent=2, exclude_none=True)
        )

    def load_status(self, job_id: str) -> JobStatusRecord:
        path = self.status_path(job_id)
        if not path.exists():
            raise FileNotFoundError(job_id)
        return JobStatusRecord.model_validate_json(path.read_text())

    def update_status(self, job_id: str, **changes: object) -> JobStatusRecord:
        with self._lock:
            record = self.load_status(job_id)
            payload = record.model_dump()
            payload.update(changes)
            payload["updated_at"] = _utcnow()
            updated = JobStatusRecord.model_validate(payload)
            self.save_status(updated)
            return updated

    def save_analysis(self, job_id: str, analysis: AssetAnalysis) -> None:
        self._write_text(self.analysis_path(job_id), analysis.model_dump_json(indent=2))

    def load_analysis(self, job_id: str) -> AssetAnalysis:
        path = self.analysis_path(job_id)
        if not path.exists():
            raise FileNotFoundError(job_id)
        return AssetAnalysis.model_validate_json(path.read_text())

    def save_report(self, job_id: str, report_markdown: str) -> None:
        self._write_text(self.report_path(job_id), report_markdown)

    def load_report(self, job_id: str) -> str:
        path = self.report_path(job_id)
        if not path.exists():
            raise FileNotFoundError(job_id)
        return path.read_text()

    def mark_incomplete_jobs_failed(self) -> None:
        for status_file in self.settings.jobs_dir.glob("*/status.json"):
            record = JobStatusRecord.model_validate_json(status_file.read_text())
            if record.status not in {JobState.QUEUED, JobState.RUNNING}:
                continue

            failed = record.model_copy(
                update={
                    "status": JobState.FAILED,
                    "error": "Job was interrupted before completion.",
                    "finished_at": _utcnow(),
                    "updated_at": _utcnow(),
                }
            )
            self.save_status(failed)

    def cleanup_expired_jobs(self) -> None:
        cutoff = _utcnow() - timedelta(hours=self.settings.job_ttl_hours)
        for status_file in self.settings.jobs_dir.glob("*/status.json"):
            record = JobStatusRecord.model_validate_json(status_file.read_text())
            if record.status not in {JobState.SUCCEEDED, JobState.FAILED}:
                continue
            if not record.finished_at or record.finished_at >= cutoff:
                continue
            shutil.rmtree(self.job_dir(record.job_id), ignore_errors=True)

    def _write_text(self, path: Path, contents: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        temp_path = path.with_suffix(path.suffix + ".tmp")
        temp_path.write_text(contents)
        temp_path.replace(path)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)
