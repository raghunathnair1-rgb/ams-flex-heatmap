# Sandboxed runtime for the FastAPI agent backend.
# Non-root user, minimal base, no shell tools beyond what's needed.
FROM python:3.12-slim AS base

RUN addgroup --system app && adduser --system --ingroup app --home /app app

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY api ./api

USER app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

EXPOSE 8000

CMD ["uvicorn", "api.index:app", "--host", "0.0.0.0", "--port", "8000"]
