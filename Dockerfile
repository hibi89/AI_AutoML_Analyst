FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY requirements-verified-py311.txt /app/requirements-verified-py311.txt
RUN python -m pip install --no-cache-dir -r requirements-verified-py311.txt

COPY . .

EXPOSE 8000

# Uvicorn listens on the container network; docker-compose restricts the host
# published port to 127.0.0.1. Do not publish this image with a wildcard host port.
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
