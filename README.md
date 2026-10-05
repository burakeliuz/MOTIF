# MOTIF: Qloo feasibility spike

MOTIF will translate a brand's, event's, or creative identity's cultural context
into an explainable olfactory direction and a perfumer brief. This repository
currently contains only the first step: a small playground that tests whether
the Qloo data accessible to the hackathon provides enough descriptive and
differentiated evidence for that.

It is **not** the product: no frontend, motif classifier, sensory scoring,
material matching, or brief generation. The project frame is
[`MOTIF_QLOO_FEASIBILITY.md`](MOTIF_QLOO_FEASIBILITY.md) (rev 0.2).

**Status:** offline playground complete; **live Qloo feasibility not yet evaluated**
(no event credential configured). See [`reports/feasibility.md`](reports/feasibility.md).

## Requirements

- Python 3.9+ (standard library only; no install step). Tests pass on 3.9–3.13 under Linux; Windows is untested.
- For live runs: Node.js ≥ 22.19.0 and the official event harness
  `npm install --global @qloo/qloo-harness` (≥ 0.1.26)

## Quick start (offline, no credential)

```sh
python3 -m motif_spike run --mode synthetic    # invented fixtures, no network
python3 -m unittest                            # 40 focused checks
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
| Event base URL | hackathon keys only work against `https://hackathon.api.qloo.com`. MOTIF passes it to the harness on every live run from `config/manifest.json` (`harness_environment`). | no |

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

In a Claude Code cloud session, add `QLOO_API_KEY` in the environment
settings (the environment menu in the session title bar, then Edit), allow
`hackathon.api.qloo.com` under the environment's network access (it is not
reachable by default), and start a new session. The harness also needs
installing there (`npm install --global @qloo/qloo-harness`).

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
normalized output from saved raw files after a parser fix.

## What a run does

For each seed (A24, MUJI, Comme des Garçons, Nike, Ralph Lauren; see `config/manifest.json`):

1. `qloo api search` → resolve to exactly one returned entity, or report
   `unresolved` / `ambiguous` and stop for that seed.
2. `qloo api entity` → the seed's own properties and tags.
3. `qloo api insights` per domain → related entities with tags, properties, affinity, and explainability if returned.
4. `qloo exec entity_tags` → tag insights for the seed.

Each request records the exact harness command, the HTTP request the harness
reports (`--dry-run`), a status, its attempts, and a pointer to the saved
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
motif_spike/        adapter (harness boundary), runner, normalize, compare, facts, CLI
config/             manifest.json (seeds, domains, plans), draft_rules.json (inactive)
fixtures/synthetic/ invented scenarios and harness-shaped outputs
data/               run outputs (git-ignored)
reports/            feasibility.md (curated report; currently not_evaluated)
docs/               evidence contract, Qloo access notes, deferred design, synthetic example output
tests/              unittest suite (+ a fake harness used only by tests)
```

## License

MIT. See [`LICENSE`](LICENSE).
