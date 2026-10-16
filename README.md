# Good Culture | Investment brief & reusable benchmark

**[Open the interactive brief ↗](https://yliclaire.github.io/good-culture-brief/)** · **[Research & implementation](docs/REVIEWER_GUIDE.md)** · **[Workflows](https://github.com/yliclaire/good-culture-brief/actions)**

An outside-in assessment of Good Culture’s positioning, substitutes and premium durability through AI answer engines. Includes the brief, Python pipeline, reviewed publication baseline, tests and two manual GitHub workflows.

[Print-friendly brief](https://yliclaire.github.io/good-culture-brief/print.html) · [Pipeline reference](https://yliclaire.github.io/good-culture-brief/reviewer-guide.html)

**156 captures: 155 included, one excluded.** Main series: 12 prompts × four browser experiences × three passes. The search supplement remains separate. Results measure engine answers, not consumer demand, market share or willingness to pay.

## Run the tool

| Workflow | What it does | API keys |
| --- | --- | --- |
| [Collect engine answers](https://github.com/yliclaire/good-culture-brief/actions/workflows/collect-answers.yml) | Preview the exact requests, or collect a new API wave | None for preview; your own keys for live collection |
| [Build investment brief](https://github.com/yliclaire/good-culture-brief/actions/workflows/build-brief.yml) | Validate and rebuild a registered, reviewed study | Not needed |

Actions require write access or a fork with Actions enabled. `build-brief` with `reviewed_study = good_culture_browser_2026_q4` rebuilds the saved study without engine calls. The report artifact contains `run.zip`; its entry point is `index.html`.

`preview` generates exact requests from the selected profile and optional brand, competitor and question overrides. `collect` requires provider secrets, explicit model IDs and paid-call confirmation. New evidence requires reviewed coding, exclusions and interpretation, sealed inputs and a registry entry before building a brief. Browser and API evidence remain separate series. The Birkenstock profile contains no collected findings.

**Hosted checks passed:** [Good Culture rebuild](https://github.com/yliclaire/good-culture-brief/actions/runs/38878639643) · [Birkenstock preview](https://github.com/yliclaire/good-culture-brief/actions/runs/38877636708). Both run from this public repository.

[Operating guide and key configuration](docs/OPERATING_GUIDE.md) · [Publication transformation](data/browser_baseline/PUBLICATION.md) · [Validation](VALIDATION.md) · [Reviewer access & reproduction check](docs/REVIEWER_AUDIT.md)

## Where to inspect the implementation

| Path | Purpose |
| --- | --- |
| [automation/run.py](automation/run.py) | Shared runner used by both Actions workflows |
| [automation/providers.py](automation/providers.py) | Four-provider API request and evidence adapters |
| [benchmark_tool/](benchmark_tool/) | Configuration, evidence validation, denominators and calculations |
| [report/](report/) | Data export, charts, narrative binding, HTML rendering and monitoring demonstration |
| [studies/](studies/) | Good Culture and Birkenstock category profiles |
| [reviewed_studies/](reviewed_studies/) | Reviewed narrative, input hashes and study registry |
| [data/browser_baseline/](data/browser_baseline/) | Sanitized, reproducible publication evidence and coding |
| [tests/](tests/) | Offline checks and interaction models |
| [.github/workflows/](.github/workflows/) | Collection and report-building workflows |

Python 3.12 and the standard library are sufficient for the pipeline. Node is used for optional interaction checks and is available on GitHub’s runner.

```sh
python -m unittest discover -s tests
python automation/run.py build-brief --reviewed-study good_culture_browser_2026_q4 --output artifacts/my-brief
python automation/run.py preview --study birkenstock --output artifacts/sandal-plan
```

Use a new output folder for each run. Artifacts are retained for 30 days; download releases you wish to keep. Building a report creates an artifact; it does not automatically replace the website. The website publishes the approved files on `main` through GitHub Pages.

## Evidence and publication

The public baseline contains sanitized answer text and separately labeled coding/context excerpts. Original captures remain private. Capture hashes, transformation records and sealed input hashes preserve lineage. Inclusion decisions, coding, denominator memberships and numeric results match the original all-brand metric table; the excluded partial answer has an audit placeholder.

Citation mapping is selective, factual verification is deferred, and coding review used the same assistant without independent human agreement. Monitoring scenarios are synthetic. Live API collection remains unpiloted; provider adapters use offline fixture tests.
