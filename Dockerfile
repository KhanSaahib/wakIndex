# Description: Reproducible runtime, test image, and GitHub container-action image.
FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
WORKDIR /opt/wakindex
COPY pyproject.toml README.md LICENSE ./
COPY src ./src
RUN python -m pip install --no-cache-dir .
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh
ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["--help"]

FROM base AS test
COPY tests ./tests
COPY scripts ./scripts
COPY docs ./docs
COPY examples ./examples
COPY CHANGELOG.md CONTRIBUTING.md RELEASE.md ./
COPY .github/workflows/release.yml ./.github/workflows/release.yml
COPY .github/workflows/wakindex.yml ./.github/workflows/wakindex.yml
COPY .gitignore ./.gitignore
RUN python -m pip install --no-cache-dir ".[dev]"
RUN python -m pytest && python -m ruff check .
ENTRYPOINT ["python", "-m", "pytest"]
CMD []

FROM base AS runtime
