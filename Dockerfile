FROM golang:1.25.3-bookworm AS go-builder

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential ca-certificates git \
    && rm -rf /var/lib/apt/lists/*

ARG PICVEC_REF=37feab91433fe57660edd77495718ee2ef47ba62
ARG TEXVEC_REF=5683bc7786779b8fed995c38bd5a82e8392b66a2

RUN git clone https://github.com/arcnem-ai/picvec.git /src/picvec \
    && git -C /src/picvec checkout "${PICVEC_REF}" \
    && git clone https://github.com/arcnem-ai/texvec.git /src/texvec \
    && git -C /src/texvec checkout "${TEXVEC_REF}"

RUN cd /src/picvec && go build -o /out/picvec .

RUN cd /src/texvec && go build -o /out/texvec .

FROM python:3.13-slim AS python-builder

ENV UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1

RUN pip install --no-cache-dir uv==0.9.13

WORKDIR /app
COPY pyproject.toml uv.lock README.md ./
COPY src ./src
RUN uv sync --frozen

FROM python:3.13-slim AS app

ENV PATH="/app/.venv/bin:${PATH}" \
    OMNIVEC_DATA_DIR="/data" \
    PYTHONUNBUFFERED=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY --from=python-builder /app /app
COPY --from=go-builder /out/picvec /usr/local/bin/picvec
COPY --from=go-builder /out/texvec /usr/local/bin/texvec

EXPOSE 8000

CMD ["omnivec"]
