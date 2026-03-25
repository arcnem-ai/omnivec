from __future__ import annotations

from pathlib import Path

from scripts.run_sample_workflow import build_upload_request_summary


def test_build_upload_request_summary_includes_curation_goal_field() -> None:
    summary = build_upload_request_summary(
        base_url="http://127.0.0.1:8010/",
        zip_path=Path("sample-assets.zip"),
        api_key="super-secret",
        form_data={"curation_goal": "dedupe"},
    )

    assert summary["method"] == "POST"
    assert summary["url"] == "http://127.0.0.1:8010/v1/jobs"
    assert summary["headers"] == {"X-API-Key": "[redacted]"}
    assert summary["multipart_form"] == {
        "fields": {"curation_goal": "dedupe"},
        "file": {
            "field_name": "file",
            "filename": "sample-assets.zip",
            "content_type": "application/zip",
            "path": "sample-assets.zip",
        },
    }
