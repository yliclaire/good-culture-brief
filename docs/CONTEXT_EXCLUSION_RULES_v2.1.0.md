> Historical method reference from the original browser study. Original working-folder paths mentioned below are not public runtime dependencies. The public derivative is documented in [PUBLICATION.md](../data/browser_baseline/PUBLICATION.md). The context protocol takes precedence over earlier v2.0 wording; the implementation uses the frozen v2.1.0 rules.

# Context and exclusion protocol v2.1.0

Frozen before full-study coding on 2026-10-15, following user acceptance. Extends codebook v2.0.0 without changing the prompts, hypotheses or frozen collection. Preserve the preceding v2 run. Apply every rule to all engines and repeats, including the already reviewed 20 cases. Rule revisions require a new version, a reason and recoding all affected observations.

## Inclusion and defects

Complete, usable answers are included for recommendation analysis, including answers with no recommendation. Valid no-recommendation outcomes receive zero brand recommendation credit and remain in the denominator. Conditional-only choices and explicit ties remain separate.

Exclude missing, wrong-prompt, truncated or unusable captures from complete-answer metrics; preserve every attempt, the captured text and its specific reason. A known defect requires adjudication, never automatic favorable replacement. Copilot Search Q1 remains excluded because its saved final table cuts off mid-row. Qualitative use must identify it as partial.

Missing citations do not invalidate a complete answer for brand/recommendation coding. A claim without an observed, claim-mapped citation cannot enter metrics requiring such citations. Report mapped-claim coverage and the missing denominator; zero observed links does not prove the engine consulted no sources. Source-panel, related-result, product-image and independently researched URLs are not automatically supporting citations.

## Visible context

Flag authored answer prose explicitly referring to the shopper's name, location, prior conversations or prior preferences not supplied in the fixed prompt. Preserve exact excerpts and the flag category. The prompt's U.S. context and preferences do not count as contamination. Conditional hypothetical language (for example, 'if you prefer creamy') and generic availability/store advice are not proof of personalization. An account identity appearing only in browser UI is not an answer-personalization flag.

No visible signal means only that none was found; it does not establish context neutrality. Retain complete flagged answers in the descriptive baseline and disclose flag counts. Report a second analysis excluding flagged answers. No post-hoc substitution with retries.

## Matched sensitivity comparisons

Main layer: retain question × repeat strata only when every one of the four main engines has an approved, complete, included answer without a context flag in that stratum. Use the same retained strata for every engine. Distinguish removal of a flagged observation from loss of otherwise usable matched peers; report both counts and retained strata. If no matching stratum remains, report 'not estimable', not zero.

Supplement layer: apply the same rule within its two engines and six planned questions; keep it separate from the main study. Do not demand supplemental observations for main-only questions. Repeat numbers are labels for matched collection passes, not randomized independent trials.

Hypothesis comparisons require comparable question coverage: for a contrast between two prompt groups, use only repeat labels with all required questions and all engines eligible, then average questions equally. Report coverage loss and do not interpret a changed question mix as an effect of removing context. A group without adequate comparable coverage remains not estimable.

Always report collected, approved/included, excluded, pending, visibly flagged and denominator used. Keep Q1–Q9 discovery separate from Q10–Q12 branded prompts. Main and supplement never share a pooled six-engine rate. Repeats measure answer variability; they are not independent consumers or market share.

## Review provenance

Freeze this file/config/raw evidence via input hashes. Record exact assistant-coding instructions and evidence-backed output tables by batch. Approved means explicit semantic/evidence review, not merely automatic extraction. Keep ambiguous items needs_review with notes until resolved. Mechanical quote matching alone is insufficient. Claims remain unverified engine statements until separately checked against comparable product/serving/date evidence.
