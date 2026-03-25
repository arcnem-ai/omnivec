"""Job orchestration from uploaded ZIP to saved report."""

from __future__ import annotations

import threading
from datetime import datetime, timezone
from pathlib import Path

from omnivec.clustering import build_reciprocal_clusters
from omnivec.ingestion import classify_assets, group_exact_duplicates, safe_extract_zip
from omnivec.reporting import ReportGenerator
from omnivec.runners import SimilarityRunner
from omnivec.schemas import (
    AssetAnalysis,
    AssetKind,
    CurationGoal,
    FileCounts,
    JobState,
    JobStatusRecord,
)
from omnivec.settings import Settings
from omnivec.storage import JobStore


class AssetAnalyzer:
    """Build structured analysis for one uploaded ZIP."""

    def __init__(
        self,
        settings: Settings,
        document_runner: SimilarityRunner,
        image_runner: SimilarityRunner,
    ) -> None:
        self.settings = settings
        self.document_runner = document_runner
        self.image_runner = image_runner

    def analyze(self, job_id: str, store: JobStore) -> AssetAnalysis:
        job_dir = store.job_dir(job_id)
        extract_dir = store.extracted_dir(job_id)
        safe_extract_zip(store.upload_path(job_id), extract_dir)

        inventory = classify_assets(extract_dir)
        if inventory.supported_count == 0:
            raise ValueError(
                "ZIP archive does not contain any supported "
                ".txt, .md, .markdown, .jpg, .jpeg, or .png files"
            )

        document_duplicates = group_exact_duplicates(extract_dir, inventory.documents, "document")
        image_duplicates = group_exact_duplicates(extract_dir, inventory.images, "image")

        document_clusters = self._analyze_similarity(
            kind="document",
            runner=self.document_runner,
            job_dir=job_dir,
            extract_dir=extract_dir,
            files=inventory.documents,
        )
        image_clusters = self._analyze_similarity(
            kind="image",
            runner=self.image_runner,
            job_dir=job_dir,
            extract_dir=extract_dir,
            files=inventory.images,
        )

        return AssetAnalysis(
            counts=FileCounts(
                documents=len(inventory.documents),
                images=len(inventory.images),
                ignored=len(inventory.ignored),
                total_supported=inventory.supported_count,
            ),
            document_files=inventory.documents,
            image_files=inventory.images,
            ignored_files=inventory.ignored,
            exact_duplicate_groups=document_duplicates + image_duplicates,
            document_clusters=document_clusters,
            image_clusters=image_clusters,
        )

    def _analyze_similarity(
        self,
        *,
        kind: AssetKind,
        runner: SimilarityRunner,
        job_dir: Path,
        extract_dir: Path,
        files: list[str],
    ):
        if len(files) < 2:
            return []

        runner.index_files(job_dir, extract_dir, files)
        search_results = {
            file_path: [
                hit
                for hit in runner.search(
                    job_dir, extract_dir, file_path, self.settings.max_neighbors
                )
                if hit.path in files
            ]
            for file_path in files
        }
        return build_reciprocal_clusters(kind=kind, search_results=search_results)


class JobService:
    """Own job lifecycle, background execution, and persisted artifacts."""

    def __init__(
        self,
        settings: Settings,
        store: JobStore,
        analyzer: AssetAnalyzer,
        report_generator: ReportGenerator,
    ) -> None:
        self.settings = settings
        self.store = store
        self.analyzer = analyzer
        self.report_generator = report_generator
        self._semaphore = threading.BoundedSemaphore(settings.max_concurrent_jobs)

    def prepare(self) -> None:
        self.store.prepare()
        self.store.mark_incomplete_jobs_failed()
        self.store.cleanup_expired_jobs()

    def create_job(
        self, filename: str, curation_goal: CurationGoal | None = None
    ) -> JobStatusRecord:
        self.store.cleanup_expired_jobs()
        return self.store.create_job(filename, curation_goal=curation_goal)

    def start_job(self, job_id: str) -> None:
        thread = threading.Thread(target=self._run_job, args=(job_id,), daemon=True)
        thread.start()

    def get_status(self, job_id: str) -> JobStatusRecord:
        return self.store.load_status(job_id)

    def get_analysis(self, job_id: str) -> AssetAnalysis:
        return self.store.load_analysis(job_id)

    def get_report(self, job_id: str) -> str:
        return self.store.load_report(job_id)

    def _run_job(self, job_id: str) -> None:
        with self._semaphore:
            status_record = self.store.update_status(
                job_id,
                status=JobState.RUNNING,
                started_at=datetime.now(timezone.utc),
                error=None,
            )
            try:
                analysis = self.analyzer.analyze(job_id, self.store)
                self.store.save_analysis(job_id, analysis)
                self.store.update_status(
                    job_id,
                    counts=analysis.counts,
                    analysis_ready=True,
                )

                report = self.report_generator.generate_report(
                    analysis,
                    curation_goal=status_record.curation_goal,
                )
                self.store.save_report(job_id, report)

                self.store.update_status(
                    job_id,
                    status=JobState.SUCCEEDED,
                    counts=analysis.counts,
                    analysis_ready=True,
                    report_ready=True,
                    finished_at=datetime.now(timezone.utc),
                )
            except Exception as exc:
                counts = self._best_effort_counts(job_id)
                self.store.update_status(
                    job_id,
                    status=JobState.FAILED,
                    counts=counts,
                    error=str(exc),
                    finished_at=datetime.now(timezone.utc),
                )
            finally:
                self.store.cleanup_expired_jobs()

    def _best_effort_counts(self, job_id: str) -> FileCounts:
        try:
            return self.store.load_analysis(job_id).counts
        except FileNotFoundError:
            return FileCounts()
