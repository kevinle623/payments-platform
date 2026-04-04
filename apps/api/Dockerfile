FROM python:3.13-slim

WORKDIR /app

# Install Poetry
RUN pip install --no-cache-dir poetry==2.1.1

# Copy dependency files first for layer caching
COPY pyproject.toml poetry.lock ./

# Install production dependencies only -- no virtualenv inside the container
RUN poetry config virtualenvs.create false \
    && poetry install --only main --no-root --no-interaction --no-ansi

# Copy application source
COPY . .

# Default command -- overridden per service in docker-compose.yml
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
