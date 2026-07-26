# Description: Reproducible runtime, test image, and GitHub container-action image.
FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
WORKDIR /opt/agentscope
COPY pyproject.toml README.md LICENSE ./
COPY src ./src
RUN python -m pip install --no-cache-dir .
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh
ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["--help"]

FROM base AS test
COPY tests ./tests
RUN python -m pip install --no-cache-dir ".[dev]"
RUN pytest && ruff check .
ENTRYPOINT ["pytest"]
CMD []

FROM base AS runtime
