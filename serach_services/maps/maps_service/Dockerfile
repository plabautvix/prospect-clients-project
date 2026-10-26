FROM python:3.12-slim

# Firefox and system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    firefox-esr \
    wget \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Geckodriver
RUN wget -q "https://github.com/mozilla/geckodriver/releases/download/v0.36.0/geckodriver-v0.36.0-linux64.tar.gz" \
    && tar -xzf geckodriver-v0.36.0-linux64.tar.gz \
    && mv geckodriver /usr/local/bin/ \
    && rm geckodriver-v0.36.0-linux64.tar.gz

WORKDIR /app

RUN pip install --no-cache-dir \
    "paho-mqtt>=2.1.0,<3.0.0" \
    "selenium>=4.38.0,<5.0.0" \
    "requests>=2.32.5,<3.0.0" \
    "python-dotenv>=1.0.0,<2.0.0" \
    "opentelemetry-sdk==1.45.1" \
    "opentelemetry-exporter-otlp-proto-http==1.45.1" \
    "opentelemetry-instrumentation-requests==0.66b1" \
    "opentelemetry-instrumentation-logging==0.66b1"

COPY src/ ./src/

WORKDIR /app/src

CMD ["python", "main.py"]
