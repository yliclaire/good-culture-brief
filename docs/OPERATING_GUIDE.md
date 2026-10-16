# Operating guide

## Rebuild the saved study

Use **Build investment brief → Run workflow**. Select `build-brief` and registry ID `good_culture_browser_2026_q4`. Download the report artifact, extract run.zip, and open index.html. No provider credentials are needed. The optional `build-browser` operation creates measurement tables without the full investment brief.

The registered input hashes and narrative fingerprint are verified before rendering. Public-source records are sanitized derivatives with explicit provenance; the original interface captures are not required to rebuild this publication baseline.

## Collect a new wave

Use **Collect engine answers** with `operation = preview` first. Choose `good_culture` or `birkenstock`. Blank brand/competitor/question fields keep the profile defaults. Changing the brand alone does not adapt category-specific questions. Custom questions replace the question set and its contrasts. Review the exact generated requests before collecting.

For live collection, in your own repository’s **Settings → Secrets and variables → Actions**, configure only the selected providers:

| Provider | Repository secret | Repository variable |
| --- | --- | --- |
| openai | OPENAI_API_KEY | OPENAI_MODEL |
| anthropic | ANTHROPIC_API_KEY | ANTHROPIC_MODEL |
| gemini | GEMINI_API_KEY | GEMINI_MODEL |
| perplexity | PERPLEXITY_API_KEY | PERPLEXITY_MODEL |

Model variables must contain explicit model IDs compatible with the adapter’s search tools. `providers.json` can instead contain non-secret model IDs. Pilot a few calls before a full collection. Keys are injected only into the live collection step. Never put them in workflow text fields, source code or screenshots.

The request limit is not a dollar cap. Configure provider-side spending controls. Timeouts may still be billed. Collection stops on the first failure/incomplete answer without automatic retries and preserves the attempt for review.

New API outputs remain a distinct series from the consumer-browser baseline. The four providers are OpenAI, Anthropic, Gemini and Perplexity; Google AI Mode and Copilot Search browser supplements are not silently replaced by APIs.

## Review and register

Collection outputs draft review templates, not approved findings. Review the answers, coding/claim rows, context, exclusions and conclusions. Use the existing reviewed-study package as the schema reference. Add a new package to `reviewed_studies/` and an entry to `registry.json`. Seal every input in the review manifest and bind the reviewed narrative to its evidence/configuration/calculation fingerprint. Add the reviewed files to your repository before running Build investment brief. Downloaded artifacts do not sync back automatically.

A full brief requires discovery and branded questions. A narrower study can produce measurement outputs without satisfying the full investment-brief template. Keep unavailable comparisons unavailable; do not plot missing values as zero.

## Reuse next quarter or in another category

Keep the exact prompts, market/context, repeat plan, coding rules and engine setup comparable. Record model/mode changes and establish a comparable series before calling a change a brand trend. Repeats are not independent consumers.

For another category, change prompts, brand roster, attributes and reviewed interpretation. The collection runner, adapters, validation, calculations and renderer carry over. The Birkenstock profile is a design/preview example with no collected footwear evidence.

## Website updates

The reviewed website files live at the repository root; GitHub Pages deploys `main` / root. Both study workflows are manual and do not auto-publish new research. Build, review the output, then update the approved website files. Protect credentials and review the publication inputs before publishing a new wave. Pattern-based privacy checks cannot guarantee anonymity.

To prepare a separate site-only export from a built release, use `python -m report.web_export --release RELEASE --output NEW_FOLDER --repo-url YOUR_PUBLIC_REPO --site-url YOUR_PAGES_URL`. This command prepares files only; it never uploads or publishes.
