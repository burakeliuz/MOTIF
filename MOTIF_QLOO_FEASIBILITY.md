# MOTIF — Qloo Feasibility Spike and Claude Code Working Brief

Revision: 0.2 · 2026-10-02 · Project owner: Burak Eliuz

This revision updates the original Qloo feasibility brief with the decisions from the 2 October discussion. No live Qloo experiment has been completed in this conversation. The illustrative cultural inputs and their motif labels were synthetic. Do not report them as findings.

## 1. Product and current objective

MOTIF is a Qloo Agentic Hackathon project that translates a brand, event, or creative identity's cultural context into an explainable olfactory direction and a perfumer brief.

The eventual pipeline is:

1. User-provided cultural references.
2. Qloo entity resolution, cross-domain relationships, and available attributes/tags.
3. Evidence-grounded cultural motif classification and aggregation.
4. A versioned, deterministic Cultural-to-Olfactory Translation Engine.
5. Material matching and composition rules, once a documented material palette exists.
6. A schema-validated brief with a traceable explanation.

The present task is to test the foundation of that pipeline: does the accessible Qloo API provide sufficiently descriptive and differentiated evidence for motif extraction? Build a small technical playground, not the product frontend or the fragrance engine.

MOTIF produces a creative direction. It does not produce a chemical formula, dosage instructions, a validated prediction of fragrance preference, or proof that an audience will like a scent.

## 2. Qloo's actual role

Qloo contributes entity resolution, cultural relationships, context-dependent rankings, and available descriptive data. Its contribution should influence which cultural references inform the design and how we justify the resulting motifs.

Keep these distinctions explicit:

| Item | Meaning in MOTIF | Does not establish |
|---|---|---|
| Qloo relationship or affinity | A returned connection between the supplied context and another cultural entity | A shared aesthetic, a person's certain preference, or fragrance suitability |
| A returned attribute or tag | A descriptive datum within its actual namespace and context | Any adjective the model associates with the entity's name |
| MOTIF motif classification | Our interpretation of specific descriptive evidence | A Qloo-supplied motif unless Qloo actually returned that label |
| Motif-to-sensory rule | An authored creative translation rule | A scientific law or a Qloo-discovered scent relationship |
| Suggested olfactory direction | A design hypothesis grounded in the preceding chain | A finished perfume or evidence of consumer acceptance |

For example, an affinity between a film and a brand does not demonstrate that both are minimalist. A tag describing a plot event does not automatically describe the film's visual style. A brand's associated audience is not interchangeable with the brand's intended identity.

Only claim that a source contains information that is actually present. If the response does not describe composition, texture, pacing, materiality, or another proposed motif cue, do not manufacture that description from the entity name or model memory.

The live experiment must test whether these missing descriptions can be obtained through the documented, accessible Qloo surfaces. Report an evidence gap when they cannot.

## 3. Evidence and responsibility boundaries

Use four distinct provenance categories:

- `qloo_observation`: an actual returned entity, relationship, attribute, tag, score, or explanation, linked to its raw response and field path.
- `motif_annotation`: a manual or later LLM classification, with explicit evidence references, the classification method, and the rule/prompt version. Never label this as Qloo output.
- `design_rule`: a versioned, human-authored cultural-to-olfactory mapping.
- `synthetic_fixture`: invented test data, visibly marked as synthetic throughout the pipeline.

An explanation must be able to follow the relevant observations, annotations, and design rules to the resulting direction. Keep contradictory or insufficient evidence visible.

The eventual LLM may classify supported evidence into the controlled motif vocabulary, name/explain motifs, and write the brief. It may not invent cultural facts, choose or substitute materials, modify engine scores, fill missing axes, or make a fragrance-preference claim. Its annotations must remain traceable and distinguishable from observations.

During this feasibility spike, do not add an LLM classification or fragrance-generation pipeline. Produce evidence-only summaries and a factual feasibility report. The restriction concerns product inference; Claude Code may still implement the playground and explain what observed responses contain.

## 4. Preserve the six sensory axes

These pairs and their directions are part of the project baseline. Do not rename, reverse, merge, or add axes during the spike.

| Axis key | First pole | Second pole | Interpretation |
|---|---|---|---|
| `warm_cool` | warm | cool | Perceived olfactory warmth/coolness |
| `light_dense` | light | dense | Perceived weight or density |
| `raw_polished` | raw | polished | Perceived texture/refinement |
| `natural_synthetic` | natural | synthetic | Perceived aesthetic impression, not ingredient origin |
| `intimate_projecting` | intimate | projecting | Intended spatial presence, not measured formula performance |
| `sweet_dry` | sweet | dry | Intended sweetness/dryness impression |

