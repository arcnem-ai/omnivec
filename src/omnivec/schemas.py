"""Pydantic models shared across the API, jobs, and persistence layers."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Literal, TypeAlias

from pydantic import BaseModel, Field

AssetKind: TypeAlias = Literal["document", "image"]


class JobState(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class CurationGoal(str, Enum):
    DISCOVERY = "discovery"
    DEDUPE = "dedupe"
    TAXONOMY_CLEANUP = "taxonomy_cleanup"


class FileCounts(BaseModel):
    documents: int = 0
    images: int = 0
    ignored: int = 0
    total_supported: int = 0


class SearchHit(BaseModel):
    path: str
    distance: float


class SimilarityEdge(BaseModel):
    source: str
    target: str
    distance: float


class SimilarityCluster(BaseModel):
    cluster_id: str
    kind: AssetKind
    members: list[str] = Field(default_factory=list)
    edges: list[SimilarityEdge] = Field(default_factory=list)


class DuplicateGroup(BaseModel):
    kind: AssetKind
    sha256: str
    files: list[str] = Field(default_factory=list)


class AssetAnalysis(BaseModel):
    counts: FileCounts = Field(default_factory=FileCounts)
    document_files: list[str] = Field(default_factory=list)
    image_files: list[str] = Field(default_factory=list)
    ignored_files: list[str] = Field(default_factory=list)
    exact_duplicate_groups: list[DuplicateGroup] = Field(default_factory=list)
    document_clusters: list[SimilarityCluster] = Field(default_factory=list)
    image_clusters: list[SimilarityCluster] = Field(default_factory=list)


class JobStatusRecord(BaseModel):
    job_id: str
    filename: str
    curation_goal: CurationGoal | None = None
    status: JobState
    created_at: datetime
    updated_at: datetime
    started_at: datetime | None = None
    finished_at: datetime | None = None
    error: str | None = None
    counts: FileCounts = Field(default_factory=FileCounts)
    analysis_ready: bool = False
    report_ready: bool = False


class JobCreateResponse(BaseModel):
    job_id: str
    curation_goal: CurationGoal | None = None
    status: JobState
    status_url: str
    report_url: str


class JobStatusResponse(JobStatusRecord):
    status_url: str
    report_url: str


class JobReportResponse(BaseModel):
    job_id: str
    curation_goal: CurationGoal | None
    report_markdown: str
    counts: FileCounts
    ignored_files: list[str]
    exact_duplicate_groups: list[DuplicateGroup]
    document_clusters: list[SimilarityCluster]
    image_clusters: list[SimilarityCluster]
