<p align="center">
  <img src="arcnem-logo.svg" alt="Arcnem AI" width="120" />
</p>

<h1 align="center">omnivec</h1>

<p align="center">
  <strong>API-first asset librarian for local-first document and image similarity analysis.</strong>
</p>

<p align="center">
  <a href="README.ja.md">日本語</a> ·
  <a href="#install">Install</a> ·
  <a href="#quick-start">Quick Start</a> ·
  <a href="#api">API</a> ·
  <a href="#docs">Docs</a>
</p>

---

omnivec accepts a ZIP of documents and images, runs local similarity analysis with `texvec` and `picvec`, and returns:

- structured JSON analysis
- a markdown report written from that analysis

Supported inputs:

- documents: `.txt`, `.md`, `.markdown`
- images: `.jpg`, `.jpeg`, `.png`

## What To Know First

- One upload creates one job directory on disk.
- ZIP extraction, file classification, duplicate grouping, similarity search, and clustering are deterministic.
- CrewAI is only used for the final markdown report.

## Install

Ensure you have Python `>=3.10,<3.14` and [uv](https://docs.astral.sh/uv/) installed.

Install dependencies:

```sh
uv sync
```

If you want to run omnivec locally without Docker, make sure `texvec` and `picvec` are available on your `PATH`.

For example, from local source checkouts:

```sh
cd ~/Documents/GitHub/picvec
go build -o /usr/local/bin/picvec .

cd ~/Documents/GitHub/texvec
go build -o /usr/local/bin/texvec .
```

Set the core environment variables:

```sh
export OPENAI_API_KEY=your-key
export OMNIVEC_DATA_DIR=$PWD/.omnivec-data
export OMNIVEC_API_KEY=dev-secret
```

`OPENAI_API_KEY` is required for CrewAI report generation. If you prefer, put these values in `.env`.

## Quick Start

The repo includes a small demo corpus under `sample_assets/`.

Start the API:

```sh
make serve
```

In another terminal, run the sample workflow:

```sh
make smoke-all
```

That flow builds `sample-assets.zip`, uploads it, polls the job, and fetches the final report. The first startup can take longer because `make serve` warms shared `texvec` and `picvec` caches.

If you want to drive the API directly, the shortest manual flow is:

```sh
make sample-zip

curl -X POST \
  -H "X-API-Key: dev-secret" \
  -F "file=@sample-assets.zip" \
  http://127.0.0.1:8000/v1/jobs
```

You can optionally add `-F "curation_goal=discovery"`, `dedupe`, or `taxonomy_cleanup` to bias the final report.

## Development

Run the default local test suite with:

```sh
uv run pytest
```

GitHub Actions runs the same `uv run pytest` command for pull requests and pushes to `main`.

## API

| Endpoint | What it does |
|---------|--------------|
| `POST /v1/jobs` | Upload a ZIP and enqueue a new analysis job |
| `GET /v1/jobs/{job_id}` | Return job status, timestamps, counts, and any error |
| `GET /v1/jobs/{job_id}/report` | Return the final markdown report plus structured JSON analysis |
| `GET /healthz` | Liveness check |

If `OMNIVEC_API_KEY` is set, all `/v1/*` endpoints require `X-API-Key`.

`POST /v1/jobs` accepts:

- `file` for the ZIP upload
- optional `curation_goal` with `discovery`, `dedupe`, or `taxonomy_cleanup`

## Docs

- [Technical overview](docs/technical-overview.md)
- [Operations and development](docs/operations.md)
- [Deployment](docs/deployment.md)
- [Extending Omnivec](docs/extending-omnivec.md)

## License

omnivec is released under the [MIT License](LICENSE).

---

<p align="center">
  Built by <a href="https://arcnem.ai">Arcnem AI</a>.
</p>
