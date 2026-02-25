FROM python:3.13-slim-bookworm

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN python -m pip install --no-cache-dir -r requirements.txt && \
    python -m pip install --no-cache-dir gunicorn

COPY ./ /app

RUN useradd -r -s /bin/false appuser
USER appuser

CMD ["python3", "-m", "gunicorn", "-b", "0.0.0.0:8000", "main:app"]
