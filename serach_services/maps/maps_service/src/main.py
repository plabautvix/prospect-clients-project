import logging

import telemetry
from messaging.mqtt_client import run_mqtt

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

logger = logging.getLogger(__name__)


def main():
    telemetry.setup()
    logger.info("Maps service starting...")
    run_mqtt()


if __name__ == "__main__":
    main()
