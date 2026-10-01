FROM python:3.12-slim@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f AS runtime

ARG UV_VERSION=0.11.32
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PATH="/app/.venv/bin:$PATH"

RUN apt-get update \
    && apt-get install --yes --no-install-recommends --only-upgrade \
        gzip \
        libpcre2-8-0 \
        libsqlite3-0 \
        libssl3t64 \
        openssl \
        openssl-provider-legacy \
        perl-base \
    && rm -rf /var/lib/apt/lists/* \
    && python -m pip install --no-cache-dir "uv==${UV_VERSION}" \
    && groupadd --gid 10001 tradeguard \
    && useradd --uid 10001 --gid tradeguard --no-create-home --shell /usr/sbin/nologin tradeguard

WORKDIR /app
COPY pyproject.toml uv.lock README.md LICENSE ./
COPY src ./src
RUN uv sync --frozen --no-dev \
    && chown -R tradeguard:tradeguard /app

USER tradeguard
EXPOSE 8000
CMD ["uvicorn", "tradeguard.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
