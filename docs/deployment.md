# Deployment

## Deployed Environment

Set these values explicitly in deployed environments:

| Variable | Guidance |
|----------|----------|
| `MODEL` | Set the CrewAI model string explicitly instead of relying on the default |
| `OPENAI_API_KEY` | Required for report generation |
| `OMNIVEC_API_KEY` | Set this for any deployed service that should not be publicly usable |

The Docker image defaults `OMNIVEC_DATA_DIR` to `/data`. Attach your persistent volume there unless your platform requires a different mount path.

If `OMNIVEC_API_KEY` is unset, any client that can reach the service can submit `/v1/*` requests.

## Image Build

```sh
make docker-build
```

The Docker image is built from the repo Dockerfile, which:

- builds pinned `picvec` and `texvec` binaries in a Go stage
- currently pins `texvec` to `v1.1.0`
- installs Python dependencies with `uv`
- runs omnivec with Uvicorn

## Railway

This repo includes `railway.toml` and a Dockerfile-based deployment path.

Recommended Railway setup:

1. Create a persistent volume mounted at `/data`.
2. Set `MODEL`.
3. Set `OPENAI_API_KEY`.
4. Set `OMNIVEC_API_KEY`.

On first real run, `texvec` and `picvec` will download ONNX Runtime and their default models into the shared cache under the mounted volume.
