# Good Culture | Investment brief & reusable benchmark

**[Open the interactive brief ↗](https://yliclaire.github.io/good-culture-brief/)** · **[Explore the code](automation/)** · **[Open the workflows](https://github.com/yliclaire/good-culture-brief/actions)**

An outside-in read of Good Culture’s positioning, substitutes and premium durability through AI answer engines. The website opens without downloading files or signing in. This repository also contains the Python implementation, reviewed publication baseline, tests and two manual GitHub workflows.

## Start with the brief

- **Investment brief:** findings, investment implications and priority diligence.
- **Explore the benchmark:** compare shopper needs and engines, then inspect the answers behind each result.
- **Methodology & reuse:** the research choices and how to run another quarter or brand.

[Print-friendly brief](https://yliclaire.github.io/good-culture-brief/print.html) · [Code & workflow walkthrough](https://yliclaire.github.io/good-culture-brief/reviewer-guide.html)

The study contains **156 captures: 155 included, one excluded**. The main series is 12 prompts × four browser experiences × three passes. The search supplement remains separate. These results describe engine answers, not consumer demand, market share or willingness to pay.

## Run the tool

| Workflow | What it does | API keys |
| --- | --- | --- |
| [Collect engine answers](https://github.com/yliclaire/good-culture-brief/actions/workflows/collect-answers.yml) | Preview the exact requests, or collect a new API wave | None for preview; your own keys for live collection |
| [Build investment brief](https://github.com/yliclaire/good-culture-brief/actions/workflows/build-brief.yml) | Validate and rebuild a registered, reviewed study | Not needed |

Anyone can inspect or download the code. To run Actions, fork the repository into your own GitHub account and enable Actions, or use an account with write access here. No installation is needed for Actions. Do not enter API keys in workflow inputs or commit them.

**Rebuild Good Culture:** open Build investment brief, choose `build-brief`, leave `reviewed_study = good_culture_browser_2026_q4`, then run it. Download the completed run’s report artifact, extract `run.zip`, and open `index.html`. This rebuild uses saved evidence and makes no new engine calls.

**Try another brand:** open Collect engine answers and run `preview` first. Choose the category profile, brand, competitors and optional questions. The uncollected Birkenstock profile changes the category questions and demonstrates reuse; it contains no footwear findings. Live collection requires keys, explicit model IDs and confirmation that API charges may apply.

**Review sits between collection and reporting.** Check answers, approve coding, resolve exclusions and review the investment interpretation. Add the approved inputs and their review manifest to the registry before building a new brief. A new quarter or brand does not automatically inherit Good Culture’s conclusion. Browser and API evidence remain separate series.

[Operating guide and key configuration](docs/OPERATING_GUIDE.md) · [Publication transformation](data/browser_baseline/PUBLICATION.md) · [Validation](VALIDATION.md)

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

This public baseline is a **labeled derivative**, not an archive of original browser interfaces. Personal references and interface material are withheld. Reviewed answer text and the coding/context excerpts required for validation are distinguished in each JSON record. Original screenshots and captures remain in a separate private archive. The original capture hash, publication transformation, derived input hashes and review manifest preserve the lineage.

All inclusion decisions, context flags, brand coding, denominator memberships and numeric results are preserved. The excluded partial answer is represented by an audit placeholder. The public baseline is checked against the original all-brand metric table. Citation mapping remains selective, material factual verification is deferred, and coding review was performed by the same assistant rather than an independent human reviewer.

The monitoring examples are synthetic and separate from the observations. Live provider collection remains unpiloted; provider adapters are checked with offline fixtures. No API credentials or paid requests are included in this submission.
