# AGENTS.md

## Project Summary

`omnivec` is an API-first asset librarian built with FastAPI and CrewAI. It accepts ZIP uploads of documents and images, runs local similarity analysis with `texvec` and `picvec`, saves structured artifacts on disk, and returns both JSON results and a markdown report.

## Start Here

If you are new to the repo, read these first:

1. `docs/technical-overview.md`
2. `src/omnivec/api.py`
3. `src/omnivec/jobs.py`

That path shows the full request flow before the work branches into ingestion, runners, storage, clustering, and reporting helpers.

## Architecture Invariants

- Keep the pipeline deterministic until the final report step. ZIP extraction, classification, duplicate grouping, similarity search, and clustering should stay local and predictable.
- CrewAI should only turn saved analysis into markdown. Do not move retrieval, indexing, or clustering decisions into agent prompts.
- Keep HTTP handlers thin. Put behavior in `jobs.py`, `ingestion.py`, `storage.py`, `runners.py`, or `reporting.py`.
- Treat `src/omnivec/schemas.py` as both API contract and on-disk persistence contract. Changes there affect `/v1/*` responses and the JSON files stored in each job directory.
- Preserve background job behavior. `POST /v1/jobs` should enqueue work and return quickly while `JobService` runs the job on a background thread.
- Preserve storage safety. `JobStore` writes artifacts through temp files and replace operations; do not downgrade persistence to partial writes.
- Preserve job isolation. Each upload gets its own job workspace, while expensive model/runtime assets stay in the shared cache under `OMNIVEC_DATA_DIR/cache`.
- Preserve the public API shape unless the change intentionally updates v1 behavior.

## Repository Map

- `src/omnivec/api.py`: FastAPI app, auth gate, and HTTP endpoints.
- `src/omnivec/jobs.py`: job lifecycle, background execution, cleanup, and orchestration.
- `src/omnivec/ingestion.py`: safe ZIP extraction, supported file classification, and exact duplicate grouping.
- `src/omnivec/runners.py`: subprocess wrappers and shared-cache wiring for `texvec` and `picvec`.
- `src/omnivec/clustering.py`: reciprocal-neighbor clustering.
- `src/omnivec/reporting.py`: report generator interface and CrewAI-backed markdown generation.
- `src/omnivec/crew.py`: CrewAI crew wiring plus YAML-backed config loading.
- `src/omnivec/schemas.py`: shared Pydantic models for API responses and persisted analysis/status.
- `src/omnivec/storage.py`: file-backed status, analysis, and report persistence.
- `src/omnivec/settings.py`: runtime configuration, env var parsing, and data/cache directory layout.
- `src/omnivec/main.py`: local CLI entrypoint for running the API with Uvicorn.
- `src/omnivec/config/`: CrewAI task and agent config.
- `sample_assets/`: checked-in demo corpus used by sample ZIP and smoke workflow scripts.
- `scripts/create_sample_zip.py`: builds the checked-in sample ZIP.
- `scripts/run_sample_workflow.py`: uploads a sample ZIP, polls status, and fetches the final report.
- `scripts/warm_cache.py`: initializes shared `texvec` and `picvec` caches for local/dev use.
- `CONTRIBUTING.md`: contributor workflow and repo expectations.
- `docs/technical-overview.md`: quickest architecture tour.
- `docs/operations.md`: commands, env vars, and runtime storage layout.
- `docs/deployment.md`: Docker and Railway deployment expectations.
- `docs/extending-omnivec.md`: likely future extension paths.
- `tests/`: offline, deterministic tests using fake runners and a fake report generator.

## Common Change Paths

| If you need to change... | Start here | Also verify |
|---|---|---|
| request validation, auth, status codes, or response fields | `src/omnivec/api.py`, `src/omnivec/schemas.py` | `tests/test_api.py` |
| job lifecycle, startup recovery, cleanup, or concurrency | `src/omnivec/jobs.py`, `src/omnivec/storage.py` | `tests/test_jobs.py`, `tests/test_api.py` |
| supported file types, ZIP safety, or duplicate grouping | `src/omnivec/ingestion.py` | `tests/test_ingestion.py`, `README.md`, `README.ja.md` |
| similarity runner setup or cache wiring | `src/omnivec/runners.py`, `src/omnivec/settings.py` | `tests/test_runners.py`, `docs/operations.md` |
| clustering behavior | `src/omnivec/clustering.py` | `tests/test_clustering.py` |
| report content, CrewAI prompt inputs, or curation-goal behavior | `src/omnivec/reporting.py`, `src/omnivec/crew.py`, `src/omnivec/config/` | `tests/test_reporting.py`, `tests/test_api.py` |
| env vars, defaults, or data paths | `src/omnivec/settings.py` | `tests/test_settings.py`, `.env.example`, `docs/operations.md`, `README.md`, `README.ja.md` |
| local/dev workflow commands | `Makefile`, `scripts/` | `README.md`, `README.ja.md`, `docs/operations.md`, `tests/test_sample_workflow.py` |
| Docker or Railway behavior | `Dockerfile`, `railway.toml`, `docs/deployment.md` | `README.md`, `README.ja.md` |

