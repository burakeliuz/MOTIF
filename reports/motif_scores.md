# Weighted motif scores on the 13 trial brands (scoring-1.0)

Generated offline by `python3 tools/engine_compare.py scores` from the stored Qloo responses (no network, no LLM). Method: `docs/MOTIF_SCORING.md`. "Max change" = the largest change of this motif's score when any one related entity is removed (20 related entities per brand). Scores are design quantities, not probabilities; the product shows words.

| Brand | Motif | Score | Own cue groups | Related entities | Cue groups | Source kinds | Legacy strength | Max change, one related entity removed |
|---|---|---|---|---|---|---|---|---|
| MUJI | restrained | 0.799 | 1 | 8 | 6 | own, brand, movie | strong | 0.034 |
| MUJI | precise | 0.758 | 1 | 6 | 3 | own, brand, movie | strong | 0.030 |
| MUJI | natural | 0.728 | 1 | 4 | 4 | own, brand | moderate | 0.038 |
| MUJI | heritage | 0.442 | 1 | 0 | 1 | own | weak | 0.000 |
| MUJI | intimate | 0.099 | 0 | 0 | 0 | common cues only | context_only | 0.009 |
| MUJI | melancholic | 0.099 | 0 | 1 | 1 | movie | weak | 0.099 |
| MUJI | playful | 0.052 | 0 | 0 | 0 | common cues only | context_only | 0.017 |
| A24 | provocative | 0.699 | 2 | 1 | 2 | own, brand | moderate | 0.072 |
| A24 | restrained | 0.451 | 0 | 2 | 2 | movie | weak | 0.083 |
| A24 | intimate | 0.208 | 0 | 2 | 1 | movie | weak | 0.056 |
| A24 | opulent | 0.099 | 0 | 1 | 1 | movie | weak | 0.099 |
| A24 | precise | 0.099 | 0 | 1 | 1 | movie | weak | 0.099 |
| A24 | playful | 0.023 | 0 | 0 | 0 | common cues only | context_only | 0.011 |
| Comme des Garçons | provocative | 0.863 | 3 | 7 | 4 | own, brand | moderate | 0.006 |
| Comme des Garçons | experimental | 0.861 | 3 | 7 | 4 | own, brand | moderate | 0.007 |
| Comme des Garçons | precise | 0.602 | 0 | 6 | 5 | brand, movie | moderate | 0.063 |
| Comme des Garçons | restrained | 0.365 | 0 | 2 | 1 | movie | weak | 0.052 |
| Comme des Garçons | industrial | 0.268 | 0 | 2 | 1 | brand | weak | 0.112 |
| Comme des Garçons | opulent | 0.099 | 0 | 1 | 1 | movie | weak | 0.099 |
| Comme des Garçons | intimate | 0.082 | 0 | 0 | 0 | common cues only | context_only | 0.009 |
| Comme des Garçons | playful | 0.035 | 0 | 0 | 0 | common cues only | context_only | 0.017 |
| Nike | restrained | 0.275 | 0 | 0 | 0 | common cues only | context_only | 0.012 |
| Nike | heritage | 0.156 | 0 | 1 | 1 | brand | weak | 0.156 |
| Nike | intimate | 0.044 | 0 | 0 | 0 | common cues only | context_only | 0.010 |
| Ralph Lauren | precise | 0.754 | 1 | 6 | 4 | own, brand | moderate | 0.019 |
| Ralph Lauren | heritage | 0.669 | 1 | 2 | 2 | own, brand | moderate | 0.068 |
| Ralph Lauren | opulent | 0.351 | 0 | 2 | 3 | brand, movie | moderate | 0.195 |
| Ralph Lauren | provocative | 0.348 | 0 | 3 | 1 | brand | weak | 0.080 |
| Ralph Lauren | restrained | 0.325 | 0 | 1 | 1 | movie | weak | 0.074 |
| Ralph Lauren | intimate | 0.054 | 0 | 0 | 0 | common cues only | context_only | 0.010 |
| Ralph Lauren | playful | 0.018 | 0 | 0 | 0 | common cues only | context_only | 0.018 |
| Le Labo | restrained | 0.676 | 0 | 6 | 4 | brand, movie | moderate | 0.041 |
| Le Labo | precise | 0.656 | 0 | 9 | 5 | brand, movie | moderate | 0.036 |
| Le Labo | industrial | 0.442 | 1 | 0 | 1 | own | weak | 0.000 |
| Le Labo | heritage | 0.309 | 0 | 2 | 2 | brand | weak | 0.153 |
| Le Labo | opulent | 0.264 | 0 | 2 | 3 | movie | weak | 0.165 |
| Le Labo | natural | 0.156 | 0 | 1 | 1 | brand | weak | 0.156 |
| Le Labo | intimate | 0.090 | 0 | 0 | 0 | common cues only | context_only | 0.017 |
| Patagonia | natural | 0.556 | 1 | 1 | 1 | own, brand | moderate | 0.114 |
| Patagonia | restrained | 0.275 | 0 | 0 | 0 | common cues only | context_only | 0.012 |
| Patagonia | precise | 0.233 | 0 | 1 | 2 | brand | weak | 0.233 |
| Patagonia | heritage | 0.156 | 0 | 1 | 1 | brand | weak | 0.156 |
| Patagonia | industrial | 0.156 | 0 | 1 | 1 | brand | weak | 0.156 |
| Patagonia | intimate | 0.091 | 0 | 0 | 0 | common cues only | context_only | 0.009 |
| Aesop | precise | 0.774 | 1 | 6 | 4 | own, brand, movie | strong | 0.036 |
| Aesop | restrained | 0.645 | 0 | 5 | 3 | brand, movie | moderate | 0.046 |
| Aesop | natural | 0.631 | 1 | 2 | 2 | own, brand | moderate | 0.056 |
| Aesop | experimental | 0.156 | 0 | 1 | 1 | brand | weak | 0.156 |
| Aesop | industrial | 0.156 | 0 | 1 | 1 | brand | weak | 0.156 |
| Aesop | provocative | 0.156 | 0 | 1 | 1 | brand | weak | 0.156 |
| Aesop | melancholic | 0.099 | 0 | 1 | 1 | movie | weak | 0.099 |
| Aesop | intimate | 0.082 | 0 | 0 | 0 | common cues only | context_only | 0.009 |
| Aesop | playful | 0.035 | 0 | 0 | 0 | common cues only | context_only | 0.017 |
| Supreme | provocative | 0.716 | 1 | 4 | 3 | own, brand | moderate | 0.036 |
| Supreme | restrained | 0.478 | 0 | 2 | 2 | brand, movie | moderate | 0.154 |
| Supreme | industrial | 0.268 | 0 | 2 | 1 | brand | weak | 0.112 |
| Supreme | intimate | 0.208 | 0 | 2 | 1 | movie | weak | 0.056 |
| Supreme | experimental | 0.156 | 0 | 1 | 1 | brand | weak | 0.156 |
| Supreme | heritage | 0.156 | 0 | 1 | 1 | brand | weak | 0.156 |
| Supreme | precise | 0.156 | 0 | 1 | 1 | brand | weak | 0.156 |
| Supreme | playful | 0.057 | 0 | 0 | 0 | common cues only | context_only | 0.017 |
| Gucci | precise | 0.665 | 0 | 10 | 6 | brand, movie | moderate | 0.029 |
| Gucci | provocative | 0.643 | 1 | 2 | 2 | own, brand | moderate | 0.087 |
| Gucci | opulent | 0.527 | 0 | 5 | 3 | brand, movie | moderate | 0.076 |
| Gucci | heritage | 0.485 | 0 | 5 | 2 | brand | weak | 0.047 |
| Gucci | industrial | 0.156 | 0 | 1 | 1 | brand | weak | 0.156 |
| Gucci | romantic | 0.099 | 0 | 1 | 1 | movie | weak | 0.099 |
| Gucci | restrained | 0.079 | 0 | 0 | 0 | common cues only | context_only | 0.016 |
| Gucci | intimate | 0.063 | 0 | 0 | 0 | common cues only | context_only | 0.010 |
| Gucci | playful | 0.018 | 0 | 0 | 0 | common cues only | context_only | 0.018 |
| Harley-Davidson | heritage | 0.556 | 1 | 1 | 1 | own, brand | moderate | 0.114 |
| Harley-Davidson | provocative | 0.442 | 1 | 0 | 1 | own | weak | 0.000 |
| Harley-Davidson | precise | 0.385 | 0 | 3 | 2 | brand | weak | 0.117 |
| Harley-Davidson | industrial | 0.348 | 0 | 3 | 1 | brand | weak | 0.080 |
| Harley-Davidson | restrained | 0.129 | 0 | 0 | 0 | common cues only | context_only | 0.014 |
| Harley-Davidson | intimate | 0.011 | 0 | 0 | 0 | common cues only | context_only | 0.011 |
| Sanrio | playful | 0.719 | 1 | 3 | 1 | own, brand | moderate | 0.031 |
| Sanrio | restrained | 0.196 | 0 | 0 | 0 | common cues only | context_only | 0.015 |
| Sanrio | intimate | 0.023 | 0 | 0 | 0 | common cues only | context_only | 0.011 |
| Balenciaga | provocative | 0.838 | 2 | 6 | 4 | own, brand | moderate | 0.014 |
| Balenciaga | precise | 0.806 | 1 | 8 | 6 | own, brand, movie | strong | 0.020 |
| Balenciaga | experimental | 0.575 | 1 | 1 | 2 | own, brand | moderate | 0.133 |
| Balenciaga | industrial | 0.556 | 1 | 1 | 1 | own, brand | moderate | 0.114 |
| Balenciaga | restrained | 0.480 | 0 | 2 | 2 | brand, movie | moderate | 0.155 |
| Balenciaga | opulent | 0.469 | 0 | 4 | 3 | brand, movie | moderate | 0.101 |
| Balenciaga | heritage | 0.330 | 0 | 2 | 2 | brand | weak | 0.175 |
| Balenciaga | romantic | 0.283 | 0 | 2 | 1 | brand, movie | moderate | 0.184 |
| Balenciaga | intimate | 0.054 | 0 | 0 | 0 | common cues only | context_only | 0.010 |
| Balenciaga | playful | 0.018 | 0 | 0 | 0 | common cues only | context_only | 0.018 |

