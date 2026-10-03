import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[3] / ".env")

WHATSAPP = "whatsapp"
INSTAGRAM = "instagram"
CHANNELS = (WHATSAPP, INSTAGRAM)


@dataclass(frozen=True)
class Pacing:
    """How fast one sender account may send.

    The limits belong to the account, not to a campaign: the platforms judge a
    number or a profile by how much it sends in total.
    """

    min_gap_seconds: int
    max_gap_seconds: int
    chunk_size: int
    chunk_pause_min_seconds: int
    chunk_pause_max_seconds: int
    daily_cap: int
    window_start_hour: int
    window_end_hour: int
    # Brazil has had no daylight saving since 2019, so a fixed offset is exact
    # and avoids depending on the system timezone database.
    utc_offset_hours: int
    block_pause_hours: int


def _env_int(name: str, default: int) -> int:
    return int(os.getenv(name, str(default)))


def _pacing(prefix: str, **defaults: int) -> Pacing:
    return Pacing(
        min_gap_seconds=_env_int(f"{prefix}_MIN_GAP_SECONDS", defaults["min_gap"]),
        max_gap_seconds=_env_int(f"{prefix}_MAX_GAP_SECONDS", defaults["max_gap"]),
        chunk_size=_env_int(f"{prefix}_CHUNK_SIZE", defaults["chunk_size"]),
        chunk_pause_min_seconds=_env_int(
            f"{prefix}_CHUNK_PAUSE_MIN_SECONDS", defaults["chunk_pause_min"]
        ),
        chunk_pause_max_seconds=_env_int(
            f"{prefix}_CHUNK_PAUSE_MAX_SECONDS", defaults["chunk_pause_max"]
        ),
        daily_cap=_env_int(f"{prefix}_DAILY_CAP", defaults["daily_cap"]),
        window_start_hour=_env_int("SEND_WINDOW_START_HOUR", 9),
        window_end_hour=_env_int("SEND_WINDOW_END_HOUR", 19),
        utc_offset_hours=_env_int("SEND_UTC_OFFSET_HOURS", -3),
        block_pause_hours=_env_int(f"{prefix}_BLOCK_PAUSE_HOURS", 24),
    )


# Conservative starting points. Raise them only once an account has been
# sending for a while without trouble.
PACING: dict[str, Pacing] = {
    WHATSAPP: _pacing(
        "WHATSAPP",
        min_gap=30,
        max_gap=90,
        chunk_size=15,
        chunk_pause_min=15 * 60,
        chunk_pause_max=30 * 60,
        daily_cap=150,
    ),
    INSTAGRAM: _pacing(
        "INSTAGRAM",
        min_gap=2 * 60,
        max_gap=5 * 60,
        chunk_size=5,
        chunk_pause_min=45 * 60,
        chunk_pause_max=90 * 60,
        daily_cap=30,
    ),
}

# A claimed message goes back to the queue if its worker does not report
# within this time, which is what makes a crash mid-send recoverable.
LEASE_SECONDS = _env_int("SEND_LEASE_SECONDS", 300)
MAX_ATTEMPTS = _env_int("SEND_MAX_ATTEMPTS", 3)
RETRY_BASE_SECONDS = _env_int("SEND_RETRY_BASE_SECONDS", 300)

# How long a worker waits before asking again when there is nothing to send.
IDLE_POLL_SECONDS = _env_int("SEND_IDLE_POLL_SECONDS", 15)

# A worker that has not called in for this long is shown as offline.
WORKER_STALE_SECONDS = _env_int("SEND_WORKER_STALE_SECONDS", 120)
