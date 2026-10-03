"""When a channel may send its next message.

Everything here is computed from what is stored: the time of the last sends,
the chunk counter and any pause. Nothing lives in a worker's memory, so a
restart cannot reset the limits.

All datetimes are naive UTC, like the rest of the database.
"""

import random
from datetime import datetime, timedelta, timezone

from prospect_clients.src.configurations.messaging import Pacing


def utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def local_day_start(now: datetime, pacing: Pacing) -> datetime:
    """Midnight of the sender's local day, expressed in UTC."""
    offset = timedelta(hours=pacing.utc_offset_hours)
    local = now + offset
    return local.replace(hour=0, minute=0, second=0, microsecond=0) - offset


def blocked_until(
    now: datetime,
    pacing: Pacing,
    next_allowed_at: datetime | None,
    paused_until: datetime | None,
    sent_today: int,
) -> datetime | None:
    """The earliest moment a send could be allowed, or None if it is now.

    Each rule that is violated now gives its own waiting point, and the latest
    one wins. Rules can chain (waiting for the gap may land outside the
    window), but the worker asks again at the returned time, and that call
    evaluates them all once more.
    """
    waits: list[datetime] = []

    if paused_until and paused_until > now:
        waits.append(paused_until)
    if next_allowed_at and next_allowed_at > now:
        waits.append(next_allowed_at)

    day_start = local_day_start(now, pacing)
    window_opens = day_start + timedelta(hours=pacing.window_start_hour)
    window_closes = day_start + timedelta(hours=pacing.window_end_hour)
    tomorrow_opens = window_opens + timedelta(days=1)

    if now < window_opens:
        waits.append(window_opens)
    elif now >= window_closes:
        waits.append(tomorrow_opens)

    if sent_today >= pacing.daily_cap:
        waits.append(tomorrow_opens)

    return max(waits) if waits else None


def after_send(
    now: datetime,
    pacing: Pacing,
    sent_in_chunk: int,
    rng: random.Random | None = None,
) -> tuple[datetime, int]:
    """Next allowed time and chunk counter once a message went out.

    A random gap between messages, and a long pause after every full chunk.
    """
    rng = rng or random
    count = sent_in_chunk + 1
    if count >= pacing.chunk_size:
        pause = rng.uniform(pacing.chunk_pause_min_seconds, pacing.chunk_pause_max_seconds)
        return now + timedelta(seconds=pause), 0

    gap = rng.uniform(pacing.min_gap_seconds, pacing.max_gap_seconds)
    return now + timedelta(seconds=gap), count
