# Consolidated submission validation

This repository consolidates the existing interactive website with the full reusable implementation and both manual workflows. The sanitized publication baseline and exact metric parity passed local validation. Both consolidated workflows have passed hosted checks; the public run links are recorded below.

Previously, the original private implementation passed 43 offline tests and hosted builds. The report-only website passed live Chrome spot checks for reading tabs, budget filtering, answer dialogs, evidence pages, workflow guide and the synthetic model-change hold. A 390px mobile viewport showed no page-wide overflow. Those historical checks do not replace checks of the consolidated source.

Live API collection has not been piloted. Full keyboard accessibility and printed-page pagination checks remain pending. Factual verification is deferred.

## Consolidated local checks — 2026-10-16

- 45 Python tests passed, including derivative provenance requirements and unchanged original/browser screenshot rules.
- A complete brief rebuilt from the sealed sanitized baseline with 156 observations, 155 included and one excluded.
- All eight analytical sections matched the prior published report exactly: numeric views, bound numbers, counts, metric bindings, repeats, contrasts, citation counts and competitor matrix. The all-brand metric CSV also matched the original golden table.
- 188 view states and 940 artifact-local links passed; the site-only export passed 808 local-link checks.
- All website/report JavaScript syntax checks passed. DOM-model tests exercised tabs, filters, dialog controls and synthetic scenarios; these are not real-browser visual QA.
- Publication text/source was checked for the author’s private identifiers, personal name/location references, private repository links and credential patterns. No original image captures or interface archives are included. Pattern checks are not a guarantee of anonymity.
- Public study inputs have a new fingerprint and review seal. Original source bytes and narrative fingerprint are not misrepresented as unchanged.

No new engine requests or paid API collection were performed. The original private research repository was preserved.

## Public hosted validation

Validated source commit: `bd44a0e`.

- [Good Culture build](https://github.com/yliclaire/good-culture-brief/actions/runs/38877585800): success, 24 seconds.
- [Birkenstock collection preview](https://github.com/yliclaire/good-culture-brief/actions/runs/38877636708): success, 16 seconds; no keys or live engine requests.
- [Consolidated website deployment](https://github.com/yliclaire/good-culture-brief/actions/runs/38877507206): success, 46 seconds.

The published website loaded in Chrome. Methodology & reuse links to both public workflow definitions and the public study registry. These results validate the consolidated source and sanitized baseline, not live provider compatibility.

## Reviewer follow-through audit

[Audit findings and limits](docs/REVIEWER_AUDIT.md). A fresh checkout passed 45 tests, the documented build and a no-key preview; an extracted source kit rebuilt independently. All 74 local guide links passed across the repository and source kit. Six public entry points returned HTTP 200 without authentication. The [updated hosted build](https://github.com/yliclaire/good-culture-brief/actions/runs/38878639643) passed on revision `73008fd` in 22 seconds.
