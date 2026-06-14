# syntax=docker/dockerfile:1
# H5: Images pinned to amd64 digests. To re-pin:
#   podman manifest inspect docker.io/library/python:3.14-slim-bookworm
#   (pick the linux/amd64 digest from the manifests list)

FROM python:3.14-slim-bookworm@sha256:5ce3eb28c51514272af9451a78ad1ccf87b68bc45174e8c353c82d67103c223a AS builder

WORKDIR /build

RUN apt-get update \
	&& apt-get install -y --no-install-recommends gcc \
	&& rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md ./
COPY src ./src

RUN pip wheel --no-cache-dir --wheel-dir /wheels .


FROM python:3.14-slim-bookworm@sha256:5ce3eb28c51514272af9451a78ad1ccf87b68bc45174e8c353c82d67103c223a AS runtime

RUN apt-get update \
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
COPY scripts/container/internal/entrypoint.sh ./scripts/container/internal/entrypoint.sh

RUN chmod +x scripts/container/internal/entrypoint.sh \
	&& chown -R app:app /app

USER app

ENV PYTHONUNBUFFERED=1 \
	PYTHONDONTWRITEBYTECODE=1 \
	PYTHONPATH=/app/src

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
	CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

ENTRYPOINT ["scripts/container/internal/entrypoint.sh"]
CMD ["fastapi", "run", "src/todos_app/main.py", "--host", "0.0.0.0", "--port", "8000"]
