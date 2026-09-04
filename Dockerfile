# uv's own image: it ships uv alongside the matching Python, so there is no
# separate install step and the version is pinned with the base image.
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app

# Dependencies before source: this layer stays cached until pyproject.toml or
# uv.lock actually change, so editing code does not reinstall Django.
# --frozen fails rather than silently re-resolving if the lock is out of date.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project

COPY . .

EXPOSE 8000

# psycopg ships binary wheels, so no libpq-dev or compiler is needed here.
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
