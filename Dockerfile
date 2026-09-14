

FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN useradd --create-home app \
    && mkdir -p /home/app/.cache/huggingface \
    && chown -R app:app /home/app

# Heavy layer: ctranslate2/faster-whisper — cached unless pyproject.toml changes
COPY pyproject.toml ./
RUN pip install --no-cache-dir "faster-whisper>=1.0"

COPY . .
RUN pip install --no-cache-dir '.[whisper]' \
    && chown -R app:app /app

USER app
ENV HOME=/home/app
EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]