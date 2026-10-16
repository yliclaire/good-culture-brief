# Public evidence baseline

This is a sanitized derivative of the reviewed browser study. It is not a new collection or an independent coding exercise.

- 156 observation IDs, 155 included answers and one excluded placeholder are retained.
- Coding, brands, selected claims, citation attachments, context flags and measurement decisions carry over.
- Personal name/location references are replaced with a withholding label. Interface captures, screenshots and local paths are omitted.
- Each `public_answers/*.json` separates reviewed answer prose from retained coding/context audit excerpts. The original capture SHA-256 identifies the privately retained original; the public file has a separate hash.
- `publication_transform.json` records the original review seal/fingerprint and affected observation IDs. `relocation.json` indexes the public derivatives; it does not claim byte identity with originals.
- The public narrative receives a new evidence fingerprint and review seal because its input bytes changed. Numeric parity with the original metric table is required.

Coding/context excerpts support traceability, not independent factual truth. Missing citation coverage and the limitations described in the brief remain unresolved. Synthetic demonstrations remain separate from observed evidence.
