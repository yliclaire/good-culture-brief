# Reviewer access and reproduction check — 2026-10-16

The repository now provides a complete path from the investment brief through answer evidence, coding rules, calculations and reusable workflows. No provider credentials are needed to read the study or reproduce the saved benchmark.

| Check | Result |
| --- | --- |
| Public access | The repository, brief, reviewer guide, codebook and both workflow pages returned HTTP 200 without cookies or authentication. |
| Clean checkout | All 45 tests passed from a fresh Git archive with provider keys/model variables removed. |
| Documented commands | Saved-study build succeeded. Birkenstock preview generated 96 planned requests with zero attempted/captured calls. |
| Numeric preservation | Eight analytical sections, including numeric views, counts, memberships, repeats, citation counts and competitor matrix, matched the published study. |
| Downloaded source kit | The release ZIP passed its CRC check; its extracted source independently rebuilt the study. Operating guide, reviewer guide, coding rules and linked trace tables are included. |
| Documentation links | 37 local links passed in the repository and the same 37 passed in the extracted source kit: 74 checks. |
| Hosted build | [Updated Good Culture build](https://github.com/yliclaire/good-culture-brief/actions/runs/38878639643) succeeded in 22 seconds on source revision `73008fd`. |
| Reviewer route | The README links to the brief, the evidence-to-code walkthrough and Actions. The guide traces the protein 12/12 result through actual observation IDs and contribution tables. |

The check repaired contradictory validation status, old run links in the assignment checklist, missing method references and incomplete source-kit documentation. It also fixed a brand name hard-coded in template status text; the existing brand-substitution regression now passes.

## Reading and running

The website, code, configuration and workflow definitions are public. To run Actions, reviewers need a fork with Actions enabled or write access to this repository. GitHub artifact downloads may require sign-in. Live collection requires their own API keys, explicit model IDs and confirmation of possible charges.

## Limits retained

Live API/provider compatibility remains unpiloted. New answers still require coding and investment review before registration. Citation mapping is partial (32/698 selected claims), factual verification is deferred, and strict context-free H1/H2 comparisons remain unavailable. Coding was reviewed by the same assistant rather than an independent human. Monitoring future cases are synthetic; the Birkenstock profile has no collected footwear findings. Full keyboard accessibility and printed-page pagination review remain pending.

These limitations affect what the study can conclude; they are not hidden behind a successful software build. No new engine queries, paid calls, raw screenshots or private interface captures were added during this audit.
