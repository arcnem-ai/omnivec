ifneq (,$(wildcard .env))
include .env
export
endif

HOST ?= http://127.0.0.1:8000
API_KEY ?= $(if $(strip $(OMNIVEC_API_KEY)),$(strip $(OMNIVEC_API_KEY)),dev-secret)
SAMPLE_ZIP ?= sample-assets.zip
JOB_ID ?=
CURATION_GOAL ?=
VENV_PYTHON ?= .venv/bin/python
VENV_PYTEST ?= .venv/bin/pytest
VENV_OMNIVEC ?= .venv/bin/omnivec
CURL_API_KEY := $(strip $(API_KEY))
CURL_AUTH_HEADER = $(if $(CURL_API_KEY),-H "X-API-Key: $(CURL_API_KEY)",)
CURL_CURATION_GOAL = $(if $(strip $(CURATION_GOAL)),-F "curation_goal=$(CURATION_GOAL)",)
SMOKE_CURATION_GOAL = $(if $(strip $(CURATION_GOAL)),--curation-goal $(CURATION_GOAL),)

.PHONY: help sync format lint typecheck check test serve warm-cache sample-zip health create-job job-status job-report smoke-all docker-build check-venv

help:
	@printf "%s\n" \
	"Omnivec commands:" \
	"  make sync         Install or update Python dependencies" \
	"  make format       Format Python files with Ruff" \
	"  make lint         Run Ruff lint checks" \
	"  make typecheck    Run Pyright" \
	"  make check        Run lint, typecheck, and tests" \
	"  make test         Run the pytest suite" \
	"  make serve        Warm shared caches, then start the local API server" \
	"  make warm-cache   Pre-initialize shared texvec/picvec runtime and model caches" \
	"  make sample-zip   Build sample-assets.zip from sample_assets/" \
	"  make health       Call the local health endpoint" \
	"  make create-job   Upload SAMPLE_ZIP to the API" \
	"                    Set CURATION_GOAL=discovery|dedupe|taxonomy_cleanup to bias the report" \
	"  make job-status JOB_ID=<id>   Fetch job status" \
	"  make job-report JOB_ID=<id>   Fetch final report JSON" \
	"  make smoke-all    Create sample ZIP, submit it, poll, and fetch the final report" \
	"  make docker-build Build the Docker image" \
	"" \
	"Values are loaded from .env when present." \
	"API_KEY defaults to OMNIVEC_API_KEY from .env, then falls back to dev-secret."

sync:
	uv sync

check-venv:
	@test -x "$(VENV_PYTHON)" || (echo "Run 'make sync' first." && exit 1)

format: check-venv
	uv run ruff format .

lint: check-venv
	uv run ruff check .

typecheck: check-venv
	uv run pyright

check: lint typecheck test

test: check-venv
	$(VENV_PYTEST)

serve: check-venv warm-cache
	$(VENV_OMNIVEC)

warm-cache: check-venv
	$(VENV_PYTHON) scripts/warm_cache.py

sample-zip:
	python3 scripts/create_sample_zip.py --source sample_assets --output $(SAMPLE_ZIP)

health:
	curl -fsS $(HOST)/healthz

create-job:
	@test -f "$(SAMPLE_ZIP)" || $(MAKE) sample-zip
	@printf "%s\n" "--- upload_request ---"
	@printf "POST %s/v1/jobs\n" "$(HOST)"
	@printf "multipart form:\n"
	@printf "  file=@%s\n" "$(SAMPLE_ZIP)"
	@if [ -n "$(strip $(CURATION_GOAL))" ]; then printf "  curation_goal=%s\n" "$(CURATION_GOAL)"; fi
	curl -fsS -X POST \
		$(CURL_AUTH_HEADER) \
		$(CURL_CURATION_GOAL) \
		-F "file=@$(SAMPLE_ZIP)" \
		$(HOST)/v1/jobs

job-status:
	@test -n "$(JOB_ID)" || (echo "Set JOB_ID=<id>" && exit 1)
	curl -fsS \
		$(CURL_AUTH_HEADER) \
		$(HOST)/v1/jobs/$(JOB_ID)

job-report:
	@test -n "$(JOB_ID)" || (echo "Set JOB_ID=<id>" && exit 1)
	curl -fsS \
		$(CURL_AUTH_HEADER) \
		$(HOST)/v1/jobs/$(JOB_ID)/report

smoke-all:
	@test -f "$(SAMPLE_ZIP)" || $(MAKE) sample-zip
	@$(MAKE) check-venv
	$(VENV_PYTHON) scripts/run_sample_workflow.py \
		--base-url $(HOST) \
		--api-key $(API_KEY) \
		$(SMOKE_CURATION_GOAL) \
		--zip-path $(SAMPLE_ZIP)

docker-build:
	docker build -t omnivec .
