from __future__ import annotations

import json
import os
from typing import Protocol

from omnivec.crew import AssetLibrarianCrew
from omnivec.schemas import AssetAnalysis
from omnivec.settings import Settings


class ReportGenerator(Protocol):
    def generate_report(self, analysis: AssetAnalysis) -> str: ...


class CrewAIReportGenerator:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def generate_report(self, analysis: AssetAnalysis) -> str:
        if not self.settings.openai_api_key:
            raise RuntimeError("OPENAI_API_KEY is required to generate CrewAI reports")

        os.environ.setdefault("CREWAI_TRACING_ENABLED", "false")
        crew = AssetLibrarianCrew()
        crew.llm_model = self.settings.llm_model
        result = crew.crew().kickoff(
            inputs={
                "analysis_payload": build_analysis_payload(analysis),
            }
        )
        report = getattr(result, "raw", str(result)).strip()
        if not report:
            raise RuntimeError("CrewAI returned an empty report")
        return report


def build_analysis_payload(analysis: AssetAnalysis) -> str:
    payload = {
        "counts": analysis.counts.model_dump(),
        "documents": analysis.document_files,
        "images": analysis.image_files,
        "ignored_files": analysis.ignored_files,
        "exact_duplicate_groups": [group.model_dump() for group in analysis.exact_duplicate_groups],
        "document_clusters": [cluster.model_dump() for cluster in analysis.document_clusters],
        "image_clusters": [cluster.model_dump() for cluster in analysis.image_clusters],
    }
    return json.dumps(payload, indent=2, sort_keys=True)
