# Dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install Poetry
RUN pip install poetry

# Copy Poetry config files
COPY pyproject.toml poetry.lock /app/

# Install dependencies
RUN poetry install --no-dev

# Copy the rest of the application code
COPY . /app

# Run the FastAPI application using Uvicorn
CMD ["poetry", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]