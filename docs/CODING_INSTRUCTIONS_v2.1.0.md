> Historical method reference from the original browser study. Original working-folder paths mentioned below are not public runtime dependencies. The public derivative is documented in [PUBLICATION.md](../data/browser_baseline/PUBLICATION.md). The context protocol takes precedence over earlier v2.0 wording; the implementation uses the frozen v2.1.0 rules.

# Assistant coding instructions and provenance

Version 2.1.0; frozen for full coding on 2026-10-15. Read docs/CODEBOOK.md, docs/CONTEXT_EXCLUSION_RULES_v2.1.0.md, and the settled second-pass decisions before coding. Unit: one saved answer, never combine repeats or layers.

For each assigned observation, read the complete saved response. Establish the authored answer boundary; exclude prompt, preview/status, account UI, source panels, suggested questions, search cards and image alt text. Keep authored product choices, lists, tables and caveats. Consult raw DOM/AX whenever extraction is ambiguous. Do not complete or fact-correct engine language. Save the answer-only text.

Enumerate distinct canonical brands in authored text, including negative mentions and comparisons. Distinguish retail availability from private-label brand names. Code purchase recommendations separately from mentions; distinguish explicit overall leader, explicit joint lead, conditional-only, no recommendation and unclear. A specific overall/default purchase choice overrides secondary branches; a best-value attribute alone is not an overall purchase default. Do not turn a category-first strategy into a unique brand lead. Record explicit replacements for Good Culture only; competing alternatives to another brand are not automatically Good Culture substitutes.

Provide brand-level exact raw excerpts for mentions, recommendations, leads and substitutions. Record material benefits, drawbacks, purchase conditions and variants as individual claim rows with exact evidence. Avoid unsupported compound codes: split variants when the quote does not support all of them. Only use codebook reason tags. Assess premium only where the answer judges paying more; price presence alone is not premium endorsement. Do not treat reported reviewer willingness-to-pay as the engine's unconditional premium endorsement.

Review authored prose for personal/location/prior-context signals not in the fixed prompt. Preserve evidence. Do not flag account UI, hypothetical preference branches or generic shopping advice. Check completeness and exact-prompt match; document inclusion/exclusion. Missing citations alone never excludes a complete recommendation answer.

Keep citations not_mapped unless the observed URL is linked to that specific claim. Use no_visible_citation only when the saved evidence establishes the absence of visible citation controls, unavailable when capture prevents determination. Never attach independent web links as engine citations. Claims remain unverified_engine_claim unless separately fact-checked with evidence.

Approved means this assistant explicitly read the answer and checked interpretation and evidence. Leave unresolved cases needs_review. Do not auto-approve from regex, brand order, model consensus or desired hypotheses. Record ambiguous decisions and repairs. Prior coding context is visible: no blind or independent agreement is claimed.

Reviewer: Codex assistant (GPT-6 family; exact serving model identifier unavailable). No external model/API classifier is used. The exact instructions are this file plus the two frozen protocol documents; structured outputs and exact evidence are coding.csv, brands.csv and claims.csv, with per-batch snapshots and run hashes. Software helpers copy/extract/validate saved evidence only; they do not supply semantic judgments.
