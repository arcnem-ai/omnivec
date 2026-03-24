from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import httpx


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run a full sample Omnivec workflow against a live server."
    )
    parser.add_argument("--base-url", default="http://127.0.0.1:8000", help="Base API URL")
    parser.add_argument("--api-key", default="dev-secret", help="API key for /v1 endpoints")
    parser.add_argument("--zip-path", default="sample-assets.zip", help="ZIP file to upload")
    parser.add_argument("--timeout-seconds", type=int, default=180, help="Maximum wait time")
    parser.add_argument(
        "--poll-interval", type=float, default=1.0, help="Polling interval in seconds"
    )
    args = parser.parse_args()

    zip_path = Path(args.zip_path)
    if not zip_path.exists():
        raise SystemExit(f"ZIP file not found: {zip_path}")

    headers = {"X-API-Key": args.api_key}
    with httpx.Client(base_url=args.base_url, timeout=60.0) as client:
        with zip_path.open("rb") as handle:
            response = client.post(
                "/v1/jobs",
                headers=headers,
                files={"file": (zip_path.name, handle, "application/zip")},
            )
        response.raise_for_status()
        job = response.json()
        job_id = job["job_id"]
        print(json.dumps(job, indent=2))

        deadline = time.time() + args.timeout_seconds
        while True:
            status_response = client.get(f"/v1/jobs/{job_id}", headers=headers)
            status_response.raise_for_status()
            status_payload = status_response.json()
            print(json.dumps(status_payload, indent=2))

            state = status_payload["status"]
            if state == "succeeded":
                report_response = client.get(f"/v1/jobs/{job_id}/report", headers=headers)
                report_response.raise_for_status()
                report_payload = report_response.json()
                print(json.dumps(report_payload, indent=2))
                print("\n--- report_markdown ---\n")
                print(report_payload["report_markdown"])
                return

            if state == "failed":
                print("Job failed.", file=sys.stderr)
                raise SystemExit(1)

            if time.time() >= deadline:
                print("Timed out waiting for job completion.", file=sys.stderr)
                raise SystemExit(1)

            time.sleep(args.poll_interval)


if __name__ == "__main__":
    main()
