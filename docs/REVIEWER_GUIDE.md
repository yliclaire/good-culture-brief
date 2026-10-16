# How to review this submission

Start with the [interactive investment brief](https://yliclaire.github.io/good-culture-brief/). No setup or GitHub account is needed to read it. This repository is the implementation behind that brief.

## Follow the research

1. **Read the investment view.** The brief identifies where Good Culture leads, where substitutes win and which purchase evidence would change the investment view. Open “Challenge the finding” for counterexamples.
2. **Inspect the comparison.** In Explore the benchmark, choose a shopper question, engine, measure and population. Discovery/branded prompts and main/supplement remain separate. Conditional or unclear answers remain in the denominator; unavailable comparisons stay unavailable.
3. **Read an answer.** Expand “Named brands and contributing answers” and select Read answer. The exact prompt, model/mode/time, context flags and reviewed transcript are retained. Personal references are withheld; original screenshots remain private.
4. **Inspect the coding.** [coding.csv](../data/browser_baseline/coding.csv) has one row per observation; [brands.csv](../data/browser_baseline/brands.csv) separates mentions from recommendations and leads; [claims.csv](../data/browser_baseline/claims.csv) records selected claims and their citation status. The [codebook](CODEBOOK.md), [context/exclusion protocol](CONTEXT_EXCLUSION_RULES_v2.1.0.md) and [assistant coding instructions](CODING_INSTRUCTIONS_v2.1.0.md) explain the decisions. This was same-assistant review, not independent human agreement.
5. **Inspect the calculations and report binding.** [analysis.py](../benchmark_tool/analysis.py) constructs eligibility, denominators and brand contributions. [export.py](../report/export.py) prepares the chart states and checks narrative bindings. [The reviewed narrative](../reviewed_studies/good_culture/2026_q4/narrative.json) stores the interpretation and metric bindings; the renderer does not ask a model to invent a new investment conclusion at build time.

## Trace one headline number: protein recommendations, 12 / 12

- Prompt **Q3** asks for a high-protein snack recommendation; it does not name Good Culture. See [the study configuration](../studies/good_culture.json).
- The report-data view key is `main|baseline|question|Q3|all`. It contains 12 observation IDs: four engines × three passes, with no excluded answers or visible context flags in this view.
- For each answer, Good Culture has explicit overall-lead credit of 1. The total is 12 credits over 12 answers. This is not 12 consumers and does not estimate market share.
- A concrete record is `main/chatgpt/Q3/1`: [reviewed answer](https://yliclaire.github.io/good-culture-brief/evidence/13d5cb43e52a6080.html), [publication JSON](../data/browser_baseline/public_answers/13d5cb43e52a6080.json). Match the same observation ID in coding.csv, brands.csv and [the contribution table](../data/chart_tables/contributions.csv).
- [denominators.csv](../data/chart_tables/denominators.csv) supplies the four engine denominators; [membership.csv](../data/chart_tables/membership.csv) supplies their observation memberships. [report_data.json](../data/report_data.json) combines them into the displayed all-engine view. Its `metric_bindings.protein_leads` names the view, brand and field.

Every chart follows the same observation-ID trail. Source links preserve recorded attachments; they do not independently verify claims or establish what influenced an engine.

## Reproduce without collecting new answers

Use [Build investment brief](https://github.com/yliclaire/good-culture-brief/actions/workflows/build-brief.yml), or the local instructions in the [operating guide](OPERATING_GUIDE.md). GitHub viewers must fork the repository and enable Actions to run their own copy. The saved-study build needs no provider keys and makes no paid engine requests.

The [validation record](../VALIDATION.md) links to successful hosted runs and distinguishes completed checks from the remaining limits. Downloading GitHub run artifacts may require signing into GitHub. The website itself does not.

## Assess reuse

[Collect engine answers](https://github.com/yliclaire/good-culture-brief/actions/workflows/collect-answers.yml) previews exact requests before optional paid collection. The Birkenstock profile demonstrates category-specific questions and a different brand roster; it contains no footwear findings. After new collection, coding and interpretation require review/registration before the brief can build. See [what changes next quarter or for another category](OPERATING_GUIDE.md#reuse-next-quarter-or-in-another-category).

The provider adapters are tested with offline fixtures; live API compatibility remains unpiloted. The quarterly monitoring scenarios are synthetic demonstrations, not collected future results. Citation coverage, context and factual-verification limits remain visible in the brief.