## Configuration And Runtime

Source of truth for runtime configuration is `src/omnivec/settings.py`.

Important variables:

- `OMNIVEC_DATA_DIR`: base directory for persisted jobs and shared caches.
- `OMNIVEC_API_KEY`: optional API key required by `/v1/*` when set.
- `MODEL`: CrewAI model string used for report generation.
- `OMNIVEC_TEXVEC_BIN` and `OMNIVEC_PICVEC_BIN`: CLI binary paths.
- `OMNIVEC_MAX_CONCURRENT_JOBS`: background job concurrency limit.
- `OMNIVEC_MAX_NEIGHBORS`: reciprocal-neighbor search depth.
- `OMNIVEC_JOB_TTL_HOURS`: retention period for finished job artifacts.
- `OPENAI_API_KEY`: required for real CrewAI report generation.

Runtime storage layout:

```text
OMNIVEC_DATA_DIR/
  jobs/
    <job_id>/
      upload.zip
      extracted/
      status.json
      analysis.json
      report.md
  cache/
    texvec/
    picvec-home/
```

Useful details:

- `JobService.prepare()` marks interrupted queued/running jobs as failed on startup and cleans expired finished jobs.
- `make serve` warms the shared runner caches before starting the API, so first startup can take longer.
- Real `texvec` and `picvec` runs may download ONNX Runtime and model assets into the shared cache.

## Working Rules

- Prefer small, direct changes that match the current architecture.
- Prefer the standard library and existing dependencies before adding new ones.
- Keep versioned API behavior stable unless the change is intentionally breaking or expanding v1.
- When changing schemas, think through both HTTP compatibility and existing on-disk job artifacts.
- When changing env vars or defaults, update `src/omnivec/settings.py`, `.env.example`, `docs/operations.md`, `README.md`, `README.ja.md`, and `tests/test_settings.py` together.
- When changing report payload shape or curation-goal behavior, update `tests/test_reporting.py`, `tests/test_api.py`, and any affected scripts or examples.
- When changing the sample workflow or command surface, update `Makefile`, `scripts/run_sample_workflow.py`, `tests/test_sample_workflow.py`, and the README examples together.
- Keep docs aligned for user-visible API, deployment, storage, or workflow changes. The English and Japanese READMEs should stay reasonably in sync.
- Avoid editing runtime or generated directories unless the task explicitly calls for it: `.omnivec-data/`, `sample-assets.zip`, and `__pycache__/`.

## Build, Test, And Smoke Commands

Preferred local workflow:

```sh
make sync
make check
make serve
make smoke-all
```

Other useful commands:

```sh
make format
make lint
make typecheck
make test
make sample-zip
make create-job CURATION_GOAL=dedupe
make docker-build
uv run python -c "from omnivec.api import create_app; print(create_app().title)"
```

Focused verification:

```sh
uv run pytest tests/test_api.py
uv run pytest tests/test_jobs.py
uv run pytest tests/test_reporting.py
uv run pytest tests/test_settings.py
```

CI currently runs `uv run pytest`. Local `make check` is stronger because it adds Ruff and Pyright.

## Testing Guidance

- Keep the default suite deterministic and offline.
- Do not make normal unit tests depend on OpenAI, ONNX Runtime downloads, model downloads, or network access.
- Prefer the fake runners and fake report generator patterns from `tests/conftest.py`.
- Use temp directories for filesystem-heavy tests instead of writing into a real persistent data directory.
- Keep smoke tests separate from the default test suite.
- If you touch `texvec` or `picvec` integration, update docs and test coverage together.

## Documentation Expectations

- Update `README.md` and `README.ja.md` for user-visible endpoint, environment, deployment, storage, or workflow changes.
- Update `docs/operations.md` for command, runtime, or configuration changes.
- Update `docs/deployment.md` for Docker, Railway, volume, or credential changes.
- Keep curl examples, `make` examples, and env var names aligned with the actual FastAPI behavior.

## Safety Notes

- Runtime data persists on disk until TTL cleanup removes it.
- `status.json` and `analysis.json` are part of the product behavior, not just test fixtures.
- If `OMNIVEC_API_KEY` is unset, any reachable client can submit `/v1/*` requests.
- Manual smoke tests that generate real reports require working `texvec` and `picvec` binaries plus `OPENAI_API_KEY`.
