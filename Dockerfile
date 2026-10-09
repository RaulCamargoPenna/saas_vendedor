FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /app/staticfiles && chown -R 10001:10001 /app/staticfiles
USER 10001:10001

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=8s --start-period=30s --retries=3 \
    CMD ["python", "manage.py", "publish_ready_event"]

CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000"]