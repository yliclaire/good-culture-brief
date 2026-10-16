# Operating guide

## Rebuild the saved study

Workflow: **Build investment brief**. Operation: `build-brief`. Registry ID: `good_culture_browser_2026_q4`. No provider credentials or new engine calls. Output: report artifact containing `run.zip`, with `index.html` as entry point. `build-browser` produces measurement tables only. Actions require write access or a fork with workflows enabled.

The registered input hashes and narrative fingerprint are verified before rendering. Public-source records are sanitized derivatives with explicit provenance; the original interface captures are not required to rebuild this publication baseline.

## Run locally instead

Python 3.12+, standard library. Node enables optional interaction tests and is included on the GitHub runner.

```sh
git clone https://github.com/yliclaire/good-culture-brief.git
cd good-culture-brief
python3 -m unittest discover -s tests
python3 automation/run.py build-brief --reviewed-study good_culture_browser_2026_q4 --output artifacts/reviewer-brief
python3 automation/run.py preview --study birkenstock --output artifacts/reviewer-sandal-plan
```

Run from the repository root with a new output directory. Built reports include an independent `code/` source kit with operating and coding references.

## Collect a new wave

**Collect engine answers** supports `preview` and `collect`. Profiles: `good_culture`, `birkenstock`. Blank overrides retain profile defaults; a brand override alone does not adapt category-specific prompts. Custom questions replace the prompt set and contrasts. Inspect the generated plan before collection.

Live collection uses Actions repository secrets and variables:

| Provider | Repository secret | Repository variable |
| --- | --- | --- |
| openai | OPENAI_API_KEY | OPENAI_MODEL |
| anthropic | ANTHROPIC_API_KEY | ANTHROPIC_MODEL |
| gemini | GEMINI_API_KEY | GEMINI_MODEL |
| perplexity | PERPLEXITY_API_KEY | PERPLEXITY_MODEL |

Model IDs must support the adapter’s search tools; non-secret IDs may also be supplied in `providers.json`. Keys are injected only into the live collection step. Pilot live compatibility before a full run.

Request limits cap calls, not cost. Provider-side spending controls apply; timeouts may be billed. Collection stops on the first failed or incomplete answer, preserves the attempt and does not retry automatically.

New API outputs remain a distinct series from the consumer-browser baseline. The four providers are OpenAI, Anthropic, Gemini and Perplexity; Google AI Mode and Copilot Search browser supplements are not silently replaced by APIs.

Custom-question input is a JSON list of objects with `id`, `kind` (`discovery` or `branded`) and `text`. Blank input keeps the category defaults. For example:

```json
[{"id":"general","kind":"discovery","text":"Which comfort-sandal brand should I buy, and why?"},{"id":"premium","kind":"branded","text":"When is Birkenstock worth paying more for than Teva?"}]
```

## Review and register

Collection emits draft coding templates. Review answers, coding, claims, context, exclusions and interpretation; register the approved package in `reviewed_studies/` and `registry.json`. The existing package defines the schema. The review manifest seals every input; the narrative binds to the evidence/configuration/calculation fingerprint. Reviewed files must be committed before building; artifacts do not sync to the repository.

A full brief requires discovery and branded questions. A narrower study can produce measurement outputs without satisfying the full investment-brief template. Keep unavailable comparisons unavailable; do not plot missing values as zero.

## Reuse next quarter or in another category

Keep the exact prompts, market/context, repeat plan, coding rules and engine setup comparable. Record model/mode changes and establish a comparable series before calling a change a brand trend. Repeats are not independent consumers.

For another category, change prompts, brand roster, attributes and reviewed interpretation. The collection runner, adapters, validation, calculations and renderer carry over. The Birkenstock profile is a design/preview example with no collected footwear evidence.

## Website updates

GitHub Pages deploys `main` / root. Study workflows produce artifacts; publication is a separate commit of reviewed website files. Public exports exclude original captures and personal references. Pattern-based privacy checks cannot guarantee anonymity.

To prepare a separate site-only export from a built release, use `python -m report.web_export --release RELEASE --output NEW_FOLDER --repo-url YOUR_PUBLIC_REPO --site-url YOUR_PAGES_URL`. This command prepares files only; it never uploads or publishes.
