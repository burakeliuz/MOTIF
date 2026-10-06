# MOTIF

MOTIF translates a brand's cultural context, as returned by Qloo, into an
explainable olfactory direction for a perfumer. The pipeline is: Qloo
evidence → motif → sensory target → material suggestion → brief.

- **The deterministic engine** decides classification, sensory targets, and
  material choices. The same evidence and versions give the same result.
- **An optional LLM** (default `claude-sonnet-5-5`) only writes the brief's
  prose. The prose is validated against the engine result; if the call fails or
  the text fails validation, a labelled template is shown instead.
- **The output is a creative direction:** not a formula, not a dosage, and
  not a prediction that anyone will like the scent.

**Status (stage 5, 2026-10-06):**

- A web interface (`python3 -m motif.web`) runs the real research flow: brand
  input, entity choice, live research steps, result with six axes, motifs,
  clickable evidence, verified materials, and the brief.
- Seven of eight palette materials have properties verified against the
  supplier's own full page (palette-0.3). ISO E SUPER stays unverified: the
  supplier site blocked automated access (HTTP 403), so it is never used live.
- Lexicon-0.3 adds general context rules (technique nouns in film tags; "lush"
  only with a design context). These changes were made after the held-out check
  (T1), so Le Labo and Patagonia are no longer independent validation.
