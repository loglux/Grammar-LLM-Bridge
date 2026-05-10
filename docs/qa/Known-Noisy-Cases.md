## Known Noisy Cases (QA)

- **Tense shifts**: “ends → ended” in descriptive present (e.g. “one paragraph ends with a comma”) — treat as false positive.
- **Word choice**: “features → has”, “running slightly behind schedule → experiencing minor delays” — stylistic; tolerate for now.
- **Hyphenation**: “open question → open-question”, “soundproof appears → soundproof-appears” — filtered if message contains “hyphen”; others may slip.
- **Comma decisions**: LLM may flag comma splices correctly (“March, others → March; others”), but also suggest extra commas in clauses starting with “while …”.
- **Masked placeholders**: complaints about `MMMM…` or `$…$` blocks are skipped by masking; ignore if seen.

Action: mark these as noise in QA unless they repeat frequently; consider future filters for word choice/tense if volume grows.
