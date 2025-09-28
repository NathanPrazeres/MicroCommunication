# Multi-stage build for Python with Poetry
FROM python:3.11-slim as builder

# Install system dependencies needed for building
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
ENV POETRY_HOME="/opt/poetry" \
    POETRY_CACHE_DIR=/opt/poetry-cache \
    POETRY_VENV_IN_PROJECT=1 \
    POETRY_NO_INTERACTION=1

RUN pip install poetry

WORKDIR /app

# Copy Poetry configuration files
COPY pyproject.toml poetry.lock* ./

# Configure Poetry and install dependencies
RUN poetry config virtualenvs.create true \
    && poetry config virtualenvs.in-project true \
    && poetry install --only=main --no-root

# Production stage
FROM python:3.11-slim as runtime

# Create non-root user for security
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Install only runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

WORKDIR /app

# Copy virtual environment from builder stage
COPY --from=builder --chown=appuser:appuser /app/.venv /app/.venv

# Copy application code
COPY --chown=appuser:appuser src/ ./src/
COPY --chown=appuser:appuser pyproject.toml ./

# Make sure we use venv
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONPATH="/app/src:$PYTHONPATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 5000

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
