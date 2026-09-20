# instagram-service

Finds Instagram profiles through the Google search index, using a real Chrome
instance driven by [nodriver](https://github.com/ultrafunkamsterdam/nodriver).
No Instagram account is used and no request goes to Instagram.

Full plan: [`../SPEC.md`](../SPEC.md). This code is the MVP slice of it.

## Modules

| File | Does |
|---|---|
| `src/main.py` | MQTT listener, entry point |
| `src/operations.py` | one thread per operation, stop event, maps profiles to leads |
| `src/backend.py` | `POST /leads/` and `PATCH /operations/{id}/status` |
| `src/search.py` | `GoogleSearch`: start, search, find_profiles, stop |
| `src/serp.py` | results page HTML to `SearchResult`, handle extraction, block detection |
| `src/config.py` | settings, read from `.env` |
| `scripts/probe.py` | run one query by hand and print what came back |

## Flow

```
backend  --publish prospect/instagram-->  main.py
                                            |
                                     Operations.start
                                            |
                                   thread + asyncio loop
                                            |
                                    GoogleSearch.find_profiles
                                            |
                          POST /leads/  +  PATCH /operations/{id}/status
```

Profiles are stored as ordinary leads, no schema change: `nome` gets `@handle`
(unique on Instagram, and `leads.nome` is the upsert key), `site` gets the
profile URL, and `categoria` gets the search text, which the frontend already
exposes as a filter.

The recency probe, the dork battery and the candidate table are still ahead. See
`../SPEC.md`.

## Setup (Windows)

```powershell
cd serach_services\instagram\instagram_service
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install nodriver lxml python-dotenv pytest
copy .env.example .env
```

Set `CHROME_PROFILE_DIR` in `.env` to a folder of your own. The first run shows
the cookie-consent dialog: accept it by hand once, and the persisted profile
remembers it.

## Running

The service, listening on MQTT:

```powershell
cd src
python main.py
```

One query by hand, without MQTT or the backend:

```powershell
python scripts\probe.py 'site:instagram.com "veterinaria" Campinas'
python scripts\probe.py 'site:instagram.com "veterinaria" Campinas' --pages 5
python scripts\probe.py '...' --dump      # writes dumps/last.html
```

Probe exit codes: `0` found profiles, `1` found none, `2` blocked by Google.

## Testing

```powershell
pytest
```

The `serp.py` tests never open a browser and do not need nodriver. The
`operations.py` tests skip themselves when nodriver is missing.

`tests/fixtures/serp.html` is **synthetic**. It matches the structure of a
results page but is not HTML captured from Google. Replace it with a real
capture from `--dump` when you can, so the test starts guarding the real layout.

## Two decisions worth knowing

**The parser is structural, never by CSS class.** Google's class names are
obfuscated and rotate. What is stable: the `h3` sits inside the result anchor and
the snippet sits outside it, in a sibling. So the parser climbs from the `h3` to
the anchor, then climbs a bit further looking for text that is not part of the
anchor. It stops if the container holds more than one `h3`, which would mean it
reached a neighbouring result.

**A block page and an empty page look identical without `is_blocked`.** Both give
zero results and no error, which reads as a broken parser. The check is four
markers and it saves a lot of time.
