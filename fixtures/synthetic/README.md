# Synthetic fixtures (not Qloo data)

Everything in this folder was invented by hand to test MOTIF's evidence contract:
seed resolution, provenance links, missing fields, duplicates, retries, and error
states. Seeds, entities, tags, scores and IDs are fictional: names start with
"Synthetic" or "Fixture", IDs start with `SYNTHETIC-`, and tag IDs start with
`synthetic:`. They are not claims about Qloo's wire format, and they are not
evidence about any real brand.

- `scenario_main.json`: four fictional seeds that between them reach every
  request status the runner distinguishes. It lists which scenario exercises what.
- `scenario_auth_error.json`: the first request fails with a credential
  error, and the run must stop.
- `responses/`: documents shaped like the harness output described in
  `docs/QLOO_ACCESS_NOTES.md`.

Run with `python3 -m motif_spike run --mode synthetic`. Outputs are marked
`synthetic: true` and `provenance_category: synthetic_fixture` at every stage,
and the facts sheet carries a "NOT QLOO DATA" banner. The synthetic transport
cannot reach a process or the network. A live run never falls back to these
files.
