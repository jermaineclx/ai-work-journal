FROM python:3.12-slim AS base

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY main.py .

RUN mkdir -p data

EXPOSE 8000

# Shell form so ${PORT} expands — Railway (and most PaaS hosts) inject their
# own PORT at runtime; it won't always be 8000.
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}
