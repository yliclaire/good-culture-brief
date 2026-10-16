# Research & implementation

[Investment brief](https://yliclaire.github.io/good-culture-brief/) · [Pipeline reference](https://yliclaire.github.io/good-culture-brief/reviewer-guide.html) · [Run configuration](OPERATING_GUIDE.md)

## Data flow

Study configuration → collection → reviewed coding and narrative → registered inputs → validated metrics → HTML brief.

| Layer | Implementation |
| --- | --- |
| Study specification | [Profiles](../studies/good_culture.json): prompts, competitors, attributes and collection settings |
| Evidence and coding | [coding.csv](../data/browser_baseline/coding.csv): observations; [brands.csv](../data/browser_baseline/brands.csv): mentions, recommendations and leads; [claims.csv](../data/browser_baseline/claims.csv): selected claims and citation status |
| Measurement | [analysis.py](../benchmark_tool/analysis.py): eligibility, denominators and brand contributions |
| Report binding | [export.py](../report/export.py): chart states and metric bindings; [reviewed narrative](../reviewed_studies/good_culture/2026_q4/narrative.json): approved interpretation |

Definitions and decision rules: [codebook](CODEBOOK.md), [context/exclusion protocol](CONTEXT_EXCLUSION_RULES_v2.1.0.md), [coding instructions](CODING_INSTRUCTIONS_v2.1.0.md).

## Lineage example: protein lead, 12 / 12

Q3 is an unbranded high-protein snack prompt. View `main|baseline|question|Q3|all` contains four engines × three passes, with no exclusions or visible context flags. Each answer assigns Good Culture explicit overall-lead credit of 1: 12 credits / 12 answers.

Record `main/chatgpt/Q3/1` links the [reviewed answer](https://yliclaire.github.io/good-culture-brief/evidence/13d5cb43e52a6080.html) to its [publication JSON](../data/browser_baseline/public_answers/13d5cb43e52a6080.json), coding and brand rows, and [contribution](../data/chart_tables/contributions.csv). [Denominators](../data/chart_tables/denominators.csv) and [membership](../data/chart_tables/membership.csv) define the engine-level populations. In [report_data.json](../data/report_data.json), `metric_bindings.protein_leads` identifies the displayed view, brand and field.

## Execution and reuse

[Build investment brief](https://github.com/yliclaire/good-culture-brief/actions/workflows/build-brief.yml) rebuilds `good_culture_browser_2026_q4` from saved inputs without API calls. [Collect engine answers](https://github.com/yliclaire/good-culture-brief/actions/workflows/collect-answers.yml) supports request preview and opt-in API collection. New evidence requires reviewed coding, interpretation and registry registration before report generation. Input hashes and narrative fingerprints are checked at build time.

The [operating guide](OPERATING_GUIDE.md) covers commands, credentials and [quarterly/category changes](OPERATING_GUIDE.md#reuse-next-quarter-or-in-another-category). The Birkenstock profile is an uncollected configuration example. [Validation](../VALIDATION.md) records local and hosted checks.

## Scope

Discovery and branded prompts, main and supplemental series, and browser and API evidence remain separate. Conditional answers remain in denominators; unavailable comparisons remain unavailable. Counts describe engine answers, not consumers or market share.

Public inputs are sanitized derivatives; original interface captures remain private. Coding review used the same assistant, without independent human agreement. Citation attachments establish recorded sources, not causal influence or factual verification. Live API collection remains unpiloted; adapter tests use offline fixtures. Monitoring scenarios are synthetic.
