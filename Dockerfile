# syntax=docker/dockerfile:1

FROM python:3.14-slim-bookworm AS builder

WORKDIR /build

RUN apt-get update \
	&& apt-get install -y --no-install-recommends gcc \
	&& rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md ./
COPY src ./src

RUN pip wheel --no-cache-dir --wheel-dir /wheels .


FROM python:3.14-slim-bookworm AS runtime

RUN apt-get update \
	&& apt-get install -y --no-install-recommends curl \
	&& rm -rf /var/lib/apt/lists/* \
	&& groupadd --gid 1000 app \
	&& useradd --uid 1000 --gid app --create-home app

WORKDIR /app

COPY --from=builder /wheels /wheels
RUN pip install --no-cache-dir /wheels/*.whl \
	&& rm -rf /wheels

COPY alembic.ini ./
COPY alembic ./alembic
COPY src ./src
COPY scripts/container/entrypoint.sh ./scripts/container/entrypoint.sh

RUN chmod +x scripts/container/entrypoint.sh \
	&& chown -R app:app /app

USER app

ENV PYTHONUNBUFFERED=1 \
	PYTHONDONTWRITEBYTECODE=1 \
	PYTHONPATH=/app/src

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
	CMD curl -f http://localhost:8000/health || exit 1

ENTRYPOINT ["scripts/container/entrypoint.sh"]
CMD ["fastapi", "run", "src/todos_app/main.py", "--host", "0.0.0.0", "--port", "8000"]
