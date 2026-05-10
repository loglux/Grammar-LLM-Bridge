# Model Environment Variables

This file centralises the environment variables used to run Grammar-LLM-Bridge
with different providers. Keep secrets out of the file (use placeholders).

## Required variables

- `OPENAI_API_KEY`: API key for the selected provider.
- `OPENAI_BASE_URL`: Base URL for the provider.
- `LLM_MODEL`: Model name for the provider.

## Optional variables

- `GRAMMAR_ONLY`: `true` or `false` (default: `false`).
- `TYPOGRAPHY_CHECK`: `true` or `false` (default: `false`).

## Provider profiles (placeholders)

### DeepSeek

```
OPENAI_API_KEY=YOUR_DEEPSEEK_KEY
OPENAI_BASE_URL=https://api.deepseek.com
LLM_MODEL=deepseek-chat
```

### OpenAI

```
OPENAI_API_KEY=YOUR_OPENAI_KEY
OPENAI_BASE_URL=https://api.openai.com/v1
LLM_MODEL=gpt-4.1-mini
```

### OpenRouter (example: Claude Sonnet 4.5)

```
OPENAI_API_KEY=YOUR_OPENROUTER_KEY
OPENAI_BASE_URL=https://openrouter.ai/api/v1
LLM_MODEL=anthropic/claude-sonnet-4.5
```

### OpenRouter (example: GPT-4o)

```
OPENAI_API_KEY=YOUR_OPENROUTER_KEY
OPENAI_BASE_URL=https://openrouter.ai/api/v1
LLM_MODEL=openai/gpt-4o
```

## Notes

- Do not commit real keys to any repository.
- These variables are used by `docker run` for `grammar-llm-bridge:latest`.
