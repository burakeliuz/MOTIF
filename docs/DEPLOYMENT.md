# Deployment

The hosted demo runs as one Python web service on Render, defined by the
Blueprint [`render.yaml`](../render.yaml). Python is pinned by
[`.python-version`](../.python-version); dependencies are in
[`requirements.txt`](../requirements.txt) (the Anthropic SDK for brief prose and
fpdf2 for the PDF brief). The server itself uses only the standard library.

## Steps

1. Sign in to Render with GitHub and create a new Blueprint from this repository
   (branch `main`).
2. Enter the secret values Render asks for (`sync: false` in the Blueprint):
   `QLOO_API_KEY`, `MOTIF_ACCESS_PASSWORD`, and optionally
   `MOTIF_ANTHROPIC_API_KEY`. No secret value is stored in the repository.
3. Deploy, then open `https://<service>.onrender.com/healthz` (returns
   `{"ok": true}` and calls no API) and the start page.

To change a variable later: open the service, **Environment**, edit the
variable, then **Save and deploy**. `render.yaml` sets `autoDeploy: false`, so
new commits are deployed manually.

## Environment variables (names only)

| Variable | Purpose | Default |
|---|---|---|
| `QLOO_API_KEY` | Qloo hackathon key (secret) | — |
| `MOTIF_ANTHROPIC_API_KEY` | Anthropic key for the brief's prose (secret, optional; `ANTHROPIC_API_KEY` is ignored) | — |
| `MOTIF_LLM_PROVIDER` | `anthropic` or `off` | `anthropic` when a key is set |
| `MOTIF_LLM_MODEL` | model for the prose; MOTIF never switches models on its own | `claude-sonnet-5-5` |
| `MOTIF_LLM_EFFORT`, `MOTIF_LLM_TIMEOUT_S` | prose call settings | `low`, `30` |
| `MOTIF_LLM_MAX_CALLS` | LLM calls per UTC day; the template writes the prose after that | `20` |
| `MOTIF_LLM_BUDGET_GUARD` | `auto`, `provider`, or `off` (see below) | `auto` |
| `MOTIF_QLOO_MAX_CALLS_PER_DAY` | daily Qloo request cap | `400` |
| `MOTIF_WEB_SESSIONS_PER_DAY` | daily research session cap | `120` |
| `MOTIF_WEB_SESSIONS_PER_IP_HOUR` | per-client hourly cap (best effort) | `8` |
| `MOTIF_DATA_DIR` | data directory (sessions, counters, LLM ledger) | `./data` |
| `MOTIF_ACCESS_PROTECTION` | optional access gate: `on` or `off` | `on` |
| `MOTIF_ACCESS_PASSWORD` | password for the access gate (secret) | — |
| `HOST`, `PORT` | bind address | `127.0.0.1:8000` |

The Blueprint sets lower caps than these code defaults; see `render.yaml`.

## Guards

- **Usage caps.** Daily counters (`data/web_usage.json`) and the LLM ledger
  (`data/llm_calls.jsonl`) are changed under a file lock, with the spend
  reserved before each call. If they cannot be read or written, no paid call is
  made (fail-closed). A reached cap is reported; nothing is replaced with sample
  data.
- **LLM budget guard.** `auto` calls the LLM on Render only when
  `MOTIF_DATA_DIR` is a persistent mount, because the counters would otherwise
  reset with the instance; otherwise the labelled template writes the prose.
  `provider` is for a deployment whose LLM spend is capped on the provider side;
  `off` makes no LLM calls. Off Render, the local disk counts as persistent.
- **Access gate.** With `MOTIF_ACCESS_PROTECTION=on`, every page and API except
  `/healthz` and the sign-in page needs `MOTIF_ACCESS_PASSWORD`, checked on the
  server (random session cookie: Secure, HttpOnly, SameSite=Strict, 12 hours;
  failed attempts are rate-limited per client and globally). Without a password
  nothing behind the gate opens. `off` opens the app.
- **Recorded mode** (`--recorded`) is refused on Render, and a live server shows
  no recorded-mode wording.

## Free instance

A free Render instance sleeps after 15 idle minutes; the first request after
that takes about a minute. Its filesystem is ephemeral, so web sessions, daily
counters, and the LLM ledger reset when it restarts, redeploys, or spins down
([Render: Deploy for Free](https://render.com/docs/free)). Within one running
instance the caps hold, including under concurrent requests.
