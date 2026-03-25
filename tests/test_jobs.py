from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

from omnivec.schemas import CurationGoal, JobState
from omnivec.settings import Settings
from omnivec.storage import JobStore


def test_job_store_marks_incomplete_jobs_failed_and_cleans_old_results(tmp_path: Path) -> None:
    settings = Settings(data_dir=tmp_path / "data", job_ttl_hours=1)
    settings.prepare_directories()
    store = JobStore(settings)

    running = store.create_job("running.zip", curation_goal=CurationGoal.DEDUPE)
    store.update_status(running.job_id, status=JobState.RUNNING)

    finished = store.create_job("finished.zip")
    store.update_status(
        finished.job_id,
        status=JobState.SUCCEEDED,
        finished_at=datetime.now(timezone.utc) - timedelta(hours=2),
    )

    store.mark_incomplete_jobs_failed()
    recovered = store.load_status(running.job_id)
    assert recovered.status == JobState.FAILED
    assert recovered.curation_goal == CurationGoal.DEDUPE
    assert recovered.error == "Job was interrupted before completion."

    store.cleanup_expired_jobs()
    assert not store.job_dir(finished.job_id).exists()