An unsupported axis is unknown. Represent its numeric value as `null`; do not replace it with zero, a midpoint, or an invented neutral score. Qualitative directions may be recorded as draft design targets where a rule exists. Numerical mappings and calibration are not yet established.

Do not confuse lightness, projection, and longevity. A natural impression does not require natural-origin ingredients. A sensory target is a brief requirement, not a guarantee of how an unformulated perfume will perform.

## 5. Motif vocabulary and provisional translation rules

The original scope was approximately 12 motifs, six axes, and a palette of approximately 20 materials. These are scope targets, not quotas or validated inventories. The 20-material list has not been finalized. Do not invent it to complete the specification.

The 12 candidate motifs remain: `restrained`, `experimental`, `intimate`, `industrial`, `romantic`, `heritage`, `playful`, `provocative`, `natural`, `precise`, `opulent`, `melancholic`.

The following five rules are draft creative hypotheses. They are not empirical findings or production-calibrated mappings. Keep them in documentation or an inactive draft registry while running the Qloo spike.

| Rule | Motif | Proposed direction | Why we propose it | No automatic inference |
|---|---|---|---|---|
| R1 | `restrained` / ölçülü | `light_dense` toward light | Translate restraint as reduced perceived weight | No projection, sweetness, or temperature decision |
| R2 | `intimate` / mahrem | `intimate_projecting` toward intimate | Translate closeness as a close-to-skin design target | No lightness or longevity decision |
| R3 | `precise` / hassas | `raw_polished` toward polished | Translate controlled detail as a refined texture target | No natural/synthetic or temperature decision |
| R4 | `opulent` / gösterişli | `light_dense` toward dense | Translate richness as greater perceived density | No automatic sweetness or projection |
| R5 | `natural` / doğal | `natural_synthetic` toward a natural impression | Translate evidenced natural imagery/materiality as an aesthetic target | No ingredient-origin, safety, or sourcing claim |

The remaining seven motifs have no automatic sensory-axis mapping yet. Preserve evidence-backed annotations for review, but do not let them influence numeric axes or material ranking until a justified rule exists. In particular, do not assume playful means sweet, melancholic means cool, romantic means floral, heritage means warm, or industrial means synthetic.

Important correction: remove the earlier provisional `restrained → intimate` mapping. Projection now belongs to R2. Do not count the same implication twice under different motif names.

Material matching is deferred. A manufacturer's olfactory descriptor can support a material's property, but it cannot validate the cultural-to-olfactory rule itself. The later palette must document exact material identity or clearly identify a note/accord, source descriptors, uncertainties, proposed sensory representation, and intended composition role. Do not treat a generic note name and a specific material grade as interchangeable.

## 6. Worked synthetic example and correction

These are manually authored fixtures, not Qloo records, tags, or search results:

| Fixture | Domain | Invented description | Manually assigned motifs |
|---|---|---|---|
| B1 | brand | Unadorned products; controlled geometric design | restrained, precise |
| F1 | movie | Sparse composition; controlled framing | restrained, precise |
| M1 | music artist | Sparse arrangement; intimate recording impression | restrained, intimate |

For this demonstration only, use a configurable support threshold of two distinct domains. It is not a validated confidence threshold. Multiple domains are not necessarily independent evidence.

Expected counts: restrained = 3 domains; precise = 2; intimate = 1.

Under the revised draft rules, restrained and precise are active. The qualitative target is light and polished. Warm/cool, natural/synthetic, intimate/projecting, and sweet/dry remain unknown. Material selection remains unperformed.

Future regression expectations:

- Reordering fixtures does not change the result.
- Duplicating B1 within the same domain does not create new domain support.
- Removing F1 reduces precise to one domain; polished becomes unknown.
- The weak intimate motif must not reappear indirectly through restrained.
- Unknown axes remain unknown in the written brief.

Document these expectations now. Do not implement the production translation engine merely to run this example. This exercise established internal rule behavior only; it did not validate Qloo coverage, cultural interpretation, or the resulting scent.

## 7. Work before the API key arrives

