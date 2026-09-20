FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir poetry==2.1.1

COPY pyproject.toml poetry.lock ./
RUN poetry config virtualenvs.create false \
    && poetry install --no-root --no-interaction --no-ansi

COPY . .

EXPOSE 8000

# Migrations run as a separate step before the app, so the application itself
# never creates or alters tables.
CMD ["sh", "-c", "alembic upgrade head && uvicorn prospect_clients.src.main:app --host 0.0.0.0 --port 8000"]
