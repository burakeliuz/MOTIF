"""Research controller: a deterministic state machine over a bounded action set.

Who decides what: this module decides every research step from the observed
state (resolution result, engine result after each fetch, budget, access
errors). The LLM, when configured, only phrases the final prose; it chooses no
action. Each step is logged as {action, observed, decision, reason}.

Actions: resolve (search) -> ask_user (choice) -> fetch_own (/entities) ->
fetch_related(domain) in the configured order -> finish. A related domain is
fetched only if it can still change the engine output:

* brand is an anchor source: it can create new active motifs, so it is fetched
  unless the budget or an access error stops the session;
* movie and artist are corroborating sources: they can only raise a mapped
  motif that already has anchored support and is not yet strong. If none
  exists, the request is skipped and the reason is logged.

The same request is never sent twice in a session (session cache), and a
missing cue is never "retried" with another query.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence

from motif_spike.adapter import OP_RELATED, OP_SEARCH, OP_SEED_DETAIL, item_view, locate_items
from motif_spike.manifest import Seed
from motif_spike.resolve import resolve_seed

from .config import EngineConfig
from .engine import run_engine
from .evidence import items_from_body
from .qloo import QlooAccess, entity_argv, related_argv, search_argv

DOMAIN_TYPES = {"brand": "urn:entity:brand", "movie": "urn:entity:movie", "artist": "urn:entity:artist"}
ANCHOR_DOMAINS = {"brand"}
REFERENCE_TYPES = {"brand": ["urn:entity:brand"], "movie": ["urn:entity:movie"], "artist": ["urn:entity:artist"], "any": []}
STOP_ACCESS = {"auth_error", "forbidden", "skipped_after_auth_error"}


class Controller:
    def __init__(self, access: QlooAccess, config: EngineConfig, reference: str, reference_type: str = "brand",
                 choose: Optional[str] = None, domains: Optional[Sequence[str]] = None,
                 allow_unverified: bool = False, overrides: Optional[Dict[str, str]] = None):
        if reference_type not in REFERENCE_TYPES:
            raise ValueError(f"reference type must be one of {sorted(REFERENCE_TYPES)}")
        self.access = access
        self.config = config
        self.reference = reference
        self.reference_type = reference_type
        self.choose = choose
        self.domains = list(domains or config.params["default_domains"])
        unknown = [d for d in self.domains if d not in DOMAIN_TYPES]
        if unknown:
            raise ValueError(f"unsupported domains {unknown}; MVP domains are {sorted(DOMAIN_TYPES)}")
        self.allow_unverified = allow_unverified
        self.overrides = overrides or {}
        self.trace: List[Dict[str, Any]] = []
        self.evidence: List[Dict[str, Any]] = []

    # -- bookkeeping ---------------------------------------------------------------

    def _step(self, action: str, observed: str, decision: str, reason: str, request: Optional[Dict[str, Any]] = None) -> None:
        row = {"step": len(self.trace) + 1, "action": action, "observed": observed, "decision": decision, "reason": reason}
        if request:
            row["request_id"] = request["request_id"]
            row["request_status"] = request["status"]
            if request.get("served_from"):
                row["served_from"] = request["served_from"]
        self.trace.append(row)

    def _stopped(self, outcome: str, message: str, **extra) -> Dict[str, Any]:
        return dict({"status": "stopped", "outcome": outcome, "message": message}, **extra)

    def _request_ok(self, rec: Dict[str, Any]) -> Optional[str]:
        """None when usable; otherwise the stop outcome."""
        if rec["status"] in ("ok", "ok_empty"):
            return None
        if rec["status"] in STOP_ACCESS:
            return "stopped_access_error"
        if rec["status"] == "skipped_budget":
            return "stopped_budget"
        if rec["status"] == "not_recorded":
            return "stopped_not_recorded"
        return "stopped_request_failed"

    # -- the flow ----------------------------------------------------------------------

    def run(self) -> Dict[str, Any]:
        resolution = self._resolve()
        if resolution["status"] != "resolved":
            return {"resolution": resolution, "trace": self.trace, "result": None, **resolution["session_outcome"]}
        entity_id = resolution["qloo_id"]

        rec = self.access.request(OP_SEED_DETAIL, entity_argv(entity_id))
        stop = self._request_ok(rec)
        self._step("fetch_own", f"/entities -> {rec['status']}", "stop" if stop else "continue",
                   "the seed's own description is the base evidence" if not stop else self._error_text(rec), rec)
        if stop:
            return {"resolution": resolution, "trace": self.trace, "result": None,
                    **self._stopped(stop, self._error_text(rec))}
        self._add_evidence("own", rec)

        for domain in self.domains:
            result = run_engine(self.evidence, self.config, self.allow_unverified, self.overrides)
            fetch, reason = self._worth_fetching(domain, result)
            if not fetch:
                self._step(f"fetch_related:{domain}", self._summary(result), "skip", reason)
                continue
            rec = self.access.request(OP_RELATED, related_argv(entity_id, DOMAIN_TYPES[domain], self.config.params["related_take"]))
            stop = self._request_ok(rec)
            self._step(f"fetch_related:{domain}", self._summary(result), "stop" if stop else "fetched",
                       reason if not stop else self._error_text(rec), rec)
            if stop:
                partial = run_engine(self.evidence, self.config, self.allow_unverified, self.overrides)
                return {"resolution": resolution, "trace": self.trace, "result": partial,
                        **self._stopped(stop, self._error_text(rec), partial_result=True)}
            self._add_evidence(domain, rec)

        result = run_engine(self.evidence, self.config, self.allow_unverified, self.overrides)
        question = self._question_for(result)
        self._step("finish", self._summary(result), "ask_user" if question else "finish",
                   question["why"] if question else "every allowed step that could change the result has been taken")
        status = "needs_choice" if question and question["kind"] == "conflict" else "completed"
        return {"resolution": resolution, "trace": self.trace, "result": result, "status": status,
                "outcome": result["outcome"], "question": question}

    def _resolve(self) -> Dict[str, Any]:
        rec = self.access.request(OP_SEARCH, search_argv(self.reference, self.config.params["search_take"]))
        stop = self._request_ok(rec)
        if stop:
            self._step("resolve", f"/search -> {rec['status']}", "stop", self._error_text(rec), rec)
            return {"status": "failed", "request_id": rec["request_id"],
                    "session_outcome": self._stopped(stop, self._error_text(rec))}
        items, _ = locate_items(OP_SEARCH, rec["body"])
        candidates = []
        for pointer, item in items:
            view = item_view("search_candidate", item, pointer)
            view["pointer"] = pointer
            view["disambiguation"] = item.get("disambiguation") if isinstance(item, dict) else None
            view["request_id"] = rec["request_id"]
            candidates.append(view)
        public = [{"qloo_id": c["qloo_id"], "name": c["name"], "types": _types(c), "disambiguation": c["disambiguation"],
                   "pointer": c["pointer"]} for c in candidates]
        base = {"input": self.reference, "type": self.reference_type, "request_id": rec["request_id"],
                "candidates_returned": len(candidates)}

        if self.choose:
            chosen = [c for c in public if c["qloo_id"] == self.choose]
            if not chosen:
                self._step("resolve", f"{len(public)} candidates", "stop",
                           "the chosen ID was not among the returned candidates; MOTIF never uses an ID Qloo did not return", rec)
                return dict(base, status="invalid_choice", session_outcome=self._stopped(
                    "invalid_choice", f"{self.choose} is not among the returned candidates", candidates=public))
            c = chosen[0]
            self._step("resolve", f"{len(public)} candidates; user chose {c['qloo_id']}", "continue", "user choice", rec)
            return dict(base, status="resolved", method="user_choice", qloo_id=c["qloo_id"], name=c["name"],
                        types=c["types"], alternatives=[p for p in public if p is not c][:9])

        if not public:
            self._step("resolve", "0 candidates", "stop", "Qloo returned no entity for this name", rec)
            return dict(base, status="not_found", session_outcome=self._stopped("not_found", "Qloo returned no entity for this name"))

        seed = Seed(key="input", input_name=self.reference, expected_types=REFERENCE_TYPES[self.reference_type])
        res = resolve_seed(seed, candidates, rec["status"])
        if res["status"] == "resolved":
            alts = [a for a in public if a["qloo_id"] != res["qloo_id"]]
            self._step("resolve", f"{len(public)} candidates; {res['method']}", "continue",
                       "exactly one candidate fits the name and type; the others are listed", rec)
            return dict(base, status="resolved", method="auto_single_match", qloo_id=res["qloo_id"], name=res["name"],
                        types=res["types"], alternatives=alts)
        exact_or_near = res["alternatives"] if res["status"] == "ambiguous" else res["near_matches"]
        ids = [o["qloo_id"] for o in exact_or_near]
        # Candidates of the requested type are always offered too, even when their name differs
        # (T1: "Le Labo" returned the brand as "Le Labo Fragrances" and only two shops matched the name).
        wanted = set(REFERENCE_TYPES[self.reference_type])
        ids += [p["qloo_id"] for p in public if wanted & set(p["types"]) and p["qloo_id"] not in ids]
        options = [dict(p, name_matches_input=p["qloo_id"] in {o["qloo_id"] for o in exact_or_near})
                   for i in ids for p in public if p["qloo_id"] == i]
        why = ("several returned candidates share this name and type" if res["status"] == "ambiguous"
               else "no returned candidate has exactly this name")
        self._step("resolve", f"{len(public)} candidates; {res['status']}", "ask_user", why, rec)
        question = {"kind": "choose_entity", "why": why, "options": options,
                    "how_to_answer": "re-run with --choose <qloo_id> (an ID from the options), or rephrase the reference"}
        return dict(base, status=res["status"], session_outcome={"status": "needs_choice", "outcome": "needs_entity_choice",
                                                                  "question": question})

    def _worth_fetching(self, domain: str, result: Dict[str, Any]) -> (bool, str):
        """Fetch unless it is provable that the domain cannot change the engine result.

        "Result" here is the outcome, which motifs are active, every anchored motif's
        strength, the axis targets and their weights, and the materials. A corroborating
        source (movie, artist) cannot create an anchor, so it can change that result only
        through a motif that already has anchored support and is not yet strong, mapped or
        not (an unmapped motif turning moderate changes the outcome from
        insufficient_evidence to no_translation_rule). If no such motif exists, the skip
        is safe. Weak, unanchored motifs it could add are display-only and do not count.
        """
        if domain in ANCHOR_DOMAINS:
            return True, "related brands are an anchor source: they can create or corroborate motifs"
        open_motifs = sorted(m for m, info in result["motifs"].items()
                             if info["anchored"] and info["strength"] in ("weak", "moderate"))
        if open_motifs:
            return True, (f"{domain} can corroborate motifs with anchored support below 'strong': "
                          + ", ".join(open_motifs) + " (their strength, the outcome, or the targets may change)")
        return False, (f"skipped safely: {domain} is a corroborating source and no motif has anchored support "
                       "below 'strong', so it cannot change the outcome, active motifs, strengths, targets, or materials")

    def _question_for(self, result: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        if result["outcome"] == "conflicted":
            axis = result["conflicted_axes"][0]
            pushes = result["axes"][axis]["pushes"]
            return {"kind": "conflict", "axis": axis,
                    "why": f"active motifs push {axis} to opposite poles",
                    "options": sorted({p["pole"] for p in pushes}) + ["open"], "pushes": pushes,
                    "how_to_answer": f"re-run with --resolve-conflict {axis}=<pole|open>"}
        if result["outcome"] in ("no_descriptive_data", "insufficient_evidence", "no_translation_rule", "partial_direction"):
            return {"kind": "next_step", "why": result["outcome_meaning"],
                    "options": ["stop", "try another reference"],
                    "how_to_answer": "no material composition is made; stop here or run MOTIF with a different reference"}
        return None

    # -- helpers ------------------------------------------------------------------------

    def _add_evidence(self, kind: str, rec: Dict[str, Any]) -> None:
        request = {"request_id": rec["request_id"], "fetched_at": rec["fetched_at"], "path": rec["path"], "params": rec["params"]}
        self.evidence.extend(items_from_body(kind, rec["body"], request, self.config.lexicon["match"]["namespaces"]))

    @staticmethod
    def _summary(result: Dict[str, Any]) -> str:
        active = [f"{m}:{i['strength']}" for m, i in sorted(result["motifs"].items()) if i["active"]]
        targets = [f"{a}={v['value']}" for a, v in result["axes"].items() if v["state"] == "target"]
        return f"evidence {result['evidence_count']}; active [{', '.join(active)}]; targets [{', '.join(targets)}]"

    @staticmethod
    def _error_text(rec: Dict[str, Any]) -> str:
        return (rec.get("error") or {}).get("message_redacted") or f"request status {rec['status']}"


def _types(view: Dict[str, Any]) -> List[str]:
    out: List[str] = []
    for value in view.get("types", {}).values():
        out.extend([value] if isinstance(value, str) else [v for v in value if isinstance(v, str)])
    return out
