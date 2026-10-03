# whatsapp-sender

Sends the WhatsApp messages of campaigns, one at a time, through
[WAHA](https://waha.devlike.pro/), a self-hosted WhatsApp Web gateway.

It holds no state. Every message lives in the backend's `outbound_messages`
table, and so does the pacing. This worker asks for the next message, sends it
and reports back. Killing it at any moment loses nothing: a message claimed and
never reported is handed out again once its lease ends.

## Modules

| File | Does |
|---|---|
| `src/main.py` | entry point, SIGTERM handling |
| `src/worker.py` | the loop: session check, claim, send, report |
| `src/backend.py` | `POST /outbox/whatsapp/claim`, `/outbox/messages/{id}/result`, `/outbox/whatsapp/health` |
| `src/gateway.py` | `WahaGateway`: session, QR code, number check, typing, send |
| `src/config.py` | settings, read from `.env` |

## Flow

```
            +-------------- worker loop --------------+
            |                                         |
   WAHA session ready? --no--> health: disconnected + QR code
            | yes
   POST /outbox/whatsapp/claim
            |
   message? --no--> wait retry_after_seconds (at most MAX_WAIT_SECONDS)
            | yes
   check-exists -> startTyping -> wait -> stopTyping -> sendText
            |
   POST /outbox/messages/{id}/result   sent | failed | retry | release
```

## Outcomes

| Gateway says | Outcome | What the backend does |
|---|---|---|
| sent | `sent` | records it and sets the gap, or the chunk pause |
| number has no WhatsApp, 4xx | `failed` | final, with the reason |
| timeout, 5xx, WAHA down | `retry` | back to the queue with backoff, at most 3 attempts |
| logged out, bad API key | `release` | back to the queue untouched; channel shown as disconnected |

## Connecting the number

1. `docker compose up -d waha whatsapp-sender`
2. Open **Campanhas** in the app. The WhatsApp card shows the QR code.
3. On the phone: WhatsApp, Linked devices, Link a device.

The session is kept in the `waha-sessions` volume, so this is done once.

Use a number dedicated to prospecting. Automating WhatsApp Web goes against
WhatsApp's terms, and the pacing lowers the chance of a ban but does not remove
it.

## Tests

```
pytest
```