- Hosting is prepared for a free Render web service (`render.yaml`); see
  [Hosting](#hosting).
- Key documents:
  - [`MOTIF_BUILD_SPEC.md`](MOTIF_BUILD_SPEC.md) (rev 0.3)
  - [`reports/holdout_t1.md`](reports/holdout_t1.md) (held-out brands and the post-hoc lexicon-0.3 re-run)
  - [`reports/design_examples.md`](reports/design_examples.md)
  - [`reports/feasibility.md`](reports/feasibility.md)
  - [`docs/SUBMISSION_NOTES.md`](docs/SUBMISSION_NOTES.md)

## Web interface

```sh
pip install -r requirements.txt   # only the Anthropic SDK; without it the brief uses the template
python3 -m motif.web              # http://127.0.0.1:8000, live Qloo (needs QLOO_API_KEY)
MOTIF_LLM_PROVIDER=off python3 -m motif.web   # live Qloo, template prose, no LLM calls

# Local preview only: replay stored live runs from data/ (labelled RECORDED, sends nothing)
python3 -m motif.web --recorded data/raw/<RUN_ID> [data/motif_sessions/<SESSION_ID> ...]
```

The browser gets static files and a small JSON API; research runs on the
server. Keys stay in the server environment and never appear in a page or a
response. Guards against repeated calls:

- The same request (reference, choice, conflict answer, mode) within 30 minutes
  returns the existing session, so reload, back, and double clicks send nothing.
- Answering a question (choosing an entity, resolving a conflict) reuses the
  first session's Qloo cache, so the search is not repeated.
- Per-IP and per-day session caps, a daily Qloo attempt cap, and a daily LLM
  call cap. A reached cap is reported; nothing is replaced with sample data.

Recorded sessions are for local testing; recorded Qloo data is not published as
demo data. Web sessions are saved under `data/web_sessions/` (git-ignored).

## Engine quick start (Python 3.9+, standard library only)

```sh
git clone https://github.com/burakeliuz/MOTIF && cd MOTIF
python3 -m unittest            # offline; recorded-data tests skip when data/ is absent

# Live: needs the Qloo hackathon key in the environment (see below)
python3 -m motif_spike check                                  # must say READY
python3 -m motif run --reference "MUJI" --type brand          # 4 Qloo requests at most for a resolved brand
python3 -m motif run --reference "Le Labo" --choose <QLOO_ID>  # answer an entity question with a returned ID
python3 -m motif run --reference "MUJI" --allow-unverified-materials   # DESIGN PREVIEW of materials (labelled)
python3 -m motif llm-check                                    # one real API call: is the configured model available?

# Recorded: replays a stored live run from data/ and sends nothing
python3 -m motif run --reference "MUJI" --recorded <RUN_ID_OR_PATH>
python3 -m motif compare --reference "MUJI" --recorded <RUN_ID_OR_PATH>   # own description only vs plus relations
```

**Options:**

- `--type brand|movie|artist|any`
- `--include-artist`: music is off by default.
- `--resolve-conflict AXIS=POLE|open`
- `--max-requests N`: the session budget, counting every network attempt.
- `--json`: prints the brief JSON.

Each session is saved under `data/motif_sessions/<id>/` (git-ignored):
`session.json` (trace, requests, labels), `engine_result.json`, `brief.json`,
and the raw responses for live sessions.

**Exit codes:** 0 completed · 3 a question needs an answer · 4 stopped (access
error, budget, or a missing recording) · 2 usage error.

### Modes and labels

| Mode | Needs | Label shown |
|---|---|---|
| Live | Qloo key in the environment | `LIVE · Qloo https://hackathon.api.qloo.com` (web: "Live · Qloo API") |
| Recorded | A stored run under `data/` | `RECORDED · Qloo data from run …` (web: "Recorded preview"); never shown as live |
| Template prose | Nothing, or `MOTIF_LLM_PROVIDER=off` | `Brief (template)` / "Template prose" |
| LLM prose | `MOTIF_ANTHROPIC_API_KEY` and `pip install anthropic` | `Brief (llm)` / "LLM prose"; a failed call or invalid text falls back to the template with a note |
| Design preview | `--allow-unverified-materials` (CLI only) | `DESIGN PREVIEW: material properties are not verified …` |

### Environment variables (names only; never commit values)

```sh
QLOO_API_KEY=                   # hackathon key; in a Claude Code cloud session the proxy injects it instead
MOTIF_ANTHROPIC_API_KEY=        # Anthropic key read explicitly by MOTIF (ANTHROPIC_API_KEY is ignored)
MOTIF_LLM_PROVIDER=             # optional: "anthropic" (default when a key is set) or "off"
MOTIF_LLM_MODEL=                # optional, default claude-sonnet-5-5; MOTIF never switches models on its own
MOTIF_LLM_EFFORT=               # optional, default "low"
MOTIF_LLM_TIMEOUT_S=            # optional, default 30
MOTIF_LLM_MAX_CALLS=            # optional, real API calls per UTC day (default 20), logged in data/llm_calls.jsonl
MOTIF_QLOO_MAX_CALLS_PER_DAY=   # web only, default 400
MOTIF_WEB_SESSIONS_PER_DAY=     # web only, default 120
MOTIF_WEB_SESSIONS_PER_IP_HOUR= # web only, default 8 (best effort; the daily caps are the hard limit)
MOTIF_DATA_DIR=                 # optional data directory (default ./data)
HOST=, PORT=                    # web server bind address (default 127.0.0.1:8000)
```

The Qloo base URL is fixed in `config/manifest.json`, because hackathon keys
only work against `https://hackathon.api.qloo.com`. Design rules are versioned
in `config/` (`motif_lexicon.json`, `draft_rules.json`, `material_palette.json`,
`engine_params.json`).

## Hosting

The hosted demo is prepared for a **Render free web service** (no credit card
for the free instance type; it sleeps after 15 minutes without traffic and the
first request after that takes about a minute). The Blueprint is
[`render.yaml`](render.yaml); Python is pinned by [`.python-version`](.python-version).

1. Sign in to Render with GitHub and create a new Blueprint from this repository
   (branch `main`).
2. When asked, enter the secret values for `QLOO_API_KEY` and, optionally,
   `MOTIF_ANTHROPIC_API_KEY`. Keys from a Claude Code session are not carried over.
3. Deploy, then open `https://<service>.onrender.com/healthz` and the start page.

Limits on the free instance: sessions live in memory and are lost when the
service sleeps or restarts; the daily caps restart with the process.

---

# Qloo feasibility spike (stages 1–2)

The `motif_spike/` playground tested whether the Qloo data accessible to the
hackathon is descriptive and differentiated enough. It is kept as is, and the
engine reuses its transport, parsers, and request log. The project frame is
[`MOTIF_QLOO_FEASIBILITY.md`](MOTIF_QLOO_FEASIBILITY.md) (rev 0.2). Evidence
excerpt: [`reports/evidence_excerpt.md`](reports/evidence_excerpt.md).

## Requirements

- Python 3.9+ (standard library only; no install step). Tests pass on 3.9–3.13 under Linux; Windows is untested.
- Live runs use the built-in direct HTTPS client by default (no extra install).
  Only `--transport harness` needs Node.js ≥ 22.19.0 and
  `npm install --global @qloo/qloo-harness` (≥ 0.1.26).

## Quick start (offline, no credential)

```sh
python3 -m motif_spike run --mode synthetic    # invented fixtures, no network
python3 -m unittest                            # all checks (spike and engine)
python3 -m motif_spike plan --plan pilot       # commands a live pilot would send (nothing runs)
python3 -m motif_spike check                   # live readiness (presence only)
```

Synthetic output is marked `synthetic` everywhere, and its facts sheet carries
a "NOT QLOO DATA" banner. It checks the pipeline, not feasibility. Sample
output: [`docs/examples/facts_synthetic_example.md`](docs/examples/facts_synthetic_example.md).

## Live configuration

The key never goes into this folder, a prompt, or a chat.

| Setting | How | Secret? |
|---|---|---|
| Qloo credential | `qloo setup --qloo` (stored in the harness's private config), or `QLOO_API_KEY` in the environment of a server or cloud session | yes |
| `QLOO_HARNESS_BIN` | full path to `qloo` if it is not on `PATH` | no |
| Event base URL | hackathon keys only work against `https://hackathon.api.qloo.com`. MOTIF uses it on every live run from `config/manifest.json` (`harness_environment`). | no |
| Transport | `direct` (default): MOTIF's own HTTPS client, which keeps full response bodies. `harness`: the official `qloo` CLI (`--transport harness`). | no |

```sh
# Placeholders only; leave values empty in anything you commit
QLOO_API_KEY=
QLOO_HARNESS_BIN=
```

To use `qloo` directly outside MOTIF (for example `qloo setup --status`),
add the base URL to your shell profile as the organizers instructed:

```sh
export QLOO_BASE_URL=https://hackathon.api.qloo.com
export QLOO_TRUSTED_BASE_URL=https://hackathon.api.qloo.com
```

In a Claude Code cloud session (Pro/Max), store the key as an environment
**API credential** for host `hackathon.api.qloo.com` with header `X-Api-Key`
(no prefix). The agent proxy adds it to outgoing requests, so the key never
enters the session, and the host becomes reachable. The direct transport sends
no key header of its own, which is what lets the proxy add it. Optionally set
`QLOO_API_KEY=proxy-injected` as a non-secret placeholder.

Then:

```sh
python3 -m motif_spike check                          # must say READY
python3 -m motif_spike run --mode live --plan pilot   # 2 seeds x 3 domains, budget 20
# read data/normalized/<run_id>/facts.md, then:
python3 -m motif_spike run --mode live --plan full    # 5 seeds x 6 domains, budget 60
```

`--seeds a24,muji`, `--domains movie,brand`, `--max-requests N` and
`--no-reuse` narrow or adjust a run. Identical successful live requests from
earlier runs are reused, not re-sent. `renormalize --run latest-live` rebuilds
normalized output from saved raw files after a parser fix. `excerpt --run latest-live`
writes a small, committable evidence excerpt (`reports/evidence_excerpt.md`) with
literal values, request IDs, and JSON Pointers.

## What a run does

For each seed (A24, MUJI, Comme des Garçons, Nike, Ralph Lauren; see `config/manifest.json`):

1. `qloo api search` → resolve to exactly one returned entity, or report
   `unresolved` / `ambiguous` and stop for that seed.
2. `qloo api entity` → the seed's own properties and tags.
3. `qloo api insights` per domain → related entities with tags, properties, affinity, and explainability if returned.
4. `qloo exec entity_tags` → tag insights for the seed.

Each request records the command, the exact HTTP request (method, URL,
parameters; never the key), a status, its attempts, and a pointer to the saved
output. See [`docs/EVIDENCE_CONTRACT.md`](docs/EVIDENCE_CONTRACT.md).

## Rules the playground enforces

- Live and synthetic never mix. A failed live call stays failed: no fixture, endpoint, or credential fallback.
- A credential error stops the run. Retries are bounded (2), and the budget is enforced.
- Observations copy literal returned values with a JSON Pointer to the raw file. Absent fields stay absent.
- Seeds resolve only on an exact name match (case and accents folded). Ambiguity is reported, never guessed.
- Overlaps use returned IDs only. Scores are never averaged across requests or called "lift".
- The six sensory axes, 12 candidate motifs, and the five draft rules live in
  `config/draft_rules.json` as an **inactive** registry. The spike does not apply them.

## Layout

```
motif/              engine: evidence, classify, translate, materials, brief, llm, qloo access, agent (controller), CLI
motif/web/          web server (stdlib), view model, and static UI (HTML, CSS, vanilla JS)
render.yaml         Render Blueprint for the hosted demo (no secret values)
motif_spike/        stage 1-2 playground: adapter, transports, runner, normalize, compare, facts, CLI
config/             manifest.json, draft_rules.json, motif_lexicon.json, material_palette.json, engine_params.json
fixtures/synthetic/ invented scenarios and harness-shaped outputs
data/               run and session outputs (git-ignored; live Qloo data stays here)
reports/            feasibility.md, evidence_excerpt.md, design_examples.md, holdout_t1.md
docs/               evidence contract, Qloo access notes, deferred design, submission notes, examples
tests/              unittest suite (network blocked; synthetic fakes; recorded-data tests skip without data/)
```

## License

MIT. See [`LICENSE`](LICENSE).
