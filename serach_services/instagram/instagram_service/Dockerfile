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

RUN pip install --no-cache-dir \
    "nodriver>=0.38" \
    "lxml>=5.3.0" \
    "paho-mqtt>=2.1.0,<3.0.0" \
    "requests>=2.32.5,<3.0.0" \
    "python-dotenv>=1.0.0,<2.0.0"

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
CMD ["sh", "-c", "rm -f /tmp/.X99-lock; Xvfb :99 -screen 0 1920x1080x24 -nolisten tcp & exec python main.py"]
    