from __future__ import annotations

from tests.conftest import build_test_client, make_zip_bytes, wait_for_job


def test_create_job_requires_api_key_when_configured(tmp_path) -> None:
    with build_test_client(tmp_path, api_key="secret") as client:
        response = client.post(
            "/v1/jobs",
            files={"file": ("assets.zip", make_zip_bytes({"doc.md": b"hello"}), "application/zip")},
        )

    assert response.status_code == 401


def test_create_job_without_api_key_configured_is_allowed(tmp_path) -> None:
    with build_test_client(tmp_path, api_key=None) as client:
        response = client.post(
            "/v1/jobs",
            files={"file": ("assets.zip", make_zip_bytes({"doc.md": b"hello"}), "application/zip")},
        )
        payload = response.json()
        status_payload = wait_for_job(client, payload["job_id"])

    assert response.status_code == 202
    assert status_payload["status"] == "succeeded"


def test_mixed_pack_returns_report_and_clusters(tmp_path, auth_headers) -> None:
    members = {
        "docs/clusterdoc-1.md": b"alpha",
        "docs/clusterdoc-2.md": b"beta",
        "docs/dup-1.md": b"same",
        "docs/dup-2.md": b"same",
        "images/clusterimg-1.png": b"img-a",
        "images/clusterimg-2.png": b"img-b",
        "images/dup-1.png": b"same-image",
        "images/dup-2.png": b"same-image",
        "ignored.bin": b"ignored",
    }

    with build_test_client(tmp_path) as client:
        response = client.post(
            "/v1/jobs",
            headers=auth_headers,
            files={"file": ("assets.zip", make_zip_bytes(members), "application/zip")},
        )
        payload = response.json()
        status_payload = wait_for_job(client, payload["job_id"], headers=auth_headers)
        report_response = client.get(payload["report_url"], headers=auth_headers)
        report = report_response.json()

    assert response.status_code == 202
    assert status_payload["status"] == "succeeded"
    assert report["counts"] == {
        "documents": 4,
        "images": 4,
        "ignored": 1,
        "total_supported": 8,
    }
    assert len(report["exact_duplicate_groups"]) == 2
    assert len(report["document_clusters"]) >= 1
    assert len(report["image_clusters"]) >= 1
    assert "Supported files: 8" in report["report_markdown"]


def test_docs_only_pack_succeeds(tmp_path, auth_headers) -> None:
    with build_test_client(tmp_path) as client:
        response = client.post(
            "/v1/jobs",
            headers=auth_headers,
            files={
                "file": (
                    "docs.zip",
                    make_zip_bytes(
                        {
                            "docs/clusterdoc-1.md": b"alpha",
                            "docs/clusterdoc-2.md": b"beta",
                            "ignored.pdf": b"pdf",
                        }
                    ),
                    "application/zip",
                )
            },
        )
        payload = response.json()
        status_payload = wait_for_job(client, payload["job_id"], headers=auth_headers)
        report = client.get(payload["report_url"], headers=auth_headers).json()

    assert status_payload["status"] == "succeeded"
    assert report["counts"]["documents"] == 2
    assert report["counts"]["images"] == 0
    assert report["image_clusters"] == []


def test_images_only_pack_succeeds(tmp_path, auth_headers) -> None:
    with build_test_client(tmp_path) as client:
        response = client.post(
            "/v1/jobs",
            headers=auth_headers,
            files={
                "file": (
                    "images.zip",
                    make_zip_bytes(
                        {
                            "images/clusterimg-1.png": b"alpha",
                            "images/clusterimg-2.png": b"beta",
                        }
                    ),
                    "application/zip",
                )
            },
        )
        payload = response.json()
        status_payload = wait_for_job(client, payload["job_id"], headers=auth_headers)
        report = client.get(payload["report_url"], headers=auth_headers).json()

    assert status_payload["status"] == "succeeded"
    assert report["counts"]["documents"] == 0
    assert report["counts"]["images"] == 2
    assert report["document_clusters"] == []


def test_unsupported_pack_fails_cleanly(tmp_path, auth_headers) -> None:
    with build_test_client(tmp_path) as client:
        response = client.post(
            "/v1/jobs",
            headers=auth_headers,
            files={
                "file": (
                    "unsupported.zip",
                    make_zip_bytes({"notes.pdf": b"pdf", "photo.gif": b"gif"}),
                    "application/zip",
                )
            },
        )
        payload = response.json()
        status_payload = wait_for_job(client, payload["job_id"], headers=auth_headers)
        report_response = client.get(payload["report_url"], headers=auth_headers)

    assert status_payload["status"] == "failed"
    assert "supported" in status_payload["error"].lower()
    assert report_response.status_code == 409
