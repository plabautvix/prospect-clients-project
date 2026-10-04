import logging
import signal

import config
from backend import BackendClient
from instagram import InstagramDM
from worker import Worker

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)


def main():
    worker = Worker(
        backend=BackendClient(),
        gateway=InstagramDM(
            username=config.INSTAGRAM_USERNAME,
            password=config.INSTAGRAM_PASSWORD,
            profile_dir=config.CHROME_PROFILE_DIR,
            headless=config.HEADLESS,
        ),
    )

    # docker stop sends SIGTERM. Finishing the message in hand and reporting
    # it is what avoids sending it twice after the restart.
    signal.signal(signal.SIGTERM, lambda *_: worker.stop())
    signal.signal(signal.SIGINT, lambda *_: worker.stop())

    worker.run_forever()


if __name__ == "__main__":
    main()
