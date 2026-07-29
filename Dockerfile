FROM python:3.12-slim AS runtime

ARG UV_VERSION=0.11.32
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PATH="/app/.venv/bin:$PATH"

RUN python -m pip install --no-cache-dir "uv==${UV_VERSION}" \
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