1. Inspect the existing repository and its instructions. Preserve unrelated work and reuse the current stack. In an empty project, choose a minimal script/CLI implementation; avoid adding application infrastructure.
2. Define a small Qloo adapter boundary, a request manifest, and the normalized evidence contract described below.
3. Add explicit live and synthetic modes. Synthetic mode must never call the network or masquerade as live results. A failed live request must never silently fall back to a fixture.
4. Create clearly labelled fixtures to exercise normalizing, provenance, absent fields, and error handling. They are local contract examples, not claims about the exact Qloo wire schema. Mark the real-response parser as unverified until checked against current documentation and live responses.
5. Prepare the five seed identities, a report template, and straightforward run instructions.
6. Keep credentials out of code, fixtures, reports, screenshots, and logs. Document local configuration with empty placeholders. Detect whether required configuration exists without displaying secret values.

With no credential, complete all offline work and report that live feasibility is not yet evaluated. Do not ask the user to paste a key into chat.

## 8. Live Qloo experiment

### 8.1 Verify access and resolve inputs

Use current official documentation and the event-provided configuration. Verify the supported base URL, authentication, entity types, request parameters, available workflows, response shapes, and event limits. Do not assume that every capability advertised for Qloo is available under the hackathon credential.

The public Qloo hackathon kit documents CLI, chat, and MCP entry points. Reuse an available supported route; do not add a second integration only for completeness. Do not substitute an endpoint or credential after an authorization error.

Start with these identities:

- A24
- MUJI
- Comme des Garçons
- Nike
- Ralph Lauren

Resolve each through Qloo Search. Preserve returned IDs and entity types. Record unresolved or ambiguous matches rather than selecting an unrelated entity with a similar name. Use the verified type identifiers actually supported by the API.

### 8.2 Request useful cross-domain evidence

Candidate domains from the original brief are brands, movies, music artists, books, people, and places. Treat these as human-readable candidates; verify their actual API representations and availability.

Begin with a small pilot on two resolved seeds and a few useful supported domains. Expand to the five seeds and remaining useful domains after confirming the requests and inspecting coverage. Use a small configurable result limit, bounded retries, and caching consistent with the event terms. Do not perform an exhaustive crawl.

Retrieve relevant tag insights and entity attributes where supported. Enable explainability only where documented and accessible. Preserve returned affinity, ranking, and explanation information, including the query context and domain. Missing explanation or score fields remain missing.

Save complete successful response bodies locally with their request provenance. Never save authentication headers or credentials. Redact secrets from any error text. Follow the applicable event/data terms for caching or sharing responses.

### 8.3 Normalize without semantic invention

Keep literal response observations separate from interpretation. Record the source pointer for each retained field. A tag's identifier, namespace, and context matter: two tags with similar display names are not automatically the same concept.

Preserve scores as returned. Do not turn them into percentages of people, confidence values, or scent suitability. Do not average scores from different query/domain contexts without a documented comparability basis. Preserve rank within the originating result set as a separate field.

An absent tag is not a negative preference. An empty result, an unsupported feature, an unresolved seed, and an authentication/rate-limit error are different states.

## 9. Minimal local evidence contract

This is MOTIF's internal contract, not a claim about Qloo's response schema. Choose concrete field names to fit the existing stack, but preserve these distinctions:

| Record | Required content |
|---|---|
| Run | Run ID, timestamp, mode, configuration/rule version, live-execution status |
| Seed resolution | Input name, returned ID/type if available, resolution status, raw-response reference |
| Request | Local request ID, operation/domain, non-secret parameters, timestamp, status, response reference |
| Observation | Local evidence ID, request ID, returned entity/tag IDs and types when available, literal name/attributes/tags, original score and rank when present, JSON path/raw reference |
| Coverage | Returned fields, missing fields, unsupported features, errors, and useful descriptive coverage by domain |
| Annotation, later phase only | Motif ID, evidence IDs and cited spans/field paths, method, annotation version, and limitations |
| Sensory target, later phase only | All six axes, proposed direction where justified, nullable numeric value, rule IDs and motif references |

Local record IDs must be recognizably local; never fabricate Qloo IDs. Synthetic records need an explicit synthetic marker and cannot serve as live proof. Keep raw and normalized outputs separate.

## 10. Feasibility report and decision

Produce a concise comparison report with:

1. Resolution status for all five seeds, including untested seeds and reasons.
2. Supported and tested domains, request status, and available fields.
3. Actual returned tag/attribute examples with their provenance.
4. Differences and overlap between seed profiles, using comparable requests.
5. Whether repeated descriptive patterns can be observed across domains without inventing semantics.
6. Whether globally common results dominate the observed patterns.
7. Available quantitative fields and whether any valid enrichment analysis is possible.
8. Missing semantic information that prevents motif classification.
9. Which potential MOTIF decisions the observed evidence could support, and which remain unsupported. Do not generate a scent to complete this section.
10. A recommendation: continue, narrow, or pause, with specific observed reasons and remaining uncertainties.

