import logging
import signal

import config
import telemetry
from backend import BackendClient
from gateway import WahaGateway
from worker import Worker

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)


def main():
    telemetry.setup()

    worker = Worker(
        backend=BackendClient(),
        gateway=WahaGateway(
            base_url=config.WAHA_URL,
            api_key=config.WAHA_API_KEY,
            session=config.WAHA_SESSION,
            timeout=config.HTTP_TIMEOUT,
        ),
    )

    # docker stop sends SIGTERM. Finishing the message in hand and reporting
    # it is what avoids sending it twice after the restart.
    signal.signal(signal.SIGTERM, lambda *_: worker.stop())
    signal.signal(signal.SIGINT, lambda *_: worker.stop())

    worker.run_forever()


if __name__ == "__main__":
    main()
