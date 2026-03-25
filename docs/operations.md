# Operations and Development

## Common Commands

If you prefer a clean command surface, use the included `Makefile`:

```sh
make help
make sync
make format
make lint
make typecheck
make check
make test
make serve
make sample-zip
make smoke-all
```

Useful local workflow:

1. `make sync`
2. `make check`
3. `make serve`
4. In another terminal, `make sample-zip`
5. Then `make create-job` or `make smoke-all`

`make serve` runs shared `texvec` and `picvec` cache initialization first, so the first startup can take longer while runtimes and models are prepared.

`make create-job`, `make job-status`, `make job-report`, and `make smoke-all` use `OMNIVEC_API_KEY` from `.env` by default, and fall back to `dev-secret` only when it is unset.

You can also set `CURATION_GOAL=discovery`, `dedupe`, or `taxonomy_cleanup` with `make create-job` or `make smoke-all`.

## Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `OMNIVEC_DATA_DIR` | Base directory for jobs and shared caches | `.omnivec-data` |
| `OMNIVEC_API_KEY` | Optional API key for `/v1/*` endpoints | unset |
| `MODEL` | CrewAI model string | `openai/gpt-4o-mini` |
| `OMNIVEC_TEXVEC_BIN` | `texvec` binary path | `texvec` |
| `OMNIVEC_PICVEC_BIN` | `picvec` binary path | `picvec` |
| `OMNIVEC_MAX_CONCURRENT_JOBS` | Number of jobs to run at once | `1` |
| `OMNIVEC_MAX_NEIGHBORS` | Reciprocal neighbor count for clustering | `3` |
| `OMNIVEC_JOB_TTL_HOURS` | TTL for finished job artifacts | `72` |
| `OPENAI_API_KEY` | Required for CrewAI report generation | unset |

## Runtime Storage

All runtime data lives under `OMNIVEC_DATA_DIR`:

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

The shared cache stores the expensive runtime and model assets. Each job keeps separate indexing state so uploads do not leak into each other.

## Development Notes

```sh
uv sync
uv run ruff format .
uv run ruff check .
uv run pyright
uv run pytest
uv run omnivec
```

The default test suite is offline and uses fake runners plus a fake report generator, so it does not require OpenAI credentials, model downloads, or network access.

For Docker and Railway deployment, see [Deployment](deployment.md).

See `CONTRIBUTING.md` for contribution workflow and `AGENTS.md` for repo-specific agent instructions.
