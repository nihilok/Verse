# syntax=docker/dockerfile:1.4

# Base stage: Install dependencies using uv
FROM ghcr.io/astral-sh/uv:latest AS deps

WORKDIR /app

# Copy requirements file
COPY requirements.txt .

# Install dependencies using uv into /app/.venv
RUN --mount=type=cache,target=/root/.cache/uv \
    uv venv /app/.venv && \
    uv pip sync requirements.txt

# Runner stage: Use Python 3.14 slim image
FROM python:3.14-slim AS runner

WORKDIR /app

# Install runtime system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from deps stage
COPY --from=deps /app/.venv /app/.venv

# Copy application code
COPY . .

# Set PATH to use the virtual environment
ENV PATH="/app/.venv/bin:$PATH"

# Expose port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
