from __future__ import annotations

import json

from omnivec.reporting import build_analysis_payload
from omnivec.schemas import AssetAnalysis, CurationGoal, FileCounts


def test_build_analysis_payload_includes_optional_curation_goal() -> None:
    analysis = AssetAnalysis(counts=FileCounts(documents=1, total_supported=1))

    payload = json.loads(build_analysis_payload(analysis, CurationGoal.TAXONOMY_CLEANUP))

    assert payload["curation_goal"] == "taxonomy_cleanup"


def test_build_analysis_payload_uses_null_when_curation_goal_is_unspecified() -> None:
    analysis = AssetAnalysis(counts=FileCounts(images=2, total_supported=2))

    payload = json.loads(build_analysis_payload(analysis))

    assert payload["curation_goal"] is None
