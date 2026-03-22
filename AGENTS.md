# AGENTS.md

## Project Summary

`omnivec` is an API-first asset librarian built with FastAPI and CrewAI. It accepts ZIP uploads of documents and images, uses `texvec` and `picvec` for local similarity analysis, and returns a curated markdown report plus structured JSON results.

## Repository Map

- `src/omnivec/api.py`: FastAPI app and HTTP endpoints.
- `src/omnivec/jobs.py`: job lifecycle, async execution, and analysis orchestration.
- `src/omnivec/runners.py`: subprocess wrappers for `texvec` and `picvec`.
- `src/omnivec/reporting.py`: CrewAI-backed report generation.
- `src/omnivec/crew.py`: CrewAI crew definition and YAML-backed agent/task config.
- `src/omnivec/ingestion.py`: safe ZIP extraction, file classification, and duplicate grouping.
- `src/omnivec/clustering.py`: reciprocal-neighbor clustering logic.
- `src/omnivec/storage.py`: file-backed status, analysis, and report persistence.
- `sample_assets/`: checked-in documents and images for local demos.
- `tests/`: deterministic unit and API tests using fake runners and a fake report generator.

## Working Rules

- Prefer small, direct changes that match the current architecture.
- Keep retrieval deterministic outside CrewAI. Agents should write reports, not perform indexing.
- Keep HTTP handlers thin. Put behavior in `jobs.py`, `ingestion.py`, `storage.py`, or `runners.py`.
- Preserve the public API shape unless the change intentionally updates v1 behavior.
- Prefer the standard library and existing dependencies before adding new ones.
- Update both `README.md` and `README.ja.md` for user-visible API, deployment, or workflow changes.

## Build And Test

- Fast validation: `uv run pytest`
- Run the API locally: `uv run omnivec`
- Smoke-check app startup: `uv run python -c "from omnivec.api import create_app; print(create_app().title)"`
- Build the container: `docker build -t omnivec .`

## Testing Guidance

- Keep tests deterministic and offline by default.
- Do not make default unit tests depend on OpenAI, ONNX Runtime downloads, model downloads, or network access.
- Use fake `texvec` and `picvec` runners in tests unless the test is explicitly marked as a manual smoke test.
- If a feature needs filesystem-heavy coverage, use temp directories instead of writing into a real persistent data volume.

## Side Effects And Safety

- Runtime data lives under `OMNIVEC_DATA_DIR`.
- Real `texvec` and `picvec` executions may download ONNX Runtime and model assets into the shared cache.
- Job uploads, extracted assets, reports, and status files persist on disk until TTL cleanup removes them.
- If `OMNIVEC_API_KEY` is set, `/v1/*` endpoints require `X-API-Key`.
- Avoid adding tests that shell out to real upstream binaries unless they are explicitly opt-in smoke tests.

## Documentation Expectations

- Update `README.md` for any user-visible endpoint, environment variable, deployment, storage, or workflow change.
- Keep `README.ja.md` reasonably aligned with the English README.
- Keep curl examples and environment variables aligned with the actual FastAPI behavior.

## Useful Commands

```sh
uv sync
uv run pytest
uv run omnivec
uv run python -c "from omnivec.api import create_app; print(create_app().title)"
docker build -t omnivec .
```