Do not call an affinity-score ratio “lift.” An enrichment calculation requires suitable observations, denominators, and a comparable reference population/sample. If only small retrieved samples are available, describe the result as sample enrichment and disclose the sampling limits. If the required basis is absent, say it cannot be calculated.

Keep separate judgments for data availability, descriptive sufficiency, and profile differentiation. A response can contain many related entities while providing little usable motif evidence.

Before live execution, use `not_evaluated`, not a positive feasibility verdict. After live execution:

- Continue when the observations provide a credible, traceable basis for distinct cultural interpretations.
- Narrow when only a subset of domains or identities has useful coverage.
- Pause the affected inference when it would require invented attributes or unsupported claims.

These are decision guidelines, not a prevalidated numeric scorecard. Do not design the evaluation to guarantee a pass.

## 11. Showing Qloo's contribution

The initial spike compares actual cross-domain evidence, coverage, and profile differentiation. It should reveal whether Qloo supplies useful cultural context beyond the seed names.

A later evaluation may hold the taxonomy, translation rules, and writing process fixed while comparing a seed-only baseline with a Qloo-enriched run. Record which observations change or substantiate motif decisions, which sensory targets change, and which remain unsupported. Mark any baseline interpretation as model/manual inference, not evidence from Qloo.

Do not add an LLM baseline pipeline to the present spike. Document the later comparison design. A changed answer alone is not proof of improvement, and Qloo need not change every output to provide useful grounding.

## 12. Deliverables and boundaries for Claude Code

Expected outputs from the coding task:

- A minimal runnable playground with explicit live and synthetic modes.
- Documented local configuration and run commands.
- A normalization contract and clearly labelled synthetic fixtures.
- Focused checks for provenance retention, missing fields, duplicate handling, and explicit error states.
- Local raw and normalized response storage for live runs, subject to applicable terms.
- A feasibility report or an honestly incomplete report when the API key is absent.

Avoid unnecessary scaffolding. A small `src/`, `fixtures/synthetic/`, `data/raw/`, `data/normalized/`, and `reports/` layout is sufficient if the repository has no existing structure. Keep secrets and non-public response data out of source control as appropriate.

Not in scope: frontend, deployment, authentication UI, production motif classifier, sensory scoring calibration, material matcher, generated perfume formula, new product features, or an expanded 20-material catalogue.

At the end, summarize in Turkish: what was built, what actually ran, what the data supports, what remains unknown, and the next concrete step. Complete reversible work already covered by this brief without repeated permission requests. If missing credentials prevent live execution, finish the offline deliverables first and state the exact local configuration needed.

## 13. References and change record

Official sources reviewed on 2026-10-02:

- [Qloo capabilities](https://www.qloo.com/capabilities): cultural enrichment, cross-domain relationships, context-dependent recommendations.
- [Qloo public API documentation](https://github.com/qloo/docs-public): official documentation and API specification.
- [Taste analysis reference](https://github.com/qloo/docs-public/blob/main/reference/taste-analysis.md): tag-based insights and their scope.
- [Affinity concepts](https://github.com/qloo/docs-public/blob/main/docs/affinity-score.md): relationship scores and their context.
- [Qloo hackathon kit](https://github.com/qloo/qloo-hackathon-kit): supported integration routes and the aggregate nature of affinity results.
- [Hackathon API access guidance](https://github.com/qloo/qloo-hackathon-kit/blob/main/docs/API_ACCESS.md): event access, limits, and data handling.
- [Hackathon developer guide](https://docs.qloo.com/reference/qloo-llm-hackathon-developer-guide): event-specific onboarding; direct retrieval was unavailable during preparation, so re-check it before implementing live access.

These references establish documented capabilities, not verified access or response coverage under Burak's eventual key.

Revision 0.2 changes:

- Preserved the five seed identities and the feasibility-first scope.
- Distinguished Qloo observations, motif annotations, creative translation rules, and synthetic fixtures.
- Preserved the six original axes; unsupported dimensions remain unknown.
- Recorded five provisional motif rules and left seven unmapped.
- Removed `restrained → intimate` and corrected the worked example.
- Added offline progress, evidence provenance, score interpretation boundaries, and an explicit feasibility decision.
- Deferred UI, runtime LLM classification, and fragrance/material generation until the relevant foundation is demonstrated.
