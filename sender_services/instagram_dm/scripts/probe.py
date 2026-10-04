"""Log in and, optionally, send one DM by hand, watching the browser.

For checking the flow against Instagram as it is today, outside the queue and
the pacing. Instagram changes its pages; when sending starts failing, this is
where to see why.

    python scripts/probe.py                      # log in only
    python scripts/probe.py seu.perfil "Oi!"     # log in and send one message

Reads INSTAGRAM_USERNAME, INSTAGRAM_PASSWORD and CHROME_PROFILE_DIR from .env.
Send only to a profile you own.
"""

import asyncio
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import config  # noqa: E402
from instagram import InstagramDM  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")


async def main(handle: str | None, text: str | None) -> None:
    gateway = InstagramDM(
        username=config.INSTAGRAM_USERNAME,
        password=config.INSTAGRAM_PASSWORD,
        profile_dir=config.CHROME_PROFILE_DIR,
        headless=False,
    )
    try:
        state = await gateway.session()
        while state.needs_code:
            code = input(f"{state.detail}\nCódigo: ").strip()
            state = await gateway.submit_code(code)
        print("Sessão:", "pronta" if state.ready else state.detail)

        if state.ready and handle:
            await gateway.send_text(handle, text or "Oi!")
            print(f"Mensagem enviada para @{handle}.")

        input("Enter para fechar o navegador. ")
    finally:
        await gateway.close()


if __name__ == "__main__":
    args = sys.argv[1:]
    asyncio.run(main(args[0] if args else None, args[1] if len(args) > 1 else None))
