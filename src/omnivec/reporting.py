"""Report generation layer.

Structured analysis comes in here after the deterministic pipeline finishes.
This module turns that saved analysis into markdown.
"""

from __future__ import annotations

import json
import os
from typing import Protocol

from omnivec.crew import create_asset_librarian_crew
from omnivec.schemas import AssetAnalysis, CurationGoal
from omnivec.settings import Settings


class ReportGenerator(Protocol):
    def generate_report(
        self, analysis: AssetAnalysis, curation_goal: CurationGoal | None = None
    ) -> str: ...


class CrewAIReportGenerator:
    """CrewAI-backed report generator used for the final summary step."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def generate_report(
        self, analysis: AssetAnalysis, curation_goal: CurationGoal | None = None
    ) -> str:
        if not self.settings.openai_api_key:
            raise RuntimeError("OPENAI_API_KEY is required to generate CrewAI reports")

        os.environ.setdefault("CREWAI_TRACING_ENABLED", "false")
        result = create_asset_librarian_crew(self.settings.llm_model).kickoff(
            inputs={
                "analysis_payload": build_analysis_payload(analysis, curation_goal),
            }
        )
        report = getattr(result, "raw", str(result)).strip()
        if not report:
            raise RuntimeError("CrewAI returned an empty report")
        return report


def build_analysis_payload(
    analysis: AssetAnalysis, curation_goal: CurationGoal | None = None
) -> str:
    payload = {
        "curation_goal": curation_goal.value if curation_goal is not None else None,
        "counts": analysis.counts.model_dump(),
        "documents": analysis.document_files,
        "images": analysis.image_files,
        "ignored_files": analysis.ignored_files,
        "exact_duplicate_groups": [group.model_dump() for group in analysis.exact_duplicate_groups],
        "document_clusters": [cluster.model_dump() for cluster in analysis.document_clusters],
        "image_clusters": [cluster.model_dump() for cluster in analysis.image_clusters],
    }
    return json.dumps(payload, indent=2, sort_keys=True)
