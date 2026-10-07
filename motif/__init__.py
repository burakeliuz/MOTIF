"""MOTIF engine: Qloo evidence -> motifs -> sensory direction -> brief.

Deterministic core (no network, standard library only):
  evidence.py    normalized evidence items from Qloo response bodies
  classify.py    lexicon cue matching and motif support
  scoring.py     weighted motif scores (continuous engine)
  continuous.py  weighted motifs -> six continuous sensory dimensions (the primary engine)
  translate.py   legacy: draft rules R1-R5 -> six sensory axes (frozen baseline engine-0.3)
  materials.py   legacy: palette scoring and composition
  brief.py       engine result, template prose, LLM prose validation

Around it:
  qloo.py       budgeted access through motif_spike's transports (live or recorded replay)
  agent.py      the research controller (deterministic state machine)
  llm.py        optional prose writer (provider and model from the environment)
  cli.py        command line
"""

ENGINE_VERSION = "engine-0.3"  # 0.3: corroborating fetches are skipped only when provably unable to change the result; context exclusions
