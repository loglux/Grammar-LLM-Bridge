# Provider modes: JSON Schema vs json_object

This bridges how we talk to different LLM providers, depending on whether they support strict structured outputs (JSON Schema) or only a looser JSON mode (json_object/example-based).

## Modes
- **JSON Schema (strict)**  
  - Uses `response_format: json_schema` (OpenAI/Ollama/Anthropic via OpenRouter).  
  - Short prompt with 4 rules (exact `error_text`, copy character-for-character, no paraphrase, empty errors if perfect).  
  - Structure is validated by the provider → minimal parsing risk.
- **json_object (example-based)**  
  - Uses `response_format: json_object` (DeepSeek, Grok, others without schema).  
  - Longer prompt with an explicit JSON array example and extra instructions (“minimal fragment, don’t duplicate, don’t return whole sentences for local issues”).  
  - No strict validation → defensive parsing and retries.

## Provider routing
- **JSON Schema**: OpenAI (gpt-4.x), Ollama (OpenAI-compatible), Anthropic via OpenRouter (e.g., `claude-sonnet-4.5`).  
  - Sentence-level retries also use this path for schema-capable providers.
- **json_object**: DeepSeek (no schema), Grok, and “Others” where schema is not supported or unreliable.

## Why this split
- Schema-capable providers give guaranteed structure → fewer parse issues, cleaner matches.  
- Providers without schema need a guided example and defensive parsing. DeepSeek’s JSON is valid, but not schema-enforced; the example prompt reduces hallucinations.

## Prompts (summary)
- **Schema prompt**: concise 4-point “CRITICAL RULES” block.  
- **json_object prompt**: includes an example array, instructions to avoid whole-sentence returns for local issues, and to avoid duplicates/overlaps.

## Notes / Future
- If we unify prompts, ensure both schema and json_object paths carry the same rules (e.g., “minimal fragment” wording), adjusting length to the provider’s tolerance.  
- Naming: current code uses “schema” vs “fallback/json_object”; could be renamed for clarity but behavior stays the same.

## References
- OpenAI structured outputs: https://platform.openai.com/docs/guides/structured-outputs
- LanguageTool HTTP API (for LT JSON shape): `languagetool-swagger.json` in repo
