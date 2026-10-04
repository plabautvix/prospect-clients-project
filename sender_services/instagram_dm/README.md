# instagram-dm

Sends the Instagram messages of campaigns as direct messages, one at a time,
from a dedicated account logged in on a real Chrome driven by
[nodriver](https://github.com/ultrafunkamsterdam/nodriver).

Instagram's official API only lets a business answer people who wrote first,
so reaching a lead means doing what a person does: open the profile, press
Message, type, press Enter.

Like the WhatsApp sender it holds no state. Messages and pacing live in the
backend; this worker asks for the next message, sends it and reports back.

## Modules

| File | Does |
|---|---|
| `src/main.py` | entry point, SIGTERM handling |
| `src/worker.py` | the loop: session, claim, send, report; acts on requests from the app |
| `src/backend.py` | `/outbox/instagram/claim`, `/outbox/messages/{id}/result`, `/outbox/instagram/health` |
| `src/instagram.py` | `InstagramDM`: Chrome, login, verification code, sending |
| `src/pages.py` | which screen a page is, from its URL and visible text |
| `src/config.py` | settings, read from `.env` |
| `scripts/probe.py` | log in and send one DM by hand, watching the browser |

## Logging in

1. Put the account in the `.env` next to `docker-compose.yml`:
   ```
   INSTAGRAM_USERNAME=conta.dedicada
   INSTAGRAM_PASSWORD=...
   ```
2. `docker compose up -d instagram-dm`
3. The worker logs in by itself. If Instagram sends a verification code by
   e-mail or SMS, the Instagram card in **Campanhas** shows a field for it.
4. If Instagram asks to confirm in the app ("Was this you?"), confirm it on the
   phone and press **Entrar novamente**.

The login lives in the `instagram-dm-profile` volume, so this is done once.

The worker never retries a login by itself. A refused password or a pending
code waits for the user: repeated logins are what gets an account locked.

## Outcomes

| What happened | Outcome | What the backend does |
|---|---|---|
| sent | `sent` | records it and sets the gap, or the chunk pause |
| profile not found, no Message button | `failed` | final, with the reason |
| page did not load, text stayed in the box | `retry` | back to the queue with backoff, at most 3 attempts |
| logged out, code needed | `release` | back to the queue untouched; card shows the problem |
| "Try again later" | `release` + `blocked` | channel paused for 24h (`INSTAGRAM_BLOCK_PAUSE_HOURS`) |

## When it breaks

Instagram changes its pages. The selectors live at the top of
`src/instagram.py` and the screen markers in `src/pages.py`. Run
`scripts/probe.py` on a machine with a display to watch the flow.

Use an account dedicated to prospecting, already used by hand for a while.
Automating Instagram goes against its terms; the pacing lowers the chance of a
restriction but does not remove it.

## Tests

```
pytest
```
