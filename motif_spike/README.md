# motif_spike: Qloo feasibility spike

Before the engine existed, this playground tested whether the Qloo data
available at the hackathon is descriptive and differentiated enough to ground a
scent direction. Result: yes for a narrow scope (brand descriptors plus related
brands and films); see [`reports/feasibility.md`](../reports/feasibility.md).
The engine reuses its transport, parsers, and request log; the playground itself
is kept unchanged. The project frame is
[`MOTIF_QLOO_FEASIBILITY.md`](../MOTIF_QLOO_FEASIBILITY.md) (rev 0.2).

## Offline (no credential)

```sh
python3 -m motif_spike run --mode synthetic    # invented fixtures, no network
python3 -m motif_spike plan --plan pilot       # the requests a live pilot would send (nothing runs)
python3 -m motif_spike check                   # live readiness (presence only, never the value)
```

Synthetic output is marked `synthetic` everywhere, and its facts sheet carries
a "NOT QLOO DATA" banner. It checks the pipeline, not feasibility. Sample:
[`docs/examples/facts_synthetic_example.md`](../docs/examples/facts_synthetic_example.md).

## Live

With the Qloo hackathon key in the environment (`QLOO_API_KEY`):

```sh
python3 -m motif_spike check                          # must say READY
python3 -m motif_spike run --mode live --plan pilot   # 2 seeds x 3 domains, budget 20
python3 -m motif_spike run --mode live --plan full    # 5 seeds x 6 domains, budget 60
python3 -m motif_spike renormalize --run latest-live  # rebuild normalized output after a parser fix
python3 -m motif_spike excerpt --run latest-live      # small committable excerpt (reports/evidence_excerpt.md)
```

`--seeds a24,muji`, `--domains movie,brand`, `--max-requests N`, and
`--no-reuse` narrow or adjust a run. Identical successful live requests from
earlier runs are reused, not re-sent.

| Setting | How | Secret? |
|---|---|---|
| Qloo credential | `QLOO_API_KEY` in the environment, or `qloo setup --qloo` for the harness | yes |
| Base URL | fixed to `https://hackathon.api.qloo.com` in `config/manifest.json` | no |
| Transport | `direct` (default): MOTIF's own HTTPS client, which keeps full response bodies; `harness`: the official `qloo` CLI (`--transport harness`, Node.js ≥ 22.19.0, `@qloo/qloo-harness` ≥ 0.1.26) | no |
| `QLOO_HARNESS_BIN` | full path to `qloo` if it is not on `PATH` | no |

## What a run does

For each seed (A24, MUJI, Comme des Garçons, Nike, Ralph Lauren; see
`config/manifest.json`):

1. Search → resolve to exactly one returned entity, or report `unresolved` /
   `ambiguous` and stop for that seed.
2. Entity → the seed's own properties and tags.
3. Insights per domain → related entities with tags, properties, affinity, and
   explainability.
4. Tag insights for the seed.

Each request records the exact HTTP request (method, URL, parameters; never the
key), a status, its attempts, and a pointer to the saved output. Record format:
[`docs/EVIDENCE_CONTRACT.md`](../docs/EVIDENCE_CONTRACT.md). Access details:
[`docs/QLOO_ACCESS_NOTES.md`](../docs/QLOO_ACCESS_NOTES.md).

## Rules the playground enforces

- Live and synthetic never mix. A failed live call stays failed: no fixture,
  endpoint, or credential fallback.
- A credential error stops the run. Retries are bounded (2), and the budget is
  enforced.
- Observations copy literal returned values with a JSON Pointer to the raw file.
  Absent fields stay absent.
- Seeds resolve only on an exact name match (case and accents folded).
  Ambiguity is reported, never guessed.
- Overlaps use returned IDs only. Scores are never averaged across requests or
  called "lift".
- The six sensory axes, 12 candidate motifs, and five draft rules live in
  `config/draft_rules.json` as an inactive registry; the spike does not apply
  them.
