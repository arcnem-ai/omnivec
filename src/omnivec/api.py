from __future__ import annotations

import shutil
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, File, Header, HTTPException, Request, UploadFile, status

from omnivec.jobs import AssetAnalyzer, JobService
from omnivec.reporting import CrewAIReportGenerator
from omnivec.runners import PicvecRunner, TexvecRunner
from omnivec.schemas import JobCreateResponse, JobReportResponse, JobState, JobStatusResponse
from omnivec.settings import Settings, get_settings
from omnivec.storage import JobStore


def create_app(
    settings: Settings | None = None,
    job_service: JobService | None = None,
) -> FastAPI:
    settings = settings or get_settings()

    if job_service is None:
        store = JobStore(settings)
        analyzer = AssetAnalyzer(
            settings=settings,
            document_runner=TexvecRunner(settings),
            image_runner=PicvecRunner(settings),
        )
        job_service = JobService(
            settings=settings,
            store=store,
            analyzer=analyzer,
            report_generator=CrewAIReportGenerator(settings),
        )

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        job_service.prepare()
        yield

    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        lifespan=lifespan,
    )
    app.state.job_service = job_service
    app.state.settings = settings

    def require_api_key(x_api_key: str | None = Header(default=None)) -> None:
        if not settings.api_key:
            return
        if x_api_key != settings.api_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key",
            )

    @app.get("/healthz")
    async def healthz() -> dict[str, str]:
        return {"status": "ok"}

    @app.post(
        "/v1/jobs",
        response_model=JobCreateResponse,
        status_code=status.HTTP_202_ACCEPTED,
        dependencies=[Depends(require_api_key)],
    )
    async def create_job(request: Request, file: UploadFile = File(...)) -> JobCreateResponse:
        service: JobService = request.app.state.job_service
        record = service.create_job(file.filename or "upload.zip")
        upload_path = service.store.upload_path(record.job_id)
        with upload_path.open("wb") as output:
            shutil.copyfileobj(file.file, output)

        service.start_job(record.job_id)
        return _job_create_response(record.job_id)

    @app.get(
        "/v1/jobs/{job_id}",
        response_model=JobStatusResponse,
        dependencies=[Depends(require_api_key)],
    )
    async def get_job(job_id: str, request: Request) -> JobStatusResponse:
        service: JobService = request.app.state.job_service
        try:
            record = service.get_status(job_id)
        except FileNotFoundError as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found") from exc
        return JobStatusResponse(
            **record.model_dump(),
            status_url=_status_url(job_id),
            report_url=_report_url(job_id),
        )

    @app.get(
        "/v1/jobs/{job_id}/report",
        response_model=JobReportResponse,
        dependencies=[Depends(require_api_key)],
    )
    async def get_report(job_id: str, request: Request) -> JobReportResponse:
        service: JobService = request.app.state.job_service
        try:
            status_record = service.get_status(job_id)
        except FileNotFoundError as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found") from exc

        if status_record.status != JobState.SUCCEEDED:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Report is not available until the job succeeds",
            )

        analysis = service.get_analysis(job_id)
        report_markdown = service.get_report(job_id)
        return JobReportResponse(
            job_id=job_id,
            report_markdown=report_markdown,
            counts=analysis.counts,
            ignored_files=analysis.ignored_files,
            exact_duplicate_groups=analysis.exact_duplicate_groups,
            document_clusters=analysis.document_clusters,
            image_clusters=analysis.image_clusters,
        )

    return app


def _job_create_response(job_id: str) -> JobCreateResponse:
    return JobCreateResponse(
        job_id=job_id,
        status=JobState.QUEUED,
        status_url=_status_url(job_id),
        report_url=_report_url(job_id),
    )


def _status_url(job_id: str) -> str:
    return f"/v1/jobs/{job_id}"


def _report_url(job_id: str) -> str:
    return f"/v1/jobs/{job_id}/report"
