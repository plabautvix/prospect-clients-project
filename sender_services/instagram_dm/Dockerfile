FROM python:3.12-slim

# Chrome runs headful under a virtual display: headless mode is easier to detect.
# The retries are here because chromium is a large download and a dropped
# connection mid-fetch fails the whole build.
RUN printf 'Acquire::Retries "8";\nAcquire::http::Timeout "120";\n' \
    > /etc/apt/apt.conf.d/99resilient \
    && apt-get update && apt-get install -y --no-install-recommends \
    chromium xvfb ca-certificates fonts-liberation \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Pinned to the version the search service runs: the DM flow was written
# against its API (Tab.mouse_click, evaluate return_by_value, CookieJar).
RUN pip install --no-cache-dir \
    "nodriver==0.50.3" \
    "requests>=2.32.5,<3.0.0" \
    "python-dotenv>=1.0.0,<2.0.0" \
    "opentelemetry-sdk==1.45.1" \
    "opentelemetry-exporter-otlp-proto-http==1.45.1" \
    "opentelemetry-instrumentation-requests==0.66b1" \
    "opentelemetry-instrumentation-logging==0.66b1"

COPY src/ ./src/
WORKDIR /app/src

ENV DISPLAY=:99
ENV PYTHONUNBUFFERED=1

# Xvfb is started directly instead of through xvfb-run for two reasons: as PID 1
# xvfb-run swallows the command's stdout, and `exec python` here makes Python
# itself PID 1, so docker stop reaches it instead of timing out into SIGKILL.
#
# The lock file has to go first: docker restart keeps the container filesystem,
# so a stale /tmp/.X99-lock makes Xvfb exit and leaves Python running with no X
# server, which only shows up later as a browser failure.
#
# Python as PID 1 also matters for sending: on SIGTERM it finishes the message
# in hand and reports it, instead of dying mid-send.
CMD ["sh", "-c", "rm -f /tmp/.X99-lock; Xvfb :99 -screen 0 1920x1080x24 -nolisten tcp & exec python main.py"]
    