FROM python:3.12-slim

# Chrome runs headful under a virtual display: headless mode is easier to detect.
RUN apt-get update && apt-get install -y --no-install-recommends \
    chromium xvfb ca-certificates fonts-liberation \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN pip install --no-cache-dir \
    "nodriver>=0.38" \
    "lxml>=5.3.0" \
    "paho-mqtt>=2.1.0,<3.0.0" \
    "requests>=2.32.5,<3.0.0" \
    "python-dotenv>=1.0.0,<2.0.0"

COPY src/ ./src/
WORKDIR /app/src

CMD ["xvfb-run", "-a", "--server-args=-screen 0 1920x1080x24", "python", "main.py"]
