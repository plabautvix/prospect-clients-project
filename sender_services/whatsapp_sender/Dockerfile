FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir \
    "requests>=2.32.5,<3.0.0" \
    "python-dotenv>=1.0.0,<2.0.0" \
    "opentelemetry-sdk==1.45.1" \
    "opentelemetry-exporter-otlp-proto-http==1.45.1" \
    "opentelemetry-instrumentation-requests==0.66b1" \
    "opentelemetry-instrumentation-logging==0.66b1"

COPY src/ ./src/
WORKDIR /app/src

ENV PYTHONUNBUFFERED=1

# exec form: Python is PID 1 and receives docker stop's SIGTERM, so it can
# finish and report the message in hand instead of being killed mid-send.
CMD ["python", "main.py"]
